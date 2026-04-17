import os
from datetime import datetime, timedelta

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'profitpilot.db')

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'YOUR_KEY_HERE')
# Calendar API key (optional: falls back to GOOGLE_API_KEY if not set)
GOOGLE_CALENDAR_KEY = os.getenv('GOOGLE_CALENDAR_KEY', GOOGLE_API_KEY)
GOOGLE_CALENDAR_ID = 'en.indian#holiday@group.v.calendar.google.com'
GOOGLE_CALENDAR_URL = 'https://www.googleapis.com/calendar/v3/calendars'
FESTIVAL_COUNTRY = 'IN'
FESTIVAL_LOOKAHEAD_DAYS = 15

# ── Stock Algorithm Thresholds ────────────────────────────────────────
DEAD_STOCK_DAYS = 14       # No sales for 14 days = dead stock
LOW_STOCK_THRESHOLD = 10   # Stock below 10 = low stock alert
RESTOCK_BUFFER = 20        # Extra buffer to add to restock recommendation
MOVING_AVG_DAYS = 7        # Days to average for demand prediction

# ── MSME Specific Constants (FY 2025-26) ──────────────────────────────
MSME_MICRO_TURNOVER = 50000000      # 5 Crore (investment) / varies for turnover
MSME_SMALL_TURNOVER = 500000000     # 50 Crore
MSME_MEDIUM_TURNOVER = 2500000000   # 250 Crore

# Section 44AD Presumptive Taxation
SEC_44AD_TURNOVER_LIMIT = 20000000         # 2 Crore standard
SEC_44AD_DIGITAL_TURNOVER_LIMIT = 30000000 # 3 Crore if 95%+ digital receipts
SEC_44AD_DIGITAL_RATE = 0.06               # 6% of turnover for digital
SEC_44AD_CASH_RATE = 0.08                  # 8% of turnover for cash

# GST Composition Scheme
COMPOSITION_TURNOVER_LIMIT = 15000000      # 1.5 Crore
COMPOSITION_TAX_RATE = 0.01                # 1% for manufacturers/traders

COST_RATIO = 0.70  # 70% assumed cost -> 30% gross margin

# ── Income Tax Slabs (FY 2025-26 — New Regime, Default) ──────────────
INCOME_TAX_NEW_REGIME = [
    (400000, 0.0),       # Up to 4L: NIL
    (800000, 0.05),      # 4L - 8L: 5%
    (1200000, 0.10),     # 8L - 12L: 10%
    (1600000, 0.15),     # 12L - 16L: 15%
    (2000000, 0.20),     # 16L - 20L: 20%
    (2400000, 0.25),     # 20L - 24L: 25%
    (float('inf'), 0.30) # Above 24L: 30%
]

# Section 87A Rebate — New Regime
SEC_87A_INCOME_LIMIT_NEW = 1200000  # 12 Lakh
SEC_87A_REBATE_NEW = 60000          # Up to 60,000

# Old Regime (Optional)
INCOME_TAX_OLD_REGIME = [
    (250000, 0.0),       # Up to 2.5L: NIL
    (500000, 0.05),      # 2.5L - 5L: 5%
    (1000000, 0.20),     # 5L - 10L: 20%
    (float('inf'), 0.30) # Above 10L: 30%
]
SEC_87A_INCOME_LIMIT_OLD = 500000   # 5 Lakh
SEC_87A_REBATE_OLD = 12500          # Up to 12,500

# ── GST Category Rates (Post Sep 2025 — 3-Slab System) ───────────────
# 0% = Exempt essentials, 5% = everyday goods, 18% = standard, 40% = sin/luxury
CATEGORY_GST_RATES = {
    # 0% Exempt (Essential / Educational)
    "fresh_produce": 0.0,
    "milk": 0.0,
    "grains": 0.0,
    "stationery": 0.0,       # Notebooks, pens, educational items - exempt

    # 5% — Everyday consumer goods
    "grocery": 0.05,
    "fmcg": 0.05,
    "packaged_food": 0.05,
    "sweets": 0.05,
    "dairy": 0.05,
    "snacks": 0.05,
    "personal_care": 0.05,
    "kitchenware": 0.05,
    "colours": 0.05,
    "clothing": 0.05,         # Clothing under Rs.1000 is 5%

    # 18% — Standard rate
    "general": 0.18,
    "electronics": 0.18,
    "lights": 0.18,
    "gifts": 0.18,
    "hardware": 0.18,
    "decorations": 0.18,
    "cosmetics": 0.18,

    # 40% — Sin / Luxury
    "drinks": 0.40,
    "tobacco": 0.40,
    "luxury": 0.40,
}

# ── Festival → Category Map ──────────────────────────────────────────
FESTIVAL_CATEGORY_MAP = {
    "diwali":           ["sweets", "lights", "gifts", "electronics", "decorations", "clothing"],
    "holi":             ["colours", "sweets", "clothing", "personal_care"],
    "eid":              ["clothing", "sweets", "gifts", "personal_care"],
    "christmas":        ["gifts", "electronics", "clothing", "sweets", "decorations"],
    "navratri":         ["clothing", "sweets", "decorations"],
    "dussehra":         ["sweets", "gifts", "clothing"],
    "raksha bandhan":   ["sweets", "gifts"],
    "ganesh chaturthi": ["sweets", "decorations", "lights", "gifts"],
    "pongal":           ["grocery", "sweets", "kitchenware"],
    "onam":             ["clothing", "sweets", "grocery"],
    "makar sankranti":  ["sweets", "grocery", "kitchenware"],
    "baisakhi":         ["clothing", "sweets", "grocery"],
    "new year":         ["drinks", "sweets", "gifts", "electronics"],
    "independence day": ["clothing", "stationery"],
    "republic day":     ["clothing", "stationery"],
    "janmashtami":      ["sweets", "dairy", "decorations"],
    "karwa chauth":     ["cosmetics", "clothing", "gifts"],
    "lohri":            ["grocery", "sweets"],
    "chhath":           ["grocery", "sweets", "kitchenware"],
}

# ── Demo Festival Fallback (dynamically generated) ────────────────────
_today = datetime.now()
DEMO_FESTIVALS_FALLBACK = [
    {"name": "Diwali",           "date": (_today + timedelta(days=3)).strftime('%Y-%m-%d'),  "relevant_categories": ["sweets", "lights", "gifts", "electronics", "decorations"]},
    {"name": "Bhai Dooj",        "date": (_today + timedelta(days=5)).strftime('%Y-%m-%d'),  "relevant_categories": ["sweets", "gifts"]},
    {"name": "Holi",             "date": (_today + timedelta(days=12)).strftime('%Y-%m-%d'), "relevant_categories": ["colours", "sweets", "clothing", "personal_care"]},
    {"name": "Ganesh Chaturthi", "date": (_today + timedelta(days=20)).strftime('%Y-%m-%d'), "relevant_categories": ["sweets", "decorations", "lights"]},
    {"name": "Raksha Bandhan",   "date": (_today + timedelta(days=28)).strftime('%Y-%m-%d'), "relevant_categories": ["sweets", "gifts"]},
]
