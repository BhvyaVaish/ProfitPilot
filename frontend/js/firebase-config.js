/* ── Firebase SDK (compat) ─────────────────────────────────────────────
   Uses Firebase compat SDK loaded via CDN in HTML files.
   This file initializes the app and exposes auth helpers.

   SECURITY: Firebase config is fetched from the backend /api/config
   endpoint at runtime — no secrets are hardcoded in this file.
   ──────────────────────────────────────────────────────────────────── */

let auth;
let googleProvider;

// ── Fetch config from backend and initialize Firebase ──────────────────
async function _initFirebase() {
  try {
    const res = await fetch('/api/config');
    if (!res.ok) throw new Error('Failed to load Firebase config');
    const firebaseConfig = await res.json();

    if (firebaseConfig.error) {
      console.error('[Firebase] Config error:', firebaseConfig.error);
      return;
    }

    firebase.initializeApp(firebaseConfig);
    auth = firebase.auth();

    // Persist session across browser restarts
    await auth.setPersistence(firebase.auth.Auth.Persistence.LOCAL);

    // Google provider
    googleProvider = new firebase.auth.GoogleAuthProvider();
    googleProvider.addScope('email');
    googleProvider.addScope('profile');

    // Signal that Firebase is ready
    window._firebaseReady = true;
    window.dispatchEvent(new Event('firebase-ready'));

  } catch (err) {
    console.error('[Firebase] Init failed:', err);
    // Dispatch anyway so auth-guard doesn't hang forever
    window._firebaseReady = true;
    window._firebaseError = true;
    window.dispatchEvent(new Event('firebase-ready'));
  }
}

// Start init immediately
_initFirebase();

/* ── Auth Helper Functions ──────────────────────────────────────────── */

async function signUpWithEmail(email, password) {
  const cred = await auth.createUserWithEmailAndPassword(email, password);
  return cred.user;
}

async function signInWithEmail(email, password) {
  const cred = await auth.signInWithEmailAndPassword(email, password);
  return cred.user;
}

async function signInWithGoogle() {
  const cred = await auth.signInWithPopup(googleProvider);
  return cred.user;
}

async function signOutUser() {
  await auth.signOut();
  window.location.href = '/auth';
}

async function getIdToken() {
  const user = auth.currentUser;
  if (!user) return null;
  return await user.getIdToken(true);
}

function getCurrentUser() {
  return auth.currentUser;
}

async function sendPasswordReset(email) {
  await auth.sendPasswordResetEmail(email);
}

async function updateDisplayName(name) {
  const user = auth.currentUser;
  if (user) {
    await user.updateProfile({ displayName: name });
  }
}

/* ── Auth State Check (for backend) ─────────────────────────────────── */

async function checkUserOnboarded() {
  const token = await getIdToken();
  if (!token) return { exists: false, onboarded: false };

  try {
    const res = await fetch('/api/auth/check', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return await res.json();
  } catch (e) {
    console.error('Auth check failed:', e);
    return { exists: false, onboarded: false };
  }
}
