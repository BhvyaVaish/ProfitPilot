from services.ai_engine import get_restock_suggestions, get_dead_stock, get_prioritized_alerts, get_home_mini_insights
from services.festival_service import get_upcoming_festivals, match_festivals_to_inventory
from services.ai_engine import get_moving_average_range, get_total_sales_range
from models import get_all_products, get_user_profile
from database import get_connection

def get_top_products(limit=3, user_id='demo'):
    conn = get_connection()
    top = conn.execute("""
        SELECT p.name, SUM(s.quantity) as total_qty
        FROM sales s
        JOIN products p ON s.product_id = p.id
        WHERE p.user_id = ? AND s.sold_at >= date('now', '-30 days')
        GROUP BY p.id
        ORDER BY total_qty DESC
        LIMIT ?
    """, (user_id, limit)).fetchall()
    conn.close()
    return [dict(t) for t in top]

def get_today_sales(user_id='demo'):
    conn = get_connection()
    stats = conn.execute("""
        SELECT COALESCE(SUM(total_price), 0) as revenue, COALESCE(COUNT(DISTINCT id), 0) as transactions
        FROM sales
        WHERE user_id = ? AND sold_at >= date('now', 'start of day')
    """, (user_id,)).fetchone()
    conn.close()
    return dict(stats)

def _build_response(title, bullets, closing=None):
    """Build a structured response."""
    lines = [title, ""]
    for b in bullets:
        lines.append(f"  {b}")
    if closing:
        lines.append("")
        lines.append(closing)
    return "\n".join(lines)

def get_response(message: str, user_id='demo') -> str:
    msg = message.lower().strip()
    words = set(msg.replace('?', '').replace('!', '').replace('.', '').split())

    # Get user profile for personalized responses
    profile = get_user_profile(user_id) if user_id != 'demo' else None
    biz_context = ""
    if profile and profile.get('business_name'):
        biz_context = f" for {profile['business_name']}"

    # -- GREETING -------------------------------------------------------
    if words & {'hi', 'hello', 'hey', 'help', 'start'} or 'what can you do' in msg:
        greeting_name = ""
        if profile and profile.get('full_name'):
            greeting_name = f", {profile['full_name'].split()[0]}"
        return (
            f"Hi{greeting_name}! I'm ProfitPilot -- your business decision assistant.\n\n"
            "Here's what I can help with:\n"
            "  What should I restock?\n"
            "  What sells the most?\n"
            "  What is not selling?\n"
            "  What will sell more soon?\n"
            "  Any upcoming festival demand?\n"
            "  What should I do today?\n"
            "  Show today's sales\n"
            "  How is my profit?\n"
            "  Tell me about GST\n\n"
            "Just ask me anything about your business!"
        )

    # -- TODAY / DO TODAY (SMART SUMMARY) --------------------------------
    if any(w in msg for w in ['what should i do', 'today', 'right now', 'summary', 'daily']):
        alerts = get_prioritized_alerts(user_id)
        insights = get_home_mini_insights(user_id)
        stats = get_today_sales(user_id)

        lines = []
        if alerts:
            for a in alerts[:3]:
                lines.append(f"{a['message']} [{a['type']}]")
        else:
            lines.append("No critical actions required right now.")

        bullets = lines
        top = insights.get('top_selling', 'N/A')
        high = insights.get('high_potential', 'None identified')

        return _build_response(
            f"Here's your business situation today{biz_context} (Sales so far: Rs.{stats['revenue']:.2f}):",
            bullets,
            f"Best seller: {top}\nHigh potential: {high}"
        )

    # -- PROFIT / MARGIN ------------------------------------------------
    if any(w in msg for w in ['profit', 'margin', 'earning', 'how much am i making', 'kitna kama']):
        conn = get_connection()
        total_rev = conn.execute("SELECT COALESCE(SUM(total_price), 0) as r FROM sales WHERE user_id = ?", (user_id,)).fetchone()['r']
        week_rev = conn.execute("SELECT COALESCE(SUM(total_price), 0) as r FROM sales WHERE user_id = ? AND sold_at >= date('now', '-7 days')", (user_id,)).fetchone()['r']
        conn.close()

        est_profit = total_rev * 0.30  # 30% margin assumption
        week_profit = week_rev * 0.30

        tips = "Tip: Declare all business expenses (rent, electricity, salary) to reduce your taxable income. Visit the Tax Estimator page for detailed analysis."
        if profile:
            if profile.get('payment_mode') == 'digital':
                tips += "\nSince you use mostly digital payments, you may qualify for the lower 6% presumptive tax rate under Section 44AD."
            if profile.get('msme_category') == 'micro':
                tips += "\nAs a Micro enterprise, explore MSME registration benefits like priority lending and delayed payment protection."

        return (
            f"Here's your profit overview{biz_context}:\n\n"
            f"  Total Revenue (all time): Rs.{total_rev:,.2f}\n"
            f"  Estimated Profit (30% margin): Rs.{est_profit:,.2f}\n"
            f"  This week's revenue: Rs.{week_rev:,.2f}\n"
            f"  This week's est. profit: Rs.{week_profit:,.2f}\n\n"
            f"{tips}"
        )

    # -- GST / TAX QUERY ------------------------------------------------
    if any(w in msg for w in ['gst', 'tax', 'itr', 'income tax', 'section 44', 'filing']):
        conn = get_connection()
        total_rev = conn.execute("SELECT COALESCE(SUM(total_price), 0) as r FROM sales WHERE user_id = ?", (user_id,)).fetchone()['r']
        conn.close()

        annual_est = total_rev * (365 / max(1, 30))  # rough projection

        lines = [
            f"Based on your current sales (Rs.{total_rev:,.2f}), here's a quick tax snapshot:",
            "",
            f"  Projected annual turnover: Rs.{annual_est:,.0f}",
        ]

        if annual_est <= 15000000:
            lines.append("  You may be eligible for the GST Composition Scheme (1% tax on turnover)")
        if annual_est <= 30000000:
            lines.append("  Section 44AD: You can declare 6-8% of turnover as profit (no detailed books needed)")

        # Personalized tips based on profile
        if profile:
            if profile.get('business_type') == 'services':
                lines.append("  For service businesses, Section 44ADA allows 50% presumptive profit")
            if profile.get('payment_mode') == 'digital':
                lines.append("  Digital payments: You qualify for the 6% rate under Section 44AD (vs 8% for cash)")

        lines.append("")
        lines.append("Visit the Tax Estimator page for a full breakdown with GST, Income Tax slabs, and tax-saving tips.")

        return "\n".join(lines)

    # -- RESTOCK --------------------------------------------------------
    if any(w in msg for w in ['restock', 'order', 'low stock', 'running out', 'what to buy', 'purchase', 'replenish', 'need to buy', 'stock bhariye']):
        suggestions = get_restock_suggestions(user_id)
        if not suggestions:
            return "All your products are sufficiently stocked. No restocking needed right now!"
        top = suggestions[:5]
        bullets = []
        for s in top:
            bullets.append(
                f"{s['name']} -- Add at least {s['suggested_restock']} units "
                f"(Current stock: {s['current_stock']}, Forecast demand: {s['predicted_demand']})"
            )
        return _build_response(
            "You should restock these items:",
            bullets,
            "Tip: These quantities include a 15% safety buffer based on your sales trend."
        )

    # -- TOP SELLING ----------------------------------------------------
    if any(w in msg for w in ['top', 'best', 'most selling', 'popular', 'trending', 'sells most', 'what sells', 'highest']):
        top = get_top_products(limit=5, user_id=user_id)
        if not top:
            return "No sales data yet. Start billing to track top products."
        bullets = [f"{p['name']} -- {p['total_qty']} units sold this month" for p in top]
        return _build_response(
            "Your top selling products (last 30 days):",
            bullets,
            "Consider keeping these items well-stocked at all times."
        )

    # -- DEAD STOCK -----------------------------------------------------
    if any(w in msg for w in ['dead', 'slow', 'not selling', 'stagnant', 'stuck', 'no sales', 'waste', 'idle']):
        dead = get_dead_stock(user_id)
        if not dead:
            return "Great news! No dead stock detected. All products have had recent sales."
        bullets = [
            f"{d['name']} -- {d['stock']} units sitting idle, last sold: {d['days_since']}"
            for d in dead[:5]
        ]
        return _build_response(
            "These items haven't sold in 7+ days:",
            bullets,
            "Action: Consider offering discounts, bundling, or running a promotion on these."
        )

    # -- DEMAND / HIGH POTENTIAL ----------------------------------------
    if any(w in msg for w in ['demand', 'potential', 'will sell', 'grow', 'increase', 'predict', 'forecast', 'future']):
        result = match_festivals_to_inventory(user_id)
        suggestions = result['suggestions']
        festivals = result['festivals']

        # Also check sales trend
        products = get_all_products(user_id)
        high_potential = []
        for p in products:
            recent_avg = get_moving_average_range(p['id'], 3, 0)
            prev_avg   = get_moving_average_range(p['id'], 6, 3)
            if prev_avg > 0 and recent_avg >= prev_avg * 1.2:
                pct = round(((recent_avg - prev_avg) / prev_avg) * 100)
                high_potential.append(f"{p['name']} -- Sales up {pct}% in the last 3 days")

        bullets = high_potential[:5]

        # Add festival-based suggestions
        restock_items = [s for s in suggestions if s['type'] == 'restock'][:3]
        opportunity_items = [s for s in suggestions if s['type'] == 'opportunity'][:3]

        for s in restock_items:
            bullets.append(f"{s['product']} -- {s['festival']} in {s['days_away']} day(s), stock up! (Current: {s['current_stock']})")
        for s in opportunity_items:
            bullets.append(f"NEW: {s['item']} -- {s['festival']} demand. Consider adding to inventory.")

        if not bullets:
            return "No significant demand spikes detected right now. Check back later or closer to a festival."

        closing = "Stock up on these products in advance to maximize your profits."
        if festivals:
            closing += f"\nNearest festival: {festivals[0]['name']} in {festivals[0]['days_away']} day(s)."

        return _build_response(
            "These items show high demand potential:",
            bullets,
            closing
        )

    # -- FESTIVAL -------------------------------------------------------
    if any(w in msg for w in ['festival', 'holiday', 'event', 'occasion', 'upcoming', 'celebration', 'diwali', 'holi', 'eid', 'tyohar']):
        result = match_festivals_to_inventory(user_id)
        festivals = result['festivals']
        suggestions = result['suggestions']

        if not festivals:
            return "No major festivals detected in the coming 15 days. Inventory looks stable."

        bullets = []
        for f in festivals[:5]:
            cats = ', '.join(f['relevant_categories'][:3]) if f['relevant_categories'] else 'general items'
            demand = ', '.join(f.get('demand_items', [])[:3]) if f.get('demand_items') else ''
            line = f"{f['name']} in {f['days_away']} day(s) -- Stock up on: {cats}"
            if demand:
                line += f" (AI suggests: {demand})"
            bullets.append(line)

        # Add top smart suggestions
        if suggestions:
            bullets.append("")
            bullets.append("Smart Suggestions:")
            for s in suggestions[:5]:
                bullets.append(f"  {s['message']}")

        return _build_response(
            "Upcoming festivals that may affect your sales (next 15 days):",
            bullets,
            "Action: Review inventory for the listed categories and restock before the festival rush."
        )

    # -- SALES / REVENUE ------------------------------------------------
    if any(w in msg for w in ['sales', 'revenue', 'earnings', 'money', 'income', 'how much', 'bikri', 'kamai']):
        stats = get_today_sales(user_id)
        conn = get_connection()
        week_rev = conn.execute("SELECT COALESCE(SUM(total_price),0) as s FROM sales WHERE user_id = ? AND sold_at >= date('now', '-7 days')", (user_id,)).fetchone()['s']
        month_rev = conn.execute("SELECT COALESCE(SUM(total_price),0) as s FROM sales WHERE user_id = ? AND sold_at >= date('now', '-30 days')", (user_id,)).fetchone()['s']
        conn.close()
        return (
            f"Today's revenue{biz_context}: Rs.{stats['revenue']:.2f} from {stats['transactions']} individual items sold.\n\n"
            f"Revenue this week: Rs.{week_rev:.2f}\n"
            f"Revenue this month: Rs.{month_rev:.2f}\n\n"
            "Check the Dashboard for the full Revenue Velocity chart."
        )

    # -- STOCK / INVENTORY OVERVIEW -------------------------------------
    if any(w in msg for w in ['stock', 'inventory', 'products', 'items', 'catalog', 'how many', 'kitna maal']):
        products = get_all_products(user_id)
        conn = get_connection()
        rows = conn.execute("""
            SELECT p.id, p.stock,
                COALESCE(SUM(s.quantity), 0) as past_7d_sales
            FROM products p
            LEFT JOIN sales s ON p.id = s.product_id AND s.sold_at >= date('now', '-7 days')
            WHERE p.user_id = ?
            GROUP BY p.id
        """, (user_id,)).fetchall()
        conn.close()

        low = []
        out = []
        for r in rows:
            avg_daily = r['past_7d_sales'] / 7.0
            thresh = max(5, avg_daily * 2)
            if r['stock'] == 0:
                out.append(r['id'])
            elif r['stock'] < thresh:
                low.append(r['id'])

        return (
            f"Your inventory overview{biz_context}:\n\n"
            f"  Total products: {len(products)}\n"
            f"  Low stock items: {len(low)}\n"
            f"  Out of stock: {len(out)}\n\n"
            "Visit the Inventory page to manage your stock easily."
        )

    # -- SPECIFIC PRODUCT QUERY -----------------------------------------
    products = get_all_products(user_id)
    matched = [p for p in products if p['name'].lower() in msg]
    if matched:
        p = matched[0]
        pid = p['id']
        last_7 = get_total_sales_range(pid, 7)
        avg_daily = last_7 / 7.0
        thresh = max(5, avg_daily * 2)
        recent_avg = get_moving_average_range(pid, 3, 0)
        prev_avg = get_moving_average_range(pid, 6, 3)

        trend = "stable"
        if prev_avg > 0:
            pct = ((recent_avg - prev_avg) / prev_avg) * 100
            if pct > 20: trend = f"increasing (+{round(pct)}%)"
            elif pct < -20: trend = f"declining ({round(pct)}%)"

        if p['stock'] == 0:
            status = "Out of Stock"
        elif p['stock'] < thresh:
            status = f"Low ({p['stock']} units)"
        else:
            status = f"OK ({p['stock']} units)"

        return (
            f"Here's what I know about {p['name']}:\n\n"
            f"  Stock status: {status}\n"
            f"  Current price: Rs.{p['price']}\n"
            f"  Sales last 7 days: {last_7} units\n"
            f"  Demand trend: {trend}\n"
            f"  Estimated days left: {'Infinite' if avg_daily == 0 else round(p['stock'] / avg_daily)}"
        )

    # -- FALLBACK -------------------------------------------------------
    return (
        "I didn't quite understand that. Try asking:\n\n"
        "  \"What should I restock?\"\n"
        "  \"What sells the most?\"\n"
        "  \"What is not selling?\"\n"
        "  \"Any upcoming festival demand?\"\n"
        "  \"What should I do today?\"\n"
        "  \"Show me today's sales\"\n"
        "  \"How is my profit?\"\n"
        "  \"Tell me about GST\""
    )
