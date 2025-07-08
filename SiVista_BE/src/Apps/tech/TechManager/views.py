"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: views.py  
 * Description:     /getlist/: In GetList a list of netlist files. It is named getList.
                    /getdata/: In GetData  retrieve data for a specific netlist file. It is named getNetlistData.
 *  
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
from rest_framework.views import APIView
from django.http import JsonResponse
from src.Services.StorageServices.StorageService import storage_servicer
from src.Models.Tech.TechResponse import TechResponse
from src.Apps.tech.TechManager.serializer import TechSerializer
from SiVista_BE.settings import S3_BUCKET_ROOT
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from drf_yasg import openapi
import json

# Create your views here.
class GetList(APIView):
    @swagger_auto_schema(
        operation_summary="Get list of tech files",
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
        user_id=request.user_id
        filename1=f'{S3_BUCKET_ROOT}/Techfile/0/'
        filename2=f'{S3_BUCKET_ROOT}/Techfile/{user_id}/'
        mylist1=storage_servicer.get_tech_netlist_list("GLOBAL",filename1)
        mylist2=storage_servicer.get_tech_netlist_list("USER",filename2)
        mylist1.extend(mylist2)
        filtered_entries = [entry for entry in mylist1 if entry['FileName'].endswith(".tech")]
        if filtered_entries != []:
            message="Success"
            response_status=True
            status_code=status.HTTP_200_OK
            response= JsonResponse(vars(TechResponse(message,status_code,response_status,filtered_entries)))
            response.status_code=status_code
            return response
        else:
            message="File not found"
            response_status=False
            status_code=status.HTTP_404_NOT_FOUND
            response= JsonResponse(vars(TechResponse(message,status_code,response_status,mylist1)))
            response.status_code=status_code
            return response
        
class GetData(APIView):
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
            json_data = json.loads(request.body)
            serializers= TechSerializer(data=json_data)
            message,status_code,response_status,data1 = serializers.validate(json_data,user_id)
            response= JsonResponse(vars(TechResponse(message,status_code,response_status,data1)))
            response.status_code=status_code
            return response
        except Exception as e:
            message = f"Error in getting data: {str(e)}"
            status_code = status.HTTP_400_BAD_REQUEST
            response_status = False
            data1 = None
            response = JsonResponse(vars(TechResponse(message, status_code, response_status, data1)))
            response.status_code = status_code
            return response
                