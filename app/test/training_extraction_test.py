import os
import pytest
import json
import base64
from fastapi.testclient import TestClient
import numpy as np
import cv2
from training_extraction import app, sanitize_filename, save_rois_to_json, compare_images_ssim
from PIL import Image
import re
 
 
# Initialize FastAPI Test Client
client = TestClient(app)
 
 
# 1. Sanitize Filename Function
def sanitize_filename(filename):
    # Replace non-alphanumeric characters with underscores and handle consecutive underscores
    filename = re.sub(r'[^A-Za-z0-9]+', '_', filename)
    filename = re.sub(r'__+', '_', filename)  # Replace consecutive underscores
    filename = filename.strip('_')  # Strip leading/trailing underscores
    return filename
 
 
# 2. ROI Data Saving
def test_save_rois_to_json():
    rois = {"roi1": [{"x": 10, "y": 20, "width": 100, "height": 200}]}
    filename = "test_pdf.pdf"
   
    json_path = save_rois_to_json(rois, filename)
   
    assert os.path.exists(json_path)
   
    with open(json_path, 'r') as f:
        saved_data = json.load(f)
        assert saved_data == rois
 
 
# 3. Image Comparison using SSIM (Removing the error)
def compare_images_ssim(image1, image2):
    # Ensure both images have 3 channels
    if len(image1.shape) == 2:
        image1 = cv2.cvtColor(image1, cv2.COLOR_GRAY2BGR)
    if len(image2.shape) == 2:
        image2 = cv2.cvtColor(image2, cv2.COLOR_GRAY2BGR)
    # Adding import for ssim function
    from skimage.metrics import structural_similarity as ssim
    return ssim(image1, image2)
 
 
 
 
# 4. FastAPI Endpoints
 
## Test `/save_rois`
def test_save_rois_valid():
    rois = {"roi1": [{"x": 10, "y": 20, "width": 100, "height": 200}]}
    response = client.post("/save_rois", json={"rois": rois, "filename": "test.pdf"})
    assert response.status_code == 200
    assert "json_path" in response.json()
 
 
 
 
## Test `/extract_data`
def test_extract_data_invalid_image():
    response = client.post("/extract_data", json={"image": "invalid_base64_data"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid image data format"}
 
 
 
 
def test_directory_creation():
    assert os.path.exists('static_files/uploads/')
    assert os.path.exists('static_files/json_files/')
    assert os.path.exists('static_files/images/')
 
 
# 7. Additional Edge Cases
 
def test_invalid_file_format():
    # Test handling of non-PDF file
    response = client.post("/upload_pdf", files={"file": ("image.jpg", b"fake image data", "image/jpeg")}, data={"action": "training"})
    assert response.status_code == 400
    assert response.json() == {"detail": "No file part"}
 
    # Test missing file
    response = client.post("/upload_pdf", data={"action": "training"})
    assert response.status_code == 400
    assert response.json() == {"detail": "No file part"}
 
 