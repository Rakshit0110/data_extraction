import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_FILE_PATH = os.path.join(BASE_DIR, 'input_files', 'sample 6.pdf')
IMAGES_FOLDER = os.path.join(BASE_DIR, '../templates/images')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'OP')
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

DB_CONFIG = {
    "host": "localhost",
    "user": "postgres",
    "password": "tingri007",
    "database": "test"
}
