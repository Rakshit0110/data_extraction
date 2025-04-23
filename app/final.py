import fitz  # PyMuPDF
import json
import re
import unicodedata
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to extract text based on direction, distance, size, approach, and regex if available
def extract_text_from_pdf(pdf_path, search_key, direction, distance, size, approach, regex=None):
    doc = fitz.open(pdf_path)
    text = ""
    valid_texts = []

    logging.info(f"Searching for '{search_key}' in PDF...")

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
        text = ""
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

# Load JSON
def load_json(file_path):
    logging.info(f"Loading JSON file from {file_path}.")
    with open(file_path, 'r', encoding="utf-8") as f:
        data = json.load(f)
    logging.info(f"Successfully loaded {len(data)} entries from the JSON file.")
    return data

# Paths
pdf_path = "../sample_invoices/iabe/iabe.pdf"
json_path = "output_results.json"

logging.info(f"Starting PDF extraction process for file {pdf_path}.")

# Load JSON data
data = load_json(json_path)
final_data = {}

# Mapping displayed key names
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

# Extract text per entry
for key, value in data.items():
    display_key = display_keys.get(key, key.lower())
    search_key = value["key"]
    approach = value["Approach"]
    size = value["Size"]

    direction = value.get("Direction")
    distance = value.get("Distance")
    regex = value.get("regex")

    if direction and distance:
        extracted_text = extract_text_from_pdf(pdf_path, search_key, direction, distance, size, approach, regex)
    else:
        doc = fitz.open(pdf_path)
        found = False
        for page in doc:
            if page.search_for(search_key):
                extracted_text = search_key
                found = True
                break
        if not found:
            extracted_text = "Not found"

    final_data[display_key] = extracted_text
    logging.debug(f"Extracted text for '{display_key}': {extracted_text[:100]}...")

# Save output
output_path = 'op_json/final_key_val.json'
logging.info(f"Saving extracted data to {output_path}.")
with open(output_path, 'w', encoding="utf-8") as json_file:
    json.dump(final_data, json_file, indent=4)

logging.info(f"Final extracted data saved to {output_path}.")
