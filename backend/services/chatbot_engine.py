"""
chatbot_engine.py — Enhanced keyword-based chatbot with vast vocabulary coverage,
tax jargon explanations, and business intelligence.
"""
from services.ai_engine import get_restock_suggestions, get_dead_stock, get_prioritized_alerts, get_home_mini_insights, get_bulk_sales_metrics
from services.festival_service import get_upcoming_festivals, match_festivals_to_inventory
from models import get_all_products, get_user_profile
from database import get_connection

# ── KEYWORD SETS ────────────────────────────────────────────────────────
_GREET = {'hi','hello','hey','help','start','namaste','namaskar','hola','sup','yo','howdy','good morning','good evening','good afternoon','kaise ho','kya hal'}
_RESTOCK = {'restock','order','low stock','running out','buy','purchase','replenish','kharidna','stock bhariye','shortage','supply','out of stock','oos','need more','refill','procurement','khatam','kam stock','stock kam','stock nahi'}
_TOP_SELL = {'top','best','most selling','popular','trending','sells most','what sells','highest','bestseller','best seller','sabse zyada','top seller','hit product','fast moving','hot selling','star product','winner'}
_DEAD = {'dead','slow','not selling','stagnant','stuck','no sales','waste','idle','bikta nahi','nahi bikta','slow moving','non moving','zero sales','poor performance','dust collecting','shelf warmer'}
_DEMAND = {'demand','potential','will sell','grow','increase','predict','forecast','future','aage','coming demand','rising','growth','opportunity','scope','high potential','momentum','surge','spike','uptick'}
_FESTIVAL = {'festival','holiday','event','occasion','upcoming','celebration','diwali','holi','eid','tyohar','christmas','raksha bandhan','navratri','ganesh','onam','pongal','makar','lohri','baisakhi','durga puja','chhath'}
_SALES = {'sales','revenue','earnings','money','income','how much','bikri','kamai','turnover','total sales','aaj ki bikri','paisa','kitna kamaya','collection','gross','net','receipt'}
_STOCK = {'stock','inventory','products','items','catalog','how many','kitna maal','warehouse','godown','store','saman','product list','stock level','stock check','maal','available'}
_PROFIT = {'profit','margin','earning','how much am i making','kitna kama','munafa','fayda','net profit','gross profit','profit margin','kamai','return','roi','net income','bottom line'}
_TAX = {'gst','tax','itr','income tax','section 44','filing','return file','tax return','kar','gst return','taxation','tds','advance tax','presumptive','44ad','44ada','composition','composition scheme','gstr','gst filing'}
_TODAY = {'what should i do','today','right now','summary','daily','aaj','aaj ka','daily summary','morning brief','kya karu','action','to do','todo','kaam'}

# ── TAX JARGON EXPLAINER ──────────────────────────────────────────────
TAX_EXPLANATIONS = {
    'gst': "**GST (Goods & Services Tax)** is a single tax on the supply of goods and services in India. It replaced many indirect taxes like VAT, excise duty, and service tax.\n\n**In simple terms:** Whenever you sell something, a percentage of that sale goes to the government as GST. The rate depends on what you sell:\n  0% — Essential items (milk, grains, fresh produce)\n  5% — Daily-use items (grocery, packaged food)\n  12-18% — Standard goods (electronics, general items)\n\nYou collect GST from your customer and pay it to the government.",
    'cgst': "**CGST (Central GST)** is the portion of GST that goes to the Central Government.\n\n**Simple explanation:** When you charge 18% GST, half (9%) goes to the Central Govt as CGST and half (9%) goes to your State Govt as SGST. You don't pay extra — it's just split between two governments.",
    'sgst': "**SGST (State GST)** is the portion of GST that goes to your State Government.\n\n**Simple explanation:** It's exactly half of the total GST rate. If total GST is 18%, SGST = 9%. This money stays in your state for development.",
    'igst': "**IGST (Integrated GST)** applies when you sell goods to a customer in another state.\n\n**Simple explanation:** Instead of splitting into CGST+SGST, the full GST goes as IGST to the Central Govt, which then shares it with the receiving state. Rate is the same — only the label changes.",
    'section 44ad': "**Section 44AD** is a scheme for small businesses to file taxes easily without maintaining detailed books.\n\n**Simple explanation:** Instead of tracking every expense, the government assumes your profit is:\n  6% of income received digitally (UPI, bank transfer)\n  8% of cash income\n\nYou pay tax only on this assumed profit. Great for businesses with turnover under Rs.2-3 Crore.",
    '44ad': "**Section 44AD** lets small businesses declare profit as 6% (digital) or 8% (cash) of turnover without maintaining detailed books of accounts. If your actual profit margin is higher than 8%, this saves you from keeping complex records. Turnover limit: Rs.3 Crore (if 95%+ digital payments) or Rs.2 Crore otherwise.",
    '44ada': "**Section 44ADA** is like 44AD but for professionals (doctors, lawyers, CAs, architects, etc.).\n\n**Simple explanation:** Professionals can declare 50% of their gross receipts as profit. Turnover limit: Rs.75 Lakh (if 95%+ digital) or Rs.50 Lakh otherwise.",
    'composition scheme': "**GST Composition Scheme** is a simplified GST payment option for small businesses.\n\n**Simple explanation:** Instead of charging different GST rates on each product and filing monthly returns, you pay a flat 1% of your total turnover as tax and file quarterly returns.\n\n**But there are restrictions:**\n  You can't collect GST from customers\n  You can't claim Input Tax Credit\n  You can only sell within your state\n  Turnover must be under Rs.1.5 Crore",
    'itr': "**ITR (Income Tax Return)** is a form you file annually to report your income and taxes to the government.\n\n**Simple explanation:** Every year (usually by July 31), you tell the government how much you earned and how much tax you owe. If you've already paid more tax than needed (TDS), you get a refund!",
    'tds': "**TDS (Tax Deducted at Source)** means tax is deducted by the payer before paying you.\n\n**Simple explanation:** If a company pays you Rs.1,00,000 for services, they might deduct Rs.10,000 as TDS and pay you Rs.90,000. The Rs.10,000 goes directly to the government. You can claim this back when filing your ITR if your total tax is less.",
    'input tax credit': "**Input Tax Credit (ITC)** means you can reduce your GST liability by the GST you already paid on purchases.\n\n**Simple explanation:** If you buy goods worth Rs.1000 + Rs.180 GST = Rs.1180, and sell them for Rs.1500 + Rs.270 GST = Rs.1770, you only pay Rs.270 - Rs.180 = Rs.90 as GST to the government. The Rs.180 you already paid is your Input Tax Credit.",
    'itc': "**ITC (Input Tax Credit)** — The GST you paid when buying goods can be subtracted from the GST you collect when selling. This way you only pay the difference to the government, not the full amount. Think of it as a refund of tax already paid.",
    'rebate 87a': "**Section 87A Rebate** gives you a tax discount if your income is below a certain limit.\n\n**Simple explanation:**\n  New Regime: If taxable income is up to Rs.12 Lakh, you get a rebate of up to Rs.60,000 (effectively zero tax)\n  Old Regime: If taxable income is up to Rs.5 Lakh, you get a rebate of up to Rs.12,500\n\nThis means many small business owners pay ZERO income tax!",
    '87a': "**Section 87A** — If your annual taxable income is under Rs.12 Lakh (new regime) or Rs.5 Lakh (old regime), you get a rebate that can make your income tax effectively zero. Most small MSME owners qualify for this.",
    'new regime': "**New Tax Regime** has lower tax rates but NO deductions (no 80C, 80D, HRA, etc.).\n\n**Tax slabs (FY 2025-26):**\n  Up to Rs.4L — 0%\n  Rs.4-8L — 5%\n  Rs.8-12L — 10%\n  Rs.12-16L — 15%\n  Rs.16-20L — 20%\n  Rs.20-24L — 25%\n  Above Rs.24L — 30%\n\nPlus 87A rebate up to Rs.12L taxable income = zero tax for most MSMEs.",
    'old regime': "**Old Tax Regime** has higher rates but allows deductions under 80C (Rs.1.5L), 80D (health insurance), HRA, etc.\n\n**Use Old Regime if:** You have large deductions (LIC, PPF, home loan, health insurance). Otherwise, the New Regime is usually better for small businesses.",
    'msme': "**MSME** stands for Micro, Small and Medium Enterprises.\n\n**Classification:**\n  Micro — Investment up to Rs.1 Cr, Turnover up to Rs.5 Cr\n  Small — Investment up to Rs.10 Cr, Turnover up to Rs.50 Cr\n  Medium — Investment up to Rs.50 Cr, Turnover up to Rs.250 Cr\n\n**Benefits of MSME registration (Udyam):**\n  Priority bank lending at lower interest\n  Protection against delayed payments\n  Subsidy on patent/trademark registration\n  Government tender preference",
    'udyam': "**Udyam Registration** is the free online registration for MSMEs by the Government of India.\n\n**Simple explanation:** Register your business at udyamregistration.gov.in with your Aadhaar. It's free and gives you access to government schemes, easier bank loans, and protection against payment delays from big buyers.",
    'cess': "**Health & Education Cess** is an additional 4% charged on your income tax amount.\n\n**Simple explanation:** After calculating your income tax, add 4% extra. If your tax is Rs.10,000, you pay Rs.10,400 total. This extra money funds healthcare and education programs."
}

def _match_explain(msg):
    """Check if the user is asking for a tax/business term explanation."""
    explain_triggers = ['explain', 'what is', 'what are', 'meaning of', 'kya hai', 'kya hota', 'samjhao',
                       'tell me about', 'define', 'how does', 'how do', 'matlab', 'simple me', 'simply',
                       'easy language', 'asan bhasha', 'hindi me', 'help me understand']
    is_explain = any(t in msg for t in explain_triggers)
    
    if is_explain or True:  # Always check for direct term matches
        for key in TAX_EXPLANATIONS:
            if key in msg:
                return TAX_EXPLANATIONS[key]
    return None

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
    lines = [title, ""]
    for b in bullets:
        lines.append(f"  {b}")
    if closing:
        lines.append("")
        lines.append(closing)
    return "\n".join(lines)

def _match_any(msg, words_set):
    """Check if any keyword/phrase from words_set appears in msg."""
    for kw in words_set:
        if ' ' in kw:
            if kw in msg:
                return True
        else:
            if kw in msg.split():
                return True
    return False

def get_response(message: str, user_id='demo') -> str:
    msg = message.lower().strip()
    words = set(msg.replace('?', '').replace('!', '').replace('.', '').replace(',', '').split())

    profile = get_user_profile(user_id) if user_id != 'demo' else None
    biz_context = ""
    if profile and profile.get('business_name'):
        biz_context = f" for {profile['business_name']}"

    # -- EXPLAIN (check first — highest priority) -----------------------
    explanation = _match_explain(msg)
    if explanation:
        return explanation

    # -- GREETING -------------------------------------------------------
    if words & _GREET or 'what can you do' in msg or 'kya kar sakte' in msg:
        greeting_name = ""
        if profile and profile.get('full_name'):
            greeting_name = f", {profile['full_name'].split()[0]}"
        return (
            f"Hi{greeting_name}! I'm ProfitPilot -- your business decision assistant.\\n\\n"
            "Here's what I can help with:\\n"
            "  What should I restock?\\n"
            "  What sells the most?\\n"
            "  What is not selling?\\n"
            "  What will sell more soon?\\n"
            "  Any upcoming festival demand?\\n"
            "  What should I do today?\\n"
            "  Show today's sales\\n"
            "  How is my profit?\\n"
            "  Tell me about GST\\n"
            "  What is Section 44AD?\\n"
            "  Explain Composition Scheme\\n\\n"
            "Just ask me anything about your business!"
        )

    # -- TODAY / DO TODAY ------------------------------------------------
    if _match_any(msg, _TODAY):
        alerts = get_prioritized_alerts(user_id)
        insights = get_home_mini_insights(user_id)
        stats = get_today_sales(user_id)

        lines = []
        if alerts:
            for a in alerts[:3]:
                lines.append(f"{a['message']} [{a['type']}]")
        else:
            lines.append("No critical actions required right now.")

        top = insights.get('top_selling', 'N/A')
        high = insights.get('high_potential', 'None identified')

        return _build_response(
            f"Here's your business situation today{biz_context} (Sales so far: Rs.{stats['revenue']:.2f}):",
            lines,
            f"Best seller: {top}\\nHigh potential: {high}"
        )

    # -- PROFIT / MARGIN ------------------------------------------------
    if _match_any(msg, _PROFIT):
        conn = get_connection()
        total_rev = conn.execute("SELECT COALESCE(SUM(total_price), 0) as r FROM sales WHERE user_id = ?", (user_id,)).fetchone()['r']
        week_rev = conn.execute("SELECT COALESCE(SUM(total_price), 0) as r FROM sales WHERE user_id = ? AND sold_at >= date('now', '-7 days')", (user_id,)).fetchone()['r']
        conn.close()

        est_profit = total_rev * 0.30
        week_profit = week_rev * 0.30

        tips = "Tip: Declare all business expenses (rent, electricity, salary) to reduce your taxable income. Visit the Tax Estimator page for detailed analysis."
        if profile:
            if profile.get('payment_mode') == 'digital':
                tips += "\\nSince you use mostly digital payments, you may qualify for the lower 6% presumptive tax rate under Section 44AD."
            if profile.get('msme_category') == 'micro':
                tips += "\\nAs a Micro enterprise, explore MSME registration benefits like priority lending and delayed payment protection."

        return (
            f"Here's your profit overview{biz_context}:\\n\\n"
            f"  Total Revenue (all time): Rs.{total_rev:,.2f}\\n"
            f"  Estimated Profit (30% margin): Rs.{est_profit:,.2f}\\n"
            f"  This week's revenue: Rs.{week_rev:,.2f}\\n"
            f"  This week's est. profit: Rs.{week_profit:,.2f}\\n\\n"
            f"{tips}"
        )

    # -- GST / TAX QUERY ------------------------------------------------
    if _match_any(msg, _TAX):
        conn = get_connection()
        total_rev = conn.execute("SELECT COALESCE(SUM(total_price), 0) as r FROM sales WHERE user_id = ?", (user_id,)).fetchone()['r']
        conn.close()

        annual_est = total_rev * (365 / max(1, 30))

        lines = [
            f"Based on your current sales (Rs.{total_rev:,.2f}), here's a quick tax snapshot:",
            "",
            f"  Projected annual turnover: Rs.{annual_est:,.0f}",
        ]

        if annual_est <= 15000000:
            lines.append("  You may be eligible for the GST Composition Scheme (1% tax on turnover)")
        if annual_est <= 30000000:
            lines.append("  Section 44AD: You can declare 6-8% of turnover as profit (no detailed books needed)")

        if profile:
            if profile.get('business_type') == 'services':
                lines.append("  For service businesses, Section 44ADA allows 50% presumptive profit")
            if profile.get('payment_mode') == 'digital':
                lines.append("  Digital payments: You qualify for the 6% rate under Section 44AD (vs 8% for cash)")

        lines.append("")
        lines.append("Visit the Tax Estimator page for a full breakdown. Ask me 'What is GST?' or 'Explain Section 44AD' for simple explanations.")

        return "\n".join(lines)

    # -- RESTOCK --------------------------------------------------------
    if _match_any(msg, _RESTOCK):
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
    if _match_any(msg, _TOP_SELL):
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
    if _match_any(msg, _DEAD):
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
    if _match_any(msg, _DEMAND):
        result = match_festivals_to_inventory(user_id)
        suggestions = result['suggestions']
        festivals = result['festivals']

        products = get_all_products(user_id)
        metrics = get_bulk_sales_metrics(user_id)
        high_potential = []
        for p in products:
            pid = p['id']
            p_metrics = metrics.get(pid, {'avg_last_3': 0, 'avg_prev_3': 0})
            recent_avg = p_metrics['avg_last_3']
            prev_avg = p_metrics['avg_prev_3']
            if prev_avg > 0 and recent_avg >= prev_avg * 1.2:
                pct = round(((recent_avg - prev_avg) / prev_avg) * 100)
                high_potential.append(f"{p['name']} -- Sales up {pct}% in the last 3 days")

        bullets = high_potential[:5]

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
            closing += f"\\nNearest festival: {festivals[0]['name']} in {festivals[0]['days_away']} day(s)."

        return _build_response("These items show high demand potential:", bullets, closing)

    # -- FESTIVAL -------------------------------------------------------
    if _match_any(msg, _FESTIVAL):
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
    if _match_any(msg, _SALES):
        stats = get_today_sales(user_id)
        conn = get_connection()
        week_rev = conn.execute("SELECT COALESCE(SUM(total_price),0) as s FROM sales WHERE user_id = ? AND sold_at >= date('now', '-7 days')", (user_id,)).fetchone()['s']
        month_rev = conn.execute("SELECT COALESCE(SUM(total_price),0) as s FROM sales WHERE user_id = ? AND sold_at >= date('now', '-30 days')", (user_id,)).fetchone()['s']
        conn.close()
        return (
            f"Today's revenue{biz_context}: Rs.{stats['revenue']:.2f} from {stats['transactions']} individual items sold.\\n\\n"
            f"Revenue this week: Rs.{week_rev:.2f}\\n"
            f"Revenue this month: Rs.{month_rev:.2f}\\n\\n"
            "Check the Dashboard for the full Revenue Velocity chart."
        )

    # -- STOCK / INVENTORY OVERVIEW -------------------------------------
    if _match_any(msg, _STOCK):
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
            avg_daily = float(r['past_7d_sales']) / 7.0
            thresh = max(5, avg_daily * 2)
            if r['stock'] == 0:
                out.append(r['id'])
            elif r['stock'] < thresh:
                low.append(r['id'])

        return (
            f"Your inventory overview{biz_context}:\\n\\n"
            f"  Total products: {len(products)}\\n"
            f"  Low stock items: {len(low)}\\n"
            f"  Out of stock: {len(out)}\\n\\n"
            "Visit the Inventory page to manage your stock easily."
        )

    # -- SPECIFIC PRODUCT QUERY -----------------------------------------
    products = get_all_products(user_id)
    matched = [p for p in products if p['name'].lower() in msg]
    if matched:
        p = matched[0]
        pid = p['id']
        metrics = get_bulk_sales_metrics(user_id)
        p_metrics = metrics.get(pid, {'last_7_days_sales': 0, 'avg_last_7': 0, 'avg_last_3': 0, 'avg_prev_3': 0})
        
        last_7 = p_metrics['last_7_days_sales']
        avg_daily = p_metrics['avg_last_7']
        thresh = max(5, avg_daily * 2)
        recent_avg = p_metrics['avg_last_3']
        prev_avg = p_metrics['avg_prev_3']

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
            f"Here's what I know about {p['name']}:\\n\\n"
            f"  Stock status: {status}\\n"
            f"  Current price: Rs.{p['price']}\\n"
            f"  Sales last 7 days: {last_7} units\\n"
            f"  Demand trend: {trend}\\n"
            f"  Estimated days left: {'Infinite' if avg_daily == 0 else round(p['stock'] / avg_daily)}"
        )

    # -- THANKS ---------------------------------------------------------
    if words & {'thanks','thank','shukriya','dhanyawad','dhanyavaad','thankyou','appreciated'}:
        return "You're welcome! Let me know if you need anything else. I'm always here to help your business grow."

    # -- FALLBACK -------------------------------------------------------
    return (
        "I didn't quite understand that. Here are some things I can help with:\\n\\n"
        "  \"What should I restock?\"\\n"
        "  \"What sells the most?\"\\n"
        "  \"What is not selling?\"\\n"
        "  \"Any upcoming festival demand?\"\\n"
        "  \"What should I do today?\"\\n"
        "  \"Show me today's sales\"\\n"
        "  \"How is my profit?\"\\n"
        "  \"Tell me about GST\"\\n"
        "  \"What is Section 44AD?\"\\n"
        "  \"Explain Composition Scheme\"\\n"
        "  \"What is Input Tax Credit?\""
    )
