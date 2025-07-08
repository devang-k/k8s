"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: LocalService.py  
 * Description: Local storage service to provide solutions on stored files
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
from os import makedirs, remove, walk, sep, listdir, path, getcwd, rename
from django.http import FileResponse
from os.path import join, exists, dirname, relpath, isdir, isfile, getmtime, basename, getsize
from pathlib import Path
from pandas import read_csv, DataFrame, concat
from io import BytesIO
from json import dump, loads
from shutil import copy2, rmtree
from src.Models.FileStorage.FileData import FileData
from src.Services.StorageServices.BaseService import BaseService
from src.Services.EncryptDecryptService import decrypt_file_content, InvalidToken
from SiVista_BE.settings import LOCAL_BASE_PATH
from rest_framework import status
from base64 import b64encode
from datetime import datetime
import pandas as pd
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)  # Create a logger instance for this module

class LocalService(BaseService):
    def __init__(self):
        print('You have chosen a local directory as your storage prference.')
        makedirs(dirname(LOCAL_BASE_PATH), exist_ok=True)
    
    def get_file(self, filePath: str):
        '''
        A function that accepts a file path and returns the file at that location in the local directory.
        Returns file as a FileResponse object.
        '''
        # Construct the full local file path
        local_file_path = join(LOCAL_BASE_PATH, filePath)
        try:
            if exists(local_file_path):
                file_stream = open(local_file_path, 'rb')
                response = FileResponse(file_stream)
                response['Content-Disposition'] = f'attachment; filename="{Path(local_file_path).name}"'
                return {
                    'success': True,
                    'response': response,
                    'status_code': status.HTTP_200_OK,
                    'data': None
            }
            else:
                message = f"FileNotFoundError: {str(e)}"
                return {
                    'success': False,
                    'error': message,
                    'status_code': status.HTTP_404_NOT_FOUND,
                    'data': None
                }
        except Exception as e:
            print("Failed to get file from local directory:", str(e))
            return {
                'success': False,
                'error': "Failed To get file from local directory",
                'status_code': 400,
                'data': None
            }
    
    def get_image(self, keypath: str):
        '''
        Retrieves an image from the local directory.
        Returns a file-like object (BytesIO).
        '''
        # Construct the full file path
        image_path = join(LOCAL_BASE_PATH, keypath)
        try:
            # Open the image in binary mode and return a BytesIO object
            if exists(image_path):
                with open(image_path, 'rb') as image_file:
                    return BytesIO(image_file.read())
            else:
                raise FileNotFoundError("Image not found in local directory")
        except Exception as e:
            raise ValueError(f"Error retrieving image: {e}")

    def store_file(self, fileData: FileData, filePath: str):
        '''
        Accepts data in the form of a FileData object and a path,
        and creates a file with that data at the specified location in the local directory.
        '''
        validation = fileData.validate()
        if not validation['passed']:
            return {
                'success': False,
                'error': validation['errors']
            }
        # Construct the full file path
        full_path = join(LOCAL_BASE_PATH, filePath)
        try:
            # Write the file data to the specified path
            with open(full_path, 'wb') as f:
                f.write(fileData.fileBytes)
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
        # Return the local file URL (can adjust as needed)
        return {
            'success': True,
            'fileUrl': f"file://{full_path}"
        }

    def delete_file(self, file_path: str):
        '''
        Delete a specific file from the local directory.
        '''
        try:
            # Construct the full file path
            file_path = join(LOCAL_BASE_PATH, file_path)
            
            # Check if the file exists and delete it
            if exists(file_path):
                remove(file_path)
                return True
            else:
                print('File not found')
                return False
        except Exception as e:
            print(f'Error deleting file: {e}')
            return False

    def write_file(self, filePath: str, fileData: str, type: int):
        '''
        Input: File path in the local directory and file data as a string.
        Action: Writes file data into the file.
        type 1 writes the data as is, type 2 writes the data as JSON.
        '''
        try:
            fileData = fileData.decode('utf-8') if isinstance(fileData, bytes) else fileData
            # Construct the full file path
            file_path = join(LOCAL_BASE_PATH, filePath)
            # Ensure the directory exists
            makedirs(dirname(file_path), exist_ok=True)
            # Write data based on the type
            if type == 1:
                # Write data as plain text
                with open(file_path, 'w') as f:
                    f.write(fileData)
                return True
            elif type == 2:
                # Write data as JSON
                with open(file_path, 'w') as f:
                    dump(loads(fileData), f, indent=4)
                return True
            else:
                return False
        except Exception as e:
            print(f'Error writing file: {e}')
            return False

    def get_bucket_file_size(self, filePath: str) -> float:
        """
        Calculates the size of the file from the local I/O path.

        Parameters:
        - local_path: str : The local file path.

        Returns:
        - float : Size in kilobytes.
        """
        try:
            file_path = join(LOCAL_BASE_PATH, filePath)
            file_size_bytes = getsize(file_path)
            return file_size_bytes / 1024.0  # Convert bytes to KB
        except OSError as e:
            print(f"Error reading file size for local path {file_path}: {e}")
            return -1.0  # Return -1 to indicate an error

    def copy_files(self, location1: str, location2: str, file_names: list):
        '''
        Copies files specified in file_names from location1 to location2 in the local directory.
        '''
        moved_files = 0
        for file_name in file_names:
            # Construct the source and destination file paths
            source_file = join(LOCAL_BASE_PATH, location1, file_name)
            destination_file = join(LOCAL_BASE_PATH, location2, file_name)
            try:
                # Ensure the destination directory exists
                makedirs(dirname(destination_file), exist_ok=True)
                # Copy the file from location1 to location2
                copy2(source_file, destination_file)
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
        Deletes all files and the folder itself in the local directory.
        '''
        # Construct the full folder path
        full_folder_path = join(LOCAL_BASE_PATH, folder_path)
        try:
            # Check if the folder exists
            if exists(full_folder_path):
                # Delete the folder and all its contents
                rmtree(full_folder_path)
                return True
            else:
                return True
        except Exception as e:
            print(e)
            return False

    def move_folder(self, source_folder: str, destination_folder: str, delete_source: bool = False):
        '''
        Makes a copy of the folder at path source_folder to destination_folder.
        If delete_source is True, it deletes the source folder after copying.
        '''
        # Construct the full source and destination folder paths
        source_folder_path = join(LOCAL_BASE_PATH, source_folder)
        destination_folder_path = join(LOCAL_BASE_PATH, destination_folder)
        try:
            # Check if the source folder exists
            if not exists(source_folder_path):
                return {'success': False, 'message': 'Source folder does not exist'}
            # Ensure the destination folder exists
            makedirs(destination_folder_path, exist_ok=True)
            # Copy the source folder to the destination
            for root, dirs, files in walk(source_folder_path):
                relative_path = relpath(root, source_folder_path)
                target_folder = join(destination_folder_path, relative_path)
                # Create the subdirectories in the destination
                makedirs(target_folder, exist_ok=True)
                # Copy each file
                for file_name in files:
                    source_file = join(root, file_name)
                    destination_file = join(target_folder, file_name)
                    copy2(source_file, destination_file)
            # Optionally delete the source folder
            if delete_source:
                rmtree(source_folder_path)
            return True
        except Exception as e:
            return False

    def list_folders(self, base_path: str):
        '''
        Lists unique folder names under the specified base_path in the local directory.
        '''
        # Construct the full base path
        full_base_path = join(LOCAL_BASE_PATH, base_path)
        folders = set()
        # Walk through the directory structure
        for root, dirs, _ in walk(full_base_path):
            # Extract the folder name relative to the base_path
            for dir_name in dirs:
                relative_path = relpath(join(root, dir_name), full_base_path)
                folder_name = relative_path.split(sep)[0]  # Get the first-level folder name
                if folder_name:  # Avoid empty folder names
                    folders.add(folder_name)
        return list(folders)

    def list_files_with_extension(self, folder_path, extension, root_path):
        # Full folder path to search
        full_folder_path = path.join(LOCAL_BASE_PATH, folder_path)
        root_base_path = path.join(LOCAL_BASE_PATH, root_path)    
        # Check if the folder exists
        if not path.exists(full_folder_path):
            return []

        # List files with the given extension and get relative paths from root_base_path
        files_with_extension = [
            path.relpath(path.join(full_folder_path, file), start=root_base_path)
            for file in listdir(full_folder_path)
            if file.endswith(extension) and path.isfile(path.join(full_folder_path, file))
        ]
        return files_with_extension

    def fetch_csv(self, file_path: str):
        '''
        Reads a CSV file from the local directory and returns it as a pandas DataFrame.
        '''
        full_path = join(LOCAL_BASE_PATH, file_path)
        try:
            return read_csv(full_path).round(4)
        except FileNotFoundError:
            print(f"CSV file not found: {file_path}")
            return DataFrame()
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return DataFrame()

    def get_combined_csv_file(self, folder_path: str, cells: list, path_extension: str):
        '''
        Combines all CSV files in the specified folder_path into a single DataFrame.
        '''
        full_folder_path = join(LOCAL_BASE_PATH, folder_path)
        combined_df = DataFrame()
        for cell in cells:
            # Construct the S3 path for CSV files in the cell folder.
            prefix = f'{full_folder_path}{cell}/{cell}{path_extension}'
            # Iterate through the files in the specified folder
            for root, _, files in walk(prefix):
                for file in files:
                    if file.lower().endswith('.csv'):
                        file_path = join(root, file)
                        try:
                            # Fetch and append the CSV data
                            df = self.fetch_csv(relpath(file_path, LOCAL_BASE_PATH))
                            combined_df = concat([combined_df, df], ignore_index=True)
                        except Exception as e:
                            print(f"Error processing file {file}: {e}")
        return combined_df

    def get_tech_netlist_data(self, filepath: str, filetype: str, ftype: str, decrypt: bool = True):
        '''
        Reads a techfile or netlist file from the local directory and returns its content.
        If decrypt is True, it decrypts the content before returning.
        '''
        # Construct the full file path
        filepath = join(LOCAL_BASE_PATH, filepath)
        message = ""
        data = None
        status_code = 0
        response_status = False
        try:
            if not path.isfile(filepath):
                message = "File not found"
                status_code = status.HTTP_404_NOT_FOUND
                response_status = False
                data = None
                return message, data, status_code, response_status

            if ftype == 'Techfile':
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        raw_content = f.read()

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
                        data = loads(decrypted_content)
                    else:
                        data = raw_content

                    message = "Success"
                    status_code = status.HTTP_200_OK
                    response_status = True
                    return message, data, status_code, response_status

                except Exception as e:
                    message = f"Unexpected error: {str(e)}"
                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                    response_status = False
                    data = None
                    return message, data, status_code, response_status

            elif ftype == 'Netlist':
                try:
                    with open(filepath, 'rb') as f:
                        body = f.read()

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
                        filecontent = body

                    message = "Success"
                    status_code = status.HTTP_200_OK
                    response_status = True
                    return message, filecontent, status_code, response_status

                except Exception as e:
                    message = f"Unexpected error: {str(e)}"
                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                    response_status = False
                    data = None
                    return message, data, status_code, response_status

        except Exception as e:
            print(e)
            message = "Unexpected server error."
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            response_status = False
            data = None
            return message, data, status_code, response_status
        
    def get_tech_netlist_list(self, name: str, filepath: str):
        full_path = join(LOCAL_BASE_PATH, filepath)
        myList = []
        # Check if the directory exists
        if not exists(full_path):
            return myList  # Return empty list if the directory doesn't exist
        # Iterate over all files in the specified directory
        for file_name in listdir(full_path):
            file_path = join(full_path, file_name)
            # Check if it's a file (not a directory)
            if isfile(file_path):
                element = {
                    'FileName': file_name,
                    'FileType': name,
                    'TimeStamp': datetime.fromtimestamp(getmtime(file_path))  # Get last modified time
                }
                myList.append(element)
        return myList
    
    def fetch_files(self, file_path):
        file_path = join(LOCAL_BASE_PATH, file_path)
        try:
            with open(file_path, 'rb') as file:
                return file.read()
        except Exception as e:
            print(f"{e}")
            return None

    def list_files(self, folder_path):
        """
        List all files in a given local folder.
        :param folder_path: Local folder path to list files from
        :return: List of file paths in the folder
        """
        folder_path = join(LOCAL_BASE_PATH, folder_path)
        file_paths = []
        try:
            # List all files recursively under the folder
            for root, dirs, files in walk(folder_path):
                filter_by_gds = 'layouts' in folder_path or 'permutations' in folder_path
                for file in files:
                    temp_path = join(root, file)
                    if filter_by_gds and file.endswith('.gds'):
                        file_paths.append(temp_path)
                    elif not filter_by_gds and not ('layouts' in root or 'permutations' in root):
                        file_paths.append(temp_path)
            return file_paths
        except Exception as e:
            print(f"Error listing files in folder {folder_path}: {str(e)}")
            return []

    def create_zip_files(self, folders_to_zip, additional_files,file_types,filtered_list,zip_type=True):
        """Create a zip file with files from S3 while maintaining the folder structure (with threading)."""
        # zip_type = true download full folder
        # zip_type = false download individual
        start_time = time.time()  # Start timing
        zip_buffer = BytesIO()
        files_added_to_zip = False
        missing_files = []  # List to track missing files
        FileSuccessList=list()
        gds_pass= list()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # # List all files from the folders
            # all_files = []
            # for path in folders_to_zip:
            #     if zip_type:
            #         all_files.extend(self.list_files(path))
            #     else:
            #         all_files.append(path)
            # filtered_files = [file for file in all_files if not file.endswith('resistance_pred.log')]
            # print(filtered_files)
            # Create a thread pool to fetch files in parallel
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_file = {executor.submit(self.fetch_files, file_path): file_path for file_path in folders_to_zip}
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        file_data = future.result()
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
                        if file_data is None:
                            missing_files.append(basename(file_path))
                            print(f"File not found in S3: {file_path}")
                        # Try to find the first stage in the list
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
                        missing_files.append(basename(file_path))
                        if zip_type==False:
                            if file_path.endswith(".gds"):
                                return None, missing_files
                        # Log any error that occurs while fetching or writing the file (optional)
                        print(f"Error processing file {file_path}: {e}")
        if file_types==None:
            pass
        elif 'gds' in file_types:
            if additional_files:
                with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED) as zip_file:
                    for file in additional_files:
                        try:
                            # Ensure the file path is relative to your current directory
                            file_path = join(getcwd(), file)  # Add the code directory path
                            
                            if exists(file_path):
                                with open(file_path, 'rb') as f:
                                    file_data = f.read()
                                    
                                    # Determine if the additional file should go in Stage1 or Stage2
                                    if "Stage1" in file:
                                        relative_path = f"Stage1/{basename(file_path)}"
                                    elif "Stage2" in file:
                                        relative_path = f"Stage2/{basename(file_path)}"
                                    else:
                                        # Default location if not specified
                                        relative_path = f"{basename(file_path)}"
                                        
                                    # Write the file to the zip under the appropriate directory
                                    zip_file.writestr(relative_path, file_data)
                                    print(f"Added additional file at {relative_path}")
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
        
    def has_png_files(self,directory_path):
        """Check if the given directory contains any .png files."""
        folder_path = join(LOCAL_BASE_PATH, directory_path)
        if not path.isdir(folder_path):
            print("Invalid directory path.")
            return False
        
        for file in listdir(folder_path):
            if file.lower().endswith('.png'):
                return True
        return False
    
    def rename_file(self, old_file_path, new_file_name):
        """
        Renames a file in local storage by changing its filename.

        Parameters:
        - old_file_path (str): Full path to the original file (e.g., '/path/to/Netlist/0/old_file.spice')
        - new_file_name (str): New file name only (e.g., 'new_file.spice')

        Returns:
        - bool: True if rename succeeded, False otherwise
        """
        try:
            old_file_path = join(LOCAL_BASE_PATH, old_file_path)
            dir_path = path.dirname(old_file_path)
            new_file_path = path.join(dir_path, new_file_name)

            if not path.exists(old_file_path):
                print(f"File not found: {old_file_path}")
                return False

            rename(old_file_path, new_file_path)
            print(f"File renamed to: {new_file_path}")
            return True

        except Exception as e:
            print(f"Rename failed: {e}")
            return False
    def get_tech_netlist_data_migration(self, filepath, filetype, ftype, decrypt=True):
        pass