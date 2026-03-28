from flask import Blueprint, request, jsonify
from database import get_connection
from models import insert_product, update_product_stock, delete_product
from services.alert_service import refresh_alerts


inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/api/inventory', methods=['GET'])
def get_inventory():
    try:
        conn = get_connection()
        # Natively calculate threshold mathematics directly via SQL aggregation vs 7d trailing
        query = """
            SELECT 
                p.id, p.name, p.category, p.price, p.stock,
                COALESCE(SUM(s.quantity), 0) as past_7d_sales
            FROM products p
            LEFT JOIN sales s ON p.id = s.product_id AND s.sold_at >= date('now', '-7 days')
            GROUP BY p.id
            ORDER BY p.name ASC
        """
        rows = conn.execute(query).fetchall()
        
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
                
            products.append(prod)
            
        conn.close()
        return jsonify({"products": products}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@inventory_bp.route('/api/inventory', methods=['POST'])
def add_product():
    try:
        data = request.json
        if not data or not all(k in data for k in ("name", "category", "price", "stock")):
            return jsonify({"error": "Missing required fields"}), 400
            
        if float(data['price']) <= 0 or int(data['stock']) < 0:
            return jsonify({"error": "Price must be > 0 and stock >= 0"}), 400
            
        # Uniqueness Check
        conn = get_connection()
        exists = conn.execute("SELECT id FROM products WHERE LOWER(name) = LOWER(?)", (data['name'],)).fetchone()
        if exists:
            conn.close()
            return jsonify({"error": "Product with this name already exists"}), 400
        conn.close()
            
        product_id = insert_product(data['name'], data['category'], float(data['price']), int(data['stock']))
        refresh_alerts()
        return jsonify({"success": True, "product_id": product_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@inventory_bp.route('/api/inventory/<int:product_id>/add-stock', methods=['POST'])
def add_stock(product_id):
    try:
        data = request.json
        if not data or 'added_quantity' not in data:
            return jsonify({"error": "Missing added_quantity"}), 400
            
        qty = int(data['added_quantity'])
        if qty <= 0:
            return jsonify({"error": "Quantity must be > 0"}), 400
            
        conn = get_connection()
        prod = conn.execute("SELECT stock FROM products WHERE id = ?", (product_id,)).fetchone()
        if not prod:
            conn.close()
            return jsonify({"error": "Product not found"}), 404
            
        new_stock = prod['stock'] + qty
        conn.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))
        conn.commit()
        conn.close()
        
        refresh_alerts()
        
        return jsonify({"success": True, "new_stock": new_stock}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@inventory_bp.route('/api/inventory/<int:product_id>', methods=['PUT'])
def update_product_route(product_id):
    try:
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

            
        if not updates:
            conn.close()
            return jsonify({"error": "Nothing valid to update"}), 400
            
        params.append(product_id)
        query = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"
        conn.execute(query, params)
        conn.commit()
        conn.close()
        
        refresh_alerts()
        
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@inventory_bp.route('/api/inventory/<int:product_id>', methods=['DELETE'])
def remove_product_route(product_id):
    try:
        conn = get_connection()
        sales_count = conn.execute("SELECT COUNT(*) as sc FROM sales WHERE product_id = ?", (product_id,)).fetchone()['sc']
        
        # Block Dashboard Disintegration
        if sales_count > 0:
            conn.close()
            return jsonify({"error": "This product has sales history and cannot be deleted. Please adjust stock to 0 or edit its name instead."}), 400
            
        delete_product(product_id)
        conn.close()
        refresh_alerts()
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
