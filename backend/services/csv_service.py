"""
csv_service.py — CSV import & export service.

Fully migrated to Firestore. No SQL.
"""

import csv
import io
from datetime import datetime, timezone
import firestore_db


def _parse_csv_date(date_str: str) -> datetime:
    """Parse various date formats from CSV into a UTC datetime."""
    date_str = (date_str or '').strip()
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y'):
        try:
            return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return datetime.now(timezone.utc)


def ingest_sales_csv(file_stream, user_id='demo'):
    """Import sales data from CSV (columns: product_name, quantity, price, date)."""
    reader = csv.DictReader(io.TextIOWrapper(file_stream, encoding='utf-8'))
    count = 0
    required_cols = {'product_name', 'quantity', 'price', 'date'}

    for row in reader:
        # Check required columns
        row_lower = {k.strip().lower(): v for k, v in row.items() if k}
        if not required_cols.issubset(set(row_lower.keys())):
            raise ValueError("CSV missing required columns: product_name, quantity, price, date")

        prod_name = row_lower['product_name'].strip()
        product = firestore_db.get_product_by_name(user_id, prod_name)
        if not product:
            continue

        try:
            qty = int(row_lower['quantity'])
            price = float(row_lower['price'])
            sold_at_dt = _parse_csv_date(row_lower['date'])
        except (ValueError, TypeError):
            continue

        item_total = price * qty
        firestore_db.insert_sale(
            user_id=user_id,
            product_id=product['id'],
            product_name=product['name'],
            category=product.get('category', 'general'),
            quantity=qty,
            total_price=item_total,
            sold_at=sold_at_dt
        )
        count += 1

    return count


# Alias for backward compatibility
ingest_csv = ingest_sales_csv


def ingest_inventory_csv(file_stream, user_id='demo'):
    """
    Bulk import products from CSV.
    Columns: product_name, category, price, stock [, cost_price]
    If a product already exists (by name), its stock is ADDED to the existing stock.
    """
    reader = csv.DictReader(io.TextIOWrapper(file_stream, encoding='utf-8'))

    required_cols = {'product_name', 'category', 'price', 'stock'}
    added = 0
    updated = 0
    errors = []

    for i, row in enumerate(reader, start=2):
        row_keys = {k.strip().lower() for k in row.keys() if k}
        if not required_cols.issubset(row_keys):
            raise ValueError("CSV missing required columns: product_name, category, price, stock")

        # Normalize keys
        normalized = {}
        for k, v in row.items():
            if k:
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
        existing = firestore_db.get_product_by_name(user_id, name)

        if existing:
            # Update: add stock, update price/category
            new_stock = existing.get('stock', 0) + stock
            update_data = {
                'stock': new_stock,
                'price': price,
                'category': category,
            }
            if cost_price is not None:
                update_data['cost_price'] = cost_price

            firestore_db.update_product(user_id, existing['id'], **update_data)
            updated += 1
        else:
            # Insert new product
            firestore_db.insert_product(
                user_id=user_id,
                name=name,
                category=category,
                price=price,
                stock=stock,
                cost_price=cost_price,
            )
            added += 1

    return {"added": added, "updated": updated, "errors": errors}
