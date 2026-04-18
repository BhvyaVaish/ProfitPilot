# 🚀 Quick Start Guide — ProfitPilot

This guide will walk you through the setup, configuration, and operation of ProfitPilot on your local machine.

---

## 📋 Table of Contents

- [Prerequisites](#-prerequisites)
- [Installation Guide](#-installation-guide)
- [Subsequent Runs](#-subsequent-runs)
- [Configuration](#️-configuration)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq)

---

## 💻 Prerequisites

Ensure you have the following installed:

- **Python 3.8 or higher**
- **Git** (optional, for cloning)
- **Modern Browser** (Chrome, Firefox, Safari, or Edge)

---

## 📥 Installation Guide

### Step 1: Clone the Repository

```bash
git clone https://github.com/bhvyavaish/profitpilot.git
cd profitpilot
```

### Step 2: Create and Activate a Virtual Environment

Isolating dependencies is highly recommended.

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run the Application

Start the backend server:

```bash
python backend/app.py
```

### Step 5: Access the App

Open your browser and go to:
👉 **[http://localhost:5000](http://localhost:5000)**

---

## 🔁 Subsequent Runs

After the initial setup, you only need to run:

**Windows:**

```powershell
.\.venv\Scripts\activate
python backend/app.py
```

**macOS / Linux:**

```bash
source .venv/bin/activate
python backend/app.py
```

---

## ⚙️ Configuration

### Environment Variables (`.env`)

1. Create a `.env` file from the template:
   - **Windows**: `copy .env.example .env`
   - **macOS/Linux**: `cp .env.example .env`
2. (Optional) Add your **Calendarific API Key** for live festival data.
3. (Optional) Set your **Firebase Service Account Path**.

### Firebase Integration (Optional)

If you want to enable secure user authentication:

1. Save your Firebase service account JSON as `backend/firebase-service-account.json`.
2. Update `frontend/js/firebase-config.js` with your web app configuration.

_Note: Without Firebase, the app runs in **Demo Mode** with local authentication disabled._

---

## 🔧 Troubleshooting

### "Python: command not found"

- On macOS/Linux, try using `python3` instead of `python`.
- Ensure Python is added to your system's PATH.

### "Permission Denied" (Windows PowerShell)

If you can't activate the virtual environment, run this as Administrator:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Port 5000 already in use

If the server fails to start, edit the last line of `backend/app.py`:

```python
app.run(debug=True, port=5001)
```

### Resetting the Database

To wipe all data and start fresh (this will recreate the demo data):

- **Windows**: `del backend\profitpilot.db`
- **macOS/Linux**: `rm backend/profitpilot.db`

### Missing Modules

Ensure your virtual environment is activated. You should see `(.venv)` in your terminal prompt. If not, rerun the activation step.

---

## ❓ FAQ

**Q: Does it work offline?**  
A: Yes! The core features work offline. Internet is only required for Firebase Auth and live Festival API updates.

**Q: Can I print the bill for my business name?**  
A: Yes, bills are automatically generated with your business name and details as configured in your profile.

**Q: Can I customize the application logo?**  
A: No, core ProfitPilot branding and logos are secured to ensure platform integrity and prevent unauthorized modifications to the software's identity.

**Q: Is my data secure?**  
A: Your business data is stored locally in an encrypted-ready SQLite database.

---

**Happy Selling! 🎉**
