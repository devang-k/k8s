"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: serializer.py  
 * Description: The NetlistSerializer class provides a robust mechanism to validate and retrieve netlist data based on the file type (GLOBAL or USER), handling both successful retrievals and various types of errors (e.g., file extension issues, missing cells, etc.).
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
from src.Services.NetlistService import *
from SiVista_BE.settings import S3_BUCKET_ROOT
from src.Apps.project.ProjectManager.models import Project
from rest_framework import status

class NetlistSerializer(serializers.Serializer):

    def validate(self, data, user_id):
        filename=data['FileName']
        filetype=data['FileType']
        if filename:
            if ((filename.lower().endswith('.spice'))):
                if filetype=='GLOBAL':
                    filepath=f'{S3_BUCKET_ROOT}/Netlist/0/{filename}'
                    message ,data1 , status_code ,response_status=storage_servicer.get_tech_netlist_data(filepath,filetype,'Netlist')
                    if response_status == True:
                        cell_list=extract_subckt(b64decode(data1).decode('utf-8'))
                        if cell_list != [] or cell_list != None:
                            cell_info=[]
                            for cell_name in cell_list:
                                element={'cell_name':cell_name, 'is_selected':False}
                                cell_info.append(element)
                            get_response={'FileContent':data1, 'Cell_Info':cell_info}
                            return message,status_code,response_status, get_response
                        else:
                            message="No cells found in the netlist file. Please check the file contents."
                            status_code=status.HTTP_404_NOT_FOUND
                            response_status=False
                            return message, status_code, response_status, None
                    else:
                        return message,status_code,response_status, None
                elif filetype=='USER':
                    filepath=f'{S3_BUCKET_ROOT}/Netlist/{user_id}/{filename}'
                    message ,data1,status_code,response_status=storage_servicer.get_tech_netlist_data(filepath,filetype,'Netlist')
                    parts = filename.split('_')
                    projectName = parts[0]
                    project=Project.objects.filter(created_by_id=user_id, project_name=projectName).first()
                    cell_list=project.netlist_metadata['cellSelections']
                    cell_info=[]
                    selected_cell_names=[]
                    if isinstance(cell_list, list):
                        for cell in cell_list:
                            cell_name = cell.get("cell_name")
                            if cell_name:
                                selected_cell_names.append(cell_name)
                    actualList=extract_subckt(b64decode(data1).decode('utf-8'))
                    if actualList == [] or actualList == None:
                        message="No cells found in the netlist file. Please check the file contents."
                        status_code=status.HTTP_404_NOT_FOUND
                        response_status=False
                        return message, status_code, response_status, None
                    if (set(selected_cell_names) == set(actualList)):
                        for cell_data in cell_list:
                            element={'cell_name':cell_data['cell_name'], 'is_selected':cell_data['is_selected']}
                            cell_info.append(element)
                        get_response={'FileContent':data1, 'Cell_Info':cell_info}
                        return message,status_code,response_status, get_response
                    else:
                        return 'Cell Missmatch', status.HTTP_400_BAD_REQUEST, False, None
                else:
                    message='No such file type available'
                    status_code=status.HTTP_404_NOT_FOUND
                    response_status=False
                    data=None
                    return message,status_code,response_status, data
            else:
                message='File extension is incorrect, Kindly select spice file for netlist. '
                status_code=status.HTTP_404_NOT_FOUND
                response_status=False
                data=None
                return message,status_code,response_status, data

        else:
            message='File Not Found.'
            status_code=status.HTTP_404_NOT_FOUND
            response_status=False
            data=None
            return message,status_code,response_status, data