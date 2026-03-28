from flask import Blueprint, request, jsonify
from database import get_connection
from services.ai_engine import (
    get_restock_suggestions, 
    get_dead_stock, 
    get_high_potential_items, 
    get_prioritized_alerts,
    get_home_festival_insights
)
from services.chatbot_engine import get_top_products

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/api/dashboard/full', methods=['GET'])
def get_dashboard_full():
    try:
        # 1. Sales Graph (Revenue Velocity) default trailing 7 days
        conn = get_connection()
        graph_data = conn.execute("""
            SELECT strftime('%d-%m-%Y', sold_at) as label, 
                   date(sold_at) as raw_date,
                   SUM(total_price) as revenue, 
                   SUM(quantity) as units
            FROM sales
            WHERE sold_at >= date('now', '-7 days')
            GROUP BY label, raw_date
            ORDER BY raw_date ASC
        """).fetchall()
        conn.close()
        
        sales_graph = {
            "labels": [d['label'] for d in graph_data],
            "revenue": [d['revenue'] for d in graph_data]
        }
        
        # 2. Top Products (Catalog Performance)
        catalog_performance = get_top_products(5)
        
        # 3. Restock Suggestions (Smart Procurement)
        smart_procurement = get_restock_suggestions()
        
        # 4. Dead Stock (Capital Efficiency)
        dead_stock = get_dead_stock()
        
        # 5. High Potential Items
        high_potential = get_high_potential_items()
        
        # 6. Alerts panel
        alerts = get_prioritized_alerts()[:3]
        
        # 7. Festival Widget
        festival_widget = get_home_festival_insights()
        
        return jsonify({
            "sales_graph": sales_graph,
            "catalog_performance": catalog_performance,
            "smart_procurement": smart_procurement,
            "dead_stock": dead_stock,
            "high_potential": high_potential,
            "alerts": alerts,
            "festival_widget": festival_widget
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
