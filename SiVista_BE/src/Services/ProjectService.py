# /***************************************************************************  
#  * Copyright © 2024 SiClarity, Inc.  
#  * All rights reserved.  
#  *  
#  * File Name: ProjectService.py  
#  * Description: Service to create project and edit project
#  *  
#  * Author: Mansi Mahadik 
#  * Created On: 17-12-2024
#  *  
#  * This source code and associated materials are the property of SiClarity, Inc.  
#  * Unauthorized copying, modification, distribution, or use of this software,  
#  * in whole or in part, is strictly prohibited without prior written permission  
#  * from SiClarity, Inc.  
#  *  
#  * Disclaimer:  
#  * This software is provided "as is," without any express or implied warranties,  
#  * including but not limited to warranties of merchantability, fitness for a  
#  * particular purpose, or non-infringement. In no event shall SiClarity, Inc.  
#  * be held liable for any damages arising from the use of this software.  
#  *  
#  * SiClarity and its logo are trademarks of SiClarity, Inc.  
#  *  
#  * For inquiries, contact: support@siclarity.com  
#  ***************************************************************************/
import re
from src.Apps.project.ProjectManager.models import *
from enum import Enum
from SiVista_BE.settings import *
from rest_framework import status
from src.Services.StorageServices.StorageService import storage_servicer
from src.Services.NetlistService import extract_subckt
from src.Services.EncryptDecryptService import encrypt_file_content
from django.db.models import Case, When, Value, F
from django.db.models.functions import Coalesce
from SiVista_BE.settings import S3_BUCKET_ROOT
from functools import lru_cache
from json import dumps
import concurrent.futures
import base64
import pandas as pd
import numpy as np
import time

class getAction(Enum):
    Layout=1
    Hyperexpresivity=2

thumbnail_suffix = {
    1: 'optimizedGDS',
    2: 'permutations'
}

def insert_project(user_id,data):
    projectName=re.sub(r'\s+', ' ', data['projectName'].strip())
    netlist_file=(data['netlistMetadata'])['fileName']
    tech_file=(data['techMetadata'])['fileName']
    if data['netlistMetadata']['fileName']==None and not isinstance(data['netlistMetadata']['fileName'],str):
        message="The netlist file name is missing or invalid. Please provide a valid string value for 'netlistFileName'."
        status_code=status.HTTP_400_BAD_REQUEST
        response_status=False
        return message,status_code,response_status,None
    if data['techMetadata']['fileName']==None and not isinstance(data['techMetadata']['fileName'],str):
        message="The tech file name is missing or invalid. Please provide a valid string value for 'techFileName'."
        status_code=status.HTTP_400_BAD_REQUEST
        response_status=False
        return message,status_code,response_status,None
    if((not netlist_file.lower().endswith('.spice')) or (not tech_file.lower().endswith('.tech'))):
        message="The file extension is incorrect. Please select a .spice file for the netlist and a .tech file for the PDK. "
        status_code=status.HTTP_400_BAD_REQUEST
        response_status=False
        return message, status_code, response_status,None
    project_type=data['projectType']
    project_type_list=ProjectType.objects.all()
    type_list=project_type_list.values_list('type',flat=True)
    if project_type in list(type_list): 
        pass
    else:
        message="Invalid Project type."
        status_code=status.HTTP_400_BAD_REQUEST
        response_status=False
        return message,status_code,response_status,None
    if checkProject(user_id, projectName) != True:
        user=User.objects.get(id=user_id)
        selected_values = getAction.Layout.value | getAction.Hyperexpresivity.value
        if ((getAction.Layout.value == data['action']) or (selected_values == data['action'])):
            netlist_content=(base64.b64decode(data['netlistFileContents'])).decode('utf-8')
            tech_content=dumps(data['techFileContents'])
            netlist_content = encrypt_file_content(netlist_content)
            tech_content = encrypt_file_content(dumps(data['techFileContents']))
            action=data['action']
            if not isinstance(project_type,int) or project_type==None:
                message="Project type is not valid."
                status_code=status.HTTP_400_BAD_REQUEST
                response_status=False
                return message,status_code,response_status,None
            if selected_values == data['action']:
                if int(project_type) != 0:
                    message=f"Project type {project_type} is not allowd for this project."
                    status_code=status.HTTP_400_BAD_REQUEST
                    response_status=False
                    return message,status_code,response_status,None
            (data['netlistMetadata'])['fileName']=netlist_file
            (data['techMetadata'])['fileName']=tech_file
            result=Project.objects.create(project_name=projectName,netlist_metadata=data['netlistMetadata'], tech_metadata=data['techMetadata'],action=action,created_by=user, modified_by=user,selectedLayouts=None, project_type=project_type,version=int(VERSION))
            result.save()
            if data['action']==selected_values:
                stage_one_project_instance = Project.objects.get(id=result.id)  # Get the instance
                result.stage_one_project = stage_one_project_instance.id 
            filepath1=f"{S3_BUCKET_ROOT}/Netlist/{user_id}/{projectName}_{netlist_file}"
            filepath2=f"{S3_BUCKET_ROOT}/Project/{user_id}/{result.id}/Netlist/{netlist_file}"
            filepath3=f"{S3_BUCKET_ROOT}/Techfile/{user_id}/{projectName}_{tech_file}"
            filepath4=f"{S3_BUCKET_ROOT}/Project/{user_id}/{result.id}/Techfile/{tech_file}"
            # Upload netlist file to S3
            if storage_servicer.write_file(filepath1, netlist_content, 1):
                # Fetch the file size from S3
                netlist_size = storage_servicer.get_bucket_file_size(filepath1)
                if netlist_size != -1:
                    # Create FileInfo record
                    name = f'{projectName}_{netlist_file}'
                    file1 = FileInfo.objects.create(name=name, type='NETLIST', dir='USER', status='ACTIVE', filesize=netlist_size, created_by=user)
                    if not file1:
                        result.delete()
                        storage_servicer.delete_file(filepath2)
                        message = "File record not created for Netlist."
                        status_code = status.HTTP_404_NOT_FOUND
                        response_status = False
                        return message, status_code, response_status, None
                else:
                    result.delete()
                    message = "Could not fetch the netlist file size. Please check the process and try again."
                    status_code = status.HTTP_404_NOT_FOUND
                    response_status = False
                    return message, status_code, response_status, None
            else:
                result.delete()
                message = "The netlist file could not be created. Please check the process and try again."
                status_code = status.HTTP_404_NOT_FOUND
                response_status = False
                return message, status_code, response_status, None

            # Upload additional copies of the netlist file if needed
            if not storage_servicer.write_file(filepath2, netlist_content, 1):
                result.delete()
                message = "The netlist file could not be created. Please check the process and try again."
                status_code = status.HTTP_404_NOT_FOUND
                response_status = False
                return message, status_code, response_status, None

            # Upload tech file to S3
            if storage_servicer.write_file(filepath3, tech_content, 1):
                # Fetch the file size from S3
                tech_size = storage_servicer.get_bucket_file_size(filepath3)
                if tech_size != -1:
                    # Create FileInfo record
                    name = f'{projectName}_{tech_file}'
                    file2 = FileInfo.objects.create(name=name, type='TECH', dir='USER', status='ACTIVE', filesize=tech_size, created_by=user)
                    if not file2:
                        result.delete()
                        storage_servicer.delete_file(filepath1)
                        storage_servicer.delete_file(filepath2)
                        storage_servicer.delete_file(filepath3)
                        storage_servicer.delete_file(filepath4)
                        message="File record not created for Tech."
                        status_code=status.HTTP_404_NOT_FOUND
                        response_status=False
                        return message,status_code,response_status,None
                else:
                    result.delete()
                    message = "Could not fetch the tech file size. Please check the process and try again."
                    status_code = status.HTTP_404_NOT_FOUND
                    response_status = False
                    return message, status_code, response_status, None
            else:
                result.delete()
                message = "The tech file could not be created. Please check the process and try again."
                status_code = status.HTTP_404_NOT_FOUND
                response_status = False
                return message, status_code, response_status, None

            # Upload additional copies of the tech file if needed
            if not storage_servicer.write_file(filepath4, tech_content, 1):
                file1.delete()
                file2.delete()
                result.delete()
                message="The tech file could not be created. Please check the process and try again."
                status_code=status.HTTP_404_NOT_FOUND
                response_status=False
                return message,status_code,response_status,None
            file1.save()
            file2.save()
            result.save()
            message="The project has been successfully created."
            status_code=status.HTTP_200_OK
            response_status=True
            return message,status_code,response_status,{'projectId':result.id}
        elif getAction.Hyperexpresivity.value == data['action']:
            if 'selectedLayouts' not in data:
                message="stage 1 Project selected layouts missing."
                status_code=status.HTTP_400_BAD_REQUEST
                response_status=False
                return message, status_code, response_status,None
            if not isinstance(data['selectedLayouts'], list):
                message="selectedLayouts must be array."
                status_code=status.HTTP_400_BAD_REQUEST
                response_status=False
                return message, status_code, response_status,None
            # if data['selectedLayouts'] == []:
            #     message="selectedLayouts must contain at least one value."
            #     status_code=status.HTTP_400_BAD_REQUEST
            #     response_status=False
            #     return message, status_code, response_status,None
            if 'stageOneProjectId' not in data:
                message="stage 1 Project Id missing in given request."
                status_code=status.HTTP_400_BAD_REQUEST
                response_status=False
                return message, status_code, response_status,None
            if not isinstance(data['stageOneProjectId'], int):
                message="stage 1 Project Id must be integer value."
                status_code=status.HTTP_400_BAD_REQUEST
                response_status=False
                return message, status_code, response_status,None
            stageProject = Project.objects.filter(id=data['stageOneProjectId']).first()
            completed_job = Job.objects.filter(project_id=data['stageOneProjectId'], status='COMPLETED').first()
            if completed_job:
                cells=completed_job.cells
            else:
                message="Stage 1 results are not available for this project."
                status_code=status.HTTP_400_BAD_REQUEST
                response_status=False
                return message, status_code, response_status,None
            if stageProject == None:
                message="Stage 1 results are not available for this project."
                status_code=status.HTTP_400_BAD_REQUEST
                response_status=False
                return message, status_code, response_status,None
            basepath=f'{S3_BUCKET_ROOT}/Project/{user_id}/{data['stageOneProjectId']}/Stage1/'
            file_list = []
            for cell in cells:
                try:
                    pexbasepath=f'{basepath}{cell}/{cell}_predictions/{cell}_GDS_PEX_PREDICTION_ML.csv'
                    pex_df = storage_servicer.fetch_csv(pexbasepath)
                    file_list.extend(pex_df['File'].tolist())
                except:
                    pass
            missing_layouts = set(data['selectedLayouts']) - set(file_list)
            if missing_layouts:
                message = f"Layout {', '.join(missing_layouts)} is are not available."
                status_code = status.HTTP_400_BAD_REQUEST
                response_status = False
                return message, status_code, response_status, None
            if stageProject.project_type!=0:
                message=f"Project type {project_type} is not allowd for this project."
                status_code=status.HTTP_400_BAD_REQUEST
                response_status=False
                return message,status_code,response_status,None
            if project_type !=0:
                message=f"Project type {project_type} is not allowd for this project."
                status_code=status.HTTP_400_BAD_REQUEST
                response_status=False
                return message,status_code,response_status,None
            action=data['action']
            (data['netlistMetadata'])['fileName']=f'{netlist_file}'
            (data['techMetadata'])['fileName']=f'{tech_file}'
            result=Project.objects.create(project_name=projectName,action=action,created_by=user,netlist_metadata=data['netlistMetadata'], tech_metadata=data['techMetadata'],stage_one_project=data['stageOneProjectId'], modified_by=user, selectedLayouts=data['selectedLayouts'],project_type=stageProject.project_type,version=int(VERSION))
            source_path=f'{S3_BUCKET_ROOT}/Project/{user_id}/{data['stageOneProjectId']}/'
            destination_path=f'{S3_BUCKET_ROOT}/Project/{user_id}/{result.id}/'
            responses = []
            for folder_name in ['Stage1', 'Netlist', 'Techfile']:
                remote_source_path = f'{source_path}{folder_name}/'
                remote_destination_path = f'{destination_path}{folder_name}/'
                response_status = storage_servicer.move_folder(remote_source_path, remote_destination_path)
                responses.append(response_status)
            if sum(responses) == 3:
                result.save()
                message="The project has been successfully created."
                status_code=status.HTTP_200_OK
                response_status=True
                return message,status_code,response_status,{'projectId':result.id}
            else:
                result.delete()
                status_code=status.HTTP_404_NOT_FOUND
                message = 'Could not move all the folders'
                return message,status_code,False,None
        else:
            message= "The action provided is not valid. Please try a valid action."
            status_code=status.HTTP_400_BAD_REQUEST
            response_status=False
            return message, status_code, response_status, None
    else:     
        message="The project name already exists. Please choose a different name."
        status_code=status.HTTP_208_ALREADY_REPORTED
        response_status=False
        return message,status_code,response_status,None


def edit_project(project, new_data, modifier_id):
    if not User.objects.filter(id=modifier_id).first():
        return {
            'message': "The user ID you provided is invalid. Please check and try again.",
            'status_code': status.HTTP_404_NOT_FOUND,
            'status': False
        } 
    if project.action==getAction.Layout.value or project.action==(getAction.Layout.value|getAction.Hyperexpresivity.value):     
        if('netlistFileContents' in new_data) and ('netlistMetadata' in new_data) :
            input_cells = [i['cell_name'] for i in new_data.get('netlistMetadata', project.netlist_metadata)['cellSelections']]
            netlist_cells = extract_subckt(base64.b64decode(new_data['netlistFileContents']).decode('utf-8'))
            if set(input_cells) != set(netlist_cells):
                return {
                    'message': f'Cells in the metadata do not match the cells in the netlist.',
                    'status_code': status.HTTP_409_CONFLICT,
                    'status': False
                }
            if new_data['netlistMetadata']:
                true_cells = sum([i['is_selected'] for i in new_data['netlistMetadata']['cellSelections']])
                if not true_cells:
                    return {
                        'message': f'At least one cell in cell metadata should be selected.',
                        'status_code': status.HTTP_409_CONFLICT,
                        'status': False
                    }
            netlist_file=project.netlist_metadata['fileName']
            netlist_content = base64.b64decode(new_data['netlistFileContents']).decode('utf-8')
            project_netlist_path = f'{S3_BUCKET_ROOT}/Project/{project.created_by_id}/{project.id}/Netlist/{netlist_file}'
            netlist_path=f'{S3_BUCKET_ROOT}/Netlist/{project.created_by_id}/{project.project_name}_{netlist_file}'
            netlist_content = encrypt_file_content(netlist_content)
            storage_servicer.write_file(project_netlist_path, netlist_content, 1)
            storage_servicer.write_file(netlist_path, netlist_content, 1)
            FileInfo.objects.filter(name=netlist_file, created_by_id=project.created_by_id).update(filesize=storage_servicer.get_bucket_file_size(project_netlist_path))
            project.netlist_metadata = new_data['netlistMetadata']
            project.netlist_metadata['fileName']=netlist_file
        elif ('netlistFileContents' not in new_data) and ('netlistMetadata' not in new_data) :
            pass
        elif (('netlistFileContents' not in new_data) and ('netlistMetadata' in new_data)) or (('netlistFileContents' in new_data) and ('netlistMetadata' not in new_data)):
            return {
                'message': "Both 'netlistFileContents' and 'netlistMetadata' must be present or absent together.",
                'status_code': status.HTTP_404_NOT_FOUND,
                'status': False
            }
        if ('techFileContents' in new_data) and ('techMetadata' in new_data):
            old_file_name = project.tech_metadata['fileName']
            project_tech_path = f'{S3_BUCKET_ROOT}/Project/{project.created_by_id}/{project.id}/Techfile/{old_file_name}'
            tech_path=f'{S3_BUCKET_ROOT}/Techfile/{project.created_by_id}/{project.project_name}_{old_file_name}'
            tech_content = encrypt_file_content(dumps(new_data['techFileContents']))
            storage_servicer.write_file(project_tech_path, tech_content, 1)
            storage_servicer.write_file(tech_path, tech_content, 1)
            project.tech_metadata = new_data['techMetadata']
            tech_file = new_data['techMetadata']['fileName']
            # if project.tech_metadata['fileName'].startswith(project.project_name):
            #     tech_file = new_data['techMetadata']['fileName']
            # else:
            #     tech_file = f'{project.project_name}_{new_data['techMetadata']['fileName']}'
            project.tech_metadata['fileName'] = tech_file
            if old_file_name!=tech_file:
                project_response_status = storage_servicer.rename_file(project_tech_path, tech_file)
                tech_response_status = storage_servicer.rename_file(tech_path, tech_file)
                if not project_response_status:
                    return {
                        'message': "The tech file could not be renamed. Please check the process and try again.",
                        'status_code': status.HTTP_404_NOT_FOUND,
                        'status': False
                    }
                if not tech_response_status:
                    return {
                        'message': "The tech file could not be renamed. Please check the process and try again.",
                        'status_code': status.HTTP_404_NOT_FOUND,
                        'status': False
                    }
            FileInfo.objects.filter(name=tech_file, created_by_id=project.created_by_id).update(filesize=storage_servicer.get_bucket_file_size(project_tech_path))
        elif ('techFileContents' not in new_data) and ('techMetadata' not in new_data):
            pass
        elif (('techFileContents' not in new_data) and ('techMetadata' in new_data)) or (('techFileContents' in new_data) and ('techMetadata' not in new_data)):
            return {
                'message': "Both techFileContents' and 'techMetadata' must be present or absent together.",
                'status_code': status.HTTP_404_NOT_FOUND,
                'status': False
            } 
        if project.action==3:
            if 'selectedLayouts' in new_data:
                if not isinstance(new_data['selectedLayouts'], list):
                    message="selectedLayouts must be array."
                    status_code=status.HTTP_400_BAD_REQUEST
                    response_status=False
                    return message, status_code, response_status,None
                # if new_data['selectedLayouts'] == []:
                #     message="selectedLayouts must contain at least one value."
                #     status_code=status.HTTP_400_BAD_REQUEST
                #     response_status=False
                #     return message, status_code, response_status,None
                project.selectedLayouts.clear()
                project.selectedLayouts = new_data['selectedLayouts']
    elif project.action==getAction.Hyperexpresivity.value:
        if 'selectedLayouts' in new_data:
            if not isinstance(new_data['selectedLayouts'], list):
                message="selectedLayouts must be array."
                status_code=status.HTTP_400_BAD_REQUEST
                response_status=False
                return message, status_code, response_status,None
            # if new_data['selectedLayouts'] == []:
            #     message="selectedLayouts must contain at least one value."
            #     status_code=status.HTTP_400_BAD_REQUEST
            #     response_status=False
            #     return message, status_code, response_status,None
            project.selectedLayouts.clear()
            project.selectedLayouts = new_data['selectedLayouts']
        if 'netlistMetadata' in new_data:
            new_data['netlistMetadata']['fileName']=project.netlist_metadata['fileName']
            project.netlist_metadata = new_data['netlistMetadata']
        if 'techMetadata' in new_data:
            new_data['techMetadata']['fileName']=project.tech_metadata['fileName']
            project.tech_metadata = new_data['techMetadata']
        if 'stageOneProjectId' in new_data:
            if 'stageOneProjectId' not in new_data:
                message="stage 1 Project Id missing in given request."
                status_code=status.HTTP_400_BAD_REQUEST
                response_status=False
                return message, status_code, response_status,None
            if not isinstance(new_data['stageOneProjectId'], int):
                message="stage 1 Project Id must be integer value."
                status_code=status.HTTP_400_BAD_REQUEST
                response_status=False
                return message, status_code, response_status,None
            stageProject = Project.objects.filter(id=new_data['stageOneProjectId']).exclude(action=2).first()
            source_path=f'{S3_BUCKET_ROOT}/Project/{modifier_id}/{new_data['stageOneProjectId']}/Stage1/'
            destination_path=f'{S3_BUCKET_ROOT}/Project/{modifier_id}/{project.id}/Stage1/'
            storage_servicer.delete_folder(destination_path)
            message, response_status=storage_servicer.move_folder(source_path,destination_path)
            if stageProject==None:
                message="Project not found."
                status_code=status.HTTP_400_BAD_REQUEST
                response_status=False
                return message, status_code, response_status,None
            project.stage_one_project=new_data['stageOneProjectId']
    project.modified_by = User.objects.get(id=modifier_id)
    project.save()
    return {
        'message': f'Project saved successfully.',
        'status_code': status.HTTP_200_OK,
        'status': True
    }


def checkProject(user_id, projectName):
    return Project.objects.filter(created_by=user_id, project_name=projectName).exists()

# def get_stage_result(user_id, project_id, stage):
#     if stage not in thumbnail_suffix.keys():
#         message = "Invalid stage number."
#         status_code = status.HTTP_404_NOT_FOUND
#         return None,None, message, status_code, False

#     base_path = f'{S3_BUCKET_ROOT}/Project/{user_id}/{project_id}/Stage{stage}/'
#     available_cells = storage_servicer.list_folders(base_path)
    
#     # Initialize empty lists for storing results
#     thumbnail_paths = []
#     pex_consolidated = []
#     all_matrix_dfs = []
#     all_pex_dfs = []

#     start_time1 = time.time()

#     # Use ThreadPoolExecutor for parallel execution, but manage the lifecycle properly
#     with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:  # limit threads
#         futures = []
#         try:
#             # Submit tasks to the thread pool
#             for cell in available_cells:
#                 futures.append(executor.submit(process_cell, cell, base_path, stage, thumbnail_suffix))

#             # Collect results from futures
#             for future in concurrent.futures.as_completed(futures):
#                 # result will contain the data returned by the process_cell function
#                 cell_thumbnail_paths, cell_pex_consolidated, matrix_df, pex_df = future.result()

#                 # Append results to the main lists
#                 thumbnail_paths.extend(cell_thumbnail_paths)
#                 pex_consolidated.extend(cell_pex_consolidated)
#                 all_matrix_dfs.append(matrix_df)
#                 all_pex_dfs.append(pex_df)

#         except Exception as e:
#             print(f"Error occurred while processing cells: {e}")

#     end_time1 = time.time()
#     print(f"Loop took {end_time1 - start_time1} seconds")
#     # Concatenate the dataframes after all threads finish
#     if all_matrix_dfs and all_pex_dfs:
#         matrixdataframes = pd.concat(all_matrix_dfs, ignore_index=True)
#         pexdataframes = pd.concat(all_pex_dfs, ignore_index=True)
#     else:
#         message = "This project is either not available or it doesn't have a complete result for this stage."
#         status_code = status.HTTP_404_NOT_FOUND
#         return None, None, message, status_code, False
#     result = []
#     start_time2 = time.time()
#     with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:  # limit threads
#         futures = []
#         # Submit tasks to process each thumbnail in parallel
#         for thumbnail in thumbnail_paths:
#             futures.append(executor.submit(process_thumbnail, thumbnail, pexdataframes, matrixdataframes))
#         # Collect results from futures and add to the result list
#         for future in concurrent.futures.as_completed(futures):
#             result.append(future.result())
#     end_time2 = time.time()
#     print(f"Thumbnail processing loop took {end_time2 - start_time2} seconds")
#     message = "Success"
#     filtered_data = list(filter(None, result))
#     return filtered_data, pex_consolidated, message, status.HTTP_200_OK, True


# def process_thumbnail(thumbnail, pexdataframes, matrixdataframes):
#     filename = thumbnail.rsplit('/', 1)[-1].split('.')[0]
#     matrixdataframes = matrixdataframes.applymap(lambda x: None if pd.isna(x) else x)
#     pexdataframes = pexdataframes.astype(object)
#     pexdataframes = pexdataframes.where(pd.notnull(pexdataframes), None)
    
#     filtered_pex = pexdataframes[pexdataframes['File'] == filename]
#     filtered_matrics = matrixdataframes[matrixdataframes['File'] == filename]
    
#     if not filtered_matrics.empty and not filtered_pex.empty:
#         return {
#             'LayoutData': thumbnail,
#             'MetricsData': filtered_matrics.to_dict(orient='records'),
#             'PEXData': filtered_pex.to_dict(orient='records')
#         }
# def process_cell(cell, base_path, stage, thumbnail_suffix):
#     try:
#         # Generate paths for thumbnails
#         pathlist = storage_servicer.list_files_with_extension(f'{base_path}{cell}/{cell}_{thumbnail_suffix[stage]}/', '.png', S3_BUCKET_ROOT)
#         cell_thumbnail_paths = pathlist
#         root_path=base_path.replace(f"{S3_BUCKET_ROOT}/","")
#         # Fetch CSV data
#         matrixbasepath = f'{base_path}{cell}/{cell}_metrics/{cell}_metrics.csv'
#         matrix_df = storage_servicer.fetch_csv(matrixbasepath)
#         pexbasepath = f'{base_path}{cell}/{cell}_predictions/{cell}_GDS_PEX_PREDICTION_ML.csv'
#         pex_df = storage_servicer.fetch_csv(pexbasepath)

#         # Consolidate PEX data
#         record_list = []
#         for _, row in pex_df.iterrows():
#             record_dict = row.to_dict()
#             record_dict['LayoutData']=f'{root_path}{cell}/{cell}_{thumbnail_suffix[stage]}/{record_dict['File']}.png'
#             record_list.append(record_dict)
#         cell_pex_consolidated = [{"name": cell, "data": record_list}]
        
#         # Return all required data
#         return cell_thumbnail_paths, cell_pex_consolidated, matrix_df, pex_df

#     except Exception as e:
#         print(f"Error processing cell {cell}: {e}")
#         return [], [], pd.DataFrame(), pd.DataFrame()  # Return empty values in case of an error

def get_stage_result(user_id, project_id, stage):
    if stage not in thumbnail_suffix:
        return None, None, "Invalid stage number.", status.HTTP_404_NOT_FOUND, False

    base_path = f'{S3_BUCKET_ROOT}/Project/{user_id}/{project_id}/Stage{stage}/'
    available_cells = storage_servicer.list_folders(base_path)

    if not available_cells:
        return None, None, "No data available for the given stage.", status.HTTP_404_NOT_FOUND, False

    max_workers = min(4, os.cpu_count() or 4)

    # Initialize results
    thumbnail_paths, pex_consolidated, all_matrix_dfs, all_pex_dfs = [], [], [], []

    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(lambda cell: process_cell(cell, base_path, stage), available_cells))

    # Unpacking results efficiently
    for cell_thumbnail_paths, cell_pex_consolidated, matrix_df, pex_df in results:
        if cell_thumbnail_paths:
            thumbnail_paths.extend(cell_thumbnail_paths)
        if cell_pex_consolidated:
            pex_consolidated.extend(cell_pex_consolidated)
        if not matrix_df.empty:
            all_matrix_dfs.append(matrix_df)
        if not pex_df.empty:
            all_pex_dfs.append(pex_df)

    print(f"Cell processing completed in {time.time() - start_time:.2f} seconds")

    if not all_matrix_dfs or not all_pex_dfs:
        return None, None, "Project data is incomplete or unavailable.", status.HTTP_404_NOT_FOUND, False

    matrix_dataframes = pd.concat(all_matrix_dfs, ignore_index=True)
    pex_dataframes = pd.concat(all_pex_dfs, ignore_index=True)

    # # Optimize memory usage
    # matrix_dataframes.fillna(value=None, inplace=True)
    # pex_dataframes.fillna(value=None, inplace=True)

    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        result = list(filter(None, executor.map(lambda thumbnail: process_thumbnail(thumbnail, pex_dataframes, matrix_dataframes), thumbnail_paths)))

    print(f"Thumbnail processing completed in {time.time() - start_time:.2f} seconds")

    return result, pex_consolidated, "Success", status.HTTP_200_OK, True


def process_thumbnail(thumbnail, pex_dataframes, matrix_dataframes):
    filename = os.path.splitext(os.path.basename(thumbnail))[0]

    # Using .query() for faster filtering
    filtered_pex = pex_dataframes.query("File == @filename")
    filtered_matrix = matrix_dataframes.query("File == @filename")

    if not filtered_matrix.empty and not filtered_pex.empty:
        # Optimize memory by replacing NaN values with None
        return {
            'LayoutData': thumbnail,
            'MetricsData': filtered_matrix.astype(object).where(pd.notnull(filtered_matrix), None).to_dict(orient='records'),
            'PEXData': filtered_pex.astype(object).where(pd.notnull(filtered_pex), None).to_dict(orient='records')
        }

    return None


def process_cell(cell, base_path, stage):
    try:
        root_path = base_path.replace(f"{S3_BUCKET_ROOT}/", "")
        
        cell_path = f'{base_path}{cell}/{cell}_{thumbnail_suffix[stage]}/'
        cell_thumbnail_paths = storage_servicer.list_files_with_extension(cell_path, '.png', S3_BUCKET_ROOT)

        matrix_path = f'{base_path}{cell}/{cell}_metrics/{cell}_metrics.csv'
        pex_path = f'{base_path}{cell}/{cell}_predictions/{cell}_GDS_PEX_PREDICTION_ML.csv'

        matrix_df = storage_servicer.fetch_csv(matrix_path)
        pex_df = storage_servicer.fetch_csv(pex_path)

        if pex_df.empty:
            return cell_thumbnail_paths, [], matrix_df, pex_df

        # Consolidate PEX data
        pex_df['LayoutData'] = pex_df['File'].apply(lambda x: f'{root_path}{cell}/{cell}_{thumbnail_suffix[stage]}/{x}.png')
        pex_df = pex_df.replace({np.nan: None})
        cell_pex_consolidated = [{"name": cell, "data": pex_df.to_dict(orient='records')}]

        return cell_thumbnail_paths, cell_pex_consolidated, matrix_df, pex_df

    except Exception as e:
        print(f"Error processing cell {cell}: {e}")
        return [], [], pd.DataFrame(), pd.DataFrame()

def check_present_cells(cell_list, data):
    cell_names_in_data = [item['cell_name'] for item in data['cellSelections']]
    result = [item for item in cell_list if item not in cell_names_in_data]
    return result


def tech_migrater(tech_data):
    json_tech = json.loads(tech_data["FileContent"])
    with open(f"{os.getcwd()}/UpdatedTech.json", "r") as f:
        updated_data = json.load(f)

    output_json = []

    # Elements to be updated directly
    non_visible_elements = {
        "hinder", "configs", "routing_layers", "via_size", 
        "minimum_enclosure", "layer_properties", "display_names"
    }

    for element in json_tech:
        name = element.get('name')
        # Skip specific permutation elements
        if name == "permutation":
            if element['name'] == "permutation":
                element["data"] = [
                record for record in element.get("data", [])
                if not (
                    isinstance(record.get("attribute"), str) and 
                    record["attribute"] in {"l_metal2_tracks", "l_metal_tracks"}
                )
            ]
                for record in element['data']:
                    attribute = record.get('attribute')
                    atr_dict={
                        "l_npoly": "npoly", "l_ppoly": "ppoly",
                        "l_ndiffusion": "ndiffcon", "l_pdiffusion": "pdiffcon", "l_metal1": "metal0",
                        "routing_grid_pitch_y": "m0_pitch", "l_metal_tracks": "metal0_track_guide",
                        "l_metal2": "metal1","l_metal2_tracks": "metal1_track_guide"
                    }
                    if attribute in ["l_metal_tracks", "l_metal2_tracks"]:
                        continue
                    elif attribute == ["l_nanosheet", "l_interconnect_via"]:
                        record['attribute'] = ["nanosheet", "diff_interconnect"]
                    elif attribute in atr_dict:
                        record['name'] = 'layer_width'
                        record['parameterName']= 'layer_width'
                        record['attribute'] = atr_dict[attribute]
            # skip = any(
            #     item.get('attribute') in {"l_metal_tracks", "l_metal2_tracks"}
            #     for item in element.get('data', [])
            # )
            # if skip:
            #     continue  # Don't append this permutation element
        # Update layer_map directly
        elif name == "layer_map":
            element['data'] = updated_data.get('layer_map', [])

        # Update tech_constraints with mapped values
        elif name == "tech_constaints":
            val_dict = {e2['key']['key1']: e2['val'] for e2 in element.get('data', [])}
            val_dict['backside_power_rail'] = "Backside power" if val_dict.get('backside_power_rail') else "Frontside power"
            val_dict['half_dr'] = True
            element['data'] = updated_data.get('tech_constaints', [])
            for e2 in element['data']:
                key1 = e2.get('key', {}).get('key1')
                if key1 in val_dict:
                    e2['val'] = val_dict[key1]

        # Replace data directly from updated file
        elif name == "other":
            element['data'] = updated_data.get(name, [])

        # Remap keys and update data for wire_width
        elif name == "wire_width":
            element['name'] = "layer_width"
            key_map = {
                "l_npoly": "npoly", "l_ppoly": "ppoly", "nanosheet_width": "nanosheet_width",
                "l_ndiffusion": "ndiffcon", "l_pdiffusion": "pdiffcon", "l_metal1": "metal0",
                "routing_grid_pitch_y": "m0_pitch", "l_metal_tracks": "metal0_track_guide",
                "l_metal2": "metal1", "vertical_metal_pitch": "vertical_metal_pitch",
                "l_metal2_tracks": "metal1_track_guide", "power_rail_width": "power_rail_width"
            }
            val_dict = {
                key_map.get(e2['key']['key1']): e2['val']
                for e2 in element.get('data', [])
                if e2['key']['key1'] in key_map
            }

            element['data'] = updated_data.get(name, [])
            for e2 in element['data']:
                old_key = e2['key']['key1']
                new_key = key_map.get(old_key)
                if new_key in val_dict:
                    e2['val'] = val_dict[new_key]
                    e2['key']['key1'] = new_key

        # Remap keys and update data for min_spacing
        elif name == "min_spacing":
            key_map = {
                "np_spacing": "np_spacing", "inner_space_width": "inner_space_width",
                "vertical_gate_spacing": "vertical_gate_spacing", "vertical_interconnect_spacing": "vertical_interconnect_spacing",
                "l_nanosheet": "nanosheet", "l_interconnect_via": "diff_interconnect",
                "pg_signal_spacing": "pg_signal_spacing", "gate_extension": "gate_extension",
                "interconnect_extension": "interconnect_extension", "via_extension": "via_extension"
            }
            val_dict = {
                key_map[e2['key']['key1']]: e2['val']
                for e2 in element.get('data', [])
                if e2['key']['key1'] in key_map
            }

            element['data'] = updated_data.get(name, [])
            for e2 in element['data']:
                key1 = e2.get('key', {}).get('key1')
                key2 = e2.get('key', {}).get('key2')

                if key1 in key_map:
                    e2['val'] = val_dict.get(key_map[key1], e2['val'])

                if key2 in key_map:
                    e2['key']['key2'] = key_map[key2]

        # Directly update from updated_data if in non-visible elements
        elif name in non_visible_elements:
            element['data'] = updated_data.get(name, [])

        output_json.append(element)

    return output_json
