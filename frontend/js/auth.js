/* ── Auth Page Logic ─────────────────────────────────────────────── */

// If already logged in, redirect away
function _initAuthPage() {
  if (!auth) {
    console.warn('[Auth] Firebase not initialized — skipping auth state listener.');
    return;
  }
  auth.onAuthStateChanged(async (user) => {
    if (user) {
      const status = await checkUserOnboarded();
      if (status.onboarded) {
        window.location.href = '/';
      } else {
        window.location.href = '/onboarding';
      }
    }
  });
}

// Wait for Firebase to be ready before attaching auth listener
if (window._firebaseReady) {
  _initAuthPage();
} else {
  window.addEventListener('firebase-ready', _initAuthPage);
}

function switchTab(tab) {
  const signinForm = document.getElementById('signin-form');
  const signupForm = document.getElementById('signup-form');
  const tabSignin = document.getElementById('tab-signin');
  const tabSignup = document.getElementById('tab-signup');

  hideMessages();

  if (tab === 'signin') {
    signinForm.style.display = 'block';
    signupForm.style.display = 'none';
    tabSignin.classList.add('active');
    tabSignup.classList.remove('active');
  } else {
    signinForm.style.display = 'none';
    signupForm.style.display = 'block';
    tabSignin.classList.remove('active');
    tabSignup.classList.add('active');
  }
}

function showError(msg) {
  const el = document.getElementById('auth-error');
  el.innerHTML = msg;
  el.style.display = 'block';
  document.getElementById('auth-success').style.display = 'none';
}

// Special error for when user tries to log in without an account
function showSignUpPrompt(message) {
  const el = document.getElementById('auth-error');
  el.innerHTML = `
    <div style="display:flex; flex-direction:column; gap:8px;">
      <span>${message}</span>
      <span>Don't have an account?
        <span onclick="switchTab('signup')" style="color:#fff; text-decoration:underline; cursor:pointer; font-weight:700;">Sign up to continue →</span>
      </span>
    </div>
  `;
  el.style.display = 'block';
  document.getElementById('auth-success').style.display = 'none';
}

function showSuccess(msg) {
  const el = document.getElementById('auth-success');
  el.textContent = msg;
  el.style.display = 'block';
  document.getElementById('auth-error').style.display = 'none';
}

function hideMessages() {
  document.getElementById('auth-error').style.display = 'none';
  document.getElementById('auth-success').style.display = 'none';
}

function setLoading(btnId, loading) {
  const btn = document.getElementById(btnId);
  if (loading) {
    btn.disabled = true;
    btn._originalText = btn.innerHTML;
    btn.innerHTML = '<span class="auth-spinner"></span>Please wait...';
  } else {
    btn.disabled = false;
    btn.innerHTML = btn._originalText || btn.innerHTML;
  }
}

async function handleSignIn(e) {
  e.preventDefault();
  hideMessages();

  const email = document.getElementById('signin-email').value.trim();
  const password = document.getElementById('signin-password').value;

  if (!email || !password) {
    showError('Please fill in all fields.');
    return;
  }

  setLoading('signin-btn', true);

  if (!auth) { showError('Firebase is not initialized. Please check that all Firebase environment variables are set on the server.'); setLoading('signin-btn', false); return; }

  try {
    await signInWithEmail(email, password);
    // onAuthStateChanged handles redirect
  } catch (err) {
    setLoading('signin-btn', false);
    const { msg, suggestSignUp } = _friendlyError(err.code);
    if (suggestSignUp) {
      showSignUpPrompt(msg);
    } else {
      showError(msg);
    }
  }
}

async function handleSignUp(e) {
  e.preventDefault();
  hideMessages();

  const name = document.getElementById('signup-name').value.trim();
  const email = document.getElementById('signup-email').value.trim();
  const password = document.getElementById('signup-password').value;
  const confirm = document.getElementById('signup-confirm').value;

  if (!name || !email || !password || !confirm) {
    showError('Please fill in all fields.');
    return;
  }

  if (password.length < 6) {
    showError('Password must be at least 6 characters.');
    return;
  }

  if (password !== confirm) {
    showError('Passwords do not match.');
    return;
  }

  setLoading('signup-btn', true);

  if (!auth) { showError('Firebase is not initialized. Please check that all Firebase environment variables are set on the server.'); setLoading('signup-btn', false); return; }

  try {
    const user = await signUpWithEmail(email, password);
    await updateDisplayName(name);
    // onAuthStateChanged will handle redirect to onboarding
  } catch (err) {
    setLoading('signup-btn', false);
    const { msg } = _friendlyError(err.code);
    showError(msg);
  }
}

async function handleGoogleSignIn() {
  hideMessages();
  setLoading('google-btn', true);

  if (!auth || !googleProvider) { showError('Firebase is not initialized. Please check that all Firebase environment variables are set on the server.'); setLoading('google-btn', false); return; }

  try {
    await signInWithGoogle();
    // onAuthStateChanged handles redirect
  } catch (err) {
    setLoading('google-btn', false);
    if (err.code !== 'auth/popup-closed-by-user') {
      const { msg } = _friendlyError(err.code);
      showError(msg);
    }
  }
}

async function handleForgotPassword() {
  const email = document.getElementById('signin-email').value.trim();
  if (!email) {
    showError('Please enter your email address first, then click "Forgot Password".');
    return;
  }

  try {
    await sendPasswordReset(email);
    showSuccess(`Password reset email sent to ${email}. Check your inbox.`);
  } catch (err) {
    const { msg } = _friendlyError(err.code);
    showError(msg);
  }
}

function _friendlyError(code) {
  // Codes that mean the user has no account and should sign up
  const noAccountCodes = ['auth/user-not-found', 'auth/invalid-credential'];

  const messages = {
    'auth/user-not-found':            'No account found with this email.',
    'auth/wrong-password':            'Incorrect password. Please try again.',
    'auth/invalid-credential':        'No account found with this email.',
    'auth/email-already-in-use':      'An account with this email already exists. Please sign in.',
    'auth/weak-password':             'Password is too weak. Use at least 6 characters.',
    'auth/invalid-email':             'Please enter a valid email address.',
    'auth/too-many-requests':         'Too many attempts. Please wait a moment and try again.',
    'auth/network-request-failed':    'Network error. Please check your internet connection.',
    'auth/popup-blocked':             'Popup was blocked. Please allow popups for this site.',
    'auth/configuration-not-found':   'Authentication is not configured. Please enable Email/Password and Google sign-in in Firebase Console.',
    'auth/unauthorized-domain':       'This domain is not authorized. Add it to Firebase Console → Authentication → Settings → Authorized domains.',
    'auth/internal-error':            'An internal error occurred. Please try again.',
    'auth/popup-closed-by-user':      'Sign-in popup was closed. Please try again.',
    'auth/cancelled-popup-request':   'Sign-in was cancelled. Please try again.',
  };

  const msg = messages[code] || (code ? `Authentication error: ${code}` : 'Authentication failed. Please try again.');
  const suggestSignUp = noAccountCodes.includes(code);
  return { msg, suggestSignUp };
}
