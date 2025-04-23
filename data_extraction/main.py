import json


from extractor import process_extraction
from config import INPUT_INVOICES_PATH


def load_invoice_data():
    with open("invoice_data.json", "r") as f:
        return json.load(f)

def main():
    invoice_matched_data = load_invoice_data()
    process_extraction(invoice_matched_data)

if __name__ == "__main__":
    main()

