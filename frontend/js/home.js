document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('current-date').innerText = new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    loadHomeSummary();
});

async function loadHomeSummary() {
    try {
        const data = await apiCall('/api/home/summary');
        
        // Quick Summary
        document.getElementById('stat-sales-today').innerText = `₹${data.quick_summary.today_sales}`;
        document.getElementById('stat-products').innerText = data.quick_summary.total_products;
        document.getElementById('stat-low-stock').innerText = data.quick_summary.low_stock_count;
        document.getElementById('stat-out-stock').innerText = data.quick_summary.out_of_stock_count;
        
        // AI Priority Actions
        const paContainer = document.getElementById('priority-actions');
        paContainer.innerHTML = '';
        if (!data.priority_actions || data.priority_actions.length === 0) {
            paContainer.innerHTML = '<div class="text-muted">No urgent actions required.</div>';
        } else {
            data.priority_actions.forEach(action => {
                let icon = '';
                if(action.type === 'Low Stock' || action.type === 'Critical Stock') icon = '⚠️';
                else if(action.type === 'High Demand') icon = '📈';
                else if(action.type === 'Dead Stock') icon = '📉';
                else icon = '💡';
                
                paContainer.innerHTML += `
                    <div style="background: rgba(255,255,255,0.03); padding: 12px; border-radius: var(--radius); border-left: 3px solid var(--accent-orange);">
                        <strong style="color: #fff;">${icon} ${action.message}</strong>
                    </div>
                `;
            });
        }
        
        // Festival Insights
        const fiContainer = document.getElementById('festival-insights');
        if(data.festival_insights) {
            fiContainer.innerHTML = `
                <div style="padding: 12px; background: rgba(52, 211, 153, 0.1); border-radius: var(--radius);">
                    <strong>🗓️ ${data.festival_insights.upcoming}</strong>
                </div>
                <div style="padding: 12px; background: rgba(52, 211, 153, 0.1); border-radius: var(--radius);">
                    <strong>💡 ${data.festival_insights.suggestion}</strong>
                </div>
            `;
        }
        
        // Mini Insights
        const miContainer = document.getElementById('mini-insights');
        if(data.mini_insights) {
            miContainer.innerHTML = `
                <div style="padding: 12px; background: rgba(59, 130, 246, 0.1); border-radius: var(--radius);">
                    <strong>🏆 Top Selling:</strong> ${data.mini_insights.top_selling}
                </div>
                <div style="padding: 12px; background: rgba(59, 130, 246, 0.1); border-radius: var(--radius);">
                    <strong>⏳ Least Selling:</strong> ${data.mini_insights.least_selling}
                </div>
                <div style="padding: 12px; background: rgba(59, 130, 246, 0.1); border-radius: var(--radius);">
                    <strong>🔥 High Potential:</strong> ${data.mini_insights.high_potential}
                </div>
            `;
        }
        
    } catch(e) {
        console.error("Failed to load home summary", e);
    }
}
