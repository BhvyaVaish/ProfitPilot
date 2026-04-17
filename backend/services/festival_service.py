"""
festival_service.py — Real-time festival data via Google Calendar API.

Fetches upcoming Indian holidays for the next 15 days, then uses
the AI mapper (Gemini) to predict demand and match against user inventory.
"""

import requests
from datetime import datetime, timedelta
from urllib.parse import quote
from config import (GOOGLE_API_KEY, GOOGLE_CALENDAR_KEY, GOOGLE_CALENDAR_ID, GOOGLE_CALENDAR_URL,
                    FESTIVAL_LOOKAHEAD_DAYS, FESTIVAL_CATEGORY_MAP,
                    DEMO_FESTIVALS_FALLBACK)
from models import get_products_by_categories, get_all_products
from services.ai_mapper import get_or_predict_demand


def _fetch_google_calendar_holidays(days=None):
    """
    Fetch upcoming holidays from Google Calendar's public Indian holidays.
    Returns a list of {name, date} dicts.
    """
    if days is None:
        days = FESTIVAL_LOOKAHEAD_DAYS

    if GOOGLE_CALENDAR_KEY == 'YOUR_KEY_HERE':
        return None  # Signal to use fallback

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
        response = requests.get(url, params=params, timeout=10)
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
            print(f"[Festival Service] Google Calendar API error: {response.status_code} {response.text[:200]}")
            return None
    except Exception as e:
        print(f"[Festival Service] Google Calendar fetch error: {e}")
        return None


def get_upcoming_festivals(days=None):
    """
    Get upcoming festivals with AI-powered demand predictions.
    Uses Google Calendar API for real-time data, falls back to demo data.

    Returns list of:
    {
        "name": "Diwali",
        "date": "2026-10-20",
        "days_away": 3,
        "relevant_categories": ["sweets", "lights", ...],
        "relevant_products": ["Kaju Katli Box", ...],
        "demand_items": ["Kaju Katli", "LED Lights", ...],
        "source": "google_calendar" | "fallback"
    }
    """
    if days is None:
        days = FESTIVAL_LOOKAHEAD_DAYS

    today = datetime.today()
    upcoming = []

    # ── Try Google Calendar API first ────────────────────────────────────
    holidays = _fetch_google_calendar_holidays(days)

    if holidays is not None and len(holidays) > 0:
        for h in holidays:
            try:
                festival_date = datetime.strptime(h['date'], '%Y-%m-%d')
                diff = (festival_date - today).days
                # Include today and future dates within range
                if -1 <= diff <= days:
                    diff = max(0, diff)  # Clamp to 0 for today

                    # Get AI demand prediction (cached or fresh)
                    demand = get_or_predict_demand(h['name'])

                    upcoming.append({
                        "name": h['name'],
                        "date": h['date'],
                        "days_away": diff,
                        "relevant_categories": demand['categories'],
                        "relevant_products": [],  # Will be filled by inventory matching
                        "demand_items": demand['items'],
                        "source": "google_calendar",
                        "prediction_source": demand['source'],
                    })
            except (KeyError, ValueError) as e:
                print(f"[Festival Service] Parse error for {h}: {e}")
                continue
    else:
        # ── Fallback to demo data ────────────────────────────────────────
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
                        "relevant_categories": demand['categories'],
                        "relevant_products": [],
                        "demand_items": demand['items'],
                        "source": "fallback",
                        "prediction_source": demand['source'],
                    })
            except (KeyError, ValueError):
                continue

    return upcoming


def match_festivals_to_inventory(user_id='demo'):
    """
    Smart inventory matching: For each upcoming festival, check the user's
    inventory and generate actionable suggestions.

    Returns:
    {
        "festivals": [...],
        "suggestions": [
            {
                "type": "restock",  # or "opportunity"
                "festival": "Diwali",
                "days_away": 3,
                "product": "Kaju Katli Box (500g)",
                "current_stock": 5,
                "message": "Diwali in 3 days! Kaju Katli demand will spike. Current stock: 5. Consider adding 20+ units."
            },
            {
                "type": "opportunity",
                "festival": "Diwali",
                "days_away": 3,
                "item": "Rangoli Colours",
                "message": "Diwali in 3 days! Rangoli Colours demand is expected to rise. Consider adding this to your inventory."
            }
        ]
    }
    """
    festivals = get_upcoming_festivals()
    products = get_all_products(user_id)

    # Build lookup maps
    product_by_name_lower = {p['name'].lower(): p for p in products}
    product_by_category = {}
    for p in products:
        cat = p['category'].lower()
        if cat not in product_by_category:
            product_by_category[cat] = []
        product_by_category[cat].append(p)

    suggestions = []

    for festival in festivals:
        fcat = festival['relevant_categories']
        demand_items = festival.get('demand_items', [])
        fname = festival['name']
        fdays = festival['days_away']

        # ── 1. Check which demand categories match user inventory ────────
        matched_products = []
        for cat in fcat:
            cat_lower = cat.lower()
            if cat_lower in product_by_category:
                for p in product_by_category[cat_lower]:
                    matched_products.append(p)
                    # If stock is low, suggest restocking
                    if p['stock'] < 20:
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

        # Fill in relevant_products on the festival object
        festival['relevant_products'] = list(set(p['name'] for p in matched_products))

        # ── 2. Check for "opportunity" items not in inventory ─────────────
        for item in demand_items:
            item_lower = item.lower()
            # Check if user has any product with similar name
            has_it = any(item_lower in pname for pname in product_by_name_lower.keys())
            if not has_it:
                # Check if any category match exists (fuzzy)
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

    # Sort suggestions: closest festival first, then restock before opportunity
    type_order = {"restock": 0, "opportunity": 1}
    suggestions.sort(key=lambda s: (s['days_away'], type_order.get(s['type'], 2)))

    return {
        "festivals": festivals,
        "suggestions": suggestions[:25],  # Cap at 25 most relevant
    }
