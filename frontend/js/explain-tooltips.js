/**
 * explain-tooltips.js — Global contextual tooltip system for jargon explanations.
 * Usage: Add data-explain="term" attribute and an ℹ icon to any element.
 * On click, shows a floating card with a simple, jargon-free explanation.
 */
(function() {
  const EXPLANATIONS = {
    'gst': 'GST (Goods & Services Tax) is a single tax on selling goods in India. Different items have different rates — essentials like milk are 0%, grocery is 5%, electronics is 18%.',
    'cgst': 'CGST is the Central Government\'s share of GST. If total GST is 18%, CGST = 9% (half goes to Centre).',
    'sgst': 'SGST is the State Government\'s share of GST. If total GST is 18%, SGST = 9% (half stays in your state).',
    'igst': 'IGST applies when selling to another state. Instead of CGST+SGST split, full GST goes as IGST.',
    'section-44ad': 'Section 44AD lets small businesses (under ₹2-3 Cr turnover) file taxes easily. Profit is assumed as 6% (digital) or 8% (cash) of turnover — no detailed bookkeeping needed.',
    'composition': 'GST Composition Scheme: Pay a flat 1% of turnover as tax instead of complex GST rates. File quarterly instead of monthly. But you can\'t collect GST from buyers or claim input credits.',
    'income-tax': 'Income Tax is paid annually on your business profit. India uses tax slabs — the more you earn, the higher the rate. Many small businesses pay zero tax thanks to the ₹12L rebate.',
    'rebate-87a': 'Section 87A gives a tax rebate if your income is under ₹12 Lakh (new regime). This effectively makes your income tax ZERO for most small businesses.',
    'new-regime': 'New Tax Regime has lower rates but no deductions (no 80C, HRA, etc.). Usually better for small businesses without big investments.',
    'old-regime': 'Old Tax Regime has higher rates but allows deductions (80C up to ₹1.5L, health insurance, HRA). Better if you have lots of deductions.',
    'itc': 'Input Tax Credit (ITC) means you can subtract the GST you paid on purchases from the GST you collect on sales. You only pay the difference.',
    'tds': 'TDS (Tax Deducted at Source) — when a company pays you, they deduct some tax upfront and send it to the government. You can claim it back in your ITR.',
    'msme': 'MSME = Micro, Small & Medium Enterprise. Register on Udyam portal for benefits like priority lending, lower interest rates, and government scheme access.',
    'profit-margin': 'Profit Margin = (Selling Price - Cost Price) / Selling Price × 100. A 30% margin means you keep ₹30 for every ₹100 sold.',
    'dead-stock': 'Dead Stock = products sitting in your warehouse that haven\'t sold recently. They tie up your money. Consider discounts or promotions to move them.',
    'restock': 'Smart Restock suggestions are based on your sales velocity — how fast items sell. We predict demand and add a 15% safety buffer.',
    'turnover': 'Turnover = Total sales revenue (before expenses). It\'s the total money that came in from selling goods/services.',
    'cess': 'Health & Education Cess is an extra 4% charged on your income tax amount. If tax is ₹10,000, you pay ₹10,400 total.',
    'cost-ratio': 'Cost Ratio is how much of your selling price is your cost. Default is 70% (meaning 30% profit margin). You can set custom cost price per product for accuracy.',
    'stock-availability': 'Stock Availability calculates the percentage of your catalog that is currently in stock. A low score means you are missing potential sales due to empty shelves.',
    'sales-momentum': 'Sales Momentum measures how fast your inventory is moving. It looks at the number of unique products sold recently compared to your total catalog size.',
    'capital-efficiency': 'Capital Efficiency tracks Dead Stock. It penalizes your score if you have products that haven\'t sold a single unit in the last 30 days, as they tie up your cash.',
    'product-diversity': 'Product Diversity ensures you aren\'t over-reliant on just 1 or 2 categories. Selling across multiple categories (like Grocery, Dairy) improves business stability.',
    'revenue-consistency': 'Revenue Consistency checks if your daily sales are steady. Frequent days with zero sales will lower this score, while daily consistent sales maximize it.',
  };

  // Create tooltip container
  const tooltip = document.createElement('div');
  tooltip.id = 'explain-tooltip';
  tooltip.style.cssText = `
    display:none; position:fixed; z-index:9999; max-width:340px;
    background:#fff; border:1px solid rgba(37,99,235,0.15);
    border-radius:12px; padding:16px 18px; font-size:0.88rem;
    line-height:1.55; color:#334155; box-shadow:0 12px 40px rgba(0,0,0,0.12);
    font-family:var(--font-body,'DM Sans',sans-serif);
    animation: tooltipFadeIn 0.2s ease;
  `;
  document.body.appendChild(tooltip);

  // Add animation
  const style = document.createElement('style');
  style.textContent = `
    @keyframes tooltipFadeIn { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
    .explain-icon{display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;
      border-radius:50%;background:rgba(37,99,235,0.08);color:var(--accent-blue,#2563eb);
      cursor:pointer;font-size:11px;font-weight:700;margin-left:5px;vertical-align:middle;
      transition:all 0.2s;border:1px solid rgba(37,99,235,0.15);flex-shrink:0;}
    .explain-icon:hover{background:rgba(37,99,235,0.15);transform:scale(1.1);}
  `;
  document.head.appendChild(style);

  // Delegate click handler
  document.addEventListener('click', (e) => {
    const icon = e.target.closest('[data-explain]');
    if (icon) {
      e.stopPropagation();
      const key = icon.getAttribute('data-explain');
      const text = EXPLANATIONS[key] || 'No explanation available for this term.';
      const formattedTitle = key.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');

      tooltip.innerHTML = `
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
          <div style="width:24px;height:24px;border-radius:50%;background:rgba(37,99,235,0.1);display:flex;align-items:center;justify-content:center;">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
          </div>
          <strong style="font-size:0.82rem;color:#2563eb;text-transform:uppercase;letter-spacing:0.04em;">${formattedTitle}</strong>
        </div>
        <div>${text}</div>
      `;
      tooltip.style.display = 'block';

      // Position near the icon
      const rect = icon.getBoundingClientRect();
      let top = rect.bottom + 8;
      let left = rect.left - 100;

      // Keep on screen
      if (left < 10) left = 10;
      if (left + 350 > window.innerWidth) left = window.innerWidth - 360;
      if (top + 200 > window.innerHeight) top = rect.top - 200;

      tooltip.style.top = top + 'px';
      tooltip.style.left = left + 'px';
      return;
    }

    // Close on outside click
    if (!e.target.closest('#explain-tooltip')) {
      tooltip.style.display = 'none';
    }
  });
})();
