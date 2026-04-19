from models import get_product_by_name
from database import get_connection

def insert_sale_csv(product_id, qty, price, date_str, user_id='demo'):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO sales (user_id, product_id, quantity, total_price, sold_at) VALUES (?, ?, ?, ?, ?)",
              (user_id, product_id, qty, price * qty, date_str))
    conn.commit()
    conn.close()

def ingest_sales_csv(file_stream, user_id='demo'):
    """Import sales data from CSV (columns: product_name, quantity, price, date)."""
    import csv, io
    reader = csv.DictReader(io.TextIOWrapper(file_stream, encoding='utf-8'))
    count = 0
    required_cols = {'product_name', 'quantity', 'price', 'date'}
    
    for row in reader:
        if not required_cols.issubset(set(row.keys())):
            raise ValueError("CSV missing required columns: product_name, quantity, price, date")
        product = get_product_by_name(row['product_name'].strip(), user_id)
        if not product:
            continue
        insert_sale_csv(product['id'], int(row['quantity']), float(row['price']), row['date'], user_id)
        count += 1
        
    return count

# Keep old name as alias for backward compatibility
ingest_csv = ingest_sales_csv

def ingest_inventory_csv(file_stream, user_id='demo'):
    """
    Bulk import products from CSV.
    Columns: product_name, category, price, stock [, cost_price]
    If a product already exists (by name), its stock is ADDED to the existing stock.
    """
    import csv, io
    reader = csv.DictReader(io.TextIOWrapper(file_stream, encoding='utf-8'))
    
    required_cols = {'product_name', 'category', 'price', 'stock'}
    added = 0
    updated = 0
    errors = []
    
    conn = get_connection()
    
    for i, row in enumerate(reader, start=2):
        row_keys = {k.strip().lower() for k in row.keys()}
        if not required_cols.issubset(row_keys):
            raise ValueError(f"CSV missing required columns: product_name, category, price, stock")
        
        # Normalize keys (handle case differences)
        normalized = {}
        for k, v in row.items():
            normalized[k.strip().lower()] = (v or '').strip()
        
        name = normalized.get('product_name', '').strip()
        category = normalized.get('category', 'general').strip() or 'general'
        price_str = normalized.get('price', '').strip()
        stock_str = normalized.get('stock', '').strip()
        cost_price_str = normalized.get('cost_price', '').strip()
        
        if not name:
            errors.append(f"Row {i}: empty product_name")
            continue
        
        try:
            price = float(price_str)
            stock = int(stock_str)
        except (ValueError, TypeError):
            errors.append(f"Row {i} ({name}): invalid price or stock")
            continue
        
        if price <= 0:
            errors.append(f"Row {i} ({name}): price must be > 0")
            continue
        if stock < 0:
            errors.append(f"Row {i} ({name}): stock must be >= 0")
            continue
        
        cost_price = None
        if cost_price_str:
            try:
                cost_price = float(cost_price_str)
            except (ValueError, TypeError):
                pass  # Ignore invalid cost_price, will use default
        
        # Check if product already exists
        existing = conn.execute(
            "SELECT id, stock FROM products WHERE user_id = ? AND LOWER(name) = LOWER(?)",
            (user_id, name)
        ).fetchone()
        
        if existing:
            # Update: add stock, update price/category if provided
            new_stock = existing['stock'] + stock
            if cost_price is not None:
                conn.execute(
                    "UPDATE products SET stock = ?, price = ?, category = ?, cost_price = ? WHERE id = ? AND user_id = ?",
                    (new_stock, price, category, cost_price, existing['id'], user_id)
                )
            else:
                conn.execute(
                    "UPDATE products SET stock = ?, price = ?, category = ? WHERE id = ? AND user_id = ?",
                    (new_stock, price, category, existing['id'], user_id)
                )
            updated += 1
        else:
            # Insert new product
            if cost_price is not None:
                conn.execute(
                    "INSERT INTO products (user_id, name, category, price, stock, cost_price) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, name, category, price, stock, cost_price)
                )
            else:
                conn.execute(
                    "INSERT INTO products (user_id, name, category, price, stock) VALUES (?, ?, ?, ?, ?)",
                    (user_id, name, category, price, stock)
                )
            added += 1
    
    conn.commit()
    conn.close()
    
    return {"added": added, "updated": updated, "errors": errors}
