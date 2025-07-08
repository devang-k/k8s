"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: S3Service.py  
 * Description: S3 aws storage service to provide solutions on stored files
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
from src.Services.StorageServices.BaseService import BaseService
import json
from SiVista_BE.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME, AWS_S3_REGION_NAME
from django.http import FileResponse
from src.Services.EncryptDecryptService import decrypt_file_content, InvalidToken
from src.Models.FileStorage.FileData import FileData
from boto3 import client as botoClient, Session
from base64 import b64encode
from io import StringIO, BytesIO
from rest_framework import status
import pandas as pd
import os
from botocore.exceptions import NoCredentialsError, ClientError
import zipfile
import io
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import ValidationError
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
logger = logging.getLogger(__name__)

class S3Service(BaseService):
    def __init__(self) -> None:
        print('You have chosen AWS S3 as your storage prference.')
        # AWS S3 boto3 client to be used in all the functions below 
        self.s3_client = botoClient(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_S3_REGION_NAME
        )

    def get_file(self, filePath: str):
        '''
        A function that accepts a file path and returns the file at that location in the S3 bucket.
        Returns file as a FileResponse object.
        '''
        try:
            s3_object = self.s3_client.get_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=filePath)
            file_stream = s3_object['Body']
            response = FileResponse(file_stream)
            response['Content-Disposition'] = f'attachment; filename="{filePath.split("/")[-1]}"'
            return {
                'success': True,
                'response': response,
                'status_code': 200,
                'data': None
            }
        except ClientError as e:
            response = e.response
            message = f"ClientError: {response['Error']['Message']}"
            if response['Error']['Message'] == "The specified key does not exist.":
                message = "File not found"
            status_code = response['ResponseMetadata']['HTTPStatusCode']
            success = False
            data = None
            return {
                'success': success,
                'error': message,
                'status_code': status_code,
                'data': data
            }
        except self.s3_client.exceptions.NoSuchKey:
            return {
                'success': False,
                'error': 'Invalid path',
                'status_code': 404,
                'data': None
            }
        except Exception as e:
            print("Error: Failed to get file due to: ", str(e))
            return {
                'success': False,
                'error': "Failed to get file",
                'status_code': 400,
                'data': None
            }

    def store_file(self, fileData: FileData, filePath: str):
        '''
        Accepts data in the form of a FileData object and a path and creates a file with that data at the specified location in the S3 bucket.
        '''
        validation = fileData.validate()
        if not validation['passed']:
            return {
                'success': False,
                'error': validation['errors']
            }
        try:
            self.s3_client.upload_fileobj(
                Fileobj=fileData.fileObj,
                Bucket=AWS_STORAGE_BUCKET_NAME,
                Key=filePath
            )
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
        file_url = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{filePath}"
        return {
            'success': True,
            'fileUrl': file_url
        }

    def delete_file(self, file_path):
        #Delete a specific file from an S3 bucket.
        try:
            # Delete the file
            self.s3_client.delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=file_path)
            return True
        except ClientError as e:
            print(f'Error deleting file: {e}')
            return False

    def write_file(self, filePath: str, fileData: str, type: int):
        '''
        Input: file path in the S3 bucket and file data as a string.
        Action: Writes file data into the file.
        type 1 writes the data as is, type 2 writes the data as a json.
        '''
        try:
            if type == 1:
                self.s3_client.put_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=filePath, Body=fileData)
                return True
            elif type == 2:
                self.s3_client.put_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=filePath, Body=fileData, ContentType='application/json')
                return True 
            else:
                return False     
        except Exception as e:
            print(e)
            return False

    def get_bucket_file_size(self, filePath: str) -> float:
        """
        Fetches the size of the file stored in the S3 bucket.
        
        Inputs:
        - filePath: str : The path of the file in the S3 bucket.
        
        Returns:
        - (float) : File size in bytes.
        """
        try:
            response = self.s3_client.get_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=filePath)
            file_size = response['Body'].read()  # Size in bytes
            return len(file_size) / 1024  # Convert to KB
        except Exception as e:
            print(f"Error fetching file size for {filePath}: {e}")
            return -1

    def get_tech_netlist_list(self, name, filepath):
        session = Session(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        s3 = session.resource('s3')
        my_bucket = s3.Bucket(AWS_STORAGE_BUCKET_NAME)
        myList=[]
        s3obj=my_bucket.objects.filter(Prefix=filepath).all()
        for my_bucket_object in s3obj:
            element={'FileName':((my_bucket_object.key).split('/')[-1]), 'FileType':name, 'TimeStamp':my_bucket_object.last_modified}
            if element['FileName']!='':
                    myList.append(element)
        return myList
    
    def move_folder(self, source_prefix, destination_prefix):
        # List all objects in the source folder
        objects = self.s3_client.list_objects_v2(Bucket=AWS_STORAGE_BUCKET_NAME, Prefix=source_prefix)
    
        # If there are no objects to move, return
        if 'Contents' not in objects:
            message = f"No files found in {source_prefix}."
            return message, False
    
        # List to collect move results
        move_results = []
    
        for obj in objects['Contents']:
            source_key = obj['Key']
            destination_key = destination_prefix + source_key[len(source_prefix):]
            try:
                # Copy the object to the new location
                self.s3_client.copy_object(
                    Bucket=AWS_STORAGE_BUCKET_NAME,
                    CopySource={'Bucket': AWS_STORAGE_BUCKET_NAME, 'Key': source_key},
                    Key=destination_key
                )    
                # Add the successful move to the result list
                move_results.append(f"Successfully copied {source_key} to {destination_key}")
            except Exception as e:
                error_message = f"Error copying {source_key}: {e}"
                print(error_message)
                move_results.append(error_message)
    
        # Return the status of the copy operation
        if all("Successfully" in result for result in move_results):
            return f"All files copied successfully: {', '.join(move_results)}", True
        else:
            return f"Some files failed to copy: {', '.join(move_results)}", False

    def copy_files(self, location1: str, location2: str, file_names: list):
        '''
        Copies files specified in file_names from location1 to location2 in the S3 bucket.
        '''
        moved_files = 0
        for file_name in file_names:
            copy_source = {
                'Bucket': AWS_STORAGE_BUCKET_NAME,
                'Key': f'{location1}{file_name}'
            }
            destination_key = f'{location2}{file_name}'
            try:
                self.s3_client.copy_object(CopySource=copy_source, Bucket=AWS_STORAGE_BUCKET_NAME, Key=destination_key)
                moved_files += 1
            except Exception as e:
                return {
                    'message': str(e),
                    'success': False,
                    'moved': moved_files
                }
        assert moved_files == len(file_names), 'Not all files have been moved.'
        return {'success': True, 'moved': moved_files}

    def delete_folder(self, folder_path: str):
        '''
        Deletes all files in a folder in the S3 bucket.
        '''
        if not folder_path.endswith('/'):
            folder_path += '/'
        delete_keys = []
        continuation_token = None
        list_kwargs = {
                'Bucket': AWS_STORAGE_BUCKET_NAME,
                'Prefix': folder_path
            }
        while True:
            if continuation_token:
                list_kwargs['ContinuationToken'] = continuation_token
            response = self.s3_client.list_objects_v2(**list_kwargs)
            if response['KeyCount']==0:
                return False
            if 'Contents' in response:
                for obj in response['Contents']:
                    delete_keys.append({'Key': obj['Key']})
            if response.get('IsTruncated'):
                continuation_token = response.get('NextContinuationToken')
            else:
                break
        for i in range(0, len(delete_keys), 1000):
            try:
                response = self.s3_client.delete_objects(
                    Bucket=AWS_STORAGE_BUCKET_NAME,
                    Delete={'Objects': delete_keys[i:i+1000]}
                )
            except Exception as e:
                print(e)
                return False
        return True

    def move_folder(self, source_folder: str, destination_folder: str, delete_source: bool=False):
        '''
        Makes a copy of folder at path source_folder at path destination_folder
        delete_source can specifies whether or not to delete the source folder
        '''
        response = self.s3_client.list_objects_v2(Bucket=AWS_STORAGE_BUCKET_NAME, Prefix=source_folder)
        # Check if there are any objects to copy
        if 'Contents' not in response:
            return False
        for obj in response['Contents']:
            source_key = obj['Key']
            # Construct the destination key by replacing the source_folder prefix with destination_folder
            destination_key = os.path.join(destination_folder, os.path.relpath(source_key, source_folder))
            # Copy the object
            copy_source = {'Bucket': AWS_STORAGE_BUCKET_NAME, 'Key': source_key}
            self.s3_client.copy_object(CopySource=copy_source, Bucket=AWS_STORAGE_BUCKET_NAME, Key=destination_key)
        return True

    def get_tech_netlist_data(self, filepath, filetype, ftype, decrypt=True):
        try:
            session = Session(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
            s3 = session.resource('s3')
            bucket = s3.Bucket(AWS_STORAGE_BUCKET_NAME)
    
            if ftype == 'Techfile':
                try:
                    response = self.s3_client.get_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=filepath)
                    raw_content = response['Body'].read().decode('utf-8')
                    if decrypt:
                        try:
                            # Attempt to decrypt to validate the file
                            decrypted_content = decrypt_file_content(raw_content)  # We're not using the result, just validating
                        except InvalidToken:
                            message = "Selected tech file is not valid. Please select a valid tech file."
                            data1 = None
                            status_code = status.HTTP_400_BAD_REQUEST
                            response_status = False
                            return message, status_code, response_status, data1
                        data = json.loads(decrypted_content)
                    else:
                        # Return raw content as is, no decryption
                        data = raw_content
    
                    message = "Success"
                    response_status = True
                    status_code = status.HTTP_200_OK
                    return message, data, status_code, response_status
    
                except ClientError as e:
                    response = e.response
                    message = f"ClientError: {response['Error']['Message']}"
                    if response['Error']['Message'] == "The specified key does not exist.":
                        message = "File not found"
                    status_code = response['ResponseMetadata']['HTTPStatusCode']
                    response_status = False
                    data = None
                    return message, data, status_code, response_status
    
                except Exception as e:
                    message = f"Unexpected error: {str(e)}"
                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                    response_status = False
                    data = None
                    return message, data, status_code, response_status
    
            elif ftype == 'Netlist':
                try:
                    for obj in bucket.objects.filter(Prefix=filepath):
                        body = obj.get()['Body'].read()
    
                    if decrypt:
                        try:
                            # Attempt to decrypt to validate the file
                            filecontent = decrypt_file_content(body)  # We're not using the result, just validating
                            filecontent = b64encode(filecontent.encode('utf-8')).decode('utf-8')
                        except InvalidToken:
                            message = "Selected tech file is not valid. Please select a valid tech file."
                            data1 = None
                            status_code = status.HTTP_400_BAD_REQUEST
                            response_status = False
                            return message, status_code, response_status, data1
                    else:
                        filecontent = body  # encode raw bytes as base64 string
    
                    message = "Success"
                    response_status = True
                    status_code = status.HTTP_200_OK
                    return message, filecontent, status_code, response_status
    
                except ClientError as e:
                    response = e.response
                    message = f"ClientError: {response['Error']['Message']}"
                    if response['Error']['Message'] == "The specified key does not exist.":
                        message = "File not found"
                    status_code = response['ResponseMetadata']['HTTPStatusCode']
                    response_status = False
                    data = None
                    return message, data, status_code, response_status
    
                except Exception as e:
                    message = f"Unexpected error: {str(e)}"
                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                    response_status = False
                    data = None
                    return message, data, status_code, response_status
    
        except Exception as e:
            print(e)
            message = "No such File available."
            status_code = status.HTTP_404_NOT_FOUND
            response_status = False
            data = None
            return message, data, status_code, response_status
    
    def list_folders(self, base_path):
        paginator = self.s3_client.get_paginator('list_objects_v2')
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

    def list_files_with_extension(self, folder_path, extension,S3_BUCKET_ROOT):
        kwargs = {'Bucket': AWS_STORAGE_BUCKET_NAME, 'Prefix': folder_path}

        png_files = []
        while True:
            response = self.s3_client.list_objects_v2(**kwargs)
            
            if 'Error' in response:
                print(f"Error occurred: {response['Error']}")
                break            
            if 'Contents' in response:
                png_files.extend([ obj['Key'][len(f'{S3_BUCKET_ROOT}/'):] for obj in response['Contents'] if obj['Key'].endswith(extension)])
            if response['IsTruncated']:
                kwargs['ContinuationToken'] = response['NextContinuationToken']
            else:
                break

        return png_files

        """print("folder_paths",folder_paths)
        paginator = self.s3_client.get_paginator('list_objects_v2')
        files = []
        # Loop through each folder_path
        for path in folder_paths:
            path = path if path[-1] == '/' else path + '/' 
            # Paginate through objects with the given prefix and check for files with the given extension
            for page in paginator.paginate(Bucket=AWS_STORAGE_BUCKET_NAME, Prefix=path, Delimiter='/'):
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    if key.lower().endswith(extension):
                        files.append(key)
        return files"""

    def get_image(self, keypath):
        
        bucket_name = AWS_STORAGE_BUCKET_NAME
        
        try:
            response = self.s3_client.get_object(Bucket=bucket_name, Key=keypath)
            # Return a file-like object (BytesIO)
            return BytesIO(response['Body'].read())
        except NoCredentialsError:
            raise ValueError("AWS credentials not found")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError("Image not found in S3")
            else:
                raise e

    def get_combined_csv_file(self, base_path,cells,path_extension):
        """Combine CSV files from the specified folders into a single DataFrame."""
        for cell in cells:
            # Construct the S3 path for CSV files in the cell folder.
            prefix = f'{base_path}{cell}/{cell}{path_extension}'
            # List objects in the folder
            paginator = self.s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=AWS_STORAGE_BUCKET_NAME, Prefix=prefix):
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    if key.endswith('.csv'):
                        df = self.fetch_csv(key)
            
        """# Combine all DataFrames
        if all_dataframes:
            combined_df = pd.concat(all_dataframes, ignore_index=True)
            df1 = combined_df.where(pd.notnull(combined_df), None)
            return df1
        else:
            print("No CSV files found.")
            return pd.DataFrame()"""

    def fetch_csv(self, key):
        """Fetch CSV data from S3 and return it as a DataFrame."""
        try:
            obj = self.s3_client.get_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=key)

            # Read the content of the CSV file and convert it into a DataFrame
            df = pd.read_csv(obj['Body']).round(4)
            return df

        except Exception as e:
            print(f"Error fetching {key}: {e}")
            return pd.DataFrame()
    
    def fetch_files(self, file_path):
        """Retrieve a file from S3 and return it as a byte stream."""
        try:
            response = self.s3_client.get_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=file_path)
            return response['Body'].read()
        except Exception as e:
            return None

    def list_files(self, folder_path):
        """
        List all files in a given folder (S3 prefix) in the bucket.
        :param folder_path: S3 folder path (prefix) to list files from
        :return: List of file paths in the folder
        """
        # List files under the given folder_path (S3 prefix)
        try:
            # S3's "list_objects_v2" returns up to 1000 items at once by default
            response = self.s3_client.list_objects_v2(
                Bucket=AWS_STORAGE_BUCKET_NAME,  # Replace with your actual bucket name
                Prefix=folder_path,  # The folder path is the prefix
                Delimiter='/'  # This ensures we only list files (not subfolders)
            )

            # Check if 'Contents' is in the response (indicating files were found)
            if 'Contents' not in response:
                return []

            # Extract the file keys (paths) from the response
            file_keys = [item['Key'] for item in response['Contents']]
            filter_by_gds = 'layouts' in folder_path or 'permutations' in folder_path
            file_paths = []
            if filter_by_gds:
                    # Filter files to only include those ending in .gds
                file_paths.extend([file_key for file_key in file_keys if file_key.endswith('.gds')])
            else:
                # For other folders, include all files
                file_paths.extend([file_key for file_key in file_keys if not file_key.endswith('/')])
            # Filter out directories (S3 objects without file extensions)
            # file_paths = [file_key for file_key in file_keys if not file_key.endswith('/')]
            
            return file_paths

        except Exception as e:
            print(f"Error listing files in folder {folder_path}: {str(e)}")
            return []
    
    def create_zip_files(self, folders_to_zip, additional_files,file_types,filtered_list=None,zip_type=True):
        """Create a zip file with files from S3 while maintaining the folder structure (with threading)."""
        # zip_type = true download full folder
        # zip_type = false download individual
        additional_files = additional_files
        start_time = time.time()  # Start timing
        zip_buffer = io.BytesIO()
        files_added_to_zip = False
        FileSuccessList=list()
        gds_pass=list()
        missing_files = []  # List to track missing files
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_file = {executor.submit(self.fetch_files, file_path): file_path for file_path in folders_to_zip} 
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        if file_path.endswith('.csv'):
                            if filtered_list:
                                file_data = future.result()
                                csv_file =io.BytesIO(file_data)
                                data=pd.read_csv(csv_file)
                                csv_bytes=data[data['File'].isin(filtered_list)]
                                if csv_bytes.empty or csv_bytes.shape[0] == 0:
                                    file_data=None
                                else:
                                    csv_bytes = csv_bytes.to_csv(index=False).encode()
                                    file_data = BytesIO(csv_bytes)
                                    file_data = file_data.getvalue()
                            else:
                                file_data = future.result()
                        else:
                            file_data = future.result()
                        # If fetch_files returns None, handle it gracefully
                        if file_data is None:
                            missing_files.append(os.path.basename(file_path))
                            if zip_type==False:
                                if file_path.endswith(".gds"):
                                    return None, missing_files
                            print(f"File not found in S3: {file_path}")
                        stages = ['Stage1', 'Stage2']
                        for stage in stages:
                            stage_index = file_path.find(stage)
                            if stage_index != -1:
                                relative_path = file_path[stage_index:]
                                break
                            else:
                                relative_path = file_path
                        if zip_type:
                            relative_path = relative_path
                        else:
                            relative_path = relative_path.split("/")[-1]
                        # Write the file data into the zip file with the relative path
                        if file_data:
                            zip_file.writestr(relative_path, file_data)
                            files_added_to_zip = True
                            if files_added_to_zip and relative_path.endswith('.gds'):
                                gds_pass.append(True)
                            FileSuccessList.append(files_added_to_zip)
                            
                    except Exception as e:
                        missing_files.append(os.path.basename(file_path))
                        print(f"Error processing file {file_path}: {e}")
        # Now append additional files to the zip_buffer inside Stage1 or Stage2
        if file_types==None:
            pass
        elif 'gds' in file_types:
            if additional_files:
                with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED) as zip_file:
                    for file in additional_files:
                        try:
                            # Ensure the file path is relative to your current directory
                            file_path = os.path.join(os.getcwd(), file)  # Add the code directory path
                            if os.path.exists(file_path):
                                with open(file_path, 'rb') as f:
                                    file_data = f.read()
                                    # Determine if the additional file should go in Stage1 or Stage2
                                    if "Stage1" in file:
                                        relative_path = f"Stage1/{os.path.basename(file_path)}"
                                    elif "Stage2" in file:
                                        relative_path = f"Stage2/{os.path.basename(file_path)}"
                                    else:
                                        # Default location if not specified
                                        relative_path = f"{os.path.basename(file_path)}"  
                                    # Write the file to the zip under the appropriate directory
                                    zip_file.writestr(relative_path, file_data)
                                    files_added_to_zip = True
                            else:
                                print(f"Additional file {file} not found in code directory.")
                                missing_files.append(file)
    
                        except Exception as e:
                            missing_files.append(file)
                            print(f"Error adding additional file {file}: {e}")
        if True in FileSuccessList:
            # Go to the start of the zip file before returning
            zip_buffer.seek(0, 2)  # Seek to end
            file_size = zip_buffer.tell()  # Get current position (file size)
            zip_buffer.seek(0)  # Reset to beginning
            end_time = time.time()  # End timing
            logger.info(f"File size: {file_size}")
            logger.info(f"Time to create zip file: {end_time - start_time:.2f} seconds")
            return (zip_buffer, missing_files) if files_added_to_zip else (None, missing_files)
        else:
            return None, missing_files
        
    def has_png_files(self, prefix=""):
        """
        Check if the given S3 bucket contains any .png files.

        :param bucket_name: Name of the S3 bucket.
        :param prefix: (Optional) Folder path inside the bucket.
        :return: True if at least one .png file is found, else False.
        """        
        try:
            response = self.s3_client.list_objects_v2(Bucket=AWS_STORAGE_BUCKET_NAME, Prefix=prefix)
            if "Contents" in response:
                for obj in response["Contents"]:
                    if obj["Key"].lower().endswith(".png"):
                        return True
            return False

        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def rename_file(self, old_file_path, new_file_name):
        """
        Renames a file in S3 by copying it to a new name and deleting the original.

        Parameters:
        - old_file_path (str): Full S3 key of the original file (e.g., 'Netlist/0/old_file.spice')
        - new_file_name (str): New file name only (e.g., 'new_file.spice')      
        Returns:
        - bool: True if rename succeeded, False otherwise
        """
        # Derive new path from old path and new filename
        path_prefix = "/".join(old_file_path.split("/")[:-1])
        new_file_path = f"{path_prefix}/{new_file_name}"        
        try:
            # Copy the object to new key
            self.s3_client.copy_object(
                Bucket=AWS_STORAGE_BUCKET_NAME,
                CopySource={'Bucket': AWS_STORAGE_BUCKET_NAME, 'Key': old_file_path},
                Key=new_file_path
            )       
            # Delete the original object
            self.s3_client.delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=old_file_path)     
            print(f"File renamed from {old_file_path} to {new_file_path}")
            return True     
        except ClientError as e:
            print(f"Failed to rename file: {e}")
            return False
        
    # def get_tech_netlist_data_migration(self, filepath, filetype, ftype, decrypt=True):
        # try:
            # session = Session(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
            # s3 = session.resource('s3')
            # bucket = s3.Bucket(AWS_STORAGE_BUCKET_NAME)
    # 
            # if ftype == 'Techfile':
                # try:
                    # response = self.s3_client.get_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=filepath)
                    # raw_content = response['Body'].read().decode('utf-8')
    # 
                    # if decrypt:
                        # decrypted_content = decrypt_file_content(raw_content)
                        # data = json.loads(decrypted_content)
                    # else:
                        # Return raw content as is, no decryption
                        # data = raw_content
    # 
                    # message = "Success"
                    # response_status = True
                    # status_code = status.HTTP_200_OK
                    # return message, data, status_code, response_status
    # 
                # except ClientError as e:
                    # response = e.response
                    # message = f"ClientError: {response['Error']['Message']}"
                    # if response['Error']['Message'] == "The specified key does not exist.":
                        # message = "File not found"
                    # status_code = response['ResponseMetadata']['HTTPStatusCode']
                    # response_status = False
                    # data = None
                    # return message, data, status_code, response_status
    # 
                # except Exception as e:
                    # message = f"Unexpected error: {str(e)}"
                    # status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                    # response_status = False
                    # data = None
                    # return message, data, status_code, response_status
    # 
            # elif ftype == 'Netlist':
                # try:
                    # for obj in bucket.objects.filter(Prefix=filepath):
                        # body = obj.get()['Body'].read()
    # 
                    # if decrypt:
                        # filecontent = decrypt_file_content(body)
                        # filecontent = b64encode(filecontent.encode('utf-8')).decode('utf-8')
                    # else:
                        # filecontent = b64encode(body).decode('utf-8')  # encode raw bytes as base64 string
    # 
                    # message = "Success"
                    # response_status = True
                    # status_code = status.HTTP_200_OK
                    # return message, filecontent, status_code, response_status
    # 
                # except ClientError as e:
                    # response = e.response
                    # message = f"ClientError: {response['Error']['Message']}"
                    # if response['Error']['Message'] == "The specified key does not exist.":
                        # message = "File not found"
                    # status_code = response['ResponseMetadata']['HTTPStatusCode']
                    # response_status = False
                    # data = None
                    # return message, data, status_code, response_status
    # 
                # except Exception as e:
                    # message = f"Unexpected error: {str(e)}"
                    # status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                    # response_status = False
                    # data = None
                    # return message, data, status_code, response_status
    # 
        # except Exception as e:
            # print(e)
            # message = "No such File available."
            # status_code = status.HTTP_404_NOT_FOUND
            # response_status = False
            # data = None
            # return message, data, status_code, response_status
    # 