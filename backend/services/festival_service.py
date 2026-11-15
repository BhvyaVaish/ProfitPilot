"""
festival_service.py — Real-time festival data via Google Calendar API.

Fetches upcoming Indian holidays for the next 15 days, then uses
the AI mapper to predict demand and match against user inventory.
Includes in-memory TTL caching to prevent slow repeated external requests.
"""

import time
import requests
from datetime import datetime, timedelta
from urllib.parse import quote
from config import (GOOGLE_API_KEY, GOOGLE_CALENDAR_KEY, GOOGLE_CALENDAR_ID, GOOGLE_CALENDAR_URL,
                    FESTIVAL_LOOKAHEAD_DAYS, DEMO_FESTIVALS_FALLBACK)
from models import get_all_products
from services.ai_mapper import get_or_predict_demand

# In-memory cache for upcoming festivals to guarantee sub-millisecond responses
_CACHE_UPCOMING = None
_CACHE_TIMESTAMP = 0
_CACHE_TTL = 900  # 15 minutes

_CALENDAR_FAILED_UNTIL = 0


def _fetch_google_calendar_holidays(days=None):
    """
    Fetch upcoming holidays from Google Calendar's public Indian holidays.
    Returns a list of {name, date} dicts.
    """
    global _CALENDAR_FAILED_UNTIL

    if days is None:
        days = FESTIVAL_LOOKAHEAD_DAYS

    if not GOOGLE_CALENDAR_KEY or GOOGLE_CALENDAR_KEY == 'YOUR_KEY_HERE':
        return None

    # Don't retry if recently failed with auth/quota errors
    if time.time() < _CALENDAR_FAILED_UNTIL:
        return None

    now = datetime.utcnow()
    time_min = now.strftime('%Y-%m-%dT00:00:00Z')
    time_max = (now + timedelta(days=days)).strftime('%Y-%m-%dT23:59:59Z')

    encoded_cal_id = quote(GOOGLE_CALENDAR_ID, safe='')
    url = f"{GOOGLE_CALENDAR_URL}/{encoded_cal_id}/events"

    params = {
        'key': GOOGLE_CALENDAR_KEY,
        'timeMin': time_min,
        'timeMax': time_max,
        'singleEvents': 'true',
        'orderBy': 'startTime',
        'maxResults': 25,
    }

    try:
        response = requests.get(url, params=params, timeout=3)
        if response.status_code == 200:
            data = response.json()
            events = data.get('items', [])
            holidays = []
            for event in events:
                name = event.get('summary', '')
                start = event.get('start', {})
                date_str = start.get('date', start.get('dateTime', '')[:10])
                if name and date_str:
                    holidays.append({
                        'name': name,
                        'date': date_str,
                    })
            return holidays
        else:
            # Back off for 15 minutes on HTTP errors
            _CALENDAR_FAILED_UNTIL = time.time() + 900
            return None
    except Exception:
        _CALENDAR_FAILED_UNTIL = time.time() + 900
        return None


def get_upcoming_festivals(days=None):
    """
    Get upcoming festivals with AI-powered demand predictions.
    Uses cached result if available to guarantee fast page loads.
    """
    global _CACHE_UPCOMING, _CACHE_TIMESTAMP

    if days is None:
        days = FESTIVAL_LOOKAHEAD_DAYS

    now_ts = time.time()
    if _CACHE_UPCOMING is not None and (now_ts - _CACHE_TIMESTAMP) < _CACHE_TTL:
        return _CACHE_UPCOMING

    today = datetime.today()
    upcoming = []

    # 1. Try Google Calendar API first
    holidays = _fetch_google_calendar_holidays(days)

    if holidays is not None and len(holidays) > 0:
        for h in holidays:
            try:
                festival_date = datetime.strptime(h['date'], '%Y-%m-%d')
                diff = (festival_date - today).days
                if -1 <= diff <= days:
                    diff = max(0, diff)
                    demand = get_or_predict_demand(h['name'])
                    upcoming.append({
                        "name": h['name'],
                        "date": h['date'],
                        "days_away": diff,
                        "relevant_categories": demand.get('categories', []),
                        "relevant_products": [],
                        "demand_items": demand.get('items', []),
                        "source": "google_calendar",
                        "prediction_source": demand.get('source', 'default'),
                    })
            except Exception:
                continue
    else:
        # 2. Fast Fallback to Indian holidays calendar data
        for f in DEMO_FESTIVALS_FALLBACK:
            try:
                festival_date = datetime.strptime(f['date'], '%Y-%m-%d')
                diff = (festival_date - today).days
                if 0 <= diff <= days:
                    demand = get_or_predict_demand(f['name'])
                    upcoming.append({
                        "name": f['name'],
                        "date": f['date'],
                        "days_away": diff,
                        "relevant_categories": demand.get('categories', []),
                        "relevant_products": [],
                        "demand_items": demand.get('items', []),
                        "source": "fallback",
                        "prediction_source": demand.get('source', 'default'),
                    })
            except Exception:
                continue

    _CACHE_UPCOMING = upcoming
    _CACHE_TIMESTAMP = now_ts
    return upcoming


def match_festivals_to_inventory(user_id='demo'):
    """
    Smart inventory matching: For each upcoming festival, check the user's
    inventory and generate actionable suggestions.
    """
    festivals = get_upcoming_festivals()
    products = get_all_products(user_id)

    product_by_name_lower = {p['name'].lower(): p for p in products}
    product_by_category = {}
    for p in products:
        cat = p['category'].lower()
        if cat not in product_by_category:
            product_by_category[cat] = []
        product_by_category[cat].append(p)

    suggestions = []

    for festival in festivals:
        fcat = festival.get('relevant_categories', [])
        demand_items = festival.get('demand_items', [])
        fname = festival['name']
        fdays = festival['days_away']

        # 1. Match categories
        matched_products = []
        for cat in fcat:
            cat_lower = cat.lower()
            if cat_lower in product_by_category:
                for p in product_by_category[cat_lower]:
                    matched_products.append(p)
                    if p.get('stock', 0) < 20:
                        suggestions.append({
                            "type": "restock",
                            "festival": fname,
                            "days_away": fdays,
                            "product": p['name'],
                            "category": p['category'],
                            "current_stock": p['stock'],
                            "message": f"{fname} in {fdays} day(s)! {p['name']} demand will spike. "
                                       f"Current stock: {p['stock']}. Consider adding 20+ units."
                        })

        festival['relevant_products'] = list(set(p['name'] for p in matched_products))

        # 2. Check opportunity items
        for item in demand_items:
            item_lower = item.lower()
            has_it = any(item_lower in pname for pname in product_by_name_lower.keys())
            if not has_it:
                cat_match = any(cat.lower() in product_by_category for cat in fcat)
                suggestions.append({
                    "type": "opportunity",
                    "festival": fname,
                    "days_away": fdays,
                    "item": item,
                    "has_category": cat_match,
                    "message": f"{fname} in {fdays} day(s)! '{item}' demand is expected to rise. "
                               f"Consider adding this to your inventory."
                })

    type_order = {"restock": 0, "opportunity": 1}
    suggestions.sort(key=lambda s: (s['days_away'], type_order.get(s['type'], 2)))

    return {
        "festivals": festivals,
        "suggestions": suggestions[:25],
    }
