import json
import math
import logging
import os
import shutil



def calculate_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def calculate_direction(x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if dx == 0:
        return "Down" if dy > 0 else "Up"
    angle = math.degrees(math.atan2(dy, dx))
    if -45 <= angle < 45:
        return "Right"
    if 45 <= angle < 135:
        return "Down"
    if -135 <= angle < -45:
        return "Up"
    return "Left"

def determine_approach(y):
    return "Top" if y < 2000 else "Down"

def add_regex_field(name):
    upper = name.upper()
    if "TVA" in upper:
        return "^.{11}"
    if "BIC" in upper or "SWIFT" in upper:
        return "^.{8}"
    return None



def process_json(json_path, logger):
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)

        output = {}

        for key in data:
            if key.endswith("KEY"):
                base = key.replace(" KEY", "").strip()
                val_key = key.replace("KEY", "VAL").strip()

                if val_key in data:
                    k = data[key][0]
                    v = data[val_key][0]

                    output[base] = {
                        # 'key' is intentionally omitted to be filled by main.py
                        "Distance": round(calculate_distance(k["x"], k["y"], v["x"], v["y"]), 2),
                        "Direction": calculate_direction(k["x"], k["y"], v["x"], v["y"]),
                        "Approach": determine_approach(k["y"]),
                        "Size": "single line"
                    }

                    regex = add_regex_field(base)
                    if regex:
                        output[base]["regex"] = regex

        # Handle standalone fields like ADDRESS or NAME
        for key in data:
            upper_label = key.upper()
            if any(x in upper_label for x in ["ADDRESS", "NAME"]) and key not in output:
                y = data[key][0]["y"]
                label_name = key.strip()

                output[label_name] = {
                    "key": label_name,
                    "Approach": determine_approach(y),
                    "Size": "multi line" if "ADDRESS" in upper_label else "single line"
                }

        logger.info("Processed relationships and generated final template.")
        return output

    except Exception as e:
        logger.error(f"Error processing JSON: {e}")
        return {}


def save_files(pdf_path, output_json, config, logger):
    try:
        base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
        json_output_dir = config["json_output_dir"]
        pdf_output_dir = config["pdf_output_dir"]

        os.makedirs(json_output_dir, exist_ok=True)
        os.makedirs(pdf_output_dir, exist_ok=True)

        json_output_path = os.path.join(json_output_dir, f"{base_filename}.json")
        pdf_output_path = os.path.join(pdf_output_dir, f"{base_filename}.pdf")

        with open(json_output_path, 'w') as json_file:
            json.dump(output_json, json_file, indent=4)

        shutil.copy(pdf_path, pdf_output_path)

        logger.info(f"Saved PDF → {pdf_output_path}")
        logger.info(f"Saved JSON → {json_output_path}")

    except Exception as e:
        logger.error(f"Error saving files: {e}")
