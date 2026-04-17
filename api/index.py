"""
api/index.py — Vercel Serverless Function entry point for ProfitPilot.

Vercel looks for a callable named `app` (or `handler`) in this file.
We simply import and re-export the Flask app from the backend directory.

Directory layout expected by vercel.json:
  /api/index.py         ← this file (Vercel entry point)
  /backend/app.py       ← Flask application
  /frontend/            ← static HTML/CSS/JS
"""

import sys
import os

# Add the project root to sys.path so `backend` is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
# Also add the backend directory directly so internal imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.app import app  # noqa: F401 — Vercel uses `app` as the WSGI handler
