from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

import os
load_dotenv()

from database import init_db
from routes.billing import billing_bp
from routes.inventory import inventory_bp
from routes.analytics import analytics_bp
from routes.home import home_bp
from routes.chatbot import chatbot_bp
from routes.festivals import festivals_bp
from routes.upload import upload_bp
from routes.tax import tax_bp

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

app.register_blueprint(billing_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(home_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(festivals_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(tax_bp)

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    if not os.path.exists(os.path.join(os.path.dirname(__file__), 'stockpilot.db')):
        init_db()
    
    init_db()
    
    try:
        from services.alert_service import refresh_alerts
        refresh_alerts()
    except Exception as e:
        print("Could not refresh alerts on startup:", e)
        
    app.run(debug=True, port=5000)
