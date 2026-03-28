from database import get_connection
from models import get_all_products
from config import RESTOCK_BUFFER
from services.festival_service import get_upcoming_festivals

def get_moving_average(product_id, days=7):
    conn = get_connection()
    result = conn.execute("""
        SELECT COALESCE(SUM(quantity), 0) / CAST(? AS REAL) as avg_daily
        FROM sales
        WHERE product_id = ?
        AND sold_at >= date('now', ? || ' days')
    """, (days, product_id, f'-{days}')).fetchone()
    conn.close()
    return result['avg_daily'] if result and result['avg_daily'] is not None else 0.0

def get_moving_average_range(product_id, start_days_ago, end_days_ago):
    conn = get_connection()
    days = start_days_ago - end_days_ago
    result = conn.execute("""
        SELECT COALESCE(SUM(quantity), 0) / CAST(? AS REAL) as avg_daily
        FROM sales
        WHERE product_id = ?
        AND sold_at >= date('now', ? || ' days')
        AND sold_at < date('now', ? || ' days')
    """, (days, product_id, f'-{start_days_ago}', f'-{end_days_ago}')).fetchone()
    conn.close()
    return result['avg_daily'] if result and result['avg_daily'] is not None else 0.0

def get_restock_suggestions():
    products = get_all_products()
    festivals = get_upcoming_festivals()
    festival_keywords = [cat.lower() for f in festivals if f['days_away'] <= 7 for cat in f['relevant_categories']]
    suggestions = []
    
    for p in products:
        pid = p['id']
        name = p['name']
        stock = p['stock']
        category = p['category'].lower()
        
        avg_last_7 = get_total_sales_range(pid, 7) / 7.0
        
        avg_last_3 = get_moving_average_range(pid, 3, 0)
        avg_prev_3 = get_moving_average_range(pid, 6, 3)
        
        predicted_demand = avg_last_7 * 7
        is_festival = category in festival_keywords or any(k in name.lower() for k in festival_keywords)
        
        # Give dormant products a baseline if 0 sales but festival approaching
        if is_festival and predicted_demand == 0:
            predicted_demand = 15
            
        if avg_prev_3 > 0 and avg_last_3 > avg_prev_3:
            predicted_demand *= 1.20
                
        if is_festival:
            predicted_demand *= 1.30
            
        predicted_demand = round(predicted_demand)
        buffer = round(predicted_demand * 0.15)
        
        restock = predicted_demand - stock + buffer
        
        if restock > 0:
            suggestions.append({
                "id": pid,
                "name": name,
                "current_stock": stock,
                "predicted_demand": predicted_demand,
                "suggested_restock": restock
            })
            
    return sorted(suggestions, key=lambda x: x['suggested_restock'], reverse=True)[:10]

def get_dead_stock():
    festivals = get_upcoming_festivals()
    festival_keywords = [cat.lower() for f in festivals if f['days_away'] <= 7 for cat in f['relevant_categories']]
    
    conn = get_connection()
    dead = conn.execute("""
        SELECT p.id, p.name, p.stock, p.category,
          COALESCE(strftime('%d-%m-%Y', MAX(s.sold_at)), 'Never') as last_sold,
          CASE 
            WHEN MAX(s.sold_at) IS NULL THEN 'Never'
            ELSE cast(julianday('now') - julianday(MAX(s.sold_at)) as integer) || ' days ago'
          END as days_since
        FROM products p
        LEFT JOIN sales s ON s.product_id = p.id
        GROUP BY p.id
        HAVING p.stock > 0 
        AND (last_sold = 'Never' OR last_sold < date('now', '-7 days'))
    """).fetchall()
    conn.close()
    
    filtered_dead = []
    for d in dead:
        c = d['category'].lower()
        n = d['name'].lower()
        if c not in festival_keywords and not any(k in n for k in festival_keywords):
            filtered_dead.append(dict(d))
            
    return filtered_dead

def get_high_potential_items():
    products = get_all_products()
    festivals = get_upcoming_festivals()
    festival_categories = [cat for f in festivals for cat in f['relevant_categories']]
    
    high_potential = []
    for p in products:
        recent_avg = get_moving_average_range(p['id'], 3, 0)
        prev_avg = get_moving_average_range(p['id'], 6, 3)
        
        reason = None
        if prev_avg > 0 and recent_avg >= prev_avg * 1.2:
            reason = f"Sales up {round(((recent_avg - prev_avg) / prev_avg) * 100)}% recently"
        elif p['category'] in festival_categories:
            matching = [f['name'] for f in festivals if p['category'] in f['relevant_categories']]
            reason = f"Demand likely due to {', '.join(matching)}"
        
        if reason:
            high_potential.append({ "name": p['name'], "category": p['category'], "reason": reason })
            
    return high_potential

def get_total_sales_range(product_id, days):
    conn = get_connection()
    result = conn.execute(f"SELECT COALESCE(SUM(quantity), 0) as total FROM sales WHERE product_id = ? AND sold_at >= date('now', '-{days} days')", (product_id,)).fetchone()
    conn.close()
    return result['total'] if result and result['total'] else 0

def get_prioritized_alerts():
    products = get_all_products()
    festivals = get_upcoming_festivals()
    festival_keywords = [cat.lower() for f in festivals if f['days_away'] <= 7 for cat in f['relevant_categories']]
    
    alerts = []
    
    for p in products:
        pid = p['id']
        name = p['name']
        stock = p['stock']
        category = p['category'].lower()
        
        last_7_days_sales = get_total_sales_range(pid, 7)
        avg_daily_sales = last_7_days_sales / 7.0
        
        avg_last_3_days = get_moving_average_range(pid, 3, 0)
        avg_prev_3_days = get_moving_average_range(pid, 6, 3)
        
        stock_urgency = 0
        demand_trend_score = 0
        festival_boost_score = 0
        
        product_alerts = []
        
        min_threshold = max(5, avg_daily_sales * 2)
        if stock < min_threshold:
            stock_urgency = 50
            product_alerts.append({
                "type": "Low Stock",
                "message": f"Restock {name} - only {stock} units left",
                "score_boost": stock_urgency
            })
            
        days_left = (stock / avg_daily_sales) if avg_daily_sales > 0 else float('inf')
        if days_left < 3:
            stock_urgency = 100
            product_alerts.append({
                "type": "Critical Stock",
                "message": f"{name} will run out in {int(days_left)} days",
                "score_boost": stock_urgency
            })
            
        if avg_prev_3_days > 0:
            percentage_increase = ((avg_last_3_days - avg_prev_3_days) / avg_prev_3_days) * 100
            if percentage_increase > 20:
                demand_trend_score = 40
                product_alerts.append({
                    "type": "High Demand",
                    "message": f"{name} demand is increasing",
                    "score_boost": demand_trend_score
                })
                
        is_festival = category in festival_keywords or any(k in name.lower() for k in festival_keywords)
        
        if last_7_days_sales == 0 and stock > 0 and not is_festival:
            product_alerts.append({
                "type": "Dead Stock",
                "message": f"{name} not selling for 7 days - consider discount",
                "score_boost": 30
            })
            
        if is_festival:
            festival_boost_score = 30
            
        for a in product_alerts:
            total_score = a['score_boost'] + (demand_trend_score if a['type'] != 'High Demand' else 0) + festival_boost_score
            alerts.append({
                "product_name": name,
                "message": a['message'],
                "priority_score": total_score,
                "type": a['type']
            })
            
    alerts.sort(key=lambda x: x['priority_score'], reverse=True)
    
    final_alerts = []
    seen = set()
    for a in alerts:
        identifier = f"{a['product_name']}-{a['type']}"
        if identifier not in seen:
            seen.add(identifier)
            final_alerts.append(a)
        if len(final_alerts) >= 5:
            break
            
    return final_alerts

def get_home_festival_insights():
    festivals = get_upcoming_festivals()
    nearest = [f for f in festivals if f['days_away'] <= 7]
    if not nearest:
        return { "upcoming": "No major festivals in the next 7 days.", "suggestion": "Maintain standard inventory levels." }
    target_festival = nearest[0]
    days_away = target_festival['days_away']
    name = target_festival['name']
    categories = target_festival['relevant_categories']
    
    products_in_cats = [p['name'] for p in get_all_products() if p['category'].lower() in [c.lower() for c in categories]]
    if products_in_cats:
        cat_str = ", ".join(products_in_cats[:2]) + (" etc." if len(products_in_cats) > 2 else "")
    else:
        cat_str = categories[0] if categories else 'relevant items'
        
    return { "upcoming": f"{name} in {days_away} days", "suggestion": f"Demand for {cat_str} expected to increase due to {name}" }

def get_home_mini_insights():
    conn = get_connection()
    products = get_all_products()
    top_row = conn.execute("SELECT p.name, COALESCE(SUM(s.quantity), 0) as total_qty FROM products p LEFT JOIN sales s ON p.id = s.product_id GROUP BY p.id ORDER BY total_qty DESC LIMIT 1").fetchone()
    top_selling = top_row['name'] if top_row and top_row['total_qty'] > 0 else "No sales yet"
    least_row = conn.execute("SELECT p.name, COALESCE(SUM(s.quantity), 0) as total_qty FROM products p LEFT JOIN sales s ON p.id = s.product_id WHERE p.stock > 5 GROUP BY p.id ORDER BY total_qty ASC LIMIT 1").fetchone()
    least_selling = least_row['name'] if least_row else "N/A"
    conn.close()
    
    festivals = get_upcoming_festivals()
    festival_keywords = [cat.lower() for f in festivals if f['days_away'] <= 7 for cat in f['relevant_categories']]
    high_potential = "None identified"
    for p in products:
        recent_avg = get_moving_average_range(p['id'], 3, 0)
        prev_avg = get_moving_average_range(p['id'], 6, 3)
        cat = p['category'].lower()
        if (prev_avg > 0 and recent_avg > prev_avg * 1.2) or (cat in festival_keywords):
            high_potential = f"{p['name']} may see increased demand"
            break
            
    return { "top_selling": top_selling, "least_selling": least_selling, "high_potential": high_potential }

def get_home_quick_summary():
    conn = get_connection()
    today_sales = conn.execute("SELECT COALESCE(SUM(total_price), 0) as s FROM sales WHERE sold_at >= date('now', 'start of day')").fetchone()['s']
    
    query = """
        SELECT 
            p.stock,
            COALESCE(SUM(s.quantity), 0) as past_7d_sales
        FROM products p
        LEFT JOIN sales s ON p.id = s.product_id AND s.sold_at >= date('now', '-7 days')
        GROUP BY p.id
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    
    total_products = len(rows)
    low_stock_count = 0
    out_of_stock_count = 0
    
    for r in rows:
        avg_daily_sales = r['past_7d_sales'] / 7.0
        threshold = max(5, avg_daily_sales * 2)
        if r['stock'] == 0:
            out_of_stock_count += 1
        elif r['stock'] < threshold:
            low_stock_count += 1
            
    return {
        "today_sales": today_sales or 0,
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "total_products": total_products
    }
