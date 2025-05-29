import os

# Paths
INPUT_INVOICES_PATH = "../sample_invoices"
PROCESSED_FILES_PATH = "../files/processed"
EXTRACTED_JSON_PATH = "../files/extract_key_value"
UNPROCESSED_PATH = "../files/unprocessed"
LOG_FILE_PATH = "logs/app.log"

# Ensure directories exist
os.makedirs(INPUT_INVOICES_PATH, exist_ok=True)
os.makedirs(PROCESSED_FILES_PATH, exist_ok=True)
os.makedirs(EXTRACTED_JSON_PATH, exist_ok=True)
os.makedirs(UNPROCESSED_PATH, exist_ok=True)
