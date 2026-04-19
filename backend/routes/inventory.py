from flask import Blueprint, request, jsonify, g
from database import get_connection
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
        conn = get_connection()
        query = """
            SELECT
                p.id, p.name, p.category, p.price, p.cost_price, p.stock,
                COALESCE(SUM(s.quantity), 0) as past_7d_sales
            FROM products p
            LEFT JOIN sales s ON p.id = s.product_id AND s.sold_at >= date('now', '-7 days')
            WHERE p.user_id = ?
            GROUP BY p.id
            ORDER BY p.name ASC
        """
        rows = conn.execute(query, (user_id,)).fetchall()

        products = []
        for r in rows:
            prod = dict(r)
            avg_daily_sales = prod['past_7d_sales'] / 7.0
            threshold = max(5, avg_daily_sales * 2)

            if prod['stock'] == 0:
                prod['status'] = 'Out of Stock'
            elif prod['stock'] < threshold:
                prod['status'] = 'Low'
            else:
                prod['status'] = 'OK'

            # Compute effective cost price
            if prod['cost_price'] is not None and prod['cost_price'] > 0:
                prod['effective_cost'] = prod['cost_price']
                prod['cost_mode'] = 'custom'
            else:
                prod['effective_cost'] = round(prod['price'] * COST_RATIO, 2)
                prod['cost_mode'] = 'default'

            products.append(prod)

        conn.close()
        return jsonify({"products": products}), 200

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

        conn = get_connection()
        exists = conn.execute("SELECT id FROM products WHERE user_id = ? AND LOWER(name) = LOWER(?)", (user_id, data['name'])).fetchone()
        if exists:
            conn.close()
            return jsonify({"error": "Product with this name already exists"}), 400
        conn.close()

        cost_price = data.get('cost_price')
        if cost_price is not None:
            try:
                cost_price = float(cost_price)
                if cost_price <= 0:
                    cost_price = None
            except (ValueError, TypeError):
                cost_price = None

        product_id = insert_product(data['name'], data['category'], float(data['price']), int(data['stock']), user_id, cost_price=cost_price)
        refresh_alerts(user_id)
        return jsonify({"success": True, "product_id": product_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@inventory_bp.route('/api/inventory/<int:product_id>/add-stock', methods=['POST'])
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

        conn = get_connection()
        prod = conn.execute("SELECT stock FROM products WHERE id = ? AND user_id = ?", (product_id, user_id)).fetchone()
        if not prod:
            conn.close()
            return jsonify({"error": "Product not found"}), 404

        new_stock = prod['stock'] + qty
        conn.execute("UPDATE products SET stock = ? WHERE id = ? AND user_id = ?", (new_stock, product_id, user_id))
        conn.commit()
        conn.close()

        refresh_alerts(user_id)

        return jsonify({"success": True, "new_stock": new_stock}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@inventory_bp.route('/api/inventory/<int:product_id>', methods=['PUT'])
@require_auth
def update_product_route(product_id):
    try:
        user_id = g.user_id
        data = request.json
        if not data:
             return jsonify({"error": "No data"}), 400

        conn = get_connection()
        updates = []
        params = []
        if 'price' in data and float(data['price']) > 0:
            updates.append("price = ?")
            params.append(float(data['price']))

        if 'name' in data and len(data['name'].strip()) > 0:
            updates.append("name = ?")
            params.append(data['name'].strip())

        if 'stock' in data and int(data['stock']) >= 0:
            updates.append("stock = ?")
            params.append(int(data['stock']))

        if 'category' in data and len(data['category'].strip()) > 0:
            updates.append("category = ?")
            params.append(data['category'].strip())

        if 'cost_price' in data:
            cp = data['cost_price']
            if cp is None or cp == '' or cp == 'default':
                updates.append("cost_price = ?")
                params.append(None)  # Reset to default
            else:
                try:
                    cp_val = float(cp)
                    if cp_val > 0:
                        updates.append("cost_price = ?")
                        params.append(cp_val)
                except (ValueError, TypeError):
                    pass

        if not updates:
            conn.close()
            return jsonify({"error": "Nothing valid to update"}), 400

        params.extend([product_id, user_id])
        query = f"UPDATE products SET {', '.join(updates)} WHERE id = ? AND user_id = ?"
        conn.execute(query, params)
        conn.commit()
        conn.close()

        refresh_alerts(user_id)

        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@inventory_bp.route('/api/inventory/<int:product_id>', methods=['DELETE'])
@require_auth
def remove_product_route(product_id):
    try:
        user_id = g.user_id
        conn = get_connection()
        sales_count = conn.execute("SELECT COUNT(*) as sc FROM sales WHERE product_id = ? AND user_id = ?", (product_id, user_id)).fetchone()['sc']

        if sales_count > 0:
            conn.close()
            return jsonify({"error": "This product has sales history and cannot be deleted. Please adjust stock to 0 or edit its name instead."}), 400

        conn.close()
        delete_product(product_id, user_id)
        refresh_alerts(user_id)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
