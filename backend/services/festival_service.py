import requests
from datetime import datetime
from config import CALENDARIFIC_API_KEY, CALENDARIFIC_URL, FESTIVAL_COUNTRY, FESTIVAL_CATEGORY_MAP, DEMO_FESTIVALS_FALLBACK
from models import get_products_by_categories

def get_upcoming_festivals(days=7):
    today = datetime.today()
    params = {
        'api_key': CALENDARIFIC_API_KEY,
        'country': FESTIVAL_COUNTRY,
        'year': today.year,
        'month': today.month,
        'type': 'national,religious'
    }
    
    holidays = []
    if CALENDARIFIC_API_KEY == 'YOUR_KEY_HERE':
        holidays_fallback = DEMO_FESTIVALS_FALLBACK
    else:
        try:
            response = requests.get(CALENDARIFIC_URL, params=params, timeout=5)
            if response.status_code == 200:
                holidays = response.json().get('response', {}).get('holidays', [])
            else:
                holidays_fallback = DEMO_FESTIVALS_FALLBACK
        except Exception:
            holidays_fallback = DEMO_FESTIVALS_FALLBACK
            
    upcoming = []
    
    if holidays:
        for h in holidays:
            date_str = h['date']['iso']
            festival_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
            diff = (festival_date - today).days
            if 0 <= diff <= days:
                name = h['name'].lower()
                cats = []
                for key, val in FESTIVAL_CATEGORY_MAP.items():
                    if key in name:
                        cats = val
                        break
                products = get_products_by_categories(cats) if cats else []
                upcoming.append({
                    "name": h['name'],
                    "date": date_str[:10],
                    "days_away": diff,
                    "relevant_categories": cats,
                    "relevant_products": [p['name'] for p in products]
                })
    else:
        for f in DEMO_FESTIVALS_FALLBACK:
            festival_date = datetime.strptime(f['date'], '%Y-%m-%d')
            diff = (festival_date - today).days
            if 0 <= diff <= days:
                cats = f['relevant_categories']
                products = get_products_by_categories(cats) if cats else []
                upcoming.append({
                    "name": f['name'],
                    "date": f['date'],
                    "days_away": diff,
                    "relevant_categories": cats,
                    "relevant_products": [p['name'] for p in products]
                })
                
    return upcoming
