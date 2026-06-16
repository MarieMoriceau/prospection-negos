// Cache du shell pour ouverture rapide / hors-ligne partiel.
// Les appels /api/* passent toujours par le réseau (jamais mis en cache).
const CACHE = 'prospection-v1';
const SHELL = ['/', '/index.html', '/manifest.json', '/icon-192.png', '/icon-512.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (url.pathname.startsWith('/api/')) return; // réseau direct
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
