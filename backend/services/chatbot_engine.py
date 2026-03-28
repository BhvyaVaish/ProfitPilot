from services.ai_engine import get_restock_suggestions, get_dead_stock, get_prioritized_alerts, get_home_mini_insights
from services.festival_service import get_upcoming_festivals
from services.ai_engine import get_moving_average_range, get_total_sales_range
from models import get_all_products
from database import get_connection

def get_top_products(limit=3):
    conn = get_connection()
    top = conn.execute(f"""
        SELECT p.name, SUM(s.quantity) as total_qty
        FROM sales s
        JOIN products p ON s.product_id = p.id
        WHERE s.sold_at >= date('now', '-30 days')
        GROUP BY p.id
        ORDER BY total_qty DESC
        LIMIT {limit}
    """).fetchall()
    conn.close()
    return [dict(t) for t in top]

def get_today_sales():
    conn = get_connection()
    stats = conn.execute("""
        SELECT COALESCE(SUM(total_price), 0) as revenue, COALESCE(COUNT(DISTINCT id), 0) as transactions
        FROM sales
        WHERE sold_at >= date('now', 'start of day')
    """).fetchone()
    conn.close()
    return dict(stats)

def _build_response(title, bullets, closing=None):
    """Build a structured markdown-ish response."""
    lines = [title, ""]
    for b in bullets:
        lines.append(f"• {b}")
    if closing:
        lines.append("")
        lines.append(closing)
    return "\n".join(lines)

def get_response(message: str) -> str:
    msg = message.lower().strip()

    # ── GREETING ──────────────────────────────────────────────────────
    if any(w in msg for w in ['hi', 'hello', 'hey', 'help', 'what can you do', 'start']):
        return (
            "Hi! I'm ProfitPilot — your business decision assistant.\n\n"
            "Here's what I can help with:\n"
            "• What should I restock?\n"
            "• What sells the most?\n"
            "• What is not selling?\n"
            "• What will sell more soon?\n"
            "• Any upcoming festival demand?\n"
            "• What should I do today?\n"
            "• Show today's sales\n\n"
            "Just ask me anything about your business!"
        )

    # ── TODAY / DO TODAY (SMART SUMMARY) ──────────────────────────────
    if any(w in msg for w in ['what should i do', 'today', 'right now', 'summary', 'daily']):
        alerts = get_prioritized_alerts()
        insights = get_home_mini_insights()
        stats = get_today_sales()

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
            f"Here's your business situation today (Sales so far: ₹{stats['revenue']:.2f}):",
            bullets,
            f"🏆 Best seller: {top}\n🔥 High potential: {high}"
        )

    # ── RESTOCK ───────────────────────────────────────────────────────
    if any(w in msg for w in ['restock', 'order', 'low stock', 'running out', 'what to buy', 'purchase', 'replenish', 'need to buy']):
        suggestions = get_restock_suggestions()
        if not suggestions:
            return "✅ All your products are sufficiently stocked. No restocking needed right now!"
        top = suggestions[:5]
        bullets = []
        for s in top:
            bullets.append(
                f"{s['name']} — Add at least {s['suggested_restock']} units "
                f"(Current stock: {s['current_stock']}, Forecast demand: {s['predicted_demand']})"
            )
        return _build_response(
            "📦 You should restock these items:",
            bullets,
            "Tip: These quantities include a 15% safety buffer based on your sales trend."
        )

    # ── TOP SELLING ───────────────────────────────────────────────────
    if any(w in msg for w in ['top', 'best', 'most selling', 'popular', 'trending', 'sells most', 'what sells', 'highest']):
        top = get_top_products(limit=5)
        if not top:
            return "No sales data yet. Start billing to track top products."
        bullets = [f"{p['name']} — {p['total_qty']} units sold this month" for p in top]
        return _build_response(
            "🏆 Your top selling products (last 30 days):",
            bullets,
            "Consider keeping these items well-stocked at all times."
        )

    # ── DEAD STOCK ────────────────────────────────────────────────────
    if any(w in msg for w in ['dead', 'slow', 'not selling', 'stagnant', 'stuck', 'no sales', 'waste', 'idle']):
        dead = get_dead_stock()
        if not dead:
            return "✅ Great news! No dead stock detected. All products have had recent sales."
        bullets = [
            f"{d['name']} — {d['stock']} units sitting idle, last sold: {d['days_since']}"
            for d in dead[:5]
        ]
        return _build_response(
            "📉 These items haven't sold in 7+ days:",
            bullets,
            "Action: Consider offering discounts, bundling, or running a promotion on these."
        )

    # ── DEMAND / HIGH POTENTIAL ────────────────────────────────────────
    if any(w in msg for w in ['demand', 'potential', 'will sell', 'grow', 'increase', 'predict', 'forecast', 'future']):
        products = get_all_products()
        festivals = get_upcoming_festivals()
        festival_keywords = [cat.lower() for f in festivals if f['days_away'] <= 7 for cat in f['relevant_categories']]

        high_potential = []
        for p in products:
            recent_avg = get_moving_average_range(p['id'], 3, 0)
            prev_avg   = get_moving_average_range(p['id'], 6, 3)
            cat = p['category'].lower()
            name = p['name'].lower()

            reason = None
            if prev_avg > 0 and recent_avg >= prev_avg * 1.2:
                pct = round(((recent_avg - prev_avg) / prev_avg) * 100)
                reason = f"{p['name']} — Sales up {pct}% in the last 3 days"
            elif cat in festival_keywords or any(k in name for k in festival_keywords):
                matching = [f['name'] for f in festivals if cat in f['relevant_categories'] or any(k in name for k in [c.lower() for c in f['relevant_categories']])]
                reason = f"{p['name']} — Demand likely due to {', '.join(matching)}" if matching else f"{p['name']} — Festival-linked category"

            if reason:
                high_potential.append(reason)

        if not high_potential:
            return "No significant demand spikes detected right now. Check back later or closer to a festival."

        return _build_response(
            "🔥 These items show high demand potential:",
            high_potential[:5],
            "Stock up on these products in advance to maximize your profits."
        )

    # ── FESTIVAL ──────────────────────────────────────────────────────
    if any(w in msg for w in ['festival', 'holiday', 'event', 'occasion', 'upcoming', 'celebration', 'diwali', 'holi', 'eid']):
        festivals = get_upcoming_festivals()
        if not festivals:
            return "No major festivals detected in the coming 7 days. Inventory looks stable."

        near = [f for f in festivals if f['days_away'] <= 7]
        if not near:
            near = festivals[:2]

        bullets = []
        for f in near[:3]:
            cats = ', '.join(f['relevant_categories'][:3]) if f['relevant_categories'] else 'general items'
            bullets.append(f"{f['name']} in {f['days_away']} days → Stock up on: {cats}")

        return _build_response(
            "🗓️ Upcoming festivals that may affect your sales:",
            bullets,
            "Action: Review inventory for the listed categories and restock before the festival rush."
        )

    # ── SALES / REVENUE ───────────────────────────────────────────────
    if any(w in msg for w in ['sales', 'revenue', 'earnings', 'money', 'income', 'how much', 'profit']):
        stats = get_today_sales()
        conn = get_connection()
        week_rev = conn.execute("SELECT COALESCE(SUM(total_price),0) as s FROM sales WHERE sold_at >= date('now', '-7 days')").fetchone()['s']
        conn.close()
        return (
            f"💰 Today's revenue: ₹{stats['revenue']:.2f} from {stats['transactions']} individual items sold.\n\n"
            f"📅 Revenue this week: ₹{week_rev:.2f}\n\n"
            "Check the Dashboard for the full Revenue Velocity chart."
        )

    # ── STOCK / INVENTORY OVERVIEW ────────────────────────────────────
    if any(w in msg for w in ['stock', 'inventory', 'products', 'items', 'catalog', 'how many']):
        products = get_all_products()
        conn = get_connection()
        rows = conn.execute("""
            SELECT p.id, p.stock,
                COALESCE(SUM(s.quantity), 0) as past_7d_sales
            FROM products p
            LEFT JOIN sales s ON p.id = s.product_id AND s.sold_at >= date('now', '-7 days')
            GROUP BY p.id
        """).fetchall()
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
            f"📊 Your inventory overview:\n\n"
            f"• Total products: {len(products)}\n"
            f"• Low stock items: {len(low)}\n"
            f"• Out of stock: {len(out)}\n\n"
            "Visit the Inventory page to manage your stock easily."
        )

    # ── SPECIFIC PRODUCT QUERY ────────────────────────────────────────
    products = get_all_products()
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
            status = "❌ Out of Stock"
        elif p['stock'] < thresh:
            status = f"⚠️ Low ({p['stock']} units)"
        else:
            status = f"✅ OK ({p['stock']} units)"

        return (
            f"Here's what I know about **{p['name']}**:\n\n"
            f"• Stock status: {status}\n"
            f"• Current price: ₹{p['price']}\n"
            f"• Sales last 7 days: {last_7} units\n"
            f"• Demand trend: {trend}\n"
            f"• Estimated days left: {'∞' if avg_daily == 0 else round(p['stock'] / avg_daily)}"
        )

    # ── FALLBACK ──────────────────────────────────────────────────────
    return (
        "I didn't quite understand that. Try asking:\n\n"
        "• \"What should I restock?\"\n"
        "• \"What sells the most?\"\n"
        "• \"What is not selling?\"\n"
        "• \"Any upcoming festival demand?\"\n"
        "• \"What should I do today?\"\n"
        "• \"Show me today's sales\""
    )
