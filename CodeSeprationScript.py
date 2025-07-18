import os
import argparse
import shutil
import base64
import secrets
from cryptography.fernet import Fernet

def delete_files_by_name(file_names: list, root_dir: str):
    """Search and delete all matching filenames recursively from root_dir."""
    deleted = 0
    for dirpath, _, filenames in os.walk(root_dir):
        for file in filenames:
            if file in file_names:
                full_path = os.path.join(dirpath, file)
                try:
                    os.remove(full_path)
                    deleted += 1
                    print(f"Deleted: {full_path}")
                except Exception as e:
                    print(f"Failed to delete {full_path}: {e}")
    if deleted == 0:
        print("No matching files found.")
def load_key_from_file(key_file_path: str) -> bytes:
    """Load a Fernet key from a .key file."""
    if not os.path.isfile(key_file_path):
        raise FileNotFoundError(f"Key file not found: {key_file_path}")
    with open(key_file_path, 'rb') as f:
        return f.read()

def extract_imports_from_file(file_path: str) -> list:
    """Extract import lines from a given Python file."""
    imports = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                imports.append(stripped)
    print(imports)
    return imports

def save_imports(imports: list, output_path: str):
    """Save the extracted imports to the given file path."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(imports))
def remove_imports_from_file(file_path: str, imports: list):
    """Remove the specified import lines from the original file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Remove matching import lines
        new_lines = [
            line for line in lines
            if not any(line.strip() == imp for imp in imports)
        ]

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        print(f"Removed imports from: {file_path}")
    except Exception as e:
        print(f"Error removing imports from {file_path}: {e}")
        
def extract_imports_to_mirrored_structure(root_dir: str, output_base: str):
    """Extract imports from each .py file, save them, and remove them from original files."""
    count = 0
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.py'):
                source_path = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(source_path, root_dir)
                output_path = os.path.join(output_base, rel_path)
                imports = extract_imports_from_file(source_path)
                if not imports:
                    print(f"No imports found in {source_path}. Skipping...")
                    continue
                
                # Save only if there are actual imports
                save_imports(imports, output_path)
                if os.path.exists(output_path) and os.path.getsize(output_path) == 0:
                    os.remove(output_path)
                    print(f"Removed empty import file: {output_path}")
                remove_imports_from_file(source_path, imports)
                count += 1
                print(f"✔ Processed: {source_path}")

def encrypt_file(file_path: str, fernet: Fernet) -> str:
    """Encrypt a .py file and return the encrypted file path."""
    with open(file_path, 'rb') as f:
        original_data = f.read()

    encrypted_data = fernet.encrypt(original_data)
    encrypted_path = os.path.splitext(file_path)[0] + '.enc'

    with open(encrypted_path, 'wb') as f:
        f.write(encrypted_data)

    print(f"Encrypted: {file_path} → {encrypted_path}")
    return encrypted_path

def encrypt_py_files_in_directory(root_dir: str, fernet: Fernet) -> list:
    """Encrypt eligible .py files and return list of .enc paths."""
    encrypted_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".py") and filename != "__init__.py" and not filename.endswith("import.py"):
                file_path = os.path.join(dirpath, filename)
                try:
                    enc_path = encrypt_file(file_path, fernet)
                    encrypted_files.append(enc_path)
                except Exception as e:
                    print(f"Failed to encrypt {file_path}: {e}")
    return encrypted_files

def move_enc_files_with_structure(enc_files: list, source_root: str, target_root: str):
    """Move .enc files to shared_memory, preserving directory structure."""
    moved_count = 0
    for enc_path in enc_files:
        rel_path = os.path.relpath(enc_path, source_root)
        target_path = os.path.join(target_root, rel_path)

        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        try:
            shutil.move(enc_path, target_path)
            moved_count += 1
        except Exception as e:
            print(f"Failed to move {enc_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Extract imports, encrypt .py files, and move .enc files.")
    parser.add_argument("--root-dir", required=True, help="Root directory to process .py files")
    parser.add_argument("--keyfile", required=True, help="Path to Fernet secret key file")
    parser.add_argument("--import-dir", default="stdcell_generation_imports", help="Directory to store extracted import files")
    parser.add_argument("--target-dir", default="stdcell_generation_shared", help="Directory to move encrypted files")
    args = parser.parse_args()

    files_to_delete = [
        "net_util.py",
        "signal_router.py",
        "grid.py",
        "data_types.py",
        "extrema.py"
    ]
    print("[0] Deleting specified files from root directory...")
    delete_files_by_name(files_to_delete, args.root_dir)
    
    if not os.path.exists(args.keyfile):
        key = base64.urlsafe_b64encode(secrets.token_bytes(32))
        with open(args.keyfile, "wb") as f:
            f.write(key)
        print(f"New key generated and saved to {args.keyfile}")
        print(f"Key: {key.decode()}")

    # Load Fernet key
    try:
        key = load_key_from_file(args.keyfile)
        fernet = Fernet(key)
    except Exception as e:
        print(f"Error loading Fernet key: {e}")
        return
    
    print("\n[1] Extracting imports...")
    extract_imports_to_mirrored_structure(args.root_dir, args.import_dir)

    print("\n[2] Encrypting .py files...")
    enc_files = encrypt_py_files_in_directory(args.root_dir, fernet)

    print("\n[3] Moving encrypted files to shared memory...")
    move_enc_files_with_structure(enc_files, args.root_dir, args.target_dir)

if __name__ == "__main__":
    main()
# execute inside SiVista Directory   
# python CodeSeprationScript.py --root-dir stdcell_generation_shared_working --keyfile secret.key 
