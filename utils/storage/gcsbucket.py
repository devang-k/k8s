from google.cloud import storage
from ..config import configs
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from shutil import rmtree
from os.path import exists

class GCSBucketService:
    def __init__(self):
        self.client = storage.Client()
        self.bucket = self.client.get_bucket(configs.get('GOOGLE_STORAGE_BUCKET_NAME'))
        
        if not self.check_connection():
            raise ConnectionError("GCS connection failed.")
        
    def check_connection(self):
        """
        Check if connection to the configured GCS bucket is successful.
        """
        try:
            # Attempt to get bucket metadata to validate the connection
            self.bucket.reload()
            print(f"Connection to GCS bucket '{self.bucket.name}' is ready.")
            return True
        except Exception as e:
            print(f"Failed to connect to GCS bucket '{self.bucket.name}': {e}")
            return False

    def upload_file(self, file_path, gcs_blob_path):
        """Uploads a file to the bucket."""
        try:
            blob = self.bucket.blob(gcs_blob_path)
            blob.upload_from_filename(file_path)
            print(f"Uploaded {file_path} to GCS at {gcs_blob_path}")
            return True
        except Exception as e:
            print(f"Failed to upload {file_path} to GCS: {e}")
            return False
        
    def upload_folder(self, local_folder_path, gcs_prefix=""):
        """
        Uploads all files in a local folder to a GCS bucket, preserving the folder structure.

        :param local_folder_path: Path to the local folder to upload
        :param gcs_prefix: Optional prefix path inside the GCS bucket
        """
        files_to_upload = []

        for root, dirs, files in os.walk(local_folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Relative path from the base folder
                rel_path = os.path.relpath(file_path, local_folder_path)
                gcs_blob_path = os.path.join(gcs_prefix, rel_path).replace("\\", "/")  # Ensure GCS-friendly path
                files_to_upload.append((file_path, gcs_blob_path))

        # Use ThreadPoolExecutor to parallelize uploads
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.upload_file, file_path, gcs_blob_path) for file_path, gcs_blob_path in files_to_upload]

            for future in as_completed(futures):
                try:
                    future.result()  # Raises exception if any occurred during upload
                except Exception as e:
                    print(f"Error occurred during upload: {e}")
                    

    def download_folder(self, gcs_folder_path, local_folder_path):
        """
        Downloads all files from a GCS folder to a local directory.

        :param gcs_folder_path: GCS prefix (folder path)
        :param local_folder_path: Local directory where files will be saved
        """
        if exists(local_folder_path):
            rmtree(local_folder_path)
        os.makedirs(local_folder_path)

        blobs = self.bucket.list_blobs(prefix=gcs_folder_path)

        for blob in blobs:
            if blob.name.endswith('/'):
                continue  # Skip folders (GCS is flat, but '/' is used as delimiter)
            try:
                file_name = os.path.basename(blob.name)
                local_file_path = os.path.join(local_folder_path, file_name)
                blob.download_to_filename(local_file_path)
                print(f"Downloaded {blob.name} to {local_file_path}")
            except Exception as e:
                print(f"Couldn't download {blob.name}: {e}")
