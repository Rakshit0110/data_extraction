import os
import json
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pytesseract
from PIL import Image
import io
import base64
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
import logging
from skimage.metrics import structural_similarity as ssim  # Import SSIM
import re

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for all routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Directory for saving files and templates
UPLOAD_FOLDER = 'static_files/uploads/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Create separate folders for json files and images
JSON_FOLDER = 'static_files/json_files/'
os.makedirs(JSON_FOLDER, exist_ok=True)

IMAGES_FOLDER = 'static_files/images/'
os.makedirs(IMAGES_FOLDER, exist_ok=True)


# Function to extract images from PDF
def extract_pdf_image(pdf_path, dpi=300):
    doc = fitz.open(pdf_path)
    # Extract the first page
    page = doc.load_page(0)
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72))  # Convert to high resolution image
    img_bytes = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_bytes))

    # Convert the image to an OpenCV format (BGR)
    img_cv = np.array(img)
    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)

    return img_cv

# Function to save ROI data to JSON
def save_rois_to_json(rois, filename):
    json_filename = os.path.splitext(filename)[0] + '.json'  # Add _rois suffix
    json_path = os.path.join(JSON_FOLDER, json_filename)

    with open(json_path, 'w') as f:
        json.dump(rois, f)

    return json_path

def sanitize_filename(filename: str) -> str:
    # Replace spaces and special characters with underscores
    sanitized_filename = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
    return sanitized_filename

# Function to compare images using SSIM
def compare_images_ssim(image1, image2):
    # Convert both images to grayscale
    gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

    # Resize images to the same shape (if necessary)
    if gray1.shape != gray2.shape:
        gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))

    # Calculate SSIM between the two images
    score, _ = ssim(gray1, gray2, full=True)
    return score


class RoiData(BaseModel):
    rois: dict
    filename: str


# Endpoint to upload PDF, convert it to image, and get the base64 image
@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...), action: str = Form(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file part")

    if action not in ["training", "testing"]:
        raise HTTPException(status_code=400, detail="Invalid action")

    filename = secure_filename(file.filename)
    sanitized_filename = sanitize_filename(filename)  # Sanitize the filename
    pdf_path = os.path.join(UPLOAD_FOLDER, sanitized_filename)
    
    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    # Extract the image using OpenCV
    img_cv = extract_pdf_image(pdf_path, dpi=300)

    # Case for "training" action: Save the PDF and return the base64 encoded image
    if action == 'training':
        image_filename = os.path.splitext(sanitized_filename)[0] + '.png'  # Save image as PNG
        image_path = os.path.join(IMAGES_FOLDER, image_filename)
        cv2.imwrite(image_path, img_cv)

        # Convert the saved image to base64 after saving
        _, img_encoded = cv2.imencode('.png', img_cv)
        img_base64 = base64.b64encode(img_encoded).decode('utf-8')

        return JSONResponse(content={'message': 'PDF saved successfully', 'image': img_base64})

    # Case for "testing" action: Convert to base64 and send the response
    elif action == 'testing':
        _, img_encoded = cv2.imencode('.png', img_cv)
        img_base64 = base64.b64encode(img_encoded).decode('utf-8')
        return JSONResponse(content={'image': img_base64})

    raise HTTPException(status_code=400, detail="Invalid action")

# Modify saving ROIs function to sanitize filenames as well
@app.post("/save_rois")
async def save_rois(data: RoiData):
    try:
        rois = data.rois  # List of ROI coordinates from the frontend
        filename = data.filename  # Get the filename for saving ROIs

        if not rois:
            raise HTTPException(status_code=400, detail="No ROIs provided")

        if not filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        sanitized_filename = sanitize_filename(filename)  # Sanitize the filename
        # Save the ROIs to a new JSON file in the json_files folder
        json_path = save_rois_to_json(rois, sanitized_filename)

        logging.info(f"ROIs saved successfully to {json_path}")
        return JSONResponse(content={'message': 'ROIs saved successfully', 'json_path': json_path})

    except Exception as e:
        logging.error(f"Error saving ROIs: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving ROIs: {e}")
    
    
    
    # Function to extract image from PDF for OCR processing
def extract_image_from_pdf(pdf_file_path):
    doc = fitz.open(pdf_file_path)
    page = doc[0]  # Get the first page
    pix = page.get_pixmap()  # Render the page as an image (pixmap)
    img_bytes = pix.tobytes()  # Get image bytes

    # Convert bytes to PIL Image
    image = Image.open(io.BytesIO(img_bytes))

    return image

# class ImageRequest(BaseModel):
#     image: str 

# Endpoint to extract data from the PDF using ROIs and OCR
# @app.post("/extract_data")
# Endpoint to extract data from the PDF using ROIs and OCR
class ImageData(BaseModel):
    image: str 

@app.post("/extract_data")
async def extract_data(data: ImageData):
    image = data.image  # Receive base64 image string directly

    if not image.startswith("data:image"):
        raise HTTPException(status_code=400, detail="Invalid image data format")

    # Decode the base64 image data (strip off the metadata part)
    image_data = image.split(",")[1]  # Get the part after the comma
    image_data = base64.b64decode(image_data)

    # Convert to a numpy array and decode the image using OpenCV
    np_image = np.frombuffer(image_data, dtype=np.uint8)
    img_cv = cv2.imdecode(np_image, cv2.IMREAD_COLOR)

    if img_cv is None:
        raise HTTPException(status_code=400, detail="Failed to decode image")

    # Compare the uploaded image with all images in the 'images' folder using SSIM
    best_match_score = -1
    best_match_image = None
    best_match_image_name = None

    for img_name in os.listdir(IMAGES_FOLDER):
        img_path = os.path.join(IMAGES_FOLDER, img_name)
        saved_img_cv = cv2.imread(img_path)

        score = compare_images_ssim(img_cv, saved_img_cv)
        if score > best_match_score:
            best_match_score = score
            best_match_image = saved_img_cv
            best_match_image_name = img_name

    # If the best match score is below 0.86, return an error
    if best_match_score < 0.9:
        raise HTTPException(status_code=400, detail="Template not trained. Match score is too low.")

    # Get the corresponding JSON file for ROIs
    json_filename = os.path.splitext(best_match_image_name)[0] + ".json"
    json_path = os.path.join(JSON_FOLDER, json_filename)

    if not os.path.exists(json_path):
        raise HTTPException(status_code=400, detail="No corresponding data found for data extraction from this template.")

    with open(json_path, "r") as json_file:
        roi_data = json.load(json_file)

    extracted_data = {}

    # Extract data from the uploaded image using the matched ROIs
    for key, roi_list in roi_data.items():
        for roi in roi_list:
            x, y, width, height = int(roi['x']), int(roi['y']), int(roi['width']), int(roi['height'])

            # Crop the image based on the ROI using OpenCV
            roi_image = img_cv[y:y + height, x:x + width]

            # Perform OCR on the cropped image using Tesseract
            extracted_text = pytesseract.image_to_string(roi_image, config='--psm 6')  # Page segmentation mode 6
            extracted_data[key] = {"text": extracted_text.strip(), "roi": roi}

    return JSONResponse(content=extracted_data)
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=5000)

# To run the FastAPI app with Uvicorn:
# uvicorn app_name:app --reload uvicorn main:app --reload
