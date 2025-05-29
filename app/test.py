import cv2
import pytesseract

# Load image
image = cv2.imread('img.jpg')
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Your install path


# Get word boxes
boxes = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

# Draw boxes
n = len(boxes['text'])
for i in range(n):
    if int(boxes['conf'][i]) > 0:
        (x, y, w, h) = (boxes['left'][i], boxes['top'][i], boxes['width'][i], boxes['height'][i])
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

# Save or show
cv2.imwrite('output.jpg', image)
