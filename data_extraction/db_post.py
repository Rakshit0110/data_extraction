import psycopg2
import json
import logging

# Configure logging for database insertion
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler('logs/db_post.log'),
    logging.StreamHandler()
])

def insert_invoice_data(data):
    """Insert extracted data into the PostgreSQL database."""
    
    # Connect to PostgreSQL database
    try:
        conn = psycopg2.connect(
            dbname="test",  # Adjust if necessary
            user="postgres",  # Adjust if necessary
            password="tingri007",  # Change to your actual password
            host="localhost",
            port="5432"
        )
        cur = conn.cursor()
        
        logging.info(f"Attempting to insert data into the database.")

        # SQL Insert query
        query = """
            INSERT INTO test.public.invoices_json_fields(
                iban, swift_bic, date, due_date, vat_number,
                total_amount, invoice_number, from_address,
                to_address, supplier_name, client_name
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Prepare values for insertion
        values = (
            json.dumps(data.get("iban", "Not found")),
            json.dumps(data.get("swift/bic", "Not found")),
            json.dumps(data.get("date", "Not found")),
            json.dumps(data.get("due date", "Not found")),
            json.dumps(data.get("vat number", "Not found")),
            json.dumps(data.get("total amount", "Not found")),
            json.dumps(data.get("invoice number", "Not found")),
            json.dumps(data.get("from address", "Not found")),
            json.dumps(data.get("to address", "Not found")),
            json.dumps(data.get("supplier name", "Not found")),
            json.dumps(data.get("client name", "Not found"))
        )

        # Execute the insert
        cur.execute(query, values)
        
        # Commit changes to the database
        conn.commit()
        logging.info(f"Data successfully inserted into the database.")

    except Exception as e:
        logging.error(f"Failed to insert data into the database: {str(e)}")
    finally:
        # Ensure the connection is closed
        if conn:
            cur.close()
            conn.close()
            logging.info(f"Database connection closed.")

