import base64
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
import tempfile
import shutil
import os
from services.image_processor import convert_to_image_if_needed
from services.matcher import find_best_match_and_json
from services.extractor import extract_data

router = APIRouter()

@router.post("/extract")
async def extract_from_file(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        file_path = tmp.name

    input_image = convert_to_image_if_needed(file_path)
    result = find_best_match_and_json(input_image)

    if result.get("model") == "untrained":
        return {"message": "model not trained"}

    extracted = extract_data(input_image, result["json"])
    return {
        "matched_template": result["template_name"],
        "extracted_data": extracted,
        "image_url": "/image"  # This is the endpoint to get the image
    }

@router.get("/image")
def get_annotated_image():
    image_path = "OP/output_key_val_boxes.jpg"  # Path to your image

    try:
        # Open the image and encode it to base64
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

        return JSONResponse(content={"image_data": encoded_image})
    
    except FileNotFoundError:
        return JSONResponse(content={"error": "Image not found"}, status_code=404)
