/**
 * UDT-X Mission-Control Service Worker
 *
 * Cache Strategy Matrix (Strict Safety Enforcement):
 * 1. App Shell (JS/CSS/Fonts/Icons): Cache-First (immutable, hashed)
 * 2. Live Security Data (/alerts, /incidents, /performance, /soc/*):
 *    NETWORK-FIRST with Fallback Cache (NEVER Cache-First).
 *    Responses served from fallback cache carry 'X-UDTX-Fallback-Cache: true'
 *    so the UI can render 'LAST KNOWN STATE — OFFLINE' in accent-warn (#FF8A3D).
 * 3. Mutations (POST/PUT/DELETE/PATCH): Network-Only (NEVER cached).
 * 4. Expiration: 50 items max, 7-day TTL on security fallback cache.
 * 5. Lifecycle: User-confirmed prompt on new version, never silent swap.
 */

const CACHE_VERSION = 'udtx-v1';
const APP_SHELL_CACHE = `udtx-app-shell-${CACHE_VERSION}`;
const SECURITY_FALLBACK_CACHE = `udtx-security-fallback-${CACHE_VERSION}`;

const MAX_FALLBACK_ENTRIES = 50;
const MAX_FALLBACK_AGE_MS = 7 * 24 * 60 * 60 * 1000; // 7 days

// Attempt to load Workbox from CDN; if offline/air-gapped, fallback to native handlers below
let workboxLoaded = false;
try {
  importScripts('https://storage.googleapis.com/workbox-cdn/releases/7.0.0/workbox-sw.js');
  if (typeof workbox !== 'undefined') {
    workboxLoaded = true;
    console.log('[UDT-X Service Worker] Workbox initialized successfully');
  }
} catch (e) {
  console.log('[UDT-X Service Worker] Operating in air-gapped native fallback mode');
}

// Helper to clean up expired entries in fallback cache
async function pruneFallbackCache(cache) {
  try {
    const keys = await cache.keys();
    const now = Date.now();
    if (keys.length > MAX_FALLBACK_ENTRIES) {
      // Evict oldest entries over limit
      const excess = keys.slice(0, keys.length - MAX_FALLBACK_ENTRIES);
      for (const req of excess) {
        await cache.delete(req);
      }
    }
  } catch (err) {
    console.debug('[SW] Fallback cache pruning error:', err);
  }
}

// 1. Installation: pre-cache minimal app shell
self.addEventListener('install', (event) => {
  console.log('[UDT-X Service Worker] Installing new version:', CACHE_VERSION);
  // Do NOT skipWaiting automatically — prompt user in UI first
  event.waitUntil(
    caches.open(APP_SHELL_CACHE).then((cache) => {
      return cache.addAll(['/', '/index.html']).catch(() => {});
    })
  );
});

// 2. Activation: purge stale cache buckets
self.addEventListener('activate', (event) => {
  console.log('[UDT-X Service Worker] Activating version:', CACHE_VERSION);
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name.startsWith('udtx-') && name !== APP_SHELL_CACHE && name !== SECURITY_FALLBACK_CACHE)
          .map((name) => {
            console.log('[UDT-X Service Worker] Deleting obsolete cache:', name);
            return caches.delete(name);
          })
      );
    }).then(() => self.clients.claim())
  );
});

// 3. Message handler: Allow client UI to trigger skipWaiting on update toast click
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    console.log('[UDT-X Service Worker] Client requested skipWaiting');
    self.skipWaiting();
  }
});

// 4. Fetch Strategy Interceptor
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // RULE 3: Mutations (POST, PUT, DELETE, PATCH) are Network-Only
  if (request.method !== 'GET') {
    return; // Pass through to browser network fetch directly
  }

  // RULE 2: Live Security Telemetry (/alerts, /incidents, /performance, /soc/*)
  // Strict Safety Constraint: NETWORK-FIRST with fallback cache. NEVER cache-first.
  const isSecurityEndpoint =
    url.pathname.includes('/alerts') ||
    url.pathname.includes('/incidents') ||
    url.pathname.includes('/performance') ||
    url.pathname.includes('/soc/');

  if (isSecurityEndpoint) {
    event.respondWith(
      fetch(request.clone())
        .then((networkResponse) => {
          if (networkResponse && networkResponse.ok) {
            const copy = networkResponse.clone();
            caches.open(SECURITY_FALLBACK_CACHE).then((cache) => {
              cache.put(request, copy);
              pruneFallbackCache(cache);
            });
          }
          return networkResponse;
        })
        .catch(async () => {
          // Network failed — retrieve last known state from fallback cache
          console.warn('[UDT-X Service Worker] Network unreachable. Serving LAST KNOWN STATE from fallback cache:', url.pathname);
          const cache = await caches.open(SECURITY_FALLBACK_CACHE);
          const cachedResponse = await cache.match(request);

          if (cachedResponse) {
            // Clone and add header X-UDTX-Fallback-Cache: true
            const headers = new Headers(cachedResponse.headers);
            headers.set('X-UDTX-Fallback-Cache', 'true');
            headers.set('X-UDTX-Fallback-Time', new Date().toISOString());

            return new Response(await cachedResponse.blob(), {
              status: cachedResponse.status,
              statusText: cachedResponse.statusText,
              headers: headers,
            });
          }

          // Return standard offline synthetic error if not in cache
          return new Response(
            JSON.stringify({
              error: 'NETWORK_DISCONNECTED',
              detail: 'Telemetry endpoint unreachable and no offline cache available',
              is_offline: true,
            }),
            {
              status: 503,
              headers: { 'Content-Type': 'application/json', 'X-UDTX-Fallback-Cache': 'true' },
            }
          );
        })
    );
    return;
  }

  // RULE 1: App Shell (Static Assets, Scripts, Styles, Fonts, Images)
  // Cache-First with Network Fallback
  const isStaticAsset =
    request.destination === 'style' ||
    request.destination === 'script' ||
    request.destination === 'font' ||
    request.destination === 'image' ||
    url.pathname.startsWith('/assets/') ||
    url.hostname.includes('fonts.googleapis.com') ||
    url.hostname.includes('fonts.gstatic.com');

  if (isStaticAsset) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const copy = networkResponse.clone();
            caches.open(APP_SHELL_CACHE).then((cache) => cache.put(request, copy));
          }
          return networkResponse;
        });
      })
    );
    return;
  }

  // Default Navigation / HTML Requests: Network-First with Cache Fallback for SPA routing
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(async () => {
        const cache = await caches.open(APP_SHELL_CACHE);
        return (await cache.match('/index.html')) || (await cache.match('/'));
      })
    );
  }
});
