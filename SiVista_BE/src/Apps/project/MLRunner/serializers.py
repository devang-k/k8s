"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: serializers.py  
 * Description: The JobSerializer and AllJobSerializer classes are serializers for the Job model, where:

        JobSerializer: Serializes the Job model along with the nested ProjectSerializer for the project field, including specific fields like id, action, status, and others.

        AllJobSerializer: Serializes all fields of the Job model by using __all__ to include every field from the model.
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
from src.Apps.project.ProjectManager.models import Job
from src.Apps.project.ProjectManager.serializer import ProjectSerializer

class JobSerializer(serializers.ModelSerializer):
    project = ProjectSerializer() 
    class Meta:
        model = Job
        fields = ['id','action','status','cells','created_date','created_by','project']  # Or specify the fields you want to include

class AllJobSerializer(serializers.ModelSerializer):
     class Meta:
        model = Job
        fields ='__all__'