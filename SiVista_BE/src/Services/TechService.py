"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: TechService.py  
 * Description: Service to convert tech file into tech json
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
from base64 import b64decode
import re
import ast
from typing import Dict, List, Union
from rest_framework import status
from src.Apps.project.ProjectManager.models import ProjectType , TechDetailedInfo, TechInfo

def fetch_tech(content,projectType):
        content=b64decode(content).decode('utf-8')
        content_up_to_string = '\n'.join(content)
        content=remove_lines_starting_with_hash(content_up_to_string)
        content=content.replace('\n','')
        content=convert_to_json(content,projectType)
        permutation_data = next(item for item in content if item["name"] == "permutation")["data"]
        file_content=update_is_selected(content,permutation_data)
        return file_content

def update_is_selected(file_content, permutation_data):
    pattern2list=['layer_width']
    for entry in permutation_data:
        parameterName=entry.get('parameterName')
        if parameterName=='other':
            name=entry.get('name')
            for section in file_content:
                if section["name"] == "other":
                    for item in section["data"]:
                        if item["key"]["key1"] == name:
                            item["isSelected"] = True
                            if isinstance(item['val'], list):
                                entry['defaultValue']=item['val']
                            else:
                                entry["defaultValue"]=[item['val']]
                            entry['options']=item['options']
                            if len(item['keyDisplayName'].values())==1:
                                entry['displayName']=list(item['keyDisplayName'].values())[0]
                            else:
                                entry['displayName']=list(item['keyDisplayName'].values())
                            entry['negativeStartAllowed']=item['negativeStartAllowed']
                            entry['negativeEndAllowed']=item['negativeEndAllowed']
                            entry['stepperFloat']=item['stepperFloat']
                            entry['stepper']=item['stepper']
                            entry['value']['step']=item['stepper']
                            entry['defaultStartValue']=item['defaultStartValue']
                            entry['defaultEndValue']=item['defaultEndValue']
                            entry['minStart']=item['minStart']
                            entry['maxStart']=item['maxStart']
                            entry['minEnd']=item['minEnd']
                            entry['maxEnd']=item['maxEnd']
                            entry['startPercentage']=item['startPercentage']
                            entry['endPercentage']=item['endPercentage']
        if parameterName in pattern2list:
            name=entry.get('attribute')
            name
            for section in file_content:
                if section["name"] in pattern2list:
                    for item in section["data"]:
                        if item["key"]["key1"] == name:
                            item["isSelected"] = True
                            if isinstance(item['val'], list):
                                entry['defaultValue']=item['val']
                            else:
                                entry["defaultValue"]=[item['val']]
                            entry['options']=item['options']
                            if len(item['keyDisplayName'].values())==1:
                                entry['displayName']=list(item['keyDisplayName'].values())[0]
                            else:
                                entry['displayName']=list(item['keyDisplayName'].values())
                            entry['negativeStartAllowed']=item['negativeStartAllowed']
                            entry['negativeEndAllowed']=item['negativeEndAllowed']
                            entry['stepperFloat']=item['stepperFloat']
                            entry['stepper']=item['stepper']
                            entry['value']['step']=item['stepper']
                            entry['defaultStartValue']=item['defaultStartValue']
                            entry['defaultEndValue']=item['defaultEndValue']
                            entry['minStart']=item['minStart']
                            entry['maxStart']=item['maxStart']
                            entry['minEnd']=item['minEnd']
                            entry['maxEnd']=item['maxEnd']
                            entry['startPercentage']=item['startPercentage']
                            entry['endPercentage']=item['endPercentage']
        if parameterName=='min_spacing':
            name=entry.get('attribute')
            for section in file_content:
                if section["name"] == "min_spacing":
                    for item in section["data"]:
                        if isinstance(name , list):
                            if (item["key"]['key1'] == name[0] and item["key"]['key2'] == name[1]):
                                item["isSelected"] = True
                                if isinstance(item['val'], list):
                                    entry['defaultValue']=item['val']
                                else:
                                    entry["defaultValue"]=[item['val']]
                                entry['options']=item['options']
                                if len(item['keyDisplayName'].values())==1:
                                    entry['displayName']=list(item['keyDisplayName'].values())[0]
                                else:
                                    entry['displayName']=list(item['keyDisplayName'].values())
                                entry['negativeStartAllowed']=item['negativeStartAllowed']
                                entry['negativeEndAllowed']=item['negativeEndAllowed']
                                entry['stepperFloat']=item['stepperFloat']
                                entry['stepper']=item['stepper']
                                entry['value']['step']=item['stepper']
                                entry['defaultStartValue']=item['defaultStartValue']
                                entry['defaultEndValue']=item['defaultEndValue']
                                entry['minStart']=item['minStart']
                                entry['maxStart']=item['maxStart']
                                entry['minEnd']=item['minEnd']
                                entry['maxEnd']=item['maxEnd']
                                entry['startPercentage']=item['startPercentage']
                                entry['endPercentage']=item['endPercentage']
                        elif isinstance(name ,str):
                            if (item["key"]['key1'] == name):
                                item["isSelected"] = True
                                if isinstance(item['val'], list):
                                    entry['defaultValue']=item['val']
                                else:
                                    entry["defaultValue"]=[item['val']]
                                entry['options']=item['options']
                                if len(item['keyDisplayName'].values())==1:
                                    entry['displayName']=list(item['keyDisplayName'].values())[0]
                                else:
                                    entry['displayName']=list(item['keyDisplayName'].values())
                                entry['negativeStartAllowed']=item['negativeStartAllowed']
                                entry['negativeEndAllowed']=item['negativeEndAllowed']
                                entry['stepperFloat']=item['stepperFloat']
                                entry['stepper']=item['stepper']
                                entry['value']['step']=item['stepper']
                                entry['defaultStartValue']=item['defaultStartValue']
                                entry['defaultEndValue']=item['defaultEndValue']
                                entry['minStart']=item['minStart']
                                entry['maxStart']=item['maxStart']
                                entry['minEnd']=item['minEnd']
                                entry['maxEnd']=item['maxEnd']
                                entry['startPercentage']=item['startPercentage']
                                entry['endPercentage']=item['endPercentage']
                        else:
                            pass
    return file_content
def extract_other_dict(text,name,projectType):
    dataResult=[]
    getparameterid=TechInfo.objects.filter(name=name).first()
    filtered_names = TechDetailedInfo.objects.filter(parameter_type_id=getparameterid.id, project_type=projectType).values_list('name', flat=True)
    keys_to_extract = [item[0] for item in filtered_names]
    pattern = re.compile(r"'(\w+)'\s*=\s*(\'[^\']*\'|\"[^\"]*\"|True|False|[\d.]+)")
    matches = pattern.findall(text)
    placerfound = 0
    for match in matches:
        key, value = match
        if key in keys_to_extract:
            if key=='placer':
                placerfound+=1
            if value in ['True', 'False']:
                value = eval(value)  # Convert to boolean
                valtype = 5  # Boolean type
            elif '.' in value:
                value = float(value)
                valtype=1
            else:
                try:
                    value = int(value)  # Attempt to convert to integer
                    valtype = 1  # Integer type
                except ValueError:
            # If it cannot be converted to an integer, treat it as a string
                    if key == 'placer' and projectType==2:
                        value='smt'
                    else:
                        value = value.replace("'","")
                    valtype = 3  # String type
            techinfo = TechDetailedInfo.objects.filter(parameter_type_id=getparameterid.id, name__contains=[key]).first()
            if techinfo:
                parameterHidingRule=None
                negative_start_allowed=techinfo.negative_start_allowed
                negative_end_allowed=techinfo.negative_end_allowed
                stepper_float=techinfo.stepper_float
                if valtype==1:
                    stepper=techinfo.stepper
                    defaultStartValue= techinfo.defaultStartValue
                    defaultEndValue= techinfo.defaultEndValue
                    minStart= techinfo.minStart
                    maxStart= techinfo.maxStart
                    minEnd= techinfo.minEnd
                    maxEnd= techinfo.maxEnd
                    startPercentage= techinfo.startPercentage
                    endPercentage= techinfo.endPercentage
                else:
                    stepper=None
                    defaultStartValue=None
                    defaultEndValue=None
                    minStart=None
                    maxStart=None
                    minEnd=None
                    maxEnd=None
                    startPercentage=None
                    endPercentage=None
                displaynamekey1=techinfo.diplay_name[0]
                unit=techinfo.unit
                description=techinfo.description
                if techinfo.options:
                    if len(techinfo.options)==1:
                        options=techinfo.options                           
                        options_description=techinfo.options_description
                    else:
                        options=techinfo.options
                        if options== ["true","false"] or options== ['True', 'False']:
                            options=[True,False]
                        options_description=techinfo.options_description
                else:
                    options=techinfo.options
                    if options== ["true","false"] or options== ['True', 'False']:
                        options=[True,False]
                    options_description=techinfo.options_description
                option_display_name=techinfo.options_display_name
                ui_visible=techinfo.ui_visible
                if key=='height_req' and projectType==2:
                    ui_visible=True
                support_variation=techinfo.support_variation
                if techinfo.options:
                    if len(techinfo.options)==1:
                        if value not in techinfo.options:
                            value=str(value)
                            if value.upper() == 'TRUE':
                                value=True
                            elif value.upper() == 'FALSE':
                                value=False
                            else:
                                value=techinfo.options[0]
            else:
                parameterHidingRule=None
                negative_start_allowed=False
                negative_end_allowed=False
                stepper_float=False
                stepper=None
                defaultStartValue=None
                defaultEndValue=None
                minStart=None
                maxStart=None
                minEnd=None
                maxEnd=None
                startPercentage=None
                endPercentage=None
                displaynamekey1=key
                unit=None
                description=None
                options=None
                option_display_name=None
                options_description=None
                ui_visible=False
                if key=='height_req' and projectType==2:
                    ui_visible=True
                support_variation=False
            dataResult.append({'supportsVariations':support_variation,"uiVisible":ui_visible,"key":{"key1":key},"keyDisplayName":{"displayNameKey1":displaynamekey1},"unit": unit,"description":description,"type":valtype,"parameterHidingRule":parameterHidingRule, "negativeStartAllowed":negative_start_allowed,"negativeEndAllowed":negative_end_allowed,"stepperFloat":stepper_float,"stepper":stepper,"defaultStartValue":defaultStartValue,"defaultEndValue":defaultEndValue,"minStart":minStart,"maxStart":maxStart,"minEnd":minEnd,"maxEnd":maxEnd,"startPercentage":startPercentage,"endPercentage":endPercentage,"options":options,"displayNameOptions":option_display_name,"optionsDescription":options_description,"val":value,"isSelected":False})
    if placerfound == 0:
        techinfo = TechDetailedInfo.objects.filter(parameter_type_id=getparameterid.id, name__contains=['placer'], project_type=projectType).first()
        if projectType in [1,0]:
            value='base0'
        elif projectType in [2]:
            value='smt'
        else :
            value=None
        if techinfo:
            parameterHidingRule=None
            negative_start_allowed=techinfo.negative_start_allowed
            negative_end_allowed=techinfo.negative_end_allowed
            stepper_float=techinfo.stepper_float
            if valtype==1:
                stepper=techinfo.stepper
                defaultStartValue= techinfo.defaultStartValue
                defaultEndValue= techinfo.defaultEndValue
                minStart= techinfo.minStart
                maxStart= techinfo.maxStart
                minEnd= techinfo.minEnd
                maxEnd= techinfo.maxEnd
                startPercentage= techinfo.startPercentage
                endPercentage= techinfo.endPercentage
            else:
                stepper=None
                defaultStartValue=None
                defaultEndValue=None
                minStart=None
                maxStart=None
                minEnd=None
                maxEnd=None
                startPercentage=None
                endPercentage=None
            key='placer'
            displaynamekey1=techinfo.diplay_name[0]
            unit=techinfo.unit
            description=techinfo.description
            options=techinfo.options
            option_display_name=techinfo.options_display_name
            options_description=techinfo.options_description
            ui_visible=techinfo.ui_visible
            support_variation=techinfo.support_variation
            type_config=3
        else:
            parameterHidingRule=None
            negative_start_allowed=False
            negative_end_allowed=False
            stepper_float=False
            stepper=None
            defaultStartValue=None
            defaultEndValue=None
            minStart=None
            maxStart=None
            minEnd=None
            maxEnd=None
            startPercentage=None
            endPercentage=None
            key='placer'
            displaynamekey1=key
            unit=None
            description=None
            options=None
            option_display_name=None
            options_description=None
            ui_visible=False
            support_variation=False
            type_config=3
        dataResult.append({'supportsVariations':support_variation,"uiVisible":ui_visible,"key":{"key1":key},"keyDisplayName":{"displayNameKey1":displaynamekey1},"unit": unit,"description":description,"type": type_config,"parameterHidingRule":parameterHidingRule, "negativeStartAllowed":negative_start_allowed,"negativeEndAllowed":negative_end_allowed,"stepperFloat":stepper_float,"stepper":stepper,"defaultStartValue":defaultStartValue,"defaultEndValue":defaultEndValue,"minStart":minStart,"maxStart":maxStart,"minEnd":minEnd,"maxEnd":maxEnd,"startPercentage":startPercentage,"endPercentage":endPercentage,"options":options,"displayNameOptions":option_display_name,"optionsDescription":options_description, "val":value ,"isSelected":False})
    return dataResult

def extract_specific_keys(text,projectType):
    resultData=[]
    keys_of_interest = [
    'scaling_factor',
    'db_unit',
    'transistor_channel_width_sizing',
    'pin_layer',
    'power_layer',
    'connectable_layers',
    'nanosheet',
    'transistor_offset_y',
    'cell_width',
    'cell_height',
    'minimum_gate_width_nfet',
    'minimum_gate_width_pfet',
    'orientation_change_penalty',
    'gate_length',
    'my_unused2',
    'my_diffusionlayer'
    ]

    patterns = {
        'tuple': r'\((\d+),\s*(\d+)\)',
        'float': r'\d+\.\d+', 
        'int': r'\d+',
        'string': r"'([^']*)'",
        'exponential':r'\d+\.\d*[eE][+-]?\d+|\d+[eE][+-]?\d+'
    }

    pattern = re.compile(r"'(\w+)'\s*=\s*(\'[^\']*\'|\d+\.\d*[eE][+-]?\d+|\d+[eE][+-]?\d+|\d+\.?\d*|\(\d+,\s*\d+\))")

    matches = pattern.findall(text)
    for match in matches:
        key, value = match
        if key in keys_of_interest:
            if re.match(patterns['tuple'], value):
                match = re.match(patterns['tuple'], value)
                if match:
                    values = list(map(int, match.groups()))
                    value = values
                    type_config=2
            elif re.match(patterns['exponential'], value):
                value = float(value) 
                type_config = 1
            elif re.match(patterns['float'], value):
                value = float(value)
                type_config=1
            elif re.match(patterns['int'], value):
                value = int(value)
                type_config=1
            elif re.match(patterns['string'], value):
                value = re.match(patterns['string'], value).group(1)
                type_config=3
            techinfo= TechDetailedInfo.objects.filter(parameter_type_id= 7, name__contains=[key], project_type=projectType).first()
            if techinfo:
                parameterHidingRule=None
                negative_start_allowed=techinfo.negative_start_allowed
                negative_end_allowed=techinfo.negative_end_allowed
                stepper_float=techinfo.stepper_float
                if type_config==1:
                    stepper=techinfo.stepper
                    defaultStartValue= techinfo.defaultStartValue
                    defaultEndValue= techinfo.defaultEndValue
                    minStart= techinfo.minStart
                    maxStart= techinfo.maxStart
                    minEnd= techinfo.minEnd
                    maxEnd= techinfo.maxEnd
                    startPercentage= techinfo.startPercentage
                    endPercentage= techinfo.endPercentage
                else:
                    stepper=None
                    defaultStartValue=None
                    defaultEndValue=None
                    minStart=None
                    maxStart=None
                    minEnd=None
                    maxEnd=None
                    startPercentage=None
                    endPercentage=None
                displaynamekey1=techinfo.diplay_name[0]
                unit=techinfo.unit
                description=techinfo.description
                options=techinfo.options
                option_display_name=techinfo.options_display_name
                options_description=techinfo.options_description
                ui_visible=techinfo.ui_visible
                support_variation=techinfo.support_variation
            else:
                parameterHidingRule=None
                negative_start_allowed=False
                negative_end_allowed=False
                stepper_float=False
                stepper=None
                defaultStartValue=None
                defaultEndValue=None
                minStart=None
                maxStart=None
                minEnd=None
                maxEnd=None
                startPercentage=None
                endPercentage=None
                displaynamekey1=key
                unit=None
                description=None
                options=None
                option_display_name=None
                options_description=None
                ui_visible=False
                support_variation=False
            resultData.append({'supportsVariations':support_variation,"uiVisible":ui_visible,"key":{"key1":key},"keyDisplayName":{"displayNameKey1":displaynamekey1},"unit": unit,"description":description,"type": type_config,"parameterHidingRule":parameterHidingRule, "negativeStartAllowed":negative_start_allowed,"negativeEndAllowed":negative_end_allowed,"stepperFloat":stepper_float,"stepper":stepper,"defaultStartValue":defaultStartValue,"defaultEndValue":defaultEndValue,"minStart":minStart,"maxStart":maxStart,"minEnd":minEnd,"maxEnd":maxEnd,"startPercentage":startPercentage,"endPercentage":endPercentage,"options":options,"displayNameOptions":option_display_name,"optionsDescription":options_description, "val": value,"isSelected":False})
    return resultData
    
def remove_lines_starting_with_hash(multiline_string):
    lines = multiline_string.splitlines()
    filtered_lines = [line for line in lines if not line.startswith('#') ]
    return '\n'.join(filtered_lines)

def convert_values_to_int(data):
    if isinstance(data, dict):
        return {k: convert_values_to_int(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_values_to_int(i) for i in data]
    elif isinstance(data, str) and data.isdigit():
        return int(data)
    else:
        return data

# get json pattern for Layer map pattern
def pattern1(data,projectType):
    kv_pattern = re.compile(r"'(\w+)':\s*\((\d+),\s*(\d+)\)")
    matches = kv_pattern.findall(data)
    data1=[]
    for key, x, y in matches:
        techinfo=TechDetailedInfo.objects.filter(parameter_type_id= 1,project_type=projectType, name__contains=[key]).first()
        valtype=2
        if techinfo:
            parameterHidingRule=None
            negative_start_allowed=techinfo.negative_start_allowed
            negative_end_allowed=techinfo.negative_end_allowed
            stepper_float=techinfo.stepper_float
            if valtype==1:
                stepper=techinfo.stepper
                defaultStartValue= techinfo.defaultStartValue
                defaultEndValue= techinfo.defaultEndValue
                minStart= techinfo.minStart
                maxStart= techinfo.maxStart
                minEnd= techinfo.minEnd
                maxEnd= techinfo.maxEnd
                startPercentage= techinfo.startPercentage
                endPercentage= techinfo.endPercentage
            else:
                stepper=None
                defaultStartValue=None
                defaultEndValue=None
                minStart=None
                maxStart=None
                minEnd=None
                maxEnd=None
                startPercentage=None
                endPercentage=None
            displaynamekey1=techinfo.diplay_name[0]
            unit=techinfo.unit
            description=techinfo.description
            options=techinfo.options
            option_display_name=techinfo.options_display_name
            options_description=techinfo.options_description
            ui_visible=techinfo.ui_visible
            support_variation=techinfo.support_variation
        else:
            parameterHidingRule=None
            negative_start_allowed=False
            negative_end_allowed=False
            stepper_float=False
            stepper=None
            defaultStartValue=None
            defaultEndValue=None
            minStart=None
            maxStart=None
            minEnd=None
            maxEnd=None
            startPercentage=None
            endPercentage=None
            displaynamekey1=key
            unit=None
            description=None
            options=None
            option_display_name=None
            options_description=None
            ui_visible=False
            support_variation=False
        data1.append({'supportsVariations':support_variation,"uiVisible":ui_visible,"key":{"key1":key},"keyDisplayName":{"displayNameKey1":displaynamekey1},"unit": unit,"description":description,"type":valtype,"parameterHidingRule":parameterHidingRule, "negativeStartAllowed":negative_start_allowed,"negativeEndAllowed":negative_end_allowed,"stepperFloat":stepper_float,"stepper":stepper,"defaultStartValue":defaultStartValue,"defaultEndValue":defaultEndValue,"minStart":minStart,"maxStart":maxStart,"minEnd":minEnd,"maxEnd":maxEnd,"startPercentage":startPercentage,"endPercentage":endPercentage,"options":options,"displayNameOptions":option_display_name,"optionsDescription":options_description,"val":(int(x), int(y)),"isSelected":False})
    return data1

#get data for ['layer_width','routing_order','hinder','weights_horizontal','weights_vertical','routing_layers','via_size']
def pattern2(data,pattern_name,projectType):
    dataResult=[]
    pattern = r"'(\w+)'\s*:\s*(['\"]?[\w\s.]+['\"]?)"
    matches = re.findall(pattern, data)
    for key, value in matches:
        value = value.strip("'\"")
        if value.isdigit():
            value = int(value)
            valtype=1
        elif re.match(r"^\d*\.\d+$", value):
            value = float(value)
            valtype=1
        else:
            value= str(value)
            valtype=3
        techParameter=TechInfo.objects.filter(name=pattern_name).first()
        if techParameter:
            techinfo=TechDetailedInfo.objects.filter(parameter_type_id= techParameter.id,project_type=projectType, name__contains=[key]).first()
        else:
            techinfo=None
        if techinfo:
            parameterHidingRule=None
            negative_start_allowed=techinfo.negative_start_allowed
            negative_end_allowed=techinfo.negative_end_allowed
            stepper_float=techinfo.stepper_float
            if valtype==1:
                stepper=techinfo.stepper
                defaultStartValue= techinfo.defaultStartValue
                defaultEndValue= techinfo.defaultEndValue
                minStart= techinfo.minStart
                maxStart= techinfo.maxStart
                minEnd= techinfo.minEnd
                maxEnd= techinfo.maxEnd
                startPercentage= techinfo.startPercentage
                endPercentage= techinfo.endPercentage
            else:
                stepper=None
                defaultStartValue=None
                defaultEndValue=None
                minStart=None
                maxStart=None
                minEnd=None
                maxEnd=None
                startPercentage=None
                endPercentage=None
            displaynamekey1=techinfo.diplay_name[0]
            unit=techinfo.unit
            description=techinfo.description
            options=techinfo.options
            option_display_name=techinfo.options_display_name
            options_description=techinfo.options_description
            ui_visible=techinfo.ui_visible
            support_variation=techinfo.support_variation
        else:
            parameterHidingRule=None
            negative_start_allowed=False
            negative_end_allowed=False
            stepper_float=False
            stepper=None
            defaultStartValue=None
            defaultEndValue=None
            minStart=None
            maxStart=None
            minEnd=None
            maxEnd=None
            startPercentage=None
            endPercentage=None
            displaynamekey1=key
            unit=None
            description=None
            options=None
            option_display_name=None
            options_description=None
            ui_visible=False
            support_variation=False
        dataResult.append({'supportsVariations':support_variation,"uiVisible":ui_visible,"key":{"key1":key},"keyDisplayName":{"displayNameKey1":displaynamekey1},"unit": unit,"description":description,"type":valtype,"parameterHidingRule":parameterHidingRule, "negativeStartAllowed":negative_start_allowed,"negativeEndAllowed":negative_end_allowed,"stepperFloat":stepper_float,"stepper":stepper,"defaultStartValue":defaultStartValue,"defaultEndValue":defaultEndValue,"minStart":minStart,"maxStart":maxStart,"minEnd":minEnd,"maxEnd":maxEnd,"startPercentage":startPercentage,"endPercentage":endPercentage,"options":options,"displayNameOptions":option_display_name,"optionsDescription":options_description,"val": value,"isSelected":False})
    return dataResult

#get data for ['min_spacing','via_weights','minimum_enclosure']

def pattern3(data, pattern_name, projectType):
    tuple_pattern = re.compile(r"\(\s*'([\w_]+)'\s*(?:,\s*'([\w_]+)')?\s*\)\s*:\s*(-?\d*\.?\d+(?:[eE][-+]?\d+)?)", re.MULTILINE)

    matches = tuple_pattern.findall(data)
    result=[]
    for match in matches:
        key1 = match[0]  # First key is always present
        key2 = match[1] if match[1] else None  # Second key might be None
        val = match[2]  # Extracted numerical value
        if '.' in val or 'e' in val or 'E' in val:
            val = float(val)  # Convert to float if it contains a decimal point or 'e'
        else:
            val = int(val)  # Otherwise, convert to int
        techParameter=TechInfo.objects.filter(name=pattern_name).first()
        if techParameter:
            if key2==None:
                techinfo=TechDetailedInfo.objects.filter(parameter_type_id= techParameter.id,project_type=projectType, name__contains=[key1]).first()
            else:
                techinfo=TechDetailedInfo.objects.filter(parameter_type_id= techParameter.id,project_type=projectType, name__contains=[key1,key2]).first()
        else:
            techinfo=None
        valtype=1
        if techinfo:
            parameterHidingRule=None
            negative_start_allowed=techinfo.negative_start_allowed
            negative_end_allowed=techinfo.negative_end_allowed
            stepper_float=techinfo.stepper_float
            if valtype==1:
                stepper=techinfo.stepper
                defaultStartValue= techinfo.defaultStartValue
                defaultEndValue= techinfo.defaultEndValue
                minStart= techinfo.minStart
                maxStart= techinfo.maxStart
                minEnd= techinfo.minEnd
                maxEnd= techinfo.maxEnd
                startPercentage= techinfo.startPercentage
                endPercentage= techinfo.endPercentage
            else:
                stepper=None
                defaultStartValue=None
                defaultEndValue=None
                minStart=None
                maxStart=None
                minEnd=None
                maxEnd=None
                startPercentage=None
                endPercentage=None
            displaynamekey1=techinfo.diplay_name[0]
            if pattern_name=='min_spacing':
                displaynamekey2=None
            else:
                displaynamekey2=techinfo.diplay_name[1]
            unit=techinfo.unit
            description=techinfo.description
            options=techinfo.options
            option_display_name=techinfo.options_display_name
            options_description=techinfo.options_description
            ui_visible=techinfo.ui_visible
            support_variation=techinfo.support_variation
        else:
            parameterHidingRule=None
            negative_start_allowed=False
            negative_end_allowed=False
            stepper_float=False
            stepper=None
            defaultStartValue=None
            defaultEndValue=None
            minStart=None
            maxStart=None
            minEnd=None
            maxEnd=None
            startPercentage=None
            endPercentage=None
            displaynamekey1=key1
            if key2==None:
                displaynamekey2=None
            else:
                displaynamekey2=key2
            unit=None
            description=None
            options=None
            option_display_name=None
            options_description=None
            ui_visible=True
            support_variation=True
        if key2==None and displaynamekey2==None:
            result.append({'supportsVariations':support_variation,"uiVisible":ui_visible,"key":{"key1":key1},"keyDisplayName":{"displayNameKey1":displaynamekey1},"unit": unit,"description":description,"type":valtype,"parameterHidingRule":parameterHidingRule, "negativeStartAllowed":negative_start_allowed,"negativeEndAllowed":negative_end_allowed,"stepperFloat":stepper_float,"stepper":stepper,"defaultStartValue":defaultStartValue,"defaultEndValue":defaultEndValue,"minStart":minStart,"maxStart":maxStart,"minEnd":minEnd,"maxEnd":maxEnd,"startPercentage":startPercentage,"endPercentage":endPercentage,"options":options,"displayNameOptions":option_display_name,"optionsDescription":options_description,"val": val,"isSelected":False})
        elif key2 and displaynamekey2==None:
            result.append({'supportsVariations':support_variation,"uiVisible":ui_visible,"key":{"key1":key1,"key2":key2},"keyDisplayName":{"displayNameKey1":displaynamekey1},"unit": unit,"description":description,"type":valtype,"parameterHidingRule":parameterHidingRule, "negativeStartAllowed":negative_start_allowed,"negativeEndAllowed":negative_end_allowed,"stepperFloat":stepper_float,"stepper":stepper,"defaultStartValue":defaultStartValue,"defaultEndValue":defaultEndValue,"minStart":minStart,"maxStart":maxStart,"minEnd":minEnd,"maxEnd":maxEnd,"startPercentage":startPercentage,"endPercentage":endPercentage,"options":options,"displayNameOptions":option_display_name,"optionsDescription":options_description,"val": val,"isSelected":False})
        else:
            result.append({'supportsVariations':support_variation,"uiVisible":ui_visible,"key":{"key1":key1,"key2":key2},"keyDisplayName":{"displayNameKey1":displaynamekey1 ,"displayNameKey2":displaynamekey2},"unit": unit,"description":description,"type":valtype,"parameterHidingRule":parameterHidingRule, "negativeStartAllowed":negative_start_allowed,"negativeEndAllowed":negative_end_allowed,"stepperFloat":stepper_float,"stepper":stepper,"defaultStartValue":defaultStartValue,"defaultEndValue":defaultEndValue,"minStart":minStart,"maxStart":maxStart,"minEnd":minEnd,"maxEnd":maxEnd,"startPercentage":startPercentage,"endPercentage":endPercentage,"options":options,"displayNameOptions":option_display_name,"optionsDescription":options_description,"val": val,"isSelected":False})    
    return result

#get json pattern for Layer properties pattern
def pattern4(data_str,pattern_name,projectType):
    data_str = '{' + data_str.strip() + '}'
    # Regular expression pattern to match key-value pairs
    item_pattern = re.compile(r'(\d+):\s*\{([^}]*)\}', re.MULTILINE | re.DOTALL)
    items = item_pattern.findall(data_str)
    # Convert to the desired format
    result = []
    for key_str, value_str in items:
        key = int(key_str)  # Convert key to integer
        # Add braces back around the value string
        value_str = '{' + value_str.strip() + '}'
        try:
            # Safely evaluate the string to convert it into a dictionary
            value_dict = ast.literal_eval(value_str)
            updated_val_data=list()
            update_value_dict_layer = {}
            update_value_dict_layer["key"] = 'layer'
            update_value_dict_layer["val"] = key_str
            update_value_dict_layer["type"] = 1
            update_value_dict_layer["isEditable"] = False
            updated_val_data.append(update_value_dict_layer)
            for key, value in value_dict.items():
                update_value_dict={}
                if key=='color':
                    value=f"#{value:06X}"
                    update_value_dict["key"] = key
                    update_value_dict["val"] = value
                    update_value_dict["type"] = 6
                    update_value_dict["isEditable"] = True
                    updated_val_data.append(update_value_dict)
                elif key=='opacity':
                    update_value_dict["key"] = key
                    update_value_dict["val"] = value
                    update_value_dict["type"] = 1
                    update_value_dict["isEditable"] = True
                    updated_val_data.append(update_value_dict)
                elif key=='offset':
                    update_value_dict["key"] = key
                    update_value_dict["val"] = value
                    update_value_dict["type"] = 1
                    update_value_dict["isEditable"] = True
                    updated_val_data.append(update_value_dict)
                elif key=='height':
                    update_value_dict["key"] = key
                    update_value_dict["val"] = value
                    update_value_dict["type"] = 1
                    update_value_dict["isEditable"] = True
                    updated_val_data.append(update_value_dict)
                elif key=='shape':
                    update_value_dict["key"] = key
                    update_value_dict["val"] = value
                    update_value_dict["type"] = 8
                    update_value_dict["options"]=['box','diamond','nanosheet']
                    update_value_dict["isEditable"] = True
                    updated_val_data.append(update_value_dict)
                elif key=='name':
                    update_value_dict["key"] = key
                    update_value_dict["val"] = value
                    update_value_dict["type"] = 3
                    update_value_dict["isEditable"] = False
                    updated_val_data.append(update_value_dict)
            desired_order = ['name', 'layer', 'color', 'opacity', 'offset', 'height', 'shape']
            # Reorder the list based on the desired order
            updated_val_data_seq = sorted(updated_val_data, key=lambda x: desired_order.index(x['key']))
            techParameter=TechInfo.objects.filter(name=pattern_name).first()
            if techParameter:
                techinfo=TechDetailedInfo.objects.filter(parameter_type_id= techParameter.id,project_type=projectType, name__contains=[key]).first()
            else:
                techinfo=None
            valtype=7
            if techinfo:
                parameterHidingRule=None
                negative_start_allowed=techinfo.negative_start_allowed
                negative_end_allowed=techinfo.negative_end_allowed
                stepper_float=techinfo.stepper_float
                if valtype==1:
                    stepper=techinfo.stepper
                    defaultStartValue= techinfo.defaultStartValue
                    defaultEndValue= techinfo.defaultEndValue
                    minStart= techinfo.minStart
                    maxStart= techinfo.maxStart
                    minEnd= techinfo.minEnd
                    maxEnd= techinfo.maxEnd
                    startPercentage= techinfo.startPercentage
                    endPercentage= techinfo.endPercentage
                else:
                    stepper=None
                    defaultStartValue=None
                    defaultEndValue=None
                    minStart=None
                    maxStart=None
                    minEnd=None
                    maxEnd=None
                    startPercentage=None
                    endPercentage=None
                displaynamekey1=techinfo.diplay_name[0]
                unit=techinfo.unit
                description=techinfo.description
                options=techinfo.options
                option_display_name=techinfo.options_display_name
                options_description=techinfo.options_description
                if projectType==0:
                    ui_visible=True
                else:
                    ui_visible=techinfo.ui_visible
                support_variation=techinfo.support_variation
            else:
                parameterHidingRule=None
                negative_start_allowed=False
                negative_end_allowed=False
                stepper_float=False
                stepper=None
                defaultStartValue=None
                defaultEndValue=None
                minStart=None
                maxStart=None
                minEnd=None
                maxEnd=None
                startPercentage=None
                endPercentage=None
                displaynamekey1=key_str
                unit=None
                description=None
                options=None
                option_display_name=None
                options_description=None
                if projectType==0:
                    ui_visible=True
                else:
                    ui_visible=False
                support_variation=False
            result.append({'supportsVariations':support_variation,"uiVisible":ui_visible,"key":{"key1":key_str},"keyDisplayName":{"displayNameKey1":displaynamekey1},"unit": unit,"description":description,"type":valtype,"parameterHidingRule":parameterHidingRule, "negativeStartAllowed":negative_start_allowed,"negativeEndAllowed":negative_end_allowed,"stepperFloat":stepper_float,"stepper":stepper,"defaultStartValue":defaultStartValue,"defaultEndValue":defaultEndValue,"minStart":minStart,"maxStart":maxStart,"minEnd":minEnd,"maxEnd":maxEnd,"startPercentage":startPercentage,"endPercentage":endPercentage,"options":options,"displayNameOptions":option_display_name,"optionsDescription":options_description,"val": updated_val_data_seq,"isSelected":False})
        except (SyntaxError, ValueError) as e:
            print(f"Error parsing dictionary for key {key}: {e}")

    return result

def getDisplayName(name):
    tech_info=TechInfo.objects.filter(name=name).first()
    if tech_info:
        if tech_info.display_name:
            displaynamekey=tech_info.display_name
        else:
            displaynamekey=name
    else:
        displaynamekey=name
    return displaynamekey

def getAttributeDisplayName(attribute):
    pass 

def extract_permutation(text: str) -> List[Dict[str, Union[str, List[str], Dict[str, int]]]]:
    range_pattern = re.compile(
        r'\(\s*(\'[^\']*\'|[^\',\s]+)\s*,\s*(\'[^\']*\'|[^\')\s]+)\s*\)\s*:\s*range\((\d+),\s*(\d+),\s*(\d+)\)'
    )
    #Extract non range pattern
    non_range_pattern = re.compile(
        r'\(\s*(\'[^\']*\'|[^\',\s]+)\s*,\s*(\'[^\']*\'|[^\')\s]+)\s*\)\s*:\s*\(([^)]+)\)'
    )
    #Extract list like pattern 
    list_pattern = re.compile(
        r"\(\s*'([^']*)'\s*,\s*\(\s*'([^']*)'(?:\s*,\s*'([^']*)')*\s*\)\s*\)\s*:\s*range\(([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)\)"
    )

    results = []
    for match in range_pattern.finditer(text):
        name = match.group(1).strip("'")
        attribute = match.group(2).strip("'")
        start = int(match.group(3))
        end = int(match.group(4))
        step = int(match.group(5))
        
        if attribute=="":
            parameterName='other'
        else:
            parameterName=name
        parameterDisplayName=getDisplayName(parameterName)
        results.append({
            "name": name,
            "parameterDisplayName":parameterDisplayName,
            "parameterName":parameterName,
            "attribute": attribute,
            "value": {
                "start": start,
                "end": end,
                "step": step
            }
        })

    for match in non_range_pattern.finditer(text):
        name = match.group(1).strip("'")
        attribute = match.group(2).strip("'")
        values_str = match.group(3).strip()
        values = [v.strip("'") for v in values_str.split(',')]
        
        if attribute=="":
            parameterName='other'
        else:
            parameterName=name
        parameterDisplayName=getDisplayName(parameterName)
        if name == 'placer':
            results.append({
                "name": name,
                "parameterDisplayName":parameterDisplayName,
                "parameterName":parameterName,
                "attribute": attribute,
                "value": values  
            })
        else:
            results.append({
                "name": name,
                "parameterDisplayName":parameterDisplayName,
                "parameterName":parameterName,
                "attribute": attribute,
                "value": values  
            })
    for match in list_pattern.findall(text):
        name = match[0]
        # Extract attributes (excluding the range values)
        attributes = [attr for attr in match[1:] if attr]   # Filter out empty attributes
        start = convert_value(match[-3])
        end = convert_value(match[-2])
        step = convert_value(match[-1])
        remove_values = set([match[-3], match[-2], match[-1]]) # Convert to a set for faster lookup
        print("remove_values",remove_values)
        attribute = [item for item in attributes if item not in remove_values]
        if len(attribute) ==1:
            attribute=attribute[0]
        parameterName = name
        parameterDisplayName = getDisplayName(parameterName)
        results.append({
            "name": name,
            "parameterDisplayName": parameterDisplayName,
            "parameterName": parameterName,
            "attribute": attribute,  # Correctly store only attributes here
            "value": {
                "start": start,
                "end": end,
                "step": step
            }
        })
    return results
def convert_value(value: str) -> Union[int, float, str]:
    """
    Convert the value to an appropriate type (int, float, or string).
    """
    try:
        # Try to convert to float first (this will catch normal floats and scientific notation)
        converted_value = float(value)
        
        # Check if the value is a whole number (for conversion to int)
        if converted_value.is_integer():
            return int(converted_value)
        else:
            return converted_value  # Return as float if it's not an integer
    except ValueError:
        # If conversion to float fails, return the original string
        return value
# pattern handling as per request block 
def parse_json_from_data(data, pattern_name,projectType):
    patterns = {
    "layer_map": r"layer_map\s*=\s*\{(.*?)\}",
    "min_spacing": r"min_spacing\s*=\s*\{(.*?)\}",
    "layer_width": r"layer_width\s*=\s*\{(.*?)\}",
    "routing_order": r"routing_order\s*=\s*\{(.*?)\}",
    "permutation": r"permutation\s*=\s*\{(.*?)\}",
    "hinder": r"hinder\s*=\s*\{(.*?)\}",
    "weights_horizontal": r"weights_horizontal\s*=\s*\{(.*?)\}",
    "weights_vertical": r"weights_vertical\s*=\s*\{(.*?)\}",
    "via_weights": r"via_weights\s*=\s*\{(.*?)\}",
    "routing_layers": r"routing_layers\s*=\s*\{(.*?)\}",
    "via_size": r"via_size\s*=\s*\{(.*?)\}",
    "minimum_enclosure": r"minimum_enclosure\s*=\s*\{(.*?)\}",
    "layer_properties": r"layer_properties\s*=\s*\{([^}]*)\}",
    "display_names": r"display_names\s*=\s*\{([^}]*)\}"
    }


    pattern = patterns[pattern_name]
    match = re.search(pattern, data, re.DOTALL)
    if not match:
        return {}
    data_str = match.group(1)
    pattern1_list=['layer_map']
    pattern2_list=['layer_width','routing_order','hinder','weights_horizontal','weights_vertical','routing_layers','via_size']
    pattern3_list=['min_spacing','via_weights','minimum_enclosure']
    pattern4_list=['layer_properties','display_names']
    if pattern_name in pattern1_list:
        return pattern1(data_str,projectType)
    elif pattern_name in pattern2_list:
        return pattern2(data_str,pattern_name,projectType)
    elif pattern_name in pattern3_list:
        return pattern3(data_str, pattern_name,projectType)
    elif pattern_name in pattern4_list:
        data_str = '{' + data_str.strip() + '}'
        return pattern4(data, pattern_name,projectType)
    return {}

def convert_string(variable_name):
    # Convert snake_case to Title Case
    return ' '.join([word.capitalize() for word in variable_name.split('_')])

def convert_to_json(input_str,projectType):
    from src.Apps.tech.TechManager.serializer import TechInfoSerializer
    technoinfo=TechInfo.objects.all().order_by('id')
    if technoinfo:
        serializers=TechInfoSerializer(technoinfo,many=True)
        json_data=list()
        project_type=ProjectType.objects.filter(type=projectType).first()
        if project_type.variation==False:
            for element in serializers.data:
                if element['name']=='other':
                    json_data.append({'supportsVariations':element['non_support_variation'],"uiVisible":element['non_support_ui_visible'],"parameterSupport":element['parameter_support_variation'],"name":element['name'],"displayName":element['display_name'], "header":element['header'],'data':extract_other_dict(input_str,element['name'],projectType)})
                elif element['name']=='tech_constaints':
                    json_data.append({'supportsVariations':element['support_variation'],"uiVisible":element['support_ui_visible'],"parameterSupport":element['parameter_support_variation'],"name":element['name'],"displayName":element['display_name'], "header":element['header'],'data':extract_other_dict(input_str,element['name'],projectType)})
                elif element['name']=='configs':
                    json_data.append({'supportsVariations':element['non_support_variation'],"uiVisible":element['non_support_ui_visible'],"parameterSupport":element['parameter_support_variation'],"name":element['name'],"displayName":element['display_name'], "header":element['header'],'data':extract_specific_keys(input_str,projectType)})
                elif element['name']=='permutation':
                    json_data.append({'supportsVariations':element['non_support_variation'],"uiVisible":element['non_support_ui_visible'],"parameterSupport":element['parameter_support_variation'],"name":element['name'],"displayName":element['display_name'], "header":element['header'],'data':[]})
                elif element['name']=='display_names':
                    json_data.append({'supportsVariations':element['support_variation'],"uiVisible":element['support_ui_visible'],"parameterSupport":element['parameter_support_variation'],"name":element['name'],"displayName":element['display_name'], "header":element['header'],'data':[]})
                else:
                    json_data.append({'supportsVariations':element['non_support_variation'],"uiVisible":element['non_support_ui_visible'],"parameterSupport":element['parameter_support_variation'],"name":element['name'],"displayName":element['display_name'], "header":element['header'],'data':parse_json_from_data(input_str,element['name'],projectType)})
        elif project_type.variation==True:
            for element in serializers.data:
                if element['name']=='other':
                    json_data.append({'supportsVariations':element['support_variation'],"uiVisible":element['support_ui_visible'],"parameterSupport":element['parameter_support_variation'],"name":element['name'],"displayName":element['display_name'], "header":element['header'],'data':extract_other_dict(input_str,element['name'],projectType)})
                elif element['name']=='tech_constaints':
                    json_data.append({'supportsVariations':element['support_variation'],"uiVisible":element['support_ui_visible'],"parameterSupport":element['parameter_support_variation'],"name":element['name'],"displayName":element['display_name'], "header":element['header'],'data':extract_other_dict(input_str,element['name'],projectType)})
                elif element['name']=='configs':
                    json_data.append({'supportsVariations':element['support_variation'],"uiVisible":element['support_ui_visible'],"parameterSupport":element['parameter_support_variation'],"name":element['name'],"displayName":element['display_name'], "header":element['header'],'data':extract_specific_keys(input_str,projectType)})
                elif element['name']=='permutation':
                    json_data.append({'supportsVariations':element['support_variation'],"uiVisible":element['support_ui_visible'],"parameterSupport":element['parameter_support_variation'],"name":element['name'],"displayName":element['display_name'], "header":element['header'],'data':extract_permutation(input_str)})
                elif element['name']=='display_names':
                    json_data.append({'supportsVariations':element['support_variation'],"uiVisible":element['support_ui_visible'],"parameterSupport":element['parameter_support_variation'],"name":element['name'],"displayName":element['display_name'], "header":element['header'],'data':[]})
                else:
                    json_data.append({'supportsVariations':element['support_variation'],"uiVisible":element['support_ui_visible'],"parameterSupport":element['parameter_support_variation'],"name":element['name'],"displayName":element['display_name'], "header":element['header'],'data':parse_json_from_data(input_str,element['name'],projectType)})
        else:
            json_data=[]
    else:
        json_data=[]
    if json_data!=[]:
        for element in json_data:
            if element['data']==[] and element['uiVisible']==True and element['name'] not in ['permutation','layer_properties']:
                element['uiVisible']=False
            elif element['data']!=[] and element['uiVisible']==True and element['name'] not in ['permutation','layer_properties']:
                for item in element['data']:
                    if item['uiVisible']==True:
                        element['uiVisible']=True
                        break
                    else:
                        element['uiVisible']=False
            else:
                pass
    return json_data

def convert_nonvariable_json(tech_data,projectType):
    ui_visible={'layer_map':True,'other':False,'min_spacing':True,'layer_width':True,'routing_order':False,'permutation':False,'hinder':False,'configs':False,'weights_horizontal':False,'weights_vertical':False,'via_weights':False,'routing_layers':False,'via_size':False,'minimum_enclosure':False,'layer_properties':False}
    non_support_variation={'layer_map':False,'other':False,'min_spacing':False,'layer_width':False,'routing_order':False,'permutation':False,'hinder':False,'configs':False,'weights_horizontal':False,'weights_vertical':False,'via_weights':False,'routing_layers':False,'via_size':False,'minimum_enclosure':False,'layer_properties':False}
    options={1:["base0","base1"],2:["smt"]}
    for item in tech_data['FileContent']:
        name = item.get('name')  # Get the 'name' field
        if name in non_support_variation:  # Check if the name exists in support_variation
            item['supportsVariations'] = non_support_variation[name]
            for record in item['data']:
                record['isSelected']=False
                if name=='other':
                    if record['key']['key1']=='placer':
                        record['val']=options[projectType][0]
                        record['options']=options[projectType]
        if name in ui_visible:
            item['uiVisible']=ui_visible[name]
    return tech_data

def convert_variable_json(tech_data):
    ui_visible={'layer_map':True,'other':False,'min_spacing':True,'wire_width':True,'routing_order':False,'permutation':True,'hinder':False,'configs':False,'weights_horizontal':False,'weights_vertical':False,'via_weights':False,'routing_layers':False,'via_size':False,'minimum_enclosure':False,'layer_properties':False}
    support_variation={'layer_map':True,'other':True,'min_spacing':True,'wire_width':True,'routing_order':False,'permutation':False,'hinder':False,'configs':False,'weights_horizontal':False,'weights_vertical':False,'via_weights':False,'routing_layers':False,'via_size':False,'minimum_enclosure':False,'layer_properties':False}
    options={"placer":["base0","base1"]}
    for item in tech_data['FileContent']:
        name = item.get('name')  # Get the 'name' field
        if name in support_variation:  # Check if the name exists in support_variation
            item['supportsVariations'] = support_variation[name]
            if name=='other':
                for record in item['data']:
                    if record['key']['key1']=='placer':
                        record['val']='base0'
                        record['options']=options['placer']
        if name in ui_visible:
            item['uiVisible']=ui_visible[name]
    return tech_data

def validate_tech_data(tech_data):
    for entry in tech_data:
        if entry['name'] == 'layer_map':
            layer_data = entry['data']
            val1_set = set()
            seen_combinations = set()
            for item in layer_data:
                val = item['val']
                combination = [val[0], val[1]]
                if not isinstance(combination, list) or len(combination) != 2:
                    status_code=status.HTTP_400_BAD_REQUEST
                    response_status= False
                    message=f'Invalid format for { item['key']['key1']}. Expected a list with two elements.'
                    return message, status_code, response_status,None 
                val1, val2 = combination
                if val1 is None or val1 == "" or val1 == None:
                    status_code=status.HTTP_400_BAD_REQUEST
                    response_status= False
                    message=f'Invalid value for {item['key']['key1']}. It should be a non-null integer.'
                    return message, status_code, response_status,None

                if not isinstance(val1, int):
                    status_code=status.HTTP_400_BAD_REQUEST
                    response_status= False
                    message=f'Invalid value for {item['key']['key1']}. It should be an integer.'
                    return message, status_code, response_status,None
                """if len(combination) < 2:
                    continue  
                val1, val2 = combination[0], combination[1]
                if (val1, val2) in seen_combinations:
                    status_code=status.HTTP_400_BAD_REQUEST
                    response_status= False
                    message=f'Duplicate layer numbers {val1} found in the layer map.'
                    return message, status_code, response_status,None
                seen_combinations.add((val1, val2))
                val1_set.add(val1)"""


        if entry['name'] == 'other':
            other_data = entry['data']
            for item in other_data:
                val = item['val']
                if val in [None, '']:
                        status_code=status.HTTP_400_BAD_REQUEST
                        response_status= False
                        message=f'Invalid or missing value for {item['key']['key1']}'
                        return message, status_code, response_status,None
                """# Check if the key is 'placer' or another field
                if item['key']['key1'] == 'placer':
                    # Placer should be a string
                    if not isinstance(val, str):
                        status_code=status.HTTP_400_BAD_REQUEST
                        response_status= False
                        message=f'Invalid value for {item['key']['key1']}. Expected string.'
                        return message, status_code, response_status,None

                else:
                    # All other fields should be integers
                    if not (isinstance(val, int) or isinstance(val, float)):
                        status_code=status.HTTP_400_BAD_REQUEST
                        response_status= False
                        message=f'Invalid value for {item['key']['key1']}. Expected integer.'
                        return message, status_code, response_status,None
                    # Also check if the value is empty or None
                    if val in [None, '']:
                        status_code=status.HTTP_400_BAD_REQUEST
                        response_status= False
                        message=f'Invalid or missing value for {item['key']['key1']}'
                        return message, status_code, response_status,None
"""
        if entry['name'] == 'min_spacing':
            minspacing_data=entry['data']
            for item in minspacing_data:
                val = item['val']
                    # Check if 'Val' is present and not None, empty, or "null"
                if val in [None, "", "null"]:
                    status_code=status.HTTP_400_BAD_REQUEST
                    response_status= False
                    message="Empty/NULL value found in the min spacing tab."
                    return message, status_code, response_status,None


                # Check if 'val' is numeric
                try:
                    # Convert to float to handle numeric values like "6.5"
                    if not (isinstance(val, int) or isinstance(val, float)):
                            status_code=status.HTTP_400_BAD_REQUEST
                            response_status= False
                            item_key = item.get("key", {})
                            message=f'Invalid value for ({item_key.get('key1')},{item_key.get('key2')}). Expected integer or float.'
                            return message, status_code, response_status,None

                except ValueError:
                    status_code=status.HTTP_400_BAD_REQUEST
                    response_status= False
                    message="Non-numeric value found in the min spacing tab."
                    return message, status_code, response_status,None


        if entry['name']=='layer_width':
            wirewidth_data=entry['data']
            for item in wirewidth_data:
            # Check if 'value' is None, an empty string, or "null"
                if item['val'] in [None, "", "null"]:
                    status_code=status.HTTP_400_BAD_REQUEST
                    response_status= False
                    message= "Empty/NULL value found in the layer data."
                    return message, status_code, response_status,None

                # Check if 'value' is an intege
                if not isinstance(item['val'], (int, float)) or isinstance(item['val'], bool):  # Exclude boolean values
                    status_code=status.HTTP_400_BAD_REQUEST
                    response_status= False
                    message= "Non-numeric value found in the layer data."
                    return message, status_code, response_status,None
    message="Valid Tech File."
    response_status=True
    status_code=status.HTTP_200_OK
    return message , status_code , response_status , None