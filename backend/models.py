from database import get_connection

def get_all_products(user_id='demo'):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM products WHERE user_id = ? ORDER BY name ASC", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_products_by_categories(categories, user_id='demo'):
    if not categories:
        return []
    conn = get_connection()
    placeholders = ','.join(['?' for _ in categories])
    params = [user_id] + [c.lower() for c in categories]
    rows = conn.execute(f"SELECT * FROM products WHERE user_id = ? AND LOWER(category) IN ({placeholders})", params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_product_by_name(name, user_id='demo'):
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE user_id = ? AND LOWER(name) = LOWER(?)", (user_id, name)).fetchone()
    conn.close()
    return dict(row) if row else None

def insert_product(name, category, price, stock, user_id='demo', cost_price=None):
    conn = get_connection()
    c = conn.cursor()
    if cost_price is not None:
        c.execute("INSERT INTO products (user_id, name, category, price, stock, cost_price) VALUES (?, ?, ?, ?, ?, ?)", (user_id, name, category, price, stock, cost_price))
    else:
        c.execute("INSERT INTO products (user_id, name, category, price, stock) VALUES (?, ?, ?, ?, ?)", (user_id, name, category, price, stock))
    conn.commit()
    product_id = c.lastrowid
    conn.close()
    return product_id

def update_product(product_id, user_id='demo', name=None, price=None, stock=None, category=None):
    conn = get_connection()
    updates = []
    params = []
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if price is not None:
        updates.append("price = ?")
        params.append(price)
    if stock is not None:
        updates.append("stock = ?")
        params.append(stock)
    if category is not None:
        updates.append("category = ?")
        params.append(category)
    if not updates:
        conn.close()
        return
    params.extend([product_id, user_id])
    conn.execute(f"UPDATE products SET {', '.join(updates)} WHERE id = ? AND user_id = ?", params)
    conn.commit()
    conn.close()

def delete_product(product_id, user_id='demo'):
    conn = get_connection()
    conn.execute("DELETE FROM products WHERE id = ? AND user_id = ?", (product_id, user_id))
    conn.commit()
    conn.close()

def get_all_alerts(user_id='demo'):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM alerts WHERE user_id = ? ORDER BY created_at DESC LIMIT 10", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def insert_alert(level, message, user_id='demo'):
    conn = get_connection()
    conn.execute("INSERT INTO alerts (user_id, level, message) VALUES (?, ?, ?)", (user_id, level, message))
    conn.commit()
    conn.close()

def clear_auto_alerts(user_id='demo'):
    conn = get_connection()
    conn.execute("DELETE FROM alerts WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_user_profile(user_id):
    """Get user profile for personalized suggestions."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM user_profiles WHERE firebase_uid = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None
