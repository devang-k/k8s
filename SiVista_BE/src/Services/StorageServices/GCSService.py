from src.Services.StorageServices.BaseService import BaseService
from google.cloud import storage
from django.http import FileResponse
from src.Services.EncryptDecryptService import decrypt_file_content, InvalidToken
from io import BytesIO
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.api_core.exceptions import GoogleAPIError
from google.cloud.exceptions import NotFound, GoogleCloudError
import zipfile
import os
import time
import json
from base64 import b64encode
from rest_framework import status
from SiVista_BE.settings import GOOGLE_STORAGE_BUCKET_NAME

class GCSService(BaseService):
    def __init__(self):
        print('You have chosen Google Cloud Storage as your storage preference.')
        self.client = storage.Client()
        self.bucket = self.client.get_bucket(GOOGLE_STORAGE_BUCKET_NAME)

    def get_file(self, filePath: str):
        '''
        A function that accepts a file path and returns the file at that location in the GCS bucket.
        Returns file as a FileResponse object.
        '''
        try:
            blob = self.bucket.blob(filePath)
            file_content = blob.download_as_bytes()
            file_stream = BytesIO(file_content)
            response = FileResponse(file_stream, as_attachment=True, filename=filePath.split("/")[-1])
            return {
                'success': True,
                'response': response,
                'status_code': status.HTTP_200_OK,
                'data': None
            }
        except NotFound as e:
            message = f"FileNotFoundError: {str(e)}"
            return {
                'success': False,
                'error': message,
                'status_code': status.HTTP_404_NOT_FOUND,
                'data': None
            }
        except GoogleCloudError as e:
            message = f"GoogleCloudError: {str(e)}"
            return {
                'success': False,
                'error': message,
                'status_code': status.HTTP_400_BAD_REQUEST,
                'data': None
            }
        except Exception as e:
            message = f"Unexpected error: {str(e)}"
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            response_status = False
            data = None
            return message, data, status_code, response_status
        except Exception as e:
            print("Failed to get file from GCS:", str(e))
            return {
                'success': False,
                'error': "Failed to get file from GCS",
                'status_code': status.HTTP_400_BAD_REQUEST,
                'data': None
            }
    
    def get_image(self, keypath):
        '''
        A function that accepts a key path and returns the image at that location in the GCS bucket.
        Returns a file-like object (BytesIO).
        '''
        try:
            # Get the blob (file) from the bucket
            blob = self.bucket.blob(keypath)
            # Download the blob's content as bytes
            file_content = blob.download_as_bytes()
            # Return a file-like object (BytesIO)
            return BytesIO(file_content)
        except Exception as e:
            if isinstance(e, storage.exceptions.NotFound):
                raise FileNotFoundError("Image not found in GCS")
            else:
                raise ValueError("An error occurred while accessing GCS: " + str(e))

    def store_file(self, fileData, filePath: str):
        '''
        Accepts data in the form of a FileData object and a path and creates a file with that data at the specified location in the GCS bucket.
        '''
        validation = fileData.validate()
        if not validation['passed']:
            return {
                'success': False,
                'error': validation['errors']
            }
        try:
            # Create a blob object
            blob = self.bucket.blob(filePath)
            # Upload the file object to the blob
            blob.upload_from_file(fileData.fileObj)
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
        
        # Construct the file URL
        file_url = f"https://storage.googleapis.com/{self.bucket.name}/{filePath}"
        return {
            'success': True,
            'fileUrl': file_url
        }

    def delete_file(self, file_path):
        '''
        Delete a specific file from a GCS bucket.
        '''
        try:
            # Get the blob (file) from the bucket
            blob = self.bucket.blob(file_path)
            # Delete the blob
            blob.delete()
            return True
        except Exception as e:
            print(f'Error deleting file: {e}')
            return False

    def write_file(self, filePath: str, fileData: str, type: int):
        '''
        Input: file path in the GCS bucket and file data as a string.
        Action: Writes file data into the file.
        type 1 writes the data as is, type 2 writes the data as a JSON.
        '''
        try:
            # Create a blob object
            blob = self.bucket.blob(filePath)
            if type == 1:
                # Upload the file data as is
                blob.upload_from_string(fileData)
                return True
            elif type == 2:
                # Upload the file data as JSON
                blob.upload_from_string(fileData, content_type='application/json')
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False

    def get_bucket_file_size(self, filePath: str) -> float:
        """
        Fetches the size of the file stored in the GCS bucket.
        
        Inputs:
        - filePath: str : The path of the file in the GCS bucket.
        
        Returns:
        - (float) : File size in bytes.
        """
        try:
            response = self.bucket.blob(filePath).download_as_bytes()  # Get the blob and download as bytes
            file_size = len(response)  # Size in bytes
            return file_size / 1024  # Convert to KB
        except Exception as e:
            print(f"Error fetching file size for {filePath}: {e}")
            return -1

    def copy_files(self, location1: str, location2: str, file_names: list):
        '''
        Copies files specified in file_names from location1 to location2 in the GCS bucket.
        '''
        moved_files = 0
        for file_name in file_names:
            source_blob_name = f'{location1}{file_name}'
            destination_blob_name = f'{location2}{file_name}'
            try:
                # Get the source blob
                source_blob = self.bucket.blob(source_blob_name)
                # Copy the blob to the new location
                self.bucket.copy_blob(source_blob, self.bucket, destination_blob_name)
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
        Deletes all files in a folder in the GCS bucket.
        '''
        if not folder_path.endswith('/'):
            folder_path += '/'
        
        # List all blobs with the specified prefix (folder path)
        blobs = self.bucket.list_blobs(prefix=folder_path)
        delete_keys = [blob.name for blob in blobs]

        if not delete_keys:
            return False

        try:
            # Delete each blob
            for blob_name in delete_keys:
                blob = self.bucket.blob(blob_name)
                blob.delete()
            return True
        except Exception as e:
            print(f'Error deleting folder: {e}')
            return False

    def move_folder(self, source_folder: str, destination_folder: str, delete_source: bool = False):
        '''
        Makes a copy of folder at path source_folder at path destination_folder.
        delete_source specifies whether or not to delete the source folder.
        '''
        if not source_folder.endswith('/'):
            source_folder += '/'
        if not destination_folder.endswith('/'):
            destination_folder += '/'

        # List all blobs with the specified prefix (source folder)
        blobs = self.bucket.list_blobs(prefix=source_folder)
        moved_files = 0

        for blob in blobs:
            source_key = blob.name
            # Construct the destination key by replacing the source_folder prefix with destination_folder
            destination_key = os.path.join(destination_folder, os.path.relpath(source_key, source_folder))
            # Copy the blob to the new location
            self.bucket.copy_blob(blob, self.bucket, destination_key)
            moved_files += 1

            # Optionally delete the source blob
            if delete_source:
                blob.delete()

        return moved_files > 0
    def list_folders(self, base_path):
        """Lists "folders" (prefixes) under a given base path in Google Cloud Storage."""

        folders = set()
        blobs = self.client.list_blobs(self.bucket, prefix=base_path, delimiter='/') 

        for blob in blobs:
            if blob.name != base_path: # Exclude the base path itself
                folder_name = blob.name[len(base_path):].split('/')[0]
                if folder_name:  # Avoid empty folder names
                    folders.add(folder_name)

        for prefix in blobs.prefixes:
            folder_name = prefix[len(base_path):].rstrip('/') # Remove trailing slash
            if folder_name:
                folders.add(folder_name.split('/')[0])

        return list(folders)

    def list_files_with_extension(self, folder_path, extension, gcs_bucket_root):
        """Lists files with a specific extension within a given folder in GCS."""

        if not folder_path.endswith('/'):
            folder_path += '/'

        blobs = self.client.list_blobs(self.bucket, prefix=folder_path)

        result = [
            blob.name[len(f'{gcs_bucket_root}/'):]
            for blob in blobs
            if blob.name.endswith(extension)
        ]

        return result

    def get_combined_csv_file(self, base_path, cells, path_extension):
        """Combines CSV files from specified folders in GCS into a single DataFrame."""

        combined_df = pd.DataFrame()  # Initialize an empty DataFrame

        for cell in cells:
            prefix = f'{base_path}{cell}/{cell}{path_extension}'
            blobs = self.client.list_blobs(self.bucket, prefix=prefix)

            for blob in blobs:
                if blob.name.endswith('.csv'):
                    df = self.fetch_csv(blob.name)
                    if df is not None: # Check if DataFrame was successfully created
                        combined_df = pd.concat([combined_df, df], ignore_index=True)

        return combined_df

    def get_tech_netlist_data(self, filepath, filetype, ftype, decrypt=True):
        try:
            blob = self.bucket.blob(filepath)

            if ftype == 'Techfile':
                try:
                    if not blob.exists():
                        raise NotFound(f"File not found: {filepath}")

                    raw_content = blob.download_as_text()

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
                        data = raw_content

                    message = "Success"
                    response_status = True
                    status_code = status.HTTP_200_OK
                    return message, data, status_code, response_status

                except NotFound:
                    message = "File not found"
                    status_code = status.HTTP_404_NOT_FOUND
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
                    if not blob.exists():
                        raise NotFound(f"File not found: {filepath}")

                    body = blob.download_as_bytes()

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

                except NotFound:
                    message = "File not found"
                    status_code = status.HTTP_404_NOT_FOUND
                    response_status = False
                    data = None
                    return message, data, status_code, response_status

                except Exception as e:
                    message = f"Unexpected error: {str(e)}"
                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                    response_status = False
                    data = None
                    return message, data, status_code, response_status

        except GoogleAPIError as e:
            message = f"GCS API error: {str(e)}"
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            response_status = False
            data = None
            return message, data, status_code, response_status

        except Exception as e:
            print(e)
            message = "No such file available."
            status_code = status.HTTP_404_NOT_FOUND
            response_status = False
            data = None
            return message, data, status_code, response_status
                
    def get_tech_netlist_list(self, name, filepath):
        """Lists files within a given filepath in GCS and returns their details."""

        my_list = []
        blobs = self.client.list_blobs(self.bucket, prefix=filepath)

        for blob in blobs:
            file_name = blob.name.split('/')[-1]
            if file_name:  # Check if filename is not empty
                element = {
                    'FileName': file_name,
                    'FileType': name,
                    'TimeStamp': blob.updated  # Use blob.updated for timestamp
                }
                my_list.append(element)

        return my_list
        
    def list_files(self, folder_path):
        """
        List all files in a given folder (GCS prefix) in the bucket.

        :param folder_path: GCS folder path (prefix) to list files from
        :return: List of file paths in the folder
        """
        try:
            blobs = self.bucket.list_blobs(prefix=folder_path)
            file_keys = [blob.name for blob in blobs]

            filter_by_gds = 'layouts' in folder_path or 'permutations' in folder_path
            file_paths = []

            if filter_by_gds:
                # Filter files to only include those ending in .gds
                file_paths.extend([file_key for file_key in file_keys if file_key.endswith('.gds')])
            else:
                # For other folders, include all files (ignore "directories")
                file_paths.extend([file_key for file_key in file_keys if not file_key.endswith('/')])

            return file_paths

        except Exception as e:
            print(f"Error listing files in folder {folder_path}: {str(e)}")
            return []
    
    def fetch_files(self, file_path):
        try:
            # Get the blob (file) from the bucket
            blob = self.bucket.blob(file_path)
            return blob.download_as_bytes()
        except Exception as e:
            print(f"An error occurred while fetching the file: {e}")
            return None
    
    def create_zip_files(self, folders_to_zip, additional_files,file_types,filtered_list=None,zip_type=True):
        """Create a zip file with files from S3 while maintaining the folder structure (with threading)."""
        # zip_type = true download full folder
        # zip_type = false download individual
        additional_files = additional_files
        start_time = time.time()  # Start timing
        zip_buffer = BytesIO()
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
                                csv_file =BytesIO(file_data)
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
            return (zip_buffer, missing_files) if files_added_to_zip else (None, missing_files)
        else:
            return None, missing_files

    
    def fetch_csv(self,key):
        """
        Fetch CSV data from GCS and return it as a DataFrame.

        :param bucket_name: Name of the GCS bucket.
        :param key: Path to the CSV file in the bucket.
        :return: pandas DataFrame containing the CSV data.
        """
        try:
            blob = self.bucket.blob(key)

            # Download the blob content as bytes and read into a DataFrame
            data = blob.download_as_bytes()
            df = pd.read_csv(BytesIO(data)).round(4)
            return df

        except Exception as e:
            print(f"Error fetching {key}: {e}")
            return pd.DataFrame()
    
    def has_png_files(self, prefix=""):
        """
        Check if the given GCS bucket contains any .png files.

        :param bucket_name: Name of the GCS bucket.
        :param prefix: (Optional) Folder path inside the bucket.
        :return: True if at least one .png file is found, else False.
        """
        try:
            blobs = self.bucket.list_blobs(prefix=prefix)

            for blob in blobs:
                if blob.name.lower().endswith(".png"):
                    return True
            return False

        except Exception as e:
            print(f"Error: {e}")
            return False

    def rename_file(self, old_blob_name, new_blob_name):
        """
        Renames a file in Google Cloud Storage by copying it to a new blob and deleting the old one.

        Parameters:
        - bucket_name (str): Name of the GCS bucket.
        - old_blob_name (str): Current full path/key of the blob in the bucket (e.g., 'Netlist/0/old_file.spice').
        - new_blob_name (str): New full path/key for the renamed blob (e.g., 'Netlist/0/new_file.spice').

        Returns:
        - bool: True if rename succeeded, False otherwise.
        """
        try:
            old_blob = self.bucket.blob(old_blob_name)

            if not old_blob.exists():
                print(f"Blob not found: {old_blob_name}")
                return False

            # Copy to new blob
            new_blob = self.bucket.copy_blob(old_blob, self.bucket, new_blob_name)

            # Delete original blob
            old_blob.delete()

            print(f"Renamed {old_blob_name} to {new_blob_name}")
            return True

        except GoogleAPIError as e:
            print(f"Error renaming blob: {e}")
            return False
        
    def get_tech_netlist_data_migration(self, filepath, filetype, ftype, decrypt=True):
        pass