// Wait for auth token to be resolved before loading data.
if (window._authReady) {
    loadTaxData();
} else {
    window.addEventListener('auth-ready', loadTaxData, { once: true });
}


async function loadTaxData() {
    try {
        const data = await apiCall('/api/tax/estimate');

        const fmt = (n) => `Rs.${Number(n).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        const fmtShort = (n) => `Rs.${Number(n).toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;

        // -- Section 1: Summary Cards ─────────────────────────────────
        document.getElementById('val-revenue').innerText = fmtShort(data.revenue);
        document.getElementById('val-profit').innerText = fmtShort(data.net_profit);
        document.getElementById('val-gst').innerText = fmtShort(data.gst_liability);
        document.getElementById('val-tax').innerText = fmtShort(data.income_tax);

        // -- Section 2: Total Liability ───────────────────────────────
        document.getElementById('val-total').innerText = fmt(data.total_liability);
        document.getElementById('cf-gst').innerText = fmt(data.gst_liability);
        document.getElementById('cf-itax').innerText = fmt(data.income_tax);

        // -- Section 3: Cashflow Snapshot ─────────────────────────────
        document.getElementById('cf-rev').innerText = fmt(data.cashflow.revenue);
        document.getElementById('cf-exp').innerText = fmt(data.cashflow.expenses);
        document.getElementById('cf-pft').innerText = fmt(data.cashflow.profit);

        const rev = data.cashflow.revenue || 1;
        setTimeout(() => {
            document.getElementById('cf-rev-bar').style.width = '100%';
            document.getElementById('cf-exp-bar').style.width = ((data.cashflow.expenses / rev) * 100).toFixed(1) + '%';
            document.getElementById('cf-pft-bar').style.width = ((data.cashflow.profit / rev) * 100).toFixed(1) + '%';
        }, 200);

        // -- Section 4: Income Tax Regime Comparison ──────────────────
        const regimeEl = document.getElementById('regime-comparison');
        if (regimeEl) {
            const newIsRec = data.recommended_regime === 'New Regime';
            const oldIsRec = data.recommended_regime === 'Old Regime';

            regimeEl.innerHTML = `
                <div class="regime-card ${newIsRec ? 'recommended' : ''}">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                        <h3 style="font-size:0.95rem;">New Regime</h3>
                        ${newIsRec ? '<span class="badge badge-green" style="font-size:0.72rem;">Recommended</span>' : ''}
                    </div>
                    <div style="font-size:1.6rem; font-weight:700; font-family:var(--font-display); color:${newIsRec ? 'var(--accent-green)' : 'var(--text-primary)'}; margin-bottom:10px;">
                        ${fmt(data.income_tax_new)}
                    </div>
                    <div style="font-size:0.82rem; color:var(--text-muted);">
                        <div>Rebate under Section 87A applied (up to Rs.60,000 if taxable income &lt; Rs.12L)</div>
                        <div style="margin-top:4px;">4% Health & Education Cess included</div>
                        <div style="margin-top:4px;">Projected annual profit: ${fmtShort(data.annual_projected_profit)}</div>
                    </div>
                </div>
                <div class="regime-card ${oldIsRec ? 'recommended' : ''}">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                        <h3 style="font-size:0.95rem;">Old Regime</h3>
                        ${oldIsRec ? '<span class="badge badge-green" style="font-size:0.72rem;">Recommended</span>' : ''}
                    </div>
                    <div style="font-size:1.6rem; font-weight:700; font-family:var(--font-display); color:${oldIsRec ? 'var(--accent-green)' : 'var(--text-primary)'}; margin-bottom:10px;">
                        ${fmt(data.income_tax_old)}
                    </div>
                    <div style="font-size:0.82rem; color:var(--text-muted);">
                        <div>Rebate under Section 87A applied (up to Rs.12,500 if taxable income &lt; Rs.5L)</div>
                        <div style="margin-top:4px;">Deductions under 80C, 80D etc. available</div>
                        <div style="margin-top:4px;">4% Health & Education Cess included</div>
                    </div>
                </div>
            `;
        }

        // -- Section 5: Section 44AD Presumptive Taxation ─────────────
        const sec44El = document.getElementById('sec44ad-content');
        if (sec44El && data.sec_44ad) {
            const s = data.sec_44ad;
            if (s.eligible) {
                sec44El.innerHTML = `
                    <div class="badge badge-green mb-1" style="font-size:0.78rem;">Eligible</div>
                    <div style="display:flex; flex-direction:column; gap:6px; font-size:0.88rem;">
                        <div class="composition-line"><span class="text-muted">Turnover Limit</span><span style="font-weight:600;">${s.turnover_limit}</span></div>
                        <div class="composition-line"><span class="text-muted">Digital Receipts (6%)</span><span style="font-weight:600;">${fmt(s.projected_digital_profit)}</span></div>
                        <div class="composition-line"><span class="text-muted">Cash Receipts (8%)</span><span style="font-weight:600;">${fmt(s.projected_cash_profit)}</span></div>
                        <div class="composition-line"><span class="text-muted">Tax (Digital path)</span><span style="font-weight:600; color:var(--accent-green);">${fmt(s.tax_on_digital)}</span></div>
                        <div class="composition-line"><span class="text-muted">Tax (Cash path)</span><span style="font-weight:600; color:var(--accent-yellow);">${fmt(s.tax_on_cash)}</span></div>
                        <div class="composition-line"><span class="text-muted">Your actual margin</span><span style="font-weight:600;">${s.actual_margin_pct}%</span></div>
                    </div>
                    <div style="margin-top:10px; padding:10px; background:rgba(37,99,235,0.05); border-radius:var(--radius-sm); font-size:0.82rem; color:var(--text-secondary);">
                        <strong>Tip:</strong> ${s.recommendation}. With Section 44AD, you don't need to maintain detailed books of accounts.
                    </div>
                `;
            } else {
                sec44El.innerHTML = `
                    <div class="badge badge-red mb-1" style="font-size:0.78rem;">Not Eligible</div>
                    <p class="text-muted" style="font-size:0.88rem; margin-top:8px;">${s.reason}</p>
                `;
            }
        }

        // -- Section 6: GST Composition Scheme ────────────────────────
        const compEl = document.getElementById('composition-content');
        if (compEl && data.composition) {
            const c = data.composition;
            if (c.eligible) {
                compEl.innerHTML = `
                    <div class="badge badge-green mb-1" style="font-size:0.78rem;">Eligible</div>
                    <div style="display:flex; flex-direction:column; gap:6px; font-size:0.88rem;">
                        <div class="composition-line"><span class="text-muted">Turnover Limit</span><span style="font-weight:600;">${c.turnover_limit}</span></div>
                        <div class="composition-line"><span class="text-muted">Composition Rate</span><span style="font-weight:600;">${c.tax_rate}</span></div>
                        <div class="composition-line"><span class="text-muted">Est. Composition Tax</span><span style="font-weight:600; color:var(--accent-green);">${fmt(c.estimated_tax)}</span></div>
                        <div class="composition-line"><span class="text-muted">Regular GST</span><span style="font-weight:600; color:var(--accent-red);">${fmt(c.regular_gst)}</span></div>
                        <div class="composition-line"><span class="text-muted">Potential Savings</span><span style="font-weight:700; color:var(--accent-green);">${fmt(c.potential_savings)}</span></div>
                    </div>
                    <div style="margin-top:10px; padding:10px; background:rgba(245,158,11,0.06); border-radius:var(--radius-sm); font-size:0.82rem;">
                        <strong>Restrictions:</strong>
                        <ul style="margin:6px 0 0 16px; padding:0; line-height:1.8;">
                            ${c.restrictions.map(r => `<li>${r}</li>`).join('')}
                        </ul>
                    </div>
                `;
            } else {
                compEl.innerHTML = `
                    <div class="badge badge-red mb-1" style="font-size:0.78rem;">Not Eligible</div>
                    <p class="text-muted" style="font-size:0.88rem; margin-top:8px;">${c.reason}</p>
                `;
            }
        }

        // -- Section 7: GST Breakdown by Category ─────────────────────
        const gstBody = document.getElementById('gst-breakdown-body');
        if (gstBody && data.gst_breakdown) {
            gstBody.innerHTML = '';
            if (data.gst_breakdown.length === 0) {
                gstBody.innerHTML = '<tr><td colspan="4" class="text-muted text-center">No GST data yet.</td></tr>';
            } else {
                data.gst_breakdown.forEach(g => {
                    gstBody.innerHTML += `
                        <tr>
                            <td><strong>${escHtml(g.category)}</strong></td>
                            <td><span class="badge badge-blue">${g.rate_pct}</span></td>
                            <td>${fmt(g.revenue)}</td>
                            <td style="font-weight:600; color:var(--accent-yellow);">${fmt(g.gst)}</td>
                        </tr>
                    `;
                });
            }
        }

        // -- Section 8: GST Filing Info ───────────────────────────────
        const filingEl = document.getElementById('gst-filing-info');
        if (filingEl && data.gst_filing_period) {
            filingEl.innerHTML = `
                <div style="margin-bottom:10px;">
                    <strong style="color:var(--text-primary);">Recommended Filing:</strong>
                    <span style="font-weight:600; color:var(--accent-blue);">${data.gst_filing_period}</span>
                </div>
                <div style="font-size:0.82rem; color:var(--text-muted); line-height:1.7;">
                    <div>Projected Annual Revenue: ${fmtShort(data.annual_projected_revenue)}</div>
                    <div style="margin-top:8px;">Businesses with turnover up to Rs.5 Crore can opt for quarterly filing under the QRMP scheme, reducing compliance burden.</div>
                </div>
            `;
        }

        // -- Section 9: Profit Margin by Product ──────────────────────
        const marginBody = document.getElementById('margin-body');
        marginBody.innerHTML = '';
        if (!data.product_margins || data.product_margins.length === 0) {
            marginBody.innerHTML = '<tr><td colspan="3" class="text-muted text-center">No sales data yet.</td></tr>';
        } else {
            data.product_margins.forEach(p => {
                const barWidth = Math.min(p.margin_pct, 100);
                const barColor = p.margin_pct >= 30 ? '#10b981' : p.margin_pct >= 15 ? '#f59e0b' : '#ef4444';
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
                        <td style="color:#10b981; font-weight:700;">Rs.${p.profit_per_unit}</td>
                    </tr>
                `;
            });
        }

        // -- Section 10: Product Tax Impact ───────────────────────────
        const taxBody = document.getElementById('tax-body');
        taxBody.innerHTML = '';
        if (!data.product_tax || data.product_tax.length === 0) {
            taxBody.innerHTML = '<tr><td colspan="3" class="text-muted text-center">No sales data yet.</td></tr>';
        } else {
            data.product_tax.forEach((p, i) => {
                const medal = i === 0 ? '<span style="color:#f59e0b; font-weight:700;">#1</span> ' : i === 1 ? '<span style="color:#94a3b8; font-weight:700;">#2</span> ' : i === 2 ? '<span style="color:#b45309; font-weight:700;">#3</span> ' : '';
                taxBody.innerHTML += `
                    <tr>
                        <td>${medal}${escHtml(p.name)}</td>
                        <td style="color:var(--accent-blue);">${fmt(p.revenue)}</td>
                        <td style="color:var(--accent-yellow); font-weight:700;">${fmt(p.tax_contribution)}</td>
                    </tr>
                `;
            });
        }

        // -- Smart Alerts ─────────────────────────────────────────────
        const alertStrip = document.getElementById('alert-strip');
        alertStrip.innerHTML = '';
        if (data.alerts && data.alerts.length > 0) {
            data.alerts.forEach(a => {
                const cls = a.type === 'warning' ? 'alert-warning' : 'alert-info';
                alertStrip.innerHTML += `
                    <div class="alert-card ${cls}">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0; margin-top:2px;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                        <span>${escHtml(a.message)}</span>
                    </div>
                `;
            });
        }

        // -- Personalized Tips (from user profile) ────────────────────
        const tipsCard = document.getElementById('personalized-tips-card');
        const tipsList = document.getElementById('personalized-tips-list');
        if (tipsCard && tipsList && data.personalized_tips && data.personalized_tips.length > 0) {
            tipsList.innerHTML = '';
            data.personalized_tips.forEach(tip => {
                tipsList.innerHTML += `
                    <div style="display:flex; gap:10px; align-items:flex-start; padding:10px 14px; background:rgba(37,99,235,0.05); border-radius:var(--radius-sm); border-left:3px solid var(--accent-blue); font-size:0.88rem;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" stroke-width="2" style="flex-shrink:0; margin-top:2px;"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
                        <span style="color:var(--text-secondary);">${escHtml(tip)}</span>
                    </div>
                `;
            });
            tipsCard.style.display = 'block';
        }

    } catch (e) {
        console.error('Tax data load failed', e);
        const tbk = document.getElementById('tax-breakdown-body');
        if (tbk) tbk.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Failed to load tax insights. Please start billing to see data.</td></tr>';
    }
}

function escHtml(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
