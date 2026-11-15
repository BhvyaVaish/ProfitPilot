"""
analytics.py — Analytics & dashboard routes.

Fully migrated to Firestore. No SQL.
"""

from flask import Blueprint, request, jsonify, g
import firestore_db
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
        sales_graph = firestore_db.get_sales_graph(user_id, days=days)

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

        # 8. Category-wise Sales Breakdown (last 30 days)
        category_breakdown = firestore_db.get_category_revenue(user_id, days=30)

        # 9. Summary stats
        rev_summary = firestore_db.get_revenue_summary(user_id)
        total_orders = firestore_db.count_bills(user_id, days=7)

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
                "week_revenue": round(rev_summary['week'], 2),
                "prev_week_revenue": round(rev_summary['prev_week'], 2),
                "total_orders": total_orders
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
