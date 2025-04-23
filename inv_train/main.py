from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from extract_keys import extract_key_texts
from detect import process_json, save_files
from utils import load_config
from logger import setup_logger
import shutil
import os
import json

app = FastAPI()

config = load_config()
logger = setup_logger(config["log_file"])

@app.post("/save-template")
async def save_template(
    pdf_file: UploadFile = File(...),
    json_data: str = Form(...)
):
    try:
        # Save uploaded PDF
        pdf_path = os.path.join("temp", pdf_file.filename)
        os.makedirs("temp", exist_ok=True)
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(pdf_file.file, buffer)

        # Save JSON coordinates
        coordinates = json.loads(json_data)
        json_path = os.path.join("temp", "input_coords.json")
        with open(json_path, "w") as f:
            json.dump(coordinates, f)

        logger.info("Extracting keys from PDF.")
        key_texts = extract_key_texts(pdf_path, json_path, logger)

        logger.debug("Extracted key_texts:")
        for k, v in key_texts.items():
            logger.debug(f"  {k} → {v}")

        logger.info("Generating template data.")
        final_json = process_json(json_path, logger)

        logger.debug("Before replacement:")
        for k in final_json:
            logger.debug(f"  {k}: key = {final_json[k].get('key', None)}")

        # ✅ Inject extracted text only if 'key' field is missing
        for item_key in final_json:
            normalized_key = f"{item_key.strip()} KEY"
            extracted_key = key_texts.get(normalized_key)

            if extracted_key and "key" not in final_json[item_key]:
                logger.info(f"Setting final_json['{item_key}']['key'] = '{extracted_key}'")
                final_json[item_key]["key"] = extracted_key
            elif not extracted_key:
                logger.warning(f"No extracted key text for: '{normalized_key}'")
            else:
                logger.debug(f"Key already exists for: '{item_key}' — skipping replacement.")

        logger.debug("After replacement:")
        for k in final_json:
            logger.debug(f"  {k}: key = {final_json[k]['key']}")

        logger.info("Saving outputs.")
        save_files(pdf_path, final_json, config, logger)

        return JSONResponse(content={"message": "Template saved successfully."})

    except Exception as e:
        logger.error(f"Error in /save-template: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
