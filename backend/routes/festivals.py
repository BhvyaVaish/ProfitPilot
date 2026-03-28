from flask import Blueprint, jsonify
from services.festival_service import get_upcoming_festivals

festivals_bp = Blueprint('festivals', __name__)

@festivals_bp.route('/api/festivals', methods=['GET'])
def get_festivals_api():
    try:
        return jsonify({"festivals": get_upcoming_festivals(30)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
