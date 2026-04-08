/**
 * LocalDB Service - Frontend caching using IndexedDB
 * Stores API data locally and refreshes periodically
 */

const DB_NAME = 'AarambhDB';
const DB_VERSION = 1;

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number; // Time to live in milliseconds
}

class LocalDBService {
  private db: IDBDatabase | null = null;
  private readonly stores = [
    'market_data',      // Stock quotes, heatmap, indices
    'news',             // News articles
    'signals',          // Trading signals
    'research',         // Stock research data
    'entities',         // Graph entities
    'user_data'         // User preferences, history
  ];

  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        this.stores.forEach(storeName => {
          if (!db.objectStoreNames.contains(storeName)) {
            db.createObjectStore(storeName, { keyPath: 'key' });
          }
        });
      };
    });
  }

  async set<T>(storeName: string, key: string, data: T, ttlMinutes: number = 5): Promise<void> {
    if (!this.db) await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      
      const entry: CacheEntry<T> = {
        data,
        timestamp: Date.now(),
        ttl: ttlMinutes * 60 * 1000
      };

      const request = store.put({ key, ...entry });
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async get<T>(storeName: string, key: string): Promise<T | null> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([storeName], 'readonly');
      const store = transaction.objectStore(storeName);
      const request = store.get(key);

      request.onsuccess = () => {
        const result = request.result as CacheEntry<T> | undefined;
        if (!result) {
          resolve(null);
          return;
        }

        // Check if data is expired
        const isExpired = Date.now() - result.timestamp > result.ttl;
        if (isExpired) {
          this.delete(storeName, key); // Clean up expired data
          resolve(null);
          return;
        }

        resolve(result.data);
      };

      request.onerror = () => reject(request.error);
    });
  }

  async delete(storeName: string, key: string): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      const request = store.delete(key);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async clear(storeName: string): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      const request = store.clear();

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async getAll<T>(storeName: string): Promise<T[]> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([storeName], 'readonly');
      const store = transaction.objectStore(storeName);
      const request = store.getAll();

      request.onsuccess = () => {
        const results = request.result as CacheEntry<T>[];
        // Filter out expired entries
        const valid = results.filter(r => {
          const isExpired = Date.now() - r.timestamp > r.ttl;
          return !isExpired;
        });
        resolve(valid.map(r => r.data));
      };

      request.onerror = () => reject(request.error);
    });
  }
}

// Create singleton instance
export const localDB = new LocalDBService();

// Helper functions for common operations
export async function cacheMarketData<T>(key: string, data: T): Promise<void> {
  return localDB.set('market_data', key, data, 5); // 5 minutes TTL
}

export async function getCachedMarketData<T>(key: string): Promise<T | null> {
  return localDB.get<T>('market_data', key);
}

export async function cacheNews<T>(key: string, data: T): Promise<void> {
  return localDB.set('news', key, data, 10); // 10 minutes TTL
}

export async function getCachedNews<T>(key: string): Promise<T | null> {
  return localDB.get<T>('news', key);
}

export async function cacheResearch<T>(key: string, data: T): Promise<void> {
  return localDB.set('research', key, data, 60); // 60 minutes TTL
}

export async function getCachedResearch<T>(key: string): Promise<T | null> {
  return localDB.get<T>('research', key);
}
