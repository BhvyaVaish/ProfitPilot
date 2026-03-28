from database import get_connection
from models import get_all_products, insert_alert
from config import LOW_STOCK_THRESHOLD, DEAD_STOCK_DAYS
from services.ai_engine import get_dead_stock
from services.festival_service import get_upcoming_festivals

def refresh_alerts():
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM alerts WHERE message NOT LIKE '%manual%'")
    
    products = get_all_products()
    dead = get_dead_stock()
    festivals = get_upcoming_festivals()
    
    issues_found = False
    
    for p in products:
        if p['stock'] < LOW_STOCK_THRESHOLD:
            insert_alert(conn, 'red', f"Low stock: {p['name']} has only {p['stock']} units left")
            issues_found = True
            
    for d in dead:
        insert_alert(conn, 'yellow', f"Dead stock: {d['name']} hasn't sold in {DEAD_STOCK_DAYS}+ days")
        issues_found = True
        
    for f in festivals:
        if f['days_away'] <= 7 and f['relevant_products']:
            insert_alert(conn, 'yellow',
                f"Festival alert: {f['name']} in {f['days_away']} days - check stock for {', '.join(f['relevant_products'][:3])}")
            issues_found = True
            
    if not issues_found:
        insert_alert(conn, 'green', "All stock levels are healthy. No critical issues detected.")
        
    conn.commit()
    conn.close()

def get_unread_alerts():
    conn = get_connection()
    alerts = conn.execute("SELECT * FROM alerts WHERE is_read = 0 ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(a) for a in alerts]
