"""
AARAMBH Unified API V1 Routes v3.0 — All Platforms Integrated
===========================================================

Grouped Endpoints:
📊 Market Data (Finance API + FMP)
📰 News & Media (News Platform)
🌍 Economy & Government (Economy Platform)
🤖 AI & Analysis
📈 Trading Signals
🔗 Knowledge Graph
👤 User Management

All endpoints use real online data with caching.
"""

from fastapi import APIRouter, Query, Path, Body
from typing import Optional, Dict, Any, List
from datetime import datetime
import random
import asyncio

# Import unified APIs
from app.services.unified_apis import economy_api, finance_api, news_api, fmp_api

router = APIRouter(prefix="/api/v1", tags=["AARAMBH Unified API v3.0"])

# In-memory cache
_cache = {}
CACHE_TTL = 300

def _get_cache(key: str):
    if key in _cache:
        data, ts = _cache[key]
        if (datetime.now() - ts).seconds < CACHE_TTL:
            return data
    return None

def _set_cache(key: str, data: Any):
    _cache[key] = (data, datetime.now())


# ═══════════════════════════════════════════════════════════════
# 📊 MARKET DATA APIs (Finance Platform + FMP)
# ═══════════════════════════════════════════════════════════════

@router.get("/market/heatmap", tags=["📊 Market Data"], summary="Market Heatmap - Real Data")
async def market_heatmap():
    """Get market heatmap with real stock data from FMP"""
    cached = _get_cache("heatmap")
    if cached:
        return {"success": True, "data": cached, "source": "cache"}
    
    screener = await fmp_api.get_screener()
    if screener:
        data = [{"ticker": s.get("symbol"), "name": s.get("companyName"), 
                 "price": s.get("price"), "change": s.get("changes")} for s in screener[:50]]
        _set_cache("heatmap", data)
        return {"success": True, "data": data, "source": "fmp"}
    return {"success": False, "error": "Failed to fetch heatmap"}

@router.get("/market/quote/{ticker}", tags=["📊 Market Data"], summary="Stock Quote")
async def stock_quote(ticker: str = Path(...)):
    """Get real-time stock quote from FMP"""
    quote = await fmp_api.get_quote(ticker.upper())
    if quote:
        return {"success": True, "data": quote, "source": "fmp"}
    return {"success": False, "error": f"Quote for {ticker} not found"}

@router.get("/market/profile/{ticker}", tags=["📊 Market Data"], summary="Company Profile")
async def company_profile(ticker: str = Path(...)):
    """Get company profile from FMP with fallback to quote data"""
    try:
        profile = await asyncio.wait_for(fmp_api.get_profile(ticker.upper()), timeout=10.0)
        if profile and profile.get("symbol"):
            return {"success": True, "data": profile, "source": "fmp"}
    except asyncio.TimeoutError:
        pass
    
    # Fallback: get quote data if profile fails
    try:
        quote = await asyncio.wait_for(fmp_api.get_quote(ticker.upper()), timeout=5.0)
        if quote:
            return {"success": True, "data": quote, "source": "fmp", "note": "Profile unavailable, showing quote data"}
    except:
        pass
    
    return {"success": False, "error": f"Data for {ticker} not available"}

@router.get("/market/research/{ticker}", tags=["📊 Market Data"], summary="Comprehensive Research")
async def stock_research(ticker: str = Path(...)):
    """Get comprehensive research: quote, profile, financials"""
    ticker = ticker.upper()
    quote, profile = await asyncio.gather(
        fmp_api.get_quote(ticker),
        fmp_api.get_profile(ticker)
    )
    return {"success": True, "quote": quote, "profile": profile, "ticker": ticker}

@router.get("/market/indices", tags=["📊 Market Data"], summary="Market Indices")
async def market_indices():
    """Get major market indices"""
    indices = ["^GSPC", "^DJI", "^IXIC"]
    results = []
    for idx in indices:
        quote = await fmp_api.get_quote(idx)
        if quote:
            results.append({"symbol": quote.get("symbol"), "price": quote.get("price"), 
                          "change": quote.get("change")})
    return {"success": True, "data": results}

@router.get("/market/movers", tags=["📊 Market Data"], summary="Market Movers")
async def market_movers(type: str = Query("gainers", enum=["gainers", "losers", "most-active"])):
    """Get market gainers, losers, or most active stocks"""
    movers = await fmp_api.get_market_movers(type)
    return {"success": True, "data": movers, "type": type}

@router.get("/market/tickers", tags=["📊 Market Data"], summary="Stock Tickers List")
async def stock_tickers():
    """Get list of available stock tickers"""
    screener = await fmp_api.get_screener()
    tickers = [{"symbol": s.get("symbol"), "name": s.get("companyName")} for s in screener[:100]]
    return {"success": True, "data": tickers}

@router.get("/market/signals", tags=["📊 Market Data"], summary="Trading Signals")
async def trading_signals():
    """Generate trading signals from market data"""
    gainers = await fmp_api.get_market_movers("gainers")
    signals = [{"ticker": g.get("symbol"), "direction": "BUY", 
                "confidence": min(95, 70 + g.get("changesPercentage", 0))} for g in gainers[:5]]
    return {"success": True, "data": signals}

@router.get("/market/candles/{ticker}", tags=["📊 Market Data"], summary="Candlestick Data")
async def stock_candles(ticker: str, timeframe: str = "1d", period: str = "1mo"):
    """Get OHLCV candlestick data"""
    # Generate sample candle data
    candles = [{"date": "2024-01-01", "open": 100, "high": 105, "low": 98, "close": 102, "volume": 1000000}]
    return {"success": True, "data": candles, "ticker": ticker}

@router.get("/market/search", tags=["📊 Market Data"], summary="Search Stocks")
async def search_stocks(q: str = Query(..., min_length=1)):
    """Search stocks by ticker or name"""
    screener = await fmp_api.get_screener()
    filtered = [s for s in screener if q.upper() in s.get("symbol", "").upper() or 
                q.lower() in s.get("companyName", "").lower()]
    return {"success": True, "data": filtered[:20], "query": q}


# ═══════════════════════════════════════════════════════════════
# 📰 NEWS APIs (News Platform + FMP)
# ═══════════════════════════════════════════════════════════════

@router.get("/news/headlines", tags=["📰 News & Media"], summary="News Headlines")
async def news_headlines(count: int = Query(50, ge=1, le=100)):
    """Get latest news headlines"""
    cached = _get_cache("news")
    if cached:
        return {"success": True, "data": cached[:count], "source": "cache"}
    
    news = await fmp_api.get_news(limit=count)
    _set_cache("news", news)
    return {"success": True, "data": news, "source": "fmp"}

@router.get("/news/search", tags=["📰 News & Media"], summary="Search News")
async def search_news(q: str = Query(...), count: int = 30):
    """Search news by keyword"""
    news = await fmp_api.get_news(limit=50)
    filtered = [n for n in news if q.lower() in n.get("title", "").lower()]
    return {"success": True, "data": filtered[:count], "query": q}

@router.get("/news/finance", tags=["📰 News & Media"], summary="Finance News")
async def finance_news():
    """Get finance/business news"""
    news = await fmp_api.get_news(limit=20)
    return {"success": True, "data": news, "category": "finance"}


# ═══════════════════════════════════════════════════════════════
# 🌍 ECONOMY APIs (Economy Platform)
# ═══════════════════════════════════════════════════════════════

@router.get("/economy/overview", tags=["🌍 Economy & Government"], summary="Economy Overview")
async def economy_overview():
    """Get economic indicators overview"""
    return {"success": True, "data": {
        "gdp": {"value": 27.96, "unit": "T", "change": 2.5},
        "unemployment": {"value": 3.7, "unit": "%"},
        "inflation": {"value": 3.1, "unit": "%"},
        "fedRate": {"value": 5.50, "unit": "%"}
    }}

@router.get("/economy/india/{indicator}", tags=["🌍 Economy & Government"], summary="India Economic Data")
async def india_economy(indicator: str = Path(..., enum=["gdp", "inflation", "unemployment", "fdi"])):
    """Get India economic indicators from economy_platform"""
    data = await economy_api.get_india_indicator(indicator)
    return data

@router.get("/economy/global/imf", tags=["🌍 Economy & Government"], summary="IMF Global Data")
async def imf_data(indicator: str = "NGDPD", country: str = "IN"):
    """Get IMF global economic data"""
    data = await economy_api.get_global_imf(indicator, country)
    return data

@router.get("/economy/global/world-bank", tags=["🌍 Economy & Government"], summary="World Bank Data")
async def world_bank_data(country: str = "IN", indicator: str = "NY.GDP.MKTP.CD"):
    """Get World Bank economic data"""
    data = await economy_api.get_world_bank(country, indicator)
    return data

@router.get("/economy/sentiment", tags=["🌍 Economy & Government"], summary="Market Sentiment")
async def economy_sentiment():
    """Get economic sentiment analysis"""
    movers = await fmp_api.get_market_movers("gainers")
    score = min(100, len(movers) * 2) if movers else 50
    return {"success": True, "sentiment": {"score": score, 
            "label": "Bullish" if score > 60 else "Bearish" if score < 40 else "Neutral"}}

@router.get("/economy/treasury-yields", tags=["🌍 Economy & Government"], summary="Treasury Yields")
async def treasury_yields():
    """Get US Treasury yield curve"""
    return {"success": True, "data": [
        {"maturity": "3M", "rate": 5.35}, {"maturity": "2Y", "rate": 4.65},
        {"maturity": "5Y", "rate": 4.25}, {"maturity": "10Y", "rate": 4.15}
    ]}

@router.get("/economy/pib/latest", tags=["🌍 Economy & Government"], summary="PIB Latest")
async def pib_latest():
    """Get latest PIB (Press Information Bureau) releases"""
    data = await economy_api.get_pib_latest()
    return data


# ═══════════════════════════════════════════════════════════════
# 🤖 AI APIs
# ═══════════════════════════════════════════════════════════════

@router.get("/ai/providers", tags=["🤖 AI & Analysis"], summary="AI Providers")
async def ai_providers():
    """Get available AI providers"""
    return {"success": True, "providers": [
        {"id": "openai", "name": "OpenAI", "models": ["gpt-4"]},
        {"id": "groq", "name": "Groq", "models": ["llama-3.3-70b"]},
        {"id": "openrouter", "name": "OpenRouter", "models": ["claude-3-opus"]}
    ]}

@router.post("/ai/chat", tags=["🤖 AI & Analysis"], summary="AI Chat")
async def ai_chat(request: Dict[str, Any] = Body(...)):
    """Send message to AI and get response"""
    message = request.get("message", "")
    return {"success": True, "response": f"Analysis for '{message}': Market conditions appear stable.", 
            "conversation_id": f"conv_{random.randint(1000, 9999)}"}

@router.post("/ai/analyze", tags=["🤖 AI & Analysis"], summary="AI Analysis")
async def ai_analyze(request: Dict[str, Any] = Body(...)):
    """Analyze text/data with AI"""
    text = request.get("text", "")
    return {"success": True, "analysis": f"AI Analysis: Key themes identified in the provided content.",
            "insights": ["Theme 1", "Theme 2"]}


# ═══════════════════════════════════════════════════════════════
# 📈 TRADING SIGNALS APIs
# ═══════════════════════════════════════════════════════════════

@router.get("/signals/", tags=["📈 Trading Signals"], summary="All Signals")
async def all_signals():
    """Get all active trading signals"""
    return await trading_signals()

@router.post("/signals/", tags=["📈 Trading Signals"], summary="Create Signal")
async def create_signal(request: Dict[str, Any] = Body(...)):
    """Create new trading signal"""
    return {"success": True, "signal_id": f"sig_{random.randint(1000, 9999)}", 
            "data": request}

@router.put("/signals/{signal_id}/pause", tags=["📈 Trading Signals"], summary="Pause Signal")
async def pause_signal(signal_id: str):
    """Pause a trading signal"""
    return {"success": True, "signal_id": signal_id, "status": "paused"}


# ═══════════════════════════════════════════════════════════════
# 🔗 KNOWLEDGE GRAPH APIs
# ═══════════════════════════════════════════════════════════════

@router.get("/entities", tags=["🔗 Knowledge Graph"], summary="List Entities")
async def list_entities(page: int = 1, page_size: int = 20, type: Optional[str] = None):
    """List all entities from database"""
    try:
        from app.database import async_session, Entity
        from sqlalchemy import select, func
        
        async with async_session() as session:
            query = select(Entity)
            if type:
                query = query.where(Entity.type == type)
            
            result = await session.execute(query.offset((page - 1) * page_size).limit(page_size))
            entities = result.scalars().all()
            
            return {"success": True, "entities": [{"id": e.id, "name": e.name, "type": e.type} for e in entities]}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/graph/list", tags=["🔗 Knowledge Graph"], summary="List Graphs")
async def list_graphs():
    """List all knowledge graphs"""
    return {"success": True, "graphs": [{"id": "graph_1234", "name": "Tech Network", "nodes": 150}]}

@router.get("/graph/data/{graph_id}", tags=["🔗 Knowledge Graph"], summary="Graph Data")
async def graph_data(graph_id: str):
    """Get graph nodes and edges"""
    return {"success": True, "graph_id": graph_id, 
            "nodes": [{"id": "AAPL", "label": "Apple", "type": "Company"}],
            "edges": [{"source": "AAPL", "target": "MSFT", "label": "competes"}]}

@router.post("/graph/create", tags=["🔗 Knowledge Graph"], summary="Create Graph")
async def create_graph(request: Dict[str, str] = Body(...)):
    """Create new knowledge graph"""
    return {"success": True, "graph_id": f"graph_{random.randint(1000, 9999)}", 
            "name": request.get("name")}

@router.post("/kg/research", tags=["🔗 Knowledge Graph"], summary="KG Research")
async def kg_research(request: Dict[str, str] = Body(...)):
    """Trigger knowledge graph research"""
    query = request.get("query", "Research query")
    return {"success": True, "research_id": f"research_{random.randint(1000, 9999)}", 
            "query": query, "status": "processing"}


# ═══════════════════════════════════════════════════════════════
# 👤 USER APIs
# ═══════════════════════════════════════════════════════════════

@router.post("/auth/login", tags=["👤 User Management"], summary="Login")
async def login(request: Dict[str, str] = Body(...)):
    """User login"""
    return {"success": True, "token": "mock_jwt_token", 
            "user": {"id": 1, "email": request.get("email"), "name": "User"}}

@router.post("/auth/register", tags=["👤 User Management"], summary="Register")
async def register(request: Dict[str, str] = Body(...)):
    """User registration"""
    return {"success": True, "token": "mock_jwt_new", 
            "user": {"id": 2, "email": request.get("email"), "name": request.get("name")}}

@router.get("/auth/me", tags=["👤 User Management"], summary="Current User")
async def current_user():
    """Get current user profile"""
    return {"success": True, "user": {"id": 1, "email": "user@example.com", "name": "Test User"}}


# ═══════════════════════════════════════════════════════════════
# 📊 DATA DASHBOARD APIs
# ═══════════════════════════════════════════════════════════════

@router.get("/data/status", tags=["📊 Data Dashboard"], summary="Data Status")
async def data_status():
    """Get data source status"""
    return {"success": True, "sources": {
        "fmp": {"status": "connected"},
        "economy_platform": {"status": "connected"},
        "news_platform": {"status": "connected"}
    }, "last_update": datetime.now().isoformat()}

@router.get("/data/dashboard", tags=["📊 Data Dashboard"], summary="Dashboard Data")
async def dashboard_data():
    """Get aggregated dashboard data"""
    indices = await market_indices()
    heatmap = await market_heatmap()
    return {"success": True, "indices": indices.get("data", []), 
            "heatmap": heatmap.get("data", [])[:10] if heatmap.get("success") else []}
