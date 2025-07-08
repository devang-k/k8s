"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: middleware.py  
 * Description:  JWT token validation for endpoints.
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
from django.http import JsonResponse
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
import datetime
from SiVista_BE.settings import LICENSE_CUTOFF_DATE
from rest_framework_jwt.utils import jwt_decode_handler
from rest_framework import status
import jwt
import json

class JWTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cutoff_date = LICENSE_CUTOFF_DATE

        # Calculate the notification date (10 days before cutoff)
        notification_date = cutoff_date - datetime.timedelta(days=10)
        current_datetime = datetime.datetime.now()

        # Check against current datetime
        if current_datetime > cutoff_date:
            response = JsonResponse({
                'message': f'Support for this service concluded on {cutoff_date.strftime('%B %d, %Y')}. For continued assistance or alternative solutions, please contact support or refer to the documentation.',
                "status_code": status.HTTP_403_FORBIDDEN,
                "status": False
            })
            response.status_code = status.HTTP_403_FORBIDDEN
            return response
        elif notification_date <= current_datetime <= cutoff_date:
            request.msg = f'Support for this service will end on {cutoff_date.strftime("%B %d, %Y")}. Please take necessary actions.'
        else:
            request.msg = None
            
        if request.path in ['/user/login/','/token/refresh/','/swagger/','/redoc/','/admin/login/','/user/about/', '/project/migrate/']:
            #['/user/login/','/token/refresh/','/user/about/']
            #['/user/login/','/token/refresh/','/swagger/','/redoc/','/admin/login/','/user/about/'] 
            response = self.get_response(request)   
            return response
        else:
            authorization_header = request.headers.get('Authorization') 
            try:

                if authorization_header:
                    if authorization_header.startswith('Bearer '):
                        token = authorization_header.split(' ')[1]
                        decoded_access_payload = jwt_decode_handler(token)
                        if float(decoded_access_payload['exp'])< datetime.datetime.now().timestamp():
                            response= JsonResponse({'message': 'Token has expired.'})
                            response.status_code=status.HTTP_401_UNAUTHORIZED
                            return response
                        else: 
                            request.user_id= decoded_access_payload['user_id']
                            response = self.get_response(request)   
                            return response
                    else:
                        response= JsonResponse({'message': 'Invalid token type.'})
                        response.status_code=status.HTTP_401_UNAUTHORIZED
                        return response
                response= JsonResponse({'message': 'Token not available.'})
                response.status_code=status.HTTP_401_UNAUTHORIZED
                return response
            except jwt.exceptions.ExpiredSignatureError as e:
                response= JsonResponse({'message': 'Token has expired.'})
                response.status_code=status.HTTP_401_UNAUTHORIZED
                return response
            except (IndexError, TokenError, InvalidToken) as e:
                print(e)

            
