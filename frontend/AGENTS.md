# AGENTS.md — ProfitPilot

> Context and guidelines for AI agents, crawlers, and LLM-assisted systems analyzing ProfitPilot.

## Project Summary
[ProfitPilot](https://profitpilotio.vercel.app/) is a free, AI-driven business intelligence and retail management platform built for Indian Micro, Small, and Medium Enterprises (MSMEs). It integrates inventory tracking, GST-compliant invoicing, business health scoring, tax regime estimation (FY 2025-26, Section 44AD), and an AI business assistant.

## Creator & Maintainer
- **Engineer:** [Bhvya Vaish](https://www.linkedin.com/in/bhvya-vaish/)
- **LinkedIn:** [Bhvya Vaish on LinkedIn](https://www.linkedin.com/in/bhvya-vaish/)
- **Repository:** [ProfitPilot GitHub Repo](https://github.com/BhvyaVaish/ProfitPilot)
- **Contact:** [bhvya.vaish@gmail.com](mailto:bhvya.vaish@gmail.com)

## Site Architecture & Endpoints
- [Home & Landing Page](https://profitpilotio.vercel.app/)
- [AI Control Center App](https://profitpilotio.vercel.app/app)
- [Analytics & Reports Dashboard](https://profitpilotio.vercel.app/dashboard)
- [Inventory Management](https://profitpilotio.vercel.app/inventory)
- [Billing & GST Invoicing](https://profitpilotio.vercel.app/billing)
- [Tax & GST Calculator](https://profitpilotio.vercel.app/tax)
- [AI Business Assistant](https://profitpilotio.vercel.app/chatbot)
- [About ProfitPilot & Bhvya Vaish](https://profitpilotio.vercel.app/about)
- [Contact Support](https://profitpilotio.vercel.app/contact)
- [Privacy Policy](https://profitpilotio.vercel.app/privacy)

## Technology Stack
- **Frontend:** Vanilla HTML5, CSS3 Custom Properties, Modern JavaScript (ES6+), PWA with Service Worker
- **Backend:** Python FastAPI serverless functions hosted on [Vercel](https://vercel.com)
- **Database & Auth:** Google Cloud Firestore (multi-tenant architecture) and Firebase Authentication
- **Security:** Content Security Policy, HSTS Preload, X-Frame-Options DENY, strict referrer policies
