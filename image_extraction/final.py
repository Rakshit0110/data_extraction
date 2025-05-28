import os
import cv2
import base64
import numpy as np
import psycopg2
import io
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from skimage.metrics import structural_similarity as ssim

app = FastAPI()

# Tesseract config
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Ensure required folders exist
os.makedirs("static_files/images", exist_ok=True)
os.makedirs("static_files/op_images", exist_ok=True)

# --- DB Connection ---
def get_db_connection():
    return psycopg2.connect(
        dbname='test',
        user='postgres',
        password='tingri007',
        host='localhost',
        port='5432'
    )

# --- SSIM Comparison ---
def compare_images_ssim(img1, img2):
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    if gray1.shape != gray2.shape:
        gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))

    score, _ = ssim(gray1, gray2, full=True)
    return score

# --- Template Detection ---
def detect_best_template(image_cv, image_folder="static_files/images", threshold=0.9):
    best_match_score = -1
    best_match_image_name = None

    for img_name in os.listdir(image_folder):
        img_path = os.path.join(image_folder, img_name)
        saved_img_cv = cv2.imread(img_path)
        if saved_img_cv is None:
            continue

        score = compare_images_ssim(image_cv, saved_img_cv)
        if score > best_match_score:
            best_match_score = score
            best_match_image_name = img_name

    if best_match_score < threshold:
        raise HTTPException(status_code=400, detail="Template not trained. Match score is too low.")

    return best_match_image_name, best_match_score

# --- Fetch Coordinates from DB ---
def get_coordinates_from_db(image_filename):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT template_name, extraction_coordinates
        FROM test.test_1.templates
        WHERE image_path LIKE %s
    """, (f"%{image_filename}",))

    result = cur.fetchone()
    conn.close()

    if result is None:
        raise HTTPException(status_code=404, detail="Matching template not found in database.")

    template_name, extraction_coordinates = result
    return template_name, extraction_coordinates

# --- Convert PDF to Image ---
def convert_pdf_to_image(pdf_path, dpi=300):
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72))
    img_bytes = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_bytes))
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    return img_cv, img

# --- Upload Endpoint: Returns Coordinates Only ---
@app.post("/uploads_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    filename = file.filename
    file_path = f"static_files/images/{filename}"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        image_cv, _ = convert_pdf_to_image(file_path)
    else:
        image_cv = cv2.imread(file_path)
        if image_cv is None:
            raise HTTPException(status_code=400, detail="Uploaded image could not be read")

    # Find the best matching template
    matched_filename, _ = detect_best_template(image_cv)

    # Fetch coordinates from database
    template_name, extraction_coords = get_coordinates_from_db(matched_filename)

    return JSONResponse(content={
        "message": "Image uploaded and template matched",
        "template_used": template_name,
        "coordinates": extraction_coords
    })
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=True)
