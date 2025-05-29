import pytesseract
from PIL import Image
import cv2
import re
import json
import unicodedata
import logging
import numpy as np

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def load_image(image_path):
    image = cv2.imread(image_path)
    return image

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)
    thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)
    return thresh

def extract_text_with_ocr(image, search_key, direction, distance, size, regex=None):
    preprocessed_img = preprocess_image(image)
    d = pytesseract.image_to_data(preprocessed_img, output_type=pytesseract.Output.DICT)

    full_text = []
    coords = []

    for i in range(len(d['text'])):
        word = d['text'][i].strip()
        if word:
            full_text.append(word)
            coords.append({
                'text': word,
                'left': d['left'][i],
                'top': d['top'][i],
                'width': d['width'][i],
                'height': d['height'][i]
            })

    joined_text = ' '.join(full_text)
    search_key_normalized = re.sub(r'\s+', '', search_key.lower())
    word_indices = []

    # Match whole key phrase
    for i in range(len(coords)):
        for j in range(i+1, min(i+6, len(coords))+1):
            phrase = ''.join([w['text'] for w in coords[i:j]]).lower()
            if search_key_normalized == re.sub(r'\s+', '', phrase):
                word_indices.append((i, j - 1))
                break

    valid_texts = []

    for start_idx, end_idx in word_indices:
        ref_box = coords[end_idx]  # Use last word of phrase as reference
        ref_x, ref_y, ref_w, ref_h = ref_box['left'], ref_box['top'], ref_box['width'], ref_box['height']

        for item in coords:
            tx, ty, tw, th = item['left'], item['top'], item['width'], item['height']
            word = item['text']

            if direction == "Right" and abs(ty - ref_y) < 20 and tx > (ref_x + ref_w) and tx < (ref_x + ref_w + distance):
                valid_texts.append(word)
            elif direction == "Left" and abs(ty - ref_y) < 20 and (tx + tw) < ref_x and (tx + tw) > (ref_x - distance):
                valid_texts.append(word)
            elif direction == "Down" and abs(tx - ref_x) < 20 and ty > (ref_y + ref_h) and ty < (ref_y + ref_h + distance):
                valid_texts.append(word)
            elif direction == "Up" and abs(tx - ref_x) < 20 and (ty + th) < ref_y and (ty + th) > (ref_y - distance):
                valid_texts.append(word)

    combined_text = " ".join(valid_texts)
    cleaned_text = unicodedata.normalize('NFC', combined_text.strip())
    cleaned_text = bytes(cleaned_text, 'utf-8').decode('unicode_escape')

    if regex:
        matched_text = re.findall(regex, cleaned_text.replace(" ", ""))
        cleaned_text = "\n".join(matched_text) if matched_text else "No match found"

    if size == "single line":
        lines = cleaned_text.splitlines()
        return lines[0] if lines else ""
    elif size == "multi line":
        return "\n".join(cleaned_text.splitlines()[:5])
    else:
        return cleaned_text

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

if __name__ == "__main__":
    image_path = "sncb-sa.png"
    json_path = "output_results.json"

    image = load_image(image_path)
    data = load_json(json_path)
    final_data = {}

    display_keys = {
        "IBAN": "iban",
        "BIC/SWIFT": "swift/bic",
        "DATE": "date",
        "DUE DATE": "due date",
        "TVA": "vat number",
        "TOTAL AMOUNT": "total amount",
        "INVOICE NO.": "invoice number",
        "FROM ADDRESS": "from address",
        "TO ADDRESS": "to address",
        "SUPPLIER NAME": "supplier name",
        "CLIENT NAME": "client name"
    }

    for key, value in data.items():
        search_key = value["key"]
        direction = value.get("Direction")
        distance = value.get("Distance", 300)
        size = value.get("Size", "single line")
        regex = value.get("regex")

        if direction and distance:
            result = extract_text_with_ocr(image, search_key, direction, distance, size, regex)
        else:
            result = "Null"

        display_key = display_keys.get(key, key.lower())
        final_data[display_key] = result
        logging.info(f"{display_key}: {result}")

    with open('op_json/image_output.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=4)
