import cv2
import pytesseract
import json
import tempfile
from PIL import Image
import re
from rapidfuzz import fuzz

# Load image
original_image = cv2.imread('images/cardif-lisbon.png')
height_limit = original_image.shape[0] // 2
img_height = original_image.shape[0]

# Preprocessing
gray = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
enhanced = clahe.apply(gray)
denoised = cv2.fastNlMeansDenoising(enhanced, h=30)
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
morphed = cv2.morphologyEx(denoised, cv2.MORPH_CLOSE, kernel)
processed = cv2.adaptiveThreshold(
    morphed, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 15, 10)

# Save high-DPI image
with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
    pil_image = Image.fromarray(processed)
    pil_image.save(tmp_file.name, dpi=(600, 600))
    temp_image_path = tmp_file.name

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Load coordinates
with open('../templates/coordinates/56_coordinates.json', 'r') as f:
    json_data = json.load(f)

# OCR
custom_config = r'--oem 3 --psm 6'
data = pytesseract.image_to_data(Image.open(temp_image_path),
                                 output_type=pytesseract.Output.DICT,
                                 config=custom_config)

image = original_image.copy()

# Organize lines
lines = {}
line_ids = {}
n = len(data['text'])

for i in range(n):
    if int(data['conf'][i]) > 0 and data['text'][i].strip():
        line_id = (data['page_num'][i], data['block_num'][i], data['par_num'][i], data['line_num'][i])
        if line_id not in lines:
            lines[line_id] = []
        word_data = {
            'text': data['text'][i],
            'left': data['left'][i],
            'top': data['top'][i],
            'width': data['width'][i],
            'height': data['height'][i]
        }
        lines[line_id].append(word_data)
        line_ids[i] = line_id

sorted_lines = sorted(lines.items(), key=lambda item: item[1][0]['top'])

# Zone function
def get_zone(y, height):
    if y < height * 0.25:
        return 'up'
    elif y < height * 0.5:
        return 'mid up'
    elif y < height * 0.75:
        return 'mid low'
    else:
        return 'low'

def filter_lines_by_zone(lines, zone, img_height):
    if zone == 'up':
        return [line for line in lines if line[1][0]['top'] < img_height * 0.25]
    elif zone == 'mid up':
        return [line for line in lines if img_height * 0.25 <= line[1][0]['top'] < img_height * 0.5]
    elif zone == 'mid low':
        return [line for line in lines if img_height * 0.5 <= line[1][0]['top'] < img_height * 0.75]
    else:
        return [line for line in lines if line[1][0]['top'] >= img_height * 0.75]

def normalize(text):
    return re.sub(r'[^\w\s]', '', text.lower()).strip()

# Process keys
for key in json_data:
    if not key.endswith("KEY"):
        continue

    base = key[:-4].strip()
    val_key = base + " VAL"
    if val_key not in json_data:
        continue

    key_entry = json_data[key][0]
    val_entry = json_data[val_key][0]

    KEYWORD = key_entry["key"]
    dx = val_entry["x"] - key_entry["x"]
    dy = val_entry["y"] - key_entry["y"]
    vw = val_entry["width"]
    vh = val_entry["height"]
    key_y = key_entry["y"]

    zone = get_zone(key_y, img_height)
    zone_lines = filter_lines_by_zone(sorted_lines, zone, img_height)

    found = False
    for _, line_words in zone_lines:
        line_texts = [normalize(w['text']) for w in line_words]
        line_joined = ' '.join(line_texts)
        keyword_norm = normalize(KEYWORD)

        score = fuzz.partial_ratio(line_joined, keyword_norm)

        if score > 85:
            key_parts = keyword_norm.split()
            num_parts = len(key_parts)

            for i in range(len(line_texts) - num_parts + 1):
                seq = ' '.join(line_texts[i:i + num_parts])
                if fuzz.ratio(seq, keyword_norm) > 85:
                    matched = line_words[i:i + num_parts]
                    x1 = min(w['left'] for w in matched)
                    y1 = min(w['top'] for w in matched)
                    x2 = max(w['left'] + w['width'] for w in matched)
                    y2 = max(w['top'] + w['height'] for w in matched)

                    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

                    rx = int(x1 + dx)
                    ry = int(y1 + dy)
                    rw = int(vw)
                    rh = int(vh)

                    cv2.rectangle(image, (rx, ry), (rx + rw, ry + rh), (255, 0, 0), 2)

                    matched_line_ids = set()
                    for idx in range(n):
                        if int(data['conf'][idx]) > 0:
                            wx, wy = data['left'][idx], data['top'][idx]
                            ww, wh = data['width'][idx], data['height'][idx]
                            if wx + ww > rx and wx < rx + rw and wy + wh > ry and wy < ry + rh:
                                if idx in line_ids:
                                    matched_line_ids.add(line_ids[idx])

                    extracted = []
                    for lid in matched_line_ids:
                        for word in lines[lid]:
                            wx, wy = word['left'], word['top']
                            ww, wh = word['width'], word['height']
                            if wx + ww > rx and wx < rx + rw and wy + wh > ry and wy < ry + rh:
                                extracted.append(word['text'])

                    print(f"{base}: {' '.join(extracted)}")
                    found = True
                    break
        if found:
            break

    if not found:
        print(f"{base}: Keyword not found.")

# Resize and display
scale_percent = 20
width = int(image.shape[1] * scale_percent / 100)
height = int(image.shape[0] * scale_percent / 100)
resized_image = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)

cv2.imwrite('OP/output_key_val_boxes.jpg', resized_image)
cv2.imshow("Key-Value Extraction", resized_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
