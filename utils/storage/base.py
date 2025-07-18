class StorageService:
    def __init__(self):
        pass

    def check_connection(self):
        raise NotImplementedError("Subclasses should implement this method.")
    
    def upload_file(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def upload_folder(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def download_folder(self):
        raise NotImplementedError("Subclasses should implement this method.")