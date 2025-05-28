import psycopg2
import json

# Your data (as-is)
data = {
    "iban": "BE07363029771966",
    "swift/bic": "BBRUBEBB",
    "date": "20/11/2023 0:00:00",
    "due date": "20/12/2023 0:00:00",
    "vat number": "BE043501827",
    "total amount": "25 637,59",
    "invoice number": "20000001781",
    "from address": "Not found",
    "to address": "Chaussée de Mons",
    "supplier name": "Unit4 Business Software N.V.",
    "client name": "Cardif Association de frais "
}

# Connect to your PostgreSQL database
conn = psycopg2.connect(
    dbname="test",
    user="postgres",
    password="tingri007",  # Replace with your password
    host="localhost",
    port="5432"
)

cur = conn.cursor()

# SQL Insert query
query = """
    INSERT INTO test.test_1.templates (
        iban, swift_bic, date, due_date, vat_number,
        total_amount, invoice_number, from_address,
        to_address, supplier_name, client_name
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

# Insert data as is (convert to JSONB)
values = (
    json.dumps(data["iban"]),
    json.dumps(data["swift/bic"]),
    json.dumps(data["date"]),
    json.dumps(data["due date"]),
    json.dumps(data["vat number"]),
    json.dumps(data["total amount"]),
    json.dumps(data["invoice number"]),
    json.dumps(data["from address"]),
    json.dumps(data["to address"]),
    json.dumps(data["supplier name"]),
    json.dumps(data["client name"])
)

# Execute the insert
cur.execute(query, values)

# Commit changes and close the connection
conn.commit()
cur.close()
conn.close()

print("Data inserted successfully!")
