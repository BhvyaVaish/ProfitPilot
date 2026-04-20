// ─────────────────────────────────────────────────────
// ProfitPilot — Central API Configuration
// Update API_BASE_URL to your Render backend URL after deployment.
// ─────────────────────────────────────────────────────
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:5000'
  : 'https://profitpilot-backend-r0cw.onrender.com';