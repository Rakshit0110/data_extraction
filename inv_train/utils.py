import os
import json
import shutil

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def save_output_files(pdf_path, final_json, output_dir, logger):
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    pdf_dest = os.path.join(output_dir, f"{base_name}.pdf")
    json_dest = os.path.join(output_dir, f"{base_name}.json")

    shutil.copy(pdf_path, pdf_dest)
    with open(json_dest, "w") as f:
        json.dump(final_json, f, indent=4)

    logger.info(f"Saved PDF to {pdf_dest}")
    logger.info(f"Saved JSON to {json_dest}")
