from .base import StorageService
from boto3 import client as boto_client
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from concurrent.futures import ThreadPoolExecutor, as_completed
from os import walk, makedirs
from os.path import join, relpath, exists, basename
from shutil import rmtree
from ..config import configs

class S3Service(StorageService):
    def __init__(self):
        self.s3_client = boto_client(
            's3',
            aws_access_key_id=configs['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=configs['AWS_SECRET_ACCESS_KEY'],
            region_name=configs['AWS_S3_REGION_NAME']
        )
        if not self.check_connection():
            print('There isn\'t a valid S3 connection to the bucket.')
            exit(0)

    def check_connection(self):
        bucket_name = configs['AWS_STORAGE_BUCKET_NAME']
        try:
            # Use head_bucket to "ping" the bucket
            self.s3_client.head_bucket(Bucket=bucket_name)
            print(f"Connection to bucket '{bucket_name}' is ready.")
            return True
        except NoCredentialsError:
            print("S3 connection failed: No credentials provided.")
        except PartialCredentialsError:
            print("S3 connection failed: Incomplete credentials provided.")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                print(f"Bucket '{bucket_name}' does not exist.")
            elif error_code == '403':
                print(f"Access denied to bucket '{bucket_name}'.")
            else:
                print(f"Failed to connect to bucket '{bucket_name}': {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        return False
    
    def upload_file(self, file_path, s3_key):
        try:
            self.s3_client.upload_file(file_path, configs['AWS_STORAGE_BUCKET_NAME'], s3_key)
            return True
        except Exception as e:
            print(f"Failed to upload {file_path}: {e}")
            return False
    
    def upload_folder(self, local_folder_path, s3_prefix=""):
        files_to_upload = []
        for root, dirs, files in walk(local_folder_path):
            for file in files:
                file_path = join(root, file)
                s3_key = join(s3_prefix, relpath(file_path, local_folder_path))
                files_to_upload.append((file_path, s3_key))
        # Using ThreadPoolExecutor to parallelize the upload
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.upload_file, file_path, s3_key) for file_path, s3_key in files_to_upload]
            for future in as_completed(futures):
                try:
                    future.result()  # This will raise an exception if the upload failed
                except Exception as e:
                    print(f"Error occurred during upload: {e}")
    
    def download_folder(self, s3_folder_path, local_folder_path):
        if exists(local_folder_path):
            rmtree(local_folder_path)
        makedirs(local_folder_path)
        # List objects in the S3 folder
        response = self.s3_client.list_objects_v2(Bucket=configs['AWS_STORAGE_BUCKET_NAME'], Prefix=s3_folder_path)
        if 'Contents' in response:
            for obj in response['Contents']:
                s3_file_path = obj['Key']
                file_name = basename(s3_file_path)
                local_file_path = join(local_folder_path, file_name)
                # Download the file from S3 to the local path
                try:
                    self.s3_client.download_file(configs['AWS_STORAGE_BUCKET_NAME'], s3_file_path, local_file_path)
                except:
                    print('couldn\'t upload')