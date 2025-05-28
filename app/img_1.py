import pytesseract
from PIL import Image
import re

# === Step 1: Initialize Tesseract local path ===
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Your install path

# === Step 2: Load the image ===
img = Image.open('cardif-lisbon.png')  # <-- Directly use your .png or .jpg

# === Step 3: OCR the image ===
data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

# === Step 4: Smart extraction ===
fields = {
    "iban": None,
    "bic": None,
    "tva": None,
    "amount": None,
    "tax": None,
    "invoice_number": None,
    "date": None,
    "due_date": None,
    # "from_address": "",
    # "to_address": "",
    # "client_name": "",
    # "supplier_name": ""
}

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def find_nearby_text(start_idx, span=5):
    return clean_text(' '.join(data['text'][start_idx:start_idx+span]))

for i, word in enumerate(data['text']):
    w = word.lower()
    
    if "iban" in w:
        fields['iban'] = find_nearby_text(i+1)

    if "swift" in w:
        fields['bic'] = find_nearby_text(i+1)
    
    if "0435" in w or "tva" in w:
        fields['tva'] = w if "0435" in w else find_nearby_text(i+1)

    if "factura" in w or "invoice" in w:
        fields['invoice_number'] = find_nearby_text(i+1)

    if "date" in w and "due" not in w:
        fields['date'] = find_nearby_text(i+1)

    if "due" in w:
        fields['due_date'] = find_nearby_text(i+1)

    if re.match(r'^\d{1,3}(\.\d{3})*,\d{2}$', data['text'][i]) or re.match(r'^\d{1,},\d{2}$', data['text'][i]):
        if not fields['amount']:
            fields['amount'] = data['text'][i]

    if re.search(r'23%|21%|6%', w):
        fields['tax'] = w

    if fields['supplier_name'] == "" and "cardif" in w and "support" in (data['text'][i+1].lower() if i+1 < len(data['text']) else ''):
        fields['supplier_name'] = find_nearby_text(i, 5)

    if fields['client_name'] == "" and "cardif" in w and "assurance" in (data['text'][i+1].lower() if i+1 < len(data['text']) else ''):
        fields['client_name'] = find_nearby_text(i, 5)

fields['from_address'] = fields['supplier_name']
fields['to_address'] = fields['client_name']

# === Step 5: Show result ===
print("\n====== Extracted Fields from Image ======")
for key, value in fields.items():
    print(f"{key.capitalize()}: {value}")
