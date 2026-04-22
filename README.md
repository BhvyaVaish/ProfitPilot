<div align="center">
   
# ProfitPilot

**Intelligent Inventory & Business Management for MSMEs.** <br>
*Smart inventory, real-time AI insights, seamless billing, GST tools and much more.....* <br>
*Built for Indian small businesses.* <br>
   
[![Python](https://img.shields.io/badge/Python-3.x-blue?style=flat-square&logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey?style=flat-square&logo=flask)](https://flask.palletsprojects.com)
[![Firebase](https://img.shields.io/badge/Auth-Firebase-yellow?style=flat-square&logo=firebase)](https://firebase.google.com)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?style=flat-square&logo=javascript)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![Vercel](https://img.shields.io/badge/Deployed-Vercel-black?style=flat-square&logo=vercel)](https://vercel.com)


---
</div>

## 📌 What is ProfitPilot?

ProfitPilot is a web app that helps small shop owners manage their business without needing an accountant or a tech background. Upload your inventory, record sales and the app figures out what to restock, what's not selling, how much tax you owe and what to focus on today — all in one place.

It's built specifically for the Indian market: GST rates, festival demand cycles, Section 44AD, Composition Scheme and Hindi language support are all built in.

---

## ✨ Features

**Home — AI Command Center**  
Real-time priority actions ranked by urgency. Business health score. Festival demand alerts. Weekly revenue at a glance.

**Inventory Management**  
Add products manually or import via CSV. Live stock filters (All / In Stock / Low / Out of Stock). Smart restock thresholds based on actual sales velocity.

**Analytics Dashboard**  
Revenue charts, top products, category breakdown, dead stock warnings, and procurement suggestions — all pulled from your own data.

**Billing & Invoicing**  
Create bills, auto-calculate GST, print professional invoices, and track bill history. Stock deducts automatically on each sale.

**Tax Estimator**  
GST breakdown by category. Income tax comparison (New vs Old Regime). Section 44AD and GST Composition Scheme eligibility checker. Fully personalized based on your business profile.

**AI Assistant**  
Ask questions in plain English or Hindi — *"What should I restock?"*, *"Mera profit kaisa hai?"* — and get answers based on your actual data, not generic answers.

**Multi-User & Secure**  
Every user's data is completely isolated. Sign in with email or Google. Onboarding captures your business profile for personalized AI suggestions and tax tips.

---

## 🌐 Live Demo

**[→ Open ProfitPilot](https://profitpilotio.vercel.app/)**

> **This is the intended way to experience ProfitPilot.**
> ProfitPilot is a full-stack cloud application. Authentication, AI insights, dynamic analytics, and database operations are designed to run seamlessly in our production environment. 

---

## 🧠 Tech Stack

**Frontend:** HTML5, CSS3 (Glassmorphism), Vanilla JavaScript (ES6+), Chart.js, PWA (Service Workers, Web App Manifest)
**Backend:** Python 3, Flask (RESTful API), SQLite (local) / PostgreSQL (production)
**Services:** Google Gemini AI (Insights/Chatbot), Google Calendar API (Festivals), Firebase Auth
**Deployment:** Vercel (Serverless Edge), Supabase (PostgreSQL)

---

## 🔐 Security

- **Environment Isolation:** All API keys and secrets are managed via environment variables and are never committed to the repository.
- **Data Privacy:** Multi-tenant architecture ensures every user's data is strictly isolated by `user_id` at the database query level.
- **Authentication:** Firebase ID tokens are securely verified server-side on every authenticated request.

---

## 📂 Project Structure

```text
ProfitPilot/
├── backend/                  # Python Flask server & AI logic
│   ├── routes/               # API blueprints (billing, inventory, tax, auth, etc.)
│   ├── services/             # AI engine, festival algorithms, chatbot
│   └── auth_middleware.py    # Firebase token verification
├── frontend/                 # PWA frontend (HTML, CSS, JS)
│   ├── css/                  # Responsive styles & design system
│   └── js/                   # API controllers, auth guards, feature modules
├── .env.example              # Environment variables template
├── vercel.json               # Deployment configuration
└── requirements.txt          # Python dependencies
```

---

## 🧑‍💻 Local Setup (Developers Only)

> ⚠️ **IMPORTANT WARNING FOR DEVELOPERS**
> Local execution provides a **highly limited, development-only experience**. 
> Without configuring external API keys (Firebase, Google AI, Google Calendar), the application defaults to a "Demo Mode" where authentication is bypassed, data is shared, and AI features fall back to static responses.

### Prerequisites
- Python 3.8 or higher
- Git
- A modern browser

### Setup Guide

1. **Clone the Repository**
   ```bash
   git clone https://github.com/bhvyavaish/profitpilot.git
   cd profitpilot
   ```

2. **Create a Virtual Environment & Install Dependencies**
   ```bash
   # Windows
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   
   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   ```bash
   # Windows: copy .env.example .env
   # macOS/Linux: cp .env.example .env
   ```
   *Open `.env` and fill in the required keys. See `.env.example` for details.*

4. **Run the Server**
   ```bash
   python backend/app.py
   ```
   *Open your browser at: `http://localhost:5000`*

### Troubleshooting
- **`Permission Denied` (Windows PowerShell):** Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` as Administrator.
- **Port 5000 in use:** Edit `backend/app.py` and change `port=5000` to `port=5001`.
- **Database Reset:** Delete the `backend/profitpilot.db` file to start fresh.

---

## ⚡ Offline Capabilities (PWA)

ProfitPilot is installable as a Progressive Web App (PWA) directly from the browser.

| Feature                             | Offline Available     |
| ----------------------------------- | --------------------- |
| Viewing app UI and last-synced data | ✅ Yes (PWA cache)    |
| Language switching (EN / HI)        | ✅ Yes (runs locally) |
| Tooltips and UI interactions        | ✅ Yes                |
| Generating a new bill               | ❌ Requires internet  |
| Adding / editing inventory          | ❌ Requires internet  |
| AI insights & health score          | ❌ Requires internet  |
| Logging in                          | ❌ Requires internet  |

---

## 📎 Links

- **Live App:** [profitpilot.vercel.app](https://profitpilotio.vercel.app/)
- **GitHub:** [github.com/bhvyavaish/ProfitPilot](https://github.com/bhvyavaish/ProfitPilot)

---

## 👤 Author

**Bhvya Vaish**
- [LinkedIn](https://www.linkedin.com/in/bhvya-vaish/)
- [GitHub](https://github.com/bhvyavaish)
