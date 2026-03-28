from database import get_connection

def get_all_products():
    conn = get_connection()
    products = conn.execute("SELECT * FROM products ORDER BY name ASC").fetchall()
    conn.close()
    return [dict(p) for p in products]

def get_product(product_id):
    conn = get_connection()
    prod = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return dict(prod) if prod else None

def get_product_by_name(name):
    conn = get_connection()
    prod = conn.execute("SELECT * FROM products WHERE name = ?", (name,)).fetchone()
    conn.close()
    return dict(prod) if prod else None

def insert_product(name, category, price, stock):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", 
              (name, category, price, stock))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return new_id

def update_product_stock(product_id, stock):
    conn = get_connection()
    conn.execute("UPDATE products SET stock = ? WHERE id = ?", (stock, product_id))
    conn.commit()
    conn.close()

def delete_product(product_id):
    conn = get_connection()
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

def get_products_by_categories(categories):
    if not categories:
        return []
    conn = get_connection()
    placeholders = ','.join('?' * len(categories))
    query = f"SELECT * FROM products WHERE category IN ({placeholders})"
    products = conn.execute(query, categories).fetchall()
    conn.close()
    return [dict(p) for p in products]

def insert_alert(conn, level, message):
    conn.execute("INSERT INTO alerts (level, message) VALUES (?, ?)", (level, message))
