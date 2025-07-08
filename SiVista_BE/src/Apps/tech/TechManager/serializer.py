"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: serializer.py  
 * Description: serializer to get data to validate tech file
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
from src.Services.StorageServices.StorageService import storage_servicer
from src.Services.TechService import *
from src.Services.EncryptDecryptService import decrypt_file_content, InvalidToken
from SiVista_BE.settings import S3_BUCKET_ROOT

class TechInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechInfo
        fields = ('id', 'name', 'support_variation', 'non_support_variation', 'support_ui_visible', 'non_support_ui_visible', 'parameter_support_variation', 'display_name', 'header')
    
class TechSerializer(serializers.Serializer):
    def validate(self, data, user_id):
        try:
            filename=data['FileName']
            filetype=data['FileType']
            projectType=data['projectType']
            if projectType==None or not isinstance(projectType,int):
                message='Invalid Project type.'
                status_code=status.HTTP_400_BAD_REQUEST
                response_status=False
                data=None
                return message,status_code,response_status, data
            project_type=ProjectType.objects.filter(type=projectType).first()
            if not project_type:
                message='Invalid Project type.'
                status_code=status.HTTP_400_BAD_REQUEST
                response_status=False
                data=None
                return message,status_code,response_status, data
            if filename:
                if ((filename.lower().endswith('.tech'))):
                    # if filetype=='GLOBAL':
                    #     filepath=f'{S3_BUCKET_ROOT}/Techfile/0/{filename}'
                    #     message ,data1 , status_code ,response_status=storage_servicer.get_tech_netlist_data(filepath,filetype,'Techfile')
                    #     matrix_data=fetch_tech(data1,projectType)
                    #     if matrix_data == None or matrix_data ==[]:
                    #         message=f'Content not found in {filename}'
                    #         status_code=status.HTTP_404_NOT_FOUND
                    #         response_status=False
                    #         matrix_data={"FileContent":matrix_data}
                    #     else:
                    #         matrix_data={"FileContent":matrix_data}
                    #     return message,status_code,response_status, matrix_data
                    if filetype=='GLOBAL':
                        filepath=f'{S3_BUCKET_ROOT}/Techfile/0/{filename}'
                    elif filetype=='USER':
                        filepath=f'{S3_BUCKET_ROOT}/Techfile/{user_id}/{filename}'
                    else:
                        message='No such file type available'
                        status_code=status.HTTP_404_NOT_FOUND
                        response_status=False
                        data=None
                        return message,status_code,response_status, data
                    message, data1,status_code,response_status=storage_servicer.get_tech_netlist_data(filepath,filetype,'Techfile')
                    if not response_status:
                        message=message
                        status_code=status.HTTP_404_NOT_FOUND
                        response_status=False
                        data=None
                        return message,status_code,response_status, data
                    tech_data={"FileContent":data1}
                    if project_type.variation==False:
                        updated_tech=convert_nonvariable_json(tech_data,project_type.type)
                    else:
                        updated_tech=convert_variable_json(tech_data)
                    if data1 == None or data1 ==[]:
                        message=f'Content not found in {filename}'
                        status_code=status.HTTP_404_NOT_FOUND
                        response_status=False
                    return message,status_code,response_status, updated_tech
                else:
                    message="Extension for tech file is not valid."
                    status_code=status.HTTP_404_NOT_FOUND
                    response_status=False
                    data=None
                    return message,status_code,response_status, data
            else:
                message='File not provided'
                status_code=status.HTTP_404_NOT_FOUND
                response_status=False
                data=None
                return message,status_code,response_status, data
        except Exception as e:
            print(e)
        
    