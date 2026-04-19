let salesChartInst = null;
let topChartInst = null;
let categoryChartInst = null;

// Wait for auth token to be resolved before loading data.
function _initDashboard() {
    loadFullDashboard();
    document.getElementById('time-range').addEventListener('change', loadFullDashboard);
}

if (window._authReady) {
    _initDashboard();
} else {
    window.addEventListener('auth-ready', _initDashboard, { once: true });
}

async function loadFullDashboard() {
    try {
        const days = document.getElementById('time-range').value || 7;
        
        // Show loading state
        const chartCards = document.querySelectorAll('canvas');
        chartCards.forEach(canvas => {
            const parent = canvas.parentElement;
            let loader = parent.querySelector('.dashboard-loader');
            if (!loader) {
                loader = document.createElement('div');
                loader.className = 'dashboard-loader text-center';
                loader.innerHTML = '<div style="margin:40px auto; width:30px; height:30px; border:3px solid rgba(37,99,235,0.2); border-top-color:var(--accent-blue); border-radius:50%; animation:spin 1s linear infinite;"></div>';
                
                if (!document.getElementById('spinner-style')) {
                    const style = document.createElement('style');
                    style.id = 'spinner-style';
                    style.innerHTML = '@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }';
                    document.head.appendChild(style);
                }
                
                parent.appendChild(loader);
            }
            loader.style.display = 'block';
            canvas.style.display = 'none';
        });

        const restockBody = document.getElementById('restock-body');
        if(restockBody) restockBody.innerHTML = '<tr><td colspan="4" class="text-center"><div style="margin:20px auto; width:24px; height:24px; border:2px solid rgba(37,99,235,0.2); border-top-color:var(--accent-blue); border-radius:50%; animation:spin 1s linear infinite;"></div></td></tr>';
        
        const deadBody = document.getElementById('dead-stock-body');
        if(deadBody) deadBody.innerHTML = '<tr><td colspan="3" class="text-center"><div style="margin:20px auto; width:24px; height:24px; border:2px solid rgba(37,99,235,0.2); border-top-color:var(--accent-blue); border-radius:50%; animation:spin 1s linear infinite;"></div></td></tr>';

        const alertPanel = document.getElementById('alert-panel');
        if(alertPanel) alertPanel.innerHTML = '<div style="margin:20px auto; width:24px; height:24px; border:2px solid rgba(37,99,235,0.2); border-top-color:var(--accent-blue); border-radius:50%; animation:spin 1s linear infinite;"></div>';

        const hpotContainer = document.getElementById('high-potential-panel');
        if(hpotContainer) hpotContainer.innerHTML = '<div style="margin:20px auto; width:24px; height:24px; border:2px solid rgba(37,99,235,0.2); border-top-color:var(--accent-blue); border-radius:50%; animation:spin 1s linear infinite;"></div>';

        const data = await apiCall(`/api/dashboard/full?days=${days}`);
        
        // Remove loaders
        document.querySelectorAll('.dashboard-loader').forEach(l => l.style.display = 'none');
        chartCards.forEach(canvas => canvas.style.display = 'block');

        // Chart.js global defaults for light theme
        Chart.defaults.color = "rgba(15, 23, 42, 0.5)";
        Chart.defaults.font.family = "'DM Sans', sans-serif";
        Chart.defaults.font.size = 12;

        // Check for completely empty data (new user / flushed data)
        if (data.sales_graph.labels.length === 0 && data.catalog_performance.length === 0) {
            const chartCards = document.querySelectorAll('canvas');
            chartCards.forEach(canvas => {
                const parent = canvas.parentElement;
                canvas.style.display = 'none';
                const emptyState = document.createElement('div');
                emptyState.innerHTML = `
                    <div style="padding:40px 20px; text-align:center; background:rgba(37,99,235,0.03); border-radius:8px; border:1px dashed rgba(37,99,235,0.2);">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" stroke-width="2" style="margin-bottom:12px; opacity:0.8;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                        <h4 style="color:var(--text-primary); margin-bottom:6px;">No Data Available</h4>
                        <p class="text-muted" style="font-size:0.9rem;">Upload your inventory or start billing to unlock actionable AI insights and revenue charts.</p>
                        <a href="inventory" class="btn btn-primary" style="margin-top:12px; display:inline-block; text-decoration:none;">Go to Inventory</a>
                    </div>
                `;
                parent.appendChild(emptyState);
            });
        } else {
            // 1. Sales Chart
            renderSalesChart(data.sales_graph.labels, data.sales_graph.revenue);

            // 2. Top Products
            renderTopChart(data.catalog_performance.map(t => t.name), data.catalog_performance.map(t => t.total_qty));

            // 3. Category Breakdown
            if (data.category_breakdown && data.category_breakdown.length > 0) {
                renderCategoryChart(data.category_breakdown);
            } else {
                const catCanvas = document.getElementById('categoryChart');
                if (catCanvas) {
                    catCanvas.style.display = 'none';
                    catCanvas.parentElement.innerHTML += '<div class="text-muted text-center" style="padding:40px 10px;">Not enough data yet.</div>';
                }
            }
        }

        // 4. Smart Procurement Table
        const restockBody = document.getElementById('restock-body');
        restockBody.innerHTML = '';
        if (data.smart_procurement.length === 0) {
            restockBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted" style="padding:30px 10px;">Stock levels optimized. <br><span style="font-size:0.85em">Add more inventory to see smart suggestions.</span></td></tr>';
        } else {
            data.smart_procurement.forEach(s => {
                restockBody.innerHTML += `
                    <tr>
                        <td><strong>${s.name}</strong></td>
                        <td>${s.current_stock}</td>
                        <td>${s.predicted_demand}</td>
                        <td class="text-green" style="font-weight:600;">+${s.suggested_restock}</td>
                    </tr>
                `;
            });
        }

        // 5. Dead Stock
        const deadBody = document.getElementById('dead-stock-body');
        deadBody.innerHTML = '';
        if (data.dead_stock.length === 0) {
            deadBody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">No dead stock found. Great efficiency!</td></tr>';
        } else {
            data.dead_stock.forEach(d => {
                deadBody.innerHTML += `
                    <tr>
                        <td><strong>${d.name}</strong></td>
                        <td>${d.stock}</td>
                        <td class="text-muted">${d.days_since}</td>
                    </tr>
                `;
            });
        }

        // 6. High Potential Items
        const hpotContainer = document.getElementById('high-potential-panel');
        hpotContainer.innerHTML = '';
        if (data.high_potential.length === 0) {
            hpotContainer.innerHTML = '<span class="text-muted" style="font-size:0.88rem;">No rapid-growth items detected currently.</span>';
        } else {
            data.high_potential.slice(0, 4).forEach(h => {
                hpotContainer.innerHTML += `
                    <div style="background: rgba(16,185,129,0.06); padding: 8px 12px; border-radius: var(--radius-sm); font-size:0.88rem;">
                        <strong>${h.name}</strong>
                        ${h.reason ? `<br><span class="text-muted" style="font-size:0.78rem;">${h.reason}</span>` : ''}
                    </div>
                `;
            });
        }

        // 7. Alert Panel
        const alertPanel = document.getElementById('alert-panel');
        alertPanel.innerHTML = '';
        if (data.alerts.length === 0) {
            alertPanel.innerHTML = '<span class="text-muted" style="font-size:0.88rem;">No critical alerts.</span>';
        } else {
            data.alerts.forEach(a => {
                alertPanel.innerHTML += `
                    <div style="background: rgba(239, 68, 68, 0.06); padding: 8px 12px; border-radius: var(--radius-sm); border-left: 2px solid var(--accent-orange); font-size:0.85rem;">
                        <strong>${a.message}</strong>
                    </div>
                `;
            });
        }

    } catch (e) {
        console.error("Dashboard failed to load", e);
        
        // Hide loaders on error
        document.querySelectorAll('.dashboard-loader').forEach(l => l.style.display = 'none');
        
        // Show error state in the first card
        const firstCanvas = document.querySelector('canvas');
        if (firstCanvas) {
            const parent = firstCanvas.parentElement;
            let errEl = parent.querySelector('.dashboard-error');
            if (!errEl) {
                errEl = document.createElement('div');
                errEl.className = 'dashboard-error text-center text-red';
                errEl.style.padding = '40px 10px';
                parent.appendChild(errEl);
            }
            errEl.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-bottom:8px;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg><br>Failed to load dashboard data. Please try refreshing.`;
        }
    }
}

function renderSalesChart(labels, data) {
    const ctx = document.getElementById('salesChart');
    if (salesChartInst) salesChartInst.destroy();

    salesChartInst = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Revenue (Rs.)',
                data,
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.08)',
                tension: 0.4,
                fill: true,
                borderWidth: 2,
                pointBackgroundColor: '#2563eb',
                pointRadius: 3,
                pointHoverRadius: 5,
            }]
        },
        options: {
            responsive: true,
            interaction: { intersect: false, mode: 'index' },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { callback: v => 'Rs.' + v.toLocaleString('en-IN') } },
                x: { grid: { display: false } }
            },
            plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => `Revenue: Rs.${ctx.parsed.y.toLocaleString('en-IN')}` } } }
        }
    });
}

function renderTopChart(labels, data) {
    const ctx = document.getElementById('topChart');
    if (topChartInst) topChartInst.destroy();

    topChartInst = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Units Sold',
                data,
                backgroundColor: 'rgba(16, 185, 129, 0.7)',
                borderRadius: 6,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            indexAxis: 'y',
            scales: {
                x: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.04)' } },
                y: { grid: { display: false } }
            },
            plugins: { legend: { display: false } }
        }
    });
}

function renderCategoryChart(categories) {
    const ctx = document.getElementById('categoryChart');
    if (categoryChartInst) categoryChartInst.destroy();

    const colors = [
        '#2563eb', '#10b981', '#f97316', '#f59e0b', '#ef4444',
        '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#64748b',
        '#d946ef', '#14b8a6'
    ];

    categoryChartInst = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: categories.map(c => c.category),
            datasets: [{
                data: categories.map(c => c.revenue),
                backgroundColor: colors.slice(0, categories.length),
                borderWidth: 0,
                hoverOffset: 6,
            }]
        },
        options: {
            responsive: true,
            cutout: '55%',
            plugins: {
                legend: { position: 'bottom', labels: { padding: 12, usePointStyle: true, pointStyle: 'circle', font: { size: 11 } } },
                tooltip: { callbacks: { label: ctx => `${ctx.label}: Rs.${ctx.parsed.toLocaleString('en-IN')}` } }
            }
        }
    });
}
