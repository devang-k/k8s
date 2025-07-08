"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: UserService.py  
 * Description: User service to validate user details while creating and updating.
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
from src.Apps.user.Login.models import User
from rest_framework import status

def create_user_validation(data):
    if not data['username']:
        message="Username is mandatory."
        status_code=status.HTTP_400_BAD_REQUEST
        response_status=False
        return message, response_status,status_code
    if not isinstance(data['username'], str):
        message= "Username must be a string value."
        status_code=status.HTTP_400_BAD_REQUEST
        response_status=False
        return message, response_status,status_code
    if len(data['username']) >= 11:
        message= "Username must be exactly 10 characters long."
        status_code=status.HTTP_400_BAD_REQUEST
        response_status=False
        return message, response_status,status_code
    username=data['username'].upper()
    if User.objects.filter(username=username).exists():
        message="Username already exists."
        status_code=status.HTTP_400_BAD_REQUEST
        response_status=False
        return message, response_status,status_code
    if not data['email']:
        message="Email is mandatory."
        status_code=status.HTTP_400_BAD_REQUEST
        response_status=False
        return message, response_status,status_code
    if data['email'] == "" or data['email'] == None:
        message="Email cannot be blank."
        response_status=False
        status_code= status.HTTP_400_BAD_REQUEST
        return message, status_code, response_status
    if not isinstance(data['email'], str):
        message="Email must be a string value."
        response_status=False
        status_code= status.HTTP_400_BAD_REQUEST
        return message, status_code, response_status
    if not data['email'].endswith('.com') or not "@" in data['email']:
        message="Invalid email format."
        response_status=False
        status_code= status.HTTP_400_BAD_REQUEST
        return message, status_code, response_status
    """if User.objects.filter(email=data['email']).exists():
        message="Email already exists."
        status_code=status.HTTP_400_BAD_REQUEST
        response_status=False
        return message, response_status,status_code"""
    if not data['name']:
        message="Name is mandatory."
        status_code=status.HTTP_400_BAD_REQUEST
        response_status=False
        return message, response_status,status_code
    if not isinstance(data['name'], str):
        message="Name must be a string value."
        status_code=status.HTTP_400_BAD_REQUEST
        response_status=False
        return message, response_status,status_code
    if re.search(r'\s{2,}', data['name']) or data['name'].startswith(' ') or data['name'].endswith(' '):
        message="Name contains more than one space or leading/trailing spaces."
        response_status=False
        status_code=status.HTTP_400_BAD_REQUEST
        return message, response_status,status_code
    if data['name']=="" or data['name'] == None:
        message="Name cant be blank."
        response_status=False
        status_code=status.HTTP_400_BAD_REQUEST
        return message, response_status,status_code
    if not data['password']:
        message="Password is mandatory."
        status_code=status.HTTP_400_BAD_REQUEST
        response_status=False
        return message, response_status,status_code
    if not isinstance(data['password'], str) :
        message='Password must be string'
        response_status=False
        status_code=status.HTTP_400_BAD_REQUEST
        return message, response_status,status_code
    if not ((8 <= len(data['password']) <= 16) and (re.search(r'[@$!%*?&]', data['password'])) and (re.search(r'\d', data['password'])) and (re.search(r'[a-z]', data['password'])) and (re.search(r'[A-Z]', data['password']) )):
        message = "Password must be between 8 to 16 characters long, contain at least one uppercase letter, contain at least one lowercase letter, contain at least one digit, and contain at least one special character (@$!%*?&)."
        status_code = status.HTTP_400_BAD_REQUEST
        response_status = False
        return message, response_status,status_code
    if data['isActive'] is None:
        message="isActive is mandatory and must be a boolean value."
        status_code=status.HTTP_400_BAD_REQUEST
        response_status=False
        return message, response_status,status_code
    if not isinstance(data['isActive'], bool):
        message="isActive must be a boolean value."
        status_code=status.HTTP_400_BAD_REQUEST
        response_status=False
        return message, response_status,status_code
    if data['isAdmin'] is None:
        message="isAdmin is mandatory and must be a boolean value."
        status_code=status.HTTP_400_BAD_REQUEST
        response_status=False
        return message, response_status,status_code
    if not isinstance(data['isAdmin'], bool):
        message="isAdmin must be a boolean value."
        status_code=status.HTTP_400_BAD_REQUEST
        response_status=False
        return message, response_status,status_code
    message="Success"
    response_status=True
    status_code=status.HTTP_200_OK
    return message, response_status,status_code

def modify_user_validate(user, data):
        if 'password' in data:
            password=data['password']
            if not isinstance(password, str) :
                message='Password must be string'
                response_status=False
                status_code=status.HTTP_400_BAD_REQUEST
                return message, status_code, response_status

            if not ((8 <= len(password) <= 16) and (re.search(r'[@$!%*?&]', password)) and (re.search(r'\d', password)) and (re.search(r'[a-z]', password)) and (re.search(r'[A-Z]', password) )):
                message = "Password must be between 8 to 16 characters long, contain at least one uppercase letter, contain at least one lowercase letter, contain at least one digit, and contain at least one special character (@$!%*?&)."
                status_code = status.HTTP_400_BAD_REQUEST
                response_status = False
                return message, status_code, response_status
        if 'username' in data:
            if not isinstance(data['username'], str):
                message="Username must be a string value."
                response_status=False
                status_code= status.HTTP_400_BAD_REQUEST
                return message, status_code, response_status
            if data['username'] == "" or data['username'] == None:
                message= "Username cannot be blank"
                response_status=False
                status_code= status.HTTP_400_BAD_REQUEST
                return message, status_code, response_status
            username=data['username'].upper()
            if User.objects.filter(username=username).exists():
                message="Username already exists."
                status_code=status.HTTP_400_BAD_REQUEST
                response_status=False
                return message, status_code, response_status
            if re.search(r'\s{2,}', data['username']) or data['username'].startswith(' ') or data['username'].endswith(' '):
                message="User Name contains more than one space or leading/trailing spaces."
                response_status=False
                status_code= status.HTTP_400_BAD_REQUEST
                return message, status_code, response_status
            if len(data['username']) >= 11:
                message= "Username must be exactly 10 characters long."
                response_status=False
                status_code= status.HTTP_400_BAD_REQUEST
                return message, status_code, response_status
        if 'email' in data:
            """if User.objects.filter(email=data['email']).exists():
                message="Email already exists."
                response_status=False
                status_code= status.HTTP_400_BAD_REQUEST
                return message, status_code, response_status"""
            if data['email'] == "" or data['email'] == None:
                message="Email cannot be blank."
                response_status=False
                status_code= status.HTTP_400_BAD_REQUEST
                return message, status_code, response_status
            if not isinstance(data['email'], str):
                message="Email must be a string value."
                response_status=False
                status_code= status.HTTP_400_BAD_REQUEST
                return message, status_code, response_status
            if not data['email'].endswith('.com') or not "@" in data['email']:
                message="Invalid email format."
                response_status=False
                status_code= status.HTTP_400_BAD_REQUEST
                return message, status_code, response_status
        if 'name' in data:
            if not isinstance(data['name'], str):
                message="Name must be a string value."
                response_status=False
                status_code= status.HTTP_400_BAD_REQUEST
                return message, status_code, response_status
            if re.search(r'\s{2,}', data['name']) or data['name'].startswith(' ') or data['name'].endswith(' '):
                message="Name contains more than one space or leading/trailing spaces."
                response_status=False
                status_code= status.HTTP_400_BAD_REQUEST
                return message, status_code, response_status
            if data['name']=="" or data['name'] == None:
                message="Name cant be blank."
                response_status=False
                status_code= status.HTTP_400_BAD_REQUEST
                return message, status_code, response_status
        if 'isActive' in data:
            if not isinstance(data['isActive'], bool):
                message="isActive must be a boolean value."
                response_status=False
                status_code= status.HTTP_400_BAD_REQUEST
                return message, status_code, response_status
            if (user.is_active== False and data['isActive']==False):
                message=f'Already {user.username} has been deactivated. '
                status_code=status.HTTP_208_ALREADY_REPORTED
                response_status=False
                return message, status_code, response_status
            if (user.is_active == True and data['isActive']==True):
                message=f'Already active user.'
                status_code=status.HTTP_208_ALREADY_REPORTED
                response_status=False
                return message, status_code, response_status
        if 'isAdmin' in data:
            if not isinstance(data['isAdmin'], bool):
                message="isAdmin must be a boolean value."
                response_status=False
                status_code= status.HTTP_400_BAD_REQUEST
                return message, status_code, response_status
            if (user.is_staff== False and data['isAdmin']==False):
                message=f'Already {user.username} has been non-admin user.'
                status_code=status.HTTP_208_ALREADY_REPORTED
                response_status=False
                return message, status_code, response_status
            if (user.is_staff == True and data['isAdmin']==True):
                message=f'Already admin user.'
                status_code=status.HTTP_208_ALREADY_REPORTED
                response_status=False
                return message, status_code, response_status
        if 'isDeleted' in data:
            if not isinstance(data['isDeleted'], bool):
                message="isAdmin must be a boolean value."
                response_status=False
                status_code= status.HTTP_400_BAD_REQUEST
                return message, status_code, response_status
            if (user.is_deleted== False and data['isDeleted']==False):
                message=f'Already {user.username} has been activated.'
                status_code=status.HTTP_208_ALREADY_REPORTED
                response_status=False
                return message, status_code, response_status
            if (user.is_deleted == True and data['isDeleted']==True):
                message=f'Already {user.username} has been deleted.'
                status_code=status.HTTP_208_ALREADY_REPORTED
                response_status=False
                return message, status_code, response_status
        if 'logLevel' in data:
            logging_levels = [99,1,2,3,4,5]
            if not isinstance(data['logLevel'], int):
                message="Log level must be an integer value."
                response_status=False
                status_code= status.HTTP_400_BAD_REQUEST
                return message, status_code, response_status
            if data['logLevel'] not in logging_levels:
                message="Invalid log level."
                response_status=False
                status_code= status.HTTP_400_BAD_REQUEST
                return message, status_code, response_status
        message="Successfully modified user details."
        response_status=True
        status_code= status.HTTP_201_CREATED
        return message, status_code, response_status

def create_user(username, email, password,name,isactive, isadmin, userId):
    username=username.upper()
    name=name.upper()
    user = User.objects.create(
    username=username,
    email=email,
    password=password,
    name=name,
    is_active=isactive,
    is_staff=isadmin,
    is_deleted=False,
    created_by=userId
    )
    return user