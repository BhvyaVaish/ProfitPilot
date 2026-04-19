/**
 * ProfitPilot Service Worker — Offline-first caching strategy.
 *
 * Strategy:
 *   - Static assets (CSS, JS, HTML, images) → Cache-first
 *   - API calls (/api/*) → Network-first with cache fallback
 *   - Everything else → Network-first
 */

const CACHE_VERSION = 'profitpilot-v3.1';

const PRECACHE_URLS = [
  '/',
  '/index',
  '/dashboard',
  '/billing',
  '/inventory',
  '/tax',
  '/chatbot',
  '/about',
  '/auth',
  '/onboarding',
  '/profile',
  '/css/base.css',
  '/css/layout.css',
  '/css/components.css',
  '/css/auth.css',
  '/js/api.js',
  '/js/auth-guard.js',
  '/js/home.js',
  '/js/i18n.js',
  '/favicon.png',
  '/manifest.json',
];

// ── Install: pre-cache all static assets ────────────────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => {
      console.log('[SW] Pre-caching static assets');
      return cache.addAll(PRECACHE_URLS);
    })
  );
  self.skipWaiting();
});

// ── Activate: clean up old caches ───────────────────────────────────────────
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_VERSION)
          .map((key) => {
            console.log('[SW] Removing old cache:', key);
            return caches.delete(key);
          })
      )
    )
  );
  self.clients.claim();
});

// ── Fetch: Network-First with Cache Fallback ────────────────────────────────
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // Skip cross-origin requests (Firebase, Google APIs, etc.)
  if (url.origin !== location.origin) return;

  // Network-First strategy for all our assets and API calls
  event.respondWith(
    fetch(request)
      .then((response) => {
        // Clone and cache successful responses for offline use
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_VERSION).then((cache) => cache.put(request, clone));
        }
        return response;
      })
      .catch(() => {
        // If network fails (offline), fallback to cache
        return caches.match(request);
      })
  );
});
