<div align="center">
   
# ProfitPilot

**Intelligent Inventory & Business Management for MSMEs.** <br>
*Smart inventory, real-time AI insights, seamless billing, GST tools, and always-on cloud database.* <br>
*Built for Indian small businesses.* <br>
   
[![Python](https://img.shields.io/badge/Python-3.x-blue?style=flat-square&logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey?style=flat-square&logo=flask)](https://flask.palletsprojects.com)
[![Firebase Auth](https://img.shields.io/badge/Auth-Firebase-yellow?style=flat-square&logo=firebase)](https://firebase.google.com)
[![Firestore](https://img.shields.io/badge/Database-Cloud_Firestore-orange?style=flat-square&logo=firebase)](https://firebase.google.com/docs/firestore)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?style=flat-square&logo=javascript)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![Vercel](https://img.shields.io/badge/Deployed-Vercel-black?style=flat-square&logo=vercel)](https://vercel.com)

---
</div>

## 📌 What is ProfitPilot?

ProfitPilot is a web app that helps small shop owners manage their business without needing an accountant or a tech background. Upload your inventory, record sales and the app figures out what to restock, what's not selling, how much tax you owe and what to focus on today — all in one place.

It's built specifically for the Indian market: GST rates, festival demand cycles, Section 44AD, Composition Scheme, and bilingual Hindi/English support are all built in.

---

## ✨ Features

- **Home — AI Command Center:** Real-time priority actions ranked by urgency, composite business health score, festival demand alerts, and weekly revenue velocity at a glance.
- **Inventory Management:** Add products manually or bulk import via CSV. Live stock filters (All / In Stock / Low / Out of Stock). Smart restock thresholds calculated from rolling sales velocity.
- **Analytics Dashboard:** Revenue trajectory charts, top products, category breakdown, dead stock warnings, and smart procurement suggestions.
- **Billing & Invoicing:** Rapid bill creation with category-based GST auto-calculation, printable invoices, and real-time automatic stock decrements.
- **Tax Estimator:** Category-wise GST breakdown, Income Tax comparison (New vs. Old Regime), Section 44AD presumptive taxation, and GST Composition Scheme checker.
- **AI Assistant:** Bilingual business chatbot (English & Hindi) that understands questions like *"What should I restock?"*, *"Aaj ki sales kitni hui?"*, or *"Explain Section 44AD"*.
- **Always-On Cloud Architecture:** Powered by Google Cloud Firestore and Vercel Serverless — zero database sleeping, zero pause timeouts, instant response times.
- **Multi-Tenant Security:** Every user's data is strictly isolated by authenticated UID with Firebase Admin SDK verification on every request.

---

## 🌐 Live Demo

**[→ Open ProfitPilot](https://profitpilotio.vercel.app/)**

> ProfitPilot is a production full-stack application. Authentication, Firestore storage, real-time analytics, and AI insights run seamlessly on Vercel with zero cold-start database delays.

---

## 🧠 Tech Stack

- **Frontend:** HTML5, CSS3 (Glassmorphic Design), Vanilla JavaScript (ES6+), Chart.js, PWA (Service Workers, Web App Manifest)
- **Backend:** Python 3, Flask RESTful API, Vercel Serverless Functions
- **Database:** Google Cloud Firestore (Always-on, multi-region NoSQL)
- **Authentication:** Firebase Auth (Email/Password & Google Sign-In with auto-session persistence)
- **AI & Integrations:** Google Gemini AI (GenAI SDK), Google Calendar Public API (Indian Holiday Engine)
- **Hosting:** Vercel (Edge CDN & Serverless Python Runtime)

---

## 🔐 Security

- **Environment Isolation:** All sensitive keys (Firebase Admin credentials, Gemini API tokens) are managed securely via Vercel Environment Variables.
- **Data Isolation:** User sub-collections (`users/{uid}/products`, `users/{uid}/sales`, etc.) ensure complete data isolation between accounts.
- **Token Verification:** Every API request verifies cryptographic Firebase ID tokens before resolving data.

---

## 📂 Project Structure

```text
ProfitPilot/
├── api/
│   └── index.py              # Vercel Serverless WSGI entry-point
├── backend/                  # Flask REST API & Core Intelligence
│   ├── routes/               # Modular API blueprints (inventory, billing, tax, auth, etc.)
│   ├── services/             # AI engine, festival matcher, chatbot, CSV ingest
│   ├── auth_middleware.py    # Firebase token & admin SDK management
│   ├── firestore_db.py       # Firestore database adapter & aggregation layer
│   └── config.py             # GST rates, tax slabs, festival lookups
├── frontend/                 # PWA Client
│   ├── css/                  # Styling & design system
│   ├── js/                   # Controllers, auth guards, charts, API adapters
│   └── *.html                # Single-page interface views
├── .env.example              # Environment variables template
├── vercel.json               # Serverless routing & static asset configuration
└── requirements.txt          # Python dependencies
```

---

## 🧑‍💻 Local Development

### Prerequisites
- Python 3.10+
- A Firebase project with Cloud Firestore and Authentication enabled

### Setup Guide

1. **Clone the Repository**
   ```bash
   git clone https://github.com/BhvyaVaish/ProfitPilot.git
   cd ProfitPilot
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
   # Copy template
   copy .env.example .env     # Windows
   cp .env.example .env       # macOS / Linux
   ```
   *Place your `firebase-service-account.json` in `backend/` and populate Firebase client variables in `.env`.*

4. **Start the Server**
   ```bash
   python backend/app.py
   ```
   *Navigate to `http://localhost:5000` in your browser.*

---

## ⚡ Progressive Web App (PWA)

ProfitPilot is installable as a native-feeling app on mobile and desktop:

| Capability | PWA Support |
| :--- | :--- |
| App Shell & Static Assets | ✅ Fully cached for instant loading |
| Bilingual Interface (EN / HI) | ✅ Instant client-side switching |
| Tooltips & Explanations | ✅ Offline accessible |
| Live Inventory & Billing Sync | ☁️ Real-time Cloud Firestore sync |
| AI Recommendations & Tax Engine | ☁️ Real-time cloud computation |

---

## 👤 Author

**Bhvya Vaish**
- [LinkedIn](https://www.linkedin.com/in/bhvya-vaish/)
- [GitHub](https://github.com/bhvyavaish)
