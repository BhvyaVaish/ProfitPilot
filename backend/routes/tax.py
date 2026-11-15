"""
tax.py — Tax estimation & GST calculation routes.

Fully migrated to Firestore. No SQL.
"""

from flask import Blueprint, jsonify, g
import firestore_db
from config import (
    CATEGORY_GST_RATES, COST_RATIO,
    INCOME_TAX_NEW_REGIME, INCOME_TAX_OLD_REGIME,
    SEC_87A_INCOME_LIMIT_NEW, SEC_87A_REBATE_NEW,
    SEC_87A_INCOME_LIMIT_OLD, SEC_87A_REBATE_OLD,
    SEC_44AD_TURNOVER_LIMIT, SEC_44AD_DIGITAL_TURNOVER_LIMIT,
    SEC_44AD_DIGITAL_RATE, SEC_44AD_CASH_RATE,
    COMPOSITION_TURNOVER_LIMIT, COMPOSITION_TAX_RATE,
)
from auth_middleware import optional_auth

tax_bp = Blueprint('tax_bp', __name__)


def _calculate_income_tax(profit, slabs):
    """Calculate slab-based income tax."""
    tax = 0
    prev = 0
    for limit, rate in slabs:
        if profit <= prev:
            break
        taxable = min(profit, limit) - prev
        tax += taxable * rate
        prev = limit
    return tax


def _apply_rebate_87a(tax, taxable_income, limit, max_rebate):
    """Apply Section 87A rebate if eligible."""
    if taxable_income <= limit:
        return max(0, tax - max_rebate)
    return tax


@tax_bp.route('/api/tax/estimate', methods=['GET'])
@optional_auth
def get_tax_estimate():
    try:
        user_id = g.user_id

        # Get user profile for personalized suggestions
        profile = firestore_db.get_user_profile(user_id) if user_id != 'demo' else None

        # -- Core Revenue & Sales Days -------------------------------------
        rev_all = firestore_db.get_revenue_all_time(user_id)
        revenue = float(rev_all['total_revenue'] or 0)
        sales_days = int(rev_all['active_sales_days'] or 1)
        category_revenue = rev_all['category_revenue']

        rev_summary = firestore_db.get_revenue_summary(user_id)
        week_revenue = float(rev_summary['week'] or 0)
        prev_week_revenue = float(rev_summary['prev_week'] or 0)

        avg_daily_revenue = revenue / max(1, sales_days)
        annual_projected_revenue = avg_daily_revenue * 365

        # -- Profit --------------------------------------------------------
        estimated_cost = revenue * COST_RATIO
        net_profit = revenue - estimated_cost  # 30% margin
        annual_projected_profit = (net_profit / sales_days) * 365 if sales_days > 0 else 0

        # -- GST (Category-wise Computation) -------------------------------
        gst_liability = 0.0
        gst_breakdown = []
        for cat, cat_rev in category_revenue.items():
            cat_clean = (cat or 'general').lower()
            rate = CATEGORY_GST_RATES.get(cat_clean, 0.18)
            cat_gst = cat_rev * rate
            gst_liability += cat_gst
            if cat_gst > 0:
                gst_breakdown.append({
                    "category": cat_clean,
                    "revenue": round(cat_rev, 2),
                    "rate": rate,
                    "rate_pct": f"{int(rate * 100)}%",
                    "gst": round(cat_gst, 2)
                })
        gst_breakdown.sort(key=lambda x: x['gst'], reverse=True)

        # -- Income Tax (New Regime - FY 2025-26) --------------------------
        income_tax_new_full = _calculate_income_tax(annual_projected_profit, INCOME_TAX_NEW_REGIME)
        income_tax_new_after_rebate = _apply_rebate_87a(
            income_tax_new_full, annual_projected_profit,
            SEC_87A_INCOME_LIMIT_NEW, SEC_87A_REBATE_NEW
        )
        cess_new = income_tax_new_after_rebate * 0.04
        income_tax_new_total = income_tax_new_after_rebate + cess_new

        if annual_projected_profit > 0:
            scale_factor = net_profit / annual_projected_profit
        else:
            scale_factor = 0
        income_tax_current_new = income_tax_new_total * scale_factor

        # -- Income Tax (Old Regime - for comparison) ----------------------
        income_tax_old_full = _calculate_income_tax(annual_projected_profit, INCOME_TAX_OLD_REGIME)
        income_tax_old_after_rebate = _apply_rebate_87a(
            income_tax_old_full, annual_projected_profit,
            SEC_87A_INCOME_LIMIT_OLD, SEC_87A_REBATE_OLD
        )
        cess_old = income_tax_old_after_rebate * 0.04
        income_tax_old_total = income_tax_old_after_rebate + cess_old
        income_tax_current_old = income_tax_old_total * scale_factor

        if income_tax_current_new <= income_tax_current_old:
            recommended_regime = "New Regime"
            income_tax_current = income_tax_current_new
        else:
            recommended_regime = "Old Regime"
            income_tax_current = income_tax_current_old

        total_liability = gst_liability + income_tax_current

        # -- Section 44AD Presumptive Taxation -----------------------------
        payment_mode = 'mixed'
        if profile:
            payment_mode = profile.get('payment_mode', 'mixed')

        sec_44ad = None
        if annual_projected_revenue <= SEC_44AD_DIGITAL_TURNOVER_LIMIT:
            digital_profit = annual_projected_revenue * SEC_44AD_DIGITAL_RATE
            cash_profit = annual_projected_revenue * SEC_44AD_CASH_RATE
            actual_margin_pct = round((net_profit / revenue * 100), 1) if revenue > 0 else 30

            tax_44ad_digital = _calculate_income_tax(digital_profit, INCOME_TAX_NEW_REGIME)
            tax_44ad_digital = _apply_rebate_87a(tax_44ad_digital, digital_profit, SEC_87A_INCOME_LIMIT_NEW, SEC_87A_REBATE_NEW)
            tax_44ad_digital += tax_44ad_digital * 0.04

            tax_44ad_cash = _calculate_income_tax(cash_profit, INCOME_TAX_NEW_REGIME)
            tax_44ad_cash = _apply_rebate_87a(tax_44ad_cash, cash_profit, SEC_87A_INCOME_LIMIT_NEW, SEC_87A_REBATE_NEW)
            tax_44ad_cash += tax_44ad_cash * 0.04

            recommendation = "44AD is beneficial" if actual_margin_pct > 8 else "Regular accounting may save more"
            if payment_mode == 'digital':
                recommendation = "You use mostly digital payments — the 6% rate under 44AD is highly beneficial for you!"
            elif payment_mode == 'cash':
                recommendation = "With mostly cash transactions, the 8% rate applies under 44AD."

            sec_44ad = {
                "eligible": True,
                "turnover_limit": "Rs.3 Cr (95%+ digital) / Rs.2 Cr (cash)",
                "digital_rate": "6%",
                "cash_rate": "8%",
                "projected_digital_profit": round(digital_profit, 2),
                "projected_cash_profit": round(cash_profit, 2),
                "tax_on_digital": round(tax_44ad_digital * scale_factor, 2),
                "tax_on_cash": round(tax_44ad_cash * scale_factor, 2),
                "actual_margin_pct": actual_margin_pct,
                "recommendation": recommendation,
                "user_payment_mode": payment_mode
            }
        else:
            sec_44ad = {
                "eligible": False,
                "reason": "Annual projected turnover exceeds Rs.3 Crore limit"
            }

        # -- GST Composition Scheme ----------------------------------------
        composition = None
        if annual_projected_revenue <= COMPOSITION_TURNOVER_LIMIT:
            comp_tax = annual_projected_revenue * COMPOSITION_TAX_RATE
            regular_gst = gst_liability * (365 / sales_days) if sales_days > 0 else 0
            savings = regular_gst - comp_tax

            composition = {
                "eligible": True,
                "turnover_limit": "Rs.1.5 Crore",
                "tax_rate": "1% of turnover",
                "estimated_tax": round(comp_tax * scale_factor, 2),
                "regular_gst": round(gst_liability, 2),
                "potential_savings": round(max(0, savings * scale_factor), 2),
                "restrictions": [
                    "Cannot collect GST from customers",
                    "No Input Tax Credit (ITC)",
                    "Only intra-state sales allowed",
                    "Must issue Bill of Supply (not Tax Invoice)"
                ]
            }
        else:
            composition = {
                "eligible": False,
                "reason": "Annual projected turnover exceeds Rs.1.5 Crore limit"
            }

        # -- GST Filing Period Recommendation ------------------------------
        if annual_projected_revenue <= 50000000:
            gst_filing = "Quarterly (GSTR-1 & GSTR-3B) under QRMP scheme"
        else:
            gst_filing = "Monthly (GSTR-1 & GSTR-3B)"

        # -- Product-wise Tax Impact & Margins -----------------------------
        all_sales = firestore_db.get_all_sales(user_id)
        products = firestore_db.get_all_products(user_id)
        prod_map = {p['id']: p for p in products}

        prod_agg = {}
        for s in all_sales:
            pid = s.get('product_id')
            pname = s.get('product_name') or (prod_map.get(pid, {}).get('name') if pid else 'Item')
            cat = s.get('category') or (prod_map.get(pid, {}).get('category') if pid else 'general')
            qty = s.get('quantity', 0)
            tot = s.get('total_price', 0)

            if pid not in prod_agg:
                prod_agg[pid] = {'name': pname, 'category': cat, 'revenue': 0.0, 'quantity': 0}
            prod_agg[pid]['revenue'] += tot
            prod_agg[pid]['quantity'] += qty

        product_tax_list = []
        for pid, data in prod_agg.items():
            cat = (data['category'] or 'general').lower()
            rate = CATEGORY_GST_RATES.get(cat, 0.18)
            tax_contrib = data['revenue'] * rate
            product_tax_list.append({
                "name": data['name'],
                "category": cat,
                "revenue": round(data['revenue'], 2),
                "gst_rate": f"{int(rate * 100)}%",
                "tax_contribution": round(tax_contrib, 2)
            })
        product_tax_list.sort(key=lambda x: x['tax_contribution'], reverse=True)
        product_tax = product_tax_list[:8]

        product_margins = []
        for pid, data in prod_agg.items():
            if data['quantity'] > 0:
                p_item = prod_map.get(pid)
                sell_price = p_item['price'] if p_item else (data['revenue'] / data['quantity'])
                cost_price = (
                    p_item['cost_price']
                    if p_item and p_item.get('cost_price') is not None
                    else sell_price * COST_RATIO
                )
                margin_pct = round(((sell_price - cost_price) / sell_price) * 100, 1) if sell_price > 0 else 0
                profit_per_unit = round(sell_price - cost_price, 2)
                product_margins.append({
                    "name": data['name'],
                    "sell_price": round(sell_price, 2),
                    "cost_price": round(cost_price, 2),
                    "margin_pct": margin_pct,
                    "profit_per_unit": profit_per_unit,
                    "total_revenue": round(data['revenue'], 2)
                })
        product_margins.sort(key=lambda x: x['total_revenue'], reverse=True)
        product_margins = product_margins[:8]

        # -- Smart Alerts --------------------------------------------------
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
                    "message": f"Revenue dropped {round(abs(gst_change_pct))}% this week -- GST liability is lower."
                })

        if net_profit > 0 and revenue > 0:
            margin = (net_profit / revenue) * 100
            if margin < 20:
                alerts.append({
                    "type": "warning",
                    "message": f"Profit margin is {round(margin, 1)}% -- below the 30% healthy threshold. Review pricing."
                })

        if annual_projected_revenue > 2000000000:
            alerts.append({
                "type": "info",
                "message": "Your projected turnover may require GST audit. Consult a CA."
            })

        # -- Personalized Tips ---------------------------------------------
        personalized_tips = []
        if profile:
            btype = profile.get('business_type', '')
            msme = profile.get('msme_category', '')

            if btype == 'manufacturing':
                personalized_tips.append("As a manufacturer, you can claim Input Tax Credit on raw materials to reduce GST liability.")
            elif btype == 'services':
                personalized_tips.append("For service businesses, consider Section 44ADA which allows 50% presumptive profit (lower than 44AD's 6-8%).")
            elif btype == 'trading':
                personalized_tips.append("As a trader, maintain purchase invoices to maximize Input Tax Credit claims.")

            if msme == 'micro':
                personalized_tips.append("Micro enterprises can register under Udyam for benefits like priority lending, lower interest rates, and delayed payment protection.")
            elif msme == 'small':
                personalized_tips.append("Small enterprises should explore CGTMSE scheme for collateral-free loans up to Rs.5 Crore.")

            if payment_mode == 'digital':
                personalized_tips.append("Your digital payment preference qualifies you for the lower 6% presumptive rate — potential tax savings!")

        return jsonify({
            "revenue": round(revenue, 2),
            "estimated_cost": round(estimated_cost, 2),
            "net_profit": round(net_profit, 2),
            "annual_projected_revenue": round(annual_projected_revenue, 2),
            "annual_projected_profit": round(annual_projected_profit, 2),
            "gst_liability": round(gst_liability, 2),
            "gst_breakdown": gst_breakdown,
            "income_tax_new": round(income_tax_current_new, 2),
            "income_tax_old": round(income_tax_current_old, 2),
            "income_tax": round(income_tax_current, 2),
            "recommended_regime": recommended_regime,
            "total_liability": round(total_liability, 2),
            "sec_44ad": sec_44ad,
            "composition": composition,
            "gst_filing_period": gst_filing,
            "product_tax": product_tax,
            "product_margins": product_margins,
            "cashflow": {
                "revenue": round(revenue, 2),
                "expenses": round(estimated_cost, 2),
                "profit": round(net_profit, 2)
            },
            "alerts": alerts,
            "personalized_tips": personalized_tips
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
