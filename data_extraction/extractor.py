import fitz  # PyMuPDF
import json
import re
import unicodedata
import logging
import os
import time  # for optional delay
from config import INPUT_INVOICES_PATH, PROCESSED_FILES_PATH, EXTRACTED_JSON_PATH, UNPROCESSED_PATH

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler('logs/app.log'),
    logging.StreamHandler()
])

def load_json(file_path):
    logging.info(f"Loading JSON file from {file_path}.")
    try:
        with open(file_path, 'r', encoding="utf-8") as f:
            data = json.load(f)
        logging.info(f"Successfully loaded {len(data)} entries from the JSON file.")
        return data
    except Exception as e:
        logging.error(f"Error loading JSON from {file_path}: {str(e)}")
        return None

def extract_text_from_pdf(pdf_path, search_key, direction, distance, size, approach, regex=None):
    try:
        text = ""
        valid_texts = []

        logging.info(f"Searching for '{search_key}' in PDF...")

        with fitz.open(pdf_path) as doc:
            for page in doc:
                text_instances = page.search_for(search_key)
                logging.debug(f"Found {len(text_instances)} instances of '{search_key}' on page {page.number}.")

                if approach == "Bottom":
                    text_instances = sorted(text_instances, key=lambda x: x[1])
                elif approach == "Top":
                    text_instances = sorted(text_instances, key=lambda x: x[1], reverse=True)

                for inst in text_instances:
                    x0, y0, x1, y1 = inst
                    if direction == "Down":
                        text_area = page.get_text("text", clip=(x0, y1, x1, y1 + distance))
                    elif direction == "Up":
                        text_area = page.get_text("text", clip=(x0, y0 - distance, x1, y0))
                    elif direction == "Left":
                        text_area = page.get_text("text", clip=(x0 - distance, y0, x0, y1))
                    elif direction == "Right":
                        text_area = page.get_text("text", clip=(x1, y0, x1 + distance, y1))
                    else:
                        text_area = ""

                    if text_area.strip():
                        valid_texts.append(text_area.strip())

            if len(valid_texts) > 1:
                text = valid_texts[1]
                logging.debug(f"Multiple non-empty texts found. Using the second one.")
            elif valid_texts:
                text = valid_texts[0]
                logging.debug(f"Only one non-empty text found. Using it.")
            else:
                # fallback to just checking presence
                for page in doc:
                    if page.search_for(search_key):
                        text = search_key
                        break
                else:
                    text = "Not found"
                    logging.warning(f"No valid text found for '{search_key}'.")

        cleaned_text = unicodedata.normalize('NFC', text.strip())
        cleaned_text = bytes(cleaned_text, 'utf-8').decode('unicode_escape')
        cleaned_text = cleaned_text.replace("\n", " ").replace("\r", "")
        cleaned_text_without_spaces = cleaned_text.replace(" ", "")

        if regex:
            matched_text = re.findall(regex, cleaned_text_without_spaces)
            text = "\n".join(matched_text) if matched_text else "No match found"

        if size == "single line":
            lines = text.splitlines()
            cleaned_text = lines[1] if len(lines) > 1 else lines[0] if lines else ""
        elif size == "multi line":
            cleaned_text = "\n".join(text.splitlines()[:5])
        else:
            cleaned_text = text

        return cleaned_text

    except Exception as e:
        logging.error(f"Error extracting text for '{search_key}' from {pdf_path}: {str(e)}")
        return ""

def save_extracted_data(extracted_data, output_path):
    try:
        with open(output_path, 'w', encoding="utf-8") as json_file:
            json.dump(extracted_data, json_file, indent=4)
        logging.info(f"Extracted data saved to {output_path}.")
    except Exception as e:
        logging.error(f"Error saving extracted data to {output_path}: {str(e)}")

def process_extraction(matched_data):
    pdf_path = matched_data["invoice_path"]
    matched_json_data = matched_data["matched_json_data"]

    logging.info(f"Starting extraction for invoice: {pdf_path}")

    extracted_data = {}

    for key, value in matched_json_data.items():
        search_key = value["key"]
        direction = value.get("Direction")
        distance = value.get("Distance")
        size = value.get("size")
        approach = value["Approach"]
        regex = value.get("regex", None)

        logging.info(f"Extracting text for '{search_key}' from the PDF.")

        if direction and distance:
            extracted_text = extract_text_from_pdf(pdf_path, search_key, direction, distance, size, approach, regex)
        else:
            with fitz.open(pdf_path) as doc:
                found = False
                for page in doc:
                    if page.search_for(search_key):
                        extracted_text = search_key
                        found = True
                        break
                if not found:
                    extracted_text = "Not found"

        if extracted_text:
            extracted_data[search_key] = extracted_text
        else:
            logging.warning(f"Failed to extract text for '{search_key}'.")

    output_path = os.path.join(EXTRACTED_JSON_PATH, f"{os.path.basename(pdf_path).split('.')[0]}.json")
    save_extracted_data(extracted_data, output_path)

    try:
        time.sleep(0.1)  # Optional: give OS time to release file lock
        if extracted_data:
            processed_path = os.path.join(PROCESSED_FILES_PATH, f"{os.path.basename(pdf_path).split('.')[0]}.pdf")
            os.rename(pdf_path, processed_path)
            logging.info(f"Processed file moved to {processed_path}.")
        else:
            unprocessed_path = os.path.join(UNPROCESSED_PATH, f"{os.path.basename(pdf_path).split('.')[0]}.pdf")
            os.rename(pdf_path, unprocessed_path)
            logging.error(f"Failed to extract data for {pdf_path}. Moved to unprocessed.")
    except Exception as e:
        logging.error(f"Failed to move file {pdf_path}: {str(e)}")
