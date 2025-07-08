"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: tasks.py  
 * Description:  This code defines a background task for processing jobs, handles pre- and post-run notifications, and sends updates via WebSocket. The process_job function performs different actions based on job data, like running layout or hyperexpressivity tasks. It also sends job status updates and summaries via WebSocket. The task_prerun, task_postrun, and task_failure signals are used to notify when the job starts, finishes, or fails, respectively.
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
from celery import shared_task
from celery.signals import task_failure, task_postrun, task_prerun
from src.Services.GRPCService import run_layout, run_hyperexpressivity
from src.Services.JobService import update_job_status, save_job_results
from src.Services.ProjectService import getAction
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from json import dumps
from re import search


@shared_task
def process_job(job_id, job_data):
    print(f'RUNNING JOB {job_id}')
    update_job_status(job_id, 'RUNNING')
    summary_messages = []
    result = []
    hyperexpressivity_pattern = r"(\w+): Number of DRC clean permutations generated: (\d+)\s+Number of LVS clean permutations: (\d+)"
    layout_pattern = r"(\w+): (\d+) Layout files generated. \(DRC fails: (\d+), LVS fails: (\d+)\)"
    try:
        if job_data['action'] == getAction.Layout.value:
            sivista_response = run_layout(job_data['cells'], job_data['projectId'], job_data['project_user_id'], job_data['netlistData'], dumps(job_data['techData']), job_id, True, job_data['project_type'], job_data['is_double_height'], job_data['project_name'], job_data['elastic_log_level'])
        elif job_data['action'] == getAction.Hyperexpresivity.value:
            sivista_response = run_hyperexpressivity(job_data['cells'], job_data['projectId'], job_data['project_user_id'], job_data['netlistData'], dumps(job_data['techData']), job_data.get('stage1Project', None), job_data.get('selectedLayouts', {}), job_id, job_data['is_double_height'])
        for response in sivista_response:
            # Update job status or stream message to WebSocket
            if 'Number of DRC clean permutations generated:' in response['message'] or 'Layout files generated.' in response['message']:
                summary_messages.append(response['message'])
            send_to_websocket(job_id, response['status'], response['message'])
        if not summary_messages:
            return
        send_to_websocket(job_id, '200', '##############################################################################################')
        send_to_websocket(job_id, '200', '####################################### RUN SUMMARY ##########################################')
        for message in summary_messages:
            if job_data['action'] == getAction.Layout.value:
                match = search(layout_pattern, message)
                if match:
                    cell_name = match.group(1)
                    layout_count = int(match.group(2))
                    drc_count = int(match.group(3))
                    lvs_count = int(match.group(4))
                    result.append({'layouts_generated': layout_count, 'DRC_fails': drc_count, 'LVS_fails': lvs_count})
                    message = f'{cell_name}: We generated {layout_count} layouts from your selections. In the process we had {drc_count} DRC failures and {lvs_count} LVS failures.'
            elif job_data['action'] == getAction.Hyperexpresivity.value:
                match = search(hyperexpressivity_pattern, message)
                if match:
                    drc_count = int(match.group(2))
                    lvs_count = int(match.group(3))
                    cell_name = match.group(1)
                    result.append({'DRC_passes': drc_count, 'LVS_passes': lvs_count})
                    message = f'{cell_name}: We generated {drc_count} DRC clean layout permutations, of which {lvs_count} passed our LVS check'
            send_to_websocket(job_id, '200', message)
            print(message)
        send_to_websocket(job_id, '200', '##################################### END OF SUMMARY #########################################')
        send_to_websocket(job_id, '200', '##############################################################################################')
        save_job_results(job_id, result)
    except Exception as e:
        print(f"Error: {str(e)}")
        send_to_websocket(job_id, '400', f"Error: {str(e)}")
        update_job_status(job_id, 'FAILED')
        # Send a special message indicating the job is complete and close WebSocket
        send_to_websocket(job_id, '400', "__close__")
        raise

@task_prerun.connect(sender=process_job)
def task_prerun_notifier(sender=None, task_id=None, task=None, **kwargs):
    job_id = task.request.args[0]
    print(f'Job {job_id} is going to start execution.')
    # TODO: We can get the job's process ID in this function and set it in the JOB table. This can be later used for SS-

@task_postrun.connect(sender=process_job)
def task_postrun_notifier(sender=None, task_id=None, task=None, **kwargs):
    job_id = task.request.args[0]
    print(f'Job {job_id} has finished execution.')
    send_to_websocket(job_id, '200', "__close__")

@task_failure.connect(sender=process_job)
def task_failure_notifier(task_id=None, exception=None, args=None, **kwargs):
    update_job_status(args[0], 'FAILED')
    print(f'Job {args[0]} failed with error: {str(exception)}')
    send_to_websocket(args[0], '400', f"Error: {str(exception)}")
    send_to_websocket(args[0], '200', "__close__")

def send_to_websocket(job_id, status, message):
    """
    Sends the message to the WebSocket group for the given job ID.
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'job_{job_id}',  # WebSocket group name
        {
            'type': 'job_message',
            'status': status,
            'message': message
        }
    )
