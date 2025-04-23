import pytesseract
from PIL import Image
import json
import re
import cv2
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Optional: set tesseract path (modify if needed)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def load_json(file_path):
    logging.info(f"Loading JSON file from {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def preprocess_image(image_path):
    logging.info(f"Preprocessing image: {image_path}")
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Improve contrast
    gray = cv2.equalizeHist(gray)
    
    # Adaptive thresholding
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    # Denoise image
    blur = cv2.GaussianBlur(thresh, (5, 5), 0)
    
    return blur

def extract_text_from_image(image_path, search_key, direction, distance, size, approach, regex=None):
    logging.debug(f"Extracting text for key: {search_key}")
    img = preprocess_image(image_path)
    
    custom_config = r'--oem 3 --psm 6'
    ocr_data = pytesseract.image_to_data(img, config=custom_config, output_type=pytesseract.Output.DICT)
    
    key_boxes = []
    results = []
    full_words = []
    
    for i in range(len(ocr_data["text"])):
        word = ocr_data["text"][i].strip()
        if not word:
            continue
        try:
            conf = int(ocr_data["conf"][i])
        except:
            conf = 0
        if conf > 60:
            full_words.append({
                "text": word,
                "x": ocr_data["left"][i],
                "y": ocr_data["top"][i],
                "w": ocr_data["width"][i],
                "h": ocr_data["height"][i],
                "conf": conf
            })
    
    logging.debug(f"Total words detected: {len(full_words)}")
    
    for i in range(len(full_words)):
        if full_words[i]["text"].lower() == search_key.lower():
            key_boxes.append(full_words[i])
            break
    
    logging.debug(f"Key boxes found: {len(key_boxes)}")
    
    for box in key_boxes:
        x0, y0, w, h = box["x"], box["y"], box["w"], box["h"]
        x1, y1 = x0 + w, y0 + h
        
        for word in full_words:
            wx, wy, ww, wh = word["x"], word["y"], word["w"], word["h"]
            match = False
            
            if direction == "Right" and wx > x1 and abs(wy - y0) < 25 and wx - x1 <= distance:
                match = True
            elif direction == "Left" and x0 > (wx + ww) and abs(wy - y0) < 25 and x0 - (wx + ww) <= distance:
                match = True
            elif direction == "Down" and wy > y1 and wy - y1 <= distance and abs(wx - x0) < 25:
                match = True
            elif direction == "Up" and y0 > (wy + wh) and y0 - (wy + wh) <= distance and abs(wx - x0) < 25:
                match = True
            
            if match:
                results.append(word["text"])
    
    text = " ".join(results).strip()
    
    if regex:
        matched = re.findall(regex, text.replace(" ", ""))
        text = "\n".join(matched) if matched else "No match found"
    
    logging.info(f"Extracted text for {search_key}: {text}")
    return text

def extract_key_values(image_path, json_path):
    data = load_json(json_path)
    final_data = {}
    
    for key, value in data.items():
        search_key = value["key"]
        direction = value["Direction"]
        distance = value["Distance"]
        size = value["size"]
        approach = value["Approach"]
        regex = value.get("regex", None)
        
        extracted_text = extract_text_from_image(image_path, search_key, direction, distance, size, approach, regex)
        final_data[search_key] = extracted_text
    
    return final_data

# Set your paths
image_path = "../sample_invoices/unit4/unit.png"
json_path = "parser_json/unit.json"

# Extract data
logging.info("Starting text extraction process...")
final_data = extract_key_values(image_path, json_path)

# Save output
output_file = 'op_json/final_key_val_from_image.json'
with open(output_file, 'w') as json_file:
    json.dump(final_data, json_file, indent=4)

logging.info(f"✅ Final extracted data saved to {output_file}")
