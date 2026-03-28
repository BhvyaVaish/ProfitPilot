async function apiCall(endpoint, method = 'GET', body = null) {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) options.body = JSON.stringify(body);
  
  try {
    const response = await fetch(endpoint, options);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'API Error');
    return data;
  } catch (error) {
    showToast(error.message, 'error');
    throw error;
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
  }, 3000);
}

function formatDateDisplay(dateStr) {
    const d = new Date(dateStr);
    return isNaN(d) ? dateStr : d.toLocaleDateString('en-IN', {day:'numeric', month:'short', year:'numeric'});
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
    void navItem.offsetWidth; // reflow to restart animation
    navItem.classList.add('nav-click-anim');
    setTimeout(() => navItem.classList.remove('nav-click-anim'), 500);
  }
});
