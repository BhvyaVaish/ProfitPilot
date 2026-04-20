/**
 * ProfitPilot Service Worker — Offline-first caching strategy.
 *
 * Strategy:
 *   - API calls (/api/*) → ALWAYS Network only (never cache)
 *   - Static assets (CSS, JS, HTML, images) → Network-first with cache fallback
 */

const CACHE_VERSION = 'profitpilot-v4.0';

const PRECACHE_URLS = [
  '/',
  '/css/base.css',
  '/css/layout.css',
  '/css/components.css',
  '/css/auth.css',
  '/favicon.png',
  '/manifest.json',
];

// ── Install: pre-cache static assets ────────────────────────────────────
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_VERSION).then(function(cache) {
      console.log('[SW] Pre-caching static assets');
      return cache.addAll(PRECACHE_URLS);
    })
  );
  self.skipWaiting();
});

// ── Activate: clean up old caches ───────────────────────────────────────
self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(
        keys.filter(function(key) { return key !== CACHE_VERSION; })
            .map(function(key) {
              console.log('[SW] Removing old cache:', key);
              return caches.delete(key);
            })
      );
    })
  );
  self.clients.claim();
});

// ── Fetch ────────────────────────────────────────────────────────────────
self.addEventListener('fetch', function(event) {
  var request = event.request;
  var url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // Skip cross-origin requests (Firebase, Google APIs, CDN, etc.)
  if (url.origin !== location.origin) return;

  // NEVER cache API calls — always go to network
  if (url.pathname.startsWith('/api/')) return;

  // Network-First strategy for all static assets
  event.respondWith(
    fetch(request).then(function(response) {
      if (response.ok) {
        var clone = response.clone();
        caches.open(CACHE_VERSION).then(function(cache) { cache.put(request, clone); });
      }
      return response;
    }).catch(function() {
      return caches.match(request);
    })
  );
});
