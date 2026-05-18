// Offline Storage Helper for Diary and Notes
// Handles localStorage fallback when offline

class OfflineStorage {
  constructor() {
    this.dbName = 'JaytiDB';
    this.dbVersion = 1;
    this.init();
  }

  init() {
    const request = indexedDB.open(this.dbName, this.dbVersion);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      
      if (!db.objectStoreNames.contains('pending-diary')) {
        db.createObjectStore('pending-diary', { keyPath: 'id', autoIncrement: true });
      }
      
      if (!db.objectStoreNames.contains('pending-notes')) {
        db.createObjectStore('pending-notes', { keyPath: 'id', autoIncrement: true });
      }
      
      if (!db.objectStoreNames.contains('cached-diary')) {
        db.createObjectStore('cached-diary', { keyPath: 'entry_date' });
      }
      
      if (!db.objectStoreNames.contains('cached-notes')) {
        db.createObjectStore('cached-notes', { keyPath: 'id' });
      }
    };
  }

  async saveDiaryOffline(entryData) {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);
      
      request.onsuccess = () => {
        const db = request.result;
        const tx = db.transaction('pending-diary', 'readwrite');
        const store = tx.objectStore('pending-diary');
        
        const data = {
          ...entryData,
          timestamp: new Date().toISOString(),
          synced: false
        };
        
        store.add(data);
        
        tx.oncomplete = () => {
          console.log('Diary saved offline');
          this.registerSync('sync-diary');
          resolve(true);
        };
        
        tx.onerror = () => reject(tx.error);
      };
      
      request.onerror = () => reject(request.error);
    });
  }

  async saveNoteOffline(noteData) {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);
      
      request.onsuccess = () => {
        const db = request.result;
        const tx = db.transaction('pending-notes', 'readwrite');
        const store = tx.objectStore('pending-notes');
        
        const data = {
          ...noteData,
          timestamp: new Date().toISOString(),
          synced: false
        };
        
        store.add(data);
        
        tx.oncomplete = () => {
          console.log('Note saved offline');
          this.registerSync('sync-notes');
          resolve(true);
        };
        
        tx.onerror = () => reject(tx.error);
      };
      
      request.onerror = () => reject(request.error);
    });
  }

  async getCachedDiary() {
    return new Promise((resolve) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);
      
      request.onsuccess = () => {
        const db = request.result;
        const tx = db.transaction('cached-diary', 'readonly');
        const store = tx.objectStore('cached-diary');
        const getAll = store.getAll();
        
        getAll.onsuccess = () => resolve(getAll.result || []);
      };
      
      request.onerror = () => resolve([]);
    });
  }

  async getCachedNotes() {
    return new Promise((resolve) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);
      
      request.onsuccess = () => {
        const db = request.result;
        const tx = db.transaction('cached-notes', 'readonly');
        const store = tx.objectStore('cached-notes');
        const getAll = store.getAll();
        
        getAll.onsuccess = () => resolve(getAll.result || []);
      };
      
      request.onerror = () => resolve([]);
    });
  }

  async cacheDiaryEntry(entry) {
    return new Promise((resolve) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);
      
      request.onsuccess = () => {
        const db = request.result;
        const tx = db.transaction('cached-diary', 'readwrite');
        const store = tx.objectStore('cached-diary');
        store.put(entry);
        tx.oncomplete = () => resolve(true);
      };
    });
  }

  async cacheNote(note) {
    return new Promise((resolve) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);
      
      request.onsuccess = () => {
        const db = request.result;
        const tx = db.transaction('cached-notes', 'readwrite');
        const store = tx.objectStore('cached-notes');
        store.put(note);
        tx.oncomplete = () => resolve(true);
      };
    });
  }

  registerSync(tag) {
    if ('serviceWorker' in navigator && 'sync' in navigator.serviceWorker) {
      navigator.serviceWorker.ready.then(registration => {
        return registration.sync.register(tag);
      });
    }
  }

  isOnline() {
    return navigator.onLine;
  }
}

// Global instance
const offlineStorage = new OfflineStorage();

// Auto-sync when coming back online
window.addEventListener('online', () => {
  console.log('Back online - syncing data');
  offlineStorage.registerSync('sync-diary');
  offlineStorage.registerSync('sync-notes');
});

// Show offline indicator
window.addEventListener('offline', () => {
  console.log('Offline mode - data will be saved locally');
  showOfflineIndicator();
});

function showOfflineIndicator() {
  const indicator = document.createElement('div');
  indicator.id = 'offline-indicator';
  indicator.style.cssText = 'position:fixed;top:10px;right:10px;background:#FF6B6B;color:white;padding:8px 16px;border-radius:20px;font-size:12px;z-index:9999;box-shadow:0 2px 10px rgba(0,0,0,0.2);';
  indicator.textContent = 'Offline - Changes saved locally';
  document.body.appendChild(indicator);
}

window.addEventListener('online', () => {
  const indicator = document.getElementById('offline-indicator');
  if (indicator) {
    indicator.style.background = '#51CF66';
    indicator.textContent = 'Back online - Syncing...';
    setTimeout(() => indicator.remove(), 3000);
  }
});
