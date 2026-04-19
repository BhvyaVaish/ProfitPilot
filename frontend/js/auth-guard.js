/* ── Auth Guard ────────────────────────────────────────────────────────
   Included on every page. Manages auth state, UI visibility, and
   auto-attaches auth tokens to API calls.
   ──────────────────────────────────────────────────────────── */

let _authToken = null;
window._isLoggedIn = false;
window._userProfile = null;
window._authToken = null; // Expose auth token globally for debugging

// Patch the global apiCall to auto-attach auth token
const _originalApiCall = window.apiCall;
window.apiCall = async function(endpoint, method = 'GET', body = null) {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };

  // Attach auth token if available
  if (_authToken) {
    options.headers['Authorization'] = `Bearer ${_authToken}`;
    console.log('[API] Calling', method, endpoint, 'with auth token');
  } else {
    console.log('[API] Calling', method, endpoint, 'WITHOUT auth token (demo mode)');
  }

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
};

// Wait for Firebase to be initialized (it now loads config asynchronously)
function _attachAuthListener() {
  // If Firebase failed to init, go straight to guest UI
  if (window._firebaseError) {
    console.warn('[AUTH] Firebase init failed — running in guest/demo mode');
    window._isLoggedIn = false;
    _authToken = null;
    window._authToken = null;
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', _showGuestUI);
    } else {
      _showGuestUI();
    }
    window._authReady = true;
    window.dispatchEvent(new CustomEvent('auth-ready'));
    return;
  }

  auth.onAuthStateChanged(async (user) => {
    if (user) {
      window._isLoggedIn = true;
      _authToken = await user.getIdToken();
      window._authToken = _authToken; // Expose globally

      console.log('[AUTH] User logged in:', user.email, 'UID:', user.uid);

      // Refresh token periodically (every 50 min)
      setInterval(async () => {
        _authToken = await user.getIdToken(true);
        window._authToken = _authToken; // Update global reference
      }, 50 * 60 * 1000);

      // Show authenticated UI (waits for DOM to be ready)
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => _showAuthenticatedUI(user));
      } else {
        _showAuthenticatedUI(user);
      }

      // Fetch profile for header
      try {
        const profileRes = await fetch('/api/auth/profile', {
          headers: { 'Authorization': `Bearer ${_authToken}` }
        });
        if (profileRes.ok) {
          const data = await profileRes.json();
          window._userProfile = data.profile;
        }
      } catch(e) { /* ignore */ }

    } else {
      window._isLoggedIn = false;
      _authToken = null;
      window._authToken = null; // Clear global reference
      console.log('[AUTH] User logged out or not authenticated');
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _showGuestUI);
      } else {
        _showGuestUI();
      }
    }

    // Signal that auth state is resolved — other scripts wait for this
    window._authReady = true;
    window.dispatchEvent(new CustomEvent('auth-ready'));
  });
}

// Attach when Firebase is ready (async init via /api/config)
if (window._firebaseReady) {
  _attachAuthListener();
} else {
  window.addEventListener('firebase-ready', _attachAuthListener, { once: true });
}


function _showAuthenticatedUI(user) {
  // Show elements that require auth — override the CSS !important default
  document.querySelectorAll('.auth-required').forEach(el => {
    el.style.setProperty('display', el.tagName === 'SPAN' ? 'inline' : 'inline-flex', 'important');
  });

  // Hide elements for guests only
  document.querySelectorAll('.guest-only').forEach(el => {
    el.style.display = 'none';
  });

  // Update user profile icon in header
  const profileEl = document.querySelector('.user-profile');
  if (profileEl) {
    const displayName = user.displayName || user.email.split('@')[0];
    const initials = displayName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);

    profileEl.innerHTML = `
      <div class="user-dropdown" onclick="toggleUserMenu()" style="display:flex; align-items:center; gap:8px; cursor:pointer; position:relative;">
        <div style="width:32px; height:32px; border-radius:50%; background:var(--accent-blue); color:#fff; display:flex; align-items:center; justify-content:center; font-size:0.75rem; font-weight:700; font-family:var(--font-display);">${initials}</div>
        <div id="user-menu" style="display:none; position:absolute; top:42px; right:0; background:var(--bg-card); border:1px solid var(--border); border-radius:var(--radius-sm); box-shadow:0 8px 30px rgba(0,0,0,0.12); min-width:200px; z-index:100; overflow:hidden;">
          <div style="padding:14px 16px; border-bottom:1px solid var(--border);">
            <div style="font-weight:600; font-size:0.9rem; color:var(--text-primary);">${displayName}</div>
            <div style="font-size:0.78rem; color:var(--text-muted); margin-top:2px;">${user.email}</div>
          </div>
          <a href="/profile" style="display:block; padding:10px 16px; font-size:0.85rem; color:var(--text-secondary); text-decoration:none; transition:background 0.15s;" onmouseover="this.style.background='rgba(37,99,235,0.05)'" onmouseout="this.style.background='transparent'">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:8px; vertical-align:text-bottom;"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>My Profile
          </a>
          <div onclick="flushUserData()" style="padding:10px 16px; font-size:0.85rem; color:var(--accent-orange); cursor:pointer; transition:background 0.15s;" onmouseover="this.style.background='rgba(245,158,11,0.05)'" onmouseout="this.style.background='transparent'">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:8px; vertical-align:text-bottom;"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>Flush Data
          </div>
          <div onclick="signOutUser()" style="padding:10px 16px; font-size:0.85rem; color:var(--accent-red); cursor:pointer; transition:background 0.15s;" onmouseover="this.style.background='rgba(239,68,68,0.05)'" onmouseout="this.style.background='transparent'">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:8px; vertical-align:text-bottom;"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>Sign Out
          </div>
        </div>
      </div>
    `;
  }

  // Update mobile nav drawer with user profile
  const mobileNav = document.querySelector('.mobile-nav');
  if (mobileNav) {
    let mobileProfile = document.getElementById('mobile-user-profile');
    if (!mobileProfile) {
      mobileProfile = document.createElement('div');
      mobileProfile.id = 'mobile-user-profile';
      mobileProfile.style.cssText = "padding: 16px; border-top: 1px solid var(--border); margin-top: auto;";
      mobileNav.appendChild(mobileProfile);
    }
    const displayName = user.displayName || user.email.split('@')[0];
    const initials = displayName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    
    mobileProfile.innerHTML = `
      <div style="display:flex; align-items:center; gap:12px; margin-bottom:16px;">
        <div style="width:36px; height:36px; border-radius:50%; background:var(--accent-blue); color:#fff; display:flex; align-items:center; justify-content:center; font-weight:700;">${initials}</div>
        <div>
          <div style="font-weight:600; font-size:0.95rem; color:var(--text-primary);">${displayName}</div>
          <div style="font-size:0.8rem; color:var(--text-muted);">${user.email}</div>
        </div>
      </div>
      <div style="display:flex; flex-direction:column; gap:12px;">
        <a href="/profile" style="color:var(--text-secondary); text-decoration:none; font-size:0.95rem; display:flex; align-items:center;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:8px;"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>My Profile</a>
        <div onclick="flushUserData(); if(typeof closeMobileNav==='function') closeMobileNav();" style="color:var(--accent-orange); font-size:0.95rem; display:flex; align-items:center; cursor:pointer;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:8px;"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>Flush Data</div>
        <div onclick="signOutUser(); if(typeof closeMobileNav==='function') closeMobileNav();" style="color:var(--accent-red); font-size:0.95rem; display:flex; align-items:center; cursor:pointer;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:8px;"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>Sign Out</div>
      </div>
    `;
  }
}

function _showGuestUI() {
  // Hide elements that require auth
  document.querySelectorAll('.auth-required').forEach(el => {
    el.style.display = 'none';
  });

  // Show guest-only elements
  document.querySelectorAll('.guest-only').forEach(el => {
    el.style.display = '';
  });

  // Update user profile icon to sign-in link
  const profileEl = document.querySelector('.user-profile');
  if (profileEl) {
    profileEl.innerHTML = `
      <a href="/auth" style="display:flex; align-items:center; gap:6px; text-decoration:none; color:var(--accent-blue); font-size:0.85rem; font-weight:600; padding:6px 14px; border:1px solid var(--accent-blue); border-radius:20px; transition:all 0.2s;" onmouseover="this.style.background='var(--accent-blue)';this.style.color='#fff'" onmouseout="this.style.background='transparent';this.style.color='var(--accent-blue)'">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path><polyline points="10 17 15 12 10 7"></polyline><line x1="15" y1="12" x2="3" y2="12"></line></svg>
        Sign In
      </a>
    `;
  }

  // Update mobile user profile to sign-in link
  const mobileNav = document.querySelector('.mobile-nav');
  if (mobileNav) {
    let mobileProfile = document.getElementById('mobile-user-profile');
    if (!mobileProfile) {
      mobileProfile = document.createElement('div');
      mobileProfile.id = 'mobile-user-profile';
      mobileProfile.style.cssText = "padding: 16px; border-top: 1px solid var(--border); margin-top: auto; text-align:center;";
      mobileNav.appendChild(mobileProfile);
    }
    mobileProfile.innerHTML = `
      <a href="/auth" style="display:flex; align-items:center; justify-content:center; gap:6px; background:var(--accent-blue); color:#fff; font-weight:600; padding:12px 14px; border-radius:8px; text-decoration:none;">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path><polyline points="10 17 15 12 10 7"></polyline><line x1="15" y1="12" x2="3" y2="12"></line></svg>
        Sign In
      </a>
    `;
  }
}

function toggleUserMenu() {
  const menu = document.getElementById('user-menu');
  if (menu) {
    menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
  }
}

// Close menu on outside click
document.addEventListener('click', (e) => {
  const menu = document.getElementById('user-menu');
  const dropdown = e.target.closest('.user-dropdown');
  if (menu && !dropdown) {
    menu.style.display = 'none';
  }
});

async function flushUserData() {
  // Check if user is logged in
  if (!window._isLoggedIn) {
    alert("Please sign in to use this feature. Demo data cannot be flushed.");
    window.location.href = '/auth';
    return;
  }

  if (!confirm("Are you sure you want to flush all your data?\n\nThis will permanently delete:\n• All products in your inventory\n• All sales history\n• All bills and invoices\n• All alerts and insights\n\nThis action cannot be undone!")) {
    return;
  }
  
  try {
    const res = await apiCall('/api/auth/flush', 'DELETE');
    if (res && res.success) {
      alert("✅ All data flushed successfully!\n\nYour account is now clean and ready for fresh data. The app will reload now.");
      window.location.reload();
    } else {
      alert("❌ Failed to flush data: " + (res.error || "Unknown error"));
    }
  } catch (e) {
    if (e.message.includes("Authentication required") || e.message.includes("sign in")) {
      alert("⚠️ Please sign in to use this feature.\n\nDemo data cannot be flushed. Create an account to manage your own data.");
      window.location.href = '/auth';
    } else if (e.message.includes("Cannot flush demo data")) {
      alert("⚠️ Demo data cannot be flushed.\n\nPlease sign in with your own account to use this feature.");
      window.location.href = '/auth';
    } else {
      alert("❌ Error flushing data: " + e.message);
    }
  }
}
