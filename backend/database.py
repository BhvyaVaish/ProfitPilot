"""
database.py — Unified DB adapter for ProfitPilot.

LOCAL DEV   → Uses SQLite  (no DATABASE_URL set)
PRODUCTION  → Uses PostgreSQL via psycopg2 (DATABASE_URL set by Vercel/Supabase)

All callers use plain ? placeholders and sqlite3-style APIs.
The adapter handles translation transparently.
"""

import os
import re
import sqlite3
import random
from datetime import datetime, timedelta

# ── Detect environment ──────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL")  # Set by Vercel from Supabase
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras

# ── SQLite path (local only) ────────────────────────────────────────────────────
_SQLITE_PATH = os.path.join(os.path.dirname(__file__), "profitpilot.db")

# ── Tables with SERIAL PRIMARY KEY (have an `id` column) ────────────────────────
# user_profiles uses firebase_uid as PK — no `id` column.
# RETURNING id must NOT be appended for tables not in this set.
_TABLES_WITH_SERIAL_ID = {"products", "sales", "bills", "alerts", "festival_demands"}


# ══════════════════════════════════════════════════════════════════════════════
#  SQL TRANSLATION — SQLite dialect → PostgreSQL dialect
# ══════════════════════════════════════════════════════════════════════════════

def _translate_sql(sql: str) -> str:
    """Translate SQLite-flavoured SQL to PostgreSQL-compatible SQL.
    Called automatically for every query when USE_POSTGRES is True.
    """
    if not USE_POSTGRES:
        return sql

    # ── 1. Paramstyle: ? → %s ─────────────────────────────────────────────────
    sql = sql.replace("?", "%s")

    # ── 2. date('now', '-N unit') → (NOW() - INTERVAL 'N unit') ───────────────
    def _date_interval(m):
        sign = m.group(1)       # '-' or '+'
        n    = m.group(2)       # numeric value
        unit = m.group(3)       # 'days', 'months', etc.
        direction = "+" if sign == "+" else "-"
        return f"(NOW() {direction} INTERVAL '{n} {unit}')"

    sql = re.sub(
        r"date\s*\(\s*'now'\s*,\s*'([+-])(\d+)\s+(\w+)'\s*\)",
        _date_interval,
        sql,
        flags=re.IGNORECASE,
    )

    # ── 3. date('now', 'start of day') → (NOW())::date ────────────────────────
    sql = re.sub(
        r"date\s*\(\s*'now'\s*,\s*'start of day'\s*\)",
        "(NOW())::date",
        sql,
        flags=re.IGNORECASE,
    )

    # ── 4. date('now', %s || ' days') — dynamic interval via concat param ─────
    #  SQLite: date('now', '-7' || ' days')  →  PG: (NOW() + (%s || ' days')::interval)
    sql = re.sub(
        r"date\s*\(\s*'now'\s*,\s*%s\s*\|\|\s*'[^']+'\s*\)",
        "(NOW() + (%s || ' days')::interval)",
        sql,
        flags=re.IGNORECASE,
    )

    # ── 5. strftime('%fmt', col_or_expr) → TO_CHAR(expr::timestamp, 'PG_FMT') ─
    def _strftime(m):
        fmt = m.group(1)
        col = m.group(2).strip()
        pg_fmt = (
            fmt.replace("%Y", "YYYY")
               .replace("%m", "MM")
               .replace("%d", "DD")
               .replace("%H", "HH24")
               .replace("%M", "MI")
               .replace("%S", "SS")
        )
        return f"TO_CHAR({col}::timestamp, '{pg_fmt}')"

    sql = re.sub(
        r"strftime\s*\(\s*'([^']+)'\s*,\s*((?:[^()',]+|\w+\s*\([^)]*\))+)\)",
        _strftime,
        sql,
        flags=re.IGNORECASE,
    )

    # ── 6. julianday difference → EXTRACT(EPOCH…)/86400 ──────────────────────
    #  SQLite: cast(julianday('now') - julianday(MAX(s.sold_at)) as integer) || ' days ago'
    #  PG:     CONCAT(FLOOR(EXTRACT(EPOCH FROM NOW()-expr::timestamp)/86400)::INT, ' days ago')
    sql = re.sub(
        r"cast\s*\(\s*julianday\s*\(\s*'now'\s*\)\s*-\s*julianday\s*\("
        r"((?:[^()]+|\([^()]*\))+)"
        r"\)\s*as\s*integer\s*\)\s*\|\|\s*'\s*days ago'",
        r"CONCAT(FLOOR(EXTRACT(EPOCH FROM NOW() - (\1)::timestamp) / 86400)::INT, ' days ago')",
        sql,
        flags=re.IGNORECASE,
    )

    # ── 7. Bare date(column) → (column)::date ────────────────────────────────
    #  By this point, all date('now', ...) patterns are already replaced.
    #  Remaining date(expr) calls are SQLite column-to-date casts.
    #  Handles: date(s.sold_at), date(sold_at), date(MAX(s.sold_at)), etc.
    def _date_cast(m):
        expr = m.group(1).strip()
        return f"({expr})::date"

    sql = re.sub(
        r"\bdate\s*\(((?:[^()]+|\([^()]*\))*)\)",
        _date_cast,
        sql,
        flags=re.IGNORECASE,
    )

    return sql


# ══════════════════════════════════════════════════════════════════════════════
#  UNIFIED CONNECTION WRAPPER
# ══════════════════════════════════════════════════════════════════════════════

class _PgCursor:
    """
    Wraps a psycopg2 RealDictCursor to expose the same interface as
    sqlite3.Cursor. Translates ? → %s automatically and emulates lastrowid
    for tables with a SERIAL PRIMARY KEY via RETURNING id on INSERTs.
    """
    def __init__(self, raw_cursor):
        self._cur = raw_cursor
        self.rowcount = 0
        self.lastrowid = None

    def execute(self, sql, params=()):
        sql = _translate_sql(sql)

        # For INSERT into tables with a SERIAL id, append RETURNING id
        # so we can emulate sqlite3's cursor.lastrowid.
        # SKIP for user_profiles (PK is firebase_uid, no `id` column).
        _needs_returning = False
        if sql.strip().upper().startswith("INSERT") and "RETURNING" not in sql.upper():
            table_match = re.match(
                r"\s*INSERT\s+(?:OR\s+\w+\s+)?INTO\s+(\w+)",
                sql,
                re.IGNORECASE,
            )
            if table_match and table_match.group(1).lower() in _TABLES_WITH_SERIAL_ID:
                sql = sql.rstrip().rstrip(";") + " RETURNING id"
                _needs_returning = True

        self._cur.execute(sql, params if params else None)
        self.rowcount = self._cur.rowcount

        if _needs_returning:
            row = self._cur.fetchone()
            if row:
                self.lastrowid = row.get("id") if isinstance(row, dict) else row[0]

        return self

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def __iter__(self):
        return iter(self.fetchall())


class _PgConnection:
    """
    Wraps a psycopg2 connection to expose the same interface as
    sqlite3.Connection: execute(), cursor(), commit(), close().
    """
    def __init__(self, raw_conn):
        self._conn = raw_conn

    def execute(self, sql, params=()):
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        wrapper = _PgCursor(cur)
        wrapper.execute(sql, params)
        return wrapper

    def cursor(self):
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        return _PgCursor(cur)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.commit()
        self.close()


# ══════════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def get_connection():
    """Return a DB connection. Callers use the same interface regardless of backend."""
    if USE_POSTGRES:
        raw = psycopg2.connect(DATABASE_URL)
        return _PgConnection(raw)
    else:
        conn = sqlite3.connect(_SQLITE_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


# ══════════════════════════════════════════════════════════════════════════════
#  SCHEMA
# ══════════════════════════════════════════════════════════════════════════════

_SQLITE_SCHEMA = [
    """CREATE TABLE IF NOT EXISTS user_profiles (
      firebase_uid   TEXT PRIMARY KEY,
      email          TEXT NOT NULL,
      full_name      TEXT NOT NULL DEFAULT '',
      phone          TEXT DEFAULT '',
      city           TEXT DEFAULT '',
      state          TEXT DEFAULT '',
      business_name  TEXT DEFAULT '',
      business_address TEXT DEFAULT '',
      gstin          TEXT DEFAULT '',
      pan_number     TEXT DEFAULT '',
      business_type  TEXT DEFAULT 'trading',
      business_sector TEXT DEFAULT 'general',
      turnover_range TEXT DEFAULT 'below_1cr',
      msme_category  TEXT DEFAULT 'micro',
      payment_mode   TEXT DEFAULT 'mixed',
      onboarded      INTEGER DEFAULT 0,
      created_at     TEXT DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS products (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id     TEXT NOT NULL DEFAULT 'demo',
      name        TEXT NOT NULL,
      category    TEXT NOT NULL DEFAULT 'general',
      price       REAL NOT NULL,
      stock       INTEGER NOT NULL DEFAULT 0,
      created_at  TEXT DEFAULT (datetime('now')),
      UNIQUE(user_id, name)
    )""",
    """CREATE TABLE IF NOT EXISTS sales (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id     TEXT NOT NULL DEFAULT 'demo',
      product_id  INTEGER NOT NULL,
      quantity    INTEGER NOT NULL,
      total_price REAL NOT NULL,
      sold_at     TEXT DEFAULT (datetime('now')),
      FOREIGN KEY (product_id) REFERENCES products(id)
    )""",
    """CREATE TABLE IF NOT EXISTS bills (
      id            INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id       TEXT NOT NULL DEFAULT 'demo',
      bill_number   TEXT NOT NULL,
      customer_name TEXT DEFAULT '',
      items_json    TEXT NOT NULL,
      subtotal      REAL NOT NULL DEFAULT 0,
      gst_amount    REAL NOT NULL DEFAULT 0,
      total         REAL NOT NULL,
      created_at    TEXT DEFAULT (datetime('now')),
      UNIQUE(user_id, bill_number)
    )""",
    """CREATE TABLE IF NOT EXISTS alerts (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id     TEXT NOT NULL DEFAULT 'demo',
      level       TEXT NOT NULL,
      message     TEXT NOT NULL,
      created_at  TEXT DEFAULT (datetime('now')),
      is_read     INTEGER DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS festival_demands (
      id              INTEGER PRIMARY KEY AUTOINCREMENT,
      festival_name   TEXT NOT NULL UNIQUE,
      categories_json TEXT NOT NULL,
      items_json      TEXT NOT NULL,
      source          TEXT NOT NULL DEFAULT 'ai',
      created_at      TEXT DEFAULT (datetime('now'))
    )""",
]

_POSTGRES_SCHEMA = [
    """CREATE TABLE IF NOT EXISTS user_profiles (
      firebase_uid     TEXT PRIMARY KEY,
      email            TEXT NOT NULL,
      full_name        TEXT NOT NULL DEFAULT '',
      phone            TEXT DEFAULT '',
      city             TEXT DEFAULT '',
      state            TEXT DEFAULT '',
      business_name    TEXT DEFAULT '',
      business_address TEXT DEFAULT '',
      gstin            TEXT DEFAULT '',
      pan_number       TEXT DEFAULT '',
      business_type    TEXT DEFAULT 'trading',
      business_sector  TEXT DEFAULT 'general',
      turnover_range   TEXT DEFAULT 'below_1cr',
      msme_category    TEXT DEFAULT 'micro',
      payment_mode     TEXT DEFAULT 'mixed',
      onboarded        INTEGER DEFAULT 0,
      created_at       TIMESTAMP DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS products (
      id          SERIAL PRIMARY KEY,
      user_id     TEXT NOT NULL DEFAULT 'demo',
      name        TEXT NOT NULL,
      category    TEXT NOT NULL DEFAULT 'general',
      price       REAL NOT NULL,
      stock       INTEGER NOT NULL DEFAULT 0,
      created_at  TIMESTAMP DEFAULT NOW(),
      UNIQUE(user_id, name)
    )""",
    """CREATE TABLE IF NOT EXISTS sales (
      id          SERIAL PRIMARY KEY,
      user_id     TEXT NOT NULL DEFAULT 'demo',
      product_id  INTEGER NOT NULL,
      quantity    INTEGER NOT NULL,
      total_price REAL NOT NULL,
      sold_at     TIMESTAMP DEFAULT NOW(),
      FOREIGN KEY (product_id) REFERENCES products(id)
    )""",
    """CREATE TABLE IF NOT EXISTS bills (
      id            SERIAL PRIMARY KEY,
      user_id       TEXT NOT NULL DEFAULT 'demo',
      bill_number   TEXT NOT NULL,
      customer_name TEXT DEFAULT '',
      items_json    TEXT NOT NULL,
      subtotal      REAL NOT NULL DEFAULT 0,
      gst_amount    REAL NOT NULL DEFAULT 0,
      total         REAL NOT NULL,
      created_at    TIMESTAMP DEFAULT NOW(),
      UNIQUE(user_id, bill_number)
    )""",
    """CREATE TABLE IF NOT EXISTS alerts (
      id          SERIAL PRIMARY KEY,
      user_id     TEXT NOT NULL DEFAULT 'demo',
      level       TEXT NOT NULL,
      message     TEXT NOT NULL,
      created_at  TIMESTAMP DEFAULT NOW(),
      is_read     INTEGER DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS festival_demands (
      id              SERIAL PRIMARY KEY,
      festival_name   TEXT NOT NULL UNIQUE,
      categories_json TEXT NOT NULL,
      items_json      TEXT NOT NULL,
      source          TEXT NOT NULL DEFAULT 'ai',
      created_at      TIMESTAMP DEFAULT NOW()
    )""",
]


def init_db():
    """Create tables and seed demo data. Safe to call multiple times."""
    if USE_POSTGRES:
        raw = psycopg2.connect(DATABASE_URL)
        cur = raw.cursor()
        for stmt in _POSTGRES_SCHEMA:
            cur.execute(stmt)
        raw.commit()
        cur.close()
        conn = _PgConnection(raw)
        seed_data(conn)
        raw.close()
    else:
        conn = sqlite3.connect(_SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        for stmt in _SQLITE_SCHEMA:
            conn.execute(stmt)
        conn.commit()
        seed_data(conn)
        conn.close()


# ══════════════════════════════════════════════════════════════════════════════
#  DEMO DATA SEEDING
# ══════════════════════════════════════════════════════════════════════════════

_SEED_PRODUCTS = [
    ("Tata Salt (1kg)",              "grocery",       28.0,  150),
    ("Aashirvaad Atta (5kg)",        "grocery",      245.0,   80),
    ("Fortune Sunflower Oil (1L)",   "grocery",      145.0,   60),
    ("India Gate Basmati Rice (5kg)","grocery",       425.0,   45),
    ("Toor Dal (1kg)",               "grocery",      140.0,   70),
    ("Sugar (1kg)",                  "grocery",       48.0,  120),
    ("Mother Dairy Ghee (1L)",       "dairy",        550.0,   25),
    ("MDH Chana Masala (100g)",      "grocery",       55.0,   90),
    ("Surf Excel Detergent (1kg)",   "fmcg",         210.0,   55),
    ("Vim Dishwash Bar (3pk)",       "fmcg",          72.0,   90),
    ("Colgate MaxFresh (150g)",      "personal_care",  95.0, 100),
    ("Dove Soap (100g)",             "personal_care",  56.0, 130),
    ("Pantene Shampoo (180ml)",      "personal_care", 165.0,  40),
    ("Dettol Handwash (200ml)",      "personal_care",  85.0,  65),
    ("Nivea Body Lotion (200ml)",    "personal_care", 195.0,  30),
    ("Maggi Noodles (12pk)",         "packaged_food", 168.0,  75),
    ("Haldiram Namkeen (400g)",      "snacks",        120.0,  60),
    ("Parle-G Biscuits (800g)",      "packaged_food",  70.0, 100),
    ("Britannia Good Day (250g)",    "packaged_food",  45.0,  80),
    ("Amul Butter (500g)",           "dairy",         270.0,  35),
    ("Lays Chips (52g) Pack of 10",  "snacks",        200.0,  50),
    ("Kaju Katli Box (500g)",        "sweets",        450.0,  20),
    ("Soan Papdi Box (250g)",        "sweets",        120.0,  40),
    ("Rasgulla Tin (1kg)",           "sweets",        220.0,  30),
    ("Decorative Diya Set (12pcs)",  "decorations",   180.0,  35),
    ("LED String Lights (10m)",      "lights",        350.0,  25),
    ("Holi Colour Pack (5 colours)", "colours",        80.0,  50),
    ("Cotton Kurta (Men)",           "clothing",      650.0,  20),
    ("Dupatta (Women)",              "clothing",      350.0,  30),
    ("Kids T-Shirt",                 "clothing",      250.0,  40),
    ("boAt Earbuds",                 "electronics",  1299.0,  15),
    ("Syska LED Bulb (9W) 3pk",      "electronics",   299.0,  50),
    ("USB Charger Cable",            "electronics",   199.0,  70),
    ("Classmate Notebook (6pk)",     "stationery",    180.0,  60),
    ("Cello Pen Set (10pcs)",        "stationery",     80.0,  80),
    ("Camlin Colour Box",            "stationery",    120.0,  35),
    ("Gift Hamper Box",              "gifts",         800.0,  15),
    ("Dry Fruits Box (500g)",        "gifts",         650.0,  20),
    ("Screwdriver Set (6pcs)",       "hardware",      250.0,  30),
    ("Fevicol (500g)",               "hardware",      120.0,  45),
    ("Steel Lunch Box (3-tier)",     "kitchenware",   350.0,  25),
    ("Prestige Cooker (3L)",         "kitchenware",  1550.0,  10),
    ("Milton Water Bottle (1L)",     "kitchenware",   250.0,  40),
]

_HIGH_FREQ = [
    "Tata Salt (1kg)", "Aashirvaad Atta (5kg)", "Fortune Sunflower Oil (1L)",
    "Sugar (1kg)", "Toor Dal (1kg)", "Colgate MaxFresh (150g)", "Dove Soap (100g)",
    "Maggi Noodles (12pk)", "Parle-G Biscuits (800g)", "Surf Excel Detergent (1kg)",
    "Vim Dishwash Bar (3pk)", "Dettol Handwash (200ml)", "Britannia Good Day (250g)",
    "MDH Chana Masala (100g)",
]
_MED_FREQ = [
    "India Gate Basmati Rice (5kg)", "Mother Dairy Ghee (1L)", "Pantene Shampoo (180ml)",
    "Haldiram Namkeen (400g)", "Amul Butter (500g)", "Classmate Notebook (6pk)",
    "Cello Pen Set (10pcs)", "USB Charger Cable", "Syska LED Bulb (9W) 3pk",
    "Milton Water Bottle (1L)", "Kids T-Shirt", "Lays Chips (52g) Pack of 10",
    "Nivea Body Lotion (200ml)",
]
_LOW_FREQ = [
    "Kaju Katli Box (500g)", "Soan Papdi Box (250g)", "Rasgulla Tin (1kg)",
    "Cotton Kurta (Men)", "Dupatta (Women)", "boAt Earbuds",
    "Gift Hamper Box", "Dry Fruits Box (500g)", "Prestige Cooker (3L)",
    "Steel Lunch Box (3-tier)", "LED String Lights (10m)", "Decorative Diya Set (12pcs)",
    "Holi Colour Pack (5 colours)", "Camlin Colour Box", "Screwdriver Set (6pcs)",
    "Fevicol (500g)",
]


def seed_data(conn):
    """Seed realistic MSME demo data. No-op if already seeded."""
    if USE_POSTGRES:
        raw_cur = conn._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        raw_cur.execute("SELECT COUNT(*) as count FROM products WHERE user_id = 'demo'")
        count = raw_cur.fetchone()["count"]
    else:
        row = conn.execute("SELECT COUNT(*) as count FROM products WHERE user_id = 'demo'").fetchone()
        count = row["count"]

    if count > 0:
        if USE_POSTGRES:
            raw_cur.close()
        return

    print("Seeding realistic MSME inventory data (demo user)...")

    if USE_POSTGRES:
        for name, cat, price, stock in _SEED_PRODUCTS:
            raw_cur.execute(
                "INSERT INTO products (user_id, name, category, price, stock) "
                "VALUES ('demo', %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                (name, cat, price, stock),
            )
        conn._conn.commit()

        raw_cur.execute("SELECT id, name, price FROM products WHERE user_id = 'demo'")
        pmap = {r["name"]: {"id": r["id"], "price": r["price"]} for r in raw_cur.fetchall()}

        _gen_sales(
            insert_fn=lambda pid, qty, total, ts: raw_cur.execute(
                "INSERT INTO sales (user_id, product_id, quantity, total_price, sold_at) "
                "VALUES ('demo', %s, %s, %s, %s)", (pid, qty, total, ts),
            ),
            commit_fn=conn._conn.commit,
            pmap=pmap,
        )
        raw_cur.close()
    else:
        for name, cat, price, stock in _SEED_PRODUCTS:
            conn.execute(
                "INSERT OR IGNORE INTO products (user_id, name, category, price, stock) "
                "VALUES ('demo', ?, ?, ?, ?)", (name, cat, price, stock),
            )
        conn.commit()

        rows = conn.execute("SELECT id, name, price FROM products WHERE user_id = 'demo'").fetchall()
        pmap = {r["name"]: {"id": r["id"], "price": r["price"]} for r in rows}

        _gen_sales(
            insert_fn=lambda pid, qty, total, ts: conn.execute(
                "INSERT INTO sales (user_id, product_id, quantity, total_price, sold_at) "
                "VALUES ('demo', ?, ?, ?, ?)", (pid, qty, total, ts),
            ),
            commit_fn=conn.commit,
            pmap=pmap,
        )

    print(f"Seeded {len(_SEED_PRODUCTS)} products with 30 days of sales history.")


def _gen_sales(insert_fn, commit_fn, pmap):
    """Generate 30 days of realistic sales data."""
    random.seed(42)
    schedule = [
        (_HIGH_FREQ, 0.70, (1, 5)),
        (_MED_FREQ,  0.40, (1, 3)),
        (_LOW_FREQ,  0.15, (1, 2)),
    ]
    for days_ago in range(30, -1, -1):
        for freq_list, prob, qty_range in schedule:
            for name in freq_list:
                if name in pmap and random.random() < prob:
                    qty = random.randint(*qty_range)
                    p = pmap[name]
                    ts = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
                    insert_fn(p["id"], qty, qty * p["price"], ts)
    commit_fn()
