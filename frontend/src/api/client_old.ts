import axios from 'axios'

// API Client instances
const apiClient = axios.create({
  baseURL: 'http://localhost:5001/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

const financeApiClient = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

const newsApiClient = axios.create({
  baseURL: 'http://localhost:8001/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

const economyApiClient = axios.create({
  baseURL: 'http://localhost:8002/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Main API Class
export class APIClient {
  // Dashboard
  async getDashboardData() {
    const response = await apiClient.get('/dashboard')
    return response.data
  }

  async getThreatLevels() {
    const response = await apiClient.get('/threat-levels')
    return response.data
  }

  // Market Data
  async getMarketData() {
    const response = await apiClient.get('/market/data')
    return response.data
  }

  async getStockQuote(ticker: string) {
    const response = await apiClient.get(`/market/quote/${ticker}`)
    return response.data
  }

  async getStockProfile(ticker: string) {
    const response = await apiClient.get(`/market/profile/${ticker}`)
    return response.data
  }

  async getMarketHeatmap() {
    const response = await apiClient.get('/market/heatmap')
    return response.data
  }

  async getMarketIndices() {
    const response = await apiClient.get('/market/indices')
    return response.data
  }

  async getStockCandles(ticker: string, period?: string) {
    const response = await apiClient.get(`/market/candles/${ticker}`, {
      params: { period }
    })
    return response.data
  }

  async getStockHistory(ticker: string, period?: string) {
    const response = await apiClient.get(`/market/history/${ticker}`, {
      params: { period }
    })
    return response.data
  }

  // News
  async getNewsHeadlines() {
    const response = await newsApiClient.get('/news/headlines')
    return response.data
  }

  async getNewsByCategory(category: string) {
    const response = await newsApiClient.get(`/news/category/${category}`)
    return response.data
  }

  async getNewsBySource(source: string) {
    const response = await newsApiClient.get(`/news/source/${source}`)
    return response.data
  }

  // Economy
  async getEconomyDashboard() {
    const response = await apiClient.get('/economy/dashboard')
    return response.data
  }

  async getEconomyOverview() {
    const response = await apiClient.get('/economy/overview')
    return response.data
  }

  async getIndiaIndicator(indicator: string) {
    const response = await economyApiClient.get(`/india/indicator/${indicator}`)
    return response.data
  }

  async getIndiaSectors() {
    const response = await economyApiClient.get('/india/sectors')
    return response.data
  }

  async getEconomySectors() {
    const response = await economyApiClient.get('/economy/sectors')
    return response.data
  }

  // Signals
  async getSignals() {
    const response = await apiClient.get('/signals')
    return response.data
  }

  // AI
  async getAIProviders() {
    const response = await apiClient.get('/ai/providers')
    return response.data
  }

  async getAIOverview(query: string) {
    const response = await apiClient.get('/ai/overview', {
      params: { q: query }
    })
    return response.data
  }

  async getAIAnalysis(data: any) {
    const response = await apiClient.post('/ai/analysis', data)
    return response.data
  }

  // Ontology & Knowledge Graph
  async getOntologyData() {
    const response = await apiClient.get('/graph/data/latest')
    return response.data
  }

  async getEntityRelationships(entityId: string) {
    const response = await apiClient.get(`/graph/entity/${entityId}/relationships`)
    return response.data
  }

  async searchEntities(query: string) {
    const response = await apiClient.get('/graph/search', {
      params: { q: query }
    })
    return response.data
  }

  async generateOntologyReport(entityId: string) {
    const response = await apiClient.post(`/graph/report/${entityId}`)
    return response.data
  }

  // Simulation
  async runSimulation(params: any) {
    const response = await apiClient.post('/simulation/run', params)
    return response.data
  }

  async getSimulationResults(simulationId: string) {
    const response = await apiClient.get(`/simulation/results/${simulationId}`)
    return response.data
  }

  // Reports
  async getReports() {
    const response = await apiClient.get('/reports')
    return response.data
  }

  async getReport(id: string) {
    const response = await apiClient.get(`/reports/${id}`)
    return response.data
  }

  async generateReport(params: any) {
    const response = await apiClient.post('/reports/generate', params)
    return response.data
  }

  // Treasury
  async getTreasuryData() {
    const response = await apiClient.get('/treasury/data')
    return response.data
  }

  // Investors
  async getFunds() {
    const response = await apiClient.get('/investors/funds')
    return response.data
  }

  async getPortfolios() {
    const response = await apiClient.get('/investors/portfolios')
    return response.data
  }

  async getCongressTrades() {
    const response = await apiClient.get('/investors/congress-trades')
    return response.data
  }

  // Corporate
  async getCorporateEvents() {
    const response = await apiClient.get('/corporate/events')
    return response.data
  }

  async getEarningsCalendar() {
    const response = await apiClient.get('/corporate/earnings')
    return response.data
  }

  // Economic Calendar
  async getEconomicCalendar() {
    const response = await apiClient.get('/economy/calendar')
    return response.data
  }
}

// Finance API
export class FinanceAPI {
  // Google Finance
  async getGoogleFinanceSummary(ticker: string, exchange: string) {
    const response = await financeApiClient.get(`/google-finance/summary/${ticker}/${exchange}`)
    return response.data
  }

  async getGoogleNewsHeadlines(country: string = 'US') {
    const response = await financeApiClient.get('/google-news/headlines', {
      params: { country }
    })
    return response.data
  }

  async getGoogleNewsSearch(query: string, country?: string) {
    const response = await financeApiClient.get('/google-news/search', {
      params: { q: query, country }
    })
    return response.data
  }

  async getGoogleNewsTopic(topic: string) {
    const response = await financeApiClient.get(`/google-news/topic/${topic}`)
    return response.data
  }

  async getGoogleNewsTicker(ticker: string) {
    const response = await financeApiClient.get(`/google-news/ticker/${ticker}`)
    return response.data
  }

  async getGoogleNewsCompany(company: string, ticker?: string) {
    const response = await financeApiClient.get(`/google-news/company/${company}`, {
      params: ticker ? { ticker } : undefined
    })
    return response.data
  }

  // Google AI
  async getGoogleAIOverview(query: string) {
    const response = await financeApiClient.get('/google-ai/overview', {
      params: { q: query }
    })
    return response.data
  }

  // Yahoo Finance
  async getYahooMarketMovers(type: 'day_gainers' | 'day_losers' | 'most_active' | 'most_losers') {
    const response = await financeApiClient.get(`/yahoo-finance/movers/${type}`)
    return response.data
  }

  async getYahooMarketIndices() {
    const response = await financeApiClient.get('/yahoo-finance/indices')
    return response.data
  }

  async getYahooStockHistory(ticker: string, period?: string) {
    const response = await financeApiClient.get(`/yahoo-finance/history/${ticker}`, {
      params: { period }
    })
    return response.data
  }

  async getYahooStockQuote(ticker: string) {
    const response = await financeApiClient.get(`/yahoo-finance/quote/${ticker}`)
    return response.data
  }

  // Site Index
  async getFinanceSiteIndex() {
    const response = await financeApiClient.get('/site-index')
    return response.data
  }
}

// News Platform API
export class NewsAPI {
  // News Feed
  async getNewsHeadlines() {
    const response = await newsApiClient.get('/news/headlines')
    return response.data
  }

  async getNewsCategory(category: string) {
    const response = await newsApiClient.get(`/news/category/${category}`)
    return response.data
  }

  async getNewsSource(source: string) {
    const response = await newsApiClient.get(`/news/source/${source}`)
    return response.data
  }

  async searchNews(query: string) {
    const response = await newsApiClient.get('/news/search', {
      params: { q: query }
    })
    return response.data
  }

  // Live TV
  async getLiveTVChannels() {
    const response = await newsApiClient.get('/live-tv/channels')
    return response.data
  }

  // Geopolitical
  async getGeopoliticalGDELT() {
    const response = await newsApiClient.get('/geopolitical/gdelt')
    return response.data
  }

  async getGeopoliticalEvents() {
    const response = await newsApiClient.get('/geopolitical/events')
    return response.data
  }

  // Health
  async getHealthData() {
    const response = await newsApiClient.get('/health/data')
    return response.data
  }

  // AI Compare
  async getAICompare(asset1: string, asset2: string) {
    const response = await newsApiClient.get(`/ai/compare/${asset1}/${asset2}`)
    return response.data
  }
}

// Economy Platform API
export class EconomyAPI {
  // India Government Data
  async getPIBLatest() {
    const response = await economyApiClient.get('/india/pib/latest')
    return response.data
  }

  async getPIBSector(sector: string) {
    const response = await economyApiClient.get(`/india/pib/sector/${sector}`)
    return response.data
  }

  async getNDAPData(dataset: string) {
    const response = await economyApiClient.get(`/india/ndap/${dataset}`)
    return response.data
  }

  async getMoSPIIndicator(indicator: string) {
    const response = await economyApiClient.get(`/india/mospi/${indicator}`)
    return response.data
  }

  async getIndiaSectors() {
    const response = await economyApiClient.get('/india/sectors')
    return response.data
  }

  // Global Economy Data
  async getGlobalIMFData(indicator: string, country?: string) {
    const response = await economyApiClient.get('/global/imf', {
      params: { indicator, country }
    })
    return response.data
  }

  async getGlobalWorldBankData(indicator: string, country?: string) {
    const response = await economyApiClient.get('/global/worldbank', {
      params: { indicator, country }
    })
    return response.data
  }

  async getGlobalFREDData(series: string) {
    const response = await economyApiClient.get('/global/fred', {
      params: { series }
    })
    return response.data
  }

  async getEconomySectors() {
    const response = await economyApiClient.get('/economy/sectors')
    return response.data
  }

  // Documents
  async searchDocuments(query: string) {
    const response = await economyApiClient.get('/documents/search', {
      params: { q: query }
    })
    return response.data
  }

  async parseDocument(url: string) {
    const response = await economyApiClient.post('/documents/parse', { url })
    return response.data
  }

  // AI Analysis
  async getEconomyAIAnalysis(query: string) {
    const response = await economyApiClient.get('/ai/analysis', {
      params: { q: query }
    })
    return response.data
  }

  async getEconomyAIForecast(indicator: string) {
    const response = await economyApiClient.get('/ai/forecast', {
      params: { indicator }
    })
    return response.data
  }

  // Site Index
  async getEconomySiteIndex() {
    const response = await economyApiClient.get('/site-index')
    return response.data
  }
}

// Export instances
export const api = new APIClient()
export const FinanceAPI = new FinanceAPI()
export const NewsAPI = new NewsAPI()
export const EconomyAPI = new EconomyAPI()
