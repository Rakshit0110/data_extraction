import cv2
import json
import psycopg2
import os
import logging
from config import IMAGES_FOLDER, DB_CONFIG
from rapidfuzz import fuzz
from skimage.metrics import structural_similarity as ssim

# Logging setup
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "app.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def image_similarity(img1_path, img2_path):
    logging.info(f"Comparing input image with template: {img2_path}")
    img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)

    if img1 is None or img2 is None:
        logging.warning(f"Could not read images: {img1_path}, {img2_path}")
        return 0.0

    # Resize template to match input image
    try:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
    except Exception as e:
        logging.warning(f"Image resizing failed: {e}")
        return 0.0

    try:
        score, _ = ssim(img1, img2, full=True)
    except Exception as e:
        logging.error(f"SSIM comparison failed: {e}")
        return 0.0

    logging.info(f"SSIM score: {score:.2f}")
    return score

def find_best_match_and_json(input_image_path):
    logging.info(f"Processing input image: {input_image_path}")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("SELECT image_path, extraction_coordinates, template_name FROM test_1.templates")
    templates = cursor.fetchall()

    best_score = 0.0
    best_template = None
    best_coords = None
    best_template_name = None

    for template_path, extraction_coordinates, template_name in templates:
        score = image_similarity(input_image_path, template_path)
        logging.info(f"Score for {template_path}: {score:.2f}")
        if score > best_score:
            best_score = score
            best_template = template_path
            best_coords = extraction_coordinates
            best_template_name = template_name

    conn.close()

    if best_score < 0.9:
        logging.error("Model not matched.")
        return {"model": "untrained"}

    if best_coords:
        logging.info(f"Best match: {best_template} with score {best_score:.2f}")
        return {
            "template_name": best_template_name,
            "json": best_coords
        }

    return {"model": "untrained"}
