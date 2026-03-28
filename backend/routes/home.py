from flask import Blueprint, jsonify
from services.ai_engine import (
    get_prioritized_alerts,
    get_home_festival_insights,
    get_home_mini_insights,
    get_home_quick_summary
)

home_bp = Blueprint('home', __name__)

@home_bp.route('/api/home/summary', methods=['GET'])
def get_home_summary():
    try:
        priority_actions = get_prioritized_alerts()
        festival_insights = get_home_festival_insights()
        quick_summary = get_home_quick_summary()
        mini_insights = get_home_mini_insights()
        
        return jsonify({
            "priority_actions": priority_actions,
            "festival_insights": festival_insights,
            "quick_summary": quick_summary,
            "mini_insights": mini_insights
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
