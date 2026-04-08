/**
 * Enhanced API Client with Local Caching and Auto-Refresh
 * 
 * Features:
 * - Fetches data from backend APIs
 * - Caches data in IndexedDB for offline access
 * - Auto-refreshes data periodically
 * - Falls back to cached data when offline
 */

import { api } from '@/api/client';
import { localDB, cacheMarketData, getCachedMarketData, cacheNews, getCachedNews, cacheResearch, getCachedResearch } from './localDB';

// Configuration
const REFRESH_INTERVALS = {
  marketHeatmap: 5 * 60 * 1000,      // 5 minutes
  marketQuote: 2 * 60 * 1000,        // 2 minutes
  marketIndices: 5 * 60 * 1000,      // 5 minutes
  news: 10 * 60 * 1000,              // 10 minutes
  signals: 5 * 60 * 1000,            // 5 minutes
  research: 60 * 60 * 1000,          // 60 minutes
};

class DataRefreshService {
  private intervals: Map<string, NodeJS.Timeout> = new Map();
  private listeners: Map<string, Set<(data: any) => void>> = new Map();

  // Subscribe to data updates
  subscribe(key: string, callback: (data: any) => void): () => void {
    if (!this.listeners.has(key)) {
      this.listeners.set(key, new Set());
    }
    this.listeners.get(key)!.add(callback);

    // Return unsubscribe function
    return () => {
      this.listeners.get(key)?.delete(callback);
    };
  }

  // Notify all listeners for a key
  private notify(key: string, data: any): void {
    this.listeners.get(key)?.forEach(callback => {
      try {
        callback(data);
      } catch (e) {
        console.error(`Error in data listener for ${key}:`, e);
      }
    });
  }

  // Start auto-refresh for a specific data type
  startRefresh(key: string, fetchFn: () => Promise<any>, intervalMs: number): void {
    // Clear existing interval if any
    this.stopRefresh(key);

    // Initial fetch
    this.fetchAndCache(key, fetchFn);

    // Set up interval
    const interval = setInterval(() => {
      this.fetchAndCache(key, fetchFn);
    }, intervalMs);

    this.intervals.set(key, interval);
  }

  // Stop auto-refresh
  stopRefresh(key: string): void {
    const interval = this.intervals.get(key);
    if (interval) {
      clearInterval(interval);
      this.intervals.delete(key);
    }
  }

  // Fetch data and cache it
  private async fetchAndCache(key: string, fetchFn: () => Promise<any>): Promise<void> {
    try {
      const data = await fetchFn();
      
      // Cache the data
      if (key.startsWith('market:')) {
        await cacheMarketData(key, data);
      } else if (key.startsWith('news:')) {
        await cacheNews(key, data);
      } else if (key.startsWith('research:')) {
        await cacheResearch(key, data);
      }

      // Notify listeners
      this.notify(key, data);
    } catch (error) {
      console.error(`Failed to refresh ${key}:`, error);
    }
  }

  // Get data (from cache or fetch)
  async getData<T>(
    key: string,
    fetchFn: () => Promise<T>,
    useCache: boolean = true
  ): Promise<T> {
    // Try cache first
    if (useCache) {
      let cached: T | null = null;
      
      if (key.startsWith('market:')) {
        cached = await getCachedMarketData<T>(key);
      } else if (key.startsWith('news:')) {
        cached = await getCachedNews<T>(key);
      } else if (key.startsWith('research:')) {
        cached = await getCachedResearch<T>(key);
      }

      if (cached) {
        // Return cached data immediately
        // Also trigger a background refresh
        this.fetchAndCache(key, fetchFn).catch(console.error);
        return cached;
      }
    }

    // Fetch fresh data
    const data = await fetchFn();
    
    // Cache it
    if (key.startsWith('market:')) {
      await cacheMarketData(key, data);
    } else if (key.startsWith('news:')) {
      await cacheNews(key, data);
    } else if (key.startsWith('research:')) {
      await cacheResearch(key, data);
    }

    return data;
  }

  // Stop all refreshes
  stopAll(): void {
    this.intervals.forEach(interval => clearInterval(interval));
    this.intervals.clear();
  }
}

// Create singleton
export const dataRefreshService = new DataRefreshService();

// ============================================
// Enhanced API Functions with Caching
// ============================================

export async function getMarketHeatmapWithCache() {
  return dataRefreshService.getData(
    'market:heatmap',
    () => api.getMarketHeatmap(),
    true
  );
}

export async function getStockQuoteWithCache(ticker: string) {
  return dataRefreshService.getData(
    `market:quote:${ticker}`,
    () => api.getStockQuote(ticker),
    true
  );
}

export async function getStockProfileWithCache(ticker: string) {
  return dataRefreshService.getData(
    `market:profile:${ticker}`,
    () => api.getStockProfile(ticker),
    true
  );
}

export async function getStockResearchWithCache(ticker: string) {
  return dataRefreshService.getData(
    `research:${ticker}`,
    () => api.getStockResearch(ticker),
    true
  );
}

export async function getMarketIndicesWithCache() {
  return dataRefreshService.getData(
    'market:indices',
    () => api.getMarketIndices(),
    true
  );
}

export async function getNewsHeadlinesWithCache(count: number = 50) {
  return dataRefreshService.getData(
    `news:headlines:${count}`,
    () => api.getNewsHeadlines(count),
    true
  );
}

export async function getSignalsWithCache() {
  return dataRefreshService.getData(
    'market:signals',
    () => api.getSignals(),
    true
  );
}

// ============================================
// Auto-Refresh Setup
// ============================================

export function startAutoRefresh(): () => void {
  // Initialize localDB
  localDB.init().catch(console.error);

  // Start refreshes
  dataRefreshService.startRefresh(
    'market:heatmap',
    () => api.getMarketHeatmap(),
    REFRESH_INTERVALS.marketHeatmap
  );

  dataRefreshService.startRefresh(
    'market:indices',
    () => api.getMarketIndices(),
    REFRESH_INTERVALS.marketIndices
  );

  dataRefreshService.startRefresh(
    'news:headlines:50',
    () => api.getNewsHeadlines(50),
    REFRESH_INTERVALS.news
  );

  dataRefreshService.startRefresh(
    'market:signals',
    () => api.getSignals(),
    REFRESH_INTERVALS.signals
  );

  // Return cleanup function
  return () => {
    dataRefreshService.stopAll();
  };
}

// ============================================
// Hook for React Components
// ============================================

import { useState, useEffect } from 'react';

export function useCachedData<T>(
  key: string,
  fetchFn: () => Promise<T>,
  deps: any[] = []
): { data: T | null; loading: boolean; error: Error | null; refresh: () => void } {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await dataRefreshService.getData(key, fetchFn, true);
      setData(result);
    } catch (e) {
      setError(e as Error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    
    // Subscribe to updates
    const unsubscribe = dataRefreshService.subscribe(key, (newData) => {
      setData(newData);
    });

    return () => {
      unsubscribe();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, loading, error, refresh: fetchData };
}
