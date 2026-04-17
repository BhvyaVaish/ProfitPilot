// Wait for auth token to be resolved before loading data.
function _initHome() {
    document.getElementById('current-date').innerText = new Date().toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    loadHomeSummary();
}

if (window._authReady) {
    _initHome();
} else {
    window.addEventListener('auth-ready', _initHome, { once: true });
}

async function loadHomeSummary() {
    try {
        const data = await apiCall('/api/home/summary');

        // Quick Summary
        animateCounter('stat-sales-today', data.quick_summary.today_sales, true);
        animateCounter('stat-week-sales', data.quick_summary.week_sales, true);
        document.getElementById('stat-low-stock').innerText = data.quick_summary.low_stock_count;
        document.getElementById('stat-out-stock').innerText = data.quick_summary.out_of_stock_count;

        // Week change indicator
        const changeEl = document.getElementById('stat-week-change');
        const wc = data.quick_summary.week_change;
        if (wc > 0) {
            changeEl.innerHTML = `<span style="color:var(--accent-green); font-weight:600;">+${wc}%</span> vs last week`;
        } else if (wc < 0) {
            changeEl.innerHTML = `<span style="color:var(--accent-red); font-weight:600;">${wc}%</span> vs last week`;
        } else {
            changeEl.innerHTML = `<span class="text-muted">Same as last week</span>`;
        }

        // Business Health Score
        if (data.health_score) {
            const hs = data.health_score;
            const scoreEl = document.getElementById('health-score');
            scoreEl.innerText = hs.score;

            const gradeEl = document.getElementById('health-grade');
            gradeEl.innerText = hs.grade;

            if (hs.score >= 80) { scoreEl.style.color = 'var(--accent-green)'; gradeEl.style.color = 'var(--accent-green)'; }
            else if (hs.score >= 60) { scoreEl.style.color = 'var(--accent-blue)'; gradeEl.style.color = 'var(--accent-blue)'; }
            else if (hs.score >= 40) { scoreEl.style.color = 'var(--accent-yellow)'; gradeEl.style.color = 'var(--accent-yellow)'; }
            else { scoreEl.style.color = 'var(--accent-red)'; gradeEl.style.color = 'var(--accent-red)'; }

            const factorsEl = document.getElementById('health-factors');
            factorsEl.innerHTML = '';
            hs.factors.forEach(f => {
                const pct = Math.round((f.score / f.max) * 100);
                const barColor = pct >= 70 ? 'var(--accent-green)' : pct >= 40 ? 'var(--accent-yellow)' : 'var(--accent-red)';
                factorsEl.innerHTML += `
                    <div style="margin-bottom:8px;">
                        <div style="display:flex; justify-content:space-between; font-size:0.82rem; margin-bottom:3px;">
                            <span style="color:var(--text-secondary); font-weight:500;">${f.name}</span>
                            <span style="font-weight:600;">${f.score}/${f.max}</span>
                        </div>
                        <div style="height:6px; background:rgba(0,0,0,0.06); border-radius:99px; overflow:hidden;">
                            <div style="height:100%; width:${pct}%; background:${barColor}; border-radius:99px; transition:width 0.6s ease;"></div>
                        </div>
                    </div>
                `;
            });
        }

        // AI Priority Actions
        const paContainer = document.getElementById('priority-actions');
        paContainer.innerHTML = '';

        if (!data.priority_actions || data.priority_actions.length === 0) {
            // Check if user has no products to show a more helpful onboarding message
            const hasNoProducts = data.quick_summary && data.quick_summary.total_products === 0;
            if (hasNoProducts) {
                paContainer.innerHTML = `
                    <div style="background: rgba(37,99,235,0.06); padding: 16px; border-radius: var(--radius-sm); border-left: 3px solid var(--accent-blue);">
                        <strong style="color: var(--accent-blue); display:block; margin-bottom:4px;">Welcome to ProfitPilot!</strong>
                        <span class="text-muted" style="font-size:0.9rem;">To see AI insights and priority actions, please <a href="inventory.html" style="color:var(--accent-blue); font-weight:600; text-decoration:none;">Add Products</a> or import your inventory CSV.</span>
                    </div>
                `;
            } else {
                paContainer.innerHTML = '<div class="text-muted" style="padding:12px; font-size:0.9rem;">✔️ No urgent actions required right now. You are all caught up!</div>';
            }
        } else {
            data.priority_actions.forEach(action => {
                let iconColor = 'var(--accent-blue)';
                if (action.type === 'Low Stock' || action.type === 'Critical Stock') iconColor = 'var(--accent-red)';
                else if (action.type === 'High Demand') iconColor = 'var(--accent-green)';
                else if (action.type === 'Dead Stock') iconColor = 'var(--accent-yellow)';

                paContainer.innerHTML += `
                    <div style="background: rgba(0,0,0,0.02); padding: 10px 14px; border-radius: var(--radius-sm); border-left: 3px solid ${iconColor}; font-size:0.88rem;">
                        <strong style="color: var(--text-primary);">${action.message}</strong>
                        <span class="badge badge-blue" style="margin-left:6px; font-size:0.7rem;">${action.type}</span>
                    </div>
                `;
            });
        }

        // Festival Insights & Smart AI Predictions
        const fiContainer = document.getElementById('festival-insights');
        if (data.festival_insights) {
            const fi = data.festival_insights;
            let html = `
                <div style="padding: 10px 14px; background: rgba(16, 185, 129, 0.06); border-radius: var(--radius-sm); font-size:0.88rem; margin-bottom:8px;">
                    <strong style="color:var(--text-primary);"><i class="fas fa-calendar-star" style="color:var(--accent-green); margin-right:6px;"></i>${fi.upcoming}</strong>
                </div>
                <div style="padding: 10px 14px; background: rgba(16, 185, 129, 0.06); border-radius: var(--radius-sm); font-size:0.88rem; margin-bottom:12px;">
                    <span style="color:var(--text-secondary);">${fi.suggestion}</span>
                </div>
            `;

            // Display Top AI Predicted Items (The "Top 15")
            if (fi.festivals && fi.festivals.length > 0) {
                const target = fi.festivals[0];
                if (target.demand_items && target.demand_items.length > 0) {
                    html += `
                        <div style="margin-top:15px;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                <span style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em; color:var(--text-secondary); font-weight:700;">AI High-Demand Forecast</span>
                                <span class="badge badge-green" style="font-size:0.65rem;">Top ${target.demand_items.length} Items</span>
                            </div>
                            <div style="display:flex; flex-wrap:wrap; gap:6px;">
                                ${target.demand_items.map(item => `
                                    <span style="background:white; border:1px solid rgba(16, 185, 129, 0.2); padding:4px 10px; border-radius:99px; font-size:0.78rem; color:var(--accent-green); font-weight:500;">
                                        ${item}
                                    </span>
                                `).join('')}
                            </div>
                        </div>
                    `;
                }
            }

            // Display Opportunity Alerts (Items user doesn't have)
            if (fi.smart_suggestions && fi.smart_suggestions.length > 0) {
                const opportunities = fi.smart_suggestions.filter(s => s.type === 'opportunity');
                if (opportunities.length > 0) {
                    html += `
                        <div style="margin-top:20px; border-top:1px dashed rgba(0,0,0,0.1); padding-top:15px;">
                            <span style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em; color:var(--text-secondary); font-weight:700; display:block; margin-bottom:10px;">Market Opportunities</span>
                            <div style="display:flex; flex-direction:column; gap:8px;">
                                ${opportunities.slice(0, 5).map(o => `
                                    <div style="display:flex; align-items:center; gap:10px; background:white; padding:10px; border-radius:var(--radius-sm); box-shadow:0 2px 4px rgba(0,0,0,0.02); border:1px solid rgba(0,0,0,0.04);">
                                        <div style="width:32px; height:32px; background:rgba(37, 99, 235, 0.08); border-radius:8px; display:flex; align-items:center; justify-content:center; color:var(--accent-blue);">
                                            <i class="fas fa-plus-circle" style="font-size:1rem;"></i>
                                        </div>
                                        <div style="flex:1;">
                                            <div style="font-size:0.85rem; font-weight:600; color:var(--text-primary);">${o.item}</div>
                                            <div style="font-size:0.72rem; color:var(--text-secondary);">High potential for ${o.festival}</div>
                                        </div>
                                        <button onclick="window.location.href='inventory.html?suggest=${encodeURIComponent(o.item)}'" 
                                                style="padding:5px 10px; font-size:0.7rem; background:var(--accent-blue); color:white; border:none; border-radius:6px; cursor:pointer; font-weight:600;">
                                            Add
                                        </button>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;
                }
            }

            fiContainer.innerHTML = html;
        }

        // Mini Insights
        const miContainer = document.getElementById('mini-insights');
        if (data.mini_insights) {
            miContainer.innerHTML = `
                <div style="padding: 10px 14px; background: rgba(37, 99, 235, 0.05); border-radius: var(--radius-sm); font-size:0.88rem;">
                    <strong>Top Selling:</strong> ${data.mini_insights.top_selling}
                </div>
                <div style="padding: 10px 14px; background: rgba(37, 99, 235, 0.05); border-radius: var(--radius-sm); font-size:0.88rem;">
                    <strong>Least Selling:</strong> ${data.mini_insights.least_selling}
                </div>
                <div style="padding: 10px 14px; background: rgba(37, 99, 235, 0.05); border-radius: var(--radius-sm); font-size:0.88rem;">
                    <strong>High Potential:</strong> ${data.mini_insights.high_potential}
                </div>
            `;
        }

    } catch (e) {
        console.error("Failed to load home summary", e);
        document.getElementById('priority-actions').innerHTML = '<div class="text-muted" style="padding:12px;">Failed to load insights. Please refresh.</div>';
        document.getElementById('festival-insights').innerHTML = '<div class="text-muted" style="padding:12px;">Data unavailable.</div>';
        document.getElementById('mini-insights').innerHTML = '<div class="text-muted" style="padding:12px;">Data unavailable.</div>';
    }
}

function animateCounter(elementId, target, isCurrency = false) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const numTarget = Number(target) || 0;
    if (numTarget === 0) {
        el.innerText = isCurrency ? formatCurrency(0) : '0';
        return;
    }
    const duration = 800;
    const startTime = performance.now();

    function step(timestamp) {
        const elapsed = timestamp - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
        const current = Math.round(numTarget * eased);

        el.innerText = isCurrency ? formatCurrency(current) : current;

        if (progress < 1) {
            requestAnimationFrame(step);
        } else {
            el.innerText = isCurrency ? formatCurrency(numTarget) : numTarget;
        }
    }
    requestAnimationFrame(step);
}
