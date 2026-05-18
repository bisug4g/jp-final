const CACHE_NAME = 'jayti-v4';
const STATIC_CACHE = 'jayti-static-v4';
const DYNAMIC_CACHE = 'jayti-dynamic-v4';

const STATIC_ASSETS = [
  '/dashboard/',
  '/static/css/custom.css',
  '/static/css/dark-mode.css',
  '/static/js/dark-mode.js',
  '/static/manifest.json',
];

const CACHE_PAGES = [
  '/diary/write/',
  '/diary/overview/',
  '/goals/',
  '/notes/',
  '/astro/',
  '/ai-chat/',
];

self.addEventListener('install', event => {
  event.waitUntil(
    Promise.all([
      caches.open(STATIC_CACHE).then(cache => cache.addAll(STATIC_ASSETS)),
      caches.open(DYNAMIC_CACHE)
    ])
  );
  self.skipWaiting();
});

self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Network-first for static assets (ensures fresh JS/CSS on deploy)
  if (request.destination === 'style' || request.destination === 'script' || request.destination === 'font') {
    event.respondWith(
      fetch(request).then(fetchResponse => {
        return caches.open(STATIC_CACHE).then(cache => {
          cache.put(request, fetchResponse.clone());
          return fetchResponse;
        });
      }).catch(() => caches.match(request))
    );
    return;
  }
  
  // Network-first for API calls and pages
  event.respondWith(
    fetch(request)
      .then(response => {
        if (response && response.status === 200) {
          const responseClone = response.clone();
          caches.open(DYNAMIC_CACHE).then(cache => {
            cache.put(request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        return caches.match(request).then(response => {
          if (response) return response;
          if (request.destination === 'document') {
            return caches.match('/dashboard/');
          }
        });
      })
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// Handle background sync for offline diary/notes
self.addEventListener('sync', event => {
  if (event.tag === 'sync-diary') {
    event.waitUntil(syncDiaryEntries());
  }
  if (event.tag === 'sync-notes') {
    event.waitUntil(syncNotes());
  }
});

async function syncDiaryEntries() {
  const entries = await getFromIndexedDB('pending-diary');
  for (const entry of entries) {
    try {
      await fetch('/diary/save/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(entry)
      });
      await removeFromIndexedDB('pending-diary', entry.id);
    } catch (e) {
      console.log('Sync failed, will retry');
    }
  }
}

async function syncNotes() {
  const notes = await getFromIndexedDB('pending-notes');
  for (const note of notes) {
    try {
      await fetch('/notes/save/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(note)
      });
      await removeFromIndexedDB('pending-notes', note.id);
    } catch (e) {
      console.log('Sync failed, will retry');
    }
  }
}

function getFromIndexedDB(storeName) {
  return new Promise((resolve) => {
    const request = indexedDB.open('JaytiDB', 1);
    request.onsuccess = () => {
      const db = request.result;
      const tx = db.transaction(storeName, 'readonly');
      const store = tx.objectStore(storeName);
      const getAll = store.getAll();
      getAll.onsuccess = () => resolve(getAll.result || []);
    };
    request.onerror = () => resolve([]);
  });
}

function removeFromIndexedDB(storeName, id) {
  return new Promise((resolve) => {
    const request = indexedDB.open('JaytiDB', 1);
    request.onsuccess = () => {
      const db = request.result;
      const tx = db.transaction(storeName, 'readwrite');
      const store = tx.objectStore(storeName);
      store.delete(id);
      tx.oncomplete = () => resolve();
    };
  });
}

self.addEventListener('push', event => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'Jayti Reminder';
  const options = {
    body: data.body || 'Your diary is waiting for you.',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/badge-72x72.png',
    vibrate: [200, 100, 200],
    data: {
      url: data.url || '/diary/write/'
    }
  };
  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data.url)
  );
});
