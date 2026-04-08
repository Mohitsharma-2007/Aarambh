import axios from "axios";

// Configuration
const API_ENDPOINTS = {
  SERPAPI: "http://localhost:8003",
  NEWS_PLATFORM: "http://localhost:8000",
  FINANCE_API: "http://localhost:8000",
  ECONOMY_PLATFORM: "http://localhost:8002",
} as const;

// Provider configuration
export interface DataProvider {
  id: string;
  name: string;
  baseUrl: string;
  priority: number;
  healthEndpoint: string;
  timeout: number;
  retryAttempts: number;
}

export interface DataRequest {
  type: 'news' | 'finance' | 'economy';
  endpoint: string;
  params?: Record<string, any>;
  preferredProvider?: string;
  fallbackProviders?: string[];
}

export interface UnifiedResponse {
  data: any;
  provider: string;
  cached: boolean;
  timestamp: number;
  error?: string;
}

interface CacheEntry {
  data: any;
  provider: string;
  timestamp: number;
  ttl: number;
}

class UnifiedDataService {
  private cache = new Map<string, CacheEntry>();
  private healthStatus = new Map<string, boolean>();
  private lastHealthCheck = new Map<string, number>();

  private providers: Record<string, DataProvider> = {
    serpapi: {
      id: 'serpapi',
      name: 'SerpAPI (Google Proxy)',
      baseUrl: API_ENDPOINTS.SERPAPI,
      priority: 1,
      healthEndpoint: '/health',
      timeout: 15000,
      retryAttempts: 3,
    },
    newsplatform: {
      id: 'newsplatform',
      name: 'News Platform (RSS Feeds)',
      baseUrl: API_ENDPOINTS.NEWS_PLATFORM,
      priority: 2,
      healthEndpoint: '/health',
      timeout: 10000,
      retryAttempts: 2,
    },
    financeapi: {
      id: 'financeapi',
      name: 'Finance API (Scrapers)',
      baseUrl: API_ENDPOINTS.FINANCE_API,
      priority: 2,
      healthEndpoint: '/health',
      timeout: 12000,
      retryAttempts: 2,
    },
    economyplatform: {
      id: 'economyplatform',
      name: 'Economy Platform (Gov Data)',
      baseUrl: API_ENDPOINTS.ECONOMY_PLATFORM,
      priority: 1,
      healthEndpoint: '/health',
      timeout: 10000,
      retryAttempts: 2,
    },
  };

  // Cache management
  private getCacheKey(request: DataRequest): string {
    return `${request.type}:${request.endpoint}:${JSON.stringify(request.params || {})}`;
  }

  private getFromCache(key: string): any {
    const entry = this.cache.get(key);
    if (!entry) return null;
    
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return entry.data;
  }

  private setCache(key: string, data: any, provider: string, ttl: number): void {
    this.cache.set(key, {
      data,
      provider,
      timestamp: Date.now(),
      ttl,
    });
  }

  // Health monitoring
  async checkProviderHealth(providerId: string): Promise<boolean> {
    const lastCheck = this.lastHealthCheck.get(providerId);
    const now = Date.now();
    
    // Don't check more than once per minute
    if (lastCheck && (now - lastCheck) < 60000) {
      return this.healthStatus.get(providerId) || false;
    }

    const provider = this.providers[providerId];
    if (!provider) return false;

    try {
      const response = await axios.get(
        `${provider.baseUrl}${provider.healthEndpoint}`,
        { timeout: 5000 }
      );
      const isHealthy = response.status === 200 && response.data?.status === 'ok';
      this.healthStatus.set(providerId, isHealthy);
      this.lastHealthCheck.set(providerId, now);
      return isHealthy;
    } catch (error) {
      console.warn(`Health check failed for ${providerId}:`, error);
      this.healthStatus.set(providerId, false);
      this.lastHealthCheck.set(providerId, now);
      return false;
    }
  }

  async checkAllProvidersHealth(): Promise<void> {
    const checks = Object.keys(this.providers).map(id => 
      this.checkProviderHealth(id)
    );
    await Promise.allSettled(checks);
  }

  // Request with retry logic
  private async requestWithRetry(
    provider: DataProvider,
    endpoint: string,
    params?: Record<string, any>
  ): Promise<any> {
    const url = `${provider.baseUrl}${endpoint}`;
    const config = {
      timeout: provider.timeout,
      headers: {
        'User-Agent': this.getRandomUserAgent(),
        'Accept': 'application/json',
      },
    };

    let lastError: any;
    
    for (let attempt = 1; attempt <= provider.retryAttempts; attempt++) {
      try {
        const response = await axios.get(url, { ...config, params });
        return response.data;
      } catch (error: any) {
        lastError = error;
        
        // Don't retry on client errors (4xx)
        if (error.response?.status >= 400 && error.response?.status < 500) {
          break;
        }
        
        // Wait before retry with exponential backoff
        if (attempt < provider.retryAttempts) {
          const delay = Math.min(1000 * Math.pow(2, attempt), 10000);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    
    throw lastError;
  }

  // User agent rotation for bypassing restrictions
  private getRandomUserAgent(): string {
    const userAgents = [
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0',
      'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
    ];
    return userAgents[Math.floor(Math.random() * userAgents.length)];
  }

  // Get provider chain based on health and preference
  private async getProviderChain(
    request: DataRequest
  ): Promise<DataProvider[]> {
    const chain: DataProvider[] = [];
    
    // Add preferred provider if specified and healthy
    if (request.preferredProvider) {
      const provider = this.providers[request.preferredProvider];
      if (provider) {
        const isHealthy = await this.checkProviderHealth(request.preferredProvider);
        if (isHealthy) {
          chain.push(provider);
        }
      }
    }
    
    // Add healthy providers by priority
    const healthyProviders = Object.values(this.providers)
      .filter(p => {
        const isHealthy = this.healthStatus.get(p.id);
        return isHealthy !== false; // Include unknown status
      })
      .sort((a, b) => a.priority - b.priority);
    
    for (const provider of healthyProviders) {
      if (!chain.find(p => p.id === provider.id)) {
        chain.push(provider);
      }
    }
    
    // Add all providers as last resort
    const allProviders = Object.values(this.providers)
      .sort((a, b) => a.priority - b.priority);
    
    for (const provider of allProviders) {
      if (!chain.find(p => p.id === provider.id)) {
        chain.push(provider);
      }
    }
    
    return chain;
  }

  // Main request method
  async request(request: DataRequest): Promise<UnifiedResponse> {
    const cacheKey = this.getCacheKey(request);
    
    // Check cache first
    const cached = this.getFromCache(cacheKey);
    if (cached) {
      return {
        data: cached,
        provider: 'cache',
        cached: true,
        timestamp: Date.now(),
      };
    }

    const providerChain = await this.getProviderChain(request);
    let lastError: any;

    for (const provider of providerChain) {
      try {
        const data = await this.requestWithRetry(provider, request.endpoint, request.params);
        
        // Cache successful response
        const ttl = this.getTTL(request.type);
        this.setCache(cacheKey, data, provider.id, ttl);
        
        return {
          data,
          provider: provider.id,
          cached: false,
          timestamp: Date.now(),
        };
      } catch (error: any) {
        lastError = error;
        console.warn(`Request failed for ${provider.id}:`, error);
        
        // Mark provider as unhealthy
        this.healthStatus.set(provider.id, false);
      }
    }

    // All providers failed
    return {
      data: null,
      provider: 'none',
      cached: false,
      timestamp: Date.now(),
      error: lastError?.message || 'All providers failed',
    };
  }

  private getTTL(type: string): number {
    const ttls = {
      news: 5 * 60 * 1000,      // 5 minutes
      finance: 1 * 60 * 1000,    // 1 minute
      economy: 5 * 60 * 1000,    // 5 minutes
    };
    return ttls[type as keyof typeof ttls] || 5 * 60 * 1000;
  }

  // Convenience methods for different data types
  async getNews(params: {
    category?: string;
    country?: string;
    search?: string;
    count?: number;
  } = {}): Promise<UnifiedResponse> {
    if (params.search) {
      return this.request({
        type: 'news',
        endpoint: '/api/news/search',
        params: { q: params.search, gl: params.country || 'us' },
        preferredProvider: 'serpapi',
        fallbackProviders: ['newsplatform'],
      });
    }

    if (params.category) {
      return this.request({
        type: 'news',
        endpoint: '/api/news/topic',
        params: { topic: params.category, gl: params.country || 'us' },
        preferredProvider: 'serpapi',
        fallbackProviders: ['newsplatform'],
      });
    }

    return this.request({
      type: 'news',
      endpoint: '/api/news/top',
      params: { gl: params.country || 'us' },
      preferredProvider: 'serpapi',
      fallbackProviders: ['newsplatform'],
    });
  }

  async getFinance(params: {
    ticker?: string;
    market?: string;
    trend?: string;
    country?: string;
  } = {}): Promise<UnifiedResponse> {
    if (params.ticker) {
      return this.request({
        type: 'finance',
        endpoint: '/api/finance/quote',
        params: { q: params.ticker },
        preferredProvider: 'serpapi',
        fallbackProviders: ['financeapi'],
      });
    }

    if (params.trend) {
      return this.request({
        type: 'finance',
        endpoint: '/api/finance/markets',
        params: { trend: params.trend, gl: params.country || 'us' },
        preferredProvider: 'serpapi',
        fallbackProviders: ['financeapi'],
      });
    }

    return this.request({
      type: 'finance',
      endpoint: '/api/finance/overview',
      params: { gl: params.country || 'us' },
      preferredProvider: 'serpapi',
      fallbackProviders: ['financeapi'],
    });
  }

  async getEconomy(params: {
    indicator?: string;
    country?: string;
    sector?: string;
  } = {}): Promise<UnifiedResponse> {
    if (params.indicator) {
      return this.request({
        type: 'economy',
        endpoint: `/api/india/indicator/${params.indicator}`,
        preferredProvider: 'economyplatform',
        fallbackProviders: ['serpapi'],
      });
    }

    return this.request({
      type: 'economy',
      endpoint: '/api/global/calendar',
      preferredProvider: 'economyplatform',
      fallbackProviders: ['serpapi'],
    });
  }

  // Health check methods
  getProviderStatus(): Record<string, boolean> {
    const status: Record<string, boolean> = {};
    for (const [id, isHealthy] of this.healthStatus) {
      status[id] = isHealthy;
    }
    return status;
  }

  async refreshAllProviders(): Promise<void> {
    await this.checkAllProvidersHealth();
  }
}

// Export singleton instance
export const unifiedDataService = new UnifiedDataService();
export default unifiedDataService;
