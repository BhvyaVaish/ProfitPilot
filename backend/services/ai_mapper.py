"""
ai_mapper.py — Gemini AI demand prediction for festivals.

Uses Google GenAI (Gemini) to predict the top 15 high-demand
product categories and items for any given festival.
Results are cached in the `festival_demands` database table.
"""

import json
from google import genai
from config import GOOGLE_API_KEY, FESTIVAL_CATEGORY_MAP

# ── Configure Gemini ─────────────────────────────────────────────────────────
_CLIENT = None

def _ensure_configured():
    """Lazy-init the Gemini client so cold-starts don't fail if key is missing."""
    global _CLIENT
    if _CLIENT is not None:
        return
    key = GOOGLE_API_KEY
    if key and key != 'YOUR_KEY_HERE':
        _CLIENT = genai.Client(api_key=key)


# ── Hardcoded fallback (fast path — no API call needed) ──────────────────────
# ── Hardcoded fallback (fast path — no API call needed) ──────────────────────
def _get_from_hardcoded_map(festival_name: str) -> dict | None:
    """Check if this festival has a hardcoded mapping in config.py."""
    name_lower = festival_name.lower()
    
    # Precise matches for common Indian festivals to save API quota
    detailed_map = {
        "diwali": {
            "categories": ["sweets", "lights", "gifts", "electronics", "decorations", "clothing", "grocery", "packaged_food"],
            "items": ["Kaju Katli Box", "LED String Lights", "Dry Fruit Gift Pack", "Earthen Diyas", "Rangoli Colours", "New Festive Clothes", "Cooking Oil", "Ghee", "Firecrackers", "Torans", "Home Decor", "Silver Coins", "Smartphones", "Kitchen Appliances", "Gold Jewelry"]
        },
        "holi": {
            "categories": ["colours", "sweets", "clothing", "personal_care", "drinks", "grocery"],
            "items": ["Herbal Gulal", "Water Guns (Pichkari)", "Gujiya Sweets", "White Kurta/T-Shirt", "Skin Protection Oil", "Thandai Mix", "Balloons", "Namkeen Snacks", "Coconut Oil", "Hair Care Kits", "Sunglasses", "Waterproof Phone Pouches", "Buckets", "Cold Drinks", "Snack Hampers"]
        },
        "raksha bandhan": {
            "categories": ["sweets", "gifts", "clothing", "personal_care"],
            "items": ["Designer Rakhi", "Rakhi Set", "Soan Papdi", "Chocolate Gift Box", "Perfume Set", "Wrist Watches", "Ladies Suits", "Greeting Cards", "Roli Chawal Pack", "Brother-Sister Gifts", "Handbags", "Dry Fruit Boxes", "Silver Rakhis", "Wallets", "Cosmetic Kits"]
        },
        "eid": {
            "categories": ["clothing", "sweets", "gifts", "personal_care", "grocery", "meat_products"],
            "items": ["Seviyan (Vermicelli)", "Dates (Khajur)", "New Eid Clothes", "Attar (Perfume)", "Biryani Masala", "Dry Fruits", "Sheer Khurma Ingredients", "Gifts for Kids", "Bangles", "Henna (Mehendi) cones", "Sherwanis", "Suits", "Ghee", "Milk Packs", "Jewelry"]
        },
        "christmas": {
            "categories": ["gifts", "electronics", "clothing", "sweets", "decorations", "packaged_food"],
            "items": ["Plum Cake", "Christmas Tree", "Decorations & Ornaments", "Santa Hats", "Gift Wrapping Paper", "Chocolates", "Winter Jackets", "LED Stars", "Greeting Cards", "Electronic Gadgets", "Party Snacks", "Wine (Non-alcoholic)", "Cookies", "Candles", "New Year Planners"]
        }
    }

    for key, data in detailed_map.items():
        if key in name_lower:
            return {
                "categories": data["categories"],
                "items": data["items"],
                "source": "hardcoded"
            }
            
    # Fallback to simple map from config
    for key, categories in FESTIVAL_CATEGORY_MAP.items():
        if key in name_lower:
            return {
                "categories": categories,
                "items": [f"{cat.replace('_', ' ').title()} items" for cat in categories],
                "source": "hardcoded"
            }
    return None


# ── Gemini AI prediction ────────────────────────────────────────────────────
def predict_festival_demand(festival_name: str) -> dict:
    """
    Use Gemini AI to predict the top 15 high-demand product categories
    and specific items for a given festival in India.
    """
    # 1. Try hardcoded map first (instant, free)
    hardcoded = _get_from_hardcoded_map(festival_name)
    if hardcoded:
        return hardcoded

    # 2. Try Gemini AI
    _ensure_configured()
    if _CLIENT:
        try:
            prompt = f"""You are an Indian retail market expert. For the festival "{festival_name}" in India,
predict the top 15 product categories and specific items that will see increased demand.

Focus on items that a small kirana/MSME shop would sell. Categories should be from this list when applicable:
grocery, fmcg, personal_care, packaged_food, snacks, dairy, sweets, decorations, lights,
colours, clothing, electronics, stationery, gifts, hardware, kitchenware, cosmetics, drinks.

Respond ONLY with valid JSON in this exact format, no other text:
{{
    "categories": ["category1", "category2", ...],
    "items": ["Specific Item 1", "Specific Item 2", ...]
}}

Return exactly 15 items and their relevant categories (can be fewer unique categories)."""

            # Try standard model names
            model_name = 'gemini-1.5-flash'
            try:
                response = _CLIENT.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
            except Exception:
                # Fallback to latest alias if standard name fails (some keys/regions prefer this)
                model_name = 'gemini-flash-latest'
                response = _CLIENT.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
            
            text = response.text.strip()

            # Extract JSON from response (handle markdown code blocks)
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()

            data = json.loads(text)
            return {
                "categories": data.get("categories", [])[:15],
                "items": data.get("items", [])[:15],
                "source": "ai"
            }
        except Exception as e:
            print(f"[AI Mapper] Gemini error for '{festival_name}': {e}")

    # 3. Generic fallback
    return {
        "categories": ["sweets", "gifts", "clothing", "decorations"],
        "items": ["Sweets Box", "Gift Hamper", "Festive Clothing", "Decorative Items"],
        "source": "fallback"
    }


# ── Database cache layer ─────────────────────────────────────────────────────
def get_cached_demand(festival_name: str) -> dict | None:
    """Check if we already have AI predictions cached for this festival."""
    from database import get_connection
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT categories_json, items_json, source FROM festival_demands WHERE festival_name = ?",
            (festival_name,)
        ).fetchone()
        if row:
            return {
                "categories": json.loads(row["categories_json"]),
                "items": json.loads(row["items_json"]),
                "source": row["source"]
            }
        return None
    finally:
        conn.close()


def cache_demand(festival_name: str, demand: dict):
    """Save AI predictions to DB for reuse. Resilient to database locked errors."""
    import time
    from database import get_connection
    for attempt in range(3):
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO festival_demands (festival_name, categories_json, items_json, source) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT (festival_name) DO UPDATE SET "
                "categories_json = ?, items_json = ?, source = ?",
                (
                    festival_name,
                    json.dumps(demand["categories"]),
                    json.dumps(demand["items"]),
                    demand["source"],
                    json.dumps(demand["categories"]),
                    json.dumps(demand["items"]),
                    demand["source"],
                )
            )
            conn.commit()
            return  # Success
        except Exception as e:
            if "locked" in str(e).lower() and attempt < 2:
                time.sleep(0.5)
                continue
            print(f"[AI Mapper] Cache write error: {e}")
        finally:
            conn.close()


def get_or_predict_demand(festival_name: str) -> dict:
    """
    Main entry point: Get demand prediction from cache or generate new one.
    """
    # Check cache first
    cached = get_cached_demand(festival_name)
    if cached:
        return cached

    # Generate prediction
    demand = predict_festival_demand(festival_name)

    # Cache it (skip caching fallback results)
    if demand["source"] in ("ai", "hardcoded"):
        cache_demand(festival_name, demand)

    return demand
