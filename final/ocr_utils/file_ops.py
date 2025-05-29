import os
import json
import re

def sanitize_filename(filename: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)

def save_json(data: dict, path: str):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
