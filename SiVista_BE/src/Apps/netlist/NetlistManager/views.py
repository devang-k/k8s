"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: views.py  
 * Description: 1. The GetList class is a Django API view that retrieves and filters netlist files from two locations, returning a JSON response with the filtered list or an error message if no files are found.

                2. The GetData class handles POST requests to retrieve data for a given Spice file, validating the input and returning the result or an error message if the file is not found.
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
from src.Models.Netlist.NetlistResponse import NetlistResponse
from src.Apps.netlist.NetlistManager.serializer import NetlistSerializer
from src.Services.StorageServices.StorageService import storage_servicer
from src.Services.NetlistService import extract_subckt, validate_netlist
from rest_framework import status
from SiVista_BE.settings import S3_BUCKET_ROOT
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import json
import re
import base64


class GetList(APIView):
    @swagger_auto_schema(
        operation_summary="Get list of netlist files",
        responses={
            200: openapi.Response(
                "Success",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "status": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT),
                    },
                ),
            ),
            400: openapi.Response(
                "Bad Request",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "status": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT),
                    },
                ),
            ),
        },
    )
    def get(self, request):
        user_id = request.user_id
        filename1 = f"{S3_BUCKET_ROOT}/Netlist/0/"
        filename2 = f"{S3_BUCKET_ROOT}/Netlist/{user_id}/"
        mylist1 = storage_servicer.get_tech_netlist_list("GLOBAL", filename1)
        mylist2 = storage_servicer.get_tech_netlist_list("USER", filename2)
        mylist1.extend(mylist2)
        filtered_entries = [
            entry for entry in mylist1 if entry["FileName"].endswith(".spice")
        ]
        if filtered_entries != []:
            message = "Success"
            response_status = True
            status_code = status.HTTP_200_OK
            response = JsonResponse(
                vars(
                    NetlistResponse(
                        message, status_code, response_status, filtered_entries
                    )
                )
            )
            response.status_code = status_code
            return response
        else:
            message = "File not found"
            response_status = False
            status_code = status.HTTP_404_NOT_FOUND
            response = JsonResponse(
                vars(NetlistResponse(message, status_code, response_status, mylist1))
            )
            response.status_code = status_code
            return response


class GetData(APIView):
    @swagger_auto_schema(
        operation_summary="Get data for given spice file",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "FileName": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Netlist Filename with .spice extension",
                ),
                "FileType": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Netlist File Type"
                ),
                "TimeStamp": openapi.Schema(
                    type=openapi.TYPE_STRING, description="File creation time stamp"
                ),
            },
            required=["FileName", "FileType"],
        ),
        responses={
            200: openapi.Response(
                "Success",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "status": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT),
                    },
                ),
            ),
            400: openapi.Response(
                "Bad Request",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "status": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT),
                    },
                ),
            ),
        },
    )
    def post(self, request):
        try:
            user_id = request.user_id
            json_data = json.loads(request.body)
            serializers = NetlistSerializer(data=json_data)
            message, status_code, response_status, data = serializers.validate(
                json_data, user_id
            )
            response = JsonResponse(
                vars(NetlistResponse(message, status_code, response_status, data))
            )
            response.status_code = status_code
            return response
        except Exception as e:
            print(e)
            message = (
                "The file could not be found. Please check the file path and try again."
            )
            status_code = status.HTTP_404_NOT_FOUND
            response_status = False
            data = None
            response = JsonResponse(
                vars(NetlistResponse(message, status_code, response_status, data))
            )
            response.status_code = status_code
            return response


# Validate netlist content
class ValidateNetlist(APIView):
    @swagger_auto_schema(
        operation_summary="Get data for netlist to validate.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "netlistFileContent": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Encoded netlist content for validation.",
                ),
            },
            required=["netlistFileContent"],
        ),
        responses={
            200: openapi.Response(
                "SUCESS",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "status": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT),
                    },
                ),
            ),
            203: openapi.Response(
                "NON AUTHORITATIVE INFORMATION",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "status": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT),
                    },
                ),
            ),
        },
    )
    def post(self, request):
        try:
            # Get data from the request
            data1 = request.data
            netlist_data = data1.get("netlistFileContents")  # Use get to avoid KeyError
            # Check if the netlist data is a string
            if isinstance(netlist_data, str):
                # Validate if the string is base64 encoded
                if len(netlist_data) % 4 == 0 and re.match(
                    r"^[A-Za-z0-9+/=]*$", netlist_data
                ):
                    try:
                        # Attempt to decode the string, validate it
                        netlist_data = base64.b64decode(netlist_data, validate=True)
                        is_base64 = True
                    except (base64.binascii.Error, TypeError):
                        # Catch errors during decoding
                        is_base64 = False
                else:
                    is_base64 = False

                # If the content is not valid base64
                if not is_base64:
                    message = "Netlist file content must be in encoded format and can't be null."
                    status_code = status.HTTP_400_BAD_REQUEST
                    response_status = False
                    return message, status_code, response_status, None
                # Validate the decoded netlist data
                (
                    validation_result,
                    status_code,
                    response_status,
                    data,
                ) = validate_netlist(netlist_data)
                if response_status == True:
                    data["FileContent"] = data1["netlistFileContents"]
                else:
                    data = None
                response = JsonResponse(
                    vars(
                        NetlistResponse(
                            validation_result, status_code, response_status, data
                        )
                    )
                )
                response.status_code = status_code
                return response
            else:
                # Handle invalid data type for netlistFileContents
                message = "Invalid netlistFileContents data type."
                status_code = status.HTTP_203_NON_AUTHORITATIVE_INFORMATION
                response_status = False
                data = None
                response = JsonResponse(
                    vars(NetlistResponse(message, status_code, response_status, data))
                )
                response.status_code = status_code
                return response

        except Exception as e:
            # Log the exception and return a generic error message
            print(e)
            message = "Invalid Netlist"
            status_code = status.HTTP_203_NON_AUTHORITATIVE_INFORMATION
            response_status = False
            data = None
            response = JsonResponse(
                vars(NetlistResponse(message, status_code, response_status, data))
            )
            response.status_code = status_code
            return response
