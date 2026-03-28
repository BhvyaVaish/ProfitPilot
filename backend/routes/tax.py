from flask import Blueprint, jsonify
from database import get_connection
from config import CATEGORY_GST_RATES

tax_bp = Blueprint('tax_bp', __name__)

GST_RATE = 0.18
COST_RATIO = 0.70     # 70% assumed cost → 30% gross margin
INCOME_TAX_SLABS = [  # (threshold, rate)
    (250000, 0.0),
    (500000, 0.05),
    (1000000, 0.20),
    (float('inf'), 0.30)
]

def _calculate_income_tax(profit):
    """Indian income tax slab estimation on annual projected profit."""
    tax = 0
    prev = 0
    for limit, rate in INCOME_TAX_SLABS:
        if profit <= prev:
            break
        taxable = min(profit, limit) - prev
        tax += taxable * rate
        prev = limit
    return tax

@tax_bp.route('/api/tax/estimate', methods=['GET'])
def get_tax_estimate():
    try:
        conn = get_connection()

        # ── Core Revenue ──────────────────────────────────────────────
        revenue = conn.execute(
            "SELECT COALESCE(SUM(total_price), 0) as total FROM sales"
        ).fetchone()['total'] or 0

        week_revenue = conn.execute(
            "SELECT COALESCE(SUM(total_price), 0) as total FROM sales WHERE sold_at >= date('now', '-7 days')"
        ).fetchone()['total'] or 0

        prev_week_revenue = conn.execute(
            "SELECT COALESCE(SUM(total_price), 0) as total FROM sales WHERE sold_at >= date('now', '-14 days') AND sold_at < date('now', '-7 days')"
        ).fetchone()['total'] or 0

        # ── Profit ────────────────────────────────────────────────────
        estimated_cost = revenue * COST_RATIO
        net_profit = revenue - estimated_cost  # 30% margin

        # ── GST ───────────────────────────────────────────────────────
        category_revenue_rows = conn.execute("""
            SELECT p.category, SUM(s.total_price) as cat_revenue
            FROM sales s
            JOIN products p ON p.id = s.product_id
            GROUP BY p.category
        """).fetchall()

        gst_liability = 0
        for r in category_revenue_rows:
            cat = (r['category'] or 'general').lower()
            rate = CATEGORY_GST_RATES.get(cat, 0.18)
            gst_liability += (r['cat_revenue'] or 0) * rate

        # ── Income Tax (slab) ─────────────────────────────────────────
        # Project profit annually (multiply monthly avg by 12)
        sales_count_rows = conn.execute(
            "SELECT COUNT(DISTINCT date(sold_at)) as days FROM sales"
        ).fetchone()['days'] or 1
        avg_daily_profit = net_profit / sales_count_rows
        annual_projected_profit = avg_daily_profit * 365
        income_tax = _calculate_income_tax(annual_projected_profit)
        # Scale back down to current-period proportion
        income_tax_current = income_tax * (net_profit / annual_projected_profit) if annual_projected_profit > 0 else 0

        total_liability = gst_liability + income_tax_current

        # ── Product-wise Tax Impact ───────────────────────────────────
        all_product_tax_rows = conn.execute("""
            SELECT p.name, p.category,
                   COALESCE(SUM(s.total_price), 0) as product_revenue
            FROM products p
            JOIN sales s ON p.id = s.product_id
            GROUP BY p.id
        """).fetchall()

        product_tax_list = []
        for r in all_product_tax_rows:
            cat = (r['category'] or 'general').lower()
            rate = CATEGORY_GST_RATES.get(cat, 0.18)
            tax_contrib = (r['product_revenue'] or 0) * rate
            product_tax_list.append({
                "name": r['name'],
                "revenue": round(r['product_revenue'], 2),
                "tax_contribution": round(tax_contrib, 2)
            })
            
        product_tax_list.sort(key=lambda x: x['tax_contribution'], reverse=True)
        product_tax = product_tax_list[:5]

        # ── Profit Margin by Product ──────────────────────────────────
        product_margin_rows = conn.execute("""
            SELECT p.name, p.price,
                   COALESCE(SUM(s.quantity), 0) as total_qty,
                   COALESCE(SUM(s.total_price), 0) as total_revenue
            FROM products p
            LEFT JOIN sales s ON p.id = s.product_id
            GROUP BY p.id
            HAVING total_qty > 0
            ORDER BY total_revenue DESC
            LIMIT 5
        """).fetchall()

        product_margins = []
        for r in product_margin_rows:
            sell_price = r['price']
            cost_price = sell_price * COST_RATIO
            margin_pct = round(((sell_price - cost_price) / sell_price) * 100, 1)
            profit_per_unit = round(sell_price - cost_price, 2)
            product_margins.append({
                "name": r['name'],
                "sell_price": round(sell_price, 2),
                "cost_price": round(cost_price, 2),
                "margin_pct": margin_pct,
                "profit_per_unit": profit_per_unit,
                "total_revenue": round(r['total_revenue'], 2)
            })

        # ── Smart Alerts ──────────────────────────────────────────────
        alerts = []
        if prev_week_revenue > 0:
            gst_change_pct = ((week_revenue - prev_week_revenue) / prev_week_revenue) * 100
            if gst_change_pct > 15:
                alerts.append({
                    "type": "warning",
                    "message": f"GST liability increased {round(gst_change_pct)}% this week due to higher sales."
                })
            elif gst_change_pct < -15:
                alerts.append({
                    "type": "info",
                    "message": f"Revenue dropped {round(abs(gst_change_pct))}% this week — GST liability is lower."
                })

        if net_profit > 0 and revenue > 0:
            margin = (net_profit / revenue) * 100
            if margin < 20:
                alerts.append({
                    "type": "warning",
                    "message": f"Profit margin is {round(margin, 1)}% — below the 30% healthy threshold. Review pricing."
                })

        conn.close()

        return jsonify({
            "revenue": round(revenue, 2),
            "estimated_cost": round(estimated_cost, 2),
            "net_profit": round(net_profit, 2),
            "gst_liability": round(gst_liability, 2),
            "income_tax": round(income_tax_current, 2),
            "total_liability": round(total_liability, 2),
            "product_tax": product_tax,
            "product_margins": product_margins,
            "cashflow": {
                "revenue": round(revenue, 2),
                "expenses": round(estimated_cost, 2),
                "profit": round(net_profit, 2)
            },
            "alerts": alerts
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
