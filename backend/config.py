import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'stockpilot.db')

CALENDARIFIC_API_KEY = os.getenv('CALENDARIFIC_API_KEY', 'YOUR_KEY_HERE')
CALENDARIFIC_URL = 'https://calendarific.com/api/v2/holidays'
FESTIVAL_COUNTRY = 'IN'

DEAD_STOCK_DAYS = 14       # No sales for 14 days = dead stock
LOW_STOCK_THRESHOLD = 10   # Stock below 10 = low stock alert
RESTOCK_BUFFER = 20        # Extra buffer to add to restock recommendation

MOVING_AVG_DAYS = 7        # Days to average for demand prediction

from datetime import datetime, timedelta

# Dynamically generate dates so the prediction module always works
_today = datetime.now()
DEMO_FESTIVALS_FALLBACK = [
    {"name": "Diwali", "date": (_today + timedelta(days=3)).strftime('%Y-%m-%d'), "relevant_categories": ["sweets", "lights", "gifts", "electronics"]},
    {"name": "Holi",   "date": (_today + timedelta(days=15)).strftime('%Y-%m-%d'), "relevant_categories": ["colours", "sweets", "clothing"]},
]

FESTIVAL_CATEGORY_MAP = {
    "diwali":       ["sweets", "lights", "gifts", "electronics"],
    "holi":         ["colours", "sweets", "clothing"],
    "eid":          ["clothing", "sweets", "gifts"],
    "christmas":    ["gifts", "electronics", "clothing", "sweets"],
    "navratri":     ["clothing", "sweets", "decorations"],
    "raksha bandhan": ["sweets", "gifts"],
    "new year":     ["drinks", "sweets", "gifts", "electronics"],
    "independence day": ["clothing", "flags"],
}

CATEGORY_GST_RATES = {
    "sweets": 0.05,
    "dairy": 0.05,
    "clothing": 0.05,
    "snacks": 0.12,
    "lights": 0.12,
    "general": 0.18,
    "colors": 0.18,
    "electronics": 0.18,
    "gifts": 0.18,
    "drinks": 0.28
}
