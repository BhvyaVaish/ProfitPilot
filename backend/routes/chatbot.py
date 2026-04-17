from flask import Blueprint, request, jsonify, g
from services.chatbot_engine import get_response
from auth_middleware import optional_auth

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/api/chat', methods=['POST'])
@optional_auth
def chat():
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"error": "Message required"}), 400
            
        reply = get_response(data['message'], user_id=g.user_id)
        return jsonify({"response": reply}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
