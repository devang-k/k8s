"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: models.py  
 * Description: User table model configurations
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
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, UserManager
from django.contrib.auth.models import PermissionsMixin


# Create your models here.
class User(AbstractBaseUser, PermissionsMixin):
    
    id = models.AutoField(primary_key=True) 
    name = models.CharField(max_length=50, null=False)
    username = models.CharField(max_length=10,unique=True)
    email = models.EmailField(max_length=50, null=False)
    password = models.CharField(max_length=100, null=True)
    is_active = models.BooleanField(default=False, null=False)
    is_staff = models.BooleanField(default=False, null=False, db_column="is_admin")
    is_deleted = models.BooleanField(default=False, null=False) 
    created_by = models.ForeignKey('self', on_delete=models.PROTECT, null=True, related_name='created')
    modified_by = models.ForeignKey('self', on_delete=models.PROTECT, null=True, related_name='modified')
    created_date = models.DateField(auto_now=True, null=True)
    modified_date = models.DateField(null=True)
    log_level = models.IntegerField(default=99, null=False) 
    first_name = None
    last_name = None
    last_login = None

    USERNAME_FIELD = "username"
    
    objects = UserManager()
    class Meta:
        db_table = "USER"

class ActiveToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.TextField(unique=True) # refresh token
    expires_at = models.DateTimeField()
    logged_in_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ActiveToken"