# StockPilot AI Implementation Plan

This document outlines the strategy for building StockPilot AI, a full-stack web application designed as an AI-powered business management assistant for small businesses.

## Goal Description

The objective is to establish a fully functional MVP handling billing, inventory management, demand prediction, festival awareness, and an interactive chatbot. The system will rely on a Python Flask backend using basic SQLite for storage, and a vanilla HTML/CSS/JS frontend styled with a modern dark aesthetics.

## Proposed Changes

We will construct the project following the specified folder structure and modular design constraint.

### Configuration & Base Setup

#### [NEW] [backend/config.py](file:///C:/Users/Asus/Documents/Hackthon%20Project/backend/config.py)
- Setup database paths, algorithm thresholds, and API keys.
- Include static fallback festival list if Calendarific API fails or is not provided.

#### [NEW] [backend/database.py](file:///C:/Users/Asus/Documents/Hackthon%20Project/backend/database.py)
- Establish SQLite schema: `products`, `sales`, `bills`, and `alerts` tables.
- Add robust `seed_data()` function to populate database defaults dynamically on blank installations.

#### [NEW] [backend/models.py](file:///C:/Users/Asus/Documents/Hackthon%20Project/backend/models.py)
- Provide raw SQL handler routines for all generic read and database connection management requirements.

#### [NEW] [requirements.txt](file:///C:/Users/Asus/Documents/Hackthon%20Project/requirements.txt)
- Specific Python dependencies: `flask`, `flask-cors`, `requests`, `python-dotenv`.

### Service Layer (Business Logic)

#### [NEW] [backend/services/ai_engine.py](file:///C:/Users/Asus/Documents/Hackthon%20Project/backend/services/ai_engine.py)
- Implement demand predictions using moving averages.
- Generate dynamic restock suggestions and high potential product insights.

#### [NEW] [backend/services/festival_service.py](file:///C:/Users/Asus/Documents/Hackthon%20Project/backend/services/festival_service.py)
- Abstract Calendarific HTTP integration logic with static mappings from MSME-friendly categories.

#### [NEW] [backend/services/alert_service.py](file:///C:/Users/Asus/Documents/Hackthon%20Project/backend/services/alert_service.py)
- Automatically assess product anomalies (low stock, dead stock) generating persistent DB badges updated on new bills.

#### [NEW] [backend/services/chatbot_engine.py](file:///C:/Users/Asus/Documents/Hackthon%20Project/backend/services/chatbot_engine.py)
- Provide a robust rule-based local intent engine matching general queries against real-time DB states.

#### [NEW] [backend/services/csv_service.py](file:///C:/Users/Asus/Documents/Hackthon%20Project/backend/services/csv_service.py)
- Allow localized historical data ingestion via simple CSV parsing.

### Routing Layer

#### [NEW] backend/routes/*
- Generate blueprint-separated modules for `/api/inventory`, `/api/billing`, `/api/analytics`, `/api/home/summary`, `/api/chat`, `/api/festivals`, and `/api/upload-csv`.

#### [NEW] [backend/app.py](file:///C:/Users/Asus/Documents/Hackthon%20Project/backend/app.py)
- Tie all blueprints directly to the active WSGI interface and route static assets correctly locally.

### Frontend Layer

#### [NEW] frontend/css/*
- Create a reusable, custom dark theme CSS system using explicit CSS properties mimicking Tailwind architecture.

#### [NEW] frontend/js/*
- Abstract standard REST fetches to simplify network requests.
- Hook into specific DOM endpoints dynamically without requiring modern frameworks contexts like React or Vue.

#### [NEW] frontend/*.html
- Establish consistent, rich responsive layouts utilizing sidebars for all pages: Home, Dashboard, Billing, Inventory, and Chatbot.

## Open Questions

> [!NOTE] 
> The prompt provides exact directives for every file structure. I will synthesize the code implementations mirroring these precise architectural guidelines immediately upon your approval.

## Verification Plan

### Automated Tests
- Once files are provisioned, I will use terminal scripts to verify the dependencies via `pip install -r requirements.txt`.
- Start the server `python backend/app.py` in the background to ensure no syntax or database initialization errors.

### Manual Verification
- You will be able to follow the specified "Hackathon Presentation Order" demo script starting locally via `http://localhost:5000/`.
