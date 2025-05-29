import fitz  # PyMuPDF
import tempfile
import os

def convert_to_image_if_needed(file_path):
    if file_path.lower().endswith('.pdf'):
        doc = fitz.open(file_path)
        page = doc.load_page(0)  # First page only
        pix = page.get_pixmap(dpi=300)
        img_path = tempfile.mktemp(suffix='.png')
        pix.save(img_path)
        return img_path
    return file_path
