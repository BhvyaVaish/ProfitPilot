from models import get_product_by_name
from database import get_connection

def insert_sale_csv(product_id, qty, price, date_str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO sales (product_id, quantity, total_price, sold_at) VALUES (?, ?, ?, ?)",
              (product_id, qty, price * qty, date_str))
    conn.commit()
    conn.close()

def ingest_csv(file_stream):
    import csv, io
    reader = csv.DictReader(io.TextIOWrapper(file_stream, encoding='utf-8'))
    count = 0
    required_cols = {'product_name', 'quantity', 'price', 'date'}
    
    for row in reader:
        if not required_cols.issubset(set(row.keys())):
            raise ValueError("CSV missing required columns: product_name, quantity, price, date")
        product = get_product_by_name(row['product_name'].strip())
        if not product:
            continue
        insert_sale_csv(product['id'], int(row['quantity']), float(row['price']), row['date'])
        count += 1
        
    return count
