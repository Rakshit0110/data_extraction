from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from werkzeug.utils import secure_filename
import os, base64, cv2, psycopg2, json, numpy as np
from typing import Dict, List

from ocr_utils.image_ops import extract_pdf_image_from_bytes
from ocr_utils.file_ops import sanitize_filename
from ocr_utils.ocr_processor import extract_keys_from_rois

import fitz  # PyMuPDF

router = APIRouter()  # ✅ Use APIRouter here

# Ensure folders exist
os.makedirs("../templates/images", exist_ok=True)
os.makedirs("../templates/json_files", exist_ok=True)
os.makedirs("../templates/coordinates", exist_ok=True)


def get_next_serial():
    counter_file = "serial_counter.txt"
    if not os.path.exists(counter_file):
        with open(counter_file, "w") as f:
            f.write("0")
    with open(counter_file, "r") as f:
        current = int(f.read())
    with open(counter_file, "w") as f:
        f.write(str(current + 1))
    return f"{current + 1}"

def get_db_connection():
    return psycopg2.connect(
        dbname='test',
        user='postgres',
        password='tingri007',
        host='localhost',
        port='5432'
    )

class RoiData(BaseModel):
    rois: Dict[str, Dict[str, List[dict]]]
    filename: str
    template_name: str
    totalPages: int = 1  # Default to 1 since we're only handling the first page

# Endpoint to upload PDF and extract image from the first page only
@router.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...), action: str = Form(...)):
    if action not in ["training", "testing"]:
        raise HTTPException(status_code=400, detail="Invalid action")

    filename = secure_filename(file.filename)
    pdf_bytes = await file.read()
    template_name = get_next_serial()  # Generate a new template name

    try:
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # Only process the first page
        if len(pdf_document) > 0:
            page = pdf_document.load_page(0)  # Load only the first page
            pix = page.get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72))
            
            img_bytes = pix.tobytes("png")
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Save the image for training
            if action == "training":
                image_path = f"../templates/images/{template_name}_temp.png"
                cv2.imwrite(image_path, img)
                print(f"[upload_pdf] Saved temp image: {image_path}")
            
            _, encoded_img = cv2.imencode(".png", img)
            base64_image = base64.b64encode(encoded_img).decode("utf-8")
            
            return JSONResponse(content={
                "message": "PDF processed successfully",
                "images": [base64_image],  # Return as array for backward compatibility
                "filename": template_name
            })
        else:
            raise HTTPException(status_code=400, detail="PDF does not contain any pages")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

# Endpoint to save ROIs and coordinates to DB and files
@router.post("/save_rois")
async def save_rois(data: RoiData):
    rois = data.rois
    template_name = data.filename
    custom_template_name = data.template_name
    
    # Check if any ROIs were provided
    if not rois or not rois.get("0"):
        raise HTTPException(status_code=400, detail="No ROIs provided")
    
    # Extract single page ROIs from the structure (simplify from the multi-page format)
    page_rois = rois.get("0", {})
    
    if not page_rois or len(page_rois) == 0:
        raise HTTPException(status_code=400, detail="No ROIs defined")
    
    template_id = template_name  # Use serial name as ID
    
    # Load the image
    image_path = f"../templates/images/{template_name}_temp.png"

    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Template image not found")
    
    image = cv2.imread(image_path)
    if image is None:
        raise HTTPException(status_code=500, detail="Failed to load template image")
    
    # Extract keys from ROIs
    extracted_keys = extract_keys_from_rois(page_rois, image)
    print(f"[save_rois] Extracted keys: {extracted_keys}")
    
    # Save permanent image
    permanent_image_path = f"../templates/images/{template_name}.png"
    cv2.imwrite(permanent_image_path, image)
    print(f"[save_rois] Saved permanent image: {permanent_image_path}")
    
    # Save raw ROI JSON
    raw_json_path = f"../templates/json_files/{template_name}.json"
    with open(raw_json_path, "w") as f:
        json.dump(page_rois, f, indent=2)
    
    # Save extracted keys
    coord_json_path = f"../templates/coordinates/{template_name}_coordinates.json"
    with open(coord_json_path, "w") as f:
        json.dump(extracted_keys, f, indent=2)
    
    # Save to DB with custom template name
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(""" 
            INSERT INTO test.test_1.templates(id, template_name, image_path, drawn_coordinates, extraction_coordinates)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            template_id,
            custom_template_name,  # Use the user-provided template name
            permanent_image_path,
            json.dumps(page_rois),
            json.dumps(extracted_keys)
        ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"[save_rois] DB Error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cur.close()
        conn.close()
    
    # Clean up temp file
    try:
        if os.path.exists(image_path):
            os.remove(image_path)
            print(f"[save_rois] Removed temp image: {image_path}")
    except Exception as e:
        print(f"[save_rois] Warning: Error cleaning up temp file: {e}")
    
    return JSONResponse(content={
        "message": "Template saved successfully",
        "template_name": custom_template_name
    })

# Run the server
 