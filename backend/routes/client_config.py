"""
routes/client_config.py — Serves Firebase client configuration to the frontend.

Firebase client config (apiKey, projectId, etc.) is NOT a secret — it's designed
to be public.  However, we serve it from an API endpoint instead of hardcoding
it in JavaScript files so that:
  1. No secrets live in version-controlled source files.
  2. Key rotation only requires changing environment variables.
  3. Different environments (dev/staging/prod) use different configs automatically.
"""

import os
from flask import Blueprint, jsonify

config_bp = Blueprint('config', __name__)


@config_bp.route('/api/config', methods=['GET'])
def get_client_config():
    """Return Firebase client-side configuration from environment variables."""
    config = {
        "apiKey":            os.getenv("FIREBASE_API_KEY", ""),
        "authDomain":        os.getenv("FIREBASE_AUTH_DOMAIN", ""),
        "projectId":         os.getenv("FIREBASE_PROJECT_ID", ""),
        "storageBucket":     os.getenv("FIREBASE_STORAGE_BUCKET", ""),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", ""),
        "appId":             os.getenv("FIREBASE_APP_ID", ""),
        "measurementId":     os.getenv("FIREBASE_MEASUREMENT_ID", ""),
    }

    # Don't expose an empty config — tell the caller something is wrong
    if not config["apiKey"]:
        return jsonify({"error": "Firebase client config not set. Check server environment variables."}), 500

    return jsonify(config)
