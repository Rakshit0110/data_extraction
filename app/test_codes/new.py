import fitz  # PyMuPDF
from PIL import Image
import pytesseract

# Config
pdf_path = "anysoft-3.pdf"
tesseract_cmd_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_path

# Viewer coordinates and scale
screen_x, screen_y = 457, 34
screen_w, screen_h = 64, 17
scale_used_in_viewer = 1.0

# Convert to PDF coordinates
pdf_x = screen_x / scale_used_in_viewer
pdf_y = screen_y / scale_used_in_viewer
pdf_w = screen_w / scale_used_in_viewer
pdf_h = screen_h / scale_used_in_viewer
rect = fitz.Rect(pdf_x, pdf_y, pdf_x + pdf_w, pdf_y + pdf_h)

# Load PDF and render region
doc = fitz.open(pdf_path)
page = doc.load_page(0)
pix = page.get_pixmap(clip=rect)
img_path = "temp_clip.png"
pix.save(img_path)

# OCR
ocr_text = pytesseract.image_to_string(Image.open(img_path)).strip()
print(ocr_text)
