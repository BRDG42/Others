/* BRDG · Photographer Spotlight — service worker.
   Precaches the whole app shell so it runs fully offline once installed. */
const CACHE = 'brdg-spotlight-v6';

const ASSETS = [
  './',
  './index.html',
  './image-slot.js',
  './manifest.webmanifest',
  './assets/html2canvas.min.js',
  './assets/fonts/fonts.css',
  './assets/fonts/gotham-medium.woff2',
  './assets/fonts/gotham-bold.woff2',
  './assets/fonts/gotham-bold-italic.woff2',
  './assets/fonts/montserrat-latin-500-normal.woff2',
  './assets/fonts/montserrat-latin-600-normal.woff2',
  './assets/fonts/montserrat-latin-700-normal.woff2',
  './assets/fonts/montserrat-latin-800-normal.woff2',
  './assets/fonts/montserrat-latin-700-italic.woff2',
  './assets/fonts/montserrat-latin-800-italic.woff2',
  './assets/fonts/caveat-latin-600-normal.woff2',
  './assets/fonts/caveat-latin-700-normal.woff2',
  './assets/icon-192.png',
  './assets/icon-512.png',
  './assets/icon-512-maskable.png',
  './assets/apple-touch-icon.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request).then((hit) => {
      if (hit) return hit;
      return fetch(e.request).then((res) => {
        // runtime-cache same-origin GETs (e.g. dropped photos aren't fetched, so this is just app files)
        const copy = res.clone();
        if (res.ok && new URL(e.request.url).origin === self.location.origin) {
          caches.open(CACHE).then((c) => c.put(e.request, copy));
        }
        return res;
      }).catch(() => caches.match('./index.html'));
    })
  );
});
