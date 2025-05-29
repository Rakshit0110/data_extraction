import os
import json
import logging
import redis
from processor.pdf_comparator import compare_token_sequences
from processor.json_manager import load_json_data
from processor.file_handler import get_all_files_in_folder, move_to_unprocessed
import config

def setup_logging():
    """Set up logging configuration."""
    os.makedirs(os.path.dirname(config.LOG_FILE_PATH), exist_ok=True)
    logging.basicConfig(
        filename=config.LOG_FILE_PATH,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

def send_to_data_extraction(data):
    """Send matched invoice data to data extraction queue."""
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)  # Connect to Redis
        job = {
            "name": "extract_invoice_data",
            "data": data,
            "opts": {}
        }
        # Pushing job to Redis list (as a queue)
        r.rpush("data-extraction-queue", json.dumps(job))  # Adjusted queue name for clarity
        logging.info("Job sent to data-extraction queue.")
    except Exception as e:
        logging.error(f"Failed to send job to Redis: {e}")

def process_invoice(invoice_path):
    """Process the invoice and match with templates."""
    # Get all templates and JSON data
    templates = get_all_files_in_folder(config.TEMPLATES_FOLDER)
    json_data = load_json_data(config.PROCESSED_JSON_FOLDER)

    best_score = 0
    best_match_template = None
    best_json_data = None

    # Compare invoice with each template
    for template in templates:
        template_path = os.path.join(config.TEMPLATES_FOLDER, template)
        score = compare_token_sequences(invoice_path, template_path)

        # Keep track of best match
        if score > best_score:
            best_score = score
            best_match_template = template
            json_key = template.replace('.pdf', '.json')
            best_json_data = json_data.get(json_key)

    # If a good match is found, send the job to data extraction
    if best_score >= config.SIMILARITY_THRESHOLD and best_json_data:
        logging.info(f"Matched with {best_match_template}, score: {best_score:.2f}")
        result = {
            "invoice_path": invoice_path,
            "matched_template": best_match_template,
            "similarity_score": round(best_score, 2),
            "matched_json_data": best_json_data
        }
        send_to_data_extraction(result)
        return result
    else:
        # If no match is found, move to unprocessed
        move_to_unprocessed(invoice_path, config.UNPROCESSED_FOLDER)
        logging.info(f"No match found. Moved {invoice_path} to unprocessed.")
        return None

if __name__ == "__main__":
    setup_logging()

    # Adjusted the invoice path to be configurable from the config file
    result = process_invoice(config.INPUT_INVOICE_PATH)

    if result:
        print("Invoice matched and job queued:")
        print(json.dumps(result, indent=4))
    else:
        print("Invoice could not be processed and was moved to 'unprocessed'")
