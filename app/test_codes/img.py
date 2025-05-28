
import pytesseract
import cv2
import re
import json
import unicodedata
import logging
import os

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_image(image_path):
    image = cv2.imread(image_path)
    return image

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
    gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 31, 2)
    return gray

def ocr_image_text(image):
    custom_config = r'--psm 6'
    text = pytesseract.image_to_string(image, config=custom_config)
    text = unicodedata.normalize('NFC', text)
    text = re.sub(r'\s+', ' ', text)  # Normalize spaces
    return text

def extract_fields_from_text(text, fields_config):
    results = {}
    for key, cfg in fields_config.items():
        pattern = cfg.get('regex')
        if pattern:
            match = re.search(pattern, text, re.IGNORECASE)
            results[key.lower().replace(" ", "_")] = match.group(1).strip() if match else "Not found"
            logging.info(f"{key}: {results[key.lower().replace(' ', '_')]}")
        else:
            results[key.lower().replace(" ", "_")] = "No regex provided"
    return results

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

if __name__ == "__main__":
    image_path = "unit.png"
    json_path = "img.json"
    output_dir = "op_json"
    os.makedirs(output_dir, exist_ok=True)

    image = load_image(image_path)
    preprocessed_img = preprocess_image(image)
    full_text = ocr_image_text(preprocessed_img)
    config_data = load_json(json_path)

    extracted_data = extract_fields_from_text(full_text, config_data)

    output_path = os.path.join(output_dir, 'op.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, indent=4)

    logging.info(f"Extraction complete. Output saved to {output_path}")
