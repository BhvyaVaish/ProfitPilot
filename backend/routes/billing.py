"""
billing.py — Billing & invoice routes.

Fully migrated to Firestore. No SQL.
"""

import json
import time
from flask import Blueprint, request, jsonify, g
import firestore_db
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

        subtotal = 0
        total_gst = 0
        bill_items = []

        for item in items:
            product_id = str(item['product_id'])
            qty = int(item['quantity'])

            prod = firestore_db.get_product(user_id, product_id)
            if not prod:
                return jsonify({"error": f"Product ID {product_id} not found"}), 404

            # Re-check stock at billing time for accuracy
            if prod['stock'] < qty:
                return jsonify({
                    "error": f"Insufficient stock for {prod['name']}. "
                             f"Available: {prod['stock']}, Requested: {qty}"
                }), 400

            item_total = qty * prod['price']
            subtotal += item_total

            # Category-wise GST
            cat = (prod.get('category') or 'general').lower()
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

            # Decrement stock
            firestore_db.decrement_stock(user_id, product_id, qty)

            # Record the sale
            firestore_db.insert_sale(
                user_id=user_id,
                product_id=product_id,
                product_name=prod['name'],
                category=cat,
                quantity=qty,
                total_price=item_total,
            )

        grand_total = subtotal + total_gst
        bill_number = f"PP-{int(time.time())}"

        bill_id = firestore_db.insert_bill(
            user_id=user_id,
            bill_number=bill_number,
            customer_name=customer_name,
            items=bill_items,
            subtotal=subtotal,
            gst_amount=total_gst,
            total=grand_total,
        )

        refresh_alerts(user_id)

        return jsonify({
            "success": True,
            "bill": {
                "id": bill_id,
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
        bills = firestore_db.get_bills(user_id, limit=limit)
        return jsonify({"bills": bills}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@billing_bp.route('/api/bills/<string:bill_id>', methods=['GET'])
@optional_auth
def get_bill(bill_id):
    try:
        user_id = g.user_id
        bill = firestore_db.get_bill(user_id, bill_id)
        if not bill:
            return jsonify({"error": "Bill not found"}), 404
        return jsonify({"bill": bill}), 200
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
        bills = firestore_db.search_bills(user_id, q)
        return jsonify({"bills": bills}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
