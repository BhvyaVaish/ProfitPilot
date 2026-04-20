"""
app.py — ProfitPilot Flask application.

Works in two modes:
  • Local dev  : python app.py  (runs on port 5000, hot-reload)
  • Vercel     : Module is imported; the `app` object is used as the handler.
                 The Vercel runtime calls init() via @app.before_first_request
                 (or the explicit startup block for newer Flask versions).
"""

import sys
import os

# Make sure the backend directory is importable when Vercel loads this module
# from the repo root via api/index.py
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, g, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from database import init_db, USE_POSTGRES
from auth_middleware import init_firebase_admin
from routes.billing import billing_bp
from routes.inventory import inventory_bp
from routes.analytics import analytics_bp
from routes.home import home_bp
from routes.chatbot import chatbot_bp
from routes.festivals import festivals_bp
from routes.upload import upload_bp
from routes.tax import tax_bp
from routes.auth import auth_bp
from routes.client_config import config_bp

app = Flask(__name__, static_folder='../frontend', static_url_path='')

allowed_origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://profitpilotio.vercel.app",
    os.environ.get("FRONTEND_URL", "https://profitpilotio.vercel.app"),
]
CORS(app, origins=allowed_origins, supports_credentials=True)

app.register_blueprint(auth_bp)
app.register_blueprint(config_bp)
app.register_blueprint(billing_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(home_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(festivals_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(tax_bp)


# ── Health check ────────────────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "ProfitPilot Backend"}), 200


# ── Global error handlers ───────────────────────────────────────────────────

@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad request", "message": str(e)}), 400

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({"error": "Unauthorized", "message": str(e)}), 401

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found", "message": str(e)}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error", "message": str(e)}), 500


# ── Static page routes ──────────────────────────────────────────────────────

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/auth')
def auth_page():
    return app.send_static_file('auth.html')

@app.route('/onboarding')
def onboarding_page():
    return app.send_static_file('onboarding.html')

@app.route('/profile')
def profile_page():
    return app.send_static_file('profile.html')

@app.route('/dashboard')
def dashboard_page():
    return app.send_static_file('dashboard.html')

@app.route('/inventory')
def inventory_page():
    return app.send_static_file('inventory.html')

@app.route('/billing')
def billing_page():
    return app.send_static_file('billing.html')

@app.route('/tax')
def tax_page():
    return app.send_static_file('tax.html')

@app.route('/chatbot')
def chatbot_page():
    return app.send_static_file('chatbot.html')

@app.route('/about')
def about_page():
    return app.send_static_file('about.html')


@app.teardown_appcontext
def close_db_connection(exception):
    db_conn = g.pop('db_conn', None)
    if db_conn is not None:
        db_conn.close()

# ── One-time initialisation ─────────────────────────────────────────────────

def _startup():
    """Run once when the app first starts (both locally and on Vercel)."""
    init_firebase_admin()

    # Auto-create tables + seed demo data if they don't already exist.
    # On Supabase/PostgreSQL this is safe to call every cold-start because
    # all CREATE TABLE statements use IF NOT EXISTS.
    try:
        init_db()
    except Exception as e:
        print(f"[WARN] DB init error (may be fine if already seeded): {e}")

    # Pre-warm alerts for the demo user
    try:
        from services.alert_service import refresh_alerts
        refresh_alerts('demo')
    except Exception as e:
        print(f"[WARN] Could not refresh alerts on startup: {e}")


# Flask 2.x+ deprecated before_first_request; use with app.app_context() instead.
with app.app_context():
    _startup()


# ── Local dev entry-point ───────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, port=5000)
