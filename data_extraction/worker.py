import redis
import json
import logging
from extractor import process_extraction

REDIS_QUEUE = "data-extraction-queue"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("data_extraction.log", encoding="utf-8")]
)

def listen_to_queue():
    r = redis.Redis(host='localhost', port=6379, db=0)

    logging.info(" Listening to Redis queue: %s", REDIS_QUEUE)

    while True:
        _, job_data = r.blpop(REDIS_QUEUE)

        try:
            job = json.loads(job_data)
            invoice_data = job.get("data")  # Fix is here

            if not invoice_data:
                logging.error(" No 'data' field found in job: %s", job)
                continue

            logging.info(" Received job from queue. Starting extraction...")
            process_extraction(invoice_data)

        except Exception as e:
            logging.error(" Failed to process job: %s", e)

if __name__ == "__main__":
    listen_to_queue()
