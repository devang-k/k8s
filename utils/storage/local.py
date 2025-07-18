from .base import StorageService
import shutil
import os
from ..config import local_file_configs

class LocalFileService(StorageService):
    def __init__(self):
        self.base_directory = local_file_configs['base_path']
        if not self.check_connection():
            print('Target folder doesn\'t exist.')
            exit(0)
    
    def check_connection(self):
        return os.path.isdir(self.base_directory)
    
    def upload_file(self, file_path, relative_target_path):
        target_path = os.path.join(self.base_directory, relative_target_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        shutil.copy(file_path, target_path)
        return True

    def upload_folder(self, folder_path, target_base):
        target_path = os.path.join(self.base_directory, target_base)
        os.makedirs(target_path, exist_ok=True)
        shutil.copytree(folder_path, target_path, dirs_exist_ok=True)

    def download_folder(self, remote_folder_path, local_folder_path):
        remote_folder_path = os.path.join(self.base_directory, remote_folder_path)
        if not os.path.exists(remote_folder_path):
            print(f"Remote folder does not exist: {remote_folder_path}")
            return
        if not os.path.exists(local_folder_path):
            os.makedirs(local_folder_path, exist_ok=True)
        shutil.copytree(remote_folder_path, local_folder_path, dirs_exist_ok=True)