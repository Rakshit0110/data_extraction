import numpy as np
import cv2
import io
import fitz  # PyMuPDF
from PIL import Image

def extract_pdf_image_from_bytes(pdf_bytes, dpi=300):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(0)
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72))
    img_bytes = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_bytes))
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
