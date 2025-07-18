import sys
import os

def extract_imports_from_file(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    import_lines = []
    code_lines = []

    with open(file_path, "r") as f:
        for line in f:
            if line.strip().startswith("import") or line.strip().startswith("from"):
                import_lines.append(line)
            else:
                code_lines.append(line)

    import_file = file_path.replace(".py", "_import.py")

    with open(import_file, "w") as f:
        f.writelines(import_lines)

    with open(file_path, "w") as f:
        f.writelines(code_lines)

    print(f"Extracted imports to '{import_file}'")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_imports.py file1.py file2.py ...")
    else:
        for path in sys.argv[1:]:
            extract_imports_from_file(path)
