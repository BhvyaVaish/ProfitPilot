from database import get_connection
from models import get_all_products
from config import LOW_STOCK_THRESHOLD, DEAD_STOCK_DAYS
from services.ai_engine import get_dead_stock
from services.festival_service import get_upcoming_festivals

def refresh_alerts(user_id='demo'):
    from services.festival_service import match_festivals_to_inventory
    from database import get_connection

    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM alerts WHERE user_id = ?", (user_id,))

    products = get_all_products(user_id)
    dead = get_dead_stock(user_id)
    
    # Use centralized smart matching logic
    match_result = match_festivals_to_inventory(user_id)
    suggestions = match_result['suggestions']

    issues_found = False

    # 1. Standard low stock alerts
    for p in products:
        if p['stock'] < LOW_STOCK_THRESHOLD:
            c.execute("INSERT INTO alerts (user_id, level, message) VALUES (?, ?, ?)",
                      (user_id, 'red', f"Low stock: {p['name']} has only {p['stock']} units left"))
            issues_found = True

    # 2. Dead stock alerts
    for d in dead:
        c.execute("INSERT INTO alerts (user_id, level, message) VALUES (?, ?, ?)",
                  (user_id, 'yellow', f"Dead stock: {d['name']} hasn't sold in {DEAD_STOCK_DAYS}+ days"))
        issues_found = True

    # 3. Smart Suggestions (Restock & Opportunity)
    for s in suggestions[:5]:  # Top 5 most urgent
        level = 'red' if s['type'] == 'restock' else 'blue'
        c.execute("INSERT INTO alerts (user_id, level, message) VALUES (?, ?, ?)",
                  (user_id, level, s['message']))
        issues_found = True

    if not issues_found:
        c.execute("INSERT INTO alerts (user_id, level, message) VALUES (?, ?, ?)",
                  (user_id, 'green', "All stock levels are healthy. No critical issues detected."))

    conn.commit()
    conn.close()

def get_unread_alerts(user_id='demo'):
    conn = get_connection()
    alerts = conn.execute("SELECT * FROM alerts WHERE user_id = ? AND is_read = 0 ORDER BY created_at DESC", (user_id,)).fetchall()
    conn.close()
    return [dict(a) for a in alerts]
