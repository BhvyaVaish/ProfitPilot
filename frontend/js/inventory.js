let inventoryData = [];
let activeFilter = 'all';

// -- AUTH GUARDS --------------------------------------------------------
// Every action requires login. Guest sees the page in read-only mode.
function _requireLogin(actionName) {
    if (!window._isLoggedIn) {
        showToast(`Please sign in to ${actionName}. Redirecting to login…`, 'error');
        setTimeout(() => { window.location.href = '/auth'; }, 1500);
        return false;
    }
    return true;
}

function guardedAddProduct()  { if (_requireLogin('add a product'))     openAddModal(); }
function guardedImport()      {
    if (_requireLogin('import products')) document.getElementById('csv-import-input').click();
}
function downloadTemplate()   { if (!_requireLogin('download the template')) return; _doDownloadTemplate(); }
function exportCSV()          { if (!_requireLogin('download inventory'))  return; _doExportCSV(); }

// Wait for auth token to be resolved before loading data.
// auth-guard.js dispatches 'auth-ready' after Firebase onAuthStateChanged resolves.
function _initInventory() {
    loadInventory();
    document.getElementById('search-inv').addEventListener('input', applyFilters);
    document.getElementById('add-form').addEventListener('submit', handleAddProduct);
}

if (window._authReady) {
    _initInventory();
} else {
    window.addEventListener('auth-ready', _initInventory, { once: true });
}

// -- DATA LOADING -------------------------------------------------------
async function loadInventory() {
    try {
        // Debug: Check current user
        console.log('[INVENTORY] Loading inventory for user:', window._isLoggedIn ? 'authenticated' : 'demo');
        if (window._authToken) {
            console.log('[INVENTORY] Auth token present:', window._authToken.substring(0, 20) + '...');
        }
        
        const res = await apiCall('/api/inventory');
        inventoryData = res.products;
        console.log('[INVENTORY] Loaded', inventoryData.length, 'products');
        renderInventory(inventoryData);
        updateStats(inventoryData);
        populateRestockDropdown(inventoryData);
    } catch (e) {
        console.error('[INVENTORY] Load failed:', e);
        // Clear spinner and show empty state on failure
        renderInventory([]);
    }
}

// -- RENDERING ----------------------------------------------------------
function renderInventory(data) {
    const tbody = document.getElementById('inventory-body');
    tbody.innerHTML = '';

    if (!data || data.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center" style="padding:48px 16px;">
                    <div style="background: rgba(37,99,235,0.03); max-width:400px; margin:0 auto; padding:24px; border-radius:8px; border:1px dashed rgba(37,99,235,0.2);">
                        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" stroke-width="2" style="margin-bottom:12px; opacity:0.8;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                        <h4 style="color:var(--text-primary); margin-bottom:6px;">Your Inventory is Empty</h4>
                        <p class="text-muted" style="font-size:0.9rem; margin-bottom:16px;">Upload a CSV file or add your first product manually to start tracking stock and generating insights.</p>
                        <button class="btn btn-primary" onclick="openAddModal()">+ Add Product</button>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    data.forEach(p => {
        let pillClass, pillLabel;
        if (p.status === 'Out of Stock') {
            pillClass = 'status-out';
            pillLabel = 'Out of Stock';
        } else if (p.status === 'Low') {
            pillClass = 'status-low';
            pillLabel = 'Low';
        } else {
            pillClass = 'status-ok';
            pillLabel = 'OK';
        }

        tbody.innerHTML += `
            <tr>
                <td><strong>${escHtml(p.name)}</strong></td>
                <td><span class="badge badge-yellow">${escHtml(p.category)}</span></td>
                <td style="text-align:center; font-size:1.05rem; font-weight:700;">${p.stock}</td>
                <td>Rs.${parseFloat(p.price).toFixed(2)}</td>
                <td style="text-align:center;"><span class="status-pill ${pillClass}">${pillLabel}</span></td>
                <td style="text-align:center; display:flex; gap:4px; justify-content:center; flex-wrap:wrap;">
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
    document.getElementById('stat-low').innerText = data.filter(p => p.status === 'Low').length;
    document.getElementById('stat-out').innerText = data.filter(p => p.status === 'Out of Stock').length;
}

function populateRestockDropdown(data) {
    const sel = document.getElementById('restock-select');
    sel.innerHTML = data.map(p => `<option value="${p.id}">[${p.stock} units] ${escHtml(p.name)}</option>`).join('');
}

// -- FILTERING ----------------------------------------------------------
function setFilter(filter, chipEl) {
    activeFilter = filter;
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    chipEl.classList.add('active');
    applyFilters();
}

function applyFilters() {
    const term = document.getElementById('search-inv').value.toLowerCase().trim();

    let filtered = inventoryData;

    if (activeFilter === 'low') filtered = filtered.filter(p => p.status === 'Low');
    if (activeFilter === 'out') filtered = filtered.filter(p => p.status === 'Out of Stock');
    if (activeFilter === 'ok') filtered = filtered.filter(p => p.status === 'OK');

    if (term) {
        filtered = filtered.filter(p => p.name.toLowerCase().includes(term) || p.category.toLowerCase().includes(term));
    }

    renderInventory(filtered);
}

// -- ADD PRODUCT MODAL --------------------------------------------------
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

    const name = document.getElementById('p-name').value.trim();
    const price = parseFloat(document.getElementById('p-price').value);
    const stock = parseInt(document.getElementById('p-stock').value);

    if (!name) { showErr(errBox, 'Product name cannot be empty.'); return; }
    if (price <= 0 || isNaN(price)) { showErr(errBox, 'Price must be greater than 0.'); return; }
    if (stock < 0 || isNaN(stock)) { showErr(errBox, 'Stock cannot be negative.'); return; }

    const payload = {
        name,
        category: document.getElementById('p-category').value,
        price,
        stock
    };

    try {
        const res = await apiCall('/api/inventory', 'POST', payload);
        if (res.error) { showErr(errBox, res.error); return; }
        showToast(`"${name}" added to inventory!`, 'success');
        closeAddModal();
        await loadInventory();
    } catch (err) {
        showErr(errBox, err.message || 'Failed to add product.');
    }
}

// -- ADD STOCK (RESTOCK) MODAL ------------------------------------------
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

    if (!productId) { showErr(errBox, 'Please select a product.'); return; }
    if (!qty || qty <= 0 || isNaN(qty)) { showErr(errBox, 'Quantity must be a positive number.'); return; }

    try {
        const res = await apiCall(`/api/inventory/${productId}/add-stock`, 'POST', { added_quantity: qty });
        if (res.error) { showErr(errBox, res.error); return; }
        showToast(`Added ${qty} units. New stock: ${res.new_stock}`, 'success');
        closeRestockModal();
        await loadInventory();
    } catch (err) {
        showErr(errBox, err.message || 'Failed to update stock.');
    }
}

// -- EDIT PRODUCT MODAL -------------------------------------------------
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

    const id = document.getElementById('edit-id').value;
    const name = document.getElementById('edit-name').value.trim();
    const price = parseFloat(document.getElementById('edit-price').value);
    const stock = parseInt(document.getElementById('edit-stock').value);

    if (!name) { showErr(errBox, 'Name cannot be empty.'); return; }
    if (price <= 0 || isNaN(price)) { showErr(errBox, 'Price must be > 0.'); return; }
    if (stock < 0 || isNaN(stock)) { showErr(errBox, 'Stock cannot be negative.'); return; }

    try {
        const res = await apiCall(`/api/inventory/${id}`, 'PUT', { name, price, stock });
        if (res.error) { showErr(errBox, res.error); return; }
        showToast('Product updated.', 'success');
        closeEditModal();
        await loadInventory();
    } catch (err) {
        showErr(errBox, err.message || 'Update failed.');
    }
}

// -- DELETE PRODUCT -----------------------------------------------------
async function deleteProduct(id, name) {
    if (!confirm(`Delete "${name}"?\n\nNote: Products with sales history cannot be deleted to protect your reports.`)) return;

    try {
        const res = await apiCall(`/api/inventory/${id}`, 'DELETE');
        if (res.error) {
            showToast(`${res.error}`, 'error');
            return;
        }
        showToast(`"${name}" deleted.`, 'success');
        await loadInventory();
    } catch (err) {
        showToast(`${err.message || 'Delete failed.'}`, 'error');
    }
}

// -- DOWNLOAD CSV TEMPLATE (internal — called via auth-gated downloadTemplate()) --
function _doDownloadTemplate() {
    // Standard columns the import parser expects
    const headers = ['product_name', 'category', 'price', 'stock'];
    const exampleRow = ['Amul Butter (500g)', 'dairy', '270', '50'];
    const note = [
        '# ProfitPilot Inventory Import Template',
        '# Required columns: product_name, category, price, stock',
        '# Rules:',
        '#   product_name  - text, must not be empty',
        '#   category      - text (e.g. grocery, dairy, clothing, fmcg, electronics, stationery)',
        '#   price         - number, must be > 0',
        '#   stock         - whole number, must be >= 0',
        '# Delete these comment lines before importing.',
        '',
    ];
    const csv = [...note, headers.join(','), exampleRow.join(',')].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url  = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href     = url;
    link.download = 'profitpilot_inventory_template.csv';
    link.click();
    URL.revokeObjectURL(url);
    showToast('Template downloaded! Fill it in and use Import to upload.', 'success');
}

// -- IMPORT CSV ---------------------------------------------------------
async function handleCSVImport(event) {
    const file = event.target.files[0];
    // Reset the file input so the same file can be re-imported if needed
    event.target.value = '';

    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.csv')) {
        showToast('Invalid file type. Please upload a .csv file.', 'error');
        return;
    }

    const text = await file.text();
    // Strip comment lines (starting with #) and blank lines
    const lines = text
        .split('\n')
        .map(l => l.trim())
        .filter(l => l && !l.startsWith('#'));

    if (lines.length < 2) {
        showToast('CSV is empty or only has headers. Please add product rows.', 'error');
        return;
    }

    // Parse header row (case-insensitive, trim spaces)
    const headerLine = lines[0];
    const headers = headerLine.split(',').map(h => h.trim().toLowerCase().replace(/"/g, ''));

    const REQUIRED = ['product_name', 'category', 'price', 'stock'];
    const missing  = REQUIRED.filter(col => !headers.includes(col));
    if (missing.length > 0) {
        showToast(
            `CSV format error: Missing required column(s): ${missing.join(', ')}.\n` +
            'Download the template to see the correct format.',
            'error'
        );
        return;
    }

    const idxName     = headers.indexOf('product_name');
    const idxCategory = headers.indexOf('category');
    const idxPrice    = headers.indexOf('price');
    const idxStock    = headers.indexOf('stock');

    const products = [];
    const errors   = [];

    for (let i = 1; i < lines.length; i++) {
        // Handle quoted fields with commas inside them
        const cols = parseCSVLine(lines[i]);
        const rowNum = i + 1;

        const name     = (cols[idxName]     || '').trim();
        const category = (cols[idxCategory] || '').trim();
        const priceRaw = (cols[idxPrice]    || '').trim();
        const stockRaw = (cols[idxStock]    || '').trim();

        if (!name) {
            errors.push(`Row ${rowNum}: product_name is empty.`);
            continue;
        }
        const price = parseFloat(priceRaw);
        if (isNaN(price) || price <= 0) {
            errors.push(`Row ${rowNum} ("${name}"): price must be a number greater than 0.`);
            continue;
        }
        const stock = parseInt(stockRaw, 10);
        if (isNaN(stock) || stock < 0) {
            errors.push(`Row ${rowNum} ("${name}"): stock must be a whole number >= 0.`);
            continue;
        }

        products.push({ name, category: category || 'general', price, stock });
    }

    if (errors.length > 0) {
        // Show first 3 errors to avoid flooding the UI
        const preview = errors.slice(0, 3).join('\n');
        const extra   = errors.length > 3 ? `\n...and ${errors.length - 3} more row(s) skipped.` : '';
        showToast(`CSV validation failed:\n${preview}${extra}`, 'error');
        if (products.length === 0) return; // Nothing valid to import
    }

    if (products.length === 0) {
        showToast('No valid products found in the CSV.', 'error');
        return;
    }

    // Send to backend in bulk
    showToast(`Importing ${products.length} product(s)…`, 'success');
    let imported = 0;
    let failed   = 0;

    for (const p of products) {
        try {
            await apiCall('/api/inventory', 'POST', p);
            imported++;
        } catch (e) {
            failed++;
        }
    }

    if (failed > 0) {
        showToast(`Import done: ${imported} added, ${failed} failed (duplicates or server errors).`, 'error');
    } else {
        showToast(`Successfully imported ${imported} product(s) into your inventory!`, 'success');
    }
    await loadInventory();
}

// Parse a single CSV line handling quoted fields
function parseCSVLine(line) {
    const result = [];
    let current  = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
        const ch = line[i];
        if (ch === '"') {
            inQuotes = !inQuotes;
        } else if (ch === ',' && !inQuotes) {
            result.push(current);
            current = '';
        } else {
            current += ch;
        }
    }
    result.push(current);
    return result;
}

// -- EXPORT CURRENT INVENTORY CSV (internal — called via auth-gated exportCSV()) --
function _doExportCSV() {
    if (!inventoryData || inventoryData.length === 0) {
        showToast('No inventory data to export.', 'error');
        return;
    }

    const headers = ['product_name', 'category', 'price', 'stock', 'status'];
    const rows = inventoryData.map(p => [
        `"${p.name}"`,
        p.category,
        p.price,
        p.stock,
        p.status
    ]);

    const csv  = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url  = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href     = url;
    link.download = `profitpilot_inventory_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
    showToast('Inventory exported as CSV!', 'success');
}

// -- HELPERS ------------------------------------------------------------
function showErr(box, msg) {
    box.textContent = msg;
    box.style.display = 'block';
}

function escHtml(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function escJs(str) {
    return String(str).replace(/\\/g, '\\\\').replace(/'/g, "\\'");
}
