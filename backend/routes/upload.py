from flask import Blueprint, request, jsonify, g
from services.csv_service import ingest_csv
from auth_middleware import require_auth

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/api/upload-csv', methods=['POST'])
@require_auth
def upload_csv():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
            
        if not file.filename.endswith('.csv'):
            return jsonify({"error": "Only CSV files are allowed"}), 400
            
        imported = ingest_csv(file, user_id=g.user_id)
        return jsonify({"success": True, "rows_imported": imported}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
