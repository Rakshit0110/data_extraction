import json
import os
import logging

def load_json_data(folder_path):
    json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    data = {}

    for file in json_files:
        file_path = os.path.join(folder_path, file)
        try:
            with open(file_path, "r") as f:
                data[os.path.basename(file)] = json.load(f)  # 🔁 FIXED
        except Exception as e:
            logging.error(f"Error reading {file}: {e}")

    return data
