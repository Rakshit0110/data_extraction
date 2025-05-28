import cv2
import json
from paddleocr import PaddleOCR

# Initialize PaddleOCR (CPU, English)
ocr = PaddleOCR(use_angle_cls=True, lang='en')  # use_gpu=False by default

# Load image
image_path = 'images/iabe.png'
image = cv2.imread(image_path)

# Run OCR
ocr_results = ocr.ocr(image_path, cls=True)[0]  # Get first page's results

# Convert results to a list of words with bounding boxes
words_data = []
for result in ocr_results:
    box, (text, conf) = result
    if not text.strip():
        continue
    x_coords = [pt[0] for pt in box]
    y_coords = [pt[1] for pt in box]
    left = int(min(x_coords))
    top = int(min(y_coords))
    right = int(max(x_coords))
    bottom = int(max(y_coords))

    words_data.append({
        'text': text,
        'conf': conf,
        'left': left,
        'top': top,
        'right': right,
        'bottom': bottom,
        'width': right - left,
        'height': bottom - top
    })

# Group words into lines based on vertical proximity
def group_lines(words, y_threshold=10):
    lines = []
    for word in sorted(words, key=lambda w: w['top']):
        matched = False
        for line in lines:
            if abs(word['top'] - line[0]['top']) <= y_threshold:
                line.append(word)
                matched = True
                break
        if not matched:
            lines.append([word])
    return lines

lines = group_lines(words_data)

# Load coordinates from JSON
with open('static_files/coordinates/iabe.json', 'r') as f:
    json_data = json.load(f)

# Process each key-value pair
for key in json_data:
    if not key.endswith("KEY"):
        continue

    base = key[:-4].strip()
    val_key = base + " VAL"
    if val_key not in json_data:
        continue

    key_entry = json_data[key][0]
    val_entry = json_data[val_key][0]

    keyword = key_entry["key"].lower()
    dx = val_entry["x"] - key_entry["x"]
    dy = val_entry["y"] - key_entry["y"]
    vw = val_entry["width"]
    vh = val_entry["height"]

    found = False
    for line in lines:
        words_lower = [w['text'].lower() for w in line]
        key_parts = keyword.split()
        for i in range(len(words_lower) - len(key_parts) + 1):
            if words_lower[i:i + len(key_parts)] == key_parts:
                matched = line[i:i + len(key_parts)]
                x1 = min(w['left'] for w in matched)
                y1 = min(w['top'] for w in matched)
                x2 = max(w['right'] for w in matched)
                y2 = max(w['bottom'] for w in matched)

                # Draw green box around keyword
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # Define value box
                rx = int(x1 + dx)
                ry = int(y1 + dy)
                rw = int(vw)
                rh = int(vh)

                # Draw blue box for value
                cv2.rectangle(image, (rx, ry), (rx + rw, ry + rh), (255, 0, 0), 2)

                # Extract text inside the value box
                extracted = []
                for word in words_data:
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

# Resize and save image
scale_percent = 20
resized = cv2.resize(
    image,
    (int(image.shape[1] * scale_percent / 100), int(image.shape[0] * scale_percent / 100)),
    interpolation=cv2.INTER_AREA
)

cv2.imwrite('OP/output_key_val_boxes_paddle.jpg', resized)
cv2.imshow("PaddleOCR Key-Value Boxes", resized)
cv2.waitKey(0)
cv2.destroyAllWindows()
