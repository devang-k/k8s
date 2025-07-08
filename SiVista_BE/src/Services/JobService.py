"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: JobService.py  
 * Description: Service to manage jobs
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
from django.utils.timezone import now
from json import dumps
from src.Apps.project.ProjectManager.models import Job, TechFileCatalog
from src.Services.StorageServices.StorageService import storage_servicer
from SiVista_BE.settings import S3_BUCKET_ROOT
from pandas import merge, concat
from numpy import arange

def create_job(project, input_data, created_by_id):
    job = Job.objects.create(  # TODO: Add process ID here once that is ready
        project=project,
        status='QUEUED',
        command=f'-c {input_data['cells']}',
        action=str(input_data['action']),
        cells=input_data['cells'],
        created_by_id=created_by_id,
        input=input_data,
        output=f'Project/{project.created_by_id}/{project.id}/Stage{input_data['action']}'
    )
    return job

def save_tech_catalog_data(project, data, job, techCatalogData ,file_name,jobStatus, request):
    try:
        tech_catalog = TechFileCatalog.objects.create(
            project=project,
            action=int(data['action']),
            job_id=job,
            cell_name=data['cells'],
            file_name=file_name,
            tech_data=techCatalogData,
            drc_count=0,
            lvs_count=0,
            status=jobStatus,
            created_by_id=request.user_id
            )
        print("Tech catalog saved successfully")
        return tech_catalog
    except Exception as e:
        print(f"Error saving tech catalog: {e}")

def update_job_status(id, status):
    job = Job.objects.filter(pk=id).first()
    if job:
        job.status = status
        job.save()
        TechFileCatalog.objects.filter(job_id=str(job.id)).update(status=status)
        
def generate_key(key_head, stage,input_string):
    return f"{key_head}_{stage}_{input_string}"

def save_job_results(id, result):
    job = Job.objects.filter(pk=id).first()
    if not job:
        return
    if job.project.project_type != 0:
        return
    consolidated_result = {}

    drc_passes = result[0].get('DRC_passes') or result[0].get('DRC_fails') or 0
    lvs_passes = result[0].get('LVS_passes') or result[0].get('LVS_fails') or 0

    update_drc_lvs_count = TechFileCatalog.objects.filter(job_id=str(job.id)).update(
            drc_count=drc_passes,
            lvs_count=lvs_passes
        )
    status_list = ['COMPLETED','RUNNING','QUEUED', 'UNPROCESSED', 'DELETED']
    TechFileCatalog.objects.exclude(status__in = status_list).delete()
    for d in result:
        for key, value in d.items():
            consolidated_result[key] = consolidated_result.get(key, 0) + value
    file_path = f'{S3_BUCKET_ROOT}/{job.output}/Run_Summary.json'
    time_diff = now() - job.created_date
    minutes, seconds = divmod(time_diff.total_seconds(), 60)
    file_data = {
        'cells': {
            'displayHeaderName': 'Cells',
            'displayType': 1,
            'value': job.cells
        },
        'runTime': {
            'displayType': 1,
            'displayHeaderName': 'Run time',
            'value': f'{int(minutes)} minutes, {int(seconds)} seconds'
        }
    }
    for k, v in consolidated_result.items():
        file_data[k] = {
            'displayHeaderName': k.replace("_", " ").capitalize(),
            'displayType': 1,
            'value': v
        }
    if job.action == 1:
        tech_val, variation_val, layermap_val = format_tech(job.input['techData'])
        file_data['techParameters'] = {
            'displayType': 2,
            'displayHeaderName': 'Tech file parameters',
            'parameterTableHeader': ['Parameter1', 'Parameter2', 'Value'],
            'value': tech_val
        }
        file_data['variationTechParameters'] = {
            'displayType': 2,
            'displayHeaderName': 'Tech file variations',
            'parameterTableHeader': ['Parameter1', 'Parameter2', 'Default', 'Start', 'End', 'Step', 'Values'],
            'value': variation_val
        }
        file_data['layermap'] = {
            'displayType': 2,
            'displayHeaderName': 'Layer map values',
            'parameterTableHeader': ['LayerName', 'LayerNumber', 'DataType'],
            'value': layermap_val
        }
    storage_servicer.write_file(file_path, dumps(file_data).encode('utf-8'), 2)
    text_file_string = f"Run Summary\n\n"
    for key, value in file_data.items():
        text_file_string += f"{value['displayHeaderName']}: {value['value']}\n"
    storage_servicer.write_file(f'{S3_BUCKET_ROOT}/{job.output}/Run_Summary.txt', text_file_string, 1)
    create_consolidated_csv(f'{S3_BUCKET_ROOT}/{job.output}', job.cells, job.action)

def format_tech(data):
    techList = []
    variationList = []
    layermapList = []
    for element in data["FileContent"]:
        if element['uiVisible'] == True and element['name'] == "layer_map":
            for record in element['data']:
                if record["isSelected"] == False:
                    myJson = {}
                    myJson["LayerName"] = record['keyDisplayName']['displayNameKey1']
                    myJson["LayerNumber"] = record['val'][0]
                    myJson["DataType"] = record['val'][1]
                    layermapList.append(myJson)
        elif element['uiVisible'] == True and element['name'] != "permutation":
            for record in element['data']:
                if record["isSelected"] == False:
                    myJson = {}
                    myJson['Parameter1'] = record['keyDisplayName'].get('displayNameKey1', None)
                    myJson['Parameter2'] = record['keyDisplayName'].get('displayNameKey2', None)
                    myJson["unit"] = record.get('unit', None)
                    myJson["Value"] = record.get('val', None)
                    techList.append(myJson)
        elif element['name'] == "permutation":
            for record in element['data']:
                if record['name'] == 'placer':
                    continue
                myJson = {}
                myJson['Parameter1'] = record['displayName']
                myJson['Parameter2'] = None if not record['attribute'] else record['attribute']
                myJson['Default'] = record['defaultValue'][0] if (record['defaultValue'] and type(record['defaultValue']) == list) else record['defaultValue']
                myJson['Start'] = record['value']['start'] if type(record['value']) == dict else None
                myJson['End'] = record['value']['end'] if type(record['value']) == dict else None
                myJson['Step'] = record['value']['step'] if type(record['value']) == dict else None
                myJson['Values'] = arange(record['value']['start'], record['value']['end'] + 0.000001, record['value']['step']).tolist() if myJson['Start'] is not None else record['value']
                variationList.append(myJson)
    return techList, variationList, layermapList

def create_consolidated_csv(output_base_path, cells, action):
    consolidated_df = []
    for cell in cells:
        summary_path = f'{output_base_path}/{cell}/{cell}_layouts/summary.csv' if action == 1 else f'{output_base_path}/{cell}/{cell}_permutations/summary.csv'
        summary_df = storage_servicer.fetch_csv(summary_path)
        pex_df = storage_servicer.fetch_csv(f'{output_base_path}/{cell}/{cell}_predictions/{cell}_GDS_PEX_PREDICTION_ML.csv')
        print(pex_df.columns)
        print(summary_df.columns)
        if action == 1:
            combined_df = merge(summary_df, pex_df, right_on='File', left_on='File name', how='left')
        elif action == 2:
            combined_df = merge(summary_df, pex_df, right_on='File', left_on='permutationLayout', how='left')
        consolidated_df.append(combined_df)
    consolidated_df = concat(consolidated_df)
    
    cols_to_move = ['Capacitance Sum', 'F2F Total Length', 'Total Area (um^2)', 'Total Length (um)', 'Cell Area (um^2)']
    cols = list(consolidated_df.columns)
    new_order = [col for col in cols if col not in cols_to_move] + [col for col in cols_to_move if col in consolidated_df.columns]
    consolidated_df = consolidated_df[new_order]
    consolidated_df = consolidated_df.drop(columns=['placer','File name'], errors='ignore')
    # Specify the column to move
    column_to_move = "File"
    # Rearrange columns: Move the specified column to the start
    consolidated_df = consolidated_df[[column_to_move] + [col for col in consolidated_df.columns if col != column_to_move]]
    csv_data = consolidated_df.to_csv(index=False)
    storage_servicer.write_file(f'{output_base_path}/Stage_Report{action}.csv', csv_data, 1)
