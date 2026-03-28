import sqlite3
import os
import time
from config import DATABASE_PATH

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Create tables
    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      name        TEXT NOT NULL UNIQUE,
      category    TEXT NOT NULL DEFAULT 'general',
      price       REAL NOT NULL,
      stock       INTEGER NOT NULL DEFAULT 0,
      created_at  TEXT DEFAULT (datetime('now'))
    )
    """)
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS sales (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      product_id  INTEGER NOT NULL,
      quantity    INTEGER NOT NULL,
      total_price REAL NOT NULL,
      sold_at     TEXT DEFAULT (datetime('now')),
      FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS bills (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      bill_number TEXT NOT NULL UNIQUE,
      items_json  TEXT NOT NULL,
      total       REAL NOT NULL,
      created_at  TEXT DEFAULT (datetime('now'))
    )
    """)
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      level       TEXT NOT NULL,
      message     TEXT NOT NULL,
      created_at  TEXT DEFAULT (datetime('now')),
      is_read     INTEGER DEFAULT 0
    )
    """)
    
    conn.commit()
    seed_data(conn)
    conn.close()

def seed_data(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as count FROM products")
    row = c.fetchone()
    if row['count'] > 0:
        return
        
    print("Seeding initial data...")
    SEED_PRODUCTS = [
        ("Basmati Rice",  "general",     150.0, 80),
        ("Sugar",         "sweets",       50.0,  5),
        ("Holi Colours",  "colours",      30.0, 60),
        ("Diya Set",      "lights",       80.0, 40),
        ("Sweets Box",    "sweets",      200.0, 25),
        ("Old Soap",      "general",      20.0, 50),
        ("Wheat Flour",   "general",      45.0, 70),
        ("Dry Fruits",    "gifts",       350.0, 20),
        ("LED String",    "lights",      120.0, 15),
        ("Cotton Kurta",  "clothing",    450.0, 30),
        ("Notebooks",     "stationery",   60.0,  0),
        ("Water Bottles", "general",     100.0,  3),
    ]
    
    for p in SEED_PRODUCTS:
        c.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", p)
        
    conn.commit()
    
    def insert_seed_sale(name, qty, days_ago):
        c.execute("SELECT id, price FROM products WHERE name = ?", (name,))
        prod = c.fetchone()
        if prod:
            sold_at = f"datetime('now', '-{days_ago} days')"
            total = qty * prod['price']
            c.execute(f"INSERT INTO sales (product_id, quantity, total_price, sold_at) VALUES (?, ?, ?, {sold_at})", (prod['id'], qty, total))

    SEED_SALES = [
        ("Basmati Rice", 15, 0), ("Basmati Rice", 15, 1), ("Basmati Rice", 20, 2), ("Basmati Rice", 10, 3),
        ("Wheat Flour", 25, 1), ("Wheat Flour", 30, 2),
        ("Sugar", 5, 1), ("Sugar", 4, 3),
        ("Holi Colours", 2, 12),
        ("Diya Set", 8, 4), ("Diya Set", 5, 5),
        ("Sweets Box", 3, 1), ("Sweets Box", 6, 2),
        ("Old Soap", 2, 9),
        ("Cotton Kurta", 1, 14),
        ("Dry Fruits", 1, 20),
    ]
    
    for s in SEED_SALES:
        insert_seed_sale(s[0], s[1], s[2])
        
    conn.commit()
