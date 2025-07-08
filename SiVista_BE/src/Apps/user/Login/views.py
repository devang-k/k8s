"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: views.py  
 * Description:  Login  - logic to login the application, AboutDetails  - logic to get version details. 
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
from rest_framework import status
from django.http import JsonResponse
from django.utils import timezone
from datetime import timezone as tmz
from src.Services.LoginService import *
from src.Services.GRPCService import get_grpc_version
from src.Models.Login.LoginResponse import *
from src.Apps.user.Login.serializers import LoginSerializer, get_version_from_build_script
from rest_framework_simplejwt.tokens import RefreshToken, TokenError, AccessToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from src.Apps.user.Login.models import ActiveToken
from rest_framework.request import Request
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from SiVista_BE.settings import CONCURRENT_USER_LIMIT, SIMPLE_JWT
from ast import literal_eval

class Login(APIView):
    @swagger_auto_schema(
        operation_summary="Login to SiVista application",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'Username': openapi.Schema(type=openapi.TYPE_STRING, description='Username for SiVista User'),
                'Password': openapi.Schema(type=openapi.TYPE_STRING, description='Password for SiVista User')
            },
            required=['Username',"Password"]
        ),
        responses={
            200: openapi.Response('Success', openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'status': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'token': openapi.Schema(type=openapi.TYPE_OBJECT),
            })),
            400: openapi.Response('Bad Request', openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'status': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'token': openapi.Schema(type=openapi.TYPE_OBJECT,nullable=True),
            })),
        }
    )
    def post(self, request: Request, *args, **kwargs):
        ActiveToken.objects.filter(expires_at__lte=timezone.now()).delete()
        if ActiveToken.objects.count() >= CONCURRENT_USER_LIMIT:
            message = "Login Unavailable: The maximum number of concurrent users has been reached. Please try again later."
            response = JsonResponse(vars(LoginResponse(message, status.HTTP_403_FORBIDDEN)))
            response.status_code = status.HTTP_403_FORBIDDEN
            return response
        try:
            serializer = LoginSerializer(data=request.data)
            if serializer.is_valid():
                message,responseStatus ,user= serializer.validated_data
                if responseStatus==200: 
                    token = serializer.get_token(user)
                    if request.msg:
                        token['notification']=request.msg
                    else:
                        token['notification']=None
                    ActiveToken.objects.filter(user_id=user.id).delete()
                    ActiveToken.objects.create(
                        user=user,
                        token=token['refresh'],
                        expires_at=timezone.now() + SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
                    )
                    response= JsonResponse(vars(LoginResponse(message,responseStatus,token)))
                    response.status_code=responseStatus
                    return response 
                else:
                    response= JsonResponse(vars(LoginResponse(message,responseStatus)))
                    response.status_code=responseStatus
                    return response
            else:
                message="Invalid Credentials."
                responseStatus=status.HTTP_401_UNAUTHORIZED
                response= JsonResponse(vars(LoginResponse(message,responseStatus)))
                response.status_code=responseStatus
                return response
        except Exception as e:
            print(e)

class AboutDetails(APIView):
    @swagger_auto_schema(
        operation_summary="Get details of version.",
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
    def get(self, *args, **kwargs):
        grpc_version = get_grpc_version()
        lib_utils_version = "Lib Util disconnected"
        try:
            grpc_version = literal_eval(grpc_version.message)
            assert type(grpc_version) is tuple and len(grpc_version) == 2
            grpc_version, lib_utils_version = grpc_version
        except Exception as e: # For backward compatibility (cases where lib_utils version is not returned)
            grpc_version = grpc_version.message
        be_version=get_version_from_build_script('build.sh')
        if be_version:
            message="Success"
            responseStatus=True
            status_code=status.HTTP_200_OK
            response= JsonResponse(vars(LoginResponseAbout(message,status_code,responseStatus,{"API_Server_Version": be_version, "SiVista_core_version": grpc_version, "Lib_utils_version": lib_utils_version})))
            response.status_code=status_code
            return response
        else:
            message="API Version missing while building."
            responseStatus=False
            status_code=status.HTTP_417_EXPECTATION_FAILED
            response= JsonResponse(vars(LoginResponseAbout(message,status_code,responseStatus,{"API_Server_Version": be_version, "SiVista_core_version": grpc_version, "Lib_utils_version": lib_utils_version})))
            response.status_code=status_code
            return response

class Logout(APIView):
    @swagger_auto_schema(
        operation_summary="Logout from SiVista application",
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
    def post(self, request: Request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        if refresh_token is None:
            return JsonResponse({"detail": "No refresh token provided."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            ActiveToken.objects.filter(token=refresh_token).delete()
        except TokenError as e:
            return JsonResponse({"detail": "Token is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse({}, status=status.HTTP_205_RESET_CONTENT)

class TokenDetails(APIView):
    @swagger_auto_schema(
        operation_summary="Get details of active tokens.",
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
    def get(self, *args, **kwargs):
        logged_in_count = ActiveToken.objects.filter(expires_at__gt=timezone.now()).count()
        return JsonResponse({"loggedInUsers": logged_in_count}, status=status.HTTP_200_OK)

class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = TokenRefreshSerializer
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        refresh_token = request.data.get("refresh")
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            ActiveToken.objects.filter(token=refresh_token).delete()
            return JsonResponse({"detail": "Invalid refresh token."}, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data  # contains the new access token
        return JsonResponse(data, status=status.HTTP_200_OK)