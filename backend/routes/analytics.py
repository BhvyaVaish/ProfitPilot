from flask import Blueprint, request, jsonify, g
from database import get_connection
from services.ai_engine import (
    get_restock_suggestions,
    get_dead_stock,
    get_high_potential_items,
    get_prioritized_alerts,
    get_home_festival_insights
)
from services.chatbot_engine import get_top_products
from auth_middleware import optional_auth

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/api/dashboard/full', methods=['GET'])
@optional_auth
def get_dashboard_full():
    try:
        user_id = g.user_id
        days = request.args.get('days', 7, type=int)
        if days not in [7, 14, 30]:
            days = 7

        # 1. Sales Graph (Revenue Velocity)
        conn = get_connection()
        graph_data = conn.execute(f"""
            SELECT strftime('%d-%m-%Y', s.sold_at) as label,
                   date(s.sold_at) as raw_date,
                   SUM(s.total_price) as revenue,
                   SUM(s.quantity) as units
            FROM sales s
            JOIN products p ON p.id = s.product_id
            WHERE p.user_id = ? AND s.sold_at >= date('now', '-{days} days')
            GROUP BY date(s.sold_at), strftime('%d-%m-%Y', s.sold_at)
            ORDER BY date(s.sold_at) ASC
        """, (user_id,)).fetchall()

        sales_graph = {
            "labels": [d['label'] for d in graph_data],
            "revenue": [d['revenue'] for d in graph_data],
            "units": [d['units'] for d in graph_data]
        }

        # 2. Top Products (Catalog Performance)
        catalog_performance = get_top_products(5, user_id)

        # 3. Restock Suggestions (Smart Procurement)
        smart_procurement = get_restock_suggestions(user_id)

        # 4. Dead Stock (Capital Efficiency)
        dead_stock = get_dead_stock(user_id)

        # 5. High Potential Items
        high_potential = get_high_potential_items(user_id)

        # 6. Alerts panel
        alerts = get_prioritized_alerts(user_id)[:3]

        # 7. Festival Widget
        festival_widget = get_home_festival_insights(user_id)

        # 8. Category-wise Sales Breakdown
        cat_data = conn.execute("""
            SELECT p.category, SUM(s.total_price) as total_revenue
            FROM sales s
            JOIN products p ON p.id = s.product_id
            WHERE p.user_id = ? AND s.sold_at >= date('now', '-30 days')
            GROUP BY p.category
            ORDER BY total_revenue DESC
        """, (user_id,)).fetchall()
        category_breakdown = [{"category": c['category'], "revenue": round(c['total_revenue'], 2)} for c in cat_data]

        # 9. Summary stats
        total_rev = conn.execute("SELECT COALESCE(SUM(s.total_price), 0) as t FROM sales s JOIN products p ON p.id = s.product_id WHERE p.user_id = ? AND s.sold_at >= date('now', '-7 days')", (user_id,)).fetchone()['t']
        prev_rev = conn.execute("SELECT COALESCE(SUM(s.total_price), 0) as t FROM sales s JOIN products p ON p.id = s.product_id WHERE p.user_id = ? AND s.sold_at >= date('now', '-14 days') AND s.sold_at < date('now', '-7 days')", (user_id,)).fetchone()['t']
        total_orders = conn.execute("SELECT COUNT(DISTINCT id) as c FROM bills WHERE user_id = ? AND created_at >= date('now', '-7 days')", (user_id,)).fetchone()['c']

        conn.close()

        return jsonify({
            "sales_graph": sales_graph,
            "catalog_performance": catalog_performance,
            "smart_procurement": smart_procurement,
            "dead_stock": dead_stock,
            "high_potential": high_potential,
            "alerts": alerts,
            "festival_widget": festival_widget,
            "category_breakdown": category_breakdown,
            "summary": {
                "week_revenue": round(total_rev, 2),
                "prev_week_revenue": round(prev_rev, 2),
                "total_orders": total_orders
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
