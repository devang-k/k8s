"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: views.py  
 * Description: path('netlist/upload/', UploadNetlist.as_view(), name='UploadNetlist')
Description: This URL route is associated with the UploadNetlist class. It handles the functionality for uploading a netlist file to the server.

path('delete/file/', DeleteFile.as_view(), name='DeleteFile')
Description: This URL route maps to the DeleteFile class. It provides functionality to delete a specified file from the server.

path('modify/file/', ModifyFile.as_view(), name='ModifyFile')
Description: This URL route is linked to the ModifyFile class. It allows modification of an existing file on the server based on the user's request.

path('tech/upload/', UploadTech.as_view(), name='UploadTech')
Description: This URL route connects to the UploadTech class. It handles the upload of technology-related files to the server.

path('getlist/', GetList.as_view(), name='GetFileList')
Description: This URL is mapped to the GetList class. It retrieves and returns a list of available files stored on the server.

path('getdata/', GetTechData.as_view(), name='GetTechData')
Description: This URL route is linked to the GetTechData class. It retrieves and returns specific technology data from the server, likely related to uploaded tech files.
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
from src.Services.NetlistService import validate_netlist
from src.Services.StorageServices.StorageService import storage_servicer
from src.Services.EncryptDecryptService import encrypt_file_content, decrypt_file_content, InvalidToken
from rest_framework import status
from src.Models.Admin.AdminResponse import AdminResponse
from SiVista_BE.settings import S3_BUCKET_ROOT
from src.Apps.user.Login.models import User
from src.Apps.project.ProjectManager.models import FileInfo
from django.db.models import Case, When,F
from django.core.paginator import Paginator, EmptyPage
from drf_yasg.utils import swagger_auto_schema
from django.utils.datastructures import MultiValueDictKeyError  # Import the error class
from redis.exceptions import ConnectionError
from drf_yasg import openapi
from django.core.cache import cache
from json import dumps
import base64
import time
from datetime import datetime
import redis
from django.utils import timezone
import re

class UploadNetlist(APIView):
    @swagger_auto_schema(
        operation_summary="Upload netlist file",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'upload': openapi.Schema(
                    type=openapi.TYPE_FILE,
                    description='File to upload (netlist format)',
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
        user=User.objects.filter(id=request.user_id).first()
        if user.is_staff == True:
            try:
                if 'upload' not in request.FILES or request.FILES['upload'].size == 0:
                    message = "The file is missing. Please upload a valid file."
                    response = JsonResponse(vars(AdminResponse(message, status.HTTP_400_BAD_REQUEST, False)))
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return response
                if request.FILES['upload'].size > 5242880: # 5242880 bytes = 5 mb upload limit
                    message = "Please upload a file less than 5 MB."
                    response = JsonResponse(vars(AdminResponse(message, status.HTTP_400_BAD_REQUEST, False)))
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return response
                upload = request.FILES['upload']
                if (upload.name).endswith('.spice'):
                    myList=storage_servicer.get_tech_netlist_list('GLOBAL', f'{S3_BUCKET_ROOT}/Netlist/0/')
                    filenames = [file['FileName'] for file in myList]
                    if upload.name not in filenames:
                        start_time = time.time()
                        netlist_content = upload.read()
                        try:
                            # Attempt to decrypt to validate the file
                            _ = decrypt_file_content(netlist_content)  # We're not using the result, just validating
                        except InvalidToken:
                            message = "Uploaded file is not encrypted with the correct key or is in plaintext."
                            response = JsonResponse(vars(AdminResponse(message, status.HTTP_400_BAD_REQUEST, False)))
                            response.status_code = status.HTTP_400_BAD_REQUEST
                            return response
                        (
                            validation_result, status_code, response_status, data
                            ) = validate_netlist(decrypt_file_content(netlist_content).encode("utf-8"))
                        if response_status == False:
                            
                            message = validation_result
                            response = JsonResponse(vars(AdminResponse(message, status_code, False, data)))
                            response.status_code = status_code
                            return response
                        elif response_status:
                            netlist_content = netlist_content.decode('utf-8')
                            response_status=storage_servicer.write_file(f'{S3_BUCKET_ROOT}/Netlist/0/{upload.name}',netlist_content , 1)
                            time_taken = time.time() - start_time 
                            if response_status:
                                file_size = upload.size / 1024  # Convert bytes to KB
                                name=upload.name
                                file=FileInfo.objects.create(name=name,type='NETLIST',dir='GLOBAL',status='ACTIVE', filesize=file_size, created_by=user)
                                if file:
                                    try:
                                        key=f"get_all_files_{request.user.id}_NETLIST"
                                        cache.delete(key)
                                    except ConnectionError:
                                        pass
                                    response= JsonResponse(vars(AdminResponse(f'file stored at /Netlist/0/{upload.name}. It took {time_taken} s to upload',status.HTTP_200_OK,response_status)))
                                    response.status_code=status.HTTP_200_OK
                                    return response
                                else:
                                    storage_servicer.delete_file(f'{S3_BUCKET_ROOT}/Netlist/0/{upload.name}')
                                    response = JsonResponse(vars(AdminResponse(f'Failed to save record for {upload.name}. Kindly co-ordinate with administrator.',status.HTTP_400_BAD_REQUEST,response_status)))
                                    response.status_code=status.HTTP_400_BAD_REQUEST
                                    return response
                            else:
                                response = JsonResponse(vars(AdminResponse(f'Failed to save file {upload.name}.',status.HTTP_400_BAD_REQUEST,response_status)))
                                response.status_code=status.HTTP_400_BAD_REQUEST
                                return response
                        else:
                            response = JsonResponse(vars(AdminResponse(f'Error occurred during validation file {upload.name}.',status.HTTP_400_BAD_REQUEST,response_status)))
                            response.status_code=status.HTTP_400_BAD_REQUEST
                            return response
                    else:
                        response = JsonResponse(vars(AdminResponse(f'File already present with same file name.',status.HTTP_400_BAD_REQUEST,False)))
                        response.status_code=status.HTTP_400_BAD_REQUEST
                        return response
                else:
                    response = JsonResponse(vars(AdminResponse(f'File extension is not correct.Could you please review the file and provide Spice file',status.HTTP_400_BAD_REQUEST,False)))
                    response.status_code=status.HTTP_400_BAD_REQUEST
                    return response
            except MultiValueDictKeyError:
                # In case of error, respond with the appropriate message
                message = "Missing file in request."
                responseStatus = status.HTTP_404_NOT_FOUND
                return JsonResponse(vars(AdminResponse(message, responseStatus, False)))
        else:
            response = JsonResponse(vars(AdminResponse(f'You do not have permission to add files.',status.HTTP_400_BAD_REQUEST,False)))
            response.status_code=status.HTTP_400_BAD_REQUEST
            return response
    """def get(self, request):
        filePath = request.POST['filePath']
        fileData = getFile(filePath)
        if fileData['success']:
            response = JsonResponse(vars(LoginResponse(str(fileData['response'].streaming_content),status.HTTP_200_OK,True)))
        else:
            response = JsonResponse(vars(LoginResponse('invalid file path',status.HTTP_404_NOT_FOUND,False)))"""
    
class DeleteFile(APIView):
    @swagger_auto_schema(
        operation_summary="Delete file.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'FileId':openapi.Schema(type=openapi.TYPE_INTEGER,description="Id of file."),
                'FileName': openapi.Schema(type=openapi.TYPE_STRING, description='Name of file.'),
                'DirType': openapi.Schema(type=openapi.TYPE_STRING, description='Netlist or Tech type of file.'),
                'FileType': openapi.Schema(type=openapi.TYPE_STRING, description='Global or user type of file.'),
                'USERNAME': openapi.Schema(type=openapi.TYPE_STRING, description='Username who created file.') 
                },
            required=['FileId','FileName','DirType','FileType','USERNAME']
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
    def delete(self, request):
        user = User.objects.filter(id=request.user.id).first()  # Correct way to access the logged-in user
        if user and user.is_staff:  # Check if user exists and is a staff member
            data = request.data
            fileId=data['FileId']
            fileName=data['FileName']
            dirType=data['DirType']
            fileType = data['FileType']
            userName=data['USERNAME']
            if (not isinstance(fileId , int)) or fileId==None:
                response= JsonResponse(vars(AdminResponse('FileId must be integer value',status.HTTP_400_BAD_REQUEST,False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            if (not isinstance(dirType , str)) or dirType==None:
                response= JsonResponse(vars(AdminResponse('DirType must be string value',status.HTTP_400_BAD_REQUEST,False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            if (not isinstance(fileType , str)) or fileType==None:
                response= JsonResponse(vars(AdminResponse('FileId must be string value',status.HTTP_400_BAD_REQUEST,False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            if (not isinstance(userName , str)) or userName==None:
                response= JsonResponse(vars(AdminResponse('FileId must be string value',status.HTTP_400_BAD_REQUEST,False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            if isinstance(fileName, str) or fileName.strip()!="" or fileName!=None:
                if dirType.upper() == 'NETLIST':
                    ftype='Netlist'
                    extenssion='.spice'
                elif dirType.upper()=='TECH':
                    ftype='Techfile'
                    extenssion='.tech'
                else:
                    response= JsonResponse(vars(AdminResponse(f'The directory type {dirType} is not valid. Allowed types are: NETLIST, TECH.',status.HTTP_400_BAD_REQUEST, False)))
                    response.status_code=status.HTTP_400_BAD_REQUEST
                    return response
                if not fileName.endswith(extenssion):
                    response= JsonResponse(vars(AdminResponse('Invalid file extenssion.',status.HTTP_400_BAD_REQUEST,False)))
                    response.status_code=status.HTTP_400_BAD_REQUEST
                    return response
                if fileType.upper()=='GLOBAL':
                    dtype=0
                elif fileType.upper()=='USER':
                    getuser=User.objects.filter(username=userName.upper()).first()
                    if getuser:
                        dtype=getuser.id
                    else:
                        response= JsonResponse(vars(AdminResponse(f'{userName} not found in record.',status.HTTP_404_NOT_FOUND, False)))
                        response.status_code=status.HTTP_404_NOT_FOUND
                        return response
                else:
                    response= JsonResponse(vars(AdminResponse(f'The file type {fileType} is not valid. Allowed types are: USER, GLOBAL.',status.HTTP_400_BAD_REQUEST, False)))
                    response.status_code=status.HTTP_400_BAD_REQUEST
                    return response
                filepath = f'{S3_BUCKET_ROOT}/{ftype}/{dtype}/{fileName}'  # Corrected to use filename directly from data
                file=FileInfo.objects.filter(id=fileId,type=dirType.upper(), dir=fileType.upper(),name=fileName, status='ACTIVE').first()
                if file:
                    if storage_servicer.delete_file(filepath): 
                        file.status='DELETED'
                        file.modified_by=user
                        file.modified_date=timezone.now()
                        file.save()
                        try:
                            key=f"get_all_files_{request.user.id}_{dirType.upper()}"
                            cache.delete(key)
                        except Exception as e:
                            pass
                        response= JsonResponse(vars(AdminResponse('File deleted successfully.',status.HTTP_200_OK, True)))
                        response.status_code=status.HTTP_200_OK
                        return response
                    else:
                        file.status='DELETED'
                        file.modified_by = user
                        file.modified_date=timezone.now()
                        file.save()
                        try:
                            key=f"get_all_files_{request.user.id}_{dirType.upper()}"
                            cache.delete(key)
                        except Exception as e:
                            pass
                        response= JsonResponse(vars(AdminResponse('File not found.',status.HTTP_404_NOT_FOUND, False)))
                        response.status_code=status.HTTP_404_NOT_FOUND
                        return response
                else:
                    response= JsonResponse(vars(AdminResponse('DB record not found.',status.HTTP_404_NOT_FOUND, False)))
                    response.status_code=status.HTTP_404_NOT_FOUND
                    return response  
            else:
                response= JsonResponse(vars(AdminResponse('FileName must be string value',status.HTTP_400_BAD_REQUEST,False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
        else:
            response= JsonResponse(vars(AdminResponse('You do not have the necessary permissions to perform this action.',status.HTTP_401_UNAUTHORIZED,False)))
            response.status_code=status.HTTP_401_UNAUTHORIZED
            return response

class ModifyFile(APIView):
    @swagger_auto_schema(
        operation_summary="Modify file.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'FileId':openapi.Schema(type=openapi.TYPE_INTEGER,description="Id of file."),
                'FileName': openapi.Schema(type=openapi.TYPE_STRING, description='Name of file.'),
                'DirType': openapi.Schema(type=openapi.TYPE_STRING, description='Netlist or Tech type of file.'),
                'FileType': openapi.Schema(type=openapi.TYPE_STRING, description='Global or user type of file.'),
                'USERNAME': openapi.Schema(type=openapi.TYPE_STRING, description='Username who created file.') ,
                'FileContents': openapi.Schema(type=openapi.TYPE_STRING, description='File content in encrypted format.')
                },
            required=['FileId','FileName','DirType','FileType','USERNAME','FileContents']
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
    def put(self, request):
        user = User.objects.filter(id=request.user_id).first()  # Correct way to access the logged-in user
        if user and user.is_staff:  # Check if user exists and is a staff member
            data = request.data
            fileId=data['FileId']
            fileName=data['FileName']
            dirType=data['DirType']
            fileType = data['FileType']
            userName=data['USERNAME']
            if (not isinstance(fileId , int)) or fileId==None:
                response= JsonResponse(vars(AdminResponse('FileId must be integer value',status.HTTP_400_BAD_REQUEST,False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            if (not isinstance(dirType , str)) or dirType==None:
                response= JsonResponse(vars(AdminResponse('DirType must be string value',status.HTTP_400_BAD_REQUEST,False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            if (not isinstance(fileType , str)) or fileType==None:
                response= JsonResponse(vars(AdminResponse('FileId must be string value',status.HTTP_400_BAD_REQUEST,False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            if (not isinstance(userName , str)) or userName==None:
                response= JsonResponse(vars(AdminResponse('FileId must be string value',status.HTTP_400_BAD_REQUEST,False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            if data['FileContents'] == "" or data['FileContents'] == None:
                message = "Netlist File content must be valid string value."
                status_code = status.HTTP_400_BAD_REQUEST
                response_status = False
                response= JsonResponse(vars(AdminResponse(message, status_code, response_status, None)))
                response.status_code=status_code
                return response
            if dirType.upper()=='TECH' and (fileType.upper()=='USER' or fileType.upper()=='GLOBAL'):
                if not isinstance(data['FileContents'], list):
                    message = "File content must be list value."
                    status_code = status.HTTP_400_BAD_REQUEST
                    response_status = False
                    response= JsonResponse(vars(AdminResponse(message, status_code, response_status, None)))
                    response.status_code=status_code
                    return response
                else:
                    filecontent=dumps(data['FileContents'])
                    filecontent=encrypt_file_content(filecontent)
                    content_type=1
            else:
                if not isinstance(data['FileContents'], str):
                    message = "File content must be string value."
                    status_code = status.HTTP_400_BAD_REQUEST
                    response_status = False
                    response= JsonResponse(vars(AdminResponse(message, status_code, response_status, None)))
                    response.status_code=status_code
                    return response
                if (len(data['FileContents']) % 4 == 0 and (re.match(r'^[A-Za-z0-9+/=]*$', data['FileContents']))):
                    # Attempt to decode the string. If it fails, it's not valid base64
                    base64.b64decode(data['FileContents'], validate=True)
                    isbase64 = True
                else:
                    isbase64 = False
                if isbase64:
                    filecontent = base64.b64decode(data['FileContents']).decode('utf-8')
                    filecontent=encrypt_file_content(filecontent)
                    content_type=1
                else:
                    message = "File content must be in encoded format."
                    status_code = status.HTTP_400_BAD_REQUEST
                    response_status = False
                    response= JsonResponse(vars(AdminResponse(message, status_code, response_status, None)))
                    response.status_code=status_code
                    return response
            
            if not isinstance(fileName, str) or fileName == "" or fileName == None or fileName== '.spice':
                message = "File name must be valid string value."
                status_code = status.HTTP_400_BAD_REQUEST
                response_status = False
                response= JsonResponse(vars(AdminResponse(message, status_code, response_status, None)))
                response.status_code=status_code
                return response
            if dirType.upper() == 'NETLIST':
                ftype='Netlist'
                extenssion='.spice'
            elif dirType.upper()=='TECH':
                ftype='Techfile'
                extenssion='.tech'
            else:
                response= JsonResponse(vars(AdminResponse(f'The directory type {dirType} is not valid. Allowed types are: NETLIST, TECH.',status.HTTP_400_BAD_REQUEST, False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            if not fileName.endswith(extenssion):
                response= JsonResponse(vars(AdminResponse('Invalid file extenssion.',status.HTTP_400_BAD_REQUEST,False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            if fileType.upper()=='GLOBAL':
                dtype=0
            elif fileType.upper()=='USER':
                getuser=User.objects.filter(username=userName.upper()).first()
                if getuser:
                    dtype=getuser.id
                else:
                    response= JsonResponse(vars(AdminResponse(f'{userName} not found in record.',status.HTTP_404_NOT_FOUND, False)))
                    response.status_code=status.HTTP_404_NOT_FOUND
                    return response
            else:
                response= JsonResponse(vars(AdminResponse(f'The file type {fileType} is not valid. Allowed types are: USER, GLOBAL.',status.HTTP_400_BAD_REQUEST, False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            filepath = f'{S3_BUCKET_ROOT}/{ftype}/{dtype}/{fileName}'  # Corrected to use filename directly from data
            file=FileInfo.objects.filter(id=fileId,type=dirType.upper(), dir=fileType.upper(),name=fileName, status='ACTIVE').first()
            if file:
                if not storage_servicer.write_file(filepath, filecontent, content_type):
                    message = "The tech file could not be updated. Please check the process and try again."
                    status_code = status.HTTP_404_NOT_FOUND
                    response_status = False
                    response= JsonResponse(vars(AdminResponse(message, status_code, response_status, None)))
                    response.status_code=status_code
                    return response
                file.filesize = storage_servicer.get_bucket_file_size(filepath)                
                file.modified_by=User.objects.filter(id=request.user_id).first()
                file.modified_date=timezone.now()
                file.save()
                try:
                    key=f"get_all_files_{request.user.id}_{dirType.upper()}"
                    cache.delete(key)
                except ConnectionError:
                    pass
                message = "File modified successfully."
                status_code = status.HTTP_200_OK
                response_status = True
                response= JsonResponse(vars(AdminResponse(message, status_code, response_status, None)))
                response.status_code=status_code
                return response
            else:
                try:
                    key=f"get_all_files_{request.user.id}_{dirType.upper()}"
                    cache.delete(key)
                except ConnectionError:
                    pass
                response= JsonResponse(vars(AdminResponse('Record not found.',status.HTTP_404_NOT_FOUND, False)))
                response.status_code=status.HTTP_404_NOT_FOUND
                return response
        else:
            response = JsonResponse(vars(AdminResponse('You do not have the necessary permissions to perform this action.',status.HTTP_401_UNAUTHORIZED,False)))
            response.status_code=status.HTTP_401_UNAUTHORIZED
            return response

class UploadTech(APIView):
    @swagger_auto_schema(
        operation_summary="Upload tech file",
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
        user=User.objects.filter(id=request.user_id).first()
        if user.is_staff == True:
            if 'upload' not in request.FILES or request.FILES['upload'].size == 0:
                message = "The file is missing. Please upload a valid file."
                response = JsonResponse(vars(AdminResponse(message, status.HTTP_400_BAD_REQUEST, False)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if request.FILES['upload'].size > 5242880: # 5242880 bytes = 5 mb upload limit
                message = "Please upload a file less than 5 MB."
                response = JsonResponse(vars(AdminResponse(message, status.HTTP_400_BAD_REQUEST, False)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            upload = request.FILES['upload']
            if (upload.name).endswith('.tech'):
                myList=storage_servicer.get_tech_netlist_list('GLOBAL', f'{S3_BUCKET_ROOT}/Techfile/0/')
                filenames = [file['FileName'] for file in myList]
                if upload.name not in filenames:
                    start_time = time.time()
                    tech_content = upload.read()
                    try:
                        # Attempt to decrypt to validate the file
                        _ = decrypt_file_content(tech_content)  # We're not using the result, just validating
                    except InvalidToken:
                        message = "Uploaded file is not encrypted with the correct key or is in plaintext."
                        response = JsonResponse(vars(AdminResponse(message, status.HTTP_400_BAD_REQUEST, False)))
                        response.status_code = status.HTTP_400_BAD_REQUEST
                        return response
                    tech_content = tech_content.decode('utf-8')
                    response_status=storage_servicer.write_file(f'{S3_BUCKET_ROOT}/Techfile/0/{upload.name}',tech_content , 1)
                    time_taken = time.time() - start_time 
                    if response_status:
                        name=upload.name
                        file_size = upload.size / 1024  # Convert bytes to KB
                        file=FileInfo.objects.create(name=name,type='TECH',dir='GLOBAL',status='ACTIVE', filesize=file_size, created_by=user)
                        if file:
                            try:
                                key=f"get_all_files_{request.user.id}_TECH"
                                cache.delete(key)
                            except ConnectionError:
                                pass
                            response= JsonResponse(vars(AdminResponse(f'file stored at /Techfile/0/{upload.name}. It took {time_taken} s to upload',status.HTTP_200_OK,response_status)))
                            response.status_code=status.HTTP_200_OK
                            return response
                        else:
                            storage_servicer.delete_file(f'{S3_BUCKET_ROOT}/Techfile/0/{upload.name}')
                            response = JsonResponse(vars(AdminResponse(f'Failed to save record for {upload.name}. Kindly co-ordinate with administrator.',status.HTTP_400_BAD_REQUEST,response_status)))
                            response.status_code=status.HTTP_400_BAD_REQUEST
                            return response
                    else:
                        response = JsonResponse(vars(AdminResponse(f'Failed to save file {upload.name}.',status.HTTP_400_BAD_REQUEST,response_status)))
                        response.status_code=status.HTTP_400_BAD_REQUEST
                        return response
                else:
                    response = JsonResponse(vars(AdminResponse(f'File already present with same file name.',status.HTTP_400_BAD_REQUEST,False)))
                    response.status_code=status.HTTP_400_BAD_REQUEST
                    return response
            else:
                response = JsonResponse(vars(AdminResponse(f'File extension is not correct.Could you please review the file and provide tech file',status.HTTP_400_BAD_REQUEST,False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
        else:
            response = JsonResponse(vars(AdminResponse(f'You do not have the necessary permissions to perform this action.',status.HTTP_400_BAD_REQUEST,False)))
            response.status_code=status.HTTP_400_BAD_REQUEST
            return response
    """def get(self, request):
        filePath = request.POST['filePath']
        fileData = getFile(filePath)
        if fileData['success']:
            response = JsonResponse(vars(AdminResponse(str(fileData['response'].streaming_content),status.HTTP_200_OK,True,None)))
        else:
            response = JsonResponse(vars(AdminResponse('invalid file path',status.HTTP_404_NOT_FOUND,False,None)))"""
         
class GetList(APIView):
    @swagger_auto_schema(
        operation_summary="Modify file from Global Netlist Folder.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'Filetype': openapi.Schema(type=openapi.TYPE_STRING, description='Filetype either netlist or tech.'),
                'page': openapi.Schema(type=openapi.TYPE_INTEGER, description='Page number'),
                "pageSize":openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of elements per page.'),
                },
            required=['FileName']
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
        user = User.objects.filter(id=request.user.id).first()  # Correct way to access the logged-in user
        if user.is_staff==False: 
            response= JsonResponse(vars(AdminResponse('You do not have the necessary permissions to perform this action.',status.HTTP_401_UNAUTHORIZED,False))) 
            response.status_code=status.HTTP_401_UNAUTHORIZED
            return response
        data= request.data
        filetype=data['Filetype']
        fileSizeUnit = "KB"
        if filetype == "" or filetype==None or not isinstance(filetype, str):
            response= JsonResponse(vars(AdminResponse(f'The file type {filetype} is not valid. Allowed types are: USER, GLOBAL.',status.HTTP_401_UNAUTHORIZED,False))) 
            response.status_code=status.HTTP_401_UNAUTHORIZED
            return response
        try:
            key=f"get_all_files_{request.user.id}_{filetype.upper()}"
            if cache.get(key) is not None:
                MyList=cache.get(key)
            else:
                MyList=list()
                if filetype.upper()=='NETLIST':
                    distinct_global_file_list = FileInfo.objects.filter(dir='GLOBAL',status='ACTIVE',type='NETLIST').annotate(userId=Case(When(created_by__isnull=False, then=F('created_by')),default=F('modified_by')),date_to_use=Case(When(modified_date__isnull=False, then=F('modified_date')),default=F('created_date'))).values('id','name','type','dir','userId', 'filesize', 'date_to_use').distinct().order_by('name')
                    distinct_user_dir_list = FileInfo.objects.filter(dir='USER',status='ACTIVE',type='NETLIST').annotate(userId=Case(When(created_by__isnull=False, then=F('created_by')),default=F('modified_by')),date_to_use=Case(When(modified_date__isnull=False, then=F('modified_date')),default=F('created_date'))).values('id','name','type','dir','userId','filesize', 'date_to_use').distinct().order_by('created_by', 'name')
                elif filetype.upper()=='TECH':
                    distinct_global_file_list = FileInfo.objects.filter(dir='GLOBAL',status='ACTIVE',type='TECH').annotate(userId=Case(When(created_by__isnull=False, then=F('created_by')),default=F('modified_by')),date_to_use=Case(When(modified_date__isnull=False, then=F('modified_date')),default=F('created_date'))).values('id','name','type','dir','userId', 'filesize','date_to_use').distinct().order_by('name')
                    distinct_user_dir_list = FileInfo.objects.filter(dir='USER',status='ACTIVE',type='TECH').annotate(userId=Case(When(created_by__isnull=False, then=F('created_by')),default=F('modified_by')),date_to_use=Case(When(modified_date__isnull=False, then=F('modified_date')),default=F('created_date'))).values('id','name','type','dir','userId','filesize','date_to_use').distinct().order_by('created_by', 'name')
                else:
                    response= JsonResponse(vars(AdminResponse(f"The file type {filetype} is not valid. Allowed types are: USER, GLOBAL.",status.HTTP_400_BAD_REQUEST,False))) 
                    response.status_code=status.HTTP_400_BAD_REQUEST
                    return response
                for element in distinct_global_file_list:
                    extractuser=User.objects.filter(id=element['userId']).first()
                    refactor_element={'FileId':element['id'],'FileName':element['name'],'DirType':element['type'],'FileType':element['dir'], 'FileSize':element['filesize'],'Unit':fileSizeUnit,'TimeStamp':element['date_to_use'],'USERNAME':extractuser.username}
                    MyList.append(refactor_element)
                for element in distinct_user_dir_list:
                    extractuser=User.objects.filter(id=element['userId']).first()
                    refactor_element={'FileId':element['id'],'FileName':element['name'],'DirType':element['type'],'FileType':element['dir'],'FileSize':element['filesize'],'Unit':fileSizeUnit,'TimeStamp':element['date_to_use'],'USERNAME':extractuser.username}
                    MyList.append(refactor_element)
                if MyList:
                    cache.set(key,MyList,1800)
                if MyList == []:
                    response= JsonResponse(vars(AdminResponse(f"No files found in the user or global folder. Please upload at least one file in the global folder.",status.HTTP_404_NOT_FOUND,False))) 
                    response.status_code=status.HTTP_404_NOT_FOUND
                    return response
        except ConnectionError:
            MyList=list()
            if filetype.upper()=='NETLIST':
                distinct_global_file_list = FileInfo.objects.filter(dir='GLOBAL',status='ACTIVE',type='NETLIST').annotate(userId=Case(When(created_by__isnull=False, then=F('created_by')),default=F('modified_by')),date_to_use=Case(When(modified_date__isnull=False, then=F('modified_date')),default=F('created_date'))).values('id','name','type','dir','userId', 'filesize','date_to_use').distinct().order_by('name')
                distinct_user_dir_list = FileInfo.objects.filter(dir='USER',status='ACTIVE',type='NETLIST').annotate(userId=Case(When(created_by__isnull=False, then=F('created_by')),default=F('modified_by')),date_to_use=Case(When(modified_date__isnull=False, then=F('modified_date')),default=F('created_date'))).values('id','name','type','dir','userId','filesize','date_to_use').distinct().order_by('created_by', 'name')
            elif filetype.upper()=='TECH':
                distinct_global_file_list = FileInfo.objects.filter(dir='GLOBAL',status='ACTIVE',type='TECH').annotate(userId=Case(When(created_by__isnull=False, then=F('created_by')),default=F('modified_by')),date_to_use=Case(When(modified_date__isnull=False, then=F('modified_date')),default=F('created_date'))).values('id','name','type','dir','userId','filesize','date_to_use').distinct().order_by('name')
                distinct_user_dir_list = FileInfo.objects.filter(dir='USER',status='ACTIVE',type='TECH').annotate(userId=Case(When(created_by__isnull=False, then=F('created_by')),default=F('modified_by')),date_to_use=Case(When(modified_date__isnull=False, then=F('modified_date')),default=F('created_date'))).values('id','name','type','dir','userId','filesize','date_to_use').distinct().order_by('created_by', 'name')
            else:
                response= JsonResponse(vars(AdminResponse(f"The file type {filetype} is not valid. Allowed types are: USER, GLOBAL.",status.HTTP_400_BAD_REQUEST,False))) 
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            for element in distinct_global_file_list:
                extractuser=User.objects.filter(id=element['userId']).first()
                refactor_element={'FileId':element['id'],'FileName':element['name'],'DirType':element['type'],'FileType':element['dir'],'FileSize':element['filesize'],'Unit':fileSizeUnit,'TimeStamp':element['date_to_use'],'USERNAME':extractuser.username}
                MyList.append(refactor_element)
            for element in distinct_user_dir_list:
                extractuser=User.objects.filter(id=element['userId']).first()
                refactor_element={'FileId':element['id'],'FileName':element['name'],'DirType':element['type'],'FileType':element['dir'],'FileSize':element['filesize'],'Unit':fileSizeUnit,'TimeStamp':element['date_to_use'],'USERNAME':extractuser.username}
                MyList.append(refactor_element)
            if MyList == []:
                response= JsonResponse(vars(AdminResponse(f"No files found in the user or global folder. Please upload at least one file in the global folder.",status.HTTP_404_NOT_FOUND,False))) 
                response.status_code=status.HTTP_404_NOT_FOUND
                return response
        try:
            page_number = int(request.data.get('page', 0)) if request.data.get('page') is not None else 0  # Default to page 0
            page_size = int(request.data.get('pageSize', 10)) if request.data.get('pageSize') is not None else 10  # Default to page size 8
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
            return JsonResponse({
                'message': 'Invalid page number or page size.',
                'status_code': status.HTTP_400_BAD_REQUEST,
                'status': False,
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        paginator = Paginator(MyList, page_size)

        # Check if page_number exceeds available pages
        if page_number >= paginator.num_pages:
            return JsonResponse({
                'message': 'Page number exceeds the total number of available pages.',
                'status_code': status.HTTP_400_BAD_REQUEST,
                'status': False,
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        # Handle pagination and return the appropriate page
        try:
            page = paginator.page(page_number + 1)  # Adjust for 1-based indexing
        except EmptyPage:
            page = paginator.page(paginator.num_pages)  # Fallback to last page

        items = list(page.object_list)  # Items for the current page
        total_items = paginator.count  # Total items across all pages
        displayed_items_count = len(items)  # Items on the current page
        remaining_items_count = total_items - (page_number * page_size + displayed_items_count)  # Remaining items

        # Format the paginated result
        paginated_result = {
            'Items': items,
            'PageNumber': page.number - 1,  # Convert back to zero-based index
            'PageSize': page.paginator.per_page,
            'TotalItems': total_items,
            'RemainingItems': remaining_items_count
        }

        return JsonResponse({
                'message': 'Success',
                'status_code': status.HTTP_200_OK,
                'status': True,
                'data': paginated_result
            }, status=status.HTTP_200_OK)
    
class GetTechData(APIView):
    @swagger_auto_schema(
        operation_summary="Get data from file.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'FileId':openapi.Schema(type=openapi.TYPE_INTEGER,description="Id of file."),
                'FileName': openapi.Schema(type=openapi.TYPE_STRING, description='Name of file.'),
                'DirType': openapi.Schema(type=openapi.TYPE_STRING, description='Netlist or Tech type of file.'),
                'FileType': openapi.Schema(type=openapi.TYPE_STRING, description='Global or user type of file.'),
                'USERNAME': openapi.Schema(type=openapi.TYPE_STRING, description='Username who created file.') ,
                },
            required=['FileId','FileName','DirType','FileType','USERNAME']
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
    def post(self,request):   
        user = User.objects.filter(id=request.user_id).first()  # Correct way to access the logged-in user
        if user and user.is_staff:  # Check if user exists and is a staff member
            data = request.data
            fileId=data['FileId']
            fileName=data['FileName']
            dirType=data['DirType']
            fileType = data['FileType']
            userName=data['USERNAME']
            if (not isinstance(fileId , int)) or fileId==None:
                response= JsonResponse(vars(AdminResponse('FileId must be integer value',status.HTTP_400_BAD_REQUEST,False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            if (not isinstance(dirType , str)) or dirType==None:
                response= JsonResponse(vars(AdminResponse('DirType must be string value',status.HTTP_400_BAD_REQUEST,False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            if (not isinstance(fileType , str)) or fileType==None:
                response= JsonResponse(vars(AdminResponse('FileId must be string value',status.HTTP_400_BAD_REQUEST,False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            if (not isinstance(userName , str)) or userName==None:
                response= JsonResponse(vars(AdminResponse('FileId must be string value',status.HTTP_400_BAD_REQUEST,False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            if not isinstance(fileName, str) or fileName == "" or fileName == None or fileName== '.spice':
                message = "File name must be valid string value."
                status_code = status.HTTP_400_BAD_REQUEST
                response_status = False
                response= JsonResponse(vars(AdminResponse(message, status_code, response_status, None)))
                response.status_code=status_code
                return response
            if dirType.upper() == 'NETLIST':
                ftype='Netlist'
                extenssion='.spice'
            elif dirType.upper()=='TECH':
                ftype='Techfile'
                extenssion='.tech'
            else:
                response= JsonResponse(vars(AdminResponse(f'The directory type {dirType} is not valid. Allowed types are: NETLIST, TECH.',status.HTTP_400_BAD_REQUEST, False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            if not fileName.endswith(extenssion):
                response= JsonResponse(vars(AdminResponse('Invalid file extenssion.',status.HTTP_400_BAD_REQUEST,False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            if fileType.upper()=='GLOBAL':
                dtype=0
            elif fileType.upper()=='USER':
                getuser=User.objects.filter(username=userName.upper()).first()
                if getuser:
                    dtype=getuser.id
                else:
                    response= JsonResponse(vars(AdminResponse(f'{userName} not found in record.',status.HTTP_404_NOT_FOUND, False)))
                    response.status_code=status.HTTP_404_NOT_FOUND
                    return response
            else:
                response= JsonResponse(vars(AdminResponse(f'The file type {fileType} is not valid. Allowed types are: USER, GLOBAL.',status.HTTP_400_BAD_REQUEST, False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            filepath = f'{S3_BUCKET_ROOT}/{ftype}/{dtype}/{fileName}'  # Corrected to use filename directly from data
            file=FileInfo.objects.filter(id=fileId,type=dirType.upper(), dir=fileType.upper(),name=fileName, status='ACTIVE').first()
            if file:
                message ,data1,status_code,response_status=storage_servicer.get_tech_netlist_data(filepath,fileType,ftype)
                if (fileType=="USER" or fileType=="GLOBAL") and ftype=='Techfile':
                    get_response={'FileContent':data1}
                else:
                    get_response=data1
                response= JsonResponse(vars(AdminResponse(message,status_code, response_status,get_response)))
                response.status_code=status_code
                return response
            else:
                response= JsonResponse(vars(AdminResponse('File not found.',status.HTTP_404_NOT_FOUND, False)))
                response.status_code=status.HTTP_404_NOT_FOUND
                return response
        else:
            response = JsonResponse(vars(AdminResponse('You do not have the necessary permissions to perform this action.',status.HTTP_401_UNAUTHORIZED,False)))
            response.status_code=status.HTTP_401_UNAUTHORIZED
            return response

class RenameFile(APIView):
    @swagger_auto_schema(
        operation_summary="Rename file.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'FileId': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the file to rename'),
                'NewFileName': openapi.Schema(type=openapi.TYPE_STRING, description='New name for the file'),
                'FileType': openapi.Schema(type=openapi.TYPE_STRING, description='Type of the file (e.g., GLOBAL, USER)'),
                'DirType': openapi.Schema(type=openapi.TYPE_STRING, description='Directory type (e.g., Netlist, Techfile)'),
                'USERNAME': openapi.Schema(type=openapi.TYPE_STRING, description='Username of the person renaming the file'),
            },
            required=['FileId', 'NewFileName', 'FileType', 'DirType', 'USERNAME'],
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
        user = User.objects.filter(id=request.user_id).first()  # Correct way to access the logged-in user
        if user and user.is_staff:  # Check if user exists and is a staff member
            data = request.data
            fileId = data['FileId']
            new_file_name = data['NewFileName']
            fileType = data['FileType']
            dirType = data['DirType']
            userName = data['USERNAME']
            if (not isinstance(dirType, str)) or dirType == None:
                response = JsonResponse(vars(AdminResponse('DirType must be string value', status.HTTP_400_BAD_REQUEST, False)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if (not isinstance(fileType, str)) or fileType == None:
                response = JsonResponse(vars(AdminResponse('FileId must be string value', status.HTTP_400_BAD_REQUEST, False)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if (not isinstance(userName, str)) or userName == None:
                response = JsonResponse(vars(AdminResponse('FileId must be string value', status.HTTP_400_BAD_REQUEST, False)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if (not isinstance(fileId, int)) or fileId == None:
                response = JsonResponse(vars(AdminResponse('FileId must be integer value', status.HTTP_400_BAD_REQUEST, False)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if (not isinstance(new_file_name, str)) or new_file_name == None:
                response = JsonResponse(vars(AdminResponse('NewFileName must be string value', status.HTTP_400_BAD_REQUEST, False)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if not isinstance(new_file_name, str) or new_file_name == "" or new_file_name == None or new_file_name == '.spice' or new_file_name == '.tech':
                message = "File name must be valid string value."
                status_code = status.HTTP_400_BAD_REQUEST
                response_status = False
                response = JsonResponse(vars(AdminResponse(message, status_code, response_status, None)))
            if fileType.upper()=='GLOBAL':
                dtype=0
            elif fileType.upper()=='USER':
                getuser=User.objects.filter(username=userName.upper()).first()
                if getuser:
                    dtype=getuser.id
                else:
                    response= JsonResponse(vars(AdminResponse(f'{userName} not found in record.',status.HTTP_404_NOT_FOUND, False)))
                    response.status_code=status.HTTP_404_NOT_FOUND
                    return response
            else:
                response= JsonResponse(vars(AdminResponse(f'The file type {fileType} is not valid. Allowed types are: USER, GLOBAL.',status.HTTP_400_BAD_REQUEST, False)))
                response.status_code=status.HTTP_400_BAD_REQUEST
                return response
            if not bool(re.fullmatch(r'[A-Za-z0-9_]+', new_file_name)):
                response = JsonResponse(vars(AdminResponse('Invalid file name. Only alphabetic characters, numbers and underscores (_) are allowed. Please remove special characters', status.HTTP_400_BAD_REQUEST, False, None)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            if dirType.upper() == 'NETLIST':
                ftype = 'Netlist'
                extenssion = '.spice'
            elif dirType.upper() == 'TECH':
                ftype = 'Techfile'
                extenssion = '.tech'
            else:
                response = JsonResponse(vars(AdminResponse(f'The directory type {dirType} is not valid. Allowed types are: NETLIST, TECH.', status.HTTP_400_BAD_REQUEST, False)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            file=FileInfo.objects.filter(type=dirType.upper(), dir=fileType.upper(),name=f'{new_file_name}{extenssion}', status='ACTIVE').first()
            if file:
                response = JsonResponse(vars(AdminResponse(f'File with same name already present.', status.HTTP_400_BAD_REQUEST, False)))
                response.status_code = status.HTTP_400_BAD_REQUEST
                return response
            rename_file=FileInfo.objects.filter(id=fileId,type=dirType.upper(), dir=fileType.upper(),name__endswith=extenssion, status='ACTIVE').first()
            if rename_file:
                old_file_name = rename_file.name
                old_file_path = f'{S3_BUCKET_ROOT}/{ftype}/{dtype}/{old_file_name}'
                new_file_name = f'{new_file_name}{extenssion}'
                response_status = storage_servicer.rename_file(old_file_path, new_file_name)
                if response_status:
                    rename_file.name = new_file_name
                    rename_file.modified_by = user
                    rename_file.modified_date = timezone.now()
                    rename_file.save()
                    try:
                        key=f"get_all_files_{request.user.id}_{dirType.upper()}"
                        cache.delete(key)
                    except redis.exceptions.ConnectionError as e:
                        print(f"Redis connection error: {e}")
                    message = "File renamed successfully."
                    status_code = status.HTTP_200_OK
                    response_status = True
                    response= JsonResponse(vars(AdminResponse(message, status_code, response_status, None)))
                    response.status_code=status_code
                    return response
                else:
                    response = JsonResponse(vars(AdminResponse(f'Failed to rename file {old_file_name}.', status.HTTP_400_BAD_REQUEST, False)))
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return response
            else:
                try:
                    key=f"get_all_files_{request.user.id}_{dirType.upper()}"
                    cache.delete(key)
                except redis.exceptions.ConnectionError as e:
                    print(f"Redis connection error: {e}")
                response= JsonResponse(vars(AdminResponse('Record not found.',status.HTTP_404_NOT_FOUND, False)))
                response.status_code=status.HTTP_404_NOT_FOUND
                return response
        else:
            response = JsonResponse(vars(AdminResponse('You do not have the necessary permissions to perform this action.',status.HTTP_401_UNAUTHORIZED,False)))
            response.status_code=status.HTTP_401_UNAUTHORIZED
            return response
          
class CloneFile(APIView):
    def post(self, request):
        try:
            user_id = request.user_id
            fileId = request.data.get('FileId')
            user = User.objects.filter(id=user_id).first()
            if not user:
                return JsonResponse(vars(AdminResponse('User not found.', status.HTTP_400_BAD_REQUEST, False)), status=status.HTTP_400_BAD_REQUEST)
            if not user.is_staff:  # Check if user exists and is a staff member
                response = JsonResponse(vars(AdminResponse('You do not have the necessary permissions to perform this action.',status.HTTP_401_UNAUTHORIZED,False)))
                response.status_code=status.HTTP_401_UNAUTHORIZED
                return response
            # Check if FileId is provided
            if not fileId:
                return JsonResponse(vars(AdminResponse('FileId is required.', status.HTTP_400_BAD_REQUEST, False)), status=status.HTTP_400_BAD_REQUEST)
            if not isinstance(fileId, int):
                return JsonResponse(vars(AdminResponse('FileId must be an integer.', status.HTTP_400_BAD_REQUEST, False)), status=status.HTTP_400_BAD_REQUEST)

            # Fetch the file from DB with filtering criteria
            clone_file = FileInfo.objects.filter(
                id=fileId,
                status='ACTIVE'
            ).first()

            # Validate if a file was found
            if not clone_file:
                return JsonResponse(vars(AdminResponse('File not found.', status.HTTP_404_NOT_FOUND, False)), status=status.HTTP_404_NOT_FOUND)
            else:
                # Determine file type and extension
                if clone_file.type.upper() == 'NETLIST':
                    ftype = 'Netlist'
                    extension = '.spice'
                elif clone_file.type.upper() == 'TECH':
                    ftype = 'Techfile'
                    extension = '.tech'
                else:
                    return JsonResponse(vars(AdminResponse(f'The file type {clone_file.type} is not valid. Allowed types are: USER, GLOBAL.', status.HTTP_400_BAD_REQUEST, False)), status=status.HTTP_400_BAD_REQUEST)
                # Generate new file name
                current_time = datetime.now().strftime("%H%M%S%f")[:8]
                new_file_name = f"{clone_file.name.split('.')[0]}_{current_time}{extension}"
                old_file_name = clone_file.name
                if clone_file.dir.upper() == 'GLOBAL':
                    old_file_path = f'{S3_BUCKET_ROOT}/{ftype}/0/{old_file_name}'
                    new_file_path = f'{S3_BUCKET_ROOT}/{ftype}/0/{new_file_name}'
                elif clone_file.dir.upper() == 'USER':
                    old_file_path = f'{S3_BUCKET_ROOT}/{ftype}/{clone_file.created_by_id}/{old_file_name}'
                    new_file_path = f'{S3_BUCKET_ROOT}/{ftype}/{clone_file.created_by_id}/{new_file_name}'
                else:
                    response = JsonResponse(vars(AdminResponse('Failed to clone file.',status.HTTP_401_UNAUTHORIZED,False)))
                    response.status_code=status.HTTP_401_UNAUTHORIZED
                    return response
                # Handle file storage
                file = storage_servicer.get_file(old_file_path)
                if file['success'] == False:
                    response = JsonResponse(vars(AdminResponse(file['error'], file['status_code'], file['success'])), None)
                    response.status_code = file['status_code']
                    return response
                
                old_file_content = storage_servicer.read_file_response_content(file['response'])
                storage_service_status = storage_servicer.write_file(new_file_path, old_file_content, 1)
                
                if not storage_service_status:
                    return JsonResponse(vars(AdminResponse('Failed to clone file.', status.HTTP_500_INTERNAL_SERVER_ERROR, False)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                # Save new entry to database
                new_file_info = FileInfo(
                    name=new_file_name,
                    type=clone_file.type,
                    dir=clone_file.dir,
                    status='ACTIVE',
                    created_by_id=clone_file.created_by_id,
                    filesize=clone_file.filesize,
                )
                new_file_info.save()
                try:
                    key=f"get_all_files_{request.user.id}_{clone_file.type.upper()}"
                    cache.delete(key)
                except redis.exceptions.ConnectionError as e:
                    print(f"Redis connection error: {e}")

                # Successful response
                message = "File cloned successfully."
                return JsonResponse(vars(AdminResponse(message, status.HTTP_200_OK, True, None)), status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse(vars(AdminResponse(f"An error occurred: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR, False)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

