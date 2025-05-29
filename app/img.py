import cv2

# Input image path
image_path = input("Enter the image path: ")

# Load the image
image = cv2.imread(image_path)
if image is None:
    print("Error: Unable to load image.")
    exit()

# Step 1: Convert to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Step 2: Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
enhanced = clahe.apply(gray)

# Step 3: Denoising
denoised = cv2.fastNlMeansDenoising(enhanced, h=30)

# Step 4: Thresholding (Otsu's method)
_, thresholded = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# Save the output image
output_path = "processed_output.png"
cv2.imwrite(output_path, thresholded)
print(f"Processed image saved as {output_path}")

# Optional: Display the result
cv2.imshow("Processed Image", thresholded)
cv2.waitKey(0)
cv2.destroyAllWindows()
