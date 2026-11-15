"""
ai_mapper.py — Gemini AI demand prediction for festivals.

Uses Google GenAI (Gemini) to predict the top 15 high-demand
product categories and items for any given festival.
Results are cached in Firestore via firestore_db.py.
"""

import json
from google import genai
from config import GOOGLE_API_KEY, FESTIVAL_CATEGORY_MAP
import firestore_db

# ── Configure Gemini ─────────────────────────────────────────────────────────
_CLIENT = None
_CLIENT_FAILED = False

def _ensure_configured():
    """Lazy-init the Gemini client so cold-starts don't fail if key is missing."""
    global _CLIENT, _CLIENT_FAILED
    if _CLIENT_FAILED or _CLIENT is not None:
        return
    key = GOOGLE_API_KEY
    if key and key != 'YOUR_KEY_HERE':
        try:
            _CLIENT = genai.Client(api_key=key)
        except Exception:
            _CLIENT_FAILED = True
    else:
        _CLIENT_FAILED = True


# ── Comprehensive Indian Festival Map (Instant, 0 latency, free) ────────────
DETAILED_FESTIVAL_MAP = {
    "diwali": {
        "categories": ["sweets", "lights", "gifts", "electronics", "decorations", "clothing", "grocery", "packaged_food"],
        "items": ["Kaju Katli Box", "LED String Lights", "Dry Fruit Gift Pack", "Earthen Diyas", "Rangoli Colours", "New Festive Clothes", "Cooking Oil", "Ghee", "Firecrackers", "Torans", "Home Decor", "Silver Coins", "Smartphones", "Kitchen Appliances", "Gold Jewelry"]
    },
    "bhai dooj": {
        "categories": ["sweets", "gifts", "clothing", "personal_care", "packaged_food"],
        "items": ["Kaju Katli Box", "Chocolate Gift Box", "Dry Fruit Hamper", "Men's Kurta", "Wrist Watch", "Roli Chawal Pack", "Coconut (Gola)", "Sweets Hamper", "Wallets", "Perfume Set"]
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
    },
    "ganesh chaturthi": {
        "categories": ["sweets", "decorations", "grocery", "lights"],
        "items": ["Modak Box", "Peda", "Fresh Flowers", "Decorative Lights", "Puja Samagri", "Incense Sticks", "Ghee", "Dry Fruits", "Decorative Backdrop", "Aarti Sangrah"]
    },
    "navratri": {
        "categories": ["grocery", "packaged_food", "clothing", "puja_items"],
        "items": ["Kuttu Ka Atta", "Singhare Ka Atta", "Sendha Namak", "Sabudana", "Makhana", "Chunri", "Puja Ghee", "Dandiya Sticks", "Traditional Kurta", "Dry Fruits"]
    },
    "dussehra": {
        "categories": ["sweets", "clothing", "gifts", "decorations"],
        "items": ["Jalebi", "Fafda", "Festive Clothing", "Puja Items", "Gifts", "Sweets Box", "Home Decor"]
    },
    "karwa chauth": {
        "categories": ["clothing", "personal_care", "cosmetics", "sweets", "puja_items"],
        "items": ["Sargi Hamper", "Karwa Chauth Thali Set", "Mehendi Cones", "Bangles", "Saree / Suit", "Cosmetic Kit", "Mathri", "Dry Fruits", "Channi", "Sweets Box"]
    },
    "makar sankranti": {
        "categories": ["grocery", "sweets", "toys", "snacks"],
        "items": ["Kites (Patang)", "Manjha (Spool)", "Tilgul Laddoo", "Gajak", "Chikki", "Jaggery (Gud)", "Sesame Seeds (Til)", "Peanuts"]
    },
    "pongal": {
        "categories": ["grocery", "sweets", "decorations"],
        "items": ["Raw Rice", "Jaggery", "Earthen Pongal Pots", "Sugarcane", "Cashews", "Ghee", "Cardamom", "Puja Items"]
    },
    "onam": {
        "categories": ["clothing", "grocery", "sweets"],
        "items": ["Kasavu Saree", "Mundu", "Payasam Mix", "Banana Chips", "Jaggery", "Rice", "Fresh Flowers", "Ghee"]
    },
    "chhath": {
        "categories": ["grocery", "fruits", "puja_items"],
        "items": ["Thekua Ingredients", "Daura (Bamboo Basket)", "Soop", "Sugarcane", "Coconut", "Gangajal", "Ghee", "Wheat Flour", "Jaggery"]
    }
}


def _get_from_hardcoded_map(festival_name: str) -> dict | None:
    """Check if this festival has a hardcoded mapping."""
    name_lower = festival_name.lower()
    
    for key, data in DETAILED_FESTIVAL_MAP.items():
        if key in name_lower or name_lower in key:
            return {
                "categories": data["categories"],
                "items": data["items"],
                "source": "hardcoded"
            }
            
    # Fallback to simple map from config
    for key, categories in FESTIVAL_CATEGORY_MAP.items():
        if key in name_lower or name_lower in key:
            return {
                "categories": categories,
                "items": [f"{cat.replace('_', ' ').title()} items" for cat in categories],
                "source": "hardcoded"
            }
    return None


# ── Gemini AI prediction ────────────────────────────────────────────────────
def predict_festival_demand(festival_name: str) -> dict:
    """
    Predict high-demand product categories and specific items for a given festival.
    Uses instant local matching first, falls back to Gemini AI when available.
    """
    global _CLIENT_FAILED
    # 1. Try instant mapping first (0ms, 100% reliable)
    hardcoded = _get_from_hardcoded_map(festival_name)
    if hardcoded:
        return hardcoded

    # 2. Try Gemini AI if available and not previously failed
    if not _CLIENT_FAILED:
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
}}"""

                response = _CLIENT.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=prompt,
                )
                
                text = response.text.strip()
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
                # Disable client on auth/quota failure to avoid blocking subsequent requests
                print(f"[AI Mapper] Gemini skipped: {e}")
                _CLIENT_FAILED = True

    # 3. Generic fallback
    return {
        "categories": ["sweets", "gifts", "clothing", "decorations"],
        "items": ["Sweets Box", "Gift Hamper", "Festive Clothing", "Decorative Items"],
        "source": "fallback"
    }


# ── Firestore cache layer ─────────────────────────────────────────────────────
def get_cached_demand(festival_name: str) -> dict | None:
    """Check if we already have predictions cached in Firestore."""
    try:
        cached = firestore_db.get_festival_demand(festival_name)
        if cached:
            return {
                "categories": cached.get("categories", []),
                "items": cached.get("items", []),
                "source": cached.get("source", "cache")
            }
    except Exception:
        pass
    return None


def cache_demand(festival_name: str, demand: dict):
    """Save AI predictions to Firestore for reuse."""
    try:
        firestore_db.save_festival_demand(
            festival_name=festival_name,
            categories=demand.get("categories", []),
            items=demand.get("items", []),
            source=demand.get("source", "ai")
        )
    except Exception:
        pass


def get_or_predict_demand(festival_name: str) -> dict:
    """Main entry point: Get demand prediction from fast lookup, cache, or generator."""
    # Fast path: check detailed static map
    fast_match = _get_from_hardcoded_map(festival_name)
    if fast_match:
        return fast_match

    # Check Firestore cache
    cached = get_cached_demand(festival_name)
    if cached:
        return cached

    # Generate prediction
    demand = predict_festival_demand(festival_name)

    if demand.get("source") in ("ai", "hardcoded"):
        cache_demand(festival_name, demand)

    return demand
