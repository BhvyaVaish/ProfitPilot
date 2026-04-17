/* ── Profile Page Logic ──────────────────────────────────────────── */

// Redirect if not logged in
auth.onAuthStateChanged(async (user) => {
  if (!user) {
    window.location.href = '/auth';
    return;
  }
  loadProfile();
});

async function loadProfile() {
  try {
    const token = await getIdToken();
    const res = await fetch('/api/auth/profile', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!res.ok) {
      throw new Error('Failed to load profile');
    }

    const data = await res.json();
    const p = data.profile;

    // Fill form fields
    document.getElementById('prof-name').value = p.full_name || '';
    document.getElementById('prof-phone').value = p.phone || '';
    document.getElementById('prof-city').value = p.city || '';
    document.getElementById('prof-state').value = p.state || '';
    document.getElementById('prof-business-name').value = p.business_name || '';
    document.getElementById('prof-business-address').value = p.business_address || '';
    document.getElementById('prof-gstin').value = p.gstin || '';
    document.getElementById('prof-pan').value = p.pan_number || '';
    document.getElementById('prof-biz-type').value = p.business_type || 'trading';
    document.getElementById('prof-biz-sector').value = p.business_sector || 'general';
    document.getElementById('prof-turnover').value = p.turnover_range || 'below_1cr';
    document.getElementById('prof-payment-mode').value = p.payment_mode || 'mixed';

    // Set header info
    document.getElementById('profile-display-name').textContent = p.full_name || 'User';
    document.getElementById('profile-email').textContent = p.email || '';

    // Avatar initials
    const initials = (p.full_name || 'U').split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    document.getElementById('profile-avatar').textContent = initials;

    // MSME badge
    const badge = document.getElementById('profile-msme-badge');
    const msme = p.msme_category || 'micro';
    const labels = { micro: 'Micro Enterprise', small: 'Small Enterprise', medium: 'Medium Enterprise' };
    badge.className = `msme-badge msme-${msme}`;
    badge.textContent = labels[msme] || 'Micro Enterprise';

    // Show card
    document.getElementById('profile-card').style.display = 'block';

  } catch (err) {
    console.error('Load profile error:', err);
    showProfileError('Failed to load profile. Please try again.');
    document.getElementById('profile-card').style.display = 'block';
  }
}

async function saveProfile() {
  const btn = document.getElementById('save-profile-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="auth-spinner"></span>Saving...';

  try {
    const token = await getIdToken();
    const payload = {
      full_name: document.getElementById('prof-name').value.trim(),
      phone: document.getElementById('prof-phone').value.trim(),
      city: document.getElementById('prof-city').value.trim(),
      state: document.getElementById('prof-state').value.trim(),
      business_name: document.getElementById('prof-business-name').value.trim(),
      business_address: document.getElementById('prof-business-address').value.trim(),
      gstin: document.getElementById('prof-gstin').value.trim().toUpperCase(),
      pan_number: document.getElementById('prof-pan').value.trim().toUpperCase(),
      business_type: document.getElementById('prof-biz-type').value,
      business_sector: document.getElementById('prof-biz-sector').value,
      turnover_range: document.getElementById('prof-turnover').value,
      payment_mode: document.getElementById('prof-payment-mode').value,
    };

    // Auto-classify MSME
    const turnoverMap = { 'below_1cr': 'micro', '1_5cr': 'small', '5_50cr': 'small', '50_250cr': 'medium' };
    payload.msme_category = turnoverMap[payload.turnover_range] || 'micro';

    const res = await fetch('/api/auth/profile', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Save failed');

    showProfileSuccess('Profile updated successfully!');
    loadProfile(); // Refresh display

  } catch (err) {
    showProfileError(err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = 'Save Changes';
  }
}

function showProfileError(msg) {
  const el = document.getElementById('profile-error');
  el.textContent = msg;
  el.style.display = 'block';
  document.getElementById('profile-success').style.display = 'none';
}

function showProfileSuccess(msg) {
  const el = document.getElementById('profile-success');
  el.textContent = msg;
  el.style.display = 'block';
  document.getElementById('profile-error').style.display = 'none';
  setTimeout(() => { el.style.display = 'none'; }, 3000);
}
