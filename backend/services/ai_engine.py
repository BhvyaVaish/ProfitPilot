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
    if days <= 0:
        conn.close()
        return 0.0
    result = conn.execute("""
        SELECT COALESCE(SUM(quantity), 0) / CAST(? AS REAL) as avg_daily
        FROM sales
        WHERE product_id = ?
        AND sold_at >= date('now', ? || ' days')
        AND sold_at < date('now', ? || ' days')
    """, (days, product_id, f'-{start_days_ago}', f'-{end_days_ago}')).fetchone()
    conn.close()
    return result['avg_daily'] if result and result['avg_daily'] is not None else 0.0

def get_total_sales_range(product_id, days):
    conn = get_connection()
    result = conn.execute(
        "SELECT COALESCE(SUM(quantity), 0) as total FROM sales WHERE product_id = ? AND sold_at >= date('now', ? || ' days')",
        (product_id, f'-{days}')
    ).fetchone()
    conn.close()
    return result['total'] if result and result['total'] else 0

def get_restock_suggestions(user_id='demo'):
    products = get_all_products(user_id)
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

def get_dead_stock(user_id='demo'):
    festivals = get_upcoming_festivals()
    festival_keywords = [cat.lower() for f in festivals if f['days_away'] <= 7 for cat in f['relevant_categories']]

    conn = get_connection()
    dead = conn.execute("""
        SELECT p.id, p.name, p.stock, p.category,
          COALESCE(strftime('%d-%m-%Y', MAX(s.sold_at)), 'Never') as last_sold_fmt,
          MAX(s.sold_at) as last_sold_raw,
          CASE
            WHEN MAX(s.sold_at) IS NULL THEN 'Never'
            ELSE cast(julianday('now') - julianday(MAX(s.sold_at)) as integer) || ' days ago'
          END as days_since
        FROM products p
        LEFT JOIN sales s ON s.product_id = p.id
        WHERE p.user_id = ?
        GROUP BY p.id
        HAVING p.stock > 0
        AND (MAX(s.sold_at) IS NULL OR MAX(s.sold_at) < date('now', '-7 days'))
    """, (user_id,)).fetchall()
    conn.close()

    filtered_dead = []
    for d in dead:
        c = d['category'].lower()
        n = d['name'].lower()
        if c not in festival_keywords and not any(k in n for k in festival_keywords):
            item = dict(d)
            item['last_sold'] = item.pop('last_sold_fmt')
            if 'last_sold_raw' in item:
                del item['last_sold_raw']
            filtered_dead.append(item)

    return filtered_dead

def get_high_potential_items(user_id='demo'):
    products = get_all_products(user_id)
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

def get_prioritized_alerts(user_id='demo'):
    products = get_all_products(user_id)
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

def get_home_festival_insights(user_id='demo'):
    from services.festival_service import match_festivals_to_inventory
    result = match_festivals_to_inventory(user_id)
    festivals = result['festivals']
    suggestions = result['suggestions']

    nearest = [f for f in festivals if f['days_away'] <= 15]
    if not nearest:
        return {
            "upcoming": "No major festivals in the next 15 days.",
            "suggestion": "Maintain standard inventory levels.",
            "festivals": [],
            "smart_suggestions": [],
        }

    target = nearest[0]
    restock_count = len([s for s in suggestions if s['type'] == 'restock'])
    opportunity_count = len([s for s in suggestions if s['type'] == 'opportunity'])

    suggestion_text = f"Demand for {', '.join(target['relevant_categories'][:3])} expected to increase due to {target['name']}."
    if restock_count > 0:
        suggestion_text += f" {restock_count} item(s) need restocking."
    if opportunity_count > 0:
        suggestion_text += f" {opportunity_count} new product opportunity(ies) identified."

    return {
        "upcoming": f"{target['name']} in {target['days_away']} day(s)",
        "suggestion": suggestion_text,
        "festivals": [{
            "name": f['name'],
            "date": f['date'],
            "days_away": f['days_away'],
            "categories": f['relevant_categories'][:5],
            "demand_items": f.get('demand_items', [])[:5],
            "source": f.get('source', 'unknown'),
        } for f in nearest[:5]],
        "smart_suggestions": suggestions[:10],
    }

def get_home_mini_insights(user_id='demo'):
    conn = get_connection()
    products = get_all_products(user_id)
    top_row = conn.execute("SELECT p.name, COALESCE(SUM(s.quantity), 0) as total_qty FROM products p LEFT JOIN sales s ON p.id = s.product_id WHERE p.user_id = ? GROUP BY p.id ORDER BY total_qty DESC LIMIT 1", (user_id,)).fetchone()
    top_selling = top_row['name'] if top_row and top_row['total_qty'] > 0 else "No sales yet"
    least_row = conn.execute("SELECT p.name, COALESCE(SUM(s.quantity), 0) as total_qty FROM products p LEFT JOIN sales s ON p.id = s.product_id WHERE p.user_id = ? AND p.stock > 5 GROUP BY p.id ORDER BY total_qty ASC LIMIT 1", (user_id,)).fetchone()
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

def get_home_quick_summary(user_id='demo'):
    conn = get_connection()
    today_sales = conn.execute("SELECT COALESCE(SUM(total_price), 0) as s FROM sales WHERE user_id = ? AND sold_at >= date('now', 'start of day')", (user_id,)).fetchone()['s']

    week_sales = conn.execute("SELECT COALESCE(SUM(total_price), 0) as s FROM sales WHERE user_id = ? AND sold_at >= date('now', '-7 days')", (user_id,)).fetchone()['s']
    prev_week_sales = conn.execute("SELECT COALESCE(SUM(total_price), 0) as s FROM sales WHERE user_id = ? AND sold_at >= date('now', '-14 days') AND sold_at < date('now', '-7 days')", (user_id,)).fetchone()['s']

    week_change = 0
    if prev_week_sales > 0:
        week_change = round(((week_sales - prev_week_sales) / prev_week_sales) * 100, 1)

    query = """
        SELECT
            p.stock,
            COALESCE(SUM(s.quantity), 0) as past_7d_sales
        FROM products p
        LEFT JOIN sales s ON p.id = s.product_id AND s.sold_at >= date('now', '-7 days')
        WHERE p.user_id = ?
        GROUP BY p.id
    """
    rows = conn.execute(query, (user_id,)).fetchall()
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
        "week_sales": week_sales or 0,
        "week_change": week_change,
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "total_products": total_products
    }

def get_business_health_score(user_id='demo'):
    """Composite 0-100 business health score."""
    products = get_all_products(user_id)
    if not products:
        return {"score": 0, "grade": "N/A", "factors": []}

    conn = get_connection()
    factors = []

    # Factor 1: Stock Health (0-30 pts)
    total = len(products)
    out_of_stock = sum(1 for p in products if p['stock'] == 0)
    stock_ratio = 1 - (out_of_stock / total) if total > 0 else 1
    stock_score = round(stock_ratio * 30)
    factors.append({"name": "Stock Availability", "score": stock_score, "max": 30})

    # Factor 2: Sales Momentum (0-25 pts)
    week_sales = conn.execute("SELECT COALESCE(SUM(total_price), 0) as s FROM sales WHERE user_id = ? AND sold_at >= date('now', '-7 days')", (user_id,)).fetchone()['s']
    prev_week = conn.execute("SELECT COALESCE(SUM(total_price), 0) as s FROM sales WHERE user_id = ? AND sold_at >= date('now', '-14 days') AND sold_at < date('now', '-7 days')", (user_id,)).fetchone()['s']
    if prev_week > 0:
        momentum = min(1.0, max(0, (week_sales / prev_week)))
    else:
        momentum = 0.5 if week_sales > 0 else 0
    momentum_score = round(momentum * 25)
    factors.append({"name": "Sales Momentum", "score": momentum_score, "max": 25})

    # Factor 3: Dead Stock Ratio (0-20 pts)
    dead = get_dead_stock(user_id)
    dead_ratio = 1 - (len(dead) / total) if total > 0 else 1
    dead_score = round(dead_ratio * 20)
    factors.append({"name": "Capital Efficiency", "score": dead_score, "max": 20})

    # Factor 4: Product Diversity (0-15 pts)
    categories = set(p['category'] for p in products)
    diversity = min(1.0, len(categories) / 8)
    diversity_score = round(diversity * 15)
    factors.append({"name": "Product Diversity", "score": diversity_score, "max": 15})

    # Factor 5: Revenue Consistency (0-10 pts)
    daily_sales = conn.execute("""
        SELECT COUNT(DISTINCT date(sold_at)) as active_days
        FROM sales WHERE user_id = ? AND sold_at >= date('now', '-7 days')
    """, (user_id,)).fetchone()['active_days']
    consistency = min(1.0, daily_sales / 7)
    consistency_score = round(consistency * 10)
    factors.append({"name": "Revenue Consistency", "score": consistency_score, "max": 10})

    conn.close()

    total_score = sum(f['score'] for f in factors)

    if total_score >= 80:
        grade = "Excellent"
    elif total_score >= 60:
        grade = "Good"
    elif total_score >= 40:
        grade = "Fair"
    else:
        grade = "Needs Attention"

    return {"score": total_score, "grade": grade, "factors": factors}
