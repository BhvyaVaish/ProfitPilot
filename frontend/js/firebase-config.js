/* ── Firebase SDK (compat) ─────────────────────────────────────────────
   Uses Firebase compat SDK loaded via CDN in HTML files.
   This file initializes the app and exposes auth helpers.
   ──────────────────────────────────────────────────────────────────── */

const firebaseConfig = {
  apiKey: "AIzaSyDN-M1mvRK9tfjWfhFL2wdZR4MB6NVPpiY",
  authDomain: "profitpilot-365ac.firebaseapp.com",
  projectId: "profitpilot-365ac",
  storageBucket: "profitpilot-365ac.firebasestorage.app",
  messagingSenderId: "561527733770",
  appId: "1:561527733770:web:ad53ded29149bd330d69f3",
  measurementId: "G-D78VP6NPTG"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();

// Persist session across browser restarts
auth.setPersistence(firebase.auth.Auth.Persistence.LOCAL);

// Google provider
const googleProvider = new firebase.auth.GoogleAuthProvider();
googleProvider.addScope('email');
googleProvider.addScope('profile');

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
