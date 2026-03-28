document.addEventListener('DOMContentLoaded', loadTaxData);

async function loadTaxData() {
    try {
        const data = await apiCall('/api/tax/estimate');

        const fmt = (n) => `₹${Number(n).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

        // ── Section 1: Summary Cards ──────────────────────────────────
        document.getElementById('val-revenue').innerText = fmt(data.revenue);
        document.getElementById('val-profit').innerText  = fmt(data.net_profit);
        document.getElementById('val-gst').innerText     = fmt(data.gst_liability);
        document.getElementById('val-tax').innerText     = fmt(data.income_tax);

        // ── Section 2: Total Liability ────────────────────────────────
        document.getElementById('val-total').innerText = fmt(data.total_liability);
        document.getElementById('cf-gst').innerText   = fmt(data.gst_liability);
        document.getElementById('cf-itax').innerText  = fmt(data.income_tax);

        // ── Section 6: Cashflow Snapshot ──────────────────────────────
        document.getElementById('cf-rev').innerText = fmt(data.cashflow.revenue);
        document.getElementById('cf-exp').innerText = fmt(data.cashflow.expenses);
        document.getElementById('cf-pft').innerText = fmt(data.cashflow.profit);

        // Animated cashflow bars (revenue = 100% reference)
        const rev = data.cashflow.revenue || 1;
        setTimeout(() => {
            document.getElementById('cf-rev-bar').style.width = '100%';
            document.getElementById('cf-exp-bar').style.width = ((data.cashflow.expenses / rev) * 100).toFixed(1) + '%';
            document.getElementById('cf-pft-bar').style.width = ((data.cashflow.profit / rev) * 100).toFixed(1) + '%';
        }, 200);

        // ── Section 4: Profit Margin by Product ──────────────────────
        const marginBody = document.getElementById('margin-body');
        marginBody.innerHTML = '';
        if (!data.product_margins || data.product_margins.length === 0) {
            marginBody.innerHTML = '<tr><td colspan="3" class="text-muted" style="text-align:center;">No sales data yet.</td></tr>';
        } else {
            data.product_margins.forEach(p => {
                const barWidth = Math.min(p.margin_pct, 100);
                const barColor = p.margin_pct >= 30 ? '#34d399' : p.margin_pct >= 15 ? '#fbbf24' : '#ef4444';
                marginBody.innerHTML += `
                    <tr>
                        <td><strong>${escHtml(p.name)}</strong></td>
                        <td>
                            <div class="margin-bar-wrap">
                                <div class="margin-bar-bg">
                                    <div class="margin-bar-fill" style="width:${barWidth}%; background:${barColor};"></div>
                                </div>
                                <span style="color:${barColor}; font-weight:700; min-width:42px;">${p.margin_pct}%</span>
                            </div>
                        </td>
                        <td style="color:#34d399; font-weight:700;">₹${p.profit_per_unit}</td>
                    </tr>
                `;
            });
        }

        // ── Section 5: Product Tax Impact ────────────────────────────
        const taxBody = document.getElementById('tax-body');
        taxBody.innerHTML = '';
        if (!data.product_tax || data.product_tax.length === 0) {
            taxBody.innerHTML = '<tr><td colspan="3" class="text-muted" style="text-align:center;">No sales data yet.</td></tr>';
        } else {
            data.product_tax.forEach((p, i) => {
                const medal = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : '';
                taxBody.innerHTML += `
                    <tr>
                        <td>${medal} ${escHtml(p.name)}</td>
                        <td style="color:#93c5fd;">₹${p.revenue.toLocaleString('en-IN')}</td>
                        <td style="color:#fbbf24; font-weight:700;">₹${p.tax_contribution.toLocaleString('en-IN')}</td>
                    </tr>
                `;
            });
        }

        // ── Smart Alerts ─────────────────────────────────────────────
        const alertStrip = document.getElementById('alert-strip');
        alertStrip.innerHTML = '';
        if (data.alerts && data.alerts.length > 0) {
            data.alerts.forEach(a => {
                const cls = a.type === 'warning' ? 'alert-warning' : 'alert-info';
                const icon = a.type === 'warning' ? '⚠️' : 'ℹ️';
                alertStrip.innerHTML += `
                    <div class="alert-card ${cls}">
                        <span style="font-size:1.1rem;">${icon}</span>
                        <span>${escHtml(a.message)}</span>
                    </div>
                `;
            });
        }

    } catch (e) {
        console.error('Tax data load failed', e);
    }
}

function escHtml(str) {
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
