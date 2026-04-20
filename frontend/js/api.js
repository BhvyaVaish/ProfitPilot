async function apiCall(endpoint, method = 'GET', body = null) {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };

  // Always attach auth token if available - this is the critical fix
  // window._authToken is set by auth-guard.js after Firebase resolves
  if (window._authToken) {
    options.headers['Authorization'] = `Bearer ${window._authToken}`;
  }

  if (body) options.body = JSON.stringify(body);

  // Add AbortController for timeout (35s covers Render cold starts)
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 35000);
  options.signal = controller.signal;

  document.body.classList.add('api-loading');

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    clearTimeout(timeoutId);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'API Error');
    return data;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      showToast('Server is warming up. Please try again in a few seconds.', 'error');
      throw new Error('Server is warming up. Please try again in a few seconds.');
    }
    showToast(error.message, 'error');
    throw error;
  } finally {
    document.body.classList.remove('api-loading');
  }
}

function showToast(msg, type = 'error') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container no-print';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerText = msg;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'slideIn 0.3s ease-in reverse forwards';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function formatDateDisplay(dateStr) {
  const d = new Date(dateStr);
  return isNaN(d) ? dateStr : d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

function formatCurrency(amount) {
  const num = Number(amount);
  if (isNaN(num)) return 'Rs.0';
  return 'Rs.' + num.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function formatCurrencyDecimal(amount) {
  const num = Number(amount);
  if (isNaN(num)) return 'Rs.0.00';
  return 'Rs.' + num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// Global button glow animation interceptor
document.addEventListener('click', (e) => {
  const btn = e.target.closest('.btn');
  if (btn) {
    btn.classList.remove('btn-anim-glow');
    void btn.offsetWidth;
    btn.classList.add('btn-anim-glow');
    setTimeout(() => btn.classList.remove('btn-anim-glow'), 600);
  }

  // Nav tab click glow
  const navItem = e.target.closest('.nav-item');
  if (navItem) {
    navItem.classList.remove('nav-click-anim');
    void navItem.offsetWidth;
    navItem.classList.add('nav-click-anim');
    setTimeout(() => navItem.classList.remove('nav-click-anim'), 500);
  }
});
