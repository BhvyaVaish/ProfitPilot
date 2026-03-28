from flask import Blueprint, request, jsonify
from database import get_connection
import json
import time
from services.alert_service import refresh_alerts

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/api/bill', methods=['POST'])
def create_bill():
    try:
        data = request.json
        if not data or 'items' not in data:
            return jsonify({"error": "Missing items"}), 400
            
        items = data['items']
        conn = get_connection()
        c = conn.cursor()
        
        total_bill = 0
        bill_items = []
        
        for item in items:
            product_id = item['product_id']
            qty = int(item['quantity'])
            
            c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            prod = c.fetchone()
            
            if not prod:
                conn.close()
                return jsonify({"error": f"Product ID {product_id} not found"}), 404
                
            if prod['stock'] < qty:
                conn.close()
                return jsonify({"error": f"Insufficient stock for {prod['name']}"}), 400
                
            item_total = qty * prod['price']
            total_bill += item_total
            
            bill_items.append({
                "product_id": product_id,
                "name": prod['name'],
                "quantity": qty,
                "price": prod['price']
            })
            
            c.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (qty, product_id))
            
            c.execute("INSERT INTO sales (product_id, quantity, total_price) VALUES (?, ?, ?)",
                      (product_id, qty, item_total))
                      
        bill_number = f"BILL-{int(time.time())}"
        items_json = json.dumps(bill_items)
        
        c.execute("INSERT INTO bills (bill_number, items_json, total) VALUES (?, ?, ?)",
                  (bill_number, items_json, total_bill))
                  
        conn.commit()
        conn.close()
        
        refresh_alerts()
        
        return jsonify({
            "success": True, 
            "bill": {
                "bill_number": bill_number, 
                "items": bill_items, 
                "total": total_bill
            }
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@billing_bp.route('/api/bills', methods=['GET'])
def get_bills():
    try:
        limit = request.args.get('limit', 20, type=int)
        conn = get_connection()
        bills = conn.execute("SELECT * FROM bills ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
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
def get_bill(bill_id):
    try:
        conn = get_connection()
        b = conn.execute("SELECT id, bill_number, items_json, total, strftime('%d-%m-%Y %H:%M:%S', created_at) as created_at FROM bills WHERE id = ?", (bill_id,)).fetchone()
        conn.close()
        
        if not b:
            return jsonify({"error": "Bill not found"}), 404
            
        b_dict = dict(b)
        b_dict['items'] = json.loads(b_dict['items_json'])
        return jsonify({"bill": b_dict}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
