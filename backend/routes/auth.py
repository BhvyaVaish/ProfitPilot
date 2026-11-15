"""
auth.py — Authentication & user profile routes.

Fully migrated to Firestore. No SQL.
"""

from flask import Blueprint, request, jsonify, g
from auth_middleware import require_auth, optional_auth
import firestore_db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/auth/check', methods=['GET'])
@require_auth
def check_user():
    """Check if user exists and is onboarded."""
    try:
        user = firestore_db.get_user_profile(g.user_id)
        if user:
            return jsonify({
                "exists": True,
                "onboarded": bool(user.get('onboarded', False)),
                "profile": user
            }), 200
        else:
            return jsonify({
                "exists": False,
                "onboarded": False
            }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route('/api/auth/onboarding', methods=['POST'])
@require_auth
def onboarding():
    """Save onboarding data for new user."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        profile_data = {
            "firebase_uid": g.user_id,
            "email": g.user_email,
            "full_name": data.get('full_name', ''),
            "phone": data.get('phone', ''),
            "city": data.get('city', ''),
            "state": data.get('state', ''),
            "business_name": data.get('business_name', ''),
            "business_address": data.get('business_address', ''),
            "gstin": data.get('gstin', ''),
            "pan_number": data.get('pan_number', ''),
            "business_type": data.get('business_type', 'trading'),
            "business_sector": data.get('business_sector', 'general'),
            "turnover_range": data.get('turnover_range', 'below_1cr'),
            "msme_category": data.get('msme_category', 'micro'),
            "payment_mode": data.get('payment_mode', 'mixed'),
            "onboarded": True,
        }

        firestore_db.upsert_user_profile(g.user_id, profile_data)

        # Seed starter products based on business sector (only if user has none)
        _seed_user_starter_data(g.user_id, data.get('business_sector', 'general'))

        return jsonify({"success": True, "message": "Onboarding complete!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route('/api/auth/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get current user's profile."""
    try:
        user = firestore_db.get_user_profile(g.user_id)
        if not user:
            return jsonify({"error": "Profile not found"}), 404
        return jsonify({"profile": user}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route('/api/auth/profile', methods=['PUT'])
@require_auth
def update_profile():
    """Update user profile (post-onboarding edits)."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        allowed_fields = [
            'full_name', 'phone', 'city', 'state',
            'business_name', 'business_address', 'gstin', 'pan_number',
            'business_type', 'business_sector', 'turnover_range',
            'msme_category', 'payment_mode'
        ]

        updates = {f: data[f] for f in allowed_fields if f in data}

        if not updates:
            return jsonify({"error": "No valid fields to update"}), 400

        firestore_db.upsert_user_profile(g.user_id, updates)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route('/api/auth/debug-user', methods=['GET'])
@optional_auth
def debug_user():
    """Debug endpoint to check current user_id."""
    return jsonify({
        "user_id": g.user_id,
        "user_email": getattr(g, 'user_email', 'N/A'),
        "user_name": getattr(g, 'user_name', 'N/A'),
        "is_demo": g.user_id == 'demo'
    }), 200


@auth_bp.route('/api/auth/flush', methods=['DELETE'])
@optional_auth
def flush_user_data():
    """Flush all user data (products, sales, bills, alerts) - allows starting fresh."""
    try:
        # Require that they at least appear signed in from the frontend
        if not request.headers.get('Authorization'):
            return jsonify({"error": "Authentication required. Please sign in."}), 401

        counts = firestore_db.delete_user_data(g.user_id)

        print(f"[FLUSH] User {g.user_id} - Deleted: {counts}")

        return jsonify({
            "success": True,
            "message": "All data flushed successfully. You can now start with fresh data.",
            "deleted": counts
        }), 200
    except Exception as e:
        print(f"[FLUSH ERROR] User {g.user_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500


def _seed_user_starter_data(user_id: str, business_sector: str):
    """Seed starter products for a new user based on their business sector."""
    # Check if user already has products
    existing = list(firestore_db.products_col(user_id).limit(1).stream())
    if existing:
        return

    sector_products = {
        'grocery': [
            ("Tata Salt (1kg)", "grocery", 28.0, 100),
            ("Aashirvaad Atta (5kg)", "grocery", 245.0, 50),
            ("Fortune Sunflower Oil (1L)", "grocery", 145.0, 40),
            ("Sugar (1kg)", "grocery", 48.0, 80),
            ("Toor Dal (1kg)", "grocery", 140.0, 50),
            ("MDH Chana Masala (100g)", "grocery", 55.0, 60),
        ],
        'electronics': [
            ("boAt Earbuds", "electronics", 1299.0, 15),
            ("Syska LED Bulb (9W) 3pk", "electronics", 299.0, 30),
            ("USB Charger Cable", "electronics", 199.0, 50),
            ("USB Hub 4-Port", "electronics", 450.0, 20),
            ("Phone Screen Guard", "electronics", 149.0, 40),
        ],
        'clothing': [
            ("Cotton Kurta (Men)", "clothing", 650.0, 20),
            ("Dupatta (Women)", "clothing", 350.0, 30),
            ("Kids T-Shirt", "clothing", 250.0, 40),
            ("Denim Jeans (Men)", "clothing", 899.0, 15),
            ("Saree (Women)", "clothing", 1200.0, 10),
        ],
        'food_beverages': [
            ("Maggi Noodles (12pk)", "packaged_food", 168.0, 50),
            ("Haldiram Namkeen (400g)", "snacks", 120.0, 40),
            ("Parle-G Biscuits (800g)", "packaged_food", 70.0, 60),
            ("Amul Butter (500g)", "dairy", 270.0, 25),
            ("Fresh Samosa (per pc)", "packaged_food", 15.0, 100),
        ],
        'pharmacy': [
            ("Dettol Handwash (200ml)", "personal_care", 85.0, 40),
            ("Colgate MaxFresh (150g)", "personal_care", 95.0, 50),
            ("Dove Soap (100g)", "personal_care", 56.0, 60),
            ("Band-Aid Strips (10pk)", "personal_care", 45.0, 30),
            ("Nivea Body Lotion (200ml)", "personal_care", 195.0, 20),
        ],
        'stationery': [
            ("Classmate Notebook (6pk)", "stationery", 180.0, 40),
            ("Cello Pen Set (10pcs)", "stationery", 80.0, 60),
            ("Camlin Colour Box", "stationery", 120.0, 25),
            ("Geometry Box", "stationery", 150.0, 30),
            ("A4 Paper Ream (500 sheets)", "stationery", 350.0, 15),
        ],
        'hardware': [
            ("Hammer (500g)", "hardware", 180.0, 20),
            ("Screwdriver Set (6pc)", "hardware", 250.0, 15),
            ("PVC Tape (5m)", "hardware", 45.0, 50),
            ("LED Torch (Rechargeable)", "hardware", 350.0, 25),
            ("Wall Hooks (10pk)", "hardware", 60.0, 40),
        ],
    }

    # Default products for general or unrecognized sectors
    products = sector_products.get(business_sector, [
        ("Sample Product A", "general", 100.0, 50),
        ("Sample Product B", "general", 200.0, 30),
        ("Sample Product C", "general", 150.0, 40),
    ])

    for name, category, price, stock in products:
        try:
            firestore_db.insert_product(
                user_id=user_id,
                name=name,
                category=category,
                price=price,
                stock=stock,
            )
        except Exception as e:
            print(f"[SEED] Error inserting {name}: {e}")
