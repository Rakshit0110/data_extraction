import os

# Path to the input invoice PDF
INPUT_INVOICE_PATH = "../sample_invoices/cardif-lisbon/cardif-lisbon.pdf"
# INPUT_INVOICE_PATH = "../sample_invoices/iabe/iabe.pdf"

# Folders
TEMPLATES_FOLDER = "../templates/pdfs"
PROCESSED_JSON_FOLDER = "../templates/jsons"
UNPROCESSED_FOLDER = "../files/unprocessed"

# Similarity threshold
SIMILARITY_THRESHOLD = 0.9

# Logging
LOG_FILE_PATH = "logs/app.log"
