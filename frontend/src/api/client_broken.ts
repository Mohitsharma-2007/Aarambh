import axios, { AxiosInstance, AxiosError } from 'axios'

// API client configuration
// In dev mode: use empty string so requests go through the Vite proxy (vite.config.ts)
// In production: use VITE_API_URL env var to point to the backend
const API_BASE_URL = import.meta.env.VITE_API_URL || ''

// Create axios instance with shorter timeout
const axiosInstance: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // Reduced from 30s to 10s for faster failure
  headers: {
    'Content-Type': 'application/json',
  },
})

// Retry helper for transient failures
const withRetry = async <T>(
  fn: () => Promise<T>,
  maxRetries: number = 2,
  delay: number = 500
): Promise<T> => {
  let lastError: any
  for (let i = 0; i <= maxRetries; i++) {
    try {
      return await fn()
    } catch (err: any) {
      lastError = err
      // Don't retry on 4xx errors (client errors)
      if (err?.response?.status >= 400 && err?.response?.status < 500) {
        throw err
      }
      if (i < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, delay * (i + 1)))
      }
    }
  }
  throw lastError
}

// Request interceptor
axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
axiosInstance.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// API client class
class APIClient {
  private client = axiosInstance

  // Auth
  async login(email: string, password: string) {
    const response = await this.client.post('/api/v1/auth/login', { email, password })
    return response.data
  }

  async register(email: string, password: string, name: string) {
    const response = await this.client.post('/api/v1/auth/register', { email, password, name })
    return response.data
  }

  async getMe() {
    const response = await this.client.get('/api/v1/auth/me')
    return response.data
  }

  // Feed/Events
  async getEvents(params?: { domain?: string; search?: string; page?: number; page_size?: number }) {
    const response = await this.client.get('/api/v1/events/', { params })
    return response.data
  }

  async getEarningsCalendar() {
    const response = await this.client.get('/api/v1/market/earnings-calendar')
    return response.data
  }

  async getEconomicCalendar() {
    const response = await this.client.get('/api/v1/economy/calendar')
    return response.data
  }

  async analyzeNewsImpact(data: { event_id: string; title: string; summary: string; domain: string; entities: any[] }) {
    const response = await this.client.post('/api/v1/ai/analyze-impact', data)
    return response.data
  }

  async triggerIngestionBackground() {
    const response = await this.client.post('/api/v1/ingestion/trigger')
    return response.data
  }

  // Market Data
  async getMarketHeatmap(): Promise<{ data: any[] }> {
    return withRetry(async () => {
      const response = await this.client.get('/api/v1/market/heatmap')
      return response.data
    })
  }

  async getStockQuote(ticker: string): Promise<any> {
    return withRetry(async () => {
      const response = await this.client.get(`/api/v1/market/quote/${ticker}`)
      return response.data
    })
  }

  async getStockHistory(ticker: string, period: string = '1M'): Promise<any[]> {
    return withRetry(async () => {
      const response = await this.client.get(`/api/v1/market/history/${ticker}`, {
        params: { period }
      })
      return response.data
    })
  }

  async getMarketIndices(): Promise<any[]> {
    return withRetry(async () => {
      const response = await this.client.get('/api/v1/market/indices')
      return response.data
    })
  }

  async getMarketCrypto(): Promise<any[]> {
    const response = await this.client.get('/api/v1/market/crypto')
    return response.data
  }

  // AI
  async getAIProviders() {
    const response = await this.client.get('/api/v1/ai/providers')
    return response.data
  }

  async sendChatMessage(data: {
    message: string
    conversation_id?: string
    provider?: string
    model?: string
    tools?: string[]
    agent_id?: string
  }) {
    const response = await this.client.post('/api/v1/ai/chat', data)
    return response.data
  }

  async getConversations() {
    const response = await this.client.get('/api/v1/ai/conversations')
    return response.data
  }

  async getConversationMessages(conversationId: string) {
    const response = await this.client.get(`/api/v1/ai/conversations/${conversationId}/messages`)
    return response.data
  }

  async getAITools() {
    const response = await this.client.get('/api/v1/ai/tools')
    return response.data
  }

  async getAIAgents() {
    const response = await this.client.get('/api/v1/ai/agents')
    return response.data
  }

  // Graph/Ontology
  async createGraph(data: { name: string; description?: string }) {
    const response = await this.client.post('/api/graph/create', data)
    return response.data
  }

  async listGraphs() {
    const response = await this.client.get('/api/graph/list')
    return response.data
  }

  async getGraphData(graphId: string) {
    const response = await this.client.get(`/api/graph/data/${graphId}`)
    return response.data
  }

  async generateOntology(data: FormData) {
    const response = await this.client.post('/api/graph/ontology/generate', data, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  }

  async buildGraph(data: { project_id: string; graph_name?: string }) {
    const response = await this.client.post('/api/graph/build', data)
    return response.data
  }

  async getProjectState(projectId: string) {
    const response = await this.client.get(`/api/graph/project/${projectId}/state`)
    return response.data
  }

  async getTaskStatus(taskId: string) {
    const response = await this.client.get(`/api/graph/task/${taskId}`)
    return response.data
  }

  // Simulation
  async createSimulation(data: any) {
    const response = await this.client.post('/api/simulation/create', data)
    return response.data
  }

  async listSimulations() {
    const response = await this.client.get('/api/simulation/list')
    return response.data
  }

  async getSimulation(id: string) {
    const response = await this.client.get(`/api/simulation/${id}`)
    return response.data
  }

  // Report
  async generateReport(data: { simulation_id: string }) {
    const response = await this.client.post('/api/report/generate', data)
    return response.data
  }

  async getReport(id: string) {
    const response = await this.client.get(`/api/report/${id}`)
    return response.data
  }

  // Treasury
  async getTreasuryYields() {
    const response = await this.client.get('/api/v1/economy/treasury-yields')
    return response.data
  }

  // Economy
  async getEconomyOverview() {
    const response = await this.client.get('/api/v1/economy/overview')
    return response.data
  }

  // Signals
  async getSignals() {
    const response = await this.client.get('/api/v1/signals/')
    return response.data
  }

  async createSignal(data: any) {
    const response = await this.client.post('/api/v1/signals/', data)
    return response.data
  }

  async pauseSignal(signalId: string) {
    const response = await this.client.put(`/api/v1/signals/${signalId}/pause`)
    return response.data
  }

  async resumeSignal(signalId: string) {
    const response = await this.client.put(`/api/v1/signals/${signalId}/resume`)
    return response.data
  }

  // Investors
  async getFunds() {
    const response = await this.client.get('/api/v1/investors/funds')
    return response.data
  }

  async getFundHoldings(cik: string) {
    const response = await this.client.get(`/api/v1/investors/funds/${cik}/holdings`)
    return response.data
  }

  async getPortfolios() {
    const response = await this.client.get('/api/v1/investors/portfolios')
    return response.data
  }

  async getCongressTrades(params?: { chamber?: string; ticker?: string }) {
    const response = await this.client.get('/api/v1/investors/congress', { params })
    return response.data
  }

  // Market Data - Additional endpoints
  async getStockCandles(ticker: string, timeframe: string = '1d', period: string = '6mo') {
    const response = await this.client.get(`/api/v1/market/candles/${ticker}`, {
      params: { timeframe, period }
    })
    return response.data
  }

  async getStockProfile(ticker: string) {
    const response = await this.client.get(`/api/v1/market/profile/${ticker}`)
    return response.data
  }

  async getStockFinancials(ticker: string) {
    const response = await this.client.get(`/api/v1/market/financials/${ticker}`)
    return response.data
  }

  async getStockOwnership(ticker: string) {
    const response = await this.client.get(`/api/v1/market/ownership/${ticker}`)
    return response.data
  }

  async getStockRatings(ticker: string) {
    const response = await this.client.get(`/api/v1/market/ratings/${ticker}`)
    return response.data
  }

  async getSectors() {
    const response = await this.client.get('/api/v1/market/sectors')
    return response.data
  }

  async getCommodities() {
    const response = await this.client.get('/api/v1/market/commodities')
    return response.data
  }

  async getFX() {
    const response = await this.client.get('/api/v1/market/fx')
    return response.data
  }

  // ==================== UNIFIED DATA BRIDGE ENDPOINTS ====================

  async getDataStatus() {
    const response = await this.client.get('/api/v1/data/status')
    return response.data
  }

  async getMarketDashboard() {
    const response = await this.client.get('/api/v1/data/dashboard')
    return response.data
  }

  async getEconomyDashboard() {
    const response = await this.client.get('/api/v1/data/economy-dashboard')
    return response.data
  }

  async getGlobalIntelligence() {
    const response = await this.client.get('/api/v1/data/intelligence')
    return response.data
  }

  // ==================== NEWS ENDPOINTS ====================

  async getNewsHeadlines(count: number = 50) {
    const response = await this.client.get('/api/v1/news/headlines', { params: { count } })
    return response.data
  }

  async getFinanceNews(count: number = 50) {
    const response = await this.client.get('/api/v1/news/finance', { params: { count } })
    return response.data
  }

  async searchNews(query: string, count: number = 30) {
    const response = await this.client.get('/api/v1/news/search', { params: { q: query, count } })
    return response.data
  }

  async getNewsByCategory(category: string, count: number = 40) {
    const response = await this.client.get(`/api/v1/news/category/${category}`, { params: { count } })
    return response.data
  }

  async getTrendingTopics() {
    const response = await this.client.get('/api/v1/news/trending')
    return response.data
  }

  async getGeopoliticalNews() {
    const response = await this.client.get('/api/v1/news/geopolitical')
    return response.data
  }

  // ==================== STOCK RESEARCH ====================

  async getStockResearch(ticker: string) {
    const response = await this.client.get(`/api/v1/market/research/${ticker}`)
    return response.data
  }

  // ==================== ECONOMY DATA ====================

  async getWorldBankData(country: string = 'IN', indicator: string = 'NY.GDP.MKTP.CD') {
    const response = await this.client.get('/api/v1/economy/world-bank', { params: { country, indicator } })
    return response.data
  }

  async getIMFData(indicator: string = 'NGDPD', country: string = 'IN') {
    const response = await this.client.get('/api/v1/economy/imf', { params: { indicator, country } })
    return response.data
  }

  async getFREDData(series: string = 'GDP', limit: number = 20) {
    const response = await this.client.get('/api/v1/economy/fred', { params: { series, limit } })
    return response.data
  }

  async getPIBLatest() {
    const response = await this.client.get('/api/v1/economy/pib/latest')
    return response.data
  }

  async getIPOCalendar() {
    const response = await this.client.get('/api/v1/economy/ipo')
    return response.data
  }

  async getDividendCalendar(date?: string) {
    const response = await this.client.get('/api/v1/economy/dividends', { params: { date } })
    return response.data
  }

  // ==================== MARKET MOVERS ====================

  async getMarketMovers(type: 'day_gainers' | 'day_losers' | 'most_actives' = 'day_gainers', count: number = 25) {
    const response = await this.client.get('/api/v1/market/movers', { params: { type, count } })
    return response.data
  }

  async getTrendingTickers(region: string = 'US') {
    const response = await this.client.get('/api/v1/market/trending', { params: { region } })
    return response.data
  }

  async searchStocks(query: string) {
    const response = await this.client.get('/api/v1/market/search', { params: { q: query } })
    return response.data
  }

  // ==================== NEO4J GRAPH API ====================

  async getNeo4jStats() {
    const response = await this.client.get('/api/v1/graph/neo4j/stats')
    return response.data
  }

  async getStockNetwork(ticker: string, depth: number = 2) {
    const response = await this.client.get(`/api/v1/graph/neo4j/stock/${ticker}/network`, {
      params: { depth }
    })
    return response.data
  }

  async getStockRelationships(ticker: string) {
    const response = await this.client.get(`/api/v1/graph/neo4j/stock/${ticker}/relationships`)
    return response.data
  }

  async searchGraphEntities(query: string, type?: string, limit: number = 20) {
    const response = await this.client.get('/api/v1/graph/neo4j/search', {
      params: { q: query, type, limit }
    })
    return response.data
  }

  async findGraphPath(
    fromId: string, toId: string,
    fromType: string = 'Stock', toType: string = 'Stock',
    maxDepth: number = 5
  ) {
    const response = await this.client.get('/api/v1/graph/neo4j/path', {
      params: { from_id: fromId, to_id: toId, from_type: fromType, to_type: toType, max_depth: maxDepth }
    })
    return response.data
  }

  // ==================== WEBSOCKET API ====================

  async getWebSocketStatus() {
    const response = await this.client.get('/api/v1/websocket/status')
    return response.data
  }
}

// Export singleton instance
export const api = new APIClient()

// Also export the axios instance for raw requests
export { axiosInstance }

// For backwards compatibility
export default api

// ==================== DIRECT PLATFORM API CLIENTS ====================
// These clients connect directly to the platform APIs for specialized features

import axios from 'axios'

// Finance API Client (Port 8000) - Google Finance, Yahoo Finance, Google News, Google AI
export const financeApiClient = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' }
})

export const FinanceAPI = {
  // Google Finance
  async getGoogleFinanceQuote(ticker: string, exchange: string = 'NASDAQ') {
    const response = await financeApiClient.get(`/api/google-finance/quote/${ticker}/${exchange}`)
    return response.data
  },

  // Yahoo Finance
  async getYahooFinanceQuote(ticker: string) {
    const response = await financeApiClient.get(`/api/yahoo-finance/quote/${ticker}`)
    return response.data
  },

  async getYahooFinanceChart(ticker: string, interval: string = '1d', range: string = '3mo') {
    const response = await financeApiClient.get(`/api/yahoo-finance/chart/${ticker}`, {
      params: { interval, range }
    })
    return response.data
  },

  async getYahooMarketMovers(type: string = 'day_gainers') {
    const response = await financeApiClient.get('/api/yahoo-finance/movers', {
      params: { type }
    })
    return response.data
  },

  // Google News
  async getGoogleNewsHeadlines(country: string = 'US') {
    const response = await financeApiClient.get('/api/google-news/headlines', {
      params: { country }
    })
    return response.data
  },

  async searchGoogleNews(query: string, country?: string) {
    const response = await financeApiClient.get('/api/google-news/search', {
      params: { q: query, country }
    })
    return response.data
  },

  async getGoogleNewsTopic(topic: string) {
    const response = await financeApiClient.get(`/api/google-news/topic/${topic}`)
    return response.data
  },

  async getGoogleNewsTicker(ticker: string) {
    const response = await financeApiClient.get(`/api/google-news/ticker/${ticker}`)
    return response.data
  },

  async getGoogleNewsCompany(company: string, ticker?: string) {
    const response = await financeApiClient.get(`/api/google-news/company/${company}`, {
      params: ticker ? { ticker } : undefined
    })
    return response.data
  },

  // Google AI
  async getGoogleAIOverview(query: string) {
    const response = await financeApiClient.get('/api/google-ai/overview', {
      params: { q: query }
    })
})
return response.data
},

async getYahooMarketMovers(type: string = 'day_gainers') {
const response = await financeApiClient.get('/api/yahoo-finance/movers', {
params: { type }
})
return response.data
},

// Google News
async getGoogleNewsHeadlines(country: string = 'US') {
const response = await financeApiClient.get('/api/google-news/headlines', {
params: { country }
})
return response.data
},

async searchGoogleNews(query: string, country?: string) {
const response = await financeApiClient.get('/api/google-news/search', {
params: { q: query, country }
})
return response.data
},

async getGoogleNewsTopic(topic: string) {
const response = await financeApiClient.get(`/api/google-news/topic/${topic}`)
return response.data
},

async getGoogleNewsTicker(ticker: string) {
const response = await financeApiClient.get(`/api/google-news/ticker/${ticker}`)
return response.data
},

async getGoogleNewsCompany(company: string, ticker?: string) {
const response = await financeApiClient.get(`/api/google-news/company/${company}`, {
params: ticker ? { ticker } : undefined
})
return response.data
},

// Google AI
async getGoogleAIOverview(query: string) {
const response = await financeApiClient.get('/api/google-ai/overview', {
params: { q: query }
})
return response.data
},

async getGoogleFinanceSummary(ticker: string) {
const response = await financeApiClient.get(`/api/google-ai/finance-summary/${ticker}`)
return response.data
},

// Site Index
async getFinanceSiteIndex() {
const response = await financeApiClient.get('/api/site-index')
return response.data
}
}

export const NewsAPI = {
// News Feed
async getNewsHeadlines() {
const response = await newsApiClient.get('/api/news/headlines')
return response.data
},
    const response = await newsApiClient.get('/api/news/headlines')
    return response.data
  },

  async getNewsCategory(category: string) {
    const response = await newsApiClient.get(`/api/news/category/${category}`)
    return response.data
  },

  async searchNews(query: string) {
    const response = await newsApiClient.get('/api/news/search', { params: { q: query } })
    return response.data
  },

  async getNewsSentiment() {
    const response = await newsApiClient.get('/api/news/sentiment')
    return response.data
  },

  // Live TV
  async getLiveTVChannels() {
    const response = await newsApiClient.get('/api/live/tv/channels')
    return response.data
  },

  async getLiveTVSchedule(channel: string) {
    const response = await newsApiClient.get(`/api/live/tv/schedule/${channel}`)
    return response.data
  },

  // Health Data
  async getHealthOutbreaks() {
    const response = await newsApiClient.get('/api/health/cdc')
    return response.data
  },

  async getHealthWHO() {
    const response = await newsApiClient.get('/api/health/who')
    return response.data
  },

  // Geopolitical
  async getGeopoliticalGDELT(query?: string) {
    const response = await newsApiClient.get('/api/geo/gdelt', {
      params: query ? { query } : undefined
    })
    return response.data
  },

  async getGeopoliticalACLED() {
    const response = await newsApiClient.get('/api/geo/acled')
    return response.data
  },

  // AI Analysis
  async getAIBriefing() {
    const response = await newsApiClient.get('/api/ai/briefing')
    return response.data
  },

  async getAICompare(asset1: string, asset2: string) {
    const response = await newsApiClient.get('/api/ai/compare', {
      params: { a: asset1, b: asset2 }
    })
    return response.data
  },

  async getAITrends(query?: string) {
    const response = await newsApiClient.get('/api/ai/trends', {
      params: query ? { q: query } : undefined
    })
    return response.data
  },

  // Site Index
  async getNewsSiteIndex() {
    const response = await newsApiClient.get('/api/site-index')
    return response.data
  }
}

// Economy Platform Client (Port 8002) - India Gov, Global Economy, Documents, AI
export const economyApiClient = axios.create({
  baseURL: 'http://localhost:8002',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' }
})

export const EconomyAPI = {
  // India Government Data
  async getIndiaIndicator(indicator: string) {
    const response = await economyApiClient.get(`/api/india/indicator/${indicator}`)
    return response.data
  },

  async getPIBLatest() {
    const response = await economyApiClient.get('/api/pib/latest')
    return response.data
  },

  async getNDAPData() {
    const response = await economyApiClient.get('/api/ndap/latest')
    return response.data
  },

  async getMoSPIData() {
    const response = await economyApiClient.get('/api/mospi/latest')
    return response.data
  },

  // Global Economy
  async getIMFData(indicator: string = 'NGDPD', country: string = 'IN') {
    const response = await economyApiClient.get('/api/global/imf', {
      params: { indicator, country }
    })
    return response.data
  },

  async getWorldBankData(country: string = 'IN', indicator: string = 'NY.GDP.MKTP.CD') {
    const response = await economyApiClient.get('/api/global/world-bank', {
      params: { country, indicator }
    })
    return response.data
  },

  async getOECDData() {
    const response = await economyApiClient.get('/api/global/oecd')
    return response.data
  },

  // Sectors
  async getIndiaSectors() {
    const response = await economyApiClient.get('/api/sectors/india')
    return response.data
  },

  async getGlobalSectors() {
    const response = await economyApiClient.get('/api/sectors/global')
    return response.data
  },

  // Documents
  async searchDocuments(query: string) {
    const response = await economyApiClient.get('/api/documents/search', {
      params: { q: query }
    })
    return response.data
  },

  async parseDocument(url: string) {
    const response = await economyApiClient.post('/api/documents/parse', { url })
    return response.data
  },

  // AI Analysis
  async getEconomyAIAnalysis(query: string) {
    const response = await economyApiClient.get('/api/ai/analysis', {
      params: { q: query }
    })
    return response.data
  },

  async getEconomyAIForecast(indicator: string) {
    const response = await economyApiClient.get('/api/ai/forecast', {
      params: { indicator }
    })
    return response.data
  },

  // Site Index
  async getEconomySiteIndex() {
    const response = await economyApiClient.get('/api/site-index')
    return response.data
  },

  // ========== MISSING PLATFORM API METHODS ==========

  // Google Finance API - Additional Methods
  async getGoogleFinanceSummary(ticker: string, exchange: string) {
    const response = await financeApiClient.get(`/api/google-finance/summary/${ticker}/${exchange}`)
    return response.data
  },

  async getGoogleNewsSearch(query: string, country?: string) {
    const response = await financeApiClient.get('/api/google-news/search', {
      params: { q: query, country }
    })
    return response.data
  },

  async getGoogleNewsTopic(topic: string) {
    const response = await financeApiClient.get(`/api/google-news/topic/${topic}`)
    return response.data
  },

  async getGoogleNewsTicker(ticker: string) {
    const response = await financeApiClient.get(`/api/google-news/ticker/${ticker}`)
    return response.data
  },

  // Yahoo Finance API - Additional Methods
  async getYahooMarketMovers(type: 'day_gainers' | 'day_losers' | 'most_active' | 'most_losers') {
    const response = await financeApiClient.get(`/api/yahoo-finance/movers/${type}`)
    return response.data
  },

  async getYahooMarketIndices() {
    const response = await financeApiClient.get('/api/yahoo-finance/indices')
    return response.data
  },

  async getYahooStockHistory(ticker: string, period?: string) {
    const response = await financeApiClient.get(`/api/yahoo-finance/history/${ticker}`, {
      params: { period }
    })
    return response.data
  },

  // News Platform API - Additional Methods
  async getNewsByCategory(category: string) {
    const response = await newsApiClient.get(`/api/news/category/${category}`)
    return response.data
  },

  async getNewsBySource(source: string) {
    const response = await newsApiClient.get(`/api/news/source/${source}`)
    return response.data
  },

  async getLiveTVChannels() {
    const response = await newsApiClient.get('/api/live-tv/channels')
    return response.data
  },

  async getGeopoliticalGDELT() {
    const response = await newsApiClient.get('/api/geopolitical/gdelt')
    return response.data
  },

  async getGeopoliticalEvents() {
    const response = await newsApiClient.get('/api/geopolitical/events')
    return response.data
  },

  async getHealthData() {
    const response = await newsApiClient.get('/api/health/data')
    return response.data
  },

  async getAICompare(asset1: string, asset2: string) {
    const response = await newsApiClient.get(`/api/ai/compare/${asset1}/${asset2}`)
    return response.data
  },

  // Economy Platform API - Additional Methods
  async getPIBLatest() {
    const response = await economyApiClient.get('/api/india/pib/latest')
    return response.data
  },

  async getPIBSector(sector: string) {
    const response = await economyApiClient.get(`/api/india/pib/sector/${sector}`)
    return response.data
  },

  async getNDAPData(dataset: string) {
    const response = await economyApiClient.get(`/api/india/ndap/${dataset}`)
    return response.data
  },

  async getMoSPIIndicator(indicator: string) {
    const response = await economyApiClient.get(`/api/india/mospi/${indicator}`)
    return response.data
  },

  async getIndiaSectors() {
    const response = await economyApiClient.get('/api/india/sectors')
    return response.data
  },

  async getGlobalIMFData(indicator: string, country?: string) {
    const response = await economyApiClient.get('/api/global/imf', {
      params: { indicator, country }
    })
    return response.data
  },

  async getGlobalWorldBankData(indicator: string, country?: string) {
    const response = await economyApiClient.get('/api/global/worldbank', {
      params: { indicator, country }
    })
    return response.data
  },

  async getGlobalFREDData(series: string) {
    const response = await economyApiClient.get('/api/global/fred', {
      params: { series }
    })
    return response.data
  },

  async getEconomySectors() {
    const response = await economyApiClient.get('/api/economy/sectors')
    return response.data
  },

  // AI and Processing Methods
  async processNewsWithAI(newsData: any[]) {
    const response = await newsApiClient.post('/api/ai/process-news', { newsData })
    return response.data
  },

  async generateSignals(newsData: any[], marketData: any[], economicData: any[]) {
    const response = await newsApiClient.post('/api/signals/generate', {
      newsData,
      marketData,
      economicData
    })
    return response.data
  },

  async getThreatLevels() {
    const response = await newsApiClient.get('/api/geopolitical/threats')
    return response.data
  },

  // Ontology and Knowledge Graph Methods
  async getOntologyData() {
    const response = await apiClient.get('/api/graph/data/latest')
    return response.data
  },

  async getEntityRelationships(entityId: string) {
    const response = await apiClient.get(`/api/graph/entity/${entityId}/relationships`)
    return response.data
  },

  async searchEntities(query: string) {
    const response = await apiClient.get('/api/graph/search', {
      params: { q: query }
    })
    return response.data
  },

  async generateOntologyReport(entityId: string) {
    const response = await apiClient.post(`/api/graph/report/${entityId}`)
    return response.data
  },

  // Simulation and Advanced Analytics
  async runSimulation(params: any) {
    const response = await apiClient.post('/api/simulation/run', params)
    return response.data
  },

  async getSimulationResults(simulationId: string) {
    const response = await apiClient.get(`/api/simulation/results/${simulationId}`)
    return response.data
  },

  async getQuantModels() {
    const response = await apiClient.get('/api/quant/models')
    return response.data
  },

  async runQuantModel(modelId: string, params: any) {
    const response = await apiClient.post(`/api/quant/run/${modelId}`, params)
    return response.data
  },

  async getQuantBacktest(modelId: string) {
    const response = await apiClient.get(`/api/quant/backtest/${modelId}`)
    return response.data
  }
}
