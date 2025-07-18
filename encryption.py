import base64
from cryptography.fernet import Fernet
import argparse
import os

def load_key_from_file(key_file_path: str) -> bytes:
    """Load a Fernet key from a .key file."""
    if not os.path.isfile(key_file_path):
        raise FileNotFoundError(f"Key file not found: {key_file_path}")
    with open(key_file_path, 'rb') as f:
        return f.read()

def encrypt_file(file_path: str, fernet: Fernet):
    """Encrypt a .py file and save it as .enc in the same location."""
    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'rb') as f:
        original_data = f.read()

    encrypted_data = fernet.encrypt(original_data)

    encrypted_file_path = file_path.replace(".py", ".enc")
    with open(encrypted_file_path, 'wb') as f:
        f.write(encrypted_data)

    print(f"Encrypted: {encrypted_file_path}")

def encrypt_all_py_in_folder(folder_path: str, fernet: Fernet):
    """Encrypt all .py files recursively in the given folder."""
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py") and not file.endswith(".enc.py"):
                full_path = os.path.join(root, file)
                encrypt_file(full_path, fernet)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Encrypt all .py files in a folder using an existing key.")
    parser.add_argument("folder", help="Path to the folder containing .py files")
    parser.add_argument("--keyfile", required=True, help="Path to the existing secret key file")
    args = parser.parse_args()

    try:
        key = load_key_from_file(args.keyfile)
        fernet = Fernet(key)
    except Exception as e:
        print(f"Failed to load or initialize key: {e}")
        exit(1)

    if not os.path.isdir(args.folder):
        print(f"Provided folder path is not a directory: {args.folder}")
        exit(1)

    encrypt_all_py_in_folder(args.folder, fernet)
