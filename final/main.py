from services.image_processor import convert_to_image_if_needed
from services.matcher import find_best_match_and_json
from services.extractor import extract_data
from config import INPUT_FILE_PATH

# Step 1: Convert to image
input_image = convert_to_image_if_needed(INPUT_FILE_PATH)

# Step 2–3: Match template and get JSON
matched_json = find_best_match_and_json(input_image)

# Step 4: Handle untrained model
if matched_json.get("model") == "untrained":
    print("No trained model matched. Output:", matched_json)
else:
    # Step 5: Run extraction
    extracted_data = extract_data(input_image, matched_json)

    # Step 6: Send extracted_data to next service
    print("Extracted:", extracted_data)
