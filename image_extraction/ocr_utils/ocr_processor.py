import pytesseract
import cv2

# Set path to Tesseract executable (update if installed elsewhere)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_keys_from_rois(rois, image):
    updated = {}
    for key, region_list in rois.items():
        new_list = []
        for region in region_list:
            x = int(region['x'])
            y = int(region['y'])
            w = int(region['width'])
            h = int(region['height'])

            roi_image = image[y:y+h, x:x+w]
            text = pytesseract.image_to_string(roi_image, config='--psm 6').strip()

            new_entry = region.copy()
            if "KEY" in key.upper() or "VAL" in key.upper():
                new_entry["key"] = text if "KEY" in key.upper() else None

            new_list.append(new_entry)
        updated[key] = new_list
    return updated
