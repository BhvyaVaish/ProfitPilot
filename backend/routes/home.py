from flask import Blueprint, jsonify, g
from auth_middleware import optional_auth
from services.ai_engine import (
    get_prioritized_alerts,
    get_home_festival_insights,
    get_home_mini_insights,
    get_home_quick_summary,
    get_business_health_score
)

home_bp = Blueprint('home', __name__)

@home_bp.route('/api/home/summary', methods=['GET'])
@optional_auth
def get_home_summary():
    try:
        user_id = g.user_id
        priority_actions = get_prioritized_alerts(user_id)
        festival_insights = get_home_festival_insights(user_id)
        quick_summary = get_home_quick_summary(user_id)
        mini_insights = get_home_mini_insights(user_id)
        health_score = get_business_health_score(user_id)

        return jsonify({
            "priority_actions": priority_actions,
            "festival_insights": festival_insights,
            "quick_summary": quick_summary,
            "mini_insights": mini_insights,
            "health_score": health_score
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
