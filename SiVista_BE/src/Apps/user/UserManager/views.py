"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: views.py  
 * Description: This file contains class which deals with user details, get user list, update user and create user.
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
from src.Services.LoginService import PassCheck, getPassword
from src.Models.User.UserResponse import UserResponse
from src.Apps.user.UserManager.serializer import ShowUserSerializer, UserCreationSerializer, UserUpdateSerializer
from rest_framework import status
from src.Services.UserService import modify_user_validate, create_user_validation
from src.Apps.user.Login.models import User
from django.core.paginator import Paginator, EmptyPage
from drf_yasg.utils import swagger_auto_schema
from redis.exceptions import ConnectionError
from django.core.cache import cache
from drf_yasg import openapi
from django.utils import timezone
import re

class UserDetails(APIView):
    @swagger_auto_schema(
        operation_summary="Get logged in user details.",
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
        userId = request.user_id  # Ensure user_id is correctly passed
        user = User.objects.filter(id=userId).first()
        if user:
            serializer = ShowUserSerializer(user)
            data=serializer.data
            data['is_admin'] = data.pop('is_staff')
            response= JsonResponse(vars(UserResponse(f'Success',status.HTTP_200_OK,True, data)))
            response.status_code=status.HTTP_200_OK
            return response
        else:
            response= JsonResponse(vars(UserResponse(f'User not found in records.',status.HTTP_400_BAD_REQUEST,False)))
            response.status_code=status.HTTP_400_BAD_REQUEST
            return response
class UserList(APIView):
    @swagger_auto_schema(
        operation_summary="Get list of all users.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'page':openapi.Schema(type=openapi.TYPE_INTEGER, description="page number"),
                'pageSize':openapi.Schema(type=openapi.TYPE_INTEGER, description="elements to show each page")
                }
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
        user=User.objects.filter(id=userId).first()
        if user.is_staff == True:
            try:
                key=f"user_list"
                if cache.get(key) is not None:
                    userlist=cache.get(key)
                else:
                    userlist = User.objects.all().order_by('id')
                    cache.set(key,userlist,1800)
            except ConnectionError:
                userlist = User.objects.all().order_by('id')
            serializer=ShowUserSerializer(userlist,many=True)
            if serializer.data==[]:
                response= JsonResponse(vars(UserResponse(f'No user found in records.Please create at least one user.',status.HTTP_404_NOT_FOUND,False, serializer.data)))
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
            paginator = Paginator(serializer.data, page_size)

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
 
            log_levels = [
                  {"key": 99,
                  "value": "NO LOGGING"},
                  {"key": 1,
                  "value": "DEBUG LOGS"},
                  {"key": 2,
                  "value": "WARNING"},
                  {"key": 3,
                  "value": "PERFORMANCE LOGS"},
                  {"key": 4,
                  "value": "OPERATIONAL LOGS"},
                  {"key": 5,
                  "value": "ERROR"}]
            # Format the paginated result
            paginated_result = {
                'Items': items,
                'logLevels': log_levels,
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
        else:
            response= JsonResponse(vars(UserResponse(f'You do not have the necessary permissions to perform this action.',status.HTTP_400_BAD_REQUEST,False)))
            response.status_code=status.HTTP_401_UNAUTHORIZED
            return response   

class CreateUser(APIView):
    @swagger_auto_schema(
        operation_summary="Create a new User in SiVista",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_INTEGER, description='UserName of uers to add record in SiVista application.'),
                'email':openapi.Schema(type=openapi.TYPE_STRING, description='email id of uers to add record in SiVista application.'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='password of uers to add record in SiVista application.'),
                'name':openapi.Schema(type=openapi.TYPE_STRING, description='name of uers to add record in SiVista application.'),
                'isActive':openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Is user active or not (by defualt true)'),
                'isAdmin':openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Is user admin or not (by defualt false)')
                },
            required=['username', 'email', 'password', 'name', 'isActive','isAdmin' ]
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
            data=request.data
            userId=request.user_id
            user=User.objects.filter(id=userId).first()
            if user.is_staff == True:
                serializer= UserCreationSerializer(data=request.data)
                message, response_status,status_code=create_user_validation(data)
                if serializer.is_valid():
                    if response_status==True:
                        key="user_list"
                        try:
                            cache.delete(key)
                        except ConnectionError:
                            pass
                        message, status_code, response_status, response_data=serializer.create(data, user)
                        response = JsonResponse(vars(UserResponse(message, status_code, response_status, response_data)))
                        response.status_code= status_code
                        return response
                    else:
                        response = JsonResponse(vars(UserResponse(message, status_code, response_status)))
                        response.status_code=status_code
                        return response
                else:
                    response= JsonResponse(vars(UserResponse(f'Kindly provide valid input.',status.HTTP_400_BAD_REQUEST,False)))
                    response.status_code=status.HTTP_400_BAD_REQUEST
                    return response
            else:
                response= JsonResponse(vars(UserResponse(f'You do not have the necessary permissions to perform this action.',status.HTTP_400_BAD_REQUEST,False)))
                response.status_code=status.HTTP_401_UNAUTHORIZED
                return response
        except Exception as e:
            print(e)

class UpdateUser(APIView):
    @swagger_auto_schema(
        operation_summary="Modify User details in SiVista",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_INTEGER, description='UserName of uers to add record in SiVista application.'),
                'email':openapi.Schema(type=openapi.TYPE_STRING, description='email id of uers to add record in SiVista application.'),
                'name':openapi.Schema(type=openapi.TYPE_STRING, description='name of uers to add record in SiVista application.'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password change for SiVista application.'),
                'isActive':openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Is user active or not (by defualt true)'),
                'isAdmin':openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Is user admin or not (by defualt false)'),
                'isDeleted':openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Soft delete user."),
                'logLevel':openapi.Schema(type=openapi.TYPE_INTEGER, description='Log level for user.'),
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
    def patch(self, request, uid):
        user = User.objects.filter(id=uid).first()
        userId=request.user_id
        if not user:
            response= JsonResponse(vars(UserResponse('User not found.', status.HTTP_404_NOT_FOUND, False)))
            response.status_code=status.HTTP_404_NOT_FOUND
            return response
        if uid==userId:
            response= JsonResponse(vars(UserResponse('You are not allowed to edit your own profile.', status.HTTP_406_NOT_ACCEPTABLE, False)))
            response.status_code=status.HTTP_406_NOT_ACCEPTABLE
            return response
        data = request.data
        try:  
            message, status_code, response_status=modify_user_validate(user, data)
            serializer = UserUpdateSerializer(user, data=data, partial=True)
            if response_status== True:
                if serializer.is_valid():
                    serializer.validate(data)
                    serializer.save() 
                    user.modified_by=User.objects.get(pk=userId)
                    user.modified_date=timezone.now()
                    user.save()
                    key="user_list"
                    try:
                        cache.delete(key)
                    except ConnectionError:
                        pass
                    response= JsonResponse(vars(UserResponse(message, status_code, response_status,serializer.data)))
                    response.status_code=status_code
                    return response
            else:
                response= JsonResponse(vars(UserResponse(message, status_code, response_status)))
                response.status_code=status_code
                return response
        except Exception as e:
            print(e)
            response= JsonResponse(vars(UserResponse('An error occurred.', status.HTTP_500_INTERNAL_SERVER_ERROR, False)))
            response.status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            return response

class PasswordUpdate(APIView):
    @swagger_auto_schema(
        operation_summary="Create a new User in SiVista",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='password of uers to add record in SiVista application.'),
                'old_password': openapi.Schema(type=openapi.TYPE_STRING, description='Old password for User.'),
                },
            required=['old_password', 'password' ]
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
        data=request.data
        old_password=data['old_password']
        if isinstance(old_password,str) or old_password!=None:
            user=User.objects.filter(id=request.user_id).first()
            if PassCheck(user, old_password):
                password=data['password']
                print(isinstance(password, str) or password!=None)
                if isinstance(password, str) or password!=None:
                    if PassCheck(user,password):
                        message='New password must be diffrent than old password.'
                        response_status=False
                        status_code=status.HTTP_400_BAD_REQUEST
                        response= JsonResponse(vars(UserResponse(message, status_code, response_status)))
                        response.status_code=status_code
                        return response
                    if not ((8 <= len(password) <= 16) and (re.search(r'[@$!%*?&]', password)) and (re.search(r'\d', password)) and (re.search(r'[a-z]', password)) and (re.search(r'[A-Z]', password) )):
                        message = "Password must be between 8 to 16 characters long, contain at least one uppercase letter, contain at least one lowercase letter, contain at least one digit, and contain at least one special character (@$!%*?&)."
                        status_code = status.HTTP_400_BAD_REQUEST
                        response_status = False
                        response= JsonResponse(vars(UserResponse(message, status_code, response_status)))
                        response.status_code=status_code
                        return response
                    updated_password=getPassword(password)
                    user.password=updated_password
                    user.save()
                    message='Password updated successfully.'
                    response_status=True
                    status_code=status.HTTP_200_OK
                    response= JsonResponse(vars(UserResponse(message, status_code, response_status)))
                    response.status_code=status_code
                    return response
                else:
                    message="Password must be a string value and cannot be null."
                    response_status=False
                    status_code=status.HTTP_400_BAD_REQUEST
                    response= JsonResponse(vars(UserResponse(message, status_code, response_status)))
                    response.status_code=status_code
                    return response
            else:
                message='Old password does not match.'
                response_status=False
                status_code=status.HTTP_400_BAD_REQUEST
                response= JsonResponse(vars(UserResponse(message, status_code, response_status)))
                response.status_code=status_code
                return response
        else:
            message='Old password must be a string value and cannot be null.'
            response_status=False
            status_code=status.HTTP_400_BAD_REQUEST
            response= JsonResponse(vars(UserResponse(message, status_code, response_status)))
            response.status_code=status_code
            return response
