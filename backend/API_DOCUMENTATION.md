# AARAMBH API Documentation

## Testing APIs

### Swagger UI (Interactive)
Start the backend server and visit:
```
http://localhost:8000/docs
```

### ReDoc (Documentation)
```
http://localhost:8000/redoc
```

---

## API Endpoints Reference

### 🔐 Authentication

| Method | Endpoint | Description | Frontend Usage |
|--------|----------|-------------|----------------|
| POST | `/api/v1/auth/login` | User login | `frontend/src/api/client.ts:70` - `api.login()` |
| POST | `/api/v1/auth/register` | User registration | `frontend/src/api/client.ts:75` - `api.register()` |
| GET | `/api/v1/auth/me` | Get current user | `frontend/src/api/client.ts:80` - `api.getMe()` |

**Example - Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

---

### 📊 Market Data

| Method | Endpoint | Description | Frontend Usage |
|--------|----------|-------------|----------------|
| GET | `/api/v1/market/heatmap` | Market heatmap data | `MarketTicker.tsx:44`, `F8_Charts.tsx:62` |
| GET | `/api/v1/market/quote/{ticker}` | Stock quote | `F4_EquityResearch.tsx:121`, `F8_Charts.tsx:88` |
| GET | `/api/v1/market/indices` | Market indices | `Dashboard.tsx:217` |
| GET | `/api/v1/market/candles/{ticker}` | OHLCV candle data | `F8_Charts.tsx:87` |
| GET | `/api/v1/market/research/{ticker}` | Comprehensive research | `F4_EquityResearch.tsx:152` |
| GET | `/api/v1/market/search?q={query}` | Search stocks | `F4_EquityResearch.tsx:118` |
| GET | `/api/v1/market/movers?type={type}` | Market movers | `client.ts:442` |

**Example - Get Stock Quote:**
```bash
curl http://localhost:8000/api/v1/market/quote/AAPL
```

**Response:**
```json
{
  "success": true,
  "data": {
    "ticker": "AAPL",
    "name": "Apple Inc",
    "price": 178.50,
    "change": 2.15,
    "changePercent": 1.22,
    "volume": 50000000,
    "marketCap": 2800000000000,
    "pe": 29.43,
    "eps": 6.07,
    "beta": 1.28
  }
}
```

**Example - Get Stock Research:**
```bash
curl http://localhost:8000/api/v1/market/research/MSFT
```

**Example - Search Stocks:**
```bash
curl "http://localhost:8000/api/v1/market/search?q=apple"
```

---

### 📰 News

| Method | Endpoint | Description | Frontend Usage |
|--------|----------|-------------|----------------|
| GET | `/api/v1/news/headlines?count={n}` | News headlines | `Dashboard.tsx:220`, `NewsFeed.tsx` |
| GET | `/api/v1/news/search?q={query}` | Search news | `client.ts:381` |
| GET | `/api/v1/news/trending` | Trending topics | `client.ts:391` |
| GET | `/api/v1/news/category/{category}` | News by category | `client.ts:386` |

**Example:**
```bash
curl "http://localhost:8000/api/v1/news/headlines?count=10"
```

---

### 📈 Signals

| Method | Endpoint | Description | Frontend Usage |
|--------|----------|-------------|----------------|
| GET | `/api/v1/signals/` | Get all signals | `Dashboard.tsx:219`, `Signals.tsx` |
| POST | `/api/v1/signals/` | Create signal | `client.ts:268` |
| PUT | `/api/v1/signals/{id}/pause` | Pause signal | `client.ts:273` |
| PUT | `/api/v1/signals/{id}/resume` | Resume signal | `client.ts:278` |

**Example:**
```bash
curl http://localhost:8000/api/v1/signals/
```

---

### 🤖 AI

| Method | Endpoint | Description | Frontend Usage |
|--------|----------|-------------|----------------|
| GET | `/api/v1/ai/providers` | Get AI providers | `ai.store.ts` |
| POST | `/api/v1/ai/chat` | Send chat message | `F4_EquityResearch.tsx:217`, `AIQuery.tsx` |
| GET | `/api/v1/ai/conversations` | List conversations | `client.ts:165` |
| GET | `/api/v1/ai/tools` | Get AI tools | `client.ts:175` |

**Example - Chat:**
```bash
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze AAPL stock", "provider": "openai"}'
```

---

### 💰 Investors

| Method | Endpoint | Description | Frontend Usage |
|--------|----------|-------------|----------------|
| GET | `/api/v1/investors/funds` | Institutional funds | `F6_Investors.tsx` |
| GET | `/api/v1/investors/funds/{cik}/holdings` | Fund holdings | `client.ts:289` |
| GET | `/api/v1/investors/congress` | Congress trades | `F6_Investors.tsx` |
| GET | `/api/v1/investors/portfolios` | Portfolios | `client.ts:294` |

**Example:**
```bash
curl http://localhost:8000/api/v1/investors/funds
curl http://localhost:8000/api/v1/investors/congress
```

---

### 🌍 Economy

| Method | Endpoint | Description | Frontend Usage |
|--------|----------|-------------|----------------|
| GET | `/api/v1/economy/overview` | Economy overview | `F10_Economy.tsx` |
| GET | `/api/v1/economy/treasury-yields` | Treasury yields | `F10_Economy.tsx` |
| GET | `/api/v1/economy/calendar` | Economic calendar | `client.ts:96` |
| GET | `/api/v1/economy/fred?series={s}` | FRED data | `client.ts:420` |

**Example:**
```bash
curl http://localhost:8000/api/v1/economy/overview
curl http://localhost:8000/api/v1/economy/treasury-yields
```

---

### 📊 Data Bridge

| Method | Endpoint | Description | Frontend Usage |
|--------|----------|-------------|----------------|
| GET | `/api/v1/data/status` | Data source status | `Ingestion.tsx` |
| GET | `/api/v1/data/dashboard` | Dashboard data | `Dashboard.tsx:216` |
| GET | `/api/v1/data/economy-dashboard` | Economy dashboard | `client.ts:359` |

**Example:**
```bash
curl http://localhost:8000/api/v1/data/dashboard
```

---

### 🔗 Graph/Ontology

| Method | Endpoint | Description | Frontend Usage |
|--------|----------|-------------|----------------|
| POST | `/api/graph/create` | Create graph | `client.ts:186` |
| GET | `/api/graph/list` | List graphs | `client.ts:191` |
| GET | `/api/graph/data/{id}` | Get graph data | `client.ts:196` |
| POST | `/api/graph/build` | Build graph | `client.ts:208` |
| GET | `/api/graph/project/{id}/state` | Project state | `client.ts:213` |

**Example:**
```bash
curl -X POST http://localhost:8000/api/graph/create \
  -H "Content-Type: application/json" \
  -d '{"name": "Tech Network", "description": "Tech companies graph"}'

curl http://localhost:8000/api/graph/list
curl http://localhost:8000/api/graph/data/graph_1234
```

---

### 🧪 Simulation

| Method | Endpoint | Description | Frontend Usage |
|--------|----------|-------------|----------------|
| POST | `/api/simulation/create` | Create simulation | `client.ts:224` |
| GET | `/api/simulation/list` | List simulations | `client.ts:229` |
| GET | `/api/simulation/{id}` | Get simulation | `client.ts:234` |

**Example:**
```bash
curl -X POST http://localhost:8000/api/simulation/create \
  -H "Content-Type: application/json" \
  -d '{"name": "Market Crash Scenario"}'

curl http://localhost:8000/api/simulation/list
```

---

### 📄 Reports

| Method | Endpoint | Description | Frontend Usage |
|--------|----------|-------------|----------------|
| POST | `/api/report/generate` | Generate report | `client.ts:240` |
| GET | `/api/report/{id}` | Get report | `client.ts:245` |

**Example:**
```bash
curl -X POST http://localhost:8000/api/report/generate \
  -H "Content-Type: application/json" \
  -d '{"simulation_id": "sim_1234"}'

curl http://localhost:8000/api/report/report_5678
```

---

## Frontend Files & API Usage Summary

| Frontend File | API Methods Used |
|---------------|------------------|
| `Dashboard.tsx` | `getMarketDashboard()`, `getMarketIndices()`, `getSignals()`, `getNewsHeadlines()` |
| `F4_EquityResearch.tsx` | `getStockResearch()`, `getStockQuote()`, `searchStocks()`, `sendChatMessage()` |
| `F8_Charts.tsx` | `getMarketHeatmap()`, `getStockCandles()`, `getStockQuote()` |
| `MarketTicker.tsx` | `getMarketHeatmap()` |
| `NewsFeed.tsx` | `getNewsHeadlines()`, `searchNews()`, `getEvents()` |
| `F6_Investors.tsx` | `getFunds()`, `getFundHoldings()`, `getCongressTrades()` |
| `F10_Economy.tsx` | `getEconomyOverview()`, `getTreasuryYields()`, `getFREDData()` |
| `Signals.tsx` | `getSignals()`, `createSignal()`, `pauseSignal()` |
| `AIQuery.tsx` | `sendChatMessage()`, `getConversations()` |
| `Ingestion.tsx` | `getDataStatus()`, `triggerIngestionBackground()` |

---

## Quick Start Testing

### 1. Start the Backend
```bash
cd d:\AARAMBH\backend
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Open Swagger UI
Navigate to: http://localhost:8000/docs

### 3. Test Endpoints in Swagger
1. Click on any endpoint to expand
2. Click "Try it out"
3. Enter parameters
4. Click "Execute"
5. View response

### 4. Test with cURL

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Get Market Heatmap:**
```bash
curl http://localhost:8000/api/v1/market/heatmap
```

**Get Stock Quote:**
```bash
curl http://localhost:8000/api/v1/market/quote/AAPL
curl http://localhost:8000/api/v1/market/quote/MSFT
curl http://localhost:8000/api/v1/market/quote/GOOGL
```

**Get Stock Research:**
```bash
curl http://localhost:8000/api/v1/market/research/NVDA
```

**Send AI Chat:**
```bash
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the outlook for tech stocks?"}'
```

---

## Response Format

All endpoints return a consistent format:

**Success:**
```json
{
  "success": true,
  "data": { ... }
}
```

**Error:**
```json
{
  "success": false,
  "error": "Error message"
}
```

---

## Notes

- All endpoints are documented with OpenAPI/Swagger
- Mock data is returned for demonstration
- Replace mock implementations with real data services in production
- Authentication endpoints require real user database
- Market data endpoints should connect to real data providers (Yahoo Finance, Alpha Vantage, etc.)
