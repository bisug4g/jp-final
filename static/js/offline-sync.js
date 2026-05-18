// Offline Sync Manager for Jayti PWA
class OfflineSync {
  constructor() {
    this.dbName = 'jayti-offline';
    this.version = 1;
    this.db = null;
    this.init();
  }

  async init() {
    if (!('indexedDB' in window)) return;
    
    this.db = await new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
      
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        if (!db.objectStoreNames.contains('notes')) {
          db.createObjectStore('notes', { keyPath: 'id', autoIncrement: true });
        }
        if (!db.objectStoreNames.contains('diary')) {
          db.createObjectStore('diary', { keyPath: 'id', autoIncrement: true });
        }
        if (!db.objectStoreNames.contains('pending')) {
          db.createObjectStore('pending', { keyPath: 'id', autoIncrement: true });
        }
      };
    });
  }

  async saveOffline(store, data) {
    if (!this.db) return;
    const tx = this.db.transaction([store], 'readwrite');
    const objectStore = tx.objectStore(store);
    await objectStore.add({ ...data, timestamp: Date.now(), synced: false });
  }

  async syncPending() {
    if (!this.db || !navigator.onLine) return;
    
    const tx = this.db.transaction(['pending'], 'readonly');
    const store = tx.objectStore('pending');
    const pending = await store.getAll();
    
    for (const item of pending) {
      try {
        await fetch(item.url, {
          method: item.method,
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': item.csrf },
          body: JSON.stringify(item.data)
        });
        
        const deleteTx = this.db.transaction(['pending'], 'readwrite');
        await deleteTx.objectStore('pending').delete(item.id);
      } catch (error) {
        console.error('Sync failed:', error);
      }
    }
  }
}

const offlineSync = new OfflineSync();

window.addEventListener('online', () => {
  offlineSync.syncPending();
  document.body.classList.remove('offline');
});

window.addEventListener('offline', () => {
  document.body.classList.add('offline');
});
