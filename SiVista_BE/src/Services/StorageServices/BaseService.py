"""/***************************************************************************  
 * Copyright © 2024 SiClarity, Inc.  
 * All rights reserved.  
 *  
 * File Name: BaseService.py  
 * Description: Abstact methods to manage storage
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
from django.http import FileResponse

class BaseService:
    def __init__(self):
        print('You have not set a storage prference.')

    def read_file_response_content(self, file_response: FileResponse):
        '''
        Input: A file as a FileResponse object.
        Output: Contents of the file as a string
        '''
        file_content = b''.join(file_response.streaming_content)
        return file_content

    def get_file(self):
        raise NotImplementedError("Subclasses should implement this method.")
    
    def get_image(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def store_file(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def delete_file(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def write_file(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def get_bucket_file_size(self):
        raise NotImplementedError("Subclasses should implement this method.")
    
    def copy_files(self):
        raise NotImplementedError("Subclasses should implement this method.")
    
    def delete_folder(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def move_folder(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def list_folders(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def list_files_with_extension(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def get_combined_csv_file(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def get_tech_netlist_data(self):
        raise NotImplementedError("Subclasses should implement this method.")
    
    def get_tech_netlist_list(self):
        raise NotImplementedError("Subclasses should implement this method.")
    
    def list_files(self):
        raise NotImplementedError("Subclasses should implement this method.")
    
    def fetch_files(self):
        raise NotImplementedError("Subclasses should implement this method.")
    
    def create_zip_files(self):
        raise NotImplementedError("Subclasses should implement this method.")
    
    def fetch_csv(self):
        raise NotImplementedError("Subclasses should implement this method.")
    
    def has_png_files(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def rename_file(self):
        raise NotImplementedError("Subclasses should implement this method.")
    
    def get_tech_netlist_data_migration(self):
        raise NotImplementedError("Subclasses should implement this method.")