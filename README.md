<div align="center">

# ✈️ ProfitPilot
**AI-Driven Retail Intelligence for MSMEs**

*Smart inventory. Real insights. Built for Indian small businesses.*

[![Python](https://img.shields.io/badge/Python-3.x-blue?style=flat-square&logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey?style=flat-square&logo=flask)](https://flask.palletsprojects.com)
[![Firebase](https://img.shields.io/badge/Auth-Firebase-yellow?style=flat-square&logo=firebase)](https://firebase.google.com)

</div>

---

## What is ProfitPilot?

ProfitPilot is a web app that helps small shop owners manage their business without needing an accountant or a tech background. Upload your inventory, record sales, and the app figures out what to restock, what's not selling, how much tax you owe, and what to focus on today — all in one place.

It's built specifically for the Indian market: GST rates, festival demand cycles, Section 44AD, Composition Scheme, and Hindi language support are all built in.

> **Setup guide** → [QUICK_START.md](QUICK_START.md)

---

## Features

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

## Tech Stack

| | |
|---|---|
| Frontend | HTML, Vanilla JS, CSS3, Chart.js |
| Backend | Python 3, Flask |
| Database | SQLite |
| Auth | Firebase Authentication |
| Festival Data | Calendarific API |
| Language | EN / HI (built-in i18n engine) |

---

## Project Structure

```
ProfitPilot/
├── README.md
├── QUICK_START.md          ← Setup, troubleshooting, FAQ
├── requirements.txt
├── .env.example
│
├── backend/
│   ├── app.py              ← Server entry point
│   ├── database.py         ← Schema & connection
│   ├── models.py           ← Data access
│   ├── config.py           ← GST rates, tax slabs
│   ├── auth_middleware.py  ← Auth verification
│   ├── routes/             ← API blueprints
│   │   ├── auth.py
│   │   ├── inventory.py
│   │   ├── billing.py
│   │   ├── analytics.py
│   │   ├── home.py
│   │   ├── tax.py
│   │   ├── chatbot.py
│   │   └── upload.py
│   └── services/           ← AI & business logic
│       ├── ai_engine.py
│       ├── chatbot_engine.py
│       ├── festival_service.py
│       └── csv_service.py
│
└── frontend/
    ├── index.html          ← Home / AI Command Center
    ├── dashboard.html      ← Analytics
    ├── inventory.html      ← Stock management
    ├── billing.html        ← Invoicing
    ├── tax.html            ← Tax estimator
    ├── chatbot.html        ← AI assistant
    ├── auth.html           ← Sign in / Sign up
    ├── onboarding.html     ← First-time setup
    ├── profile.html        ← Profile management
    ├── css/
    │   ├── base.css        ← Design tokens
    │   ├── layout.css      ← Grid & header
    │   ├── components.css  ← UI components
    │   └── auth.css        ← Auth & onboarding
    └── js/
        ├── api.js          ← HTTP helper
        ├── auth-guard.js   ← Auth state management
        ├── i18n.js         ← EN/HI translations
        ├── home.js
        ├── dashboard.js
        ├── inventory.js
        ├── billing.js
        ├── tax.js
        └── chatbot.js
```

---

## How the AI Works

No external ML library. The AI engine uses rolling sales averages to detect demand trends, cross-references upcoming festivals from the Calendarific API to predict category spikes, and calculates restock quantities with a 15% safety buffer. The Business Health Score is a weighted composite of stock availability, sales momentum, capital efficiency, product diversity, and revenue consistency.

---

## Pages

| URL | Page |
|---|---|
| `/` | Home — AI actions and overview |
| `/dashboard.html` | Revenue charts and analytics |
| `/inventory.html` | Product catalogue and stock |
| `/billing.html` | Create bills and print invoices |
| `/tax.html` | GST and income tax estimator |
| `/chatbot.html` | AI business assistant |
| `/auth` | Sign in / Sign up |
| `/onboarding` | First-time business setup |
| `/profile` | Edit your business profile |

---

<div align="center">

Built by **[Bhvya Vaish](https://github.com/bhvyavaish/)** for MSMEs everywhere.

</div>
