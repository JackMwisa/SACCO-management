const CACHE_NAME = 'prime-sacco-cache-v1';

const ASSETS = [
  '/',  // homepage
  '/static/assets/css/styles.css',
  '/static/assets/js/app.js',
  '/static/icon/icon-192x192.png',
  '/static/icon/icon-512x512.png',
  // Add more assets if needed
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        return cache.addAll(ASSETS);
      })
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        return response || fetch(event.request);
      })
  );
});
