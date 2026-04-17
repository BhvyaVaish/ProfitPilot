from flask import Blueprint, jsonify, g
from auth_middleware import optional_auth
from services.festival_service import get_upcoming_festivals, match_festivals_to_inventory

festivals_bp = Blueprint('festivals', __name__)

@festivals_bp.route('/api/festivals', methods=['GET'])
@optional_auth
def get_festivals_api():
    try:
        user_id = g.user_id
        result = match_festivals_to_inventory(user_id)
        return jsonify({
            "festivals": result['festivals'],
            "suggestions": result['suggestions'],
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
