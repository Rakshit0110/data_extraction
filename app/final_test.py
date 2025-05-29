import cv2
import pytesseract
import json

# Load image and Tesseract
image = cv2.imread('unit_2.png')
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Load coordinates from JSON
with open('coords.json', 'r') as f:
    json_data = json.load(f)

# Run OCR
data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
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

# Process each key-value pair from JSON
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

    found = False
    for line_words in lines.values():
        words = [w['text'].lower() for w in line_words]
        key_parts = KEYWORD.lower().split()
        num_parts = len(key_parts)

        for i in range(len(words) - num_parts + 1):
            if words[i:i + num_parts] == key_parts:
                matched = line_words[i:i + num_parts]
                x1 = min(w['left'] for w in matched)
                y1 = min(w['top'] for w in matched)
                x2 = max(w['left'] + w['width'] for w in matched)
                y2 = max(w['top'] + w['height'] for w in matched)

                # Draw green box around key
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # Define relative value box
                rx = int(x1 + dx)
                ry = int(y1 + dy)
                rw = int(vw)
                rh = int(vh)

                # Draw blue box around value
                cv2.rectangle(image, (rx, ry), (rx + rw, ry + rh), (255, 0, 0), 2)

                # Find lines intersecting the value box
                matched_line_ids = set()
                for idx in range(n):
                    if int(data['conf'][idx]) > 0:
                        wx, wy = data['left'][idx], data['top'][idx]
                        ww, wh = data['width'][idx], data['height'][idx]
                        if wx + ww > rx and wx < rx + rw and wy + wh > ry and wy < ry + rh:
                            if idx in line_ids:
                                matched_line_ids.add(line_ids[idx])

                # Extract text on same line inside the value box
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

# Resize image to 20% of original size
scale_percent = 20
width = int(image.shape[1] * scale_percent / 100)
height = int(image.shape[0] * scale_percent / 100)
resized_image = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)

# Save and show resized image with boxes
cv2.imwrite('output_key_val_boxes.jpg', resized_image)
cv2.imshow("Key-Value Extraction", resized_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
