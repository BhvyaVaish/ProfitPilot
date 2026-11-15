"""
alert_service.py — Smart business alert engine.

Fully migrated to Firestore. No SQL.
"""

import firestore_db
from config import LOW_STOCK_THRESHOLD, DEAD_STOCK_DAYS
from services.ai_engine import get_dead_stock


def refresh_alerts(user_id='demo'):
    from services.festival_service import match_festivals_to_inventory

    # Clear old alerts in Firestore
    firestore_db.clear_alerts(user_id)

    products = firestore_db.get_all_products(user_id)
    dead = get_dead_stock(user_id)

    # Use centralized smart matching logic
    match_result = match_festivals_to_inventory(user_id)
    suggestions = match_result.get('suggestions', [])

    issues_found = False

    # 1. Standard low stock alerts
    for p in products:
        if p.get('stock', 0) < LOW_STOCK_THRESHOLD:
            firestore_db.insert_alert(
                user_id, 'red',
                f"Low stock: {p['name']} has only {p['stock']} units left"
            )
            issues_found = True

    # 2. Dead stock alerts
    for d in dead:
        firestore_db.insert_alert(
            user_id, 'yellow',
            f"Dead stock: {d['name']} hasn't sold in {DEAD_STOCK_DAYS}+ days"
        )
        issues_found = True

    # 3. Smart Suggestions (Restock & Opportunity)
    for s in suggestions[:5]:  # Top 5 most urgent
        level = 'red' if s.get('type') == 'restock' else 'blue'
        firestore_db.insert_alert(user_id, level, s['message'])
        issues_found = True

    if not issues_found:
        firestore_db.insert_alert(
            user_id, 'green',
            "All stock levels are healthy. No critical issues detected."
        )


def get_unread_alerts(user_id='demo'):
    return firestore_db.get_alerts(user_id, unread_only=True)
