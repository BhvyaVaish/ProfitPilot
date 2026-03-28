let salesChartInst = null;
let topChartInst = null;

document.addEventListener('DOMContentLoaded', () => {
    loadFullDashboard();
});

async function loadFullDashboard() {
    try {
        const data = await apiCall('/api/dashboard/full');
        
        // 1 & 2. Render Charts
        renderSalesChart(data.sales_graph.labels, data.sales_graph.revenue);
        renderTopChart(data.catalog_performance.map(t => t.name), data.catalog_performance.map(t => t.total_qty));
        
        // 3. Smart Procurement Table
        const restockBody = document.getElementById('restock-body');
        restockBody.innerHTML = '';
        if(data.smart_procurement.length === 0) {
            restockBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Stock levels perfectly optimized.</td></tr>';
        } else {
            data.smart_procurement.forEach(s => {
                restockBody.innerHTML += `
                    <tr>
                        <td>${s.name}</td>
                        <td>${s.current_stock}</td>
                        <td>${s.predicted_demand}</td>
                        <td class="text-green">+${s.suggested_restock}</td>
                    </tr>
                `;
            });
        }
        
        // 4. Dead Stock
        const deadBody = document.getElementById('dead-stock-body');
        deadBody.innerHTML = '';
        if(data.dead_stock.length === 0) {
            deadBody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">No dead stock found. Great efficiency!</td></tr>';
        } else {
            data.dead_stock.forEach(d => {
                deadBody.innerHTML += `
                    <tr>
                        <td>${d.name}</td>
                        <td>${d.stock}</td>
                        <td class="text-muted">${d.days_since}</td>
                    </tr>
                `;
            });
        }
        
        // 5. High Potential Items
        const hpotContainer = document.getElementById('high-potential-panel');
        hpotContainer.innerHTML = '';
        if(data.high_potential.length === 0) {
            hpotContainer.innerHTML = '<span class="text-muted">No rapid-growth items detected currently.</span>';
        } else {
            data.high_potential.slice(0, 3).forEach(h => {
                hpotContainer.innerHTML += `
                    <div style="background: rgba(59, 130, 246, 0.1); padding: 8px 12px; border-radius: var(--radius);">
                        <strong>${h.name}</strong>
                    </div>
                `;
            });
        }
        
        // 6. Alert Panel
        const alertPanel = document.getElementById('alert-panel');
        alertPanel.innerHTML = '';
        if(data.alerts.length === 0) {
            alertPanel.innerHTML = '<span class="text-muted">No critical alerts.</span>';
        } else {
            data.alerts.forEach(a => {
                alertPanel.innerHTML += `
                    <div style="background: rgba(239, 68, 68, 0.1); padding: 8px 12px; border-radius: var(--radius); border-left: 2px solid var(--accent-orange);">
                        <strong style="font-size: 0.9em">${a.message}</strong>
                    </div>
                `;
            });
        }
        
        // 7. Festival Widget
        const festContainer = document.getElementById('festival-widget');
        if(data.festival_widget && data.festival_widget.upcoming) {
            festContainer.innerHTML = `
                <div style="background: rgba(52, 211, 153, 0.1); padding: 8px 12px; border-radius: var(--radius);">
                    <div style="font-size: 0.8em" class="text-muted">NEXT FESTIVAL</div>
                    <strong>🗓️ ${data.festival_widget.upcoming}</strong>
                </div>
                <div style="background: rgba(52, 211, 153, 0.1); padding: 8px 12px; border-radius: var(--radius); margin-top: 8px;">
                    <div style="font-size: 0.8em" class="text-muted">DEMAND IMPACT</div>
                    <strong>📈 ${data.festival_widget.suggestion}</strong>
                </div>
            `;
        }
        
    } catch(e) {
        console.error("Dashboard failed to load", e);
    }
}

function renderSalesChart(labels, data) {
    const ctx = document.getElementById('salesChart');
    if(salesChartInst) salesChartInst.destroy();
    
    Chart.defaults.color = "rgba(255,255,255,0.6)";
    Chart.defaults.font.family = "'JetBrains Mono', monospace";
    
    salesChartInst = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Revenue (₹)',
                data,
                borderColor: '#d95f36',
                backgroundColor: 'rgba(217, 95, 54, 0.1)',
                tension: 0.4,
                fill: true,
                borderWidth: 2,
                pointBackgroundColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } },
                x: { grid: { display: false } }
            },
            plugins: { legend: { display: false } }
        }
    });
}

function renderTopChart(labels, data) {
    const ctx = document.getElementById('topChart');
    if(topChartInst) topChartInst.destroy();
    
    topChartInst = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Units Sold',
                data,
                backgroundColor: 'rgba(52, 211, 153, 0.8)',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            indexAxis: 'y',
            scales: {
                x: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { grid: { display: false } }
            },
            plugins: { legend: { display: false } }
        }
    });
}
