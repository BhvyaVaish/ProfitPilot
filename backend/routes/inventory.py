import io
import csv

from flask import Blueprint, request, jsonify, g, make_response
import firestore_db
from models import insert_product, delete_product
from services.alert_service import refresh_alerts
from auth_middleware import optional_auth, require_auth
from config import COST_RATIO

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/api/inventory', methods=['GET'])
@optional_auth
def get_inventory():
    try:
        user_id = g.user_id

        # Fetch all products and 7-day sales metrics in parallel
        products_list = firestore_db.get_all_products(user_id)
        bulk_metrics = firestore_db.get_bulk_sales_metrics(user_id)

        products = []
        for prod in products_list:
            pid = prod['id']
            metrics = bulk_metrics.get(pid, {})
            past_7d_sales = metrics.get('last_7_days_sales', 0)
            avg_daily_sales = metrics.get('avg_last_7', 0.0)

            prod['past_7d_sales'] = past_7d_sales

            threshold = max(5, avg_daily_sales * 2)
            stock = prod.get('stock', 0)
            if stock == 0:
                prod['status'] = 'Out of Stock'
            elif stock < threshold:
                prod['status'] = 'Low'
            else:
                prod['status'] = 'OK'

            # Compute effective cost price
            cost_price = prod.get('cost_price')
            if cost_price is not None and cost_price > 0:
                prod['effective_cost'] = cost_price
                prod['cost_mode'] = 'custom'
            else:
                prod['effective_cost'] = round(prod['price'] * COST_RATIO, 2)
                prod['cost_mode'] = 'default'

            products.append(prod)

        return jsonify({"products": products}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inventory_bp.route('/api/inventory/export', methods=['GET'])
@optional_auth
def export_inventory():
    """Export inventory as a CSV file."""
    try:
        user_id = g.user_id
        products_list = firestore_db.get_all_products(user_id)
        bulk_metrics = firestore_db.get_bulk_sales_metrics(user_id)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Name', 'Category', 'Price', 'Cost Price', 'Stock', 'Past 7d Sales', 'Status'])

        for prod in products_list:
            pid = prod['id']
            metrics = bulk_metrics.get(pid, {})
            past_7d_sales = metrics.get('last_7_days_sales', 0)
            avg_daily_sales = metrics.get('avg_last_7', 0.0)
            threshold = max(5, avg_daily_sales * 2)
            stock = prod.get('stock', 0)
            if stock == 0:
                status = 'Out of Stock'
            elif stock < threshold:
                status = 'Low'
            else:
                status = 'OK'

            writer.writerow([
                pid,
                prod.get('name', ''),
                prod.get('category', ''),
                prod.get('price', ''),
                prod.get('cost_price', ''),
                stock,
                past_7d_sales,
                status,
            ])

        csv_data = output.getvalue()
        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=inventory.csv'
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inventory_bp.route('/api/inventory', methods=['POST'])
@require_auth
def add_product():
    try:
        user_id = g.user_id
        data = request.json
        if not data or not all(k in data for k in ("name", "category", "price", "stock")):
            return jsonify({"error": "Missing required fields"}), 400

        if float(data['price']) <= 0 or int(data['stock']) < 0:
            return jsonify({"error": "Price must be > 0 and stock >= 0"}), 400

        # Check for duplicate product name
        existing = firestore_db.get_product_by_name(user_id, data['name'])
        if existing:
            return jsonify({"error": "Product with this name already exists"}), 400

        cost_price = data.get('cost_price')
        if cost_price is not None:
            try:
                cost_price = float(cost_price)
                if cost_price <= 0:
                    cost_price = None
            except (ValueError, TypeError):
                cost_price = None

        product_id = insert_product(
            data['name'],
            data['category'],
            float(data['price']),
            int(data['stock']),
            user_id,
            cost_price=cost_price,
        )
        refresh_alerts(user_id)
        return jsonify({"success": True, "product_id": product_id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inventory_bp.route('/api/inventory/<string:product_id>/add-stock', methods=['POST'])
@require_auth
def add_stock(product_id):
    try:
        user_id = g.user_id
        data = request.json
        if not data or 'added_quantity' not in data:
            return jsonify({"error": "Missing added_quantity"}), 400

        qty = int(data['added_quantity'])
        if qty <= 0:
            return jsonify({"error": "Quantity must be > 0"}), 400

        prod = firestore_db.get_product(user_id, product_id)
        if not prod:
            return jsonify({"error": "Product not found"}), 404

        new_stock = firestore_db.add_stock(user_id, product_id, qty)
        refresh_alerts(user_id)

        return jsonify({"success": True, "new_stock": new_stock}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inventory_bp.route('/api/inventory/<string:product_id>', methods=['PUT'])
@require_auth
def update_product_route(product_id):
    try:
        user_id = g.user_id
        data = request.json
        if not data:
            return jsonify({"error": "No data"}), 400

        updates = {}

        if 'price' in data:
            try:
                price_val = float(data['price'])
                if price_val > 0:
                    updates['price'] = price_val
            except (ValueError, TypeError):
                pass

        if 'name' in data and str(data['name']).strip():
            updates['name'] = data['name'].strip()

        if 'stock' in data:
            try:
                stock_val = int(data['stock'])
                if stock_val >= 0:
                    updates['stock'] = stock_val
            except (ValueError, TypeError):
                pass

        if 'category' in data and str(data['category']).strip():
            updates['category'] = data['category'].strip()

        if 'cost_price' in data:
            cp = data['cost_price']
            if cp is None or cp == '' or cp == 'default':
                updates['cost_price'] = None
            else:
                try:
                    cp_val = float(cp)
                    if cp_val > 0:
                        updates['cost_price'] = cp_val
                except (ValueError, TypeError):
                    pass

        if not updates:
            return jsonify({"error": "Nothing valid to update"}), 400

        firestore_db.update_product(user_id, product_id, **updates)
        refresh_alerts(user_id)

        return jsonify({"success": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inventory_bp.route('/api/inventory/<string:product_id>', methods=['DELETE'])
@require_auth
def remove_product_route(product_id):
    try:
        user_id = g.user_id

        # Check for sales history to protect data integrity
        sales = firestore_db.get_sales_since(user_id, firestore_db.days_ago(3650))  # ~10 years
        has_sales = any(s.get('product_id') == product_id for s in sales)

        if has_sales:
            return jsonify({
                "error": "This product has sales history and cannot be deleted. "
                         "Please adjust stock to 0 or edit its name instead."
            }), 400

        delete_product(product_id, user_id)
        refresh_alerts(user_id)
        return jsonify({"success": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
