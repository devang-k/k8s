"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: views.py  
 * Description: This code defines several views in Django for managing project-related tasks like running projects, retrieving job lists, viewing job details, and clearing results. Each view is designed to interact with a project or job, ensuring proper validation, status handling, and responses. The swagger_auto_schema decorator is used to automatically generate OpenAPI documentation for each API endpoint. 
 *  
 * Author: Mansi Mahadik 
 * Created On: 17-12-2024
 * Modified On: 20-01-2025
 *  
 * This source code and associated materials are the property of SiClarity, Inc.  
 * Unauthorized copying, modification, distribution, or use of this software,  
 * in whole or in part, is strictly prohibited without prior written permission  
 * from SiClarity, Inc.  
 *  
 * Disclaimer:  
 * This software is provided "as is," without any express or implied warranties,  
 * including but not limited to warranties of merchantability, fitness for a  
 * particular purpose, or non-infringement. In no event shall SiClarity, Inc.  
 * be held liable for any damages arising from the use of this software.  
 *  
 * SiClarity and its logo are trademarks of SiClarity, Inc.  
 *  
 * For inquiries, contact: support@siclarity.com  
 ***************************************************************************/"""
from base64 import b64decode
import json
from django.db.models import Q, OuterRef, Subquery
from django.http import JsonResponse
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from json import loads
from rest_framework.views import APIView
from rest_framework import status
from src.Apps.project.MLRunner.serializers import JobSerializer, AllJobSerializer
from src.Apps.project.MLRunner.tasks import process_job
from src.Apps.project.ProjectManager.models import Project, Job, TechFileCatalog
from src.Apps.user.Login.models import User
from src.Services.ProjectService import getAction , check_present_cells
from src.Services.JobService import create_job, save_tech_catalog_data
from src.Services.GRPCService import check_input_validity, gds_file_check, update_project_tech
from src.Models.Project.ProjectResponse import ProjectResponse
from src.Services.StorageServices.StorageService import storage_servicer
from SiVista_BE.settings import S3_BUCKET_ROOT
from datetime import datetime
import copy

class RunProject(APIView):
    @swagger_auto_schema(
        operation_summary="Run project",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'cells': openapi.Schema(type=openapi.TYPE_ARRAY,
                                        items=[openapi.Schema(type=openapi.TYPE_STRING)], 
                                        description='List of cells names'),
                'projectName': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the project'),
                'netlistData': openapi.Schema(type=openapi.TYPE_STRING, description='Netlist metadata'),
                'techData': openapi.Schema(type=openapi.TYPE_OBJECT, description='Tech metadata'),
                'action': openapi.Schema(type=openapi.TYPE_INTEGER, description='Action to perform'),
                'selectedLayouts': openapi.Schema(type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(type=openapi.TYPE_STRING,description='Name of the GDS file'), 
                                        description='List of GDS file names'),
                'stage1Project':openapi.Schema(type=openapi.TYPE_INTEGER,description='Project Id')
            },
            required=['projectName', 'netlistMetadata', 'techMetadata', 'action']
        ),
        responses={
            200: openapi.Response('Success', openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'status': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'data': openapi.Schema(type=openapi.TYPE_OBJECT),
            })),
            400: openapi.Response('Bad Request', openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'status': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'data': openapi.Schema(type=openapi.TYPE_OBJECT),
            })),
        }
    )
    def post(self, request):
        data = loads(request.body)
        project_id = data['projectId']
        active_job_statuses = ['RUNNING','QUEUED']
        project = Project.objects.filter(pk=project_id).first() if isinstance(project_id, int) else None
        user = User.objects.filter(pk=request.user_id).first()
        data['project_name'] = project.project_name if project else None
        data['elastic_log_level'] = user.log_level if user else None
        if not project:
            response = JsonResponse(vars(ProjectResponse("Invalid project ID", status.HTTP_404_NOT_FOUND, False)))
            response.status_code = status.HTTP_404_NOT_FOUND
            return response
        if project.created_by_id != request.user_id:  # TODO: Check if the user has the permissions to run this project
            response = JsonResponse(vars(ProjectResponse("You are not allowed to run this project", status.HTTP_403_FORBIDDEN, False)))
            response.status_code = status.HTTP_403_FORBIDDEN
            return response
        data['project_user_id'] = project.created_by_id
        if not isinstance(data['action'], int) or isinstance(data['action'], bool):
            response = JsonResponse(vars(ProjectResponse("Invalid action", status.HTTP_400_BAD_REQUEST, False)))
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response
        if data['action'] == getAction.Layout.value:
            # TODO: check if project_type is valid or not here.
            if Job.objects.filter(created_by=request.user_id, project_id=project_id, status__in=active_job_statuses).exists():
                response = JsonResponse(vars(ProjectResponse('The project is currently in a running state. Please try again later.', status.HTTP_208_ALREADY_REPORTED, False)))
                response.status_code = status.HTTP_208_ALREADY_REPORTED
                return response
            if Job.objects.filter(created_by=request.user_id, project_id=project_id, action=1, status='COMPLETED').exists():
                response = JsonResponse(vars(ProjectResponse('Some results from your previous runs will be overwritten. Do you want to continue?', status.HTTP_409_CONFLICT, False)))
                response.status_code = status.HTTP_409_CONFLICT
                return response
            is_valid, message = check_input_validity(data['cells'], data['netlistData'], data['techData'])
            if not is_valid:
                response = JsonResponse(vars(ProjectResponse(message, status.HTTP_400_BAD_REQUEST, False)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            non_present_cells = check_present_cells(data['cells'],project.netlist_metadata)
            if non_present_cells==[]:
                data['netlistData'] = b64decode(data['netlistData']).decode('utf-8').replace('\\n', '\n')
                data['project_type'] = project.project_type
                #saving techfile data in techCatalog befor update
                techCatalogData = copy.deepcopy(data['techData'])
                data['techData'], data['is_double_height'] = update_project_tech(data['techData'], project.project_type)
                job = create_job(project, data, request.user_id)
                if techCatalogData:
                    existing_entries = TechFileCatalog.objects.filter(
                        project_id=project,
                        created_by_id=request.user_id
                    )
                tech_data_str = json.dumps(techCatalogData, sort_keys=True)
                is_duplicate = False
                for entry in existing_entries:
                    existing_tech_data_str = json.dumps(entry.tech_data, sort_keys=True)
                    if existing_tech_data_str == tech_data_str:
                        # entry.status = 'QUEUED'
                        # entry.job_id = job.id
                        # entry.save()
                        is_duplicate = True
                        break
                if not is_duplicate:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    fileName=f'{project.tech_metadata['fileName'].replace('.tech','')}_{timestamp}.tech'
                    job_id = job.id
                    jobStatus = job.status
                    saveTechCatalogData = save_tech_catalog_data(project, data, job_id, techCatalogData,fileName,jobStatus, request)
                    if saveTechCatalogData:
                        print("Tech catalog saved successfully for job ID:", job_id)
                process_job.delay(job.id, data)
            else:
                response = JsonResponse(vars(ProjectResponse(f"Cells {', '.join(non_present_cells)} are not present in the netlist", status.HTTP_400_BAD_REQUEST, False)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            #result = run_layout(data['cells'], project.id, project.created_by_id, data['netlistData'], dumps(data['techData']), job.id, stage1=True)
        elif data['action'] == getAction.Hyperexpresivity.value:
            if Job.objects.filter(created_by_id=request.user_id, project_id=project_id, status__in=active_job_statuses).exists():
                response = JsonResponse(vars(ProjectResponse('The project is currently in a running state. Please try again later.', status.HTTP_208_ALREADY_REPORTED, False)))
                response.status_code = status.HTTP_208_ALREADY_REPORTED
                return response
            if Job.objects.filter(created_by=request.user_id, project_id=project_id, action=2, status='COMPLETED').exists():
                response = JsonResponse(vars(ProjectResponse('Some results from your previous runs will be overwritten. Do you want to continue?', status.HTTP_409_CONFLICT, False)))
                response.status_code = status.HTTP_409_CONFLICT
                return response
            if not isinstance(data['cells'], list) or data['cells'] == [] or len(data['cells']) == 0 or data['cells'] == None:
                response = JsonResponse(vars(ProjectResponse(f"Select at least one cell and must be list instance", status.HTTP_400_BAD_REQUEST, False)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if not isinstance(data['selectAll'], bool):
                response = JsonResponse(vars(ProjectResponse(f"SelectAll must be bool instance", status.HTTP_400_BAD_REQUEST, False)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if data['selectAll']==False:
                if data['selectedLayouts']==[]:
                    response = JsonResponse(vars(ProjectResponse(f"Select at least one layout.", status.HTTP_400_BAD_REQUEST, False)))
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return response
            else:
                if data['selectedLayouts']==[]:
                    pass
                else:
                    response = JsonResponse(vars(ProjectResponse(f"Selected layouts must be empty list.", status.HTTP_400_BAD_REQUEST, False)))
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return response
            if project.action==3 or project.action==2:
                project.selectedLayouts = None
                project.selectedLayouts=data['selectedLayouts']
                project.save()
            if not data['selectAll']:
                basepath=f'{S3_BUCKET_ROOT}/Project/{data['project_user_id']}/{data['projectId']}/Stage1/'
                cells=storage_servicer.list_folders(basepath)
                non_present_cells = check_present_cells(data['cells'],project.netlist_metadata)
                if non_present_cells==[]:
                    mismatch = []
                    # Iterate through each item in the selected list
                    for item in data['selectedLayouts']:
                        # Check if the item starts with any of the elements in the cell list
                        if not any(item.startswith(prefix) for prefix in data['cells']): 
                            mismatch.append(item)
                    if mismatch==[]:
                        file_list = []
                        for cell in cells:
                            try:
                                pexbasepath=f'{basepath}{cell}/{cell}_predictions/{cell}_GDS_PEX_PREDICTION_ML.csv'
                                pex_df = storage_servicer.fetch_csv(pexbasepath)
                                file_list.extend(pex_df['File'].tolist())
                            except:
                                pass
                        missing_layouts = set(data['selectedLayouts']) - set(file_list)
                        # if missing_layouts:
                        #     response = JsonResponse(vars(ProjectResponse(f"Layout {', '.join(missing_layouts)} is are not available.", status.HTTP_400_BAD_REQUEST, False)))
                        #     response.status_code = status.HTTP_400_BAD_REQUEST
                        #     return response
                        data['selectedLayouts'] = [sl if sl.endswith('.gds') else sl + '.gds' for sl in data['selectedLayouts']]
                        is_valid = gds_file_check(data['selectedLayouts'])
                        if not is_valid:
                            response = JsonResponse(vars(ProjectResponse('selected layouts must all be GDS files', status.HTTP_400_BAD_REQUEST, False)))
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return response
                        else:
                            if project.action==3:
                                tech_message, tech_data, status_code, response_status=storage_servicer.get_tech_netlist_data(f'{S3_BUCKET_ROOT}/Project/{request.user_id}/{project_id}/Techfile/{project.tech_metadata['fileName']}','USER','Techfile')
                                netlist_message, netlist_data, status_code, response_status=storage_servicer.get_tech_netlist_data(f'{S3_BUCKET_ROOT}/Project/{request.user_id}/{project_id}/Netlist/{project.netlist_metadata['fileName']}','USER','Netlist')
                            elif project.action==2:
                                tech_file = project.tech_metadata['fileName']#.replace(project.stage_one_project_name, "")
                                netlist_file= project.netlist_metadata['fileName']#.replace(project.stage_one_project_name, "")
                                tech_message, tech_data, status_code, response_status=storage_servicer.get_tech_netlist_data(f'{S3_BUCKET_ROOT}/Project/{request.user_id}/{project_id}/Techfile/{tech_file}','USER','Techfile')
                                netlist_message, netlist_data, status_code, response_status=storage_servicer.get_tech_netlist_data(f'{S3_BUCKET_ROOT}/Project/{request.user_id}/{project_id}/Netlist/{netlist_file}','USER','Netlist')
                            data['netlistData'] = None
                            data['techData'] = {}
                            if tech_message =='Success' and netlist_message=='Success':
                                data['netlistData'] = netlist_data
                                data['netlistData']=b64decode(data['netlistData']).decode('utf-8').replace('\\n', '\n')
                                data['techData']={"FileContent":tech_data}
                            if data['techData']=={} or data['netlistData']==None:
                                response = JsonResponse(vars(ProjectResponse("Techfile or Netlist file is not available.", status.HTTP_400_BAD_REQUEST, False)))
                                response.status_code = status.HTTP_400_BAD_REQUEST
                                return response
                            else:
                                data['techData'], data['is_double_height'] = update_project_tech(data['techData'], project.project_type)
                                job = create_job(project, data, request.user_id)
                                process_job.delay(job.id, data)
                    else:
                        response = JsonResponse(vars(ProjectResponse(f"Layout {', '.join(mismatch)} not included in the selected cells.", status.HTTP_400_BAD_REQUEST, False)))
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return response
                else:
                    response = JsonResponse(vars(ProjectResponse(f"Cells {', '.join(non_present_cells)} are not present in the netlist", status.HTTP_400_BAD_REQUEST, False)))
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return response
                # result = run_hyperexpressivity(data['cells'], project.id, project.created_by_id, dumps(data['techData']), data.get('stage1Project', None), data.get('selectedLayouts', {}), job.id)
            else:
                if project.action==3:
                    tech_message, tech_data, status_code, response_status=storage_servicer.get_tech_netlist_data(f'{S3_BUCKET_ROOT}/Project/{request.user_id}/{project_id}/Techfile/{project.tech_metadata['fileName']}','USER','Techfile')
                    netlist_message, netlist_data, status_code, response_status=storage_servicer.get_tech_netlist_data(f'{S3_BUCKET_ROOT}/Project/{request.user_id}/{project_id}/Netlist/{project.netlist_metadata['fileName']}','USER','Netlist')
                elif project.action==2:
                    tech_file = project.tech_metadata['fileName']#.split("_", 1)[1]
                    netlist_file= project.netlist_metadata['fileName']#.split("_", 1)[1]
                    tech_message, tech_data, status_code, response_status=storage_servicer.get_tech_netlist_data(f'{S3_BUCKET_ROOT}/Project/{request.user_id}/{project_id}/Techfile/{tech_file}','USER','Techfile')
                    netlist_message, netlist_data, status_code, response_status=storage_servicer.get_tech_netlist_data(f'{S3_BUCKET_ROOT}/Project/{request.user_id}/{project_id}/Netlist/{netlist_file}','USER','Netlist')
                data['netlistData'] = None
                data['techData'] = {}
                if tech_message =='Success' and netlist_message=='Success':
                    data['netlistData'] = netlist_data
                    data['netlistData']=b64decode(data['netlistData']).decode('utf-8').replace('\\n', '\n')
                    data['techData']={"FileContent":tech_data}
                if data['techData']=={} or data['netlistData']==None:
                    response = JsonResponse(vars(ProjectResponse("Techfile or Netlist file is not available.", status.HTTP_400_BAD_REQUEST, False)))
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return response
                else:
                    data['techData'], data['is_double_height'] = update_project_tech(data['techData'], project.project_type)
                    job = create_job(project, data, request.user_id)
                    process_job.delay(job.id, data)
        else:
            response = JsonResponse(vars(ProjectResponse("Invalid action", status.HTTP_404_NOT_FOUND, False)))
            response.status_code = status.HTTP_404_NOT_FOUND
            return response
        response = JsonResponse(vars(ProjectResponse("Job has been queued successfully", status.HTTP_200_OK, True, {'jobId': job.id})))
        response.status_code = status.HTTP_200_OK
        return response

class JobList(APIView):
    @swagger_auto_schema(
        operation_summary="Get the list of running jobs",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'showAllJobs': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Show all jobs'),
            },
            required=['showAllJobs']),
        responses={
            200: openapi.Response('Success', openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'status': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'data': openapi.Schema(type=openapi.TYPE_OBJECT),
            })),
            400: openapi.Response('Bad Request', openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'status': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'data': openapi.Schema(type=openapi.TYPE_OBJECT),
            })),
        }
    )
    def post(self, request):
        userId=request.user_id
        user = User.objects.filter(pk=userId).first()
        if not user:
            response = JsonResponse(vars(ProjectResponse("Invalid user ID", status.HTTP_404_NOT_FOUND, False)))
            response.status_code = status.HTTP_404_NOT_FOUND
            return response
        data=request.data
        show_all_jobs=data.get('showAllJobs',False)
        if isinstance(show_all_jobs,bool):
            if show_all_jobs==False:
                
                if user.is_staff == True:
                    jobs = Job.objects.filter(
                        Q(status='RUNNING',created_by=userId)
                    ).distinct().order_by('-created_date')
                else:
                    jobs = Job.objects.filter(
                        (Q(project__created_by=user) | Q(project__modified_by=user)) & Q(status='RUNNING')
                    ).distinct().order_by('-created_date')
            else:
                if user.is_staff == True:
                    # Step 1: Create a subquery to get the latest job by `created_date` for each project
                    latest_job_subquery = Job.objects.filter(
                        project_id=OuterRef('project_id')  # Match the project_id of the outer query
                    ).order_by('-created_date', '-id')  # Order by `created_date` and `id` (desc) to get the latest job

                    # Step 2: Main query to get only the last job per project
                    jobs = Job.objects.filter(
                        (Q(project__created_by=user) | Q(project__modified_by=user)) &
                        Q(status__in=['COMPLETED', 'RUNNING', 'FAILED'],created_by=userId)
                    ).filter(
                        id=Subquery(latest_job_subquery.values('id')[:1])  # Get the job with the latest created_date and id for each project
                    ).order_by('-created_date')  # Order by created_date to ensure jobs are ordered in descending order

                else:
                    # Step 1: Create a subquery to get the latest job by `created_date` for each project
                    latest_job_subquery = Job.objects.filter(
                        project_id=OuterRef('project_id')  # Match the project_id of the outer query
                    ).order_by('-created_date', '-id')  # Order by `created_date` and `id` (desc) to get the latest job

                    # Step 2: Main query to get only the last job per project
                    jobs = Job.objects.filter(
                        (Q(project__created_by=user) | Q(project__modified_by=user)) &
                        Q(status__in=['COMPLETED', 'RUNNING', 'FAILED'])
                    ).filter(
                        id=Subquery(latest_job_subquery.values('id')[:1])  # Get the job with the latest created_date and id for each project
                    ).order_by('-created_date')  # Order by created_date to ensure jobs are ordered in descending order
                    # jobs = Job.objects.filter(
                    #     (Q(project__created_by=user) | Q(project__modified_by=user)) & Q(status='RUNNING')
                    # ).distinct().order_by('-created_date')
            serializer = JobSerializer(jobs, many=True)
            if serializer.data == [] or serializer.data==None:
                response = JsonResponse(vars(ProjectResponse("There is not any running job present", status.HTTP_404_NOT_FOUND, False)))
                response.status_code = status.HTTP_404_NOT_FOUND
                return response
            response = JsonResponse(vars(ProjectResponse("Running jobs list retrieved", status.HTTP_200_OK, True, serializer.data)))
            response.status_code = status.HTTP_200_OK
            return response
        else:
            response = JsonResponse(vars(ProjectResponse("Invalid showAllJobs value must be boolean.", status.HTTP_400_BAD_REQUEST, False)))
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response

class JobDetails(APIView):
    @swagger_auto_schema(
        operation_summary="Get the description of running jobs",
        responses={
            200: openapi.Response('Success', openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'status': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'data': openapi.Schema(type=openapi.TYPE_OBJECT),
            })),
            400: openapi.Response('Bad Request', openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'status': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'data': openapi.Schema(type=openapi.TYPE_OBJECT),
            })),
        }
    )
    def get(self, request, jid):
        job = Job.objects.filter(pk=jid).first()
        if not job:
            response = JsonResponse(vars(ProjectResponse("Invalid job ID", status.HTTP_404_NOT_FOUND, False)))
            response.status_code = status.HTTP_404_NOT_FOUND
        elif job.created_by_id != request.user_id:
            response = JsonResponse(vars(ProjectResponse("You can't view this job's details", status.HTTP_403_FORBIDDEN, False)))
            response.status_code = status.HTTP_403_FORBIDDEN
        else:
            job = AllJobSerializer(job)
            response = JsonResponse(vars(ProjectResponse("Job details retrieved", status.HTTP_200_OK, True, job.data)))
            response.status_code = status.HTTP_200_OK
        return response
    
class ClearResult(APIView):
    @swagger_auto_schema(
        operation_summary="Clear results from S3 for perticular project",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'projectId': openapi.Schema(type=openapi.TYPE_INTEGER, description='Id for the Project'),
                'stage': openapi.Schema(type=openapi.TYPE_INTEGER, description='Action to perform'),
            },
            required=['project', 'action']
        ),
        responses={
            200: openapi.Response('Success', openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'status': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'data': openapi.Schema(type=openapi.TYPE_OBJECT),
            })),
            400: openapi.Response('Bad Request', openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'status': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'data': openapi.Schema(type=openapi.TYPE_OBJECT),
            })),
        }
    )
    def post(self, request):
        data=request.data
        userId=request.user_id
        projectId=data['projectId']
        stage=data['stage']
        if not isinstance(projectId, int):
            response = JsonResponse(vars(ProjectResponse("Invalid project ID", status.HTTP_404_NOT_FOUND, False)))
            response.status_code = status.HTTP_404_NOT_FOUND
            return response
        if not isinstance(stage , int):
            message= "The action provided is not valid. Try with valid action."
            status_code=status.HTTP_400_BAD_REQUEST
            response_status=False
            response = JsonResponse(vars(ProjectResponse(message, status_code, response_status)))
            response.status_code=status_code
            return response
        if not (int(stage) == getAction.Hyperexpresivity.value or int(stage) == getAction.Layout.value ):
            message= "The stage provided is not valid. Try with valid action."
            status_code=status.HTTP_400_BAD_REQUEST
            response_status=False
            response = JsonResponse(vars(ProjectResponse(message, status_code, response_status)))
            response.status_code=status_code
            return response
        project = Project.objects.filter(pk=projectId).first()
        if not project :
            response = JsonResponse(vars(ProjectResponse("Invalid project ID", status.HTTP_404_NOT_FOUND, False)))
            response.status_code = status.HTTP_404_NOT_FOUND
            return response
        if project.created_by_id != request.user_id:  # TODO: Check if the user has the permissions to run this project
            response = JsonResponse(vars(ProjectResponse("You are not allowed to run this project", status.HTTP_403_FORBIDDEN, False)))
            response.status_code = status.HTTP_403_FORBIDDEN
            return response
        if int(stage)==int(getAction.Layout.value):
            status_flag1=storage_servicer.delete_folder(f'{S3_BUCKET_ROOT}/Project/{userId}/{projectId}/Stage1/')
            if project.action==3:
                status_flag=storage_servicer.delete_folder(f'{S3_BUCKET_ROOT}/Project/{userId}/{projectId}/Stage2/')
                if status_flag==True:
                    job = Job.objects.filter(project_id=projectId, created_by=userId,action=2,status="COMPLETED")
                    for j in job:
                        j.status='DELETED'
                        j.save()
            if status_flag1==True:
                job = Job.objects.filter(project_id=projectId, created_by=userId,action=1,status="COMPLETED")
                for j in job:
                    j.status='DELETED'
                    j.save()
                message="Success"
                status_code=status.HTTP_200_OK
                response_status=True
            else:
                message="Nothing to delete."
                status_code=status.HTTP_404_NOT_FOUND
                response_status=False
            response = JsonResponse(vars(ProjectResponse(message, status_code, response_status  , None)))
            response.status_code = status_code
            return response
        elif int(stage)==int(getAction.Hyperexpresivity.value):
            status_flag=storage_servicer.delete_folder(f'{S3_BUCKET_ROOT}/Project/{userId}/{projectId}/Stage2/')
            if status_flag==True:
                job = Job.objects.filter(project_id=projectId, created_by=userId, action=2,status="COMPLETED")
                for j in job:
                    j.status='DELETED'
                    j.save()
                message="Success"
                status_code=status.HTTP_200_OK
                response_status=True
            else:
                message="Nothing to delete."
                status_code=status.HTTP_404_NOT_FOUND
                response_status=False
            response = JsonResponse(vars(ProjectResponse(message, status_code, response_status  , None)))
            response.status_code = status_code
            return response
        else:
            response = JsonResponse(vars(ProjectResponse("Invalid stage provided.", status.HTTP_404_NOT_FOUND, False, None)))
            response.status_code = status.HTTP_404_NOT_FOUND
            return response
        
        
