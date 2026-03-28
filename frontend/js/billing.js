let products = [];
let cart = [];

const GST_RATES = {
    sweets: 0.05, dairy: 0.05, clothing: 0.05,
    snacks: 0.12, lights: 0.12, general: 0.18,
    colors: 0.18, electronics: 0.18, gifts: 0.18, drinks: 0.28
};

document.addEventListener('DOMContentLoaded', async () => {
    await loadProducts();
    document.getElementById('product-search').addEventListener('input', handleSearch);
    document.getElementById('generate-bill-btn').addEventListener('click', generateBill);
});

async function loadProducts() {
    const data = await apiCall('/api/inventory');
    products = data.products;
}

function handleSearch(e) {
    const term = e.target.value.toLowerCase();
    const suggestions = document.getElementById('search-suggestions');
    suggestions.innerHTML = '';
    
    if(!term) return;
    
    const matches = products.filter(p => p.name.toLowerCase().includes(term));
    
    matches.forEach(p => {
        const div = document.createElement('div');
        div.className = 'search-item';
        div.style.padding = '8px';
        div.style.cursor = 'pointer';
        div.style.borderBottom = '1px solid var(--border)';
        div.innerHTML = `<strong>${p.name}</strong> - ₹${p.price} <small class="text-muted">(Stock: ${p.stock})</small>`;
        
        div.addEventListener('click', () => {
            addToCart(p);
            e.target.value = '';
            suggestions.innerHTML = '';
        });
        
        suggestions.appendChild(div);
    });
}

function addToCart(product) {
    product.id = product.id || product.product_id;
    const existing = cart.find(i => i.id === product.id);
    if(existing) {
        if(existing.quantity < product.stock) {
            existing.quantity++;
        } else {
            showToast(`Only ${product.stock} units available for ${product.name}`);
        }
    } else {
        if(product.stock > 0) {
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
    if(item) {
        const prod = products.find(p => p.id === id);
        if(qty > prod.stock) {
            showToast(`Only ${prod.stock} units available`);
            item.quantity = prod.stock;
        } else if(qty < 1) {
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
    
    cart.forEach(item => {
        const itemTotal = item.quantity * item.price;
        total += itemTotal;
        
        tbody.innerHTML += `
            <tr>
                <td>${item.name}</td>
                <td>₹${item.price}</td>
                <td>
                    <input type="number" class="input-control" style="width: 70px; padding: 4px;" value="${item.quantity}" onchange="updateQuantity(${item.product_id}, this.value)">
                </td>
                <td>₹${itemTotal}</td>
                <td><button class="btn btn-danger" style="padding: 4px 8px" onclick="removeFromCart(${item.product_id})">X</button></td>
            </tr>
        `;
    });
    
    document.getElementById('cart-total').innerText = `₹${total}`;
    document.getElementById('generate-bill-btn').disabled = cart.length === 0;
}

async function generateBill() {
    const payload = {
        items: cart.map(i => ({ product_id: i.product_id, quantity: i.quantity }))
    };
    
    try {
        const btn = document.getElementById('generate-bill-btn');
        btn.innerHTML = '<div class="spinner"></div>';
        btn.disabled = true;
        
        const res = await apiCall('/api/bill', 'POST', payload);
        
        showToast('Bill Generated Successfully!', 'success');
        cart = [];
        renderCart();
        loadProducts(); 
        
        showInvoiceModal(res.bill);
        
        btn.innerHTML = 'Generate Bill';
    } catch(e) {
        document.getElementById('generate-bill-btn').innerHTML = 'Generate Bill';
        document.getElementById('generate-bill-btn').disabled = false;
    }
}

function showInvoiceModal(bill) {
    const modal = document.getElementById('invoice-modal');
    document.getElementById('inv-number').innerText = bill.bill_number;
    document.getElementById('inv-date').innerText = new Date().toLocaleDateString();
    
    const itemsDiv = document.getElementById('inv-items');
    itemsDiv.innerHTML = '';
    
    let subtotal = 0;
    let totalCgst = 0;
    let totalSgst = 0;
    
    bill.items.forEach(i => {
        const lineTotal = i.price * i.quantity;
        subtotal += lineTotal;
        itemsDiv.innerHTML += `
            <div class="flex-between mb-1" style="font-family: var(--font-body)">
                <span>${i.name} x${i.quantity}</span>
                <span>₹${lineTotal.toFixed(2)}</span>
            </div>
        `;
        
        const prodMatch = products.find(p => p.id === i.product_id);
        const cat = prodMatch && prodMatch.category ? prodMatch.category.toLowerCase() : 'general';
        const rate = GST_RATES[cat] || 0.18; // Default to 18% if category not found or general
        
        const itemGst = lineTotal * rate;
        totalCgst += itemGst / 2;
        totalSgst += itemGst / 2;
    });
    
    // Calculate Taxes & Fees
    const manualGstInput = document.getElementById('manual-gst').value.trim();
    const manualFeeInput = document.getElementById('manual-fee').value.trim();
    
    let platformFee = manualFeeInput !== '' ? parseFloat(manualFeeInput) : 10.00;
    
    if (manualGstInput !== '' && !isNaN(manualGstInput)) {
        // Manual override based on subtotal
        const overrideRate = parseFloat(manualGstInput) / 100;
        const totalGst = subtotal * overrideRate;
        totalCgst = totalGst / 2;
        totalSgst = totalGst / 2;
        document.getElementById('lbl-cgst').innerText = `CGST (${(parseFloat(manualGstInput)/2).toFixed(1)}%)`;
        document.getElementById('lbl-sgst').innerText = `SGST (${(parseFloat(manualGstInput)/2).toFixed(1)}%)`;
    } else {
        document.getElementById('lbl-cgst').innerText = `CGST (Auto-Category)`;
        document.getElementById('lbl-sgst').innerText = `SGST (Auto-Category)`;
    }

    const grandTotal = subtotal + totalCgst + totalSgst + platformFee;
    
    document.getElementById('inv-subtotal').innerText = `₹${subtotal.toFixed(2)}`;
    document.getElementById('inv-cgst').innerText = `₹${totalCgst.toFixed(2)}`;
    document.getElementById('inv-sgst').innerText = `₹${totalSgst.toFixed(2)}`;
    document.getElementById('inv-fee').innerText = `₹${platformFee.toFixed(2)}`;
    document.getElementById('inv-total').innerText = `₹${grandTotal.toFixed(2)}`;
    
    document.getElementById('modal-overlay').classList.add('active');
}

function closeInvoice() {
    document.getElementById('modal-overlay').classList.remove('active');
}
