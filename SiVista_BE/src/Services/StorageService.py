"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: StorageService.py  
 * Description: Storage service to handle files.
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
import json
from django.conf import settings
from SiVista_BE.settings import *
from django.http import FileResponse
from src.Models.FileStorage.FileData import FileData
from time import time
from boto3 import client as botoClient, Session
from base64 import b64encode
from io import StringIO, BytesIO
from rest_framework import status
import pandas as pd
from botocore.exceptions import NoCredentialsError, ClientError

# AWS S3 boto3 client to be used in all the functions below 
s3_client = botoClient(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME
)

def getFile(filePath: str):
    '''
    A function that accepts a file path and returns the file at that location in the S3 bucket.
    Returns file as a FileResponse object.
    '''
    try:
        s3_object = s3_client.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=filePath)
        file_stream = s3_object['Body']
        response = FileResponse(file_stream)
        response['Content-Disposition'] = f'attachment; filename="{filePath.split("/")[-1]}"'
        return {
            'success': True,
            'response': response
        }
    except s3_client.exceptions.NoSuchKey:
        return {
            'success': False,
            'error': 'Invalid path'
        }

def storeFile(fileData: FileData, filePath: str):
    '''
    Accepts data in the form of a FileData object and a path and creates a file with that data at the specified location in the S3 bucket.
    '''
    validation = fileData.validate()
    if not validation['passed']:
        return {
            'success': False,
            'error': validation['errors']
        }
    timeTaken = 0
    try:
        start_time = time()
        s3_client.upload_fileobj(
            Fileobj=fileData.fileObj,
            Bucket=AWS_STORAGE_BUCKET_NAME,
            Key=filePath
        )
        end_time = time()
        timeTaken = end_time - start_time
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    file_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{filePath}"
    return {
        'success': True,
        'fileUrl': file_url,
        'timeTaken': timeTaken
    }
def delete_file_from_s3(file_name):
    #Delete a specific file from an S3 bucket.
    try:
        # Delete the file
        s3_client.delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=file_name)
        return True
    except ClientError as e:
        print(f'Error deleting file: {e}')
        return False

def readFileResponseContent(file_response: FileResponse):
    '''
    Input: A file as a FileResponse object.
    Output: Contents of the file as a string
    '''
    file_content = b''.join(file_response.streaming_content)
    return file_content

def writeFile(filePath: str, fileData: str, type: int):
    '''
    Input: file path in the S3 bucket and file data as a string.
    Action: Writes file data into the file.
    type 1 writes the data as is, type 2 writes the data as a json.
    '''
    try:
        if type == 1:
            s3_client.put_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=filePath, Body=fileData)
            return True
        elif type == 2:
            s3_client.put_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=filePath, Body=fileData, ContentType='application/json')
            return True 
        else:
            return False     
    except Exception as e:
        print(e)
        return False

def getList(name,filepath):
    session = Session(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    s3 = session.resource('s3')
    my_bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
    myList=[]
    for my_bucket_object in my_bucket.objects.filter(Prefix=filepath).all():
           element={'FileName':((my_bucket_object.key).split('/')[-1]), 'FileType':name, 'TimeStamp':my_bucket_object.last_modified}
           if element['FileName']!='':
                myList.append(element)
    return myList


def copy_files_in_s3(location1: str, location2: str, file_names: list):
    '''
    Copies files specified in file_names from location1 to location2 in the S3 bucket.
    '''
    moved_files = 0
    for file_name in file_names:
        copy_source = {
            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
            'Key': f'{location1}{file_name}'
        }
        destination_key = f'{location2}{file_name}'
        try:
            s3_client.copy_object(CopySource=copy_source, Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=destination_key)
            moved_files += 1
        except Exception as e:
            return {
                'message': str(e),
                'success': False,
                'moved': moved_files
            }
    assert moved_files == len(file_names), 'Not all files have been moved.'
    return {'success': True, 'moved': moved_files}

def delete_all_from_path(folder_path: str):
    '''
    Deletes all files in a folder in the S3 bucket.
    '''
    if not folder_path.endswith('/'):
        folder_path += '/'
    delete_keys = []
    continuation_token = None
    list_kwargs = {
            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
            'Prefix': folder_path
        }
    while True:
        if continuation_token:
            list_kwargs['ContinuationToken'] = continuation_token
        response = s3_client.list_objects_v2(**list_kwargs)
        if response['KeyCount']==0:
            return True
        if 'Contents' in response:
            for obj in response['Contents']:
                delete_keys.append({'Key': obj['Key']})
        if response.get('IsTruncated'):
            continuation_token = response.get('NextContinuationToken')
        else:
            break
    for i in range(0, len(delete_keys), 1000):
        try:
            response = s3_client.delete_objects(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Delete={'Objects': delete_keys[i:i+1000]}
            )
        except Exception as e:
            return {'success': False, 'error': str(e)}
    return True

def move_folder_in_s3(source_folder: str, destination_folder: str, delete_source: bool=False):
    '''
    Makes a copy of folder at path source_folder at path destination_folder
    delete_source can specifies whether or not to delete the source folder
    '''
    response = s3_client.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Prefix=source_folder)
    # Check if there are any objects to copy
    if 'Contents' not in response:
        return False
    for obj in response['Contents']:
        source_key = obj['Key']
        # Construct the destination key by replacing the source_folder prefix with destination_folder
        destination_key = os.path.join(destination_folder, os.path.relpath(source_key, source_folder))
        # Copy the object
        copy_source = {'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': source_key}
        s3_client.copy_object(CopySource=copy_source, Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=destination_key)
    return True

def getdata(filepath, filetype, type ):
    try:
        if (type=='Tech'):
            if (filetype=='GLOBAL'):
                session = Session(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
                s3 = session.resource('s3')
                bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
                for obj in bucket.objects.filter(Prefix=filepath):
                    body = obj.get()['Body'].read()
                filecontent=b64encode(body).decode('utf-8')
                message="Success"
                response_status=True
                status_code=status.HTTP_200_OK
                return message,filecontent, status_code, response_status
            elif (filetype=='USER'):
                response = s3_client.get_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=filepath)                
                json_content = response['Body'].read().decode('utf-8')
                data = json.loads(json_content)
                message="Success"
                response_status=True
                status_code=status.HTTP_200_OK
                return message,data, status_code, response_status
        elif(type=='Netlist'):
            session = Session(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
            s3 = session.resource('s3')
            bucket = s3.Bucket(AWS_STORAGE_BUCKET_NAME)
            for obj in bucket.objects.filter(Prefix=filepath):
                body = obj.get()['Body'].read()
            filecontent=b64encode(body).decode('utf-8')
            if filecontent:
                message="Success"
                response_status=True
                status_code=status.HTTP_200_OK
                return message,filecontent, status_code, response_status
            else:
                message="The file is empty. Please provide a valid file."
                response_status=False
                status_code=status.HTTP_404_NOT_FOUND
                return message,None, status_code, response_status
    except Exception as e:
        print(e)
        message="No such File available."
        status_code=status.HTTP_204_NO_CONTENT
        response_status=False
        return message,None,status_code,response_status

def list_folders(base_path):
    paginator = s3_client.get_paginator('list_objects_v2')
    # Use a set to store unique folder names
    folders = set()
    # Paginate through the objects
    for page in paginator.paginate(Bucket=AWS_STORAGE_BUCKET_NAME, Prefix=base_path, Delimiter='/'):
        # Iterate over common prefixes to get folder names
        for common_prefix in page.get('CommonPrefixes', []):
            folder = common_prefix['Prefix']
            # Extract the folder name relative to base_path
            folder_name = folder[len(base_path):].strip('/')
            if folder_name:  # Avoid empty folder names
                folders.add(folder_name.split('/')[0])
    return list(folders)

def list_files_with_extension(folder_paths, extension):
    paginator = s3_client.get_paginator('list_objects_v2')
    files = []
    # Loop through each folder_path
    for path in folder_paths:
        path = path if path[-1] == '/' else path + '/' 
        # Paginate through objects with the given prefix and check for files with the given extension
        for page in paginator.paginate(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Prefix=path, Delimiter='/'):
            for obj in page.get('Contents', []):
                key = obj['Key']
                if key.lower().endswith(extension):
                    files.append(key)
    return files

def get_image(keypath):
    
    bucket_name = AWS_STORAGE_BUCKET_NAME
    
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=keypath)
        # Return a file-like object (BytesIO)
        return BytesIO(response['Body'].read())
    except NoCredentialsError:
        raise ValueError("AWS credentials not found")
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise FileNotFoundError("Image not found in S3")
        else:
            raise e

def combine_csv_files(base_path,cells,path_extension):
    """Combine CSV files from the specified folders into a single DataFrame."""
    all_dataframes = []
    for cell in cells:
        # Construct the S3 path for CSV files in the cell folder.
        prefix = f'{base_path}{cell}/{cell}{path_extension}'
        # List objects in the folder
        paginator = s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=AWS_STORAGE_BUCKET_NAME, Prefix=prefix):
            for obj in page.get('Contents', []):
                key = obj['Key']
                if key.endswith('.csv'):
                    df = fetch_csv(key)
                    if not df.empty:
                        all_dataframes.append(df)
    # Combine all DataFrames
    if all_dataframes:
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        return combined_df
    else:
        print("No CSV files found.")
        return pd.DataFrame()

def fetch_csv(key):
    """Fetch CSV data from S3 and return it as a DataFrame."""
    try:
        response = s3_client.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key)
        csv_content = response['Body'].read().decode('utf-8')
        return pd.read_csv(StringIO(csv_content)).round(4)
    except Exception as e:
        print(f"Error fetching {key}: {e}")
        return pd.DataFrame()