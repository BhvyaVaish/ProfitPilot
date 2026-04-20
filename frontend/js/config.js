// ─────────────────────────────────────────────────────
// ProfitPilot — Central API Configuration
// Update API_BASE_URL to your Render backend URL after deployment.
// ─────────────────────────────────────────────────────
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:5000'
  : 'https://YOUR_RENDER_APP_NAME.onrender.com';  // ← Replace with actual Render URL after deploy
