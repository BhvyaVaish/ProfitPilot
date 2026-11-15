"""
models.py — Firestore-backed CRUD wrappers for ProfitPilot.

Exposes the same function signatures as the old SQL-based models.py
so that existing callers (services, routes) need no changes.
"""

import firestore_db


# ── Products ───────────────────────────────────────────────────────────

def get_all_products(user_id='demo'):
    return firestore_db.get_all_products(user_id)


def get_products_by_categories(categories, user_id='demo'):
    return firestore_db.get_products_by_categories(user_id, categories)


def get_product_by_name(name, user_id='demo'):
    return firestore_db.get_product_by_name(user_id, name)


def insert_product(name, category, price, stock, user_id='demo', cost_price=None):
    """Insert a product and return its new Firestore document ID (string)."""
    return firestore_db.insert_product(
        user_id=user_id,
        name=name,
        category=category,
        price=price,
        stock=stock,
        cost_price=cost_price,
    )


def update_product(product_id, user_id='demo', **kwargs):
    firestore_db.update_product(user_id, product_id, **kwargs)


def delete_product(product_id, user_id='demo'):
    firestore_db.delete_product(user_id, product_id)


# ── Alerts ─────────────────────────────────────────────────────────────

def get_all_alerts(user_id='demo'):
    return firestore_db.get_alerts(user_id)


def insert_alert(level, message, user_id='demo'):
    firestore_db.insert_alert(user_id, level, message)


def clear_auto_alerts(user_id='demo'):
    firestore_db.clear_alerts(user_id)


# ── User profile ───────────────────────────────────────────────────────

def get_user_profile(user_id):
    return firestore_db.get_user_profile(user_id)
