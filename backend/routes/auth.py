from flask import Blueprint, request, jsonify, g
from auth_middleware import require_auth, optional_auth
from database import get_connection

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/auth/check', methods=['GET'])
@require_auth
def check_user():
    """Check if user exists and is onboarded."""
    try:
        conn = get_connection()
        user = conn.execute(
            "SELECT * FROM user_profiles WHERE firebase_uid = ?",
            (g.user_id,)
        ).fetchone()
        conn.close()

        if user:
            return jsonify({
                "exists": True,
                "onboarded": bool(user['onboarded']),
                "profile": dict(user)
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

        conn = get_connection()
        c = conn.cursor()

        # Check if already onboarded
        existing = conn.execute(
            "SELECT firebase_uid FROM user_profiles WHERE firebase_uid = ?",
            (g.user_id,)
        ).fetchone()

        if existing:
            # Update existing profile
            c.execute("""
                UPDATE user_profiles SET
                    full_name = ?, phone = ?, city = ?, state = ?,
                    business_name = ?, business_address = ?,
                    gstin = ?, pan_number = ?,
                    business_type = ?, business_sector = ?,
                    turnover_range = ?, msme_category = ?,
                    payment_mode = ?, onboarded = 1
                WHERE firebase_uid = ?
            """, (
                data.get('full_name', ''),
                data.get('phone', ''),
                data.get('city', ''),
                data.get('state', ''),
                data.get('business_name', ''),
                data.get('business_address', ''),
                data.get('gstin', ''),
                data.get('pan_number', ''),
                data.get('business_type', 'trading'),
                data.get('business_sector', 'general'),
                data.get('turnover_range', 'below_1cr'),
                data.get('msme_category', 'micro'),
                data.get('payment_mode', 'mixed'),
                g.user_id
            ))
        else:
            # Create new profile
            c.execute("""
                INSERT INTO user_profiles (
                    firebase_uid, email, full_name, phone, city, state,
                    business_name, business_address, gstin, pan_number,
                    business_type, business_sector, turnover_range,
                    msme_category, payment_mode, onboarded
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                g.user_id,
                g.user_email,
                data.get('full_name', ''),
                data.get('phone', ''),
                data.get('city', ''),
                data.get('state', ''),
                data.get('business_name', ''),
                data.get('business_address', ''),
                data.get('gstin', ''),
                data.get('pan_number', ''),
                data.get('business_type', 'trading'),
                data.get('business_sector', 'general'),
                data.get('turnover_range', 'below_1cr'),
                data.get('msme_category', 'micro'),
                data.get('payment_mode', 'mixed')
            ))

        # Seed starter products based on business sector
        _seed_user_starter_data(c, g.user_id, data.get('business_sector', 'general'))

        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Onboarding complete!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route('/api/auth/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get current user's profile."""
    try:
        conn = get_connection()
        user = conn.execute(
            "SELECT * FROM user_profiles WHERE firebase_uid = ?",
            (g.user_id,)
        ).fetchone()
        conn.close()

        if not user:
            return jsonify({"error": "Profile not found"}), 404

        return jsonify({"profile": dict(user)}), 200
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

        conn = get_connection()
        allowed_fields = [
            'full_name', 'phone', 'city', 'state',
            'business_name', 'business_address', 'gstin', 'pan_number',
            'business_type', 'business_sector', 'turnover_range',
            'msme_category', 'payment_mode'
        ]

        updates = []
        params = []
        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = ?")
                params.append(data[field])

        if not updates:
            conn.close()
            return jsonify({"error": "No valid fields to update"}), 400

        params.append(g.user_id)
        conn.execute(
            f"UPDATE user_profiles SET {', '.join(updates)} WHERE firebase_uid = ?",
            params
        )
        conn.commit()
        conn.close()

        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route('/api/auth/debug-user', methods=['GET'])
@optional_auth
def debug_user():
    """Debug endpoint to check current user_id."""
    from flask import g
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
        
        conn = get_connection()
        c = conn.cursor()
        
        # Count before deletion for verification
        before_products = c.execute("SELECT COUNT(*) as count FROM products WHERE user_id = ?", (g.user_id,)).fetchone()['count']
        before_sales = c.execute("SELECT COUNT(*) as count FROM sales WHERE user_id = ?", (g.user_id,)).fetchone()['count']
        before_bills = c.execute("SELECT COUNT(*) as count FROM bills WHERE user_id = ?", (g.user_id,)).fetchone()['count']
        before_alerts = c.execute("SELECT COUNT(*) as count FROM alerts WHERE user_id = ?", (g.user_id,)).fetchone()['count']
        
        print(f"[FLUSH] User {g.user_id} - Before: {before_products} products, {before_sales} sales, {before_bills} bills, {before_alerts} alerts")
        
        # IMPORTANT: Delete in correct order due to foreign key constraints
        # Delete sales first (references products)
        c.execute("DELETE FROM sales WHERE user_id = ?", (g.user_id,))
        sales_deleted = c.rowcount
        
        # Delete bills (no foreign key constraints)
        c.execute("DELETE FROM bills WHERE user_id = ?", (g.user_id,))
        bills_deleted = c.rowcount
        
        # Delete alerts (no foreign key constraints)
        c.execute("DELETE FROM alerts WHERE user_id = ?", (g.user_id,))
        alerts_deleted = c.rowcount
        
        # Delete products last (after sales are deleted)
        c.execute("DELETE FROM products WHERE user_id = ?", (g.user_id,))
        products_deleted = c.rowcount
        
        conn.commit()
        
        # Verify deletion
        after_products = c.execute("SELECT COUNT(*) as count FROM products WHERE user_id = ?", (g.user_id,)).fetchone()['count']
        after_sales = c.execute("SELECT COUNT(*) as count FROM sales WHERE user_id = ?", (g.user_id,)).fetchone()['count']
        after_bills = c.execute("SELECT COUNT(*) as count FROM bills WHERE user_id = ?", (g.user_id,)).fetchone()['count']
        after_alerts = c.execute("SELECT COUNT(*) as count FROM alerts WHERE user_id = ?", (g.user_id,)).fetchone()['count']
        
        print(f"[FLUSH] User {g.user_id} - After: {after_products} products, {after_sales} sales, {after_bills} bills, {after_alerts} alerts")
        print(f"[FLUSH] User {g.user_id} - Deleted: {products_deleted} products, {sales_deleted} sales, {bills_deleted} bills, {alerts_deleted} alerts")
        
        conn.close()
        
        if after_products > 0 or after_sales > 0 or after_bills > 0 or after_alerts > 0:
            return jsonify({
                "error": f"Flush incomplete. Remaining: {after_products} products, {after_sales} sales, {after_bills} bills, {after_alerts} alerts",
                "success": False
            }), 500
        
        return jsonify({
            "success": True,
            "message": "All data flushed successfully. You can now start with fresh data.",
            "deleted": {
                "products": products_deleted,
                "sales": sales_deleted,
                "bills": bills_deleted,
                "alerts": alerts_deleted
            }
        }), 200
    except Exception as e:
        print(f"[FLUSH ERROR] User {g.user_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500


def _seed_user_starter_data(cursor, user_id, business_sector):
    """Seed starter products for a new user based on their business sector."""
    # Check if user already has products
    existing = cursor.execute(
        "SELECT COUNT(*) as c FROM products WHERE user_id = ?", (user_id,)
    ).fetchone()
    if existing and existing['c'] > 0:
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
    }

    # Default products for general or unrecognized sectors
    products = sector_products.get(business_sector, [
        ("Sample Product A", "general", 100.0, 50),
        ("Sample Product B", "general", 200.0, 30),
        ("Sample Product C", "general", 150.0, 40),
    ])

    for name, category, price, stock in products:
        cursor.execute(
            "INSERT INTO products (name, category, price, stock, user_id) VALUES (?, ?, ?, ?, ?)",
            (name, category, price, stock, user_id)
        )
