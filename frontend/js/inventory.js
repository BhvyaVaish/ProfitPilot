let inventoryData = [];
let activeFilter = 'all';

document.addEventListener('DOMContentLoaded', () => {
    loadInventory();
    document.getElementById('search-inv').addEventListener('input', applyFilters);
    document.getElementById('add-form').addEventListener('submit', handleAddProduct);
});

// ─── DATA LOADING ─────────────────────────────────────────────────────────
async function loadInventory() {
    try {
        const res = await apiCall('/api/inventory');
        inventoryData = res.products;
        renderInventory(inventoryData);
        updateStats(inventoryData);
        populateRestockDropdown(inventoryData);
    } catch(e) {
        console.error('Inventory load failed', e);
    }
}

// ─── RENDERING ────────────────────────────────────────────────────────────
function renderInventory(data) {
    const tbody = document.getElementById('inventory-body');
    tbody.innerHTML = '';

    if(!data || data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:var(--text-muted); padding:32px;">No products found.</td></tr>';
        return;
    }

    data.forEach(p => {
        let pillClass, pillLabel;
        if (p.status === 'Out of Stock') {
            pillClass = 'status-out';
            pillLabel = '● Out of Stock';
        } else if (p.status === 'Low') {
            pillClass = 'status-low';
            pillLabel = '● Low';
        } else {
            pillClass = 'status-ok';
            pillLabel = '● OK';
        }

        tbody.innerHTML += `
            <tr>
                <td><strong>${escHtml(p.name)}</strong></td>
                <td><span class="badge badge-yellow">${escHtml(p.category)}</span></td>
                <td style="text-align:center; font-size:1.05rem; font-weight:700;">${p.stock}</td>
                <td>₹${parseFloat(p.price).toFixed(2)}</td>
                <td style="text-align:center;"><span class="status-pill ${pillClass}">${pillLabel}</span></td>
                <td style="text-align:center; display:flex; gap:6px; justify-content:center;">
                    <button class="btn btn-primary tbl-action-btn" onclick="openRestockModal(${p.id})">Restock</button>
                    <button class="btn tbl-action-btn" onclick="openEditModal(${p.id}, '${escJs(p.name)}', ${p.price}, ${p.stock})">Edit</button>
                    <button class="btn btn-danger tbl-action-btn" onclick="deleteProduct(${p.id}, '${escJs(p.name)}')">Delete</button>
                </td>
            </tr>
        `;
    });
}

function updateStats(data) {
    document.getElementById('stat-total').innerText = data.length;
    document.getElementById('stat-low').innerText  = data.filter(p => p.status === 'Low').length;
    document.getElementById('stat-out').innerText  = data.filter(p => p.status === 'Out of Stock').length;
}

function populateRestockDropdown(data) {
    const sel = document.getElementById('restock-select');
    sel.innerHTML = data.map(p => `<option value="${p.id}">[${p.stock} units] ${escHtml(p.name)}</option>`).join('');
}

// ─── FILTERING ────────────────────────────────────────────────────────────
function setFilter(filter, chipEl) {
    activeFilter = filter;
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    chipEl.classList.add('active');
    applyFilters();
}

function applyFilters() {
    const term = document.getElementById('search-inv').value.toLowerCase().trim();

    let filtered = inventoryData;

    if (activeFilter === 'low')  filtered = filtered.filter(p => p.status === 'Low');
    if (activeFilter === 'out')  filtered = filtered.filter(p => p.status === 'Out of Stock');
    if (activeFilter === 'ok')   filtered = filtered.filter(p => p.status === 'OK');

    if (term) {
        filtered = filtered.filter(p => p.name.toLowerCase().includes(term) || p.category.toLowerCase().includes(term));
    }

    renderInventory(filtered);
}

// ─── ADD PRODUCT MODAL ────────────────────────────────────────────────────
function openAddModal() {
    document.getElementById('add-modal-overlay').classList.add('active');
    document.getElementById('add-error').style.display = 'none';
}
function closeAddModal() {
    document.getElementById('add-modal-overlay').classList.remove('active');
    document.getElementById('add-form').reset();
}

async function handleAddProduct(e) {
    e.preventDefault();
    const errBox = document.getElementById('add-error');
    errBox.style.display = 'none';

    const name  = document.getElementById('p-name').value.trim();
    const price = parseFloat(document.getElementById('p-price').value);
    const stock = parseInt(document.getElementById('p-stock').value);

    if(!name) { showErr(errBox, 'Product name cannot be empty.'); return; }
    if(price <= 0 || isNaN(price)) { showErr(errBox, 'Price must be greater than 0.'); return; }
    if(stock < 0 || isNaN(stock)) { showErr(errBox, 'Stock cannot be negative.'); return; }

    const payload = {
        name,
        category: document.getElementById('p-category').value,
        price,
        stock
    };

    try {
        const res = await apiCall('/api/inventory', 'POST', payload);
        if(res.error) { showErr(errBox, res.error); return; }
        showToast(`✅ "${name}" added to inventory!`, 'success');
        closeAddModal();
        await loadInventory();
    } catch(err) {
        showErr(errBox, err.message || 'Failed to add product.');
    }
}

// ─── ADD STOCK (RESTOCK) MODAL ────────────────────────────────────────────
function openRestockModal(preselectId = null) {
    document.getElementById('restock-modal-overlay').classList.add('active');
    document.getElementById('restock-error').style.display = 'none';
    document.getElementById('restock-qty').value = '';
    if (preselectId) {
        document.getElementById('restock-select').value = preselectId;
    }
}
function closeRestockModal() {
    document.getElementById('restock-modal-overlay').classList.remove('active');
}

async function handleAddStock() {
    const errBox = document.getElementById('restock-error');
    errBox.style.display = 'none';

    const productId = parseInt(document.getElementById('restock-select').value);
    const qty = parseInt(document.getElementById('restock-qty').value);

    if(!productId) { showErr(errBox, 'Please select a product.'); return; }
    if(!qty || qty <= 0 || isNaN(qty)) { showErr(errBox, 'Quantity must be a positive number.'); return; }

    try {
        const res = await apiCall(`/api/inventory/${productId}/add-stock`, 'POST', { added_quantity: qty });
        if(res.error) { showErr(errBox, res.error); return; }
        showToast(`✅ Added ${qty} units. New stock: ${res.new_stock}`, 'success');
        closeRestockModal();
        await loadInventory();
    } catch(err) {
        showErr(errBox, err.message || 'Failed to update stock.');
    }
}

// ─── EDIT PRODUCT MODAL ───────────────────────────────────────────────────
function openEditModal(id, name, price, stock) {
    document.getElementById('edit-id').value = id;
    document.getElementById('edit-name').value = name;
    document.getElementById('edit-price').value = price;
    if (stock !== undefined) {
        document.getElementById('edit-stock').value = stock;
    }
    document.getElementById('edit-error').style.display = 'none';
    document.getElementById('edit-modal-overlay').classList.add('active');
}
function closeEditModal() {
    document.getElementById('edit-modal-overlay').classList.remove('active');
}

async function handleEditProduct() {
    const errBox = document.getElementById('edit-error');
    errBox.style.display = 'none';

    const id    = document.getElementById('edit-id').value;
    const name  = document.getElementById('edit-name').value.trim();
    const price = parseFloat(document.getElementById('edit-price').value);
    const stock = parseInt(document.getElementById('edit-stock').value);

    if(!name) { showErr(errBox, 'Name cannot be empty.'); return; }
    if(price <= 0 || isNaN(price)) { showErr(errBox, 'Price must be > 0.'); return; }
    if(stock < 0 || isNaN(stock)) { showErr(errBox, 'Stock cannot be negative.'); return; }

    try {
        const res = await apiCall(`/api/inventory/${id}`, 'PUT', { name, price, stock });
        if(res.error) { showErr(errBox, res.error); return; }
        showToast('✅ Product updated.', 'success');
        closeEditModal();
        await loadInventory();
    } catch(err) {
        showErr(errBox, err.message || 'Update failed.');
    }
}

// ─── DELETE PRODUCT ───────────────────────────────────────────────────────
async function deleteProduct(id, name) {
    if(!confirm(`Delete "${name}"?\n\nNote: Products with sales history cannot be deleted to protect your reports.`)) return;

    try {
        const res = await apiCall(`/api/inventory/${id}`, 'DELETE');
        if(res.error) {
            showToast(`⚠️ ${res.error}`, 'error');
            return;
        }
        showToast(`🗑️ "${name}" deleted.`, 'success');
        await loadInventory();
    } catch(err) {
        showToast(`⚠️ ${err.message || 'Delete failed.'}`, 'error');
    }
}

// ─── HELPERS ──────────────────────────────────────────────────────────────
function showErr(box, msg) {
    box.textContent = msg;
    box.style.display = 'block';
}

function escHtml(str) {
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function escJs(str) {
    return String(str).replace(/'/g, "\\'").replace(/\\/g, '\\\\');
}
