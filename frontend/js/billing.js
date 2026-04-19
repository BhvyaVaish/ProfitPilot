let products = [];
let cart = [];

const GST_RATES = {
    // 0% Exempt (Essential / Educational)
    fresh_produce: 0, milk: 0, grains: 0, stationery: 0,
    // 5% Everyday consumer goods
    grocery: 0.05, fmcg: 0.05, packaged_food: 0.05,
    sweets: 0.05, dairy: 0.05, snacks: 0.05,
    personal_care: 0.05, kitchenware: 0.05,
    colours: 0.05, clothing: 0.05,
    // 18% Standard rate
    general: 0.18, electronics: 0.18, lights: 0.18,
    gifts: 0.18, hardware: 0.18, decorations: 0.18, cosmetics: 0.18,
    // 40% Sin / Luxury
    drinks: 0.40, tobacco: 0.40, luxury: 0.40
};

// -- AUTH GUARD ---------------------------------------------------------
function _requireBillingLogin(action) {
    if (!window._isLoggedIn) {
        showToast(`Please sign in to ${action}. Redirecting to login…`, 'error');
        setTimeout(() => { window.location.href = '/auth'; }, 1500);
        return false;
    }
    return true;
}

// Wait for auth-guard to finish resolving before loading products.
// auth-guard.js fires 'auth-ready' on window when onAuthStateChanged resolves.
function _initBilling() {
    loadProducts();
    loadRecentBills();
    document.getElementById('product-search').addEventListener('input', handleSearch);
    document.getElementById('generate-bill-btn').addEventListener('click', () => {
        if (_requireBillingLogin('generate a bill')) generateBill();
    });
    _initBillSearch();
}

// auth-guard fires 'auth-ready' — if it already fired before this script ran,
// _authReady will be true (set below).
if (window._authReady) {
    document.addEventListener('DOMContentLoaded', _initBilling);
} else {
    window.addEventListener('auth-ready', _initBilling, { once: true });
}

async function loadProducts() {
    const data = await apiCall('/api/inventory');
    products = data.products;
}

function handleSearch(e) {
    if (!_requireBillingLogin('search products for billing')) {
        e.target.value = '';
        return;
    }
    const term = e.target.value.toLowerCase();
    const suggestions = document.getElementById('search-suggestions');
    suggestions.innerHTML = '';

    if (!term) return;

    const matches = products.filter(p => p.name.toLowerCase().includes(term));

    matches.forEach(p => {
        const div = document.createElement('div');
        div.className = 'search-item';
        const stockColor = p.stock === 0 ? 'var(--accent-red)' : p.stock < 10 ? 'var(--accent-yellow)' : 'var(--text-muted)';
        div.innerHTML = `<strong>${p.name}</strong> - Rs.${p.price} <small style="color:${stockColor};">(Stock: ${p.stock})</small>`;

        div.addEventListener('click', () => {
            addToCart(p);
            e.target.value = '';
            suggestions.innerHTML = '';
        });

        suggestions.appendChild(div);
    });
}

function addToCart(product) {
    if (!_requireBillingLogin('add items to cart')) return;
    product.id = product.id || product.product_id;
    const existing = cart.find(i => i.id === product.id);
    if (existing) {
        if (existing.quantity < product.stock) {
            existing.quantity++;
        } else {
            showToast(`Only ${product.stock} units available for ${product.name}`);
        }
    } else {
        if (product.stock > 0) {
            cart.push({ ...product, quantity: 1, product_id: product.id });
        } else {
            showToast(`${product.name} is out of stock`);
            return;
        }
    }
    renderCart();
}

function updateQuantity(id, qty) {
    const item = cart.find(i => i.product_id === id);
    if (item) {
        const prod = products.find(p => p.id === id);
        if (qty > prod.stock) {
            showToast(`Only ${prod.stock} units available`);
            item.quantity = prod.stock;
        } else if (qty < 1) {
            cart = cart.filter(i => i.product_id !== id);
        } else {
            item.quantity = parseInt(qty);
        }
    }
    renderCart();
}

function removeFromCart(id) {
    cart = cart.filter(i => i.product_id !== id);
    renderCart();
}

function renderCart() {
    const tbody = document.getElementById('cart-body');
    tbody.innerHTML = '';

    let total = 0;

    if (cart.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-muted text-center" style="padding:24px;">Search and add products above to start billing.</td></tr>';
        document.getElementById('cart-total').innerText = 'Rs.0';
        document.getElementById('generate-bill-btn').disabled = true;
        return;
    }

    cart.forEach(item => {
        const itemTotal = item.quantity * item.price;
        total += itemTotal;

        tbody.innerHTML += `
            <tr>
                <td><strong>${item.name}</strong></td>
                <td>Rs.${item.price}</td>
                <td>
                    <input type="number" class="input-control" style="width: 68px; padding: 5px 8px; text-align:center;" value="${item.quantity}" min="1" max="${item.stock}" onchange="updateQuantity(${item.product_id}, this.value)">
                </td>
                <td style="font-weight:600;">Rs.${itemTotal}</td>
                <td><button class="btn btn-danger btn-sm" onclick="removeFromCart(${item.product_id})" style="padding:3px 8px;">X</button></td>
            </tr>
        `;
    });

    document.getElementById('cart-total').innerText = formatCurrency(total);
    document.getElementById('generate-bill-btn').disabled = false;

    // Low stock warning
    const warnDiv = document.getElementById('low-stock-warning');
    if (warnDiv) {
        const warnings = [];
        cart.forEach(item => {
            const prod = products.find(p => p.id === item.product_id);
            if (prod) {
                const remainAfter = prod.stock - item.quantity;
                if (remainAfter <= 0) {
                    warnings.push(`<strong>${item.name}</strong> will be <span style="color:var(--accent-red);font-weight:700;">OUT OF STOCK</span> after this bill`);
                } else if (remainAfter < 5) {
                    warnings.push(`<strong>${item.name}</strong> will have only <span style="color:var(--accent-yellow);font-weight:700;">${remainAfter} units</span> left`);
                }
            }
        });
        if (warnings.length > 0) {
            warnDiv.innerHTML = `<div style="background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.3); border-radius:var(--radius-sm); padding:10px 14px; margin-top:12px; font-size:0.85rem;">
                <div style="font-weight:600; color:var(--accent-yellow); margin-bottom:6px;">⚠ Stock Warning</div>
                ${warnings.map(w => `<div style="margin:3px 0; color:var(--text-secondary);">${w}</div>`).join('')}
            </div>`;
            warnDiv.style.display = 'block';
        } else {
            warnDiv.style.display = 'none';
            warnDiv.innerHTML = '';
        }
    }
}

async function generateBill() {
    const customerName = document.getElementById('customer-name').value.trim();
    const payload = {
        items: cart.map(i => ({ product_id: i.product_id, quantity: i.quantity })),
        customer_name: customerName
    };

    try {
        const btn = document.getElementById('generate-bill-btn');
        btn.innerHTML = '<div class="spinner"></div>';
        btn.disabled = true;

        const res = await apiCall('/api/bill', 'POST', payload);

        showToast('Bill Generated Successfully!', 'success');
        cart = [];
        renderCart();
        document.getElementById('customer-name').value = '';
        await loadProducts();

        showInvoiceModal(res.bill);
        loadRecentBills();

        btn.innerHTML = 'Generate Bill';
    } catch (e) {
        document.getElementById('generate-bill-btn').innerHTML = 'Generate Bill';
        document.getElementById('generate-bill-btn').disabled = false;
    }
}

function showInvoiceModal(bill) {
    // Get org name from user profile (set by auth-guard)
    const orgName = (window._userProfile && window._userProfile.business_name)
        ? window._userProfile.business_name
        : 'Your Business';

    document.getElementById('modal-overlay').classList.add('active');
    document.getElementById('inv-number').innerText = bill.bill_number;
    document.getElementById('inv-date').innerText = new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
    document.getElementById('inv-customer').innerText = bill.customer_name || 'Walk-in Customer';
    document.getElementById('inv-org-name').innerText = orgName;

    const itemsDiv = document.getElementById('inv-items');
    itemsDiv.innerHTML = '';

    let subtotal = bill.subtotal;
    let totalGst = bill.gst_amount;

    bill.items.forEach(i => {
        const lineTotal = i.price * i.quantity;
        itemsDiv.innerHTML += `
            <div class="flex-between mb-1" style="font-family: var(--font-body); font-size:0.9rem;">
                <span>${i.name} x${i.quantity}</span>
                <span>Rs.${lineTotal.toFixed(2)}</span>
            </div>
        `;
    });

    // Check GST override
    const manualGstInput = document.getElementById('manual-gst').value.trim();
    if (manualGstInput !== '' && !isNaN(manualGstInput)) {
        const overrideRate = parseFloat(manualGstInput) / 100;
        totalGst = subtotal * overrideRate;
        document.getElementById('lbl-cgst').innerText = `CGST (${(parseFloat(manualGstInput) / 2).toFixed(1)}%)`;
        document.getElementById('lbl-sgst').innerText = `SGST (${(parseFloat(manualGstInput) / 2).toFixed(1)}%)`;
    } else {
        document.getElementById('lbl-cgst').innerText = `CGST (Category-wise)`;
        document.getElementById('lbl-sgst').innerText = `SGST (Category-wise)`;
    }

    const cgst = totalGst / 2;
    const sgst = totalGst / 2;
    const grandTotal = subtotal + totalGst;

    document.getElementById('inv-subtotal').innerText = `Rs.${subtotal.toFixed(2)}`;
    document.getElementById('inv-cgst').innerText     = `Rs.${cgst.toFixed(2)}`;
    document.getElementById('inv-sgst').innerText     = `Rs.${sgst.toFixed(2)}`;
    document.getElementById('inv-total').innerText    = `Rs.${grandTotal.toFixed(2)}`;

    // Profit estimate
    const profitDiv = document.getElementById('inv-profit-estimate');
    if (profitDiv) {
        const estimatedCost = bill.items.reduce((sum, i) => {
            const prod = products.find(p => p.id === i.product_id);
            const costPerUnit = (prod && prod.effective_cost) ? prod.effective_cost : (i.price * 0.7);
            return sum + (costPerUnit * i.quantity);
        }, 0);
        const estimatedProfit = subtotal - estimatedCost;
        const marginPct = subtotal > 0 ? ((estimatedProfit / subtotal) * 100).toFixed(1) : 0;
        profitDiv.innerHTML = `
            <div style="border-top:1px dashed var(--border); margin-top:12px; padding-top:10px;">
                <div class="flex-between mb-1" style="font-size:0.85rem;">
                    <span style="color:var(--text-muted);">Est. Cost</span>
                    <span>Rs.${estimatedCost.toFixed(2)}</span>
                </div>
                <div class="flex-between" style="font-size:0.95rem; font-weight:700;">
                    <span style="color:var(--accent-green);">Est. Profit (${marginPct}%)</span>
                    <span style="color:var(--accent-green);">Rs.${estimatedProfit.toFixed(2)}</span>
                </div>
            </div>
        `;
    }
}

function closeInvoice() {
    document.getElementById('modal-overlay').classList.remove('active');
}

function printBill() {
    if (!_requireBillingLogin('print/download the bill')) return;
    window.print();
}

async function loadRecentBills() {
    try {
        const res = await apiCall('/api/bills?limit=10');
        _renderBillList(res.bills || [], document.getElementById('recent-bills'));
    } catch (e) {
        console.error('Failed to load recent bills', e);
    }
}

function _renderBillList(bills, container) {
    container.innerHTML = '';
    if (!bills || bills.length === 0) {
        container.innerHTML = '<span class="text-muted" style="font-size:0.85rem;">No bills found.</span>';
        return;
    }

    bills.forEach(b => {
        const items = b.items || [];
        const itemCount = items.reduce((sum, i) => sum + (i.quantity || 0), 0);
        const div = document.createElement('div');
        div.className = 'recent-bill-item';
        div.style.cursor = 'pointer';
        div.onclick = () => viewBillDetails(b);
        div.innerHTML = `
            <div>
                <strong style="font-size:0.88rem; color:var(--text-primary);">${b.bill_number}</strong>
                ${b.customer_name ? `<span class="text-muted"> - ${b.customer_name}</span>` : ''}
                <div class="text-muted" style="font-size:0.78rem;">${b.created_at} | ${itemCount} items</div>
            </div>
            <div style="font-weight:700; color:var(--accent-blue);">Rs.${Number(b.total).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
        `;
        container.appendChild(div);
    });
}

function viewBillDetails(bill) {
    showInvoiceModal(bill);
}

// Bill search with debounce
let _billSearchTimer = null;
function _initBillSearch() {
    const input = document.getElementById('bill-search-input');
    if (!input) return;
    input.addEventListener('input', (e) => {
        clearTimeout(_billSearchTimer);
        _billSearchTimer = setTimeout(async () => {
            const q = e.target.value.trim();
            if (!q) {
                loadRecentBills();
                return;
            }
            try {
                const res = await apiCall(`/api/bills/search?q=${encodeURIComponent(q)}`);
                _renderBillList(res.bills || [], document.getElementById('recent-bills'));
            } catch (err) {
                console.error('Bill search failed', err);
            }
        }, 350);
    });
}

