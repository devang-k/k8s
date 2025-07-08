"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: views.py  
 * Description: getting Stage results --> GDS, Matrix, Pex , Download results, get images
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
import os
from django.http import JsonResponse, FileResponse, StreamingHttpResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from src.Services.ProjectService import get_stage_result
from src.Services.JobService import generate_key
from src.Models.Project.ProjectResponse import ProjectResponse
from src.Models.Stage.StageResponse import StageResponse
from src.Apps.project.ProjectManager.models import Project, FileInfo, Job
from src.Apps.user.Login.models import User
from src.Services.StorageServices.StorageService import storage_servicer
from django.core.cache import cache
from SiVista_BE.settings import S3_BUCKET_ROOT
from django.core.paginator import Paginator, EmptyPage
from redis.exceptions import ConnectionError
import numpy as np
import base64
import numpy as np
import pandas as pd
import logging
import json
import time
import asyncio
import concurrent.futures

logger = logging.getLogger(__name__)

class StageStatus(APIView):
    @swagger_auto_schema(
        operation_summary="Get stage result from s3",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                    "projectId":openapi.Schema(type=openapi.TYPE_NUMBER,description='Project Id for stage results'),
                    "stage":openapi.Schema(type=openapi.TYPE_NUMBER,description='Stage action for stage results')},
            required=['projectId', 'stage']),
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
    def post(self,request):
        # Extract project ID, stage ID, and user ID
        project_id = request.data.get('projectId')
        stage_id = request.data.get('stage')
        user_id = request.user_id
        if (not isinstance(project_id,int)) or project_id==None:
            message = f'A project with id {project_id} doesn\'t exist.'
            status_code = status.HTTP_404_NOT_FOUND
            response_status = False
            response = JsonResponse({
                    'message': message,
                    'status_code': status_code,
                    'response_status': response_status,
                    'result': None
                })
            response.status_code=status_code
            return response   
        if stage_id not in [1,2]:
            message = f'Invalid stage Id.'
            status_code = status.HTTP_400_BAD_REQUEST
            response_status = False
            response = JsonResponse({
                    'message': message,
                    'status_code': status_code,
                    'response_status': response_status,
                    'data': None
                })
            response.status_code=status_code
            return response 
        # Fetch the project
        project = Project.objects.filter(id=project_id).first()
        # Check if project exists and if user has access
        if not project:
            message = f'A project with id {project_id} doesn\'t exist.'
            status_code = status.HTTP_404_NOT_FOUND
            response_status = False
            response = JsonResponse({
                    'message': message,
                    'status_code': status_code,
                    'response_status': response_status,
                    'data': None
                })
            response.status_code=status_code
            return response
        elif project.created_by_id != user_id:  # TODO: Check if user has the required permissions
            message = 'You cannot view the results of this project.'
            status_code = status.HTTP_401_UNAUTHORIZED
            response_status = False
            response=JsonResponse({
                    'message': message,
                    'status_code': status_code,
                    'response_status': response_status,
                    'data': None
                })
            response.status_code=status_code
            return response
        else:
            job=Job.objects.filter(project_id=project_id, action=stage_id, status='COMPLETED').first()
            if job:
                base_path=f'{S3_BUCKET_ROOT}/Project/{user_id}/{project_id}/Stage{stage_id}/'
                cells=storage_servicer.list_folders(base_path)
                for cell in cells:
                    if stage_id==1:
                        s3_status=storage_servicer.has_png_files(f'{base_path}{cell}/{cell}_optimizedGDS/')
                    elif stage_id==2:
                        s3_status=storage_servicer.has_png_files(f'{base_path}{cell}/{cell}_permutations')
                    else:
                        s3_status=False
                    if s3_status:
                        break
                if s3_status:
                    message = 'Success'
                    status_code = status.HTTP_200_OK
                    response_status = True
                    response = JsonResponse({
                            'message': message,
                            'status_code': status_code,
                            'response_status': response_status,
                            'data': True
                        })
                    response.status_code=status_code
                    return response
                else:
                    message = f'Result not found.'
                    status_code = status.HTTP_200_OK
                    response_status = False
                    response = JsonResponse({
                            'message': message,
                            'status_code': status_code,
                            'response_status': response_status,
                            'data': False
                        })
                    response.status_code=status_code
                    return response
            else:
                message = f'Result not found.'
                status_code = status.HTTP_200_OK
                response_status = False
                response = JsonResponse({
                        'message': message,
                        'status_code': status_code,
                        'response_status': response_status,
                        'data': False
                    })
                response.status_code=status_code
                return response

class StageResult(APIView):
    @swagger_auto_schema(
        operation_summary="Get stage result from s3",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                    "projectId":openapi.Schema(type=openapi.TYPE_NUMBER,description='Project Id for stage results'),
                    "stage":openapi.Schema(type=openapi.TYPE_NUMBER,description='Stage action for stage results'),
                    "page":openapi.Schema(type=openapi.TYPE_NUMBER,description='Page Number'),
                    "pageSize": openapi.Schema(type=openapi.TYPE_NUMBER,description='Number of elements for each page'),
                    "filter": openapi.Schema(type=openapi.TYPE_OBJECT,properties={
                        "cellSelectAll":openapi.Schema(type=openapi.TYPE_BOOLEAN, description="All cells selected or partial cell selection for all value is true"),
                        "cells":openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING, description="Cell names"),description="List of partially selected cells."),
                        "filterParametersName":openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                            "filterLeve1":openapi.Schema(type=openapi.TYPE_ARRAY,items=openapi.Schema(type=openapi.TYPE_OBJECT,properties={
                                "parameterName1":openapi.Schema(type=openapi.TYPE_STRING,description="Name of parameter1 to apply filter."),
                                "parameterName2":openapi.Schema(type=openapi.TYPE_STRING,description="Name of parameter2 to apply filter."),
                                "filterationValue":openapi.Schema(type=openapi.TYPE_STRING,description=">,<,<=,>=,=,between"),
                                "value1":openapi.Schema(type=openapi.TYPE_INTEGER,description="Vlaue for filter."),
                                "value2":openapi.Schema(type=openapi.TYPE_INTEGER,description="Vlaue for filter.")})),
                            "filterLeve2":openapi.Schema(type=openapi.TYPE_ARRAY,items=openapi.Schema(type=openapi.TYPE_OBJECT,properties={
                                "parameterName1":openapi.Schema(type=openapi.TYPE_STRING,description="Name of parameter1 to apply filter."),
                                "parameterName2":openapi.Schema(type=openapi.TYPE_STRING,description="Name of parameter2 to apply filter."),
                                "filterationValue":openapi.Schema(type=openapi.TYPE_STRING,description=">,<,<=,>=,=,between"),
                                "value1":openapi.Schema(type=openapi.TYPE_INTEGER,description="Vlaue for filter."),
                                "value2":openapi.Schema(type=openapi.TYPE_INTEGER,description="Vlaue for filter.")}))
                            })})
                },
            required=['projectId', 'stage', 'page', 'pageSize','filter','cellSelectAll','filterParametersName']
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
        # Extract project ID, stage ID, and user ID
        project_id = request.data.get('projectId')
        stage_id = request.data.get('stage')
        user_id = request.user_id
        filter=request.data.get('filter',None)
        filebylist=request.data.get('filterByLayout',None)
        if (not isinstance(project_id,int)) or project_id==None:
            result = None
            message = f'A project with id {project_id} doesn\'t exist.'
            status_code = status.HTTP_404_NOT_FOUND
            response_status = False
            response = JsonResponse({
                    'message': message,
                    'status_code': status_code,
                    'response_status': response_status,
                    'result': None
                })
            response.status_code=status_code
            return response          
        # Fetch the project
        project = Project.objects.filter(id=project_id).first()
        # Check if project exists and if user has access
        if not project:
            result = None
            message = f'A project with id {project_id} doesn\'t exist.'
            status_code = status.HTTP_404_NOT_FOUND
            response_status = False
            response = JsonResponse({
                    'message': message,
                    'status_code': status_code,
                    'response_status': response_status,
                    'data': None
                })
            response.status_code=status_code
            return response
        elif project.created_by_id != user_id:  # TODO: Check if user has the required permissions
            result = None
            message = 'You cannot view the results of this project.'
            status_code = status.HTTP_401_UNAUTHORIZED
            response_status = False
            response=JsonResponse({
                    'message': message,
                    'status_code': status_code,
                    'response_status': response_status,
                    'data': None
                })
            response.status_code=status_code
            return response
        elif not isinstance(stage_id, int):
            result = None
            message = f'Stage ID should be integer.'
            status_code = status.HTTP_400_BAD_REQUEST
            response_status = False
            response = JsonResponse({
                    'message': message,
                    'status_code': status_code,
                    'response_status': response_status,
                    'data': None
                })
            response.status_code=status_code
            return response      
        else:
            base_path=f'{S3_BUCKET_ROOT}/Project/{user_id}/{project_id}/Stage{stage_id}/'
            if stage_id==1:
                input_data_stage1=storage_servicer.fetch_files(f'{base_path}Run_Summary.json')
                if input_data_stage1:
                    input_data_stage1=input_data_stage1.decode('utf-8')
                    input_data_stage1=json.loads(input_data_stage1)
                    key=generate_key(f'StageResult_{project_id}_{stage_id}_{input_data_stage1['cells']['value']}', stage_id, {"techParameters": input_data_stage1['techParameters'], "variationTechParameters": input_data_stage1['variationTechParameters'],"layerMap":input_data_stage1['layermap']})
                else:
                     key=None
            elif stage_id == 2:
                base_path_1=f'{S3_BUCKET_ROOT}/Project/{user_id}/{project_id}/Stage1/'
                input_data_stage1=storage_servicer.fetch_files(f'{base_path_1}Run_Summary.json')
                input_data_stage2=storage_servicer.fetch_files(f'{base_path}Run_Summary.json')
                if input_data_stage1 and input_data_stage2:
                    input_data_stage2=input_data_stage2.decode('utf-8')
                    input_data_stage1=input_data_stage1.decode('utf-8')
                    input_data_stage2=json.loads(input_data_stage2)
                    input_data_stage1=json.loads(input_data_stage1)
                    key=generate_key(f'StageResult_{project_id}_{stage_id}_{input_data_stage2['cells']['value']}', stage_id, {"techParameters": input_data_stage1['techParameters'], "variationTechParameters": input_data_stage1['variationTechParameters'],"layerMap":input_data_stage1['layermap']})
                else:
                    key=None
            elif stage_id not in [1,2]:
                result = None
                message = f'Invalid stage.'
                status_code = status.HTTP_400_BAD_REQUEST
                response_status = False
                response = JsonResponse({
                        'message': message,
                        'status_code': status_code,
                        'response_status': response_status,
                        'data': None
                    })
                response.status_code=status_code
                return response
            # Connect to Redis
            #http://13.126.133.62:3006/redis-stack/browser
            try:
                if key:
                    if cache.get(key) is not None:
                        result_data = cache.get(key)
                        result_json = json.loads(result_data)
                        result=result_json['result']
                        pex_consolidated=result_json['pex_consolidated']
                        message = "Success"
                        status_code = status.HTTP_200_OK
                        response_status = True
                    else:
                        # Retrieve the result from the stage
                        result,pex_consolidated, message, status_code, response_status = get_stage_result(user_id, project_id, stage_id)
                        result=sorted(result, key=lambda x: x['LayoutData'])
                        pex_consolidated = sorted(pex_consolidated, key=lambda x: (x['name'], sorted(x['data'], key=lambda y: y['LayoutData'])))
                        cache.set(key, json.dumps({'result': result, 'pex_consolidated': pex_consolidated}), 1800)
                else:
                    result,pex_consolidated, message, status_code, response_status = get_stage_result(user_id, project_id, stage_id)
                    if result:
                        result=sorted(result, key=lambda x: x['LayoutData'])
                        pex_consolidated = sorted(pex_consolidated, key=lambda x: (x['name'], sorted(x['data'], key=lambda y: y['LayoutData'])))
                    else:
                        message = "This project is either not available or it doesn't have a complete result for this stage."
                        status_code = status.HTTP_404_NOT_FOUND
                        response_status = False
            except ConnectionError:
                result,pex_consolidated, message, status_code, response_status = get_stage_result(user_id, project_id, stage_id)
                if result:
                    result=sorted(result, key=lambda x: x['LayoutData'])
                    pex_consolidated = sorted(pex_consolidated, key=lambda x: (x['name'], sorted(x['data'], key=lambda y: y['LayoutData'])))
                else:
                    message = "This project is either not available or it doesn't have a complete result for this stage."
                    status_code = status.HTTP_404_NOT_FOUND
                    response_status = False
            if not filter == None and isinstance(filter, dict):
                base_path=f'{S3_BUCKET_ROOT}/Project/{user_id}/{project_id}/Stage{stage_id}/'
                detailed_data_path = f'{base_path}Stage_Report{stage_id}.csv'
                detailed_data = storage_servicer.fetch_csv(detailed_data_path)
                if not detailed_data.empty:
                    # Replace NaN with None
                    detailed_dataframes = detailed_data.applymap(lambda x: None if pd.isna(x) else x)
                    # If 'cells' are provided, filter those rows
                    if 'File' not in detailed_dataframes.columns:
                        message=f"Column 'File' does not exist in the DataFrame."
                        status_code=status.HTTP_400_BAD_REQUEST
                        response_status=False
                        response=JsonResponse({
                            'message': message,
                            'status_code': status_code,
                            'response_status': response_status,
                            'data': None
                        })
                        response.status_code=status_code
                        return response
                    if not isinstance(filter['cellSelectAll'], bool):
                        message="Cell select all flag must be a boolean."
                        status_code=status.HTTP_400_BAD_REQUEST
                        response_status=False
                        response=JsonResponse({
                            'message': message,
                            'status_code': status_code,
                            'response_status': response_status,
                            'data': None
                        })
                        response.status_code=status_code
                        return response
                    if (filter['cells']==[] and filter['cellSelectAll']==False) or (filter['cells'] is None and filter['cellSelectAll']==False) or not isinstance(filter['cells'], list):
                        message="Cell can't be empty if select all flag is false."
                        status_code=status.HTTP_404_NOT_FOUND
                        response_status=False
                        response=JsonResponse({
                            'message': message,
                            'status_code': status_code,
                            'response_status': response_status,
                            'data': None
                        })
                        response.status_code=status_code
                        return response
                    elif filter['cells'] is not None and isinstance(filter['cells'], list) and filter['cellSelectAll']==False:
                        if "Cells" not in detailed_dataframes.columns:
                            message=f"Column 'Cell' does not exist in the DataFrame."
                            status_code=status.HTTP_400_BAD_REQUEST
                            response_status=False
                            response=JsonResponse({
                                'message': message,
                                'status_code': status_code,
                                'response_status': response_status,
                                'data': None
                            })
                            response.status_code=status_code
                            return response
                        cell_filtered_datapoints = detailed_dataframes[detailed_dataframes['Cells'].isin(filter['cells'])]
                    elif filter['cellSelectAll']==True:
                        cell_filtered_datapoints = detailed_dataframes
                    cell_filtered_datapoints=cell_filtered_datapoints.reset_index()
                    if cell_filtered_datapoints.empty:
                        message="No data found for the provided filter."
                        status_code=status.HTTP_404_NOT_FOUND
                        response_status=False
                        response=JsonResponse({
                            'message': message,
                            'status_code': status_code,
                            'response_status': response_status,
                            'data': None
                        })
                        response.status_code=status_code
                        return response
                    # Check if 'selectAllValue' is False in the first element of 'filterParametersName'
                    if not isinstance(filter['filterParametersName'], dict):
                        message="Filter parameters must be a object."
                        status_code=status.HTTP_400_BAD_REQUEST
                        response_status=False
                        response=JsonResponse({
                            'message': message,
                            'status_code': status_code,
                            'response_status': response_status,
                            'data': None
                        })
                        response.status_code=status_code
                        return response
                    if filter['filterParametersName']==None:
                        message="Filter parameters can't be null."
                        status_code=status.HTTP_400_BAD_REQUEST
                        response_status=False
                        response=JsonResponse({
                            'message': message,
                            'status_code': status_code,
                            'response_status': response_status,
                            'data': None
                        })
                        response.status_code=status_code
                        return response
                    if filter['filterParametersName']!={} or filter['filterParametersName']!=None:
                        # Define operators for comparison
                        operators = {
                            '>': lambda x, y: x > y,
                            '<': lambda x, y: x < y,
                            '=': lambda x, y: x == y,
                            '!=': lambda x, y: x != y,
                            '>=': lambda x, y: x >= y,
                            '<=': lambda x, y: x <= y,
                            'between': lambda x, low, high: (x >= low) & (x <= high)
                        }
                        if 'filterParametersName' in filter:
                            for level, filters in filter['filterParametersName'].items():  # Iterating over each level (Level1, Level2, etc.)
                                if filters == [] or filters is None:
                                    pass
                                elif not isinstance(filters, list):
                                    message = "Filter parameters must be either a list or null."
                                    status_code = status.HTTP_400_BAD_REQUEST
                                    response_status = False
                                    response = JsonResponse({
                                        'message': message,
                                        'status_code': status_code,
                                        'response_status': response_status,
                                        'data': None
                                    })
                                    response.status_code = status_code
                                    return response
                                else:    
                                    for filter_param in filters:  # Iterating over each filter within the current level
                                        # Check if filterationValue is a string
                                        if not isinstance(filter_param['filterationValue'], str):
                                            message = "Filteration value must be a string."
                                            status_code = status.HTTP_400_BAD_REQUEST
                                            response_status = False
                                            response = JsonResponse({
                                                'message': message,
                                                'status_code': status_code,
                                                'response_status': response_status,
                                                'data': None
                                            })
                                            response.status_code = status_code
                                            return response

                                        # Validate if the filterationValue is an acceptable operator
                                        operators_list = ['>', '<', '=', '!=', '>=', '<=', 'between']
                                        if filter_param['filterationValue'] not in operators_list:
                                            message = "Invalid operator."
                                            status_code = status.HTTP_400_BAD_REQUEST
                                            response_status = False
                                            response = JsonResponse({
                                                'message': message,
                                                'status_code': status_code,
                                                'response_status': response_status,
                                                'data': None
                                            })
                                            response.status_code = status_code
                                            return response

                                        # Validate parameterName1 is a string
                                        if not isinstance(filter_param['parameterName1'], str):
                                            message = "Parameter name must be a string."
                                            status_code = status.HTTP_400_BAD_REQUEST
                                            response_status = False
                                            response = JsonResponse({
                                                'message': message,
                                                'status_code': status_code,
                                                'response_status': response_status,
                                                'data': None
                                            })
                                            response.status_code = status_code
                                            return response

                                        # Validate value1 is a number
                                        if (isinstance(filter_param['value1'], (int, float, str)) and filter_param['value1'] is not None) or (isinstance(filter_param['value2'], (int, float, str)) and filter_param['value2'] is not None):
                                            pass
                                        else:
                                            message = "Value must be a number or string."
                                            status_code = status.HTTP_400_BAD_REQUEST
                                            response_status = False
                                            response = JsonResponse({
                                                'message': message,
                                                'status_code': status_code,
                                                'response_status': response_status,
                                                'data': None
                                            })
                                            response.status_code = status_code
                                            return response
                                        # Validate for 'between' operator (if it's used)
                                        if filter_param['filterationValue'] == 'between' and (not isinstance(filter_param['value1'], (int, float)) or filter_param['value1'] is None):
                                            message = "Value1 must be a number."
                                            status_code = status.HTTP_400_BAD_REQUEST
                                            response_status = False
                                            response = JsonResponse({
                                                'message': message,
                                                'status_code': status_code,
                                                'response_status': response_status,
                                                'data': None
                                            })
                                            response.status_code = status_code
                                            return response
                                        
                                        if filter_param['filterationValue'] == 'between' and (
                                            filter_param['value2'] is None or not isinstance(filter_param['value2'], (int, float))):
                                            message = "Value2 must be a number."
                                            status_code = status.HTTP_400_BAD_REQUEST
                                            response_status = False
                                            response = JsonResponse({
                                                'message': message,
                                                'status_code': status_code,
                                                'response_status': response_status,
                                                'data': None
                                            })
                                            response.status_code = status_code
                                            return response

                                        # Ensure value2 > value1 if 'between' is used
                                        if filter_param['filterationValue'] == 'between' and filter_param['value2'] < filter_param['value1']:
                                            message = "Value2 must be greater than value1."
                                            status_code = status.HTTP_400_BAD_REQUEST
                                            response_status = False
                                            response = JsonResponse({
                                                'message': message,
                                                'status_code': status_code,
                                                'response_status': response_status,
                                                'data': None
                                            })
                                            response.status_code = status_code
                                            return response

                                        # Access the filter parameters
                                        column = filter_param['parameterName1']
                                        condition = filter_param['filterationValue']
                                        value1 = filter_param['value1']
                                        value2 = filter_param['value2']

                                        if column in cell_filtered_datapoints.columns:
                                            # Check if the column contains any strings
                                            contains_string = cell_filtered_datapoints[column].apply(lambda x: isinstance(x, str)).any()
                                        else:
                                            message = f"Column '{column}' does not exist in the Stage report."
                                            status_code = status.HTTP_400_BAD_REQUEST
                                            response_status = False
                                            response = JsonResponse({
                                                'message': message,
                                                'status_code': status_code,
                                                'response_status': response_status,
                                                'data': None
                                            })
                                            response.status_code = status_code
                                            return response

                                        # If the column has strings, only allow '=' operator
                                        if contains_string and condition not in ['=']:
                                            message = "Invalid operator for string column."
                                            status_code = status.HTTP_400_BAD_REQUEST
                                            response_status = False
                                            response = JsonResponse({
                                                'message': message,
                                                'status_code': status_code,
                                                'response_status': response_status,
                                                'data': None
                                            })
                                            response.status_code = status_code
                                            return response
                                        if value1 :
                                            value=value1
                                        elif value2 :
                                            value=value2
                                        else:
                                            value=None
                                        # Apply the filter dynamically
                                        if condition == 'between' and filter_param['value2'] is not None:
                                            value2 = filter_param['value2']
                                            value = np.float64(value)
                                            value2 = np.float64(value2)
                                            cell_filtered_datapoints = cell_filtered_datapoints[
                                                operators[condition](cell_filtered_datapoints[column], value1, value2)
                                            ]
                                        else:
                                            value = np.float64(value)
                                            cell_filtered_datapoints = cell_filtered_datapoints[
                                                operators[condition](cell_filtered_datapoints[column], value)
                                            ]

                            # Continue to filter and process the data as before
                            cell_filtered_datapoints = cell_filtered_datapoints.reset_index(drop=True)
                            row_indices = cell_filtered_datapoints.index
                            if stage_id==1:
                                filtered_rows = cell_filtered_datapoints.iloc[row_indices]['File'].tolist()
                            elif stage_id==2:
                                filtered_rows = cell_filtered_datapoints.iloc[row_indices]['permutationLayout'].tolist()
                            if filebylist and isinstance(filebylist, list):
                                filtered_rows.extend(filebylist)
                                filtered_rows=list(set(filtered_rows))
                            # Filter the results based on the updated rows
                            filtered_result = [{
                                'LayoutData': item['LayoutData'],
                                'MetricsData': item['MetricsData'],
                                'PEXData': item['PEXData']
                            }
                            for item in result if any(pex['File'] in filtered_rows for pex in item['PEXData'])]

                            # Filter the PEX consolidated data similarly
                            filtered_pex_consolidate = [{
                                'name': item['name'],
                                'data': [pex for pex in item['data'] if pex['File'] in filtered_rows]
                            }
                            for item in pex_consolidated if any(pex['File'] in filtered_rows for pex in item['data'])]

                            if filtered_pex_consolidate == [] or filtered_result == []:
                                message = "No data found for the provided filter."
                                status_code = status.HTTP_404_NOT_FOUND
                                response_status = False
                                response = JsonResponse({
                                    'message': message,
                                    'status_code': status_code,
                                    'response_status': response_status,
                                    'data': None
                                })
                                response.status_code = status_code
                                return response
                    else:
                        # Continue to filter and process the data as before
                        cell_filtered_datapoints = cell_filtered_datapoints.reset_index(drop=True)
                        row_indices = cell_filtered_datapoints.index
                        if stage_id==1:
                            filtered_rows = cell_filtered_datapoints.iloc[row_indices]['File'].tolist()
                        elif stage_id==2:
                            filtered_rows = cell_filtered_datapoints.iloc[row_indices]['permutationLayout'].tolist()
                        if filebylist and isinstance(filebylist, list):
                            filtered_rows.extend(filebylist)
                            filtered_rows=list(set(filtered_rows))
                        # Filter the results based on the updated rows
                        filtered_result = [{
                            'LayoutData': item['LayoutData'],
                            'MetricsData': item['MetricsData'],
                            'PEXData': item['PEXData']
                        }
                        for item in result if any(pex['File'] in filtered_rows for pex in item['PEXData'])]
                        # Filter the PEX consolidated data similarly
                        filtered_pex_consolidate = [{
                            'name': item['name'],
                            'data': [pex for pex in item['data'] if pex['File'] in filtered_rows]
                        }
                        for item in pex_consolidated if any(pex['File'] in filtered_rows for pex in item['data'])]
                        if filtered_pex_consolidate == [] or filtered_result == []:
                            message = "No data found for the provided filter."
                            status_code = status.HTTP_404_NOT_FOUND
                            response_status = False
                            response = JsonResponse({
                                'message': message,
                                'status_code': status_code,
                                'response_status': response_status,
                                'data': None
                            })
                            response.status_code = status_code
                            return response
                else:
                    message = "Case report not present for this project."
                    status_code = status.HTTP_404_NOT_FOUND
                    response_status = False
                    response=JsonResponse({
                        'message': message,
                        'status_code': status_code,
                        'response_status': response_status,
                        'data': None
                    })
                    response.status_code=status_code
                    return response
            elif filebylist and isinstance(filebylist, list):
                filtered_rows = filebylist
                # Filter the results based on the updated rows
                filtered_result = [{
                    'LayoutData': item['LayoutData'],
                    'MetricsData': item['MetricsData'],
                    'PEXData': item['PEXData']
                }
                for item in result if any(pex['File'] in filtered_rows for pex in item['PEXData'])]
                # Filter the PEX consolidated data similarly
                filtered_pex_consolidate = [{
                    'name': item['name'],
                    'data': [pex for pex in item['data'] if pex['File'] in filtered_rows]
                }
                for item in pex_consolidated if any(pex['File'] in filtered_rows for pex in item['data'])]
                if filtered_pex_consolidate == [] or filtered_result == []:
                    message = "No data found for the provided filter."
                    status_code = status.HTTP_404_NOT_FOUND
                    response_status = False
                    response = JsonResponse({
                        'message': message,
                        'status_code': status_code,
                        'response_status': response_status,
                        'data': None
                    })
                    response.status_code = status_code
                    return response
            else:
                filtered_result = result
                filtered_pex_consolidate = pex_consolidated
            
            if response_status == False:
                response= JsonResponse({
                        'message': message,
                        'status_code': status_code,
                        'status': response_status,
                        'data': result
                    })
                response.status_code=status_code
                return response            
            # Extract page number and page size from request data
            try:
                page_number = int(request.data.get('page', 0)) if request.data.get('page') is not None else 0 # Default to page 0 if not provided
                page_size = int(request.data.get('pageSize', 8)) if request.data.get('pageSize') is not None else 8 # Default to page size of 8 if not provided
                if page_number < 0:
                    response=JsonResponse({
                    'message': "Page number can't be less than 0.",
                    'status_code': status.HTTP_400_BAD_REQUEST,
                    'status': False,
                    'data': None
                })
                    response.status_code=status.HTTP_400_BAD_REQUEST
                    return response
                if page_size < 1:
                    response=JsonResponse({
                    'message': "Elements per page can't be less than 1.",
                    'status_code': status.HTTP_400_BAD_REQUEST,
                    'status': False,
                    'data': None
                })
                    response.status_code=status.HTTP_400_BAD_REQUEST
                    return response
            except ValueError:
                # Handle invalid page number or page size
                response=JsonResponse({
                    'message': 'Invalid page number or page size.',
                    'status_code': status.HTTP_400_BAD_REQUEST,
                    'status': False,
                    'data': None
                })
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            
            if filtered_result and isinstance(filtered_result, list):  # Ensure result is a list for pagination
                paginator = Paginator(filtered_result, page_size)
                non_filtered_paginator=Paginator(result, page_size)
                if page_size <= 0:
                    response = JsonResponse({
                        'message': 'No pages available.',
                        'status_code': status.HTTP_400_BAD_REQUEST,
                        'status': False,
                        'data': None
                    })
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return response
                # Check if the requested page number exceeds the number of available pages
                if page_number >= paginator.num_pages:
                    response= JsonResponse({
                        'message': 'Page number exceeds the total number of available pages.',
                        'status_code': status.HTTP_400_BAD_REQUEST,
                        'status': False,
                        'data': None
                    })
                    response.status_code=status.HTTP_400_BAD_REQUEST
                    return response

                try:
                    # Adjust for Django's 1-based indexing
                    page = paginator.page(page_number + 1)
                except EmptyPage:
                    # Handle empty page by returning the last page
                    page = paginator.page(paginator.num_pages)
                
                # Format the paginated response
                items = list(page.object_list)
                total_items = paginator.count
                total_gds_generated=non_filtered_paginator.count
                displayed_items_count = len(items)
                remaining_items_count = paginator.count - (page_number * page_size + displayed_items_count)
                if project:
                    selectedLayouts=project.selectedLayouts           
                    paginated_result = {
                        'Items': items,
                        'selectedLayouts':selectedLayouts,
                        'PageNumber': page.number - 1,  # Convert back to zero-based index
                        'PageSize': page.paginator.per_page,
                        'TotalGdsCount':total_gds_generated,
                        'TotalItems': total_items,
                        'RemainingItems': remaining_items_count
                    }
                    if page_number < 1:
                        paginated_result['PEX_Consolidated'] = filtered_pex_consolidate
                    
                else:
                    response= JsonResponse({
                    'message': 'Project not available.',
                    'status_code': status.HTTP_400_BAD_REQUEST,
                    'status': False,
                    'data': None
                })
                    response.status_code=status.HTTP_400_BAD_REQUEST
                    return response 
            else:
                # Default response when there are no items
                response= JsonResponse({
                    'message': 'Result must be list instance.',
                    'status_code': status.HTTP_400_BAD_REQUEST,
                    'status': False,
                    'data': None
                })
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response 
            
            # Update message and status code based on result processing
            message = message if message else 'Results retrieved successfully.'
            status_code = status.HTTP_200_OK
            response_status = True
        
        # Return the response as a JSON object
        response_data = {
            'message': message,
            'status_code': status_code,
            'status': response_status,
            'data': paginated_result
        }
        
        response= JsonResponse(response_data)
        response.status_code=status_code
        return response

class CopyStage1Layouts(APIView):
    @swagger_auto_schema(
        operation_summary="Copy layout data from one location to another of project",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                    "sourceProjectId":openapi.Schema(type=openapi.TYPE_NUMBER,description='Project Id for stage results'),
                    "destinationProjectId":openapi.Schema(type=openapi.TYPE_NUMBER,description='Stage action for stage results'),
                    "cells":openapi.Schema(type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(type=openapi.TYPE_STRING, description='List of cells'))},
            required=['projectId', 'stage', 'page', 'pageSize']
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
        source_pid = request.data['sourceProjectId']
        destination_pid = request.data['destinationProjectId']
        cells = request.data['cells']
        source_project = Project.objects.filter(pk=source_pid).first()
        destination_project = Project.objects.filter(pk=destination_pid).first()
        if not source_project:
            response = JsonResponse(vars(ProjectResponse(f'A project with id {source_pid} doesn\'t exist.', status.HTTP_404_NOT_FOUND, False)))
            response.status_code = status.HTTP_404_NOT_FOUND
            return response
        if not destination_project:
            response = JsonResponse(vars(ProjectResponse(f'A project with id {destination_pid} doesn\'t exist.', status.HTTP_404_NOT_FOUND, False)))
            response.status_code = status.HTTP_404_NOT_FOUND
            return response
        if request.user_id != source_project.created_by_id:
            response = JsonResponse(vars(ProjectResponse(f'You cannot copy files from project with id {source_pid}.', status.HTTP_401_UNAUTHORIZED, False)))
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return response
        if request.user_id != destination_project.created_by_id:
            response = JsonResponse(vars(ProjectResponse(f'You cannot copy files to project with id {destination_pid}.', status.HTTP_401_UNAUTHORIZED, False)))
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return response
        available_cells = storage_servicer.list_folders(f'{S3_BUCKET_ROOT}/Project/{request.user_id}/{source_pid}/Stage1/')
        cell_results = []
        for cell in cells:
            if cell not in available_cells:
                cell_results.append(False)
                continue
            source_path = f'{S3_BUCKET_ROOT}/Project/{request.user_id}/{source_pid}/Stage1/{cell}/'
            destination_path = f'{S3_BUCKET_ROOT}/Project/{request.user_id}/{destination_pid}/Stage1/{cell}/'
            result = storage_servicer.move_folder(source_path, destination_path)
            cell_results.append(result)
        if sum(cell_results) == len(cells):
            response = JsonResponse(vars(ProjectResponse(f'All cells folders copied from project {source_pid} to project {destination_pid}.', status.HTTP_200_OK, True)))
            response.status_code = status.HTTP_200_OK
        else:
            response = JsonResponse(vars(ProjectResponse(f'The following cells could not be copied: {[cells[i] for i in range(len(cells)) if not cell_results[i]]}', status.HTTP_417_EXPECTATION_FAILED, False)))
            response.status_code = status.HTTP_417_EXPECTATION_FAILED
        return response
    
class GetGDSJPG(APIView):
    @swagger_auto_schema(
        operation_summary="Get Image of GDS in JPG format from S3",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "LayoutData": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING, description='JPG GDS image path')
                ),
            },
            required=['LayoutData']
        ),
        responses={
            200: openapi.Response('Success', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'images': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING, description='Base64 encoded image')
                    ),
                }
            )),
            400: openapi.Response('Bad Request', openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'status': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'data': openapi.Schema(type=openapi.TYPE_OBJECT),
            }))
        }
    )
    def post(self, request):
        # Extract 'LayoutData' from the request data
        layout_data = request.data.get('LayoutData')
        
        if not layout_data:
            response_data = {
                'message': "LayoutData not provided",
                'status_code': status.HTTP_400_BAD_REQUEST,
                'status': False,
                'data': None
            }
            response = JsonResponse(response_data)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response

        # Ensure layout_data is a list
        if not isinstance(layout_data, list):
            response_data = {
                'message': "LayoutData must be an array",
                'status_code': status.HTTP_400_BAD_REQUEST,
                'status': False,
                'data': None
            }
            response = JsonResponse(response_data)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response

        # Function to retrieve and encode a single image
        def retrieve_and_encode_image(image_path):
            keypath = f'{S3_BUCKET_ROOT}/{image_path}'

            try:
                result = storage_servicer.get_image(keypath)
            except FileNotFoundError:
                response_data = {
                    'message': f"Image not found: {image_path}",
                    'status_code': status.HTTP_404_NOT_FOUND,
                    'status': False,
                    'data': None
                }
                response = JsonResponse(response_data)
                response.status_code = status.HTTP_404_NOT_FOUND
                return response

            # Ensure `result` is a file-like object
            if not hasattr(result, 'read'):
                return {
                    'error': "Invalid file object",
                    'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
                }

            # Encode the image
            GDSFileName = os.path.splitext(os.path.basename(image_path))[0]
            encoded_image = base64.b64encode(result.read()).decode('utf-8')
            return {
                'file': GDSFileName,
                'encodedImage': encoded_image
            }

        # Process each image sequentially
        encoded_images = []
        for image_path in layout_data:
            result = retrieve_and_encode_image(image_path)
            if isinstance(result, JsonResponse):
                # If we get a JsonResponse back (error), return it immediately
                return result

            encoded_images.append(result)

        # Create the response with the array of encoded images
        return JsonResponse(
            {
                'message': "Success",
                'status': True,
                'status_code': status.HTTP_200_OK,
                'images': encoded_images
            },
            content_type='application/json'
        )

class DownloadResult(APIView):
    parser_classes = [JSONParser]
    # Define responses in the schema
    @swagger_auto_schema(
        operation_summary="Download a ZIP file",
        operation_description="This endpoint allows the user to download a ZIP file containing specific project data based on the provided stage, project ID, and file types.",
        request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'stage': openapi.Schema(
                type=openapi.TYPE_INTEGER, 
                description="The stage of the project (1 or 2)"
            ),
            'project_id': openapi.Schema(
                type=openapi.TYPE_INTEGER, 
                description="The ID of the project"
            ),
            'file_types': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING),
                description="List of file types to include in the ZIP (e.g., ['gds', 'metrics', 'pex'])"
            ),
            'downloadType': openapi.Schema(type=openapi.TYPE_INTEGER, description="Type of download Cart-1, filter-2, all-3"),
            'fileList': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING,description="List of layouts which are in cart.")),
            "filter": openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "cellSelectAll": openapi.Schema(
                        type=openapi.TYPE_BOOLEAN, 
                        description="All cells selected or partial cell selection for all value is true"
                    ),
                    "cells": openapi.Schema(
                        type=openapi.TYPE_ARRAY, 
                        items=openapi.Schema(type=openapi.TYPE_STRING, description="Cell names"),
                        description="List of partially selected cells."
                    ),
                    "filterParametersName": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "filterLevel1": openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "parameterName1": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            description="Name of parameter1 to apply filter."
                                        ),
                                        "parameterName2": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            description="Name of parameter2 to apply filter."
                                        ),
                                        "filterationValue": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            description=">,<,<=,>=,=,between"
                                        ),
                                        "value1": openapi.Schema(
                                            type=openapi.TYPE_INTEGER,
                                            description="Value for filter."
                                        ),
                                        "value2": openapi.Schema(
                                            type=openapi.TYPE_INTEGER,
                                            description="Value for filter."
                                        )
                                    }
                                )
                            ),
                            "filterLevel2": openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "parameterName1": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            description="Name of parameter1 to apply filter."
                                        ),
                                        "parameterName2": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            description="Name of parameter2 to apply filter."
                                        ),
                                        "filterationValue": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            description=">,<,<=,>=,=,between"
                                        ),
                                        "value1": openapi.Schema(
                                            type=openapi.TYPE_INTEGER,
                                            description="Value for filter."
                                        ),
                                        "value2": openapi.Schema(
                                            type=openapi.TYPE_INTEGER,
                                            description="Value for filter."
                                        )
                                    }
                                )
                            )
                        }
                    )
                }
            )
        },
        required=['stage', 'project_id', 'file_types','filter','downloadType']
    ),
        responses={
            200: openapi.Response(
                'Success', 
                openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description="ZIP file download"
                )
            ),
            400: openapi.Response(
                'Bad Request', 
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description="Error message"),
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Status of the request (False if error)")
                    }
                )
            ),
            404: openapi.Response(
                'File Not Found', 
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description="Error message"),
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Status of the request (False if error)")
                    }
                )
            ),
            500: openapi.Response(
                'Internal Server Error', 
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description="Error message"),
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Status of the request (False if error)")
                    }
                )
            )
        }
    )
    def post(self, request):
        try:
            # Get data from the request body
            data = request.data
            stage = data.get('stage')
            project_id = data.get('project_id')
            file_types = data.get('file_types')
            filter = data.get('filter', None)
            download_type=data.get('downloadType',None)
            file_list=data.get('fileList',None)
            filterByLayout=data.get('filterByLayout',None)
            
            if not isinstance(project_id, int):
                response= JsonResponse(vars(StageResponse("Invalid project ID", status.HTTP_400_BAD_REQUEST, False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            project=Project.objects.filter(id=project_id).first()
            if not project or not isinstance(project_id, int):
                response= JsonResponse(vars(StageResponse("Project not found", status.HTTP_404_NOT_FOUND, False)))
                response.status_code=status.HTTP_404_NOT_FOUND
                return response
            if not project.created_by_id==request.user_id:
                response= JsonResponse(vars(StageResponse("You do not have permission to access this project.", status.HTTP_401_UNAUTHORIZED, False)))
                response.status_code=status.HTTP_401_UNAUTHORIZED
                return response
            if stage not in [1, 2] or not isinstance(stage, int):
                response= JsonResponse(vars(StageResponse("Invalid stage", status.HTTP_400_BAD_REQUEST, False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            if download_type is None or download_type not in [1,2,3,4] or not isinstance(download_type, int): 
                response= JsonResponse(vars(StageResponse("Invalid download_type", status.HTTP_400_BAD_REQUEST, False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response    
            if (download_type in [1, 2, 3]) and (file_types==[] or any(file_type not in ['gds', 'metrics', 'pex'] for file_type in file_types) or not isinstance(file_types, list) or file_types==None):
                response=JsonResponse(vars(StageResponse("Invalid file type", status.HTTP_400_BAD_REQUEST, False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            if download_type==1 and (file_list==[] or not isinstance(file_list, list) or file_list==None):
                response=JsonResponse(vars(StageResponse("Invalid file list", status.HTTP_400_BAD_REQUEST, False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            if download_type == 2 and ((filter is None or not isinstance(filter, dict)) and (filterByLayout is None or not isinstance(filterByLayout, list))):
                response = JsonResponse(vars(StageResponse("Invalid filter", status.HTTP_400_BAD_REQUEST, False)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if not project.created_by_id == request.user_id:
                response= JsonResponse(vars(StageResponse("You do not have permission to access this project.", status.HTTP_401_UNAUTHORIZED, False)))
                response.status_code=status.HTTP_401_UNAUTHORIZED
                return response
            # Get the project name
            project_name = project.project_name
            # Base path for projects
            base_path = f'{S3_BUCKET_ROOT}/Project/{request.user.id}/{project_id}/Stage{stage}/'
            # Initialize list to store folders that need to be zipped
            folders_to_zip = []
            try:
                # List folders under the base path
                cells = storage_servicer.list_folders(base_path)
            except Exception as e:
                logger.error(f"Error fetching folders from local storage: {str(e)}")
                response= JsonResponse(vars(StageResponse(f"Error fetching folders from local storage: {str(e)}", status.HTTP_404_NOT_FOUND, False)))
                response.status_code=status.HTTP_404_NOT_FOUND
                return response
            
            linkage_path = f'{base_path}Stage_Report{stage}.csv'
            detailed_data = storage_servicer.fetch_csv(linkage_path)
            
            # Download type 1 for cart 
            if download_type==1 and file_list and any(file_type in ['gds', 'metrics', 'pex'] for file_type in file_types):
                if not detailed_data.empty:
                    filelist=file_list
                    if stage==1:
                        filtered_filelist = [item for item in filelist if item in detailed_data['File'].values]
                    elif stage==2:
                        filtered_filelist = [item for item in filelist if item in detailed_data['permutationLayout'].values]
                    filelist=filtered_filelist
                    if filelist == []:
                        message = "No data found for the provided cart."
                        status_code = status.HTTP_404_NOT_FOUND
                        response_status = False
                        response = JsonResponse({
                            'message': message,
                            'status_code': status_code,
                            'response_status': response_status,
                            'data': None
                        })
                        response.status_code = status_code
                        return response
                else:
                    message = "Case report not present for this project."
                    status_code = status.HTTP_404_NOT_FOUND
                    response_status = False
                    response=JsonResponse({
                        'message': message,
                        'status_code': status_code,
                        'response_status': response_status,
                        'data': None
                    })
                    response.status_code=status_code
                    return response
                # for cell in file_list:
                #     if cell not in cells:
                #         response= JsonResponse(vars(StageResponse(f"Cell {cell} not found", status.HTTP_404_NOT_FOUND, False)))
                #         response.status_code=status.HTTP_404_NOT_FOUND
                #         return response
                #     folders_to_zip.append(f'{base_path}{cell}/')
            # Download type 2 for filter 
            elif not filter == None and not filter == {} and isinstance(filter, dict) and download_type==2 and any(file_type in ['gds', 'metrics', 'pex'] for file_type in file_types):
                if not detailed_data.empty:
                    # Replace NaN with None
                    detailed_dataframes = detailed_data.applymap(lambda x: None if pd.isna(x) else x)
                    # If 'cells' are provided, filter those rows
                    if not isinstance(filter['cellSelectAll'], bool):
                        message="Cell select all flag must be a boolean."
                        status_code=status.HTTP_400_BAD_REQUEST
                        response_status=False
                        response=JsonResponse({
                            'message': message,
                            'status_code': status_code,
                            'response_status': response_status,
                            'data': None
                        })
                        response.status_code=status_code
                        return response
                    if (filter['cells']==[] and filter['cellSelectAll']==False) or (filter['cells'] is None and filter['cellSelectAll']==False) or not isinstance(filter['cells'], list):
                        message="Cell can't be empty if select all flag is false."
                        status_code=status.HTTP_404_NOT_FOUND
                        response_status=False
                        response=JsonResponse({
                            'message': message,
                            'status_code': status_code,
                            'response_status': response_status,
                            'data': None
                        })
                        response.status_code=status_code
                        return response
                    elif filter['cells'] is not None and isinstance(filter['cells'], list) and filter['cellSelectAll']==False:
                        if "Cells" not in detailed_dataframes.columns:
                            message=f"Column 'Cell' does not exist in the DataFrame."
                            status_code=status.HTTP_400_BAD_REQUEST
                            response_status=False
                            response=JsonResponse({
                                'message': message,
                                'status_code': status_code,
                                'response_status': response_status,
                                'data': None
                            })
                            response.status_code=status_code
                            return response
                        cell_filtered_datapoints = detailed_dataframes[detailed_dataframes['Cells'].isin(filter['cells'])]
                    elif filter['cellSelectAll']==True:
                        cell_filtered_datapoints = detailed_dataframes
                    if cell_filtered_datapoints.empty:
                        message="No data found for the provided filter."
                        status_code=status.HTTP_404_NOT_FOUND
                        response_status=False
                        response=JsonResponse({
                            'message': message,
                            'status_code': status_code,
                            'response_status': response_status,
                            'data': None
                        })
                        response.status_code=status_code
                        return response
                    # Check if 'selectAllValue' is False in the first element of 'filterParametersName'
                    if not isinstance(filter['filterParametersName'], dict):
                        message="Filter parameters must be a object."
                        status_code=status.HTTP_400_BAD_REQUEST
                        response_status=False
                        response=JsonResponse({
                            'message': message,
                            'status_code': status_code,
                            'response_status': response_status,
                            'data': None
                        })
                        response.status_code=status_code
                        return response
                    if filter['filterParametersName']==None:
                        message="Filter parameters can't be null."
                        status_code=status.HTTP_400_BAD_REQUEST
                        response_status=False
                        response=JsonResponse({
                            'message': message,
                            'status_code': status_code,
                            'response_status': response_status,
                            'data': None
                        })
                        response.status_code=status_code
                        return response
                    if not filter['filterParametersName']=={} or not filter['filterParametersName']==None:
                        # Define operators for comparison
                        operators = {
                            '>': lambda x, y: x > y,
                            '<': lambda x, y: x < y,
                            '=': lambda x, y: x == y,
                            '!=': lambda x, y: x != y,
                            '>=': lambda x, y: x >= y,
                            '<=': lambda x, y: x <= y,
                            'between': lambda x, low, high: (x >= low) & (x <= high)
                        }
                        if 'filterParametersName' in filter:
                            for level, filters in filter['filterParametersName'].items():  # Iterating over each level (Level1, Level2, etc.)
                                if filters == [] or filters is None:
                                    pass
                                elif not isinstance(filters, list):
                                    message = "Filter parameters must be either a list or null."
                                    status_code = status.HTTP_400_BAD_REQUEST
                                    response_status = False
                                    response = JsonResponse({
                                        'message': message,
                                        'status_code': status_code,
                                        'response_status': response_status,
                                        'data': None
                                    })
                                    response.status_code = status_code
                                    return response
                                else:
                                    for filter_param in filters:  # Iterating over each filter within the current level
                                        # Check if filterationValue is a string
                                        if not isinstance(filter_param['filterationValue'], str):
                                            message = "Filteration value must be a string."
                                            status_code = status.HTTP_400_BAD_REQUEST
                                            response_status = False
                                            response = JsonResponse({
                                                'message': message,
                                                'status_code': status_code,
                                                'response_status': response_status,
                                                'data': None
                                            })
                                            response.status_code = status_code
                                            return response
                                        # Validate if the filterationValue is an acceptable operator
                                        operators_list = ['>', '<', '=', '!=', '>=', '<=', 'between']
                                        if filter_param['filterationValue'] not in operators_list:
                                            message = "Invalid operator."
                                            status_code = status.HTTP_400_BAD_REQUEST
                                            response_status = False
                                            response = JsonResponse({
                                                'message': message,
                                                'status_code': status_code,
                                                'response_status': response_status,
                                                'data': None
                                            })
                                            response.status_code = status_code
                                            return response
                                        # Validate parameterName1 is a string
                                        if not isinstance(filter_param['parameterName1'], str):
                                            message = "Parameter name must be a string."
                                            status_code = status.HTTP_400_BAD_REQUEST
                                            response_status = False
                                            response = JsonResponse({
                                                'message': message,
                                                'status_code': status_code,
                                                'response_status': response_status,
                                                'data': None
                                            })
                                            response.status_code = status_code
                                            return response
                                        # Validate value1 is a number
                                        if (isinstance(filter_param['value1'], (int, float, str)) and filter_param['value1'] is not None) or (isinstance(filter_param['value2'], (int, float, str)) and filter_param['value2'] is not None):
                                            pass
                                        else:
                                            message = "Value must be a number or string."
                                            status_code = status.HTTP_400_BAD_REQUEST
                                            response_status = False
                                            response = JsonResponse({
                                                'message': message,
                                                'status_code': status_code,
                                                'response_status': response_status,
                                                'data': None
                                            })
                                            response.status_code = status_code
                                            return response
                                        # Validate for 'between' operator (if it's used)
                                        if filter_param['filterationValue'] == 'between' and (not isinstance(filter_param['value1'], (int, float)) or filter_param['value1'] is None):
                                            message = "Value1 must be a number."
                                            status_code = status.HTTP_400_BAD_REQUEST
                                            response_status = False
                                            response = JsonResponse({
                                                'message': message,
                                                'status_code': status_code,
                                                'response_status': response_status,
                                                'data': None
                                            })
                                            response.status_code = status_code
                                            return response
                                        if filter_param['filterationValue'] == 'between' and (
                                            filter_param['value2'] is None or not isinstance(filter_param['value2'], (int, float))):
                                            message = "Value2 must be a number."
                                            status_code = status.HTTP_400_BAD_REQUEST
                                            response_status = False
                                            response = JsonResponse({
                                                'message': message,
                                                'status_code': status_code,
                                                'response_status': response_status,
                                                'data': None
                                            })
                                            response.status_code = status_code
                                            return response
                                        # Ensure value2 > value1 if 'between' is used
                                        if filter_param['filterationValue'] == 'between' and filter_param['value2'] < filter_param['value1']:
                                            message = "Value2 must be greater than value1."
                                            status_code = status.HTTP_400_BAD_REQUEST
                                            response_status = False
                                            response = JsonResponse({
                                                'message': message,
                                                'status_code': status_code,
                                                'response_status': response_status,
                                                'data': None
                                            })
                                            response.status_code = status_code
                                            return response
                                        # Access the filter parameters
                                        column = filter_param['parameterName1']
                                        condition = filter_param['filterationValue']
                                        value1 = filter_param['value1']
                                        value2 = filter_param['value2']
                                        
                                        if column in cell_filtered_datapoints.columns:
                                            # Check if the column contains any strings
                                            contains_string = cell_filtered_datapoints[column].apply(lambda x: isinstance(x, str)).any()
                                        else:
                                            message = f"Column '{column}' does not exist in the srage report."
                                            status_code = status.HTTP_400_BAD_REQUEST
                                            response_status = False
                                            response = JsonResponse({
                                                'message': message,
                                                'status_code': status_code,
                                                'response_status': response_status,
                                                'data': None
                                            })
                                            response.status_code = status_code
                                            return response
                                        # If the column has strings, only allow '=' operator
                                        if contains_string and condition not in ['=']:
                                            message = "Invalid operator for string column."
                                            status_code = status.HTTP_400_BAD_REQUEST
                                            response_status = False
                                            response = JsonResponse({
                                                'message': message,
                                                'status_code': status_code,
                                                'response_status': response_status,
                                                'data': None
                                            })
                                            response.status_code = status_code
                                            return response
                                        if value1 :
                                            value=value1
                                        elif value2 :
                                            value=value2
                                        else:
                                            value=None
                                        # Apply the filter dynamically
                                        if condition == 'between' and filter_param['value2'] is not None:
                                            value2 = filter_param['value2']
                                            value = np.float64(value)
                                            value2 = np.float64(value2)
                                            cell_filtered_datapoints = cell_filtered_datapoints[
                                                operators[condition](cell_filtered_datapoints[column], value1, value2)
                                            ]
                                        else:
                                            value = np.float64(value)
                                            cell_filtered_datapoints = cell_filtered_datapoints[
                                                operators[condition](cell_filtered_datapoints[column], value)
                                            ]
                            # Continue to filter and process the data as before
                            cell_filtered_datapoints = cell_filtered_datapoints.reset_index(drop=True)
                            row_indices = cell_filtered_datapoints.index
                            if stage==1:
                                filelist = cell_filtered_datapoints.iloc[row_indices]['File'].tolist()
                            elif stage==2:
                                filelist = cell_filtered_datapoints.iloc[row_indices]['permutationLayout'].tolist()
                            if filterByLayout and isinstance(filterByLayout, list):
                                filelist.extend(filterByLayout)
                                filelist=list(set(filelist))
                            if filelist == []:
                                message = "No data found for the provided filter."
                                status_code = status.HTTP_404_NOT_FOUND
                                response_status = False
                                response = JsonResponse({
                                    'message': message,
                                    'status_code': status_code,
                                    'response_status': response_status,
                                    'data': None
                                })
                                response.status_code = status_code
                                return response
                    else:
                        # Continue to filter and process the data as before
                        cell_filtered_datapoints = cell_filtered_datapoints.reset_index(drop=True)
                        row_indices = cell_filtered_datapoints.index
                        if stage==1:
                            filelist = cell_filtered_datapoints.iloc[row_indices]['File'].tolist()
                        elif stage==2:
                            filelist = cell_filtered_datapoints.iloc[row_indices]['permutationLayout'].tolist()
                        if filterByLayout and isinstance(filterByLayout, list):
                                filelist.extend(filterByLayout)
                                filelist=list(set(filelist))
                        if filelist == []:
                            message = "No data found for the provided filter."
                            status_code = status.HTTP_404_NOT_FOUND
                            response_status = False
                            response = JsonResponse({
                                'message': message,
                                'status_code': status_code,
                                'response_status': response_status,
                                'data': None
                            })
                            response.status_code = status_code
                            return response
                else:
                    message = "Case report not present for this project."
                    status_code = status.HTTP_404_NOT_FOUND
                    response_status = False
                    response=JsonResponse({
                        'message': message,
                        'status_code': status_code,
                        'response_status': response_status,
                        'data': None
                    })
                    response.status_code=status_code
                    return response  
            elif download_type==2 and filterByLayout !=[] and isinstance(filterByLayout, list) and any(file_type in ['gds', 'metrics', 'pex'] for file_type in file_types):      
                if not detailed_data.empty:
                    filelist=filterByLayout
                    if stage==1:
                        filtered_filelist = [item for item in filelist if item in detailed_data['File'].values]
                    elif stage==2:
                        filtered_filelist = [item for item in filelist if item in detailed_data['permutationLayout'].values]
                    filelist=filtered_filelist
                    if filelist == []:
                        message = "No data found for the provided cart."
                        status_code = status.HTTP_404_NOT_FOUND
                        response_status = False
                        response = JsonResponse({
                            'message': message,
                            'status_code': status_code,
                            'response_status': response_status,
                            'data': None
                        })
                        response.status_code = status_code
                        return response
                else:
                    message = "Case report not present for this project."
                    status_code = status.HTTP_404_NOT_FOUND
                    response_status = False
                    response=JsonResponse({
                        'message': message,
                        'status_code': status_code,
                        'response_status': response_status,
                        'data': None
                    })
                    response.status_code=status_code
                    return response
            # Download type 3 for download all 
            elif download_type==3:
                filelist=None
            # Download type 4 for summary and linkage file 
            elif download_type==4:
                filelist=None
                folders_to_zip.extend([f'{base_path}Run_Summary.txt',f'{base_path}Stage_Report{stage}.csv']) 
            else:
                filelist=None 
            if filelist:   
                filelist = list(set([item for item in filelist if item is not None]))
            if download_type in [1,2,3]:     
                for file_type in file_types:
                    # Directly assign the folder suffix based on the file_type and stage
                    if file_type == 'gds':
                        if filelist:
                            for file in filelist:
                                # Directly assign the folder suffix based on the file_type and stage
                                folder_suffix = 'optimizedGDS' if stage == 1 else 'permutations'
                                cell = file.split("_")[0]
                                folders_to_zip.append(f'{base_path}{cell}/{cell}_{folder_suffix}/{file}.gds')
                        else:
                            for cell in cells:
                                folder_suffix = 'optimizedGDS' if stage == 1 else 'permutations'
                                folder_path = f'{base_path}{cell}/{cell}_{folder_suffix}/'
                                folder_paths=storage_servicer.list_files(folder_path)
                                filtered_files = [file for file in folder_paths if not file.endswith('.png') and not file.endswith('.json')]
                                folders_to_zip.extend(filtered_files)
                    elif file_type == 'metrics':
                        if filelist:
                            added_cells=set()
                            for file in filelist:
                                # Extract the cell name from the file (before the first "_")
                                cell = file.split("_")[0]
                                if cell not in added_cells:  # Check if the cell is already processed
                                    folder_suffix = 'metrics'
                                    folder_path = f'{base_path}{cell}/{cell}_{folder_suffix}/'
                                    csv_file = f'{folder_path}{cell}_metrics.csv'  # Single CSV for each cell
                                    folders_to_zip.append(csv_file)
                                    added_cells.add(cell)  # Add the cell to the set to avoid duplicate processing    
                        else:           
                            for cell in cells:
                                folder_suffix = 'metrics'
                                folder_path = f'{base_path}{cell}/{cell}_{folder_suffix}/'
                                csv_file = f'{folder_path}{cell}_metrics.csv'  # Single CSV for each cell
                                folders_to_zip.append(csv_file)
                    elif file_type == 'pex':
                        if filelist:
                            added_cells=set()
                            for file in filelist:
                                # Extract the cell name from the file (before the first "_")
                                cell = file.split("_")[0]
                                if cell not in added_cells:  # Check if the cell is already processed
                                    folder_suffix = 'predictions'
                                    folder_path = f'{base_path}{cell}/{cell}_{folder_suffix}/'
                                    csv_file = f'{folder_path}{cell}_GDS_PEX_PREDICTION_ML.csv'  # Single CSV for each cell
                                    folders_to_zip.append(csv_file)
                                    added_cells.add(cell)  # Add the cell to the set to avoid duplicate processing 
                        else:
                            for cell in cells:
                                folder_suffix = 'predictions'
                                folder_path = f'{base_path}{cell}/{cell}_{folder_suffix}/'
                                csv_file = f'{folder_path}{cell}_GDS_PEX_PREDICTION_ML.csv'  # Single CSV for each cell
                                folders_to_zip.append(csv_file)
                    else:
                        continue  # Skip unknown file types
                if folders_to_zip!=[] or folders_to_zip!=None:
                    folders_to_zip.extend([f'{base_path}Run_Summary.txt',f'{base_path}Stage_Report{stage}.csv'])
            # Check if any folders were selected for zipping
            if not folders_to_zip:
                response= JsonResponse(vars(StageResponse("No valid folders found to zip.", status.HTTP_400_BAD_REQUEST, False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            try:
                # Create the ZIP file from the selected folders
                filtered_list=filelist
                additional_files = []
                for root, dirs, files_in_dir in os.walk('src/Resources/LayerProperties'):
                    for file in files_in_dir:
                        # Join the directory and file name to get the full file path
                        additional_files.append(os.path.join(root, file))
                zip_buffer, missing_files = storage_servicer.create_zip_files(folders_to_zip,additional_files,file_types,filtered_list,True)
                if zip_buffer==None:
                    message = "No data found for the provided cart."
                    status_code = status.HTTP_404_NOT_FOUND
                    response_status = False
                    response = JsonResponse({
                        'message': message,
                        'status_code': status_code,
                        'response_status': response_status,
                        'data': None
                    })
                    response.status_code = status_code
                    return response
            except Exception as e:
                logger.error(f"Error creating zip file: {str(e)}")
                response= JsonResponse(vars(StageResponse(f"Error creating zip file: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR, False)))
                response.status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                return response
            
            # Return the zip file as an HTTP response
            response = FileResponse(zip_buffer, as_attachment=True)
            response['Content-Type'] = 'application/zip'
            response['Content-Disposition'] = f'attachment; filename="{project_name}_Stage{stage}.zip"'
            response['X-Filename'] = f'{project_name}_Stage{stage}.zip'
            response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition, X-Filename'
            return response
        except ValidationError as ve:
            response= JsonResponse(ve.detail, status=400)
            response.status_code=status.HTTP_400_BAD_REQUEST
            return response
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            response= JsonResponse({'message': f"Unexpected error: {str(e)}", 'status': False}, status=500)
            response.status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            return response
        

class DownloadGDS(APIView):
    parser_classes = [JSONParser]
    # Define responses in the schema
    @swagger_auto_schema(
        operation_summary="Download a ZIP file",
        operation_description="This endpoint allows the user to download ZIP file containing data based on the provided stage, project ID, and file list.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'stage': openapi.Schema(type=openapi.TYPE_INTEGER, description="The stage of the project (1 or 2)"),
                'projectId': openapi.Schema(type=openapi.TYPE_INTEGER, description="The ID of the project"),
                'fileList': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="List of file list to include in the ZIP (e.g., ['INVD4_1_RT_6_1', 'INVX8_1_RT_6_12'])"
                ),
            },
            required=['stage', 'projectId', 'fileList']
        ),
        responses={
            200: openapi.Response(
                'Success', 
                openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description="ZIP file download"
                )
            ),
            400: openapi.Response(
                'Bad Request', 
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description="Error message"),
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Status of the request (False if error)")
                    }
                )
            ),
            404: openapi.Response(
                'File Not Found', 
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description="Error message"),
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Status of the request (False if error)")
                    }
                )
            ),
            500: openapi.Response(
                'Internal Server Error', 
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description="Error message"),
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Status of the request (False if error)")
                    }
                )
            )
        }
    )
    def post(self, request):
        try:
            # Get data from the request body
            data = request.data
            stage = data.get('stage')
            projectId = data.get('projectId')
            fileList = data.get('fileList')
            if not all([stage, projectId, fileList]):
                response= JsonResponse(vars(StageResponse("stage, projectId, and fileList are required fields.", status.HTTP_400_BAD_REQUEST, False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            if stage not in [1, 2]:
                response= JsonResponse(vars(StageResponse("invalid stage", status.HTTP_400_BAD_REQUEST, False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response

            if not fileList or not isinstance(fileList, list) or not all(isinstance(item, str) for item in fileList):
                response = JsonResponse(vars(StageResponse("invalid fileList", status.HTTP_400_BAD_REQUEST, False)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response

            if not isinstance(projectId, int):
                response= JsonResponse(vars(StageResponse("invalid projectId", status.HTTP_400_BAD_REQUEST, False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response 
            if len(fileList) == 1:
                zip_name=fileList[0]
            else:
                response= JsonResponse(vars(StageResponse("Only a single layout can be downloaded at a time.", status.HTTP_400_BAD_REQUEST, False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            # Fetch project from database
            project = Project.objects.filter(id=projectId, created_by_id=request.user.id).first()
            if not project:
                response= JsonResponse(vars(StageResponse("Project not found or you do not have permission.", status.HTTP_404_NOT_FOUND, False)))
                response.status_code=status.HTTP_404_NOT_FOUND
                return response

            # Base path for projects
            base_path = f'{S3_BUCKET_ROOT}/Project/{request.user.id}/{projectId}/Stage{stage}/'
            # Initialize list to store folders that need to be zipped
            folders_to_zip = []
            for file in fileList:
                # Directly assign the folder suffix based on the file_type and stage
                folder_suffix = 'optimizedGDS' if stage == 1 else 'permutations'
                cell = file.split("_")[0]
                folders_to_zip.append(f'{base_path}{cell}/{cell}_{folder_suffix}/{file}.gds')
            folders_to_zip.extend([f'{base_path}Run_Summary.txt',f'{base_path}Stage_Report{stage}.csv'])
            # Check if any folders were selected for zipping
            if not folders_to_zip:
                response= JsonResponse(vars(StageResponse("No valid folders found to zip.", status.HTTP_400_BAD_REQUEST, False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            try:
                # Create the ZIP file from the selected folders
                additional_files = []
                for root, dirs, files_in_dir in os.walk('src/Resources/LayerProperties'):
                    for file in files_in_dir:
                        # Join the directory and file name to get the full file path
                        additional_files.append(os.path.join(root, file))
                filtered_list=None
                zip_buffer, missing_files = storage_servicer.create_zip_files(folders_to_zip,additional_files,['gds'],filtered_list,False)
                if zip_buffer is None:
                    response= JsonResponse(vars(StageResponse(f"{', '.join(fileList)} layout not found in Bucket", status.HTTP_404_NOT_FOUND, False)))
                    response.status_code=status.HTTP_404_NOT_FOUND
                    return response
            except Exception as e:
                logger.error(f"Error creating zip file: {str(e)}")
                response= JsonResponse(vars(StageResponse(f"Error creating zip file: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR, False)))
                response.status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                return response
            
            # Return the zip file as an HTTP response
            response = FileResponse(zip_buffer, as_attachment=True)
            response['Content-Type'] = 'application/zip'
            response['Content-Disposition'] = f'attachment; filename="{zip_name}.zip"'
            response['X-Filename'] = f'{zip_name}.zip'
            response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition, X-Filename'
            return response

        except ValidationError as ve:
            response= JsonResponse(ve.detail, status=400)
            response.status_code=status.HTTP_400_BAD_REQUEST
            return response
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            response= JsonResponse({'message': f"Unexpected error: {str(e)}", 'status': False}, status=500)
            response.status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            return response

class DownloadFiles(APIView):
    parser_classes = [JSONParser]

    @swagger_auto_schema(
        operation_summary="Download files as a ZIP",
        operation_description="This endpoint allows users to download a ZIP file containing selected project files based on the provided data.",
        request_body=openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'FileName': openapi.Schema(type=openapi.TYPE_STRING, description="Name of the file to be downloaded."),
                    'DirType': openapi.Schema(type=openapi.TYPE_STRING, description="Type of directory (e.g., 'TECHFILE' or 'NETLIST')."),
                    'FileType': openapi.Schema(type=openapi.TYPE_STRING, description="Type of file (e.g., 'USER' or 'GLOBAL')."),
                    'USERNAME': openapi.Schema(type=openapi.TYPE_STRING, description="Username for user files, required if FileType is 'USER'."),
                    'FileId': openapi.Schema(type=openapi.TYPE_INTEGER, description="Unique file identifier."),
                },
                required=['FileName', 'DirType', 'FileType', 'USERNAME', 'FileId']
            ),
        ),
        responses={
            200: openapi.Response(
                description="ZIP file download",
                schema=openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="A downloadable ZIP file containing the selected project files."
                )
            ),
            400: openapi.Response(
                description="Bad Request - Invalid input or data validation errors.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Indicates if the request was successful."),
                        'status_code': openapi.Schema(type=openapi.TYPE_INTEGER, description="HTTP status code of the response."),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description="Error message providing details of the failure."),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description="Additional data related to the error (if any).")
                    }
                )
            ),
            500: openapi.Response(
                description="Internal Server Error - Error while processing the request.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Indicates if the request was successful."),
                        'status_code': openapi.Schema(type=openapi.TYPE_INTEGER, description="HTTP status code of the response."),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description="Error message providing details of the failure."),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description="Additional data related to the error (if any).")
                    }
                )
            )
        }
    )
    def post(self, request):
        try:
            # Helper function to return JsonResponse with consistent structure
            def return_error(message, status_code=400):
                return JsonResponse({
                    "status": False,
                    "status_code": status_code,
                    "message": message,
                    "data": None
                }, status=status_code)

            # Validate that request data is a non-empty list
            if not isinstance(request.data, list) or not request.data:
                return return_error("Input data must be a non-empty list.", 400)

            # Remove duplicate data based on unique identifier
            seen = set()
            unique_data = []
            for item in request.data:
                if not isinstance(item, dict):
                    return return_error(f"Each item in the input data must be a dictionary, found {type(item).__name__}.", 400)
                if not all(isinstance(item.get(field), str) for field in ['FileName', 'DirType', 'FileType', 'USERNAME']):
                    return return_error("All fields ('FileName', 'DirType', 'FileType', 'USERNAME') must be strings.", 400)

                identifier = (item.get('FileId'), item.get('FileName'), item.get('DirType'),
                            item.get('FileType'), item.get('USERNAME'))
                if identifier not in seen:
                    seen.add(identifier)
                    unique_data.append(item)

            # Validation rules
            allowed_dir_types = {"TECHFILE", "NETLIST"}
            allowed_file_types = {"USER", "GLOBAL"}
            extension_rules = {"NETLIST": ".spice", "TECHFILE": ".tech"}
            required_fields = {"FileName", "DirType", "FileType", "USERNAME"}

            # Validate each item in unique_data
            for item in unique_data:
                for field in required_fields:
                    if field not in item or not item[field]:
                        return return_error(f"{field} is required and cannot be empty.", 400)
                    if not isinstance(item[field], str):
                        return return_error(f"{field} must be a string.", 400)

                # DirType and FileType validation
                dir_type = item.get('DirType', '').upper()
                file_type = item.get('FileType', '').upper()
                if dir_type not in allowed_dir_types:
                    return return_error(f"Invalid DirType. Allowed values are 'techfile' and 'netlist'.", 400)
                if file_type not in allowed_file_types:
                    return return_error(f"Invalid FileType. Allowed values are USER and GLOBAL.", 400)  

                # FileName extension validation based on DirType
                file_name = item.get('FileName', '')
                if dir_type in extension_rules and not file_name.endswith(extension_rules[dir_type]):
                    return return_error(f"FileName should have {extension_rules[dir_type]} extension for DirType '{dir_type}'.", 400)

            # Collect all USERNAMEs for batch user query
            usernames = set(item['USERNAME'] for item in unique_data if item['FileType'].upper() == 'USER')
            users_cache = {}
            
            if usernames:
                # Fetch all users in a single query to reduce database hits
                users = User.objects.filter(username__in=[username.upper() for username in usernames])
                users_cache = {user.username.upper(): user for user in users}

            # Prepare the file paths for zipping
            files_to_zip = []
            for item in unique_data:
                file_type = item['FileType'].upper()
                if file_type == 'USER':  # For 'GLOBAL' FileType, no need for username
                    username = item['USERNAME']
                    user = users_cache.get(username.upper())
                    if not user:
                        return return_error(f"USERNAME {username} not found.", 400)
                    user_or_global_id = user.id
                else:
                    user_or_global_id = 0
                dir_type = "Techfile" if item['DirType'].upper() == "TECHFILE" else "Netlist"
                base_path = f"{S3_BUCKET_ROOT}/{dir_type}/{user_or_global_id}/{item['FileName']}"
                files_to_zip.append(base_path)

            if not files_to_zip:
                return return_error("No valid folders found to zip.", 400)

            # Attempt to create a ZIP file
            try:
                filtered_list=None
                zip_buffer, missing_files = storage_servicer.create_zip_files(files_to_zip,None,[], filtered_list,False,)
                if zip_buffer is None:
                    return return_error("No valid files in the S3 bucket found to zip.", 404)
            except Exception as e:
                logger.error(f"Error creating zip file: {str(e)}")
                return return_error(f"Error processing files. Error creating zip file: {str(e)}", 500)

            # Handle missing files
            if missing_files:
                missing_files_str = ', '.join(set(missing_files))
                for missing_file in missing_files:
                    item = next((x for x in unique_data if x['FileName'] == missing_file), None)
                    if item:
                        username = item['USERNAME']
                        user = users_cache.get(username.upper())
                        if not user:
                            return return_error(f"USERNAME '{username}' not found.", 400)
                        user_or_global_id = user.id
                    else:
                        continue  # Skip missing files without a matching item

                    FileInfo.objects.filter(
                        name=missing_file,
                        status='ACTIVE',
                        created_by_id=user_or_global_id
                    ).update(
                        status='DELETED',
                        modified_by=users_cache[username]
                    )

            # Set the filename for the zip response
            dir_type = unique_data[0].get('DirType', '').upper()
            file_name = f"{dir_type}_Files.zip" if dir_type in ['TECHFILE', 'NETLIST'] else "Files.zip"

            response = FileResponse(zip_buffer, as_attachment=True)
            response['Content-Type'] = 'application/zip'
            response['Content-Disposition'] = f'attachment; filename={file_name}'
            response['X-Filename'] = file_name
            if missing_files:
                response['X-Missing-Files'] = missing_files_str
            response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition, X-Filename, X-Missing-Files'

            return response

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return return_error(f"Unexpected error: {str(e)}", 500)
#Class to fetch summary of a project
class Summary(APIView):
    @swagger_auto_schema(
        operation_summary="Get summary result from s3 or locally.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                    "projectId":openapi.Schema(type=openapi.TYPE_NUMBER,description='Project Id for summary results'),
                    "stage":openapi.Schema(type=openapi.TYPE_NUMBER,description='Stage action for summary results'),
            },
            required=['projectId', 'stage']
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
        #stage , project_id
        project_id = request.data.get('projectId')
        stage_id = request.data.get('stage')
        user_id = request.user_id
        if (not isinstance(project_id,int)) or project_id==None:
            result = None
            message = f'A project with id {project_id} doesn\'t exist.'
            status_code = status.HTTP_404_NOT_FOUND
            response_status = False
            response = JsonResponse({
                    'message': message,
                    'status_code': status_code,
                    'response_status': response_status,
                    'result': None
                })
            response.status_code=status_code
            return response
        if not isinstance(stage_id,int) or stage_id not in [1,2] or stage_id==None:
            result = None
            message = f'Invalid stage id.'
            status_code = status.HTTP_400_BAD_REQUEST
            response_status = False
            response = JsonResponse({
                    'message': message,
                    'status_code': status_code,
                    'response_status': response_status,
                    'result': None
                })
            response.status_code=status_code
            return response          
        # Fetch the project
        project = Project.objects.filter(id=project_id).first()
        # Check if project exists and if user has access
        if not project:
            result = None
            message = f'A project with id {project_id} doesn\'t exist.'
            status_code = status.HTTP_404_NOT_FOUND
            response_status = False
            response = JsonResponse({
                    'message': message,
                    'status_code': status_code,
                    'response_status': response_status,
                    'data': None
                })
            response.status_code=status_code
            return response
        elif project.created_by_id != user_id:  # TODO: Check if user has the required permissions
            result = None
            message = 'You cannot view the results of this project.'
            status_code = status.HTTP_401_UNAUTHORIZED
            response_status = False
            response=JsonResponse({
                    'message': message,
                    'status_code': status_code,
                    'response_status': response_status,
                    'data': None
                })
            response.status_code=status_code
            return response
        else:
            job_id = Job.objects.filter(project_id=project_id, status='COMPLETED').first()
            if job_id and job_id.status == 'COMPLETED':
                result=storage_servicer.fetch_files(f'{S3_BUCKET_ROOT}/Project/{user_id}/{project_id}/Stage{stage_id}/Run_Summary.json')
                if result:
                    message = 'Results retrieved successfully.'
                    status_code = status.HTTP_200_OK
                    response_status = True
                    response=JsonResponse({
                        'message': message,
                        'status_code': status_code,
                        'response_status': response_status,
                        'data': json.loads(result.decode('utf-8'))
                    })
                    response.status_code=status_code
                    return response
                else:
                    result = None
                    message = f'A summary is not available for the results at Stage {stage_id} of the project.'
                    status_code = status.HTTP_404_NOT_FOUND
                    response_status = False
                    response=JsonResponse({
                        'message': message,
                        'status_code': status_code,
                        'response_status': response_status,
                        'data': None
                    })
                    response.status_code=status_code
                    return response
            elif project.action==2 and stage_id==1:
                result=storage_servicer.fetch_files(f'{S3_BUCKET_ROOT}/Project/{user_id}/{project_id}/Stage{stage_id}/Run_Summary.json')
                if result:
                    message = 'Results retrieved successfully.'
                    status_code = status.HTTP_200_OK
                    response_status = True
                    response=JsonResponse({
                        'message': message,
                        'status_code': status_code,
                        'response_status': response_status,
                        'data': json.loads(result.decode('utf-8'))
                    })
                    response.status_code=status_code
                    return response
                else:
                    result = None
                    message = f'A summary is not available for the results at Stage {stage_id} of the project.'
                    status_code = status.HTTP_404_NOT_FOUND
                    response_status = False
                    response=JsonResponse({
                        'message': message,
                        'status_code': status_code,
                        'response_status': response_status,
                        'data': None
                    })
                    response.status_code=status_code
                    return response
            else:
                result = None
                message = f'A summary is not available for the results at Stage {stage_id} of the project.'
                status_code = status.HTTP_404_NOT_FOUND
                response_status = False
                response=JsonResponse({
                    'message': message,
                    'status_code': status_code,
                    'response_status': response_status,
                    'data': None
                })
                response.status_code=status_code
                return response
