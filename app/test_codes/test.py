import psycopg2

conn = psycopg2.connect(
    dbname="test",
    user="postgres",
    password="tingri007",  # Replace with your real password
    host="localhost",
    port="5432"
)
cur = conn.cursor()

cur.execute("""
CREATE SCHEMA IF NOT EXISTS test_1 AUTHORIZATION postgres;

CREATE TABLE IF NOT EXISTS test_1.invoices_json_fields (
    id SERIAL PRIMARY KEY,
    iban JSONB,
    swift_bic JSONB,
    date JSONB,
    due_date JSONB,
    vat_number JSONB,
    total_amount JSONB,
    invoice_number JSONB,
    from_address JSONB,
    to_address JSONB,
    supplier_name JSONB,
    client_name JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

conn.commit()
cur.close()
conn.close()
