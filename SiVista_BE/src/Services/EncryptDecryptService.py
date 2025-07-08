from SiVista_BE.settings import FileEncryptionKey
from cryptography.fernet import Fernet, InvalidToken

def encrypt_file_content(file_bytes):
    file_bytes = file_bytes.encode('utf-8')
    fernet = Fernet(FileEncryptionKey)
    return fernet.encrypt(file_bytes)

def decrypt_file_content(encrypted_bytes):
    fernet = Fernet(FileEncryptionKey)
    return fernet.decrypt(encrypted_bytes).decode('utf-8')