// API client for unified backend (port 8000)
const API_BASE = 'http://localhost:8000';

// Cache configuration
const CACHE_PREFIX = 'news_cache_';
const CACHE_EXPIRATION_TIME = 5 * 60 * 1000; // 5 minutes

class UnifiedAPI {
  private getCachedData(key: string): any | null {
    try {
      const cached = localStorage.getItem(CACHE_PREFIX + key);
      if (cached) {
        const { data, timestamp } = JSON.parse(cached);
        if (Date.now() - timestamp < CACHE_EXPIRATION_TIME) {
          console.log(`[Cache] Serving ${key} from cache`);
          return data;
        } else {
          console.log(`[Cache] ${key} expired`);
          localStorage.removeItem(CACHE_PREFIX + key);
        }
      }
    } catch (e) {
      console.error("[Cache] Error reading from cache:", e);
    }
    return null;
  }

  private setCachedData(key: string, data: any): void {
    try {
      const cacheEntry = { data, timestamp: Date.now() };
      localStorage.setItem(CACHE_PREFIX + key, JSON.stringify(cacheEntry));
      console.log(`[Cache] Stored ${key}`);
    } catch (e) {
      console.error("[Cache] Error writing to cache:", e);
    }
  }
  // Finance - Google
  async getGoogleQuote(ticker: string, exchange: string = 'NASDAQ') {
    try {
      const res = await fetch(`${API_BASE}/api/google-finance/quote/${ticker}/${exchange}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.error(`[Finance] Google Quote failed for ${ticker}:`, e);
      return { error: true, message: "Service temporarily unavailable" };
    }
  }

  async getGoogleMarket(section: string) {
    const res = await fetch(`${API_BASE}/api/google-finance/market/${section}`);
    return res.json();
  }

  // DEPRECATED: Removed due to reliability issues
  async getGoogleOverview() {
    console.warn("[Finance] getGoogleOverview is deprecated due to timeout issues.");
    return { error: true, message: "Service unavailable" };
  }

  async searchGoogleFinance(query: string) {
    const res = await fetch(`${API_BASE}/api/google-finance/search?q=${encodeURIComponent(query)}`);
    return res.json();
  }

  // Finance - Yahoo (REDIRECTED TO GOOGLE FOR STABILITY)
  async getYahooQuote(ticker: string) {
    console.log(`[Finance] Redirecting Yahoo Quote request for ${ticker} to Google Finance...`);
    const exchange = ticker.endsWith('.NS') ? 'NSE' : 'NASDAQ';
    const cleanTicker = ticker.replace('.NS', '');
    return this.getGoogleQuote(cleanTicker, exchange);
  }

  async getYahooTrending(region: string = 'US') {
    const res = await fetch(`${API_BASE}/api/yahoo-finance/trending?region=${region}`);
    return res.json();
  }

  async getYahooMovers(type: string = 'most_actives') {
    const res = await fetch(`${API_BASE}/api/yahoo-finance/movers?type=${type}`);
    return res.json();
  }

  async getYahooFinancials(ticker: string) {
    const res = await fetch(`${API_BASE}/api/yahoo-finance/financials/${ticker}`);
    return res.json();
  }

  // News - Enhanced Platform (port 8001) - Fixed all issues
  async getNewsHeadlines(page: number = 1, limit: number = 10, country?: string) {
    const cacheKey = `headlines_enhanced_page_${page}_limit_${limit}_${country || 'all'}`;
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    let url = `http://localhost:8000/api/news-enhanced/headlines?page=${page}&limit=${limit}`;
    if (country) {
      url += `&country=${country}`;
    }

    const res = await fetch(url);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  async getFeaturedNews(limit: number = 10) {
    const cacheKey = `featured_enhanced_${limit}`;
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    const res = await fetch(`http://localhost:8000/api/news-enhanced/featured?limit=${limit}`);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  async getLocationBasedNews(countryCode: string, page: number = 1, limit: number = 10) {
    const cacheKey = `location_enhanced_${countryCode}_page_${page}_limit_${limit}`;
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    const res = await fetch(`http://localhost:8000/api/news-enhanced/location/${countryCode}?page=${page}&limit=${limit}`);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  async getNewsByCategory(category: string, page: number = 1, limit: number = 10, country?: string) {
    const cacheKey = `category_enhanced_${category}_page_${page}_limit_${limit}_${country || 'all'}`;
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    let url = `http://localhost:8000/api/news-enhanced/category/${category}?page=${page}&limit=${limit}`;
    if (country) {
      url += `&country=${country}`;
    }

    const res = await fetch(url);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  async getArticleAIAnalysis(articleId: number) {
    const res = await fetch(`http://localhost:8000/api/news-enhanced/ai/analyze/${articleId}`);
    const data = await res.json();
    return data;
  }

  async getNewsByCountry(code: string) {
    const cacheKey = `country_${code}`;
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    const res = await fetch(`http://localhost:8000/api/news/country/${code}`);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  async searchNews(query: string) {
    const cacheKey = `search_${query}`;
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    const res = await fetch(`http://localhost:8000/api/news/search?q=${encodeURIComponent(query)}`);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  async getFinanceNews() {
    const cacheKey = 'finance_news';
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    const res = await fetch(`http://localhost:8000/api/news/category/finance`);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  // Live TV (port 8001) - Comprehensive with all Indian and global channels
  async getLiveTVChannels() {
    const cacheKey = 'live_tv_channels_comprehensive';
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    // Use comprehensive YouTube Data API for all channels
    const res = await fetch(`http://localhost:8000/api/live-tv-comprehensive/live-status`);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  async getIndiaChannels() {
    const cacheKey = 'india_channels';
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    const res = await fetch(`http://localhost:8000/api/live-tv-comprehensive/india`);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  async getIndiaGeneralNews() {
    const cacheKey = 'india_general_news';
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    const res = await fetch(`http://localhost:8000/api/live-tv-comprehensive/india/general-news`);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  async getIndiaFinanceNews() {
    const cacheKey = 'india_finance_news';
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    const res = await fetch(`http://localhost:8000/api/live-tv-comprehensive/india/finance-news`);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  async getGlobalChannels() {
    const cacheKey = 'global_channels';
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    const res = await fetch(`http://localhost:8000/api/live-tv-comprehensive/global`);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  async getGlobalGeneralNews() {
    const cacheKey = 'global_general_news';
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    const res = await fetch(`http://localhost:8000/api/live-tv-comprehensive/global/general-news`);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  async getGlobalFinanceNews() {
    const cacheKey = 'global_finance_news';
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    const res = await fetch(`http://localhost:8000/api/live-tv-comprehensive/global/finance-news`);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  async getLiveChannelsOnly() {
    const cacheKey = 'live_channels_only';
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    const res = await fetch(`http://localhost:8000/api/live-tv-comprehensive/live-only`);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  async getWarLiveStreams() {
    const cacheKey = 'war_live_streams';
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    // Use comprehensive YouTube Data API for war-related live streams
    const res = await fetch(`http://localhost:8000/api/live-tv-comprehensive/war-live`);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  async getFeaturedLiveTV() {
    const cacheKey = 'featured_live_tv';
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    const res = await fetch(`http://localhost:8000/api/live-tv-comprehensive/featured`);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  async getChannelLiveStatus(channelKey: string) {
    const res = await fetch(`http://localhost:8000/api/live-tv-comprehensive/channel/${channelKey}/status`);
    const data = await res.json();
    return data;
  }

  async getChannelEmbedUrl(channelKey: string) {
    const res = await fetch(`http://localhost:8000/api/live-tv-comprehensive/channel/${channelKey}/embed`);
    const data = await res.json();
    return data;
  }

  // Health (port 8001)
  async getHealthNews() {
    const cacheKey = 'health_news';
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    const res = await fetch(`http://localhost:8000/api/health/news`);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  // Geopolitical (port 8001)
  async getGeoConflicts() {
    const cacheKey = 'geo_conflicts';
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    const res = await fetch(`http://localhost:8000/api/geo/conflicts`);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  async getGeoSanctions() {
    const cacheKey = 'geo_sanctions';
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    const res = await fetch(`http://localhost:8000/api/geo/sanctions`);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  // AI (port 8001)
  async getAISummary(topic: string) {
    const cacheKey = `ai_summary_${topic}`;
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    const res = await fetch(`http://localhost:8000/api/ai/summarize?topic=${encodeURIComponent(topic)}`);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  async getAISentiment(topic: string) {
    const cacheKey = `ai_sentiment_${topic}`;
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    const res = await fetch(`http://localhost:8000/api/ai/sentiment?topic=${encodeURIComponent(topic)}`);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  // Enhanced AI Analysis (port 8001)
  async analyzeArticle(articleId: number, forceReanalyze: boolean = false) {
    const res = await fetch(`http://localhost:8000/api/ai-enhanced/analyze/${articleId}?force_reanalyze=${forceReanalyze}`, {
      method: 'POST'
    });
    return res.json();
  }

  async batchAnalyzeArticles(limit: number = 50, category?: string, forceReanalyze: boolean = false) {
    const body = {
      limit,
      category,
      force_reanalyze: forceReanalyze
    };

    const res = await fetch(`http://localhost:8000/api/ai-enhanced/batch-analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    });
    return res.json();
  }

  async getAIAnalysisStats() {
    const cacheKey = 'ai_stats';
    const cachedData = this.getCachedData(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    const res = await fetch(`http://localhost:8000/api/ai-enhanced/stats`);
    const data = await res.json();
    this.setCachedData(cacheKey, data);
    return data;
  }

  // Economy Platform (port 8002) - Verified India Gov Data
  async getPIBLatest() {
    const res = await fetch(`http://localhost:8000/api/pib/latest`);
    return res.json();
  }

  async getPIBSearch(query: string) {
    const res = await fetch(`http://localhost:8000/api/pib/search?q=${encodeURIComponent(query)}`);
    return res.json();
  }

  async getIndiaIndicator(indicator: string) {
    const res = await fetch(`http://localhost:8000/api/india/indicator/${indicator}`);
    return res.json();
  }

  async getMoSPIGDP() {
    const res = await fetch(`http://localhost:8000/api/mospi/gdp`);
    return res.json();
  }

  async getSectorData(sector: string) {
    const res = await fetch(`http://localhost:8000/api/sectors/${sector}`);
    return res.json();
  }

  async getGlobalEconomyData(indicator: string = "NGDPD") {
    const res = await fetch(`http://localhost:8000/api/global/imf?indicator=${indicator}`);
    return res.json();
  }

  async getFredData(seriesId: string) {
    const res = await fetch(`http://localhost:8000/api/global/fred?series_id=${seriesId}`);
    return res.json();
  }

  // Social Feeds (port 8002) — Reddit + World Leaders
  async getRedditTrending(subreddit: string = "economics", sort: string = "hot", limit: number = 15) {
    const res = await fetch(`http://localhost:8000/api/social/reddit/trending?subreddit=${subreddit}&sort=${sort}&limit=${limit}`);
    return res.json();
  }

  async getRedditMulti(limit: number = 5) {
    const res = await fetch(`http://localhost:8000/api/social/reddit/multi?limit=${limit}`);
    return res.json();
  }

  async getWorldLeaderCommentary(limit: number = 10) {
    const res = await fetch(`http://localhost:8000/api/social/world-leaders?limit=${limit}`);
    return res.json();
  }

  async getCorporateCommentary(limit: number = 10) {
    const res = await fetch(`http://localhost:8000/api/social/corporate?limit=${limit}`);
    return res.json();
  }
}

export const unifiedAPI = new UnifiedAPI();
