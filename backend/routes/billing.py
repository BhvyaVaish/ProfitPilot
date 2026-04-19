from flask import Blueprint, request, jsonify, g
from database import get_connection
import json
import time
from config import CATEGORY_GST_RATES
from services.alert_service import refresh_alerts
from auth_middleware import optional_auth, require_auth

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/api/bill', methods=['POST'])
@require_auth
def create_bill():
    try:
        user_id = g.user_id
        data = request.json
        if not data or 'items' not in data:
            return jsonify({"error": "Missing items"}), 400

        items = data['items']
        customer_name = data.get('customer_name', '').strip()
        conn = get_connection()
        c = conn.cursor()

        subtotal = 0
        total_gst = 0
        bill_items = []

        for item in items:
            product_id = item['product_id']
            qty = int(item['quantity'])

            c.execute("SELECT * FROM products WHERE id = ? AND user_id = ?", (product_id, user_id))
            prod = c.fetchone()

            if not prod:
                conn.close()
                return jsonify({"error": f"Product ID {product_id} not found"}), 404

            # Re-check stock at billing time for accuracy
            if prod['stock'] < qty:
                conn.close()
                return jsonify({"error": f"Insufficient stock for {prod['name']}. Available: {prod['stock']}, Requested: {qty}"}), 400

            item_total = qty * prod['price']
            subtotal += item_total

            # Category-wise GST
            cat = (prod['category'] or 'general').lower()
            gst_rate = CATEGORY_GST_RATES.get(cat, 0.18)
            item_gst = item_total * gst_rate
            total_gst += item_gst

            bill_items.append({
                "product_id": product_id,
                "name": prod['name'],
                "category": cat,
                "quantity": qty,
                "price": prod['price'],
                "gst_rate": gst_rate
            })

            c.execute("UPDATE products SET stock = stock - ? WHERE id = ? AND user_id = ?", (qty, product_id, user_id))

            c.execute("INSERT INTO sales (user_id, product_id, quantity, total_price) VALUES (?, ?, ?, ?)",
                      (user_id, product_id, qty, item_total))

        grand_total = subtotal + total_gst
        bill_number = f"PP-{int(time.time())}"
        items_json = json.dumps(bill_items)

        c.execute("INSERT INTO bills (user_id, bill_number, customer_name, items_json, subtotal, gst_amount, total) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (user_id, bill_number, customer_name, items_json, subtotal, total_gst, grand_total))

        conn.commit()
        conn.close()

        refresh_alerts(user_id)

        return jsonify({
            "success": True,
            "bill": {
                "bill_number": bill_number,
                "customer_name": customer_name,
                "items": bill_items,
                "subtotal": round(subtotal, 2),
                "gst_amount": round(total_gst, 2),
                "total": round(grand_total, 2)
            }
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@billing_bp.route('/api/bills', methods=['GET'])
@optional_auth
def get_bills():
    try:
        user_id = g.user_id
        limit = request.args.get('limit', 20, type=int)
        conn = get_connection()
        bills = conn.execute("""
            SELECT id, bill_number, customer_name, items_json, subtotal, gst_amount, total,
                   strftime('%d-%m-%Y %H:%M', created_at) as created_at
            FROM bills WHERE user_id = ? ORDER BY id DESC LIMIT ?
        """, (user_id, limit)).fetchall()
        conn.close()

        result = []
        for b in bills:
            b_dict = dict(b)
            b_dict['items'] = json.loads(b_dict['items_json'])
            result.append(b_dict)

        return jsonify({"bills": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@billing_bp.route('/api/bills/<int:bill_id>', methods=['GET'])
@optional_auth
def get_bill(bill_id):
    try:
        user_id = g.user_id
        conn = get_connection()
        b = conn.execute("""
            SELECT id, bill_number, customer_name, items_json, subtotal, gst_amount, total,
                   strftime('%d-%m-%Y %H:%M:%S', created_at) as created_at
            FROM bills WHERE id = ? AND user_id = ?
        """, (bill_id, user_id)).fetchone()
        conn.close()

        if not b:
            return jsonify({"error": "Bill not found"}), 404

        b_dict = dict(b)
        b_dict['items'] = json.loads(b_dict['items_json'])
        return jsonify({"bill": b_dict}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@billing_bp.route('/api/bills/search', methods=['GET'])
@optional_auth
def search_bills():
    """Search bills by bill number or customer name."""
    try:
        user_id = g.user_id
        q = request.args.get('q', '').strip()
        if not q:
            return jsonify({"bills": []}), 200

        conn = get_connection()
        bills = conn.execute("""
            SELECT id, bill_number, customer_name, items_json, subtotal, gst_amount, total,
                   strftime('%d-%m-%Y %H:%M', created_at) as created_at
            FROM bills
            WHERE user_id = ? AND (
                LOWER(bill_number) LIKE LOWER(?) OR
                LOWER(customer_name) LIKE LOWER(?)
            )
            ORDER BY id DESC LIMIT 20
        """, (user_id, f'%{q}%', f'%{q}%')).fetchall()
        conn.close()

        result = []
        for b in bills:
            b_dict = dict(b)
            b_dict['items'] = json.loads(b_dict['items_json'])
            result.append(b_dict)

        return jsonify({"bills": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
