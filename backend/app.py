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

from flask import Flask
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
CORS(app)

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
