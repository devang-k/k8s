import json

def write_to_json(output_file, data):
    with open(output_file, "w") as f:
        json.dump(data, f)
