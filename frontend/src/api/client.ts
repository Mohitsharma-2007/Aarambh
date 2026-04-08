import axios from "axios";

// Finance API - Port 8000
export const FinanceAPI = {
  async getStockProfile(ticker: string) {
    const response = await axios.get(`http://localhost:8000/api/v1/market/profile/${ticker}`);
    return response.data;
  },
  async getStockResearch(ticker: string) {
    const response = await axios.get(`http://localhost:8000/api/v1/market/research/${ticker}`);
    return response.data;
  },
  async getStockHistory(ticker: string, range?: string) {
    const url = range
      ? `http://localhost:8000/api/v1/market/history/${ticker}?range=${range}`
      : `http://localhost:8000/api/v1/market/history/${ticker}`;
    const response = await axios.get(url);
    return response.data;
  },
  async getSignals() {
    const response = await axios.get("http://localhost:8000/api/v1/market/signals");
    return response.data;
  },
  // Google Finance APIs
  async getStockQuote(ticker: string, exchange?: string) {
    const url = exchange
      ? `http://localhost:8000/api/google-finance/quote/${ticker}/${exchange}`
      : `http://localhost:8000/api/google-finance/quote/${ticker}`;
    const response = await axios.get(url);
    return response.data;
  },

  async getMultiQuote(tickers: string[]) {
    const response = await axios.post(
      "http://localhost:8000/api/google-finance/multi-quote",
      { tickers },
    );
    return response.data;
  },

  async getMarketSection(section: string) {
    const response = await axios.get(
      `http://localhost:8000/api/google-finance/market/${section}`,
    );
    return response.data;
  },

  async getMarketOverview() {
    const response = await axios.get(
      "http://localhost:8000/api/google-finance/overview",
    );
    return response.data;
  },

  async searchStocks(query: string) {
    const response = await axios.get(
      `http://localhost:8000/api/google-finance/search?q=${encodeURIComponent(query)}`,
    );
    return response.data;
  },

  async getStockChart(ticker: string) {
    const response = await axios.get(
      `http://localhost:8000/api/google-finance/chart/${ticker}`,
    );
    return response.data;
  },

  async getStockNews(ticker: string) {
    const response = await axios.get(
      `http://localhost:8000/api/google-finance/news/${ticker}`,
    );
    return response.data;
  },

  // Yahoo Finance APIs
  async getYahooQuote(ticker: string) {
    const response = await axios.get(
      `http://localhost:8000/api/yahoo-finance/quote/${ticker}`,
    );
    return response.data;
  },

  async getYahooChart(ticker: string) {
    const response = await axios.get(
      `http://localhost:8000/api/yahoo-finance/chart/${ticker}`,
    );
    return response.data;
  },

  async getYahooFinancials(ticker: string) {
    const response = await axios.get(
      `http://localhost:8000/api/yahoo-finance/financials/${ticker}`,
    );
    return response.data;
  },

  async getTrendingTickers() {
    const response = await axios.get(
      "http://localhost:8000/api/yahoo-finance/trending",
    );
    return response.data;
  },

  async getMarketMovers() {
    const response = await axios.get(
      "http://localhost:8000/api/yahoo-finance/movers",
    );
    return response.data;
  },

  // Google News for Finance
  async getGoogleNewsHeadlines() {
    const response = await axios.get(
      "http://localhost:8000/api/google-news/headlines",
    );
    return response.data;
  },

  async getGoogleNewsByTopic(topic: string) {
    const response = await axios.get(
      `http://localhost:8000/api/google-news/topic/${topic}`,
    );
    return response.data;
  },

  async getGoogleNewsForTicker(ticker: string) {
    const response = await axios.get(
      `http://localhost:8000/api/google-news/ticker/${ticker}`,
    );
    return response.data;
  },

  // Legacy endpoints for backward compatibility
  async getMarketData() {
    return await this.getMarketOverview();
  },

  async getMarketHeatmap() {
    return await this.getMarketSection("heatmap");
  },

  async getMarketIndices() {
    return await this.getMarketSection("indexes");
  },

  // Indian Stock Market — aggregates Yahoo Finance movers + Google Finance gainers
  async getIndianStockMarket() {
    try {
      const [movers, gainers] = await Promise.all([
        axios
          .get(
            "http://localhost:8000/api/yahoo-finance/movers?type=most_actives",
          )
          .catch(() => ({ data: {} })),
        axios
          .get("http://localhost:8000/api/google-finance/market/gainers")
          .catch(() => ({ data: {} })),
      ]);

      const moversData = movers.data;
      const gainersData = gainers.data;

      // Yahoo Finance movers come as { most_actives: [...], day_gainers: [...], day_losers: [...] }
      const rawStocks: any[] = [
        ...(moversData?.most_actives || moversData?.quotes || []),
        ...(moversData?.day_gainers || []),
        ...(gainersData?.stocks ||
          gainersData?.items ||
          gainersData?.results ||
          []),
      ];

      const seen = new Set<string>();
      const stocks = rawStocks
        .filter((s) => {
          const sym = s?.symbol || s?.ticker || "";
          if (!sym || seen.has(sym)) return false;
          seen.add(sym);
          return true;
        })
        .slice(0, 25)
        .map((s) => ({
          symbol: s.symbol || s.ticker || "",
          name: s.shortName || s.name || s.company || s.symbol || "",
          price: parseFloat(s.regularMarketPrice ?? s.price ?? 0) || 0,
          change: parseFloat(s.regularMarketChange ?? s.change ?? 0) || 0,
          changePercent:
            parseFloat(s.regularMarketChangePercent ?? s.changePercent ?? 0) ||
            0,
          volume:
            parseInt(String(s.regularMarketVolume ?? s.volume ?? 0), 10) || 0,
          marketCap: s.marketCap ?? undefined,
        }));

      return { stocks, source: "Yahoo Finance + Google Finance" };
    } catch {
      return { stocks: [] };
    }
  },
};

// News Platform API - Port 8000
export const NewsAPI = {
  // News Feed
  async getNewsHeadlines(count: number = 50) {
    const response = await axios.get(
      `http://localhost:8000/api/news/headlines?count=${count}`,
    );
    return response.data;
  },

  async searchNews(query: string, count: number = 30) {
    const response = await axios.get(
      `http://localhost:8000/api/news/search?q=${encodeURIComponent(query)}&count=${count}`,
    );
    return response.data;
  },

  async getNewsByCategory(category: string, count: number = 40) {
    const response = await axios.get(
      `http://localhost:8000/api/news/category/${category}?count=${count}`,
    );
    return response.data;
  },

  async getNewsByCountry(country: string, count: number = 40) {
    const response = await axios.get(
      `http://localhost:8000/api/news/country/${country}?count=${count}`,
    );
    return response.data;
  },

  async getNewsBySource(sourceKey: string, count: number = 20) {
    const response = await axios.get(
      `http://localhost:8000/api/news/source/${sourceKey}?count=${count}`,
    );
    return response.data;
  },

  async getFinanceNews(count: number = 50) {
    const response = await axios.get(
      `http://localhost:8000/api/news/finance?count=${count}`,
    );
    return response.data;
  },

  async getTrendingNews() {
    const response = await axios.get("http://localhost:8000/api/news/trending");
    return response.data;
  },

  async getAggregatedNews(sources: string, count: number = 40) {
    const response = await axios.get(
      `http://localhost:8000/api/news/aggregate?sources=${encodeURIComponent(sources)}&count=${count}`,
    );
    return response.data;
  },

  async getNewsSources() {
    const response = await axios.get("http://localhost:8000/api/news/sources");
    return response.data;
  },

  // Live TV
  async getAllLiveTV(category?: string, country?: string) {
    const params = new URLSearchParams();
    if (category) params.append("category", category);
    if (country) params.append("country", country);
    const response = await axios.get(
      `http://localhost:8000/api/live-tv/all?${params.toString()}`,
    );
    return response.data;
  },

  async getLiveTVByCountry(country: string) {
    const response = await axios.get(
      `http://localhost:8000/api/live-tv/country/${country}`,
    );
    return response.data;
  },

  async getLiveTVByCategory(category: string) {
    const response = await axios.get(
      `http://localhost:8000/api/live-tv/category/${category}`,
    );
    return response.data;
  },

  async getFinanceLiveTV() {
    const response = await axios.get(
      "http://localhost:8000/api/live-tv/finance",
    );
    return response.data;
  },

  async searchLiveTV(query: string) {
    const response = await axios.get(
      `http://localhost:8000/api/live-tv/search?q=${encodeURIComponent(query)}`,
    );
    return response.data;
  },

  async getLiveTVStream(channelKey: string) {
    const response = await axios.get(
      `http://localhost:8000/api/live-tv/stream/${channelKey}`,
    );
    return response.data;
  },

  async getLiveTVDirectory() {
    const response = await axios.get(
      "http://localhost:8000/api/live-tv/directory",
    );
    return response.data;
  },

  // Health News
  async getHealthNews(count: number = 50) {
    const response = await axios.get(
      `http://localhost:8000/api/health/news?count=${count}`,
    );
    return response.data;
  },

  async getWHOAlerts() {
    const response = await axios.get(
      "http://localhost:8000/api/health/who-alerts",
    );
    return response.data;
  },

  async getCDCUpdates() {
    const response = await axios.get(
      "http://localhost:8000/api/health/cdc-updates",
    );
    return response.data;
  },

  async filterHealthNews(keyword: string, count: number = 30) {
    const response = await axios.get(
      `http://localhost:8000/api/health/filter?keyword=${encodeURIComponent(keyword)}&count=${count}`,
    );
    return response.data;
  },

  async getHealthNewsBySubcategory(subcat: string) {
    const response = await axios.get(
      `http://localhost:8000/api/health/subcategory/${subcat}`,
    );
    return response.data;
  },

  async getHealthNewsByCountry(country: string) {
    const response = await axios.get(
      `http://localhost:8000/api/health/country/${country}`,
    );
    return response.data;
  },

  async getHealthCategories() {
    const response = await axios.get(
      "http://localhost:8000/api/health/categories",
    );
    return response.data;
  },

  // Geopolitical
  async getConflicts() {
    const response = await axios.get("http://localhost:8000/api/geo/conflicts");
    return response.data;
  },

  async getSanctions() {
    const response = await axios.get("http://localhost:8000/api/geo/sanctions");
    return response.data;
  },

  async getElections() {
    const response = await axios.get("http://localhost:8000/api/geo/elections");
    return response.data;
  },

  async getTensions() {
    const response = await axios.get("http://localhost:8000/api/geo/tensions");
    return response.data;
  },

  async getTreaties() {
    const response = await axios.get("http://localhost:8000/api/geo/treaties");
    return response.data;
  },

  async getCountryRisk(country: string) {
    const response = await axios.get(
      `http://localhost:8000/api/geo/country/${country}`,
    );
    return response.data;
  },

  async searchGDELT(query: string, records: number = 25) {
    const response = await axios.get(
      `http://localhost:8000/api/geo/gdelt?query=${encodeURIComponent(query)}&records=${records}`,
    );
    return response.data;
  },

  async getGDELTVolume(query: string) {
    const response = await axios.get(
      `http://localhost:8000/api/geo/gdelt/timeline?query=${encodeURIComponent(query)}`,
    );
    return response.data;
  },

  async getGeoRiskMap() {
    const response = await axios.get("http://localhost:8000/api/geo/risk-map");
    return response.data;
  },

  async getGeopoliticalAll(count: number = 50) {
    const response = await axios.get(
      `http://localhost:8000/api/geo/all?count=${count}`,
    );
    return response.data;
  },

  // AI Analysis
  async getAISummary(topic: string) {
    const response = await axios.get(
      `http://localhost:8000/api/ai/summarize?topic=${encodeURIComponent(topic)}`,
    );
    return response.data;
  },

  async getAISentiment(topic: string) {
    const response = await axios.get(
      `http://localhost:8000/api/ai/sentiment?topic=${encodeURIComponent(topic)}`,
    );
    return response.data;
  },

  async getAIBriefing() {
    const response = await axios.get("http://localhost:8000/api/ai/briefing");
    return response.data;
  },

  async compareAI(topic1: string, topic2: string) {
    const response = await axios.get(
      `http://localhost:8000/api/ai/compare?topic1=${encodeURIComponent(topic1)}&topic2=${encodeURIComponent(topic2)}`,
    );
    return response.data;
  },

  async postAIAnalysis(text: string) {
    const response = await axios.post("http://localhost:8000/api/ai/analyze", {
      text,
    });
    return response.data;
  },

  async getAITrends() {
    const response = await axios.get("http://localhost:8000/api/ai/trends");
    return response.data;
  },

  async getAISetup() {
    const response = await axios.get("http://localhost:8000/api/ai/setup");
    return response.data;
  },
};

// Economy Platform API - Port 8000
export const EconomyAPI = {
  // India Gov Portals
  async getIndiaNews() {
    const response = await axios.get("http://localhost:8000/api/india/news");
    return response.data;
  },

  async getIndiaIndicator(name: string) {
    const response = await axios.get(
      `http://localhost:8000/api/india/indicator/${name}`,
    );
    return response.data;
  },

  async searchIndiaSchemes(query: string) {
    const response = await axios.get(
      `http://localhost:8000/api/india/schemes/search?q=${encodeURIComponent(query)}`,
    );
    return response.data;
  },

  async getIndiaSchemesCategories() {
    const response = await axios.get(
      "http://localhost:8000/api/india/schemes/categories",
    );
    return response.data;
  },

  async getRBIData(feed: string) {
    const response = await axios.get(
      `http://localhost:8000/api/india/rbi/${feed}`,
    );
    return response.data;
  },

  async getRBIRates() {
    const response = await axios.get(
      "http://localhost:8000/api/india/rbi-rates",
    );
    return response.data;
  },

  async getSEBIData(feed: string) {
    const response = await axios.get(
      `http://localhost:8000/api/india/sebi/${feed}`,
    );
    return response.data;
  },

  async searchNSWS(query: string) {
    const response = await axios.get(
      `http://localhost:8000/api/india/nsws/search?q=${encodeURIComponent(query)}`,
    );
    return response.data;
  },

  async searchDataPortal(query: string) {
    const response = await axios.get(
      `http://localhost:8000/api/india/dataportal/search?q=${encodeURIComponent(query)}`,
    );
    return response.data;
  },

  async getMoSPIData(indicator: string) {
    const response = await axios.get(
      `http://localhost:8000/api/india/mospi/${indicator}`,
    );
    return response.data;
  },

  async getMoSPIReleases() {
    const response = await axios.get(
      "http://localhost:8000/api/mospi/releases",
    );
    return response.data;
  },

  async getMoSPIIndicator(name: string) {
    const response = await axios.get(
      `http://localhost:8000/api/mospi/indicator/${name}`,
    );
    return response.data;
  },

  // 31 Sectors
  async getSectorsList() {
    const response = await axios.get("http://localhost:8000/api/sectors/list");
    return response.data;
  },

  async getSectorData(sectorKey: string) {
    const response = await axios.get(
      `http://localhost:8000/api/sectors/${sectorKey}`,
    );
    return response.data;
  },

  async getSectorNews(sectorKey: string) {
    const response = await axios.get(
      `http://localhost:8000/api/sectors/${sectorKey}/news`,
    );
    return response.data;
  },

  async getSectorInfo(sectorKey: string) {
    const response = await axios.get(
      `http://localhost:8000/api/sectors/${sectorKey}/info`,
    );
    return response.data;
  },

  // Global Economy
  async getWorldBankData(country: string, indicator?: string) {
    const url = indicator
      ? `http://localhost:8000/api/global/world-bank?country=${country}&indicator=${indicator}`
      : `http://localhost:8000/api/global/world-bank/profile/${country}`;
    const response = await axios.get(url);
    return response.data;
  },

  async getWorldBankIndicators() {
    const response = await axios.get(
      "http://localhost:8000/api/global/world-bank/indicators",
    );
    return response.data;
  },

  async getIMFData(indicator?: string, country?: string) {
    const response = await axios.get("http://localhost:8000/api/global/imf", {
      params: { indicator, country },
    });
    return response.data;
  },

  async getFREDData(indicator?: string) {
    const response = await axios.get("http://localhost:8000/api/global/fred", {
      params: { indicator },
    });
    return response.data;
  },

  async getFREDIndicators() {
    const response = await axios.get(
      "http://localhost:8000/api/global/fred/indicators",
    );
    return response.data;
  },

  async getOECDData() {
    const response = await axios.get("http://localhost:8000/api/global/oecd");
    return response.data;
  },

  async getEarningsCalendar() {
    const response = await axios.get(
      "http://localhost:8000/api/global/earnings",
    );
    return response.data;
  },

  async getIPOCalendar() {
    const response = await axios.get("http://localhost:8000/api/global/ipo");
    return response.data;
  },

  async getDividendCalendar() {
    const response = await axios.get(
      "http://localhost:8000/api/global/dividends",
    );
    return response.data;
  },

  async getUNData() {
    const response = await axios.get("http://localhost:8000/api/global/un");
    return response.data;
  },

  async getEconomicCalendar() {
    const response = await axios.get(
      "http://localhost:8000/api/global/calendar",
    );
    return response.data;
  },

  async getIndiaVsWorld(indicator: string) {
    const response = await axios.get(
      `http://localhost:8000/api/global/india-vs-world/${indicator}`,
    );
    return response.data;
  },

  // Document Parser
  async parseDocument(url: string) {
    const response = await axios.get(
      `http://localhost:8000/api/docs/parse?url=${encodeURIComponent(url)}`,
    );
    return response.data;
  },

  async uploadDocument(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    const response = await axios.post(
      "http://localhost:8000/api/docs/upload",
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      },
    );
    return response.data;
  },

  async getPIBDoc(url: string) {
    const response = await axios.get(
      `http://localhost:8000/api/docs/pib-doc?url=${encodeURIComponent(url)}`,
    );
    return response.data;
  },

  async getRBICircular(url: string) {
    const response = await axios.get(
      `http://localhost:8000/api/docs/rbi-circular?url=${encodeURIComponent(url)}`,
    );
    return response.data;
  },

  // AI Analysis
  async getAISetup() {
    const response = await axios.get("http://localhost:8000/api/ai/setup");
    return response.data;
  },

  async getAISummary(topic: string) {
    const response = await axios.get(
      `http://localhost:8000/api/ai/summarize?topic=${encodeURIComponent(topic)}`,
    );
    return response.data;
  },

  async getAIBriefing() {
    const response = await axios.get("http://localhost:8000/api/ai/briefing");
    return response.data;
  },

  async postAICompare(data: { indicator1: string; indicator2: string }) {
    const response = await axios.post(
      "http://localhost:8000/api/ai/compare",
      data,
    );
    return response.data;
  },

  async postAIAnalyze(text: string) {
    const response = await axios.post("http://localhost:8000/api/ai/analyze", {
      text,
    });
    return response.data;
  },

  async postAIExtractInsights(data: any) {
    const response = await axios.post(
      "http://localhost:8000/api/ai/extract-insights",
      data,
    );
    return response.data;
  },

  async postAIAnalyzeDocument(document: any) {
    const response = await axios.post(
      "http://localhost:8000/api/ai/analyze-document",
      document,
    );
    return response.data;
  },

  // Legacy endpoints for backward compatibility
  async getIndiaIndicatorLegacy(indicator: string) {
    return await this.getIndiaIndicator(indicator);
  },

  async getIndiaSectors() {
    return await this.getSectorsList();
  },

  // PIB — latest press releases  →  /api/pib/latest
  async getPIBLatest(count: number = 10) {
    const response = await axios.get(
      `http://localhost:8000/api/pib/latest?count=${count}`,
    );
    return response.data;
  },

  // NDAP / NITI Aayog datasets  →  /api/ndap/datasets
  async getNDAPData(query: string = "", sector: string = "") {
    const params = new URLSearchParams();
    if (query) params.append("q", query);
    if (sector) params.append("sector", sector);
    const response = await axios.get(
      `http://localhost:8000/api/ndap/datasets?${params.toString()}`,
    );
    return response.data;
  },

  // RBI key rates shorthand
  async getRBIKeyRates() {
    const response = await axios.get(
      "http://localhost:8000/api/india/rbi-rates",
    );
    return response.data;
  },

  // PIB search
  async searchPIB(query: string, count: number = 20) {
    const response = await axios.get(
      `http://localhost:8000/api/pib/search?q=${encodeURIComponent(query)}&count=${count}`,
    );
    return response.data;
  },
};

// MiroFish Ontology API - Port 8001
export const MiroFishAPI = {
  // Ontology Generation
  async generateOntology() {
    const response = await axios.post(
      "http://localhost:8001/api/graph/ontology/generate",
    );
    return response.data;
  },

  async buildGraph() {
    const response = await axios.post("http://localhost:8001/api/graph/build");
    return response.data;
  },

  async getTaskStatus(taskId: string) {
    const response = await axios.get(
      `http://localhost:8001/api/graph/task/${taskId}`,
    );
    return response.data;
  },

  async getProject(projectId: string) {
    const response = await axios.get(
      `http://localhost:8001/api/graph/project/${projectId}`,
    );
    return response.data;
  },

  async getGraphData(graphId: string) {
    const response = await axios.get(
      `http://localhost:5001/api/graph/data/${graphId}`,
    );
    return response.data;
  },

  // Simulation
  async createSimulation(params: any) {
    const response = await axios.post(
      "http://localhost:5001/api/simulation/create",
      params,
    );
    return response.data;
  },

  async prepareSimulation(params: any) {
    const response = await axios.post(
      "http://localhost:5001/api/simulation/prepare",
      params,
    );
    return response.data;
  },

  async getPrepareStatus() {
    const response = await axios.get(
      "http://localhost:5001/api/simulation/prepare/status",
    );
    return response.data;
  },

  async getSimulation(simulationId: string) {
    const response = await axios.get(
      `http://localhost:5001/api/simulation/${simulationId}`,
    );
    return response.data;
  },

  async getSimulationProfiles(simulationId: string) {
    const response = await axios.get(
      `http://localhost:5001/api/simulation/${simulationId}/profiles`,
    );
    return response.data;
  },

  async getSimulationConfig(simulationId: string) {
    const response = await axios.get(
      `http://localhost:5001/api/simulation/${simulationId}/config`,
    );
    return response.data;
  },

  async startSimulation(simulationId: string) {
    const response = await axios.post(
      `http://localhost:5001/api/simulation/start`,
      { simulationId },
    );
    return response.data;
  },

  async stopSimulation(simulationId: string) {
    const response = await axios.post(
      `http://localhost:5001/api/simulation/stop`,
      { simulationId },
    );
    return response.data;
  },

  async getRunStatus(simulationId: string) {
    const response = await axios.get(
      `http://localhost:5001/api/simulation/${simulationId}/run-status`,
    );
    return response.data;
  },

  async getSimulationActions(simulationId: string) {
    const response = await axios.get(
      `http://localhost:5001/api/simulation/${simulationId}/actions`,
    );
    return response.data;
  },

  async listSimulations() {
    const response = await axios.get(
      "http://localhost:5001/api/simulation/list",
    );
    return response.data;
  },

  // Reports
  async generateReport(params: any) {
    const response = await axios.post(
      "http://localhost:5001/api/report/generate",
      params,
    );
    return response.data;
  },

  async getGenerateStatus() {
    const response = await axios.get(
      "http://localhost:5001/api/report/generate/status",
    );
    return response.data;
  },

  async getReport(reportId: string) {
    const response = await axios.get(
      `http://localhost:5001/api/report/${reportId}`,
    );
    return response.data;
  },

  async chatWithReport(reportId: string, message: string) {
    const response = await axios.post(
      `http://localhost:5001/api/report/chat`,
      { message },
      {
        params: { reportId },
      },
    );
    return response.data;
  },

  async getAgentLog(reportId: string) {
    const response = await axios.get(
      `http://localhost:5001/api/report/${reportId}/agent-log`,
    );
    return response.data;
  },

  async getConsoleLog(reportId: string) {
    const response = await axios.get(
      `http://localhost:5001/api/report/${reportId}/console-log`,
    );
    return response.data;
  },

  // AI Providers
  async getAIProviders() {
    try {
      const response = await axios.get("http://localhost:8000/api/ai/setup");
      return response.data;
    } catch (error) {
      // Fallback when main backend is not running
      return {
        providers: [
          {
            id: "openai",
            name: "OpenAI",
            models: [
              { id: "gpt-4", name: "GPT-4" },
              { id: "gpt-3.5-turbo", name: "GPT-3.5 Turbo" },
            ],
          },
          {
            id: "anthropic",
            name: "Anthropic",
            models: [
              { id: "claude-3", name: "Claude 3" },
              { id: "claude-2", name: "Claude 2" },
            ],
          },
        ],
        default: "openai",
      };
    }
  },
};

export const AIQueryAPI = {
  // AI Chat & Conversations
  async getConversations() {
    const response = await axios.get("http://localhost:8000/api/v1/ai/conversations");
    return response.data;
  },

  async sendChatMessage(data: {
    message: string;
    conversation_id?: string;
    provider?: string;
    model?: string;
    tools?: string[]
  }) {
    const response = await axios.post("http://localhost:8000/api/v1/ai/chat", {
      message: data.message,
      conversation_id: data.conversation_id,
      tools: data.tools
    });
    return response.data;
  },

  async getConversationMessages(conversationId: string) {
    const response = await axios.get(`http://localhost:8000/api/v1/ai/conversations/${conversationId}/messages`);
    return response.data;
  },
};

// Consolidated API export for backward compatibility
export const api = {
  ...FinanceAPI,
  ...NewsAPI,
  ...EconomyAPI,
  ...MiroFishAPI,
  ...AIQueryAPI,
};
