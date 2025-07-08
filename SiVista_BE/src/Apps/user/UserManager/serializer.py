"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: serializer.py  
 * Description:  serializers to get data in required dict format from uer table also update users.
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
from src.Apps.user.Login.models import User
from src.Services.UserService import create_user
from rest_framework import status
from rest_framework.validators import UniqueValidator
import hashlib

class ShowUserSerializer(serializers.ModelSerializer):
    log_level = serializers.SerializerMethodField()
    class Meta:
        model=User
        fields = ['id','username', 'email', 'name','is_staff', 'is_active','is_deleted','log_level']  # Specify the fields you want to include in the serialized output
    
    def get_log_level(self, obj):
        log_level_mapping = {
            99: "NO LOGGING",
            1: "DEBUG LOGS",
            2: "WARNING",
            3: "PERFORMANCE LOGS",
            4: "OPERATIONAL LOGS",
            5: "ERROR"
    }
        return log_level_mapping.get(obj.log_level, "UNKNOWN")

class UserUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=10, 
        validators=[UniqueValidator(queryset=User.objects.all())], 
        required=False  # Make it optional for updates
    )
    email = serializers.EmailField(max_length=50, required=False)
    name = serializers.CharField(max_length=50, required=False)
    password = serializers.CharField(max_length=100, write_only=True, required=False)
    is_active = serializers.BooleanField(required=False)
    is_staff = serializers.BooleanField(required=False)
    class Meta:
        model = User
        fields = ['username', 'email', 'name', 'password','is_active', 'is_staff', 'is_deleted','log_level']  # List fields you want to allow updates for
    
    def __init__(self, *args, **kwargs):
        # Store the user instance
        self.instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)
    
    def validate(self, data):
        if 'username' in data:
            self.instance.username=data['username'].upper()
        if 'email' in data:
            self.instance.email=data['email']
        if 'name' in data:
            self.instance.name=data['name'].upper()
        if 'password' in data:
            password=data['password']
            password = hashlib.md5(password.encode())
            password=password.hexdigest().upper()
            self.instance.password=password
        if 'isActive' in data:
            self.instance.is_active=data['isActive']
        if 'isAdmin' in data:
            self.instance.is_staff=data['isAdmin']
        if 'isDeleted' in data:
            self.instance.is_deleted=data['isDeleted']
        if 'logLevel' in data:
            self.instance.log_level=data['logLevel']
        return data
    def save(self, **kwargs):
        # Ensure password hashing is done before saving
        self.instance.save()  # Save the instance after the password is hashed
        return self.instance

class UserCreationSerializer(serializers.Serializer):
    class Meta:
        model = User
        fields = ['name', 'username', 'email', 'password','is_active', 'is_staff']

    def create(self, data, userId):
        username= data['username']
        email=data['email']
        name=data['name']
        is_active = data['isActive']
        is_stuff = data['isAdmin']
        password=data['password']
        password = hashlib.md5(password.encode())
        password=password.hexdigest().upper()
        user=create_user(username,email, password, name, is_active, is_stuff, userId)
        message=f'{user} created successfully.'
        status_code=status.HTTP_200_OK
        response_status=True
        print(f'{user} created successfully')
        return message, status_code, response_status, {"UserID":user.id}
