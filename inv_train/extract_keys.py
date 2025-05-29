import json
import fitz  # PyMuPDF

def extract_key_texts(pdf_path, json_path, logger):
    with open(json_path, 'r') as f:
        data = json.load(f)

    doc = fitz.open(pdf_path)
    page = doc.load_page(0)

    results = {}
    for key in data:
        if key.endswith("KEY"):
            coords = data[key][0]
            x, y, w, h = coords["x"], coords["y"], coords["width"], coords["height"]
            adjusted_h = 10
            rect = fitz.Rect(x, y, x + w, y + adjusted_h)

            text = page.get_textbox(rect).strip()
            if not text:
                logger.warning(f"No text found for key: {key}, trying nearby blocks.")
                for block in page.get_text("blocks"):
                    x0, y0, x1, y1, block_text, *_ = block
                    if fitz.Rect(x0, y0, x1, y1).intersects(rect):
                        text = block_text.strip()
                        break

            results[key] = text
            logger.info(f"Extracted key '{key}': {text}")
    return results
