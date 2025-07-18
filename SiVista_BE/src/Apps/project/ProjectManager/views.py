"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: views.py  
 * Description:  Django views that handle various API endpoints related to managing projects. Below is a breakdown of the key views and their functionality, with some improvement suggestions.
 *  
 * Author: Mansi Mahadik 
 * Created On: 17-12-2024
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
import re
from base64 import b64encode
from rest_framework.views import APIView
from rest_framework import status
from src.Apps.project.ProjectManager.models import Project, TechFileCatalog
from django.http import JsonResponse
from src.Apps.project.ProjectManager.serializer import CreateSerializer, ProjectSerializer, ProjectSerializer1, TechFileCatalogSerializer
from src.Services.StorageServices.StorageService import storage_servicer
from src.Services.ProjectService import *
from src.Services.EncryptDecryptService import decrypt_file_content, InvalidToken
from django.db.models import Q
from src.Services.JobService import save_tech_catalog_data
from django.db.models.functions import Coalesce
from src.Models.Project.ProjectResponse import ProjectResponse
from src.Models.Tech.TechFileCatalogResponse import TechFileCatalogResponse
from drf_yasg.utils import swagger_auto_schema
from concurrent.futures import ThreadPoolExecutor
from drf_yasg import openapi
from json import loads
import string
from django.http import FileResponse
from SiVista_BE.settings import S3_BUCKET_ROOT, VERSION
from django.core.cache import cache
import json

class Create(APIView):
    @swagger_auto_schema(
        operation_summary="Create a new project",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'projectName': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the project'),
                'projectType':openapi.Schema(type=openapi.TYPE_INTEGER, description="Type of project -->0->Regular,1->RL,2->200+ transistors"),
                'stageOneProjectId':openapi.Schema(type=openapi.TYPE_INTEGER, description='Stage I Result Project ID'),
                'selectedLayouts':openapi.Schema(type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(type=openapi.TYPE_STRING),description='Object of selected GDS'),
                'netlistMetadata':openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'fileName':openapi.Schema(type=openapi.TYPE_STRING, description='Name of the netlist file'),
                    'netlistType':openapi.Schema(type=openapi.TYPE_STRING, description='Details of cells'),
                    'cellSelections':openapi.Schema(type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(type=openapi.TYPE_OBJECT,properties={
                                            'cell_name':openapi.Schema(type=openapi.TYPE_STRING, description='Name of the cells'),
                                            'is_selected':openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Is cell selected or not')
                                        }), 
                                        description='Object of cell selection'),
                } ),
                'techMetadata': openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'fileName':openapi.Schema(type=openapi.TYPE_STRING, description='Name of the netlist file'),
                    'netlistType':openapi.Schema(type=openapi.TYPE_STRING, description='Details of cells')}),
                'action': openapi.Schema(type=openapi.TYPE_STRING, description='Action to perform'),
                'netlistFileContents':openapi.Schema(type=openapi.TYPE_STRING, description='Netlist ecvrypted file content'),
                'techFileContents':openapi.Schema(type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(type=openapi.TYPE_OBJECT,properties={
                                            'supportsVariations':openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Is cell selected or not'),
                                            'uiVisible':openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Is cell selected or not'),
                                            'name':openapi.Schema(type=openapi.TYPE_STRING, description='Name of the cells'),
                                            'displayName':openapi.Schema(type=openapi.TYPE_STRING, description='Name of the cells'),
                                            'data':openapi.Schema(type=openapi.TYPE_OBJECT, description="Data for each element of tech file.")}))},
            required=['projectName', 'netlistMetadata', 'techMetadata', 'action','netlistFileContents', 'techFileContents','supportsVariations','uiVisible', 'name','displayName','data']
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
        try:
            user_id = request.user_id  
            data = loads(request.body)
            serializer = CreateSerializer(data=data)
            if data.get('projectName', '').strip() == '':
                message = "The project name cannot be left blank. Please enter a valid project name."
                status_code = status.HTTP_400_BAD_REQUEST
                response_status = False
                response = JsonResponse(vars(ProjectResponse(message,status_code,response_status,None)))
                response.status_code=status_code
                return response
            if serializer.is_valid():
                message, status_code, response_status,data = serializer.validat(data, user_id)
                response = JsonResponse(vars(ProjectResponse(message,status_code,response_status,data)))
                response.status_code=status_code
                return response
            else:
                message = str(serializer.errors)
                response_status = False
                status_code = status.HTTP_400_BAD_REQUEST
                response = JsonResponse(vars(ProjectResponse(message,status_code,response_status,None)))
                response.status_code=status_code
                return response
        except Exception as e:
            message = f"There was an issue with the JSON request: {str(e)}. Please review the request and try again."
            response_status = False
            status_code = status.HTTP_400_BAD_REQUEST
            response = JsonResponse(vars(ProjectResponse(message,status_code,response_status,None)))
            response.status_code=status_code
            return response    

class ListProjects(APIView):
    @swagger_auto_schema(
        operation_summary="Getting the List of Projects",
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
    def get(self, request):
        user_id = request.user_id
        user = User.objects.get(id=user_id)
        if not user:
            response = JsonResponse(vars(ProjectResponse("You cannot view this!", status.HTTP_401_UNAUTHORIZED, False)))
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return response
        #projects = Project.objects.filter(created_by=user_id)
        projects = Project.objects.filter((Q(created_by_id=user) | Q(modified_by_id=user))).distinct().order_by(Coalesce('modified_date', 'created_date').desc(),'-created_date')
        if projects:
            serializer = ProjectSerializer(projects, many=True)
            response = JsonResponse(vars(ProjectResponse("Project list retrieved.", status.HTTP_200_OK, True, serializer.data)))
            response.status_code = status.HTTP_200_OK
            return response
        else:
            response = JsonResponse(vars(ProjectResponse("No projects created yet. Kindly create one project at least.", status.HTTP_200_OK, True)))
            response.status_code = status.HTTP_200_OK
            return response

class GetProject(APIView):
    @swagger_auto_schema(
        operation_summary="Get the details of Projects",
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
    def get(self, request, pid):
        project = Project.objects.filter(id=pid).first()
        user=User.objects.filter(id=request.user_id).first()
        if project:
            if user.is_staff==False:
                if project.created_by_id != user.id:  # TODO: check if user has permission to view this project
                    response= JsonResponse(vars(ProjectResponse("You cannot view this!", status.HTTP_401_UNAUTHORIZED, False)))
                    response.status_code=status.HTTP_401_UNAUTHORIZED
                    return response
            serializer = ProjectSerializer1(project)
            action=serializer.data['action']
            if action == 1 or action == 3:
                tech_path = f'{S3_BUCKET_ROOT}/Project/{project.created_by_id}/{pid}/Techfile/{project.tech_metadata['fileName']}'
                netlist_path = f'{S3_BUCKET_ROOT}/Project/{project.created_by_id}/{pid}/Netlist/{project.netlist_metadata['fileName']}'
                tech_file = self.get_file_content(tech_path)
                if tech_file is None:
                    response = JsonResponse(vars(ProjectResponse("Tech file not found.", status.HTTP_404_NOT_FOUND, False, None)))
                    response.status_code = status.HTTP_404_NOT_FOUND
                    return response
                tech_file = decrypt_file_content(tech_file)
                netlist_file = self.get_file_content(netlist_path)
                if netlist_file is None:
                    response = JsonResponse(vars(ProjectResponse("Netlist file not found.", status.HTTP_404_NOT_FOUND, False, None)))
                    response.status_code = status.HTTP_404_NOT_FOUND
                    return response
                netlist_file = decrypt_file_content(netlist_file)
                if netlist_file:
                    netlist_file=b64encode(netlist_file.encode('utf-8'))
                else:
                    response = JsonResponse(vars(ProjectResponse("Netlist file is empty.", status.HTTP_404_NOT_FOUND, False, None)))
                    response.status_code = status.HTTP_404_NOT_FOUND
                    return response
                project_details = serializer.data
                project_details['created_by'] = project.created_by.username
                project_details['modified_by'] = project.modified_by.username
                data = {
                    "project_details": project_details,
                    "netlistFileContent": netlist_file.decode('utf-8'),
                    "FileContent": loads(tech_file),
                }
                response = JsonResponse(vars(ProjectResponse("Project details retrieved.", status.HTTP_200_OK, True, data)))
                response.status_code = status.HTTP_200_OK
                return response
            elif action == 2:
                tech_path = f'{S3_BUCKET_ROOT}/Project/{project.created_by_id}/{pid}/Techfile/{project.tech_metadata['fileName']}'
                netlist_path = f'{S3_BUCKET_ROOT}/Project/{project.created_by_id}/{pid}/Netlist/{project.netlist_metadata['fileName']}'
                tech_file = self.get_file_content(tech_path)
                tech_file = decrypt_file_content(tech_file)
                netlist_file = self.get_file_content(netlist_path)
                netlist_file = decrypt_file_content(netlist_file.decode('utf-8'))
                if netlist_file:
                    netlist_file=b64encode(netlist_file.encode('utf-8'))
                else:
                    response = JsonResponse(vars(ProjectResponse("Netlist file is empty.", status.HTTP_404_NOT_FOUND, False, None)))
                    response.status_code = status.HTTP_404_NOT_FOUND
                    return response
                project_details = serializer.data
                stage1_project= Project.objects.filter(id=project_details['stage_one_project']).first()
                project_details['created_by'] = project.created_by.username
                project_details['modified_by'] = project.modified_by.username
                if stage1_project==None:
                    project_details['stage_one_project_name']=None
                else:
                    project_details['stage_one_project_name']=stage1_project.project_name
                data = {
                    "project_details": project_details,
                    "netlistFileContent": netlist_file.decode('utf-8'),
                    "FileContent": loads(tech_file),
                }
                response = JsonResponse(vars(ProjectResponse("Project details retrieved.", status.HTTP_200_OK, True, data)))
                response.status_code = status.HTTP_200_OK
                return response
            else:
                response = JsonResponse(vars(ProjectResponse("Invalid action provided.", status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
        else:
            response= JsonResponse(vars(ProjectResponse("Invalid project ID", status.HTTP_404_NOT_FOUND, False)))
            response.status_code = status.HTTP_404_NOT_FOUND
            return response
    def get_file_content(self, path):
        file = storage_servicer.get_file(path)
        return storage_servicer.read_file_response_content(file['response']) if file['success'] else None

class EditProject(APIView):
    @swagger_auto_schema(
        operation_summary="Edit the existing project",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'netlistMetadata': openapi.Schema(type=openapi.TYPE_OBJECT, description='Netlist metadata'),
                'techMetadata': openapi.Schema(type=openapi.TYPE_OBJECT, description='Tech metadata'),
                'netlistFileContents':openapi.Schema(type=openapi.TYPE_STRING, description='Edit Netlist'),
                'techFileContents':openapi.Schema(type=openapi.TYPE_OBJECT, properties={}, description='Edit Netlist'),
                'stageOneProjectId':openapi.Schema(type=openapi.TYPE_INTEGER, description='Stage I Result Project ID')
            },
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
    def patch(self, request, pid):
        new_data = request.data
        uid= request.user_id
        project = Project.objects.filter(pk=pid).first()  # TODO: Check if the user has the permissions to edit this project
        if project.created_by_id != uid:
            response = JsonResponse(vars(ProjectResponse("Your account does not have permission to make edits to this project.", status.HTTP_404_NOT_FOUND, False)))
            response.status_code = status.HTTP_404_NOT_FOUND
            return response 
        if not project:
            response = JsonResponse(vars(ProjectResponse("Invalid project ID", status.HTTP_404_NOT_FOUND, False)))
            response.status_code = status.HTTP_404_NOT_FOUND
            return response
        serializer = CreateSerializer(data={
            'projectName': project.project_name,
            'netlistMetadata': new_data.get('netlistMetadata', project.netlist_metadata),
            'techMetadata': new_data.get('techMetadata', project.tech_metadata),
            'action': project.action
        })
        if serializer.is_valid():
            result = edit_project(project, new_data, request.user_id)
            response = JsonResponse(vars(ProjectResponse(result['message'], result['status_code'], result['status'])))
            response.status_code = result['status_code']
            return response
        else:
            response = JsonResponse(vars(ProjectResponse("Invalid input data", status.HTTP_400_BAD_REQUEST, False)))
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response

class Stage1Ready(APIView):
    @swagger_auto_schema(
        operation_summary="List of project which contain stage 1 results in S3 bucket.",
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
    def get(self, request):
        if not request.user_id:
            response = JsonResponse(vars(ProjectResponse("Please log in", status.HTTP_404_NOT_FOUND, False, None)))
            response.status_code = status.HTTP_404_NOT_FOUND
            return response
        projects = Project.objects.filter(
            created_by_id=request.user_id,
            project_type=0,
            action=1,
            jobs__action=1,
            jobs__status='COMPLETED'
        ).distinct().order_by(Coalesce('modified_date', 'created_date').desc(),'-created_date')
        if projects:
            serializer = ProjectSerializer1(projects, many=True)
            for project in serializer.data:
                if 'created_date' in project:
                    # Parse the date and remove the time part
                    project['created_date'] = project['created_date'].split('T')[0]
                if 'modified_date' in project:
                    project['modified_date'] = project['modified_date'].split('T')[0]
            response = JsonResponse(vars(ProjectResponse("Project list retrieved.", status.HTTP_200_OK, True, serializer.data)))
            response.status_code = status.HTTP_200_OK
        else:
            message="No projects with Layouts to choose from. If you want to run the Hyperexpressivity flow, please create at least one project and run Layout Generation."
            response = JsonResponse(vars(ProjectResponse(message, status.HTTP_200_OK, True, None)))
            response.status_code = status.HTTP_200_OK
        return response

class CheckProject(APIView):
    @swagger_auto_schema(
        operation_summary="Validate project name",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'projectName': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the project'),
            },
            required=['projectName']
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
        userId=request.user_id
        data= request.data
        if data['projectName']== None:
            message="Project can't be blank..."
            status_code=status.HTTP_400_BAD_REQUEST
            response_status=False
            response = JsonResponse(vars(ProjectResponse(message,status_code,response_status)))
            response.status_code=status_code
            return response
        if re.search(r'\s{2,}', data['projectName']) or data['projectName'].startswith(' ') or data['projectName'].endswith(' '):
            message="Name contains more than one space or leading/trailing spaces."
            status_code=status.HTTP_400_BAD_REQUEST
            response_status=False
            response = JsonResponse(vars(ProjectResponse(message,status_code,response_status)))
            response.status_code=status_code
            return response
        if isinstance(data['projectName'], str):
                projectName = data['projectName']            
                special_characters = string.punctuation+' '
                if not all(char in special_characters for char in projectName):
                    if 101>len(projectName)>1:
                        if checkProject(userId,projectName) != True:
                            message="Success"
                            status_code=status.HTTP_200_OK
                            response_status=True
                            response = JsonResponse(vars(ProjectResponse(message,status_code,response_status)))
                            response.status_code=status_code
                            return response

                        else:
                            message="Project Already Exist."
                            status_code=status.HTTP_208_ALREADY_REPORTED
                            response_status=False
                            response=JsonResponse(vars(ProjectResponse(message,status_code,response_status)))
                            response.status_code=status_code
                            return response

                    else:
                            message="The project name should be between 2 and 100 characters."
                            status_code=status.HTTP_400_BAD_REQUEST
                            response_status=False
                            response = JsonResponse(vars(ProjectResponse(message,status_code,response_status)))
                            response.status_code=status_code
                            return response
                else:
                        message="Project name can't be only special characters"
                        status_code=status.HTTP_400_BAD_REQUEST
                        response_status=False
                        response = JsonResponse(vars(ProjectResponse(message,status_code,response_status)))
                        response.status_code=status_code
                        return response 
            
        else:
            message="Invalid Project Name"
            status_code=status.HTTP_400_BAD_REQUEST
            response_status=False
            response = JsonResponse(vars(ProjectResponse(message,status_code,response_status)))
            response.status_code=status_code
            return response
        
class DeleteProject(APIView):
    def delete(self, request, pid):
        project = Project.objects.filter(pk=pid).first()
        if project:
            if project.created_by_id != request.user_id:
                response = JsonResponse(vars(ProjectResponse("You cannot delete this project.", status.HTTP_401_UNAUTHORIZED, False)))
                response.status_code = status.HTTP_401_UNAUTHORIZED
                return response
            job=Job.objects.filter(project_id=pid)
            for job_unit in job:
                job_unit.delete()
            project.delete()
            storage_servicer.delete_folder(f'{S3_BUCKET_ROOT}/Project/{request.user_id}/{pid}')
            response = JsonResponse(vars(ProjectResponse("Project deleted successfully.", status.HTTP_200_OK, True)))
            response.status_code = status.HTTP_200_OK
            return response
        else:
            response = JsonResponse(vars(ProjectResponse("Invalid project ID", status.HTTP_404_NOT_FOUND, False)))
            response.status_code = status.HTTP_404_NOT_FOUND
            return response

class UploadProjectTech(APIView):
    @swagger_auto_schema(
        operation_summary="Upload project tech file",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'upload': openapi.Schema(
                    type=openapi.TYPE_FILE,
                    description='File to upload (tech format)',
                ),
            },
            required=['upload'],
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
        user = User.objects.filter(id=request.user_id).first()
        if 'upload' not in request.FILES or request.FILES['upload'].size == 0:
            message = "No file was uploaded. Please upload a valid file."
            response = JsonResponse(vars(ProjectResponse(message, status.HTTP_400_BAD_REQUEST, False)))
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response
        if request.FILES['upload'].size > 5242880: # 5242880 bytes = 5 mb upload limit
            message = "This file is too large. Please upload a file with a size less than 5 MB."
            response = JsonResponse(vars(ProjectResponse(message, status.HTTP_400_BAD_REQUEST, False)))
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response
        upload = request.FILES['upload']
        if not upload.name.endswith('.tech'):
            message = "Invalid file type. Please upload a .tech file."
            response = JsonResponse(vars(ProjectResponse(message, status.HTTP_400_BAD_REQUEST, False)))
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response
        tech_content = upload.read()
        file_size = upload.size / 1024
        name=upload.name
        check_present_file = FileInfo.objects.filter(name=name, type='TECH', dir='USER', status='ACTIVE', created_by=user).first()
        if check_present_file:
            message = f"A file with the name {name} already exists. Please rename your file and try again."
            response = JsonResponse(vars(ProjectResponse(message, status.HTTP_400_BAD_REQUEST, False)))
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response
        try:
            # Attempt to decrypt to validate the file
            _ = decrypt_file_content(tech_content)  # We're not using the result, just validating
           
        except InvalidToken:
            message = "Uploaded file is not encrypted with the correct key or is in plaintext."
            response = JsonResponse(vars(ProjectResponse(message, status.HTTP_400_BAD_REQUEST, False)))
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response
        response_status=storage_servicer.write_file(f'{S3_BUCKET_ROOT}/Techfile/{request.user_id}/{upload.name}',tech_content , 1)
        if response_status:
            file=FileInfo.objects.create(name=name,type='TECH',dir='USER',status='ACTIVE', filesize=file_size, created_by=user)
            if file:
                try:
                    key=f"get_all_files_{request.user.id}_TECH"
                    cache.delete(key)
                except redis.exceptions.ConnectionError as e:
                    print(f"Redis connection error: {e}")
                tech_content = decrypt_file_content(tech_content)
                tech_content = tech_content.replace("\n", "").replace("\t", "")
                try:
                    tech_content = loads(tech_content)
                    if not isinstance(tech_content, list):
                        message = "The file was not a valid tech file json array."
                        response = JsonResponse(vars(ProjectResponse(message, status.HTTP_400_BAD_REQUEST, False)))
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return response
                    tech_content = {"FileContent": tech_content}
                except:
                    message = "The file did not contain a valid json body."
                    response = JsonResponse(vars(ProjectResponse(message, status.HTTP_400_BAD_REQUEST, False)))
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return response
                if not file:
                    message = f"Failed to create a database record for {upload.name}. Please contact your database administrator."
                    response = JsonResponse(vars(ProjectResponse(message, status.HTTP_400_BAD_REQUEST, False)))
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return response
                message = "Techfile uploaded successfully."
                response = JsonResponse(vars(ProjectResponse(message, status.HTTP_200_OK, True, data=tech_content)))
                response.status_code = status.HTTP_200_OK
                return response
            else:
                storage_servicer.delete_file(f'{S3_BUCKET_ROOT}/Techfile/0/{upload.name}')
                response = JsonResponse(vars(ProjectResponse(f'Failed to save record for {upload.name}. Kindly co-ordinate with administrator.',status.HTTP_400_BAD_REQUEST,response_status)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
        else:
            response = JsonResponse(vars(ProjectResponse(f'Failed to save file {upload.name}.',status.HTTP_400_BAD_REQUEST,response_status)))
            response.status_code=status.HTTP_400_BAD_REQUEST
            return response
    
class ListTechFileCatalog(APIView):
    @swagger_auto_schema(
        operation_summary="Getting the List of Tech File Catalog",
        operation_description="Retrieve a list of completed Tech File Catalog entries for a specific project. The user must be authorized to access the project.",
        manual_parameters=[
            openapi.Parameter(
                'pid',
                openapi.IN_PATH,
                description="Project ID to fetch Tech File Catalog for",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
        ],
        responses={
            200: openapi.Response(
                description='Success - Tech File Catalog retrieved successfully',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example="Tech File Catalog retrieved successfully"),
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'data': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Catalog entry ID"),
                                    'project_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Associated Project ID"),
                                    'file_name': openapi.Schema(type=openapi.TYPE_STRING, description="Name of the tech file"),
                                    'status': openapi.Schema(type=openapi.TYPE_STRING, description="Status of the catalog entry"),
                                    'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Creation timestamp"),
                                    # Add other fields as per your TechFileCatalogSerializer
                                }
                            )
                        ),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, example=200)
                    }
                )
            ),
            400: openapi.Response(
                description='Bad Request - Invalid Project ID',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example="Invalid Project Id"),
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, example=400)
                    }
                )
            ),
            404: openapi.Response(
                description='Not Found - Project or Tech File Catalog not found',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example="No Project Found"),
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, example=404)
                    }
                )
            ),
            500: openapi.Response(
                description='Internal Server Error - Unexpected error occurred',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example="An error occurred: [error details]"),
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, example=500)
                    }
                )
            )
        }
    )
    def get(self, request, pid):
        try:
            # Convert pid to integer and validate
            project_id = int(pid)
            user_id = request.user_id
            if not isinstance(project_id, int):
                response = JsonResponse(vars(TechFileCatalogResponse(
                    "Project id should be integer." ,
                    status.HTTP_400_BAD_REQUEST,
                    False
                )))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            
             # Fetch the project
            project= Project.objects.filter(id=project_id).first()
            if not project:
                response = JsonResponse(vars(TechFileCatalogResponse(
                    "Catalog file not found.",
                    status.HTTP_400_BAD_REQUEST,
                    False
                )))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            
            # logged-in user owns the project
            if not project.created_by_id==user_id:
                response = JsonResponse(vars(TechFileCatalogResponse(
                    "You are not authorized to access this project.",
                    status.HTTP_401_UNAUTHORIZED,
                    False
                )))
                response.status_code = status.HTTP_401_UNAUTHORIZED
                return response

            # Check if project exists
            status_list = ['COMPLETED','RUNNING','QUEUED', 'UNPROCESSED','DELETED']
            techFileCatalogData = TechFileCatalog.objects.filter(
                    Q(project_id=pid) & Q(status__in = status_list)
            ).distinct().order_by('-created_at')
            if techFileCatalogData:
                serializer = TechFileCatalogSerializer(techFileCatalogData, many=True)
                response = JsonResponse(vars(TechFileCatalogResponse(
                    "Tech File Catalog retrieved successfully.",
                    status.HTTP_200_OK,
                    True,
                    serializer.data
                )))
                response.status_code = status.HTTP_200_OK
                return response
            else:
                # Fetch the project
                response = JsonResponse(vars(TechFileCatalogResponse(
                    "Catalog file not found.",
                    status.HTTP_400_BAD_REQUEST,
                    False
                )))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            
        except Exception as e:
            response = JsonResponse(vars(TechFileCatalogResponse(
                f"An error occurred: {str(e)}",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                False
            )))
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return response
        
class GetTechFileCatalogData(APIView):
    @swagger_auto_schema(
        operation_summary="Get data for given tech file",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'FileName': openapi.Schema(type=openapi.TYPE_STRING, description='Netlist Filename with .tech extension'),
                'FileType': openapi.Schema(type=openapi.TYPE_STRING, description='Netlist File Type'),
                'TimeStamp': openapi.Schema(type=openapi.TYPE_STRING, description='File creation time stamp')
            },
            required=['FileName', 'FileType']
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
        try:
            user_id=request.user_id
            json_data = loads(request.body)
            tech_id=json_data["techId"]
            if tech_id==None:
                response = JsonResponse(vars(TechFileCatalogResponse(f'Invalid tech id.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if not tech_id:
                response = JsonResponse(vars(TechFileCatalogResponse(f'Missing {tech_id} in request.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if not isinstance(tech_id, int):
                response = JsonResponse(vars(TechFileCatalogResponse(f'Tech ID must be integer.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            status_list = ['COMPLETED','RUNNING','QUEUED', 'UNPROCESSED','DELETED']
            data = TechFileCatalog.objects.filter(id=tech_id,status__in=status_list).first()
            if not data:
                response = JsonResponse(vars(TechFileCatalogResponse(f'Tech File not found in catalog.', status.HTTP_404_NOT_FOUND, False, None)))
                response.status_code = status.HTTP_404_NOT_FOUND
                return response
            if data.created_by_id != user_id:
                response = JsonResponse(vars(TechFileCatalogResponse(f'You cannot view this file.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            response = JsonResponse(vars(TechFileCatalogResponse("Tech File Catalog.", status.HTTP_200_OK, True, data.tech_data)))
            response.status_code = status.HTTP_200_OK
            return response
        except TechFileCatalog.DoesNotExist:
            message = "Tech File Catalog not found."
            response_status = False
            status_code = status.HTTP_404_NOT_FOUND
            response = JsonResponse(vars(TechFileCatalogResponse(message,status_code,response_status)))
            response.status_code=status_code
            return response
        except Exception as e:
            message = f"There was an issue with the JSON request: {str(e)}. Please review the request and try again."
            response_status = False
            status_code = status.HTTP_400_BAD_REQUEST
            response = JsonResponse(vars(TechFileCatalogResponse(message,status_code,response_status)))
            response.status_code=status_code
            return response 
class DownloadTechFile(APIView):
    @swagger_auto_schema(
        operation_summary="Get data for given tech file",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='File ID'),
                'file_name': openapi.Schema(type=openapi.TYPE_OBJECT, description='Tech file name'),
                'projectId': openapi.Schema(type=openapi.TYPE_INTEGER, description='Project ID'),
            },
            required=['FileName', 'FileType']
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
        try:
            # Parse request body
            json_data = loads(request.body)
            tech_file_id = json_data.get("id")
            project_id = json_data.get("project_id")
            if not project_id:
                response = JsonResponse(vars(ProjectResponse(f'Invalid project id.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if not isinstance(project_id, int):
                response = JsonResponse(vars(ProjectResponse(f'Project id must be integer.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            project = Project.objects.filter(id=project_id).first()
            if not project:
                response = JsonResponse(vars(ProjectResponse(f'Project not found.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if not project.created_by_id == request.user_id:
                response = JsonResponse(vars(ProjectResponse(f'You cannot download this file.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if not json_data.get("file_name"):
                response = JsonResponse(vars(ProjectResponse(f'Invalid file name.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if not isinstance(json_data['file_name'], str):
                response = JsonResponse(vars(ProjectResponse(f'File name must be string.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if json_data.get("file_name").endswith('.tech')==False:
                response = JsonResponse(vars(ProjectResponse(f'File name must end with .tech.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if not tech_file_id:
                response = JsonResponse(vars(ProjectResponse(f'Invalid file id.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if not isinstance(tech_file_id, int):
                response = JsonResponse(vars(ProjectResponse(f'Tech file id must be integer.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            # Fetch tech file from DB
            try:
                tech_file = TechFileCatalog.objects.get(id=tech_file_id)
            except TechFileCatalog.DoesNotExist:
                response = JsonResponse(vars(ProjectResponse('Tech file not found.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_200_OK
                return response
            file_content = tech_file.tech_data['FileContent']  # Assuming field name is 'tech_data'
            file_content = json.dumps(file_content)
            file_content = encrypt_file_content(file_content)
            file_name = json_data.get("file_name", f"tech_file_{tech_file_id}.tech")
            # Prepare in-memory zip
            response = FileResponse(file_content.decode('utf-8'), as_attachment=True, filename=file_name)
            response['Content-Type'] = 'application/octet-stream'
            response['X-Filename'] = file_name
            response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition, X-Filename'
            return response
        except Exception as e:
            response = JsonResponse(vars(ProjectResponse(f'Internal Server Error: {str(e)}', status.HTTP_500_INTERNAL_SERVER_ERROR, False, None)))
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return response
        
class RenameCatalogTechFile(APIView):
    @swagger_auto_schema(
        operation_summary="Rename Tech File",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'techId': openapi.Schema(type=openapi.TYPE_INTEGER, description='Tech file ID'),
                'projectId': openapi.Schema(type=openapi.TYPE_INTEGER, description='Project ID'),
                'newName': openapi.Schema(type=openapi.TYPE_STRING, description='New name for the tech file'),
            },
            required=['techId', 'newName', ]
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
        try:
            user_id = request.user_id
            json_data = loads(request.body)
            tech_file_id = json_data.get("techId")
            project_id = json_data.get("projectId")
            new_name = json_data.get("newName")
            if not project_id:
                response = JsonResponse(vars(ProjectResponse(f'Invalid project id.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if not isinstance(project_id, int):
                response = JsonResponse(vars(ProjectResponse(f'Project id must be integer.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            project = Project.objects.filter(id=project_id).first()
            if not project:
                response = JsonResponse(vars(ProjectResponse(f'Project not found.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if not project.created_by_id == user_id:
                response = JsonResponse(vars(ProjectResponse(f'You cannot rename this file.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if not tech_file_id:
                response = JsonResponse(vars(ProjectResponse(f'Invalid tech file id.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if not isinstance(tech_file_id, int):
                response = JsonResponse(vars(ProjectResponse(f'Tech file id must be integer.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            # if not old_name:
            #     response = JsonResponse(vars(ProjectResponse(f'Invalid old name.', status.HTTP_400_BAD_REQUEST, False, None)))
            #     response.status_code = status.HTTP_400_BAD_REQUEST
            #     return response
            # if not isinstance(old_name, str):
            #     response = JsonResponse(vars(ProjectResponse(f'Old name must be string.', status.HTTP_400_BAD_REQUEST, False, None)))
            #     response.status_code = status.HTTP_400_BAD_REQUEST
            #     return response
            # if not old_name.endswith('.tech'):
            #     response = JsonResponse(vars(ProjectResponse(f'Old name must end with .tech.', status.HTTP_400_BAD_REQUEST, False, None)))
            #     response.status_code = status.HTTP_400_BAD_REQUEST
            #     return response
            if not isinstance(new_name, str):
                response = JsonResponse(vars(ProjectResponse(f'New name must be string.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if not bool(re.fullmatch(r'[A-Za-z0-9_]+', new_name)):
                response = JsonResponse(vars(ProjectResponse('Invalid file name. Only alphabetic characters, numbers and underscores (_) are allowed. Please remove special characters', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            tech_entries = TechFileCatalog.objects.filter(file_name=f'{new_name}.tech', created_by_id=user_id,project_id=project_id).first()
            if tech_entries:
                response = JsonResponse(vars(ProjectResponse(f'Tech file with this name already exists.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            tech_file = TechFileCatalog.objects.filter(id=tech_file_id).first()
            if f'{new_name}.tech' == tech_file.file_name:
                response = JsonResponse(vars(ProjectResponse(f'New name must be different from old name.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            # Fetch tech file from DB
            if not tech_file:
                response = JsonResponse(vars(ProjectResponse('Tech file not found.', status.HTTP_404_NOT_FOUND, False, None)))
                response.status_code = status.HTTP_404_NOT_FOUND
                return response
            # Check if the user is authorized to rename this file
            if tech_file.created_by_id != user_id:
                response = JsonResponse(vars(ProjectResponse('You cannot rename this file.', status.HTTP_401_UNAUTHORIZED, False, None)))
                response.status_code = status.HTTP_401_UNAUTHORIZED
                return response
            # Rename the file in the database
            tech_file.file_name = f'{new_name}.tech'
            tech_file.save()
            message = "Tech file renamed successfully."
            response = JsonResponse(vars(ProjectResponse(message, status.HTTP_200_OK, True)))
            response.status_code = status.HTTP_200_OK
            return response
        except Exception as e:
            message = f"Internal Server Error: {str(e)}"
            response = JsonResponse(vars(ProjectResponse(message, status.HTTP_500_INTERNAL_SERVER_ERROR, False)))
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return response
        
class SaveCatalogTechFile(APIView):
    @swagger_auto_schema(
        operation_summary="Save Tech File Catalog",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'projectId': openapi.Schema(type=openapi.TYPE_INTEGER, description='Project ID'),
                'techData': openapi.Schema(type=openapi.TYPE_OBJECT, description='Tech file data'),
                'file_name': openapi.Schema(type=openapi.TYPE_STRING, description='Tech file name')
            },
            required=['projectId', 'techData', 'file_name' ]
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
        try:
            user_id = request.user_id
            json_data = loads(request.body)
            tech_data = json_data.get("techData")
            project_id = json_data.get("projectId")
            file_name = json_data.get("file_name")
            if not project_id:
                response = JsonResponse(vars(ProjectResponse(f'Invalid project id.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if  not isinstance(project_id, int):
                response = JsonResponse(vars(ProjectResponse(f'Project id must be integer.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if not isinstance(file_name, str):
                response = JsonResponse(vars(ProjectResponse(f'File name must be string.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if not bool(re.fullmatch(r'[A-Za-z0-9_]+', file_name)):
                response = JsonResponse(vars(ProjectResponse('Invalid file name. Only alphabetic characters, numbers and underscores (_) are allowed. Please remove special characters', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            project = Project.objects.filter(id=project_id).first()
            if not project:
                response = JsonResponse(vars(ProjectResponse(f'Project not found.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if not project.created_by_id == user_id:
                response = JsonResponse(vars(ProjectResponse(f'You cannot save this file.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if not tech_data:
                response = JsonResponse(vars(ProjectResponse(f'Invalid tech data.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if not isinstance(tech_data, dict):
                response = JsonResponse(vars(ProjectResponse(f'Tech data must be a object.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            fileName = TechFileCatalog.objects.filter(project_id=project, created_by_id=user_id,file_name=f'{file_name}.tech').first()
            if fileName:
                response = JsonResponse(vars(ProjectResponse(f'Tech file with this name already exists.', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if tech_data:
                    existing_entries = TechFileCatalog.objects.filter(
                        project_id=project,
                        created_by_id=user_id
                    )
            tech_data_str = json.dumps(tech_data, sort_keys=True)
            is_duplicate = False
            for entry in existing_entries:
                existing_tech_data_str = json.dumps(entry.tech_data, sort_keys=True)
                if existing_tech_data_str == tech_data_str:
                    is_duplicate = True
                    break
            if is_duplicate:
                message = f"A tech file with the name '{entry.file_name}'.tech already exists in the catalog. Would you like to rename the new file {file_name}?"
                response = JsonResponse(vars(ProjectResponse(message, status.HTTP_208_ALREADY_REPORTED, False, {"techId":entry.id})))
                response.status_code = status.HTTP_208_ALREADY_REPORTED
                return response
            if not is_duplicate:
                data={}
                data['action'] = 1
                data['cells'] = None
                job = None
                jobStatus='UNPROCESSED'
                saveTechCatalogData = save_tech_catalog_data(project, data, job, tech_data, f'{file_name}.tech',jobStatus, request)
                if not saveTechCatalogData:
                    response = JsonResponse(vars(ProjectResponse('Failed to save tech file.', status.HTTP_400_BAD_REQUEST, False, None)))
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return response
                message = "Tech file saved successfully."
                response = JsonResponse(vars(ProjectResponse(message, status.HTTP_200_OK, True)))
                response.status_code = status.HTTP_200_OK
                return response
            response = JsonResponse(vars(ProjectResponse('Failed to save tech file.', status.HTTP_400_BAD_REQUEST, False, None)))
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response
        except Exception as e:
            message = f"Internal Server Error: {str(e)}"
            response = JsonResponse(vars(ProjectResponse(message, status.HTTP_500_INTERNAL_SERVER_ERROR, False)))
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return response
        except json.JSONDecodeError:
            message = "Invalid JSON format in tech data."
            response = JsonResponse(vars(ProjectResponse(message, status.HTTP_400_BAD_REQUEST, False)))
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response
        except Exception as e:
            message = f"Internal Server Error: {str(e)}"
            response = JsonResponse(vars(ProjectResponse(message, status.HTTP_500_INTERNAL_SERVER_ERROR, False)))
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return response
        finally:
            # Clean up any resources if needed
            pass

from rest_framework.response import Response
from rest_framework import status
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import multiprocessing
from itertools import islice
from rest_framework.exceptions import APIException


def get_max_workers(default=10, scale=5, cap=100):
    try:
        cpu_cores = multiprocessing.cpu_count()
        # Scale it (use higher multiple for I/O-bound workloads)
        calculated = cpu_cores * scale
        # Pick the safe lower of calculated, cap, and default fallback
        return min(calculated, cap)
    except NotImplementedError:
        return default  # Fallback
    
MAX_WORKERS = get_max_workers()
CHUNK_SIZE = 100

def chunked_iterable(iterable, size):
    it = iter(iterable)
    return iter(lambda: list(islice(it, size)), [])

def process_files_in_parallel(file_list, process_function):
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for chunk in chunked_iterable(file_list, CHUNK_SIZE):
            futures = [executor.submit(process_function, f) for f in chunk]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Processing error: {e}")

class MigrateApplication(APIView):
    def process_tech_file(self, file_name):
        try:
            msg, file_response, _, success = storage_servicer.get_tech_netlist_data(file_name, "USER", "Techfile", False)
            if success:
                try:
                    # This will throw if not properly encrypted
                    decrypt_file_content(file_response)
                    print(f"File is already encrypted. Skipping encryption for {file_name}.")
                    result = True
                except Exception:
                    content = tech_migrater({"FileContent": file_response})
                    # Not encrypted, proceed to encrypt
                    encrypted = encrypt_file_content(json.dumps(content, indent=4))
                    result = storage_servicer.write_file(file_name, encrypted, 1)
                return result
        except Exception as e:
            print(f"Techfile error {file_name}: {e}")
            return False

    def process_netlist_file(self, file_name):
        try:
            msg, file_response, _, success = storage_servicer.get_tech_netlist_data(file_name, "USER", "Netlist", False)
            if success:
                try:
                    # This will throw if not properly encrypted
                    decrypt_file_content(file_response)
                    print(f"File is already encrypted. Skipping encryption for {file_name}.")
                    result = True
                except Exception:
                    # Not encrypted, proceed to encrypt
                    encrypted = encrypt_file_content(file_response.decode('utf-8'))
                    result = storage_servicer.write_file(file_name, encrypted, 1)
                return result
        except Exception as e:
            print(f"Netlist error {file_name}: {e}")
            return False

    def process_folder(self, folder, kind):
        path = f'{S3_BUCKET_ROOT}/{kind}/{folder}/'
        files = storage_servicer.list_files(path)
        print(f"Processing {kind} folder: {folder} with files: {files}")
        ext = '.tech' if kind == "Techfile" else '.spice'
        
        target_files = [f for f in files if f.endswith(ext)]
        process_function = self.process_tech_file if kind == "Techfile" else self.process_netlist_file

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for chunk in chunked_iterable(target_files, CHUNK_SIZE):
                futures = [executor.submit(process_function, f) for f in chunk]
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        if not result:
                            print(f"Processing failed for one of the files.")
                    except Exception as e:
                        print(f"Error in processing {kind} file: {e}")
    def process_project(self, project):
        try:
            tech_path = f'{S3_BUCKET_ROOT}/Project/{project.created_by_id}/{project.id}/Techfile/{project.tech_metadata["fileName"]}'
            netlist_path = f'{S3_BUCKET_ROOT}/Project/{project.created_by_id}/{project.id}/Netlist/{project.netlist_metadata["fileName"]}'

            tech_success = self.process_tech_file(tech_path)
            netlist_success = self.process_netlist_file(netlist_path)

            if tech_success and netlist_success:
                project.version = VERSION
                return ('success', project)
            else:
                return ('fail', project)
        except Exception as e:
            print(f"Project {project.id} error: {e}")
            return ('fail', project)

    def get(self, request):
        try:
            projects = Project.objects.exclude(version=VERSION)
            if not projects.exists():
                return Response({
                    'message': 'Application already migrated.',
                    'status': True,
                    'data': {}
                }, status=status.HTTP_200_OK)
            # fileinfo_qs = FileInfo.objects.filter(dir='GLOBAL', type = 'TECH').exclude(status='DELETED')
            # if fileinfo_qs.exists():
            #     storage_servicer.delete_folder(f'{S3_BUCKET_ROOT}/Techfile/0')
            #     fileinfo_qs.update(status='DELETED')
            tech_folders = [f for f in storage_servicer.list_folders(f'{S3_BUCKET_ROOT}/Techfile/') if f != "0"]
            netlist_folders = storage_servicer.list_folders(f'{S3_BUCKET_ROOT}/Netlist/')
            for folder in tech_folders:
                self.process_folder(folder, "Techfile")
            for folder in netlist_folders:
                self.process_folder(folder, "Netlist")
               
            success_projects = []
            failed_projects = []

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = [executor.submit(self.process_project, project) for project in projects]
                for future in as_completed(futures):
                    status_str, proj = future.result()
                    if status_str == 'success':
                        success_projects.append(proj)
                    else:
                        failed_projects.append(proj)
            if success_projects:
                # Only update version for successfully processed projects
                Project.objects.bulk_update(success_projects, ['version'])
            
            return Response({
                'message': 'Migration process completed successfully.',
                'status': True,
                'data': {
                    'success_projects': [p.id for p in success_projects],
                    'failed_projects': [p.id for p in failed_projects]
                }
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'message': f'Migration error: {str(e)}',
                'status': False,
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)
# curl --location 'http://127.0.0.1:8000/project/migrate/'

class DeleteCatalogTechFile(APIView):
    def delete(self, request, pid):
        try:
            techCatalogProject = TechFileCatalog.objects.get(pk=pid)
            if not techCatalogProject:
                response = JsonResponse(vars(ProjectResponse("Invalid project ID",status.HTTP_404_NOT_FOUND,False)))
                response.status_code = status.HTTP_404_NOT_FOUND
                return response
            if techCatalogProject.created_by_id != request.user_id:
                response = JsonResponse(vars(ProjectResponse("You can not delete this Tech File",status.HTTP_401_UNAUTHORIZED,False)))
                response.status_code = status.HTTP_401_UNAUTHORIZED
                return response
            techCatalogProject.delete()
            response = JsonResponse(vars(ProjectResponse("Catalog file deleted successfully.",status.HTTP_200_OK,True)))
            response.status_code = status.HTTP_200_OK
            return response
        except Exception as e:
            print(e)
            response = JsonResponse(vars(ProjectResponse("Failed to delete",status.HTTP_409_CONFLICT,False)))
            response.status_code = status.HTTP_409_CONFLICT
            return response
            

