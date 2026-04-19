/* ── Onboarding Logic ────────────────────────────────────────────── */

let currentStep = 1;

// Redirect if not logged in or already onboarded
auth.onAuthStateChanged(async (user) => {
  if (!user) {
    window.location.href = '/auth';
    return;
  }

  // Check if already onboarded
  const status = await checkUserOnboarded();
  if (status.onboarded) {
    window.location.href = '/';
    return;
  }

  // Pre-fill name from Firebase profile
  if (user.displayName) {
    document.getElementById('ob-name').value = user.displayName;
  }
});

function goToStep(step) {
  // Validate current step before advancing
  if (step > currentStep) {
    if (!validateStep(currentStep)) return;
  }

  currentStep = step;

  // Update steps visibility
  document.querySelectorAll('.onboarding-step').forEach(el => el.classList.remove('active'));
  document.getElementById(`step-${step}`).classList.add('active');

  // Update progress dots
  document.querySelectorAll('.progress-dot').forEach((dot, i) => {
    dot.classList.remove('active', 'completed');
    if (i + 1 === step) dot.classList.add('active');
    else if (i + 1 < step) dot.classList.add('completed');
  });

  hideError();
}

function validateStep(step) {
  if (step === 1) {
    const name = document.getElementById('ob-name').value.trim();
    if (!name) {
      showError('Please enter your name.');
      return false;
    }
    return true;
  }
  if (step === 2) {
    const bizName = document.getElementById('ob-business-name').value.trim();
    if (!bizName) {
      showError('Please enter your business name.');
      return false;
    }

    // Validate GSTIN if provided
    const gstin = document.getElementById('ob-gstin').value.trim();
    if (gstin && !/^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/i.test(gstin)) {
      showError('Invalid GSTIN format. Expected: 22AAAAA0000A1Z5');
      return false;
    }

    // Validate PAN if provided
    const pan = document.getElementById('ob-pan').value.trim();
    if (pan && !/^[A-Z]{5}[0-9]{4}[A-Z]{1}$/i.test(pan)) {
      showError('Invalid PAN format. Expected: ABCDE1234F');
      return false;
    }

    return true;
  }
  return true;
}

function autoClassifyMSME() {
  const turnover = document.getElementById('ob-turnover').value;
  const badge = document.getElementById('msme-category-badge');
  const hidden = document.getElementById('ob-msme-category');

  let category, label, cls;

  switch (turnover) {
    case 'below_1cr':
      category = 'micro';
      label = 'Micro Enterprise';
      cls = 'msme-micro';
      break;
    case '1_5cr':
      category = 'small';
      label = 'Small Enterprise';
      cls = 'msme-small';
      break;
    case '5_50cr':
      category = 'small';
      label = 'Small Enterprise';
      cls = 'msme-small';
      break;
    case '50_250cr':
      category = 'medium';
      label = 'Medium Enterprise';
      cls = 'msme-medium';
      break;
    default:
      category = 'micro';
      label = 'Micro Enterprise';
      cls = 'msme-micro';
  }

  badge.className = `msme-badge ${cls}`;
  badge.innerHTML = `
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
    ${label}
  `;
  hidden.value = category;
}

async function completeOnboarding() {
  if (!validateStep(3)) return;

  const btn = document.getElementById('complete-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="auth-spinner"></span>Setting up...';

  try {
    const token = await getIdToken();
    if (!token) throw new Error('Not authenticated');

    const payload = {
      full_name: document.getElementById('ob-name').value.trim(),
      phone: document.getElementById('ob-phone').value.trim(),
      city: document.getElementById('ob-city').value.trim(),
      state: document.getElementById('ob-state').value,
      business_name: document.getElementById('ob-business-name').value.trim(),
      business_address: document.getElementById('ob-business-address').value.trim(),
      gstin: document.getElementById('ob-gstin').value.trim().toUpperCase(),
      pan_number: document.getElementById('ob-pan').value.trim().toUpperCase(),
      business_type: document.getElementById('ob-biz-type').value,
      business_sector: document.getElementById('ob-biz-sector').value,
      turnover_range: document.getElementById('ob-turnover').value,
      msme_category: document.getElementById('ob-msme-category').value,
      payment_mode: document.getElementById('ob-payment-mode').value,
    };

    const res = await fetch('/api/auth/onboarding', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || 'Onboarding failed');
    }

    // Success! Redirect to dashboard
    window.location.href = '/';

  } catch (err) {
    btn.disabled = false;
    btn.innerHTML = 'Complete Setup';
    showError(err.message);
  }
}

function showError(msg) {
  const el = document.getElementById('onboard-error');
  el.textContent = msg;
  el.style.display = 'block';
}

function hideError() {
  document.getElementById('onboard-error').style.display = 'none';
}
