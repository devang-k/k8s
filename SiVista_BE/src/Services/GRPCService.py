"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: GRPCService.py  
 * Description: Model for response format
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
import grpc
import src.Apps.project.MLRunner.grpc.protobuf_stream_pb2 as protobuf_stream_pb2
import src.Apps.project.MLRunner.grpc.protobuf_stream_pb2_grpc as protobuf_stream_pb2_grpc
from src.Services.NetlistService import extract_subckt
from src.Services.StorageServices.StorageService import storage_servicer
from src.Services.JobService import update_job_status
from SiVista_BE.settings import GRPC_CHANNEL, S3_BUCKET_ROOT
from src.Models.User.UserResponse import UserResponse
from base64 import b64decode
from google.protobuf import struct_pb2

def get_grpc_version():
    with grpc.insecure_channel(GRPC_CHANNEL) as channel:
        stub = protobuf_stream_pb2_grpc.SiVistaLayoutStub(channel)
        try:
            return stub.GetVersion(protobuf_stream_pb2.Empty())
        except Exception as e:
            print('GRPC server is not connected:',e)
            return UserResponse('GRPC disconnected', '400', False)

def run_layout(cells, project_id, user_id, netlist_data, tech_data={}, job_id='0', stage1=True, project_type='0', is_double_height=False, project_name='', elastic_log_level=99, log_level=5):
    with grpc.insecure_channel(GRPC_CHANNEL) as channel:
        stub =  protobuf_stream_pb2_grpc.SiVistaLayoutStub(channel)
        job_failed = False
        message_count = 0
        try:
            for cell_name in cells:
                responses = stub.LayoutGen(protobuf_stream_pb2.LayoutGenRequest(
                    netlist_data=netlist_data,
                    job_id=str(job_id),
                    cell=cell_name,
                    s3_prefix=f'{S3_BUCKET_ROOT}/Project/{user_id}/{project_id}/',
                    tech_json=str(tech_data),
                    params={
                        'run_layout_only': struct_pb2.Value(bool_value=stage1),
                        'type': struct_pb2.Value(string_value=str(project_type)),
                        'multi_height': struct_pb2.Value(bool_value=is_double_height),
                        'project_id': struct_pb2.Value(number_value=int(project_id)),
                        'user_id': struct_pb2.Value(number_value=int(user_id)),
                        'project_name': struct_pb2.Value(string_value=str(project_name)),
                        'elastic_log_level': struct_pb2.Value(number_value=int(elastic_log_level)),
                        'log_level': struct_pb2.Value(number_value=int(log_level))
                    }
                ))
                for response in responses:
                    if not job_failed and response.status == '400':
                        job_failed = True
                    message_count += 1
                    yield {
                        "status": response.status,
                        "message": response.message
                    }
        except grpc.RpcError as e:
            print(f"gRPC Error: {e.code()}, {e.details()}")
        finally:
            new_status = 'COMPLETED' if not job_failed else 'FAILED' # message count = 9
            update_job_status(job_id, new_status)

def run_hyperexpressivity(cells, project_id, user_id, netlist_data='', tech_data={}, stage1_project=None, selected_layouts=[], job_id='0', is_double_height=False):
    with grpc.insecure_channel(GRPC_CHANNEL) as channel:
        stub =  protobuf_stream_pb2_grpc.SiVistaLayoutStub(channel)
        selected_layouts = preprocess_selected_layouts(cells, selected_layouts)
        job_failed = False
        message_count = 0
        try:
            for cell_name in cells:
                gds_folder_path = f'{cell_name}/{cell_name}_layouts'
                layouts = selected_layouts.get(cell_name, [])
                if layouts:
                    result = create_selected_layouts_folder(project_id, user_id, cell_name, stage1_project, layouts)
                    if result:
                        gds_folder_path = f'{cell_name}/{cell_name}_selected'
                responses = stub.Hyperexpressivity(protobuf_stream_pb2.HyperexpressivityRequest(
                    gds_folder_path=gds_folder_path,
                    job_id=str(job_id),
                    cell=cell_name, 
                    s3_prefix=f'{S3_BUCKET_ROOT}/Project/{user_id}/{project_id}/',
                    tech_json=str(tech_data),
                    netlist_data=netlist_data,
                    params={
                        'multi_height': struct_pb2.Value(bool_value=is_double_height)
                    }
                ))
                for response in responses:
                    if not job_failed and response.status == '400':
                        job_failed = True
                    message_count += 1
                    yield {
                        "status": response.status,
                        "message": response.message
                    }
        finally:
            new_status = 'COMPLETED' if not job_failed else 'FAILED' # message_count = 8
            update_job_status(job_id, new_status)

def create_selected_layouts_folder(project_id, user_id, cell, stage1_project, selected_layouts):
    stage1_project = stage1_project or project_id
    source = f'{S3_BUCKET_ROOT}/Project/{user_id}/{stage1_project}/Stage1/{cell}/{cell}_layouts/'
    destination = f'{S3_BUCKET_ROOT}/Project/{user_id}/{project_id}/Stage1/{cell}/{cell}_selected/'
    storage_servicer.delete_folder(destination)
    layermaps = {f'layerMap{layout.split('.')[0]}.json' for layout in selected_layouts}
    selected_layouts.extend(list(layermaps))
    selected_layouts.append('summary.csv')
    response = storage_servicer.copy_files(source, destination, selected_layouts)
    return response['success']

def preprocess_selected_layouts(cells, selected_layouts):
    return {cell: [layout for layout in selected_layouts if layout.startswith(cell)] for cell in cells}

def check_input_validity(cells, netlist_data, tech_data):
    if not isinstance(cells, list) or not len(cells):
        return False, '\'cells\' should be a non-empty list.'
    if not all(isinstance(cell, str) for cell in cells):
        return False, '\'cells\' should be a list of strings.'
    if not isinstance(netlist_data, str) or not len(netlist_data):
        return False, '\'netlistData\' should be a non-empty string.'
    try:
        b64decode(netlist_data, validate=True)
    except:
        return False, '\'netlistData\' should be a base64 encoded string.'
    netlist_cells = extract_subckt(b64decode(netlist_data).decode('utf-8'))
    if set(cells) - set(netlist_cells):
        return False, f'The following cells are not defined in the netlist: {list(set(cells) - set(netlist_cells))}.'
    if not isinstance(tech_data, dict) or not tech_data.get('FileContent', None):
        return False, '\'techData\' must be an object with the key \'FileContent\'.'
    if not isinstance(tech_data['FileContent'], list) or not len(tech_data['FileContent']):
        return False, 'The value of \'FileContent\' in \'techData\' must be a non-empty array of objects.'
    if sum([True if isinstance(element, dict) else False for element in tech_data['FileContent']]) != len(tech_data['FileContent']):
        return False, '\'FileContent\' in \'techData\' is not in a valid JSON format.'
    return True, None

def gds_file_check(selected_cells):
    for cell in selected_cells:
        if not cell.endswith('.gds'):
            return False
    return True

def update_project_tech(tech_dic, project_type):
    tech = tech_dic['FileContent']
    placerfound=0
    scaling_factor_flag = False
    design_rules_data=list()
    for obj in tech:
        if obj['name']=='other':
            obj['uiVisible']=True
            for element in obj['data']:
                if element['key']['key1']=='placer':
                    if project_type==0:
                        element['isSelected']=True
                    elif project_type == 2:
                        assert element['val'] == 'smt', 'This POC only supports the SMT placer.'
            design_rules_parameters_other = ['placer','height_req']
            for element in obj['data'][:]:
                if element['key']['key1'] in design_rules_parameters_other:
                    design_rules_data.append(element)
                    obj['data'].remove(element)
        elif obj['name'] == 'permutation':
            for element in obj['data']:
                if element['name']=='placer':
                    placerfound+=1
            if placerfound==0 and project_type==0:
                obj['data'].append({
                    "name": "placer",
                    "displayName": "Placer",
                    "parameterName": "other",
                    "attribute": "",
                    "value": ["base0", "base1"],
                    "defaultValue": ["base0"],
                    "options": ["base0", "base1"]
                })            
        elif obj['name'] == 'tech_constaints':
            design_rules_parameters_tech = ['number_of_routing_tracks', 'height_req']
            for element in obj['data'][:]:
                if element['key']['key1'] == 'backside_power_rail':
                    if element['val'] == 'Backside power':
                        element['val'] = True
                    elif element['val'] == 'Frontside power':
                        element['val'] = False
                    element['type'] = 5
                elif element['key']['key1'] == 'height_req':
                    if element['val'] == 'Single Height':
                        element['val'] = 1
                    elif element['val'] == 'Double Height':
                        element['val'] = 2
                        scaling_factor_flag=True
                    element['type'] = 1
                if element['key']['key1'] in design_rules_parameters_tech:
                    design_rules_data.append(element)
                    obj['data'].remove(element)    
        elif obj['name'] == 'configs':
            for element in obj['data'][:]:
                if element['key']['key1'] == 'scaling_factor':
                    if scaling_factor_flag:
                        element['val'] = 8
                    else:
                        element['val'] = 4
        elif obj['name'] == 'min_spacing':
            design_rules_parameters_min = ['inner_space_width','via_extension','gate_extension','interconnect_extension','np_spacing','vertical_gate_spacing','vertical_interconnect_spacing','pg_signal_spacing']
            for element in obj['data'][:]:
                if element['keyDisplayName']['displayNameKey1'] == 'Diffusion to Diff interconnect spacing':
                    element['keyDisplayName']['displayNameKey2'] = element['keyDisplayName']['displayNameKey1']
                if element['key']['key1'] in design_rules_parameters_min:
                    design_rules_data.append(element)
                    obj['data'].remove(element)
        elif obj['name'] == 'layer_width':
            design_rules_parameters_width = ['power_rail_width','nanosheet_width','m0_pitch','vertical_metal_pitch']
            for element in obj['data'][:]:
                if element['key']['key1'] in design_rules_parameters_width:
                    design_rules_data.append(element)
                    obj['data'].remove(element)
    for obj in tech:
        if obj['name'] == 'other':
            obj['data']=design_rules_data
        elif obj['name'] == 'permutation':
            design_rules_parameters_permutation = {"Number of routing tracks":'number_of_routing_tracks','Power rail width':'power_rail_width','Diffusion width':'nanosheet_width','Metal0 routing pitch':'m0_pitch','Metal1 routing pitch':'vertical_metal_pitch','Poly to Diffcon spacing':'inner_space_width','Via extension':'via_extension','Gate extension':'gate_extension','Diffcon extension':'interconnect_extension','N/P Diffusion spacing':'np_spacing','Gate Cut spacing':'vertical_gate_spacing','Diffcon ETE spacing':'vertical_interconnect_spacing','PG rails to Signal spacing':'pg_signal_spacing'}
            for element in obj['data'][:]:
                if element['displayName'] in design_rules_parameters_permutation:
                    element['name']=design_rules_parameters_permutation[element['displayName']]
                    element['attribute']=""
                    element['parameterDisplayName']="Design Rules"
                    element['parameterName']="other"
                elif element['displayName']=='Diffusion to Diff interconnect spacing':
                    display_name=element['displayName']
                    element['displayName']=[display_name,display_name]
                else:
                    pass
    updated_tech={'FileContent': tech}
    return updated_tech, scaling_factor_flag