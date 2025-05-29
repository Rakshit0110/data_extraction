import fitz  # PyMuPDF

# ==== INPUTS ====
pdf_path = "../sample_invoices/iabe/iabe.pdf"
scale_used_in_viewer = 1.0

# Coordinates for the part of the document
screen_x, screen_y = 45.399603350812654, 284.6045907693566
screen_w, screen_h = 72.09859024061575, 24.183630774273972


# Adjust the height and width of the box (shrink if necessary to avoid extra data)
adjusted_screen_h = 10  # Reduce height if it's capturing extra lines

# ==== CONVERT TO PDF COORDINATES ====
pdf_x = screen_x / scale_used_in_viewer
pdf_y = screen_y / scale_used_in_viewer
pdf_w = screen_w / scale_used_in_viewer
pdf_h = adjusted_screen_h / scale_used_in_viewer

# Draw the adjusted rectangle for PDF extraction
rect = fitz.Rect(pdf_x, pdf_y, pdf_x + pdf_w, pdf_y + pdf_h)

# ==== LOAD PDF ====
doc = fitz.open(pdf_path)
page = doc.load_page(0)

# ==== TRY DIRECT EXTRACTION ====
print(f"Using PDF-space rect: {rect}")
text = page.get_textbox(rect).strip()

if text:
    print(" Extracted text:", text)
else:
    print(" No direct match found in box. Scanning nearby blocks...\n")
    for block in page.get_text("blocks"):
        x0, y0, x1, y1, block_text, *_ = block
        block_rect = fitz.Rect(x0, y0, x1, y1)
        if rect.intersects(block_rect):
            print(f"🟨 Block ({x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f}): {block_text.strip()}")


