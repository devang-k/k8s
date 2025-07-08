"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: serializers.py  
 * Description: Coustomise serializers to validate user details while login.
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

from rest_framework import serializers
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from src.Services.LoginService import *
import re


class LoginSerializer(serializers.Serializer):
    Username=serializers.CharField(max_length=10)
    Password=serializers.CharField(max_length=100)

    def validate(self,data):
        user = CheckUser(data['Username'].upper())
        if user and PassCheck(user, data['Password']):
            if IsActive(user) and not IsDeleted(user):
                message='Success'
                responseStatus=status.HTTP_200_OK
                return message,responseStatus,user
            else:
                message=f'User {data['Username'].upper()} is inactive, kindly coordinate with Admin user.'
                responseStatus=status.HTTP_401_UNAUTHORIZED
                return message,responseStatus,user
        else:
            message='Invalid Credentials'
            responseStatus=status.HTTP_401_UNAUTHORIZED
            return message, responseStatus,user
    
    def get_token(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'isAdmin':user.is_staff
        }
    
def get_version_from_build_script(script_path):
    with open(script_path, 'r') as file:
        for line in file:
            # Match the line that starts with VERSION= and extract the version
            match = re.match(r'^\s*VERSION="([^"]+)"', line)
            if match:
                return match.group(1)  # Return the extracted version
    return None  # Return None if VERSION is not found

            
