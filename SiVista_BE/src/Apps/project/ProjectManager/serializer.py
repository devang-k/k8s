"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: serializer.py  
 * Description: ProjectSerializerBase: A base serializer that contains the shared logic for the last_touched_date. This avoids code duplication and allows you to extend it for other serializers.
                ProjectSerializer: Inherits from ProjectSerializerBase, but it explicitly includes the desired fields (id, project_name, etc.).
                ProjectSerializer1: Inherits from ProjectSerializerBase and includes all fields from the model via "__all__".
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
from src.Apps.project.ProjectManager.models import *
from src.Services.ProjectService import *
from src.Services.NetlistService import *
from src.Services.TechService import *
import string

        
class CreateSerializer(serializers.Serializer):
    projectName=serializers.CharField(max_length=200)
    action=serializers.IntegerField()
    
    def validat(self,data,user_id):
        if (data['projectName'])!='':
            special_characters = string.punctuation
            if not all(char in special_characters for char in data['projectName']):
                if 101>len(data['projectName'])>1:
                    selected_values = getAction.Layout.value | getAction.Hyperexpresivity.value
                    if (data['netlistMetadata']['netlistType']=='USER' or data['netlistMetadata']['netlistType']== 'GLOBAL') :
                        if (data['techMetadata']['techType']=='USER' or data['techMetadata']['techType']== 'GLOBAL') :
                            if ((getAction.Layout.value == data['action']) or (selected_values == data['action'])):
                                if data['techFileContents']!='' and data['techFileContents'] !=None and data['techFileContents']!=[]:
                                    if data['netlistFileContents']!='' and data['netlistFileContents']!=None:
                                        if (len(data['netlistFileContents']) % 4 == 0 and (re.match(r'^[A-Za-z0-9+/=]*$', data['netlistFileContents']))):
                                            # Attempt to decode the string. If it fails, it's not valid base64
                                            base64.b64decode(data['netlistFileContents'], validate=True)
                                            isbase64 = True
                                        else:
                                            isbase64 = False
                                        if not isbase64:
                                            message = "Netlist file content must be in encoded format."
                                            status_code = status.HTTP_400_BAD_REQUEST
                                            response_status = False
                                            return message,status_code,response_status,None
                                        if data['netlistMetadata']['cellSelections']!=None:
                                            selected_cell_names=[]
                                            if isinstance(data['netlistMetadata']['cellSelections'], list):
                                                for cell in data['netlistMetadata']['cellSelections']:
                                                    cell_name = cell.get("cell_name")
                                                    if cell_name:
                                                        selected_cell_names.append(cell_name)
                                            actualList=extract_subckt(b64decode(data['netlistFileContents']).decode('utf-8'))
                                            if (set(selected_cell_names) == set(actualList)):
                                                if any(cell["is_selected"] for cell in data['netlistMetadata']['cellSelections']):
                                                    message,status_code, response_status,techdata=validate_tech_data(data['techFileContents'])
                                                    if status_code==200:
                                                        message, status_code,response_status,data1=insert_project(user_id,data)
                                                        return message, status_code, response_status,data1
                                                    else:
                                                        return message, status_code, response_status,techdata
                                                else:
                                                    message="No cells are selected."
                                                    status_code=status.HTTP_400_BAD_REQUEST
                                                    response_status=False
                                                    return message, status_code, response_status,None
                                            else:
                                                message="Cell mismatch detected. Please verify that the cell details are correct and consistent."
                                                status_code=status.HTTP_400_BAD_REQUEST
                                                response_status=False
                                                return message, status_code, response_status,None
                                        else:
                                            message="Please verify that the cell details are correct and consistent."
                                            status_code=status.HTTP_400_BAD_REQUEST
                                            response_status=False
                                            return message, status_code, response_status,None
                                    else:
                                        message="The netlist file is empty. Please upload a file with the required content."
                                        status_code=status.HTTP_400_BAD_REQUEST
                                        response_status=False
                                        return message, status_code, response_status,None
                                else:
                                    message="The tech file is empty. Please upload a file with the required content."
                                    status_code=status.HTTP_400_BAD_REQUEST
                                    response_status=False
                                    return message, status_code, response_status,None
                            else:
                                message, status_code,response_status,data1=insert_project(user_id,data)
                                return message, status_code, response_status,data1
                        else:
                            message="The Tech file type is not valid. Please provide a file with the correct format."
                            status_code=status.HTTP_400_BAD_REQUEST
                            response_status=False
                            return message, status_code, response_status,None
                    else:
                            message="The Netlist file type is not valid. Please provide a file with the correct format."
                            status_code=status.HTTP_400_BAD_REQUEST
                            response_status=False
                            return message, status_code, response_status,None
                else:
                    message="Please ensure the project name is between 2 and 100 characters long."
                    status_code=status.HTTP_400_BAD_REQUEST
                    response_status=False
                    return message, status_code, response_status,None
            else:
                message="The project name cannot consist only of special characters. Please include letters or numbers in the name."
                status_code=status.HTTP_400_BAD_REQUEST
                response_status=False
                return message, status_code, response_status , None
        else:
            message="Project can't be blank..."
            status_code=status.HTTP_400_BAD_REQUEST
            response_status=False
            return message, status_code, response_status,None
    class Meta:
        model = Project
        fields = ('name','action','stage_one_project','selectedlayouts')
        
class ProjectSerializer(serializers.ModelSerializer):
    last_touched_date = serializers.SerializerMethodField()
    class Meta:
        model= Project
        fields=("id","project_name", "action","created_by","last_touched_date","project_type","version")
    def get_last_touched_date(self, obj):
        # Determine the last touched date between created_date and modified_date
        return max(obj.created_date, obj.modified_date) if obj.created_date and obj.modified_date else None

class ProjectSerializer1(serializers.ModelSerializer):
    last_touched_date = serializers.SerializerMethodField()
    class Meta:
        model= Project
        fields="__all__"
    def get_last_touched_date(self, obj):
        # Determine the last touched date between created_date and modified_date
        return max(obj.created_date, obj.modified_date) if obj.created_date and obj.modified_date else None
    
class TechFileCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechFileCatalog
        # file_url
        fields = ("id", "file_name", "project_id", "drc_count", "lvs_count","created_at")
