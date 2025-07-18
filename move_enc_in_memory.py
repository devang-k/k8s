import os
import shutil

def move_enc_files_with_structure(source_dir, target_root):
    # Walk through all subdirectories
    for root, dirs, files in os.walk(source_dir):
        for filename in files:
            if filename.endswith(".enc"):
                source_path = os.path.join(root, filename)

                # Get the relative path from source_dir
                rel_path = os.path.relpath(root, source_dir)
                target_dir = os.path.join(target_root, rel_path)
                os.makedirs(target_dir, exist_ok=True)

                target_path = os.path.join(target_dir, filename)

                try:
                    shutil.move(source_path, target_path)
                    print(f"Moved: {source_path} → {target_path}")
                except Exception as e:
                    print(f"Failed to move {source_path}: {e}")

if __name__ == "__main__":
    # Set your source and target directories here
    SOURCE_DIR = "stdcell_generation_shared"  # starting from current directory
    TARGET_DIR = "shared_memory"

    move_enc_files_with_structure(SOURCE_DIR, TARGET_DIR)
