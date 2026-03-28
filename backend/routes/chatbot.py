from flask import Blueprint, request, jsonify
from services.chatbot_engine import get_response

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"error": "Message required"}), 400
            
        reply = get_response(data['message'])
        return jsonify({"response": reply}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
