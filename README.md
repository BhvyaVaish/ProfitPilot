# 🚀 ProfitPilot - AI-Driven Retail Management

ProfitPilot is a premium, AI-driven business management and point-of-sale (POS) tool specifically designed for small and medium enterprises (MSMEs). It transforms raw business data into actionable, easy-to-understand insights, helping shop owners manage inventory, predict demand, estimate tax liabilities, and generate professional invoices—all without needing a background in data science or accounting.

---

## ✨ Key Features

- **🌐 AI Control Center (Home):** A decision-making engine that instantly ranks the top actions you need to take today (restock warnings, high-demand alerts, dead stock detection).
- **📊 Deep Analytics Dashboard:** Visualizes revenue velocity, catalog performance, cash efficiency, and provides mathematically sound smart procurement suggestions based on trends and upcoming festivals.
- **📦 Smart Inventory Management:** A powerful control panel to manage your stock with instant color-coded health indicators and dynamic real-time threshold warnings, ensuring you never run out of your best-selling items.
- **🧾 Billing & Invoicing:** Seamless cart management and bill generation that automatically calculates subtotal, GST (CGST/SGST), and synchronizes your live inventory instantly.
- **💰 Tax & Financial Insights:** Demystifies your finances by estimating gross revenue, net profit margins, GST liability, and slab-based income tax, along with actionable tax-saving tips.
- **🤖 AI Conversational Assistant:** A simulated natural language chatbot that acts as your business partner. Ask it about top-selling items or restock needs and get instant, data-backed answers.

---

## 🛠️ Technology Stack

Our application features a robust separation of concerns, utilizing an elegant custom UI overlayed on a fast, scalable Python backend.

- **Frontend:** HTML5, CSS3 (Custom Premium Dark-Mode Glassmorphic UI), Vanilla JavaScript, Chart.js
- **Backend API:** Python 3, Flask (RESTful architecture)
- **Database:** SQLite 3 (Lightweight, serverless, and robust local storage)
- **Dependencies:** `Flask`, `Flask-CORS`, `requests`, `python-dotenv`

---

## 🚀 Installation & Setup instructions

Follow these steps to seamlessly clone, set up, and run ProfitPilot on any machine.

### Prerequisites
- **Python 3.8+** installed on your system.
- **Git** installed on your system.

### 1. Clone the Repository
Open your terminal and clone the project:
```bash
git clone https://github.com/your-username/profitpilot.git
cd profitpilot
```

### 2. Create a Virtual Environment
It is highly recommended to isolate your dependencies using a Python virtual environment:

**On Windows:**
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

**On Mac/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
With your virtual environment activated (you will see `(.venv)` in your terminal prompt), install the required backend packages:
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables (Optional)
If you want the Festival Prediction Engine to pull live data from the Calendarific API rather than using the integrated fallback system:
1. Copy the example file:
   - Linux/Mac: `cp .env.example .env`
   - Windows: `copy .env.example .env`
2. Open `.env` and replace `your_api_key_here` with your actual key.

### 5. Start the Application Server
Boot up the Python backend server (which also serves the frontend):
```bash
python backend/app.py
```
*Note: Upon its first run, the system will automatically generate a fresh `stockpilot.db` SQLite database populated with demo inventory and sales figures to power your charts!*

### 6. Open the Application
Navigate to your preferred web browser and open:
👉 **[http://localhost:5000](http://localhost:5000)**

---

## 📂 Repository Architecture

```text
ProfitPilot/
├── backend/
│   ├── app.py                 # Core Flask application and server configuration
│   ├── config.py              # Environment variables, algorithm thresholds, and fallbacks
│   ├── database.py            # SQLite schema initialization and seed generation
│   ├── models.py              # Database interaction and manipulation methods
│   ├── routes/                # Modular API endpoints (Analytics, Billing, Inventory)
│   └── services/              # Core logic layer (AI Engine, Chatbot queries, External APIs)
│
├── frontend/
│   ├── css/                   # Global styles, layout grids, and premium UI components
│   ├── js/                    # Client-side JavaScript bound to DOM manipulations
│   └── *.html                 # The interconnected web application interfaces
│
├── .env.example               # Template for API Keys and local secrets
├── .gitignore                 # Protected system files
└── requirements.txt           # Python dependency manifest
```

---

## 💡 Troubleshooting

- **Port 5000 is occupied:** If Flask throws a port unavailable error, edit the `app.run(port=5000)` port in `backend/app.py` or manually stop the conflicting process.
- **Missing Module Errors:** This happens if your virtual environment is deactivated. Run `.\.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Mac/Linux) and reinstall the `requirements.txt`.
- **Resetting the Database:** If you wish to wipe the application data and start over, simply delete `backend/stockpilot.db` and restart the backend server. It will automatically regenerate a new database on launch.
