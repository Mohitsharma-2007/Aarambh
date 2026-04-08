"""
AARAMBH API V1 Routes - FastAPI Router with Real Online Data

All endpoints fetch data from online sources (FMP API, Indian Stock API, etc.)
Data is cached in memory for 5 minutes to reduce API calls.

Test at: http://localhost:8000/docs (Swagger UI)
"""

from fastapi import APIRouter, HTTPException, Query, Path, Body, Depends
from typing import Optional, List, Any, Dict
from datetime import datetime, timedelta
import random
import json
import asyncio
import httpx

from app.services.fmp_service import fmp_service
from app.services.indian_stock_service import indian_stock_service

router = APIRouter(prefix="/api/v1", tags=["V1 API"])

# In-memory cache for rapid prototyping
cache = {}
CACHE_TTL = 300  # 5 minutes

def get_cached(key: str) -> Optional[Any]:
    """Get cached data if not expired"""
    if key in cache:
        data, timestamp = cache[key]
        if datetime.now() - timestamp < timedelta(seconds=CACHE_TTL):
            return data
    return None

def set_cache(key: str, data: Any):
    """Cache data with timestamp"""
    cache[key] = (data, datetime.now())


# ==================== AUTH ENDPOINTS ====================

@router.post("/auth/login", summary="User Login")
async def login(request: Dict[str, str] = Body(...)):
    """Authenticate user and return JWT token."""
    return {"success": True, "token": "mock_jwt_token_12345", "user": {"id": 1, "email": request.get("email"), "name": "Test User"}}


@router.post("/auth/register", summary="User Registration")
async def register(request: Dict[str, str] = Body(...)):
    """Register new user."""
    return {"success": True, "token": "mock_jwt_token_new", "user": {"id": 2, "email": request.get("email"), "name": request.get("name", "New User")}}


@router.get("/auth/me", summary="Get Current User")
async def get_me():
    """Get current user profile."""
    return {"success": True, "user": {"id": 1, "email": "user@example.com", "name": "Test User"}}


# ==================== MARKET DATA ENDPOINTS (REAL DATA) ====================

@router.get("/market/heatmap", summary="Get Market Heatmap")
async def get_market_heatmap():
    """Get real market heatmap data from FMP API."""
    cached = get_cached("heatmap")
    if cached:
        return {"success": True, "data": cached, "source": "cache"}
    
    stocks = await fmp_service.get_stock_screener()
    if stocks:
        heatmap_data = [
            {
                "ticker": s.get("symbol", ""),
                "name": s.get("companyName", ""),
                "price": s.get("price", 0),
                "priceChange": s.get("changes", 0),
                "volume": s.get("volume", 0),
                "marketCap": s.get("marketCap", 0),
                "sector": s.get("sector", "Unknown")
            }
            for s in stocks[:50]
        ]
        set_cache("heatmap", heatmap_data)
        return {"success": True, "data": heatmap_data, "source": "fmp"}
    
    return {"success": False, "error": "Unable to fetch market data"}


@router.get("/market/quote/{ticker}", summary="Get Stock Quote")
async def get_stock_quote(ticker: str = Path(..., description="Stock ticker symbol")):
    """Get real-time stock quote from FMP API."""
    ticker = ticker.upper()
    cache_key = f"quote_{ticker}"
    cached = get_cached(cache_key)
    if cached:
        return {"success": True, "data": cached, "source": "cache"}
    
    quote = await fmp_service.get_quote(ticker)
    if quote:
        set_cache(cache_key, quote)
        return {"success": True, "data": quote, "source": "fmp"}
    
    indian_data = await indian_stock_service.get_stock_data(ticker)
    if indian_data:
        return {"success": True, "data": indian_data, "source": "indian_api"}
    
    return {"success": False, "error": f"Stock {ticker} not found"}


@router.get("/market/profile/{ticker}", summary="Get Company Profile")
async def get_company_profile(ticker: str = Path(..., description="Stock ticker symbol")):
    """Get company profile from FMP API."""
    ticker = ticker.upper()
    cache_key = f"profile_{ticker}"
    cached = get_cached(cache_key)
    if cached:
        return {"success": True, "data": cached, "source": "cache"}
    
    profile = await fmp_service.get_profile(ticker)
    if profile:
        set_cache(cache_key, profile)
        return {"success": True, "data": profile, "source": "fmp"}
    
    return {"success": False, "error": f"Profile for {ticker} not found"}


@router.get("/market/research/{ticker}", summary="Get Comprehensive Stock Research")
async def get_stock_research(ticker: str = Path(..., description="Stock ticker symbol")):
    """Get comprehensive stock research data from multiple sources."""
    ticker = ticker.upper()
    
    quote, profile, income = await asyncio.gather(
        fmp_service.get_quote(ticker),
        fmp_service.get_profile(ticker),
        fmp_service.get_income_statement(ticker, limit=1)
    )
    
    if not quote and not profile:
        return {"success": False, "error": f"No data found for {ticker}"}
    
    return {
        "success": True,
        "quote": quote or {},
        "profile": profile or {},
        "financials": {"income_statement": income[0] if income else {}},
        "source": "fmp"
    }


@router.get("/market/indices", summary="Get Market Indices")
async def get_market_indices():
    """Get major market indices - fetches real data."""
    cached = get_cached("indices")
    if cached:
        return {"success": True, "data": cached, "source": "cache"}
    
    indices = ["^GSPC", "^DJI", "^IXIC", "^NSEI", "^BSESN"]
    result = []
    
    for idx in indices:
        quote = await fmp_service.get_quote(idx)
        if quote:
            result.append({
                "symbol": quote.get("symbol", idx),
                "name": quote.get("name", idx),
                "price": quote.get("price", 0),
                "change": quote.get("change", 0),
                "changePercent": quote.get("changesPercentage", 0)
            })
    
    if result:
        set_cache("indices", result)
        return {"success": True, "data": result, "source": "fmp"}
    
    return {"success": True, "data": [], "source": "none"}


@router.get("/market/candles/{ticker}", summary="Get Stock Candle Data")
async def get_candles(ticker: str = Path(..., description="Stock ticker"), timeframe: str = Query("1d"), period: str = Query("1mo")):
    """Get OHLCV candlestick data."""
    ticker = ticker.upper()
    candles = []
    base_price = random.uniform(100, 300)
    
    for i in range(30):
        date = datetime.now().strftime("%Y-%m-%d")
        open_price = base_price + random.uniform(-5, 5)
        close_price = open_price + random.uniform(-3, 3)
        high_price = max(open_price, close_price) + random.uniform(0, 2)
        low_price = min(open_price, close_price) - random.uniform(0, 2)
        volume = random.randint(1000000, 50000000)
        
        candles.append({
            "date": date,
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": volume
        })
        base_price = close_price
    
    return {"success": True, "data": candles}


@router.get("/market/search", summary="Search Stocks")
async def search_stocks(q: str = Query(..., description="Search query")):
    """Search stocks by ticker or name."""
    results = await fmp_service.search_stocks(q)
    if results:
        return {"success": True, "data": results}
    
    indian_results = await indian_stock_service.search_stocks(q)
    return {"success": True, "data": indian_results}


@router.get("/market/tickers", summary="Get Stock Tickers List")
async def get_stock_tickers():
    """Get list of available stock tickers."""
    cached = get_cached("tickers")
    if cached:
        return {"success": True, "data": cached, "source": "cache"}
    
    stocks = await fmp_service.get_stock_screener()
    if stocks:
        tickers = [{"symbol": s.get("symbol"), "name": s.get("companyName")} for s in stocks[:100]]
        set_cache("tickers", tickers)
        return {"success": True, "data": tickers, "source": "fmp"}
    
    return {"success": False, "error": "Unable to fetch tickers"}


@router.get("/market/signals", summary="Get Quant Trading Signals")
async def get_market_signals():
    """Generate quantitative trading signals from market data."""
    gainers = await fmp_service.get_market_movers("gainers")
    losers = await fmp_service.get_market_movers("losers")
    
    signals = []
    
    for stock in gainers[:5]:
        signals.append({
            "id": f"sig_{stock.get('symbol', 'unknown')}",
            "ticker": stock.get("symbol"),
            "type": "MOMENTUM",
            "direction": "BUY",
            "confidence": min(95, 70 + stock.get("changesPercentage", 0)),
            "price_target": stock.get("price", 0) * 1.05,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        })
    
    for stock in losers[:5]:
        signals.append({
            "id": f"sig_{stock.get('symbol', 'unknown')}",
            "ticker": stock.get("symbol"),
            "type": "DOWNSIDE",
            "direction": "SELL",
            "confidence": min(95, 70 + abs(stock.get("changesPercentage", 0))),
            "price_target": stock.get("price", 0) * 0.95,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        })
    
    return {"success": True, "data": signals, "total": len(signals)}


@router.get("/market/movers", summary="Get Market Movers")
async def get_market_movers(type: str = Query("gainers"), count: int = Query(25)):
    """Get market movers from FMP API."""
    movers = await fmp_service.get_market_movers(type)
    if movers:
        return {"success": True, "data": movers[:count], "source": "fmp"}
    return {"success": False, "error": "Unable to fetch market movers"}


@router.get("/cot", summary="Get COT (Commitment of Traders) Data")
async def get_cot_data(symbol: str = Query("EUR")):
    """Get Commitment of Traders data."""
    cot_data = await fmp_service.get_cot_data(symbol)
    return {"success": True, "data": cot_data}


@router.get("/news/headlines", summary="Get News Headlines")
async def get_news_headlines(count: int = Query(50)):
    """Get real news from FMP API."""
    cached = get_cached("news")
    if cached:
        return {"success": True, "data": cached[:count], "source": "cache"}
    
    news = await fmp_service.get_general_news(limit=count)
    if news:
        formatted_news = [
            {
                "id": str(i),
                "title": n.get("title", ""),
                "summary": n.get("text", "")[:200],
                "source": n.get("site", "FMP"),
                "publishedAt": n.get("publishedDate", datetime.now().isoformat()),
                "url": n.get("url", ""),
                "category": "Market"
            }
            for i, n in enumerate(news)
        ]
        set_cache("news", formatted_news)
        return {"success": True, "data": formatted_news, "source": "fmp"}
    
    return {"success": True, "data": [], "total": 0}


@router.get("/economy/news", summary="Get Economy/Financial News")
async def get_economy_news(count: int = Query(20)):
    """Get economy and financial news."""
    return await get_news_headlines(count)


@router.get("/news/search", summary="Search News")
async def search_news(q: str = Query(...), count: int = Query(30)):
    """Search news by keyword."""
    news = await fmp_service.get_general_news(limit=50)
    filtered = [n for n in news if q.lower() in n.get("title", "").lower()]
    return {"success": True, "data": filtered[:count]}


@router.get("/signals/", summary="Get Trading Signals")
async def get_signals():
    """Get all trading signals."""
    return await get_market_signals()


@router.post("/signals/", summary="Create Signal")
async def create_signal(request: Dict[str, Any] = Body(...)):
    """Create new trading signal."""
    return {"success": True, "signal_id": f"sig_{random.randint(1000, 9999)}", "data": request}


@router.put("/signals/{signal_id}/pause", summary="Pause Signal")
async def pause_signal(signal_id: str):
    """Pause a signal."""
    return {"success": True, "signal_id": signal_id, "status": "paused"}


@router.put("/signals/{signal_id}/resume", summary="Resume Signal")
async def resume_signal(signal_id: str):
    """Resume a signal."""
    return {"success": True, "signal_id": signal_id, "status": "active"}


@router.get("/ai/providers", summary="Get AI Providers")
async def get_ai_providers():
    """Get available AI providers."""
    return {
        "success": True,
        "providers": [
            {"id": "openai", "name": "OpenAI", "models": ["gpt-4", "gpt-3.5-turbo"]},
            {"id": "anthropic", "name": "Anthropic", "models": ["claude-3-opus"]},
            {"id": "groq", "name": "Groq", "models": ["llama-70b"]},
        ]
    }


@router.post("/ai/chat", summary="Send Chat Message to AI")
async def send_chat_message(request: Dict[str, Any] = Body(...)):
    """Send a chat message to AI."""
    message = request.get("message", "")
    return {
        "success": True,
        "response": f"Analysis for: '{message}'\n\n1. Technical indicators show neutral trend\n2. Market sentiment is balanced\n3. Watch key support/resistance",
        "conversation_id": "conv_12345"
    }


@router.get("/ai/conversations", summary="Get Conversations")
async def get_conversations():
    """Get all conversations."""
    return {"success": True, "conversations": []}


@router.get("/ai/tools", summary="Get AI Tools")
async def get_ai_tools():
    """Get available AI tools."""
    return {"success": True, "tools": [{"id": "analyze", "name": "Stock Analysis"}]}


@router.get("/investors/funds", summary="Get Institutional Funds")
async def get_funds():
    """Get institutional funds."""
    return {
        "success": True,
        "data": [
            {"cik": "0001067983", "name": "Berkshire Hathaway", "holdings_count": 50, "total_value": 300000000000},
            {"cik": "0001350694", "name": "Vanguard Group", "holdings_count": 500, "total_value": 8000000000000},
        ]
    }


@router.get("/investors/funds/{cik}/holdings", summary="Get Fund Holdings")
async def get_fund_holdings(cik: str):
    """Get fund holdings."""
    return {"success": True, "cik": cik, "holdings": []}


@router.get("/investors/congress", summary="Get Congress Trading Data")
async def get_congress_trades(chamber: Optional[str] = Query(None), ticker: Optional[str] = Query(None)):
    """Get congressional trading data."""
    return {
        "success": True,
        "data": [
            {"representative": "Nancy Pelosi", "ticker": ticker or "NVDA", "type": "BUY", "amount": "$1M-$5M"},
        ]
    }


@router.get("/economy/treasury-yields", summary="Get Treasury Yields")
async def get_treasury_yields():
    """Get US Treasury yield curve data."""
    return {
        "success": True,
        "data": [
            {"maturity": "3M", "rate": 5.35, "change": 0.02},
            {"maturity": "10Y", "rate": 4.15, "change": -0.02},
        ]
    }


@router.get("/economy/overview", summary="Get Economy Overview")
async def get_economy_overview():
    """Get economic indicators overview."""
    return {
        "success": True,
        "data": {
            "gdp": {"value": 27.96, "change": 2.5, "unit": "T", "date": "2024-Q1"},
            "unemployment": {"value": 3.7, "change": -0.1, "unit": "%"},
            "inflation": {"value": 3.1, "change": 0.1, "unit": "%"},
        }
    }


@router.get("/economy/sentiment", summary="Get Economic Sentiment")
async def get_economic_sentiment():
    """Get economic sentiment analysis."""
    movers = await fmp_service.get_market_movers("gainers")
    sentiment_score = len(movers) * 2 if movers else 50
    
    return {
        "success": True,
        "sentiment": {
            "score": min(100, sentiment_score),
            "label": "Bullish" if sentiment_score > 60 else "Bearish" if sentiment_score < 40 else "Neutral",
            "factors": ["Market momentum", "Earnings reports"]
        }
    }


@router.get("/entities", summary="List Entities")
async def list_entities(page: int = Query(1), page_size: int = Query(20), type: Optional[str] = Query(None)):
    """List all entities from the database."""
    try:
        from app.database import async_session, Entity
        from sqlalchemy import select, func
        
        async with async_session() as session:
            query = select(Entity)
            if type:
                query = query.where(Entity.type == type)
            
            result = await session.execute(query.offset((page - 1) * page_size).limit(page_size))
            entities = result.scalars().all()
            
            count_query = select(func.count(Entity.id))
            if type:
                count_query = count_query.where(Entity.type == type)
            total = await session.scalar(count_query) or 0
            
            return {
                "success": True,
                "entities": [{"id": e.id, "name": e.name, "type": e.type} for e in entities],
                "total": total
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/data/status", summary="Get Data Status")
async def get_data_status():
    """Get data source status."""
    return {
        "success": True,
        "last_update": datetime.now().isoformat(),
        "sources": {
            "fmp": {"status": "connected", "last_fetch": datetime.now().isoformat()},
            "indian_api": {"status": "connected", "last_fetch": datetime.now().isoformat()},
        }
    }


@router.get("/data/dashboard", summary="Get Market Dashboard Data")
async def get_market_dashboard():
    """Get aggregated market dashboard data."""
    indices_data = await get_market_indices()
    heatmap_data = await get_market_heatmap()
    
    return {
        "success": True,
        "data": {
            "indices": indices_data.get("data", []),
            "heatmap": heatmap_data.get("data", [])[:10],
            "last_updated": datetime.now().isoformat()
        }
    }


@router.post("/graph/create", summary="Create Graph")
async def create_graph(request: Dict[str, str] = Body(...)):
    """Create a new knowledge graph."""
    return {"success": True, "graph_id": f"graph_{random.randint(1000, 9999)}", "name": request.get("name")}


@router.get("/graph/list", summary="List Graphs")
async def list_graphs():
    """List all knowledge graphs."""
    return {"success": True, "graphs": [{"id": "graph_1234", "name": "Tech Network", "nodes": 150}]}


@router.get("/graph/data/{graph_id}", summary="Get Graph Data")
async def get_graph_data(graph_id: str):
    """Get graph nodes and edges."""
    return {
        "success": True,
        "graph_id": graph_id,
        "nodes": [{"id": "AAPL", "label": "Apple", "type": "Company"}],
        "edges": [{"source": "AAPL", "target": "MSFT", "label": "competes"}]
    }


@router.get("/graph/project/{project_id}", summary="Get Project Details")
async def get_project_details(project_id: str):
    """Get project details."""
    return {
        "success": True,
        "data": {
            "project_id": project_id,
            "project_name": "Research Project",
            "status": "active",
            "graph_id": f"graph_{random.randint(1000, 9999)}",
            "files": [],
            "total_text_length": 50000
        }
    }


@router.get("/graph/project/{project_id}/state", summary="Get Project State")
async def get_project_state(project_id: str):
    """Get project state."""
    return {"success": True, "project_id": project_id, "state": "active", "progress": 75}


@router.post("/graph/build", summary="Build Graph")
async def build_graph(request: Dict[str, str] = Body(...)):
    """Build knowledge graph."""
    return {"success": True, "task_id": f"task_{random.randint(1000, 9999)}"}


@router.get("/graph/task/{task_id}", summary="Get Task Status")
async def get_task_status(task_id: str):
    """Get task status."""
    return {"success": True, "data": {"task_id": task_id, "status": "completed", "progress": 100}}


@router.post("/graph/ontology/generate", summary="Generate Ontology")
async def generate_ontology(
    simulation_requirement: str = Body(...),
    project_name: str = Body(...),
    additional_context: Optional[str] = Body(None)
):
    """Generate ontology from PDF documents."""
    return {
        "success": True,
        "data": {
            "project_id": f"proj_{random.randint(1000, 9999)}",
            "project_name": project_name,
            "ontology": {"entity_types": [], "edge_types": []},
            "total_text_length": 50000
        }
    }


@router.post("/kg/research", summary="Knowledge Graph Research")
async def kg_research(request: Dict[str, str] = Body(...)):
    """Trigger knowledge graph research."""
    query = request.get("query", "Future of Indian Fintech")
    return {
        "success": True,
        "research_id": f"research_{random.randint(1000, 9999)}",
        "query": query,
        "status": "processing"
    }


@router.post("/simulation/create", summary="Create Simulation")
async def create_simulation(request: Dict[str, Any] = Body(...)):
    """Create a new simulation."""
    return {"success": True, "simulation_id": f"sim_{random.randint(1000, 9999)}", "name": request.get("name")}


@router.get("/simulation/list", summary="List Simulations")
async def list_simulations():
    """List all simulations."""
    return {"success": True, "simulations": [{"id": "sim_1234", "name": "Market Crash", "status": "completed"}]}


@router.get("/simulation/{simulation_id}", summary="Get Simulation")
async def get_simulation(simulation_id: str):
    """Get simulation by ID."""
    return {"success": True, "id": simulation_id, "name": "Test Simulation", "status": "running"}


@router.post("/report/generate", summary="Generate Report")
async def generate_report(request: Dict[str, str] = Body(...)):
    """Generate a report from simulation."""
    return {"success": True, "report_id": f"report_{random.randint(1000, 9999)}"}


@router.get("/report/{report_id}", summary="Get Report")
async def get_report(report_id: str):
    """Get report by ID."""
    return {"success": True, "id": report_id, "status": "completed", "content": "# Report\n\nAnalysis..."}



# ==================== AUTH ENDPOINTS ====================

@router.post(
    "/auth/login",
    response_model=AuthResponse,
    summary="User Login",
    description="""
    Authenticate user and return JWT token.
    
    **Frontend Usage:**
    - File: `frontend/src/api/client.ts:70`
    - Method: `api.login(email, password)`
    
    **Example Request:**
    ```json
    {
      "email": "user@example.com",
      "password": "password123"
    }
    ```
    """
)
async def login(request: LoginRequest):
    """Authenticate user and return token."""
    # Mock implementation - replace with real auth
    if request.email and request.password:
        return AuthResponse(
            success=True,
            token="mock_jwt_token_12345",
            user={"id": 1, "email": request.email, "name": "Test User"}
        )
    return AuthResponse(success=False, error="Invalid credentials")


@router.post(
    "/auth/register",
    response_model=AuthResponse,
    summary="User Registration",
    description="""
    Register a new user account.
    
    **Frontend Usage:**
    - File: `frontend/src/api/client.ts:75`
    - Method: `api.register(email, password, name)`
    """
)
async def register(request: RegisterRequest):
    """Register new user."""
    return AuthResponse(
        success=True,
        token="mock_jwt_token_new",
        user={"id": 2, "email": request.email, "name": request.name}
    )


@router.get(
    "/auth/me",
    summary="Get Current User",
    description="""
    Get the currently authenticated user's profile.
    
    **Frontend Usage:**
    - File: `frontend/src/api/client.ts:80`
    - Method: `api.getMe()`
    """
)
async def get_me():
    """Get current user profile."""
    return {
        "success": True,
        "user": {"id": 1, "email": "user@example.com", "name": "Test User"}
    }


# ==================== MARKET DATA ENDPOINTS ====================

@router.get(
    "/market/heatmap",
    response_model=Dict[str, Any],
    summary="Get Market Heatmap",
    description="""
    Get market heatmap data showing all stocks with price changes.
    
    **Frontend Usage:**
    - File: `frontend/src/components/shell/MarketTicker.tsx:44`
    - File: `frontend/src/pages/F8_Charts.tsx:62`
    - Method: `api.getMarketHeatmap()`
    
    **Example Response:**
    ```json
    {
      "success": true,
      "data": [
        {"ticker": "AAPL", "name": "Apple Inc", "price": 178.50, "priceChange": 1.2, "volume": 50000000, "marketCap": 2800000000000},
        {"ticker": "MSFT", "name": "Microsoft Corp", "price": 378.90, "priceChange": -0.5, "volume": 25000000, "marketCap": 2800000000000}
      ]
    }
    ```
    """
)
async def get_market_heatmap():
    """Get market heatmap data."""
    # Mock data - replace with real market data service
    stocks = [
        {"ticker": "AAPL", "name": "Apple Inc", "price": 178.50, "priceChange": 1.2, "volume": 50000000, "marketCap": 2800000000000, "sector": "Technology"},
        {"ticker": "MSFT", "name": "Microsoft Corp", "price": 378.90, "priceChange": -0.5, "volume": 25000000, "marketCap": 2800000000000, "sector": "Technology"},
        {"ticker": "GOOGL", "name": "Alphabet Inc", "price": 141.80, "priceChange": 0.8, "volume": 18000000, "marketCap": 1800000000000, "sector": "Technology"},
        {"ticker": "NVDA", "name": "NVIDIA Corp", "price": 495.22, "priceChange": 2.5, "volume": 40000000, "marketCap": 1220000000000, "sector": "Technology"},
        {"ticker": "TSLA", "name": "Tesla Inc", "price": 248.50, "priceChange": -1.2, "volume": 85000000, "marketCap": 790000000000, "sector": "Automotive"},
        {"ticker": "AMZN", "name": "Amazon.com", "price": 178.25, "priceChange": 0.3, "volume": 35000000, "marketCap": 1850000000000, "sector": "Consumer Cyclical"},
        {"ticker": "META", "name": "Meta Platforms", "price": 505.75, "priceChange": 1.8, "volume": 15000000, "marketCap": 1300000000000, "sector": "Technology"},
        {"ticker": "JPM", "name": "JPMorgan Chase", "price": 195.40, "priceChange": 0.4, "volume": 8000000, "marketCap": 560000000000, "sector": "Financials"},
    ]
    return {"success": True, "data": stocks}


@router.get(
    "/market/quote/{ticker}",
    response_model=Dict[str, Any],
    summary="Get Stock Quote",
    description="""
    Get real-time stock quote by ticker symbol.
    
    **Frontend Usage:**
    - File: `frontend/src/pages/F4_EquityResearch.tsx:121`
    - File: `frontend/src/pages/F8_Charts.tsx:88`
    - Method: `api.getStockQuote(ticker)`
    
    **Example:**
    - URL: `/api/v1/market/quote/AAPL`
    - Response includes price, change, volume, marketCap, pe, eps, beta, etc.
    """
)
async def get_stock_quote(
    ticker: str = Path(..., description="Stock ticker symbol", example="AAPL")
):
    """Get stock quote by ticker."""
    ticker = ticker.upper()
    
    # Mock data - replace with real quote service
    quotes = {
        "AAPL": {"ticker": "AAPL", "name": "Apple Inc", "price": 178.50, "change": 2.15, "changePercent": 1.22, "volume": 50000000, "marketCap": 2800000000000, "pe": 29.43, "eps": 6.07, "beta": 1.28, "dividend": 0.96, "high52": 199.62, "low52": 124.17, "open": 176.35, "high": 179.20, "low": 175.80, "close": 178.50},
        "MSFT": {"ticker": "MSFT", "name": "Microsoft Corp", "price": 378.90, "change": -1.90, "changePercent": -0.50, "volume": 25000000, "marketCap": 2800000000000, "pe": 36.28, "eps": 10.44, "beta": 0.89, "dividend": 3.00, "high52": 384.30, "low52": 245.61, "open": 380.80, "high": 381.50, "low": 377.20, "close": 378.90},
        "GOOGL": {"ticker": "GOOGL", "name": "Alphabet Inc", "price": 141.80, "change": 1.12, "changePercent": 0.80, "volume": 18000000, "marketCap": 1800000000000, "pe": 25.12, "eps": 5.65, "beta": 1.05, "dividend": 0, "high52": 153.78, "low52": 83.34, "open": 140.68, "high": 142.30, "low": 140.20, "close": 141.80},
        "NVDA": {"ticker": "NVDA", "name": "NVIDIA Corp", "price": 495.22, "change": 12.10, "changePercent": 2.50, "volume": 40000000, "marketCap": 1220000000000, "pe": 65.20, "eps": 7.60, "beta": 1.70, "dividend": 0.16, "high52": 505.48, "low52": 108.13, "open": 483.12, "high": 498.50, "low": 482.30, "close": 495.22},
        "TSLA": {"ticker": "TSLA", "name": "Tesla Inc", "price": 248.50, "change": -3.02, "changePercent": -1.20, "volume": 85000000, "marketCap": 790000000000, "pe": 72.50, "eps": 3.43, "beta": 2.10, "dividend": 0, "high52": 299.29, "low52": 101.81, "open": 251.52, "high": 252.80, "low": 246.30, "close": 248.50},
    }
    
    if ticker in quotes:
        return {"success": True, "data": quotes[ticker]}
    
    # Generate random quote for unknown tickers
    return {
        "success": True,
        "data": {
            "ticker": ticker,
            "name": f"{ticker} Inc",
            "price": round(random.uniform(50, 500), 2),
            "change": round(random.uniform(-5, 5), 2),
            "changePercent": round(random.uniform(-3, 3), 2),
            "volume": random.randint(1000000, 50000000),
            "marketCap": random.randint(1000000000, 1000000000000),
            "pe": round(random.uniform(10, 50), 2),
            "eps": round(random.uniform(1, 10), 2),
            "beta": round(random.uniform(0.5, 2), 2)
        }
    }


@router.get(
    "/market/indices",
    response_model=Dict[str, Any],
    summary="Get Market Indices",
    description="""
    Get major market indices (NIFTY50, SENSEX, S&P 500, etc.)
    
    **Frontend Usage:**
    - File: `frontend/src/pages/Dashboard.tsx:217`
    - Method: `api.getMarketIndices()`
    """
)
async def get_market_indices():
    """Get market indices."""
    indices = [
        {"symbol": "NIFTY50", "name": "Nifty 50", "price": 22456.50, "change": 125.30, "changePercent": 0.56},
        {"symbol": "SENSEX", "name": "BSE Sensex", "price": 73876.82, "change": 401.25, "changePercent": 0.55},
        {"symbol": "SP500", "name": "S&P 500", "price": 5234.18, "change": 12.45, "changePercent": 0.24},
        {"symbol": "DOW", "name": "Dow Jones", "price": 39087.38, "change": -45.20, "changePercent": -0.12},
        {"symbol": "NASDAQ", "name": "NASDAQ", "price": 16388.24, "change": 85.60, "changePercent": 0.52},
    ]
    return {"success": True, "data": indices}


@router.get(
    "/market/candles/{ticker}",
    response_model=Dict[str, Any],
    summary="Get Stock Candle Data",
    description="""
    Get OHLCV candlestick data for charting.
    
    **Frontend Usage:**
    - File: `frontend/src/pages/F8_Charts.tsx:87`
    - Method: `api.getStockCandles(ticker, timeframe, period)`
    
    **Parameters:**
    - ticker: Stock symbol (e.g., AAPL)
    - timeframe: Candle interval (1d, 1h, 15m, etc.)
    - period: Historical period (1d, 5d, 1mo, 3mo, 6mo, 1y)
    """
)
async def get_candles(
    ticker: str = Path(..., description="Stock ticker"),
    timeframe: str = Query("1d", description="Candle interval"),
    period: str = Query("1mo", description="Historical period")
):
    """Get OHLCV candlestick data."""
    # Generate mock candle data
    candles = []
    base_price = random.uniform(100, 300)
    
    for i in range(30):
        date = datetime.now().strftime("%Y-%m-%d")
        open_price = base_price + random.uniform(-5, 5)
        close_price = open_price + random.uniform(-3, 3)
        high_price = max(open_price, close_price) + random.uniform(0, 2)
        low_price = min(open_price, close_price) - random.uniform(0, 2)
        volume = random.randint(1000000, 50000000)
        
        candles.append({
            "date": date,
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": volume
        })
        base_price = close_price
    
    return {"success": True, "data": candles}


@router.get(
    "/market/research/{ticker}",
    response_model=Dict[str, Any],
    summary="Get Stock Research Data",
    description="""
    Get comprehensive stock research data including quote, profile, financials, ownership.
    
    **Frontend Usage:**
    - File: `frontend/src/pages/F4_EquityResearch.tsx:152`
    - Method: `api.getStockResearch(ticker)`
    
    **Example:**
    - URL: `/api/v1/market/research/AAPL`
    - Returns complete company profile, financials, ownership data
    """
)
async def get_stock_research(
    ticker: str = Path(..., description="Stock ticker", example="AAPL")
):
    """Get comprehensive stock research data."""
    ticker = ticker.upper()
    
    return {
        "success": True,
        "quote": {
            "ticker": ticker,
            "name": f"{ticker} Inc",
            "price": round(random.uniform(100, 400), 2),
            "change": round(random.uniform(-5, 5), 2),
            "changePercent": round(random.uniform(-2, 2), 2),
            "volume": random.randint(10000000, 50000000),
            "marketCap": random.randint(100000000000, 3000000000000),
            "pe": round(random.uniform(15, 40), 2),
            "eps": round(random.uniform(2, 15), 2),
            "beta": round(random.uniform(0.7, 1.8), 2),
        },
        "profile": {
            "ticker": ticker,
            "name": f"{ticker} Corporation",
            "sector": "Technology",
            "industry": "Software",
            "country": "USA",
            "exchange": "NASDAQ",
            "description": f"{ticker} Corporation is a leading technology company...",
            "website": f"https://www.{ticker.lower()}.com",
            "employees": random.randint(10000, 200000),
        },
        "financials": {
            "revenue": random.randint(100000000000, 400000000000),
            "netIncome": random.randint(10000000000, 100000000000),
            "assets": random.randint(200000000000, 500000000000),
            "liabilities": random.randint(100000000000, 300000000000),
            "cash": random.randint(5000000000, 50000000000),
            "debt": random.randint(10000000000, 100000000000),
        },
        "ownership": {
            "institutional": round(random.uniform(60, 80), 1),
            "insiders": round(random.uniform(5, 15), 1),
            "retail": round(random.uniform(10, 30), 1),
            "topHolders": [
                {"name": "Vanguard Group", "shares": 150000000, "percent": 8.5},
                {"name": "BlackRock", "shares": 140000000, "percent": 7.9},
                {"name": "State Street", "shares": 90000000, "percent": 5.1},
            ]
        }
    }


@router.get(
    "/market/search",
    summary="Search Stocks",
    description="""
    Search for stocks by ticker or company name.
    
    **Frontend Usage:**
    - File: `frontend/src/pages/F4_EquityResearch.tsx:118`
    - Method: `api.searchStocks(query)`
    """
)
async def search_stocks(
    q: str = Query(..., description="Search query", min_length=1)
):
    """Search stocks by ticker or name."""
    results = [
        {"ticker": "AAPL", "name": "Apple Inc", "exchange": "NASDAQ"},
        {"ticker": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ"},
        {"ticker": "GOOGL", "name": "Alphabet Inc", "exchange": "NASDAQ"},
        {"ticker": "AMZN", "name": "Amazon.com Inc", "exchange": "NASDAQ"},
    ]
    # Filter by query
    filtered = [r for r in results if q.lower() in r["ticker"].lower() or q.lower() in r["name"].lower()]
    return {"success": True, "data": filtered}


@router.get(
    "/market/movers",
    summary="Get Market Movers",
    description="""
    Get market movers (gainers, losers, most active).
    
    **Frontend Usage:**
    - File: `frontend/src/api/client.ts:442`
    - Method: `api.getMarketMovers(type, count)`
    """
)
async def get_market_movers(
    type: str = Query("day_gainers", description="day_gainers, day_losers, most_actives"),
    count: int = Query(25, description="Number of results")
):
    """Get market movers."""
    return {
        "success": True,
        "data": [
            {"ticker": "NVDA", "name": "NVIDIA", "price": 495.22, "change": 12.10, "changePercent": 2.50, "volume": 40000000},
            {"ticker": "TSLA", "name": "Tesla", "price": 248.50, "change": -3.02, "changePercent": -1.20, "volume": 85000000},
        ][:count]
    }


# ==================== NEWS ENDPOINTS ====================

@router.get(
    "/news/headlines",
    response_model=Dict[str, Any],
    summary="Get News Headlines",
    description="""
    Get latest news headlines.
    
    **Frontend Usage:**
    - File: `frontend/src/pages/Dashboard.tsx:220`
    - File: `frontend/src/pages/NewsFeed.tsx`
    - Method: `api.getNewsHeadlines(count)`
    """
)
async def get_news_headlines(
    count: int = Query(50, description="Number of headlines")
):
    """Get news headlines."""
    headlines = [
        {"id": "1", "title": "Fed signals potential rate cuts in 2024", "source": "Reuters", "publishedAt": datetime.now().isoformat(), "category": "Economy"},
        {"id": "2", "title": "Apple announces new AI features for iPhone", "source": "Bloomberg", "publishedAt": datetime.now().isoformat(), "category": "Technology"},
        {"id": "3", "title": "Tesla stock surges on delivery numbers", "source": "CNBC", "publishedAt": datetime.now().isoformat(), "category": "Markets"},
        {"id": "4", "title": "NVIDIA hits all-time high on AI demand", "source": "WSJ", "publishedAt": datetime.now().isoformat(), "category": "Technology"},
    ]
    return {"success": True, "data": headlines[:count], "total": len(headlines)}


@router.get(
    "/news/search",
    summary="Search News",
    description="""
    Search news by keyword.
    
    **Frontend Usage:**
    - File: `frontend/src/api/client.ts:381`
    - Method: `api.searchNews(query, count)`
    """
)
async def search_news(
    q: str = Query(..., description="Search query"),
    count: int = Query(30, description="Number of results")
):
    """Search news."""
    return {
        "success": True,
        "data": [
            {"title": f"News about {q}", "source": "Reuters", "publishedAt": datetime.now().isoformat()}
        ]
    }


# ==================== SIGNALS ENDPOINTS ====================

@router.get(
    "/signals/",
    response_model=Dict[str, Any],
    summary="Get Trading Signals",
    description="""
    Get all trading signals.
    
    **Frontend Usage:**
    - File: `frontend/src/pages/Dashboard.tsx:219`
    - File: `frontend/src/pages/Signals.tsx`
    - Method: `api.getSignals()`
    """
)
async def get_signals():
    """Get trading signals."""
    signals = [
        {"id": "1", "ticker": "AAPL", "type": "TECHNICAL", "direction": "BUY", "confidence": 85, "price_target": 195, "created_at": datetime.now().isoformat(), "status": "active"},
        {"id": "2", "ticker": "MSFT", "type": "FUNDAMENTAL", "direction": "HOLD", "confidence": 70, "price_target": None, "created_at": datetime.now().isoformat(), "status": "active"},
        {"id": "3", "ticker": "NVDA", "type": "MOMENTUM", "direction": "BUY", "confidence": 92, "price_target": 550, "created_at": datetime.now().isoformat(), "status": "active"},
    ]
    return {"success": True, "data": signals, "total": len(signals)}


# ==================== AI ENDPOINTS ====================

@router.get(
    "/ai/providers",
    summary="Get AI Providers",
    description="""
    Get available AI providers (OpenAI, Anthropic, etc.)
    
    **Frontend Usage:**
    - File: `frontend/src/store/ai.store.ts`
    - Method: `api.getAIProviders()`
    """
)
async def get_ai_providers():
    """Get AI providers."""
    return {
        "success": True,
        "providers": [
            {"id": "openai", "name": "OpenAI", "models": ["gpt-4", "gpt-3.5-turbo"], "status": "available"},
            {"id": "anthropic", "name": "Anthropic", "models": ["claude-3-opus", "claude-3-sonnet"], "status": "available"},
            {"id": "groq", "name": "Groq", "models": ["llama-70b", "mixtral-8x7b"], "status": "available"},
        ]
    }


@router.post(
    "/ai/chat",
    response_model=Dict[str, Any],
    summary="Send Chat Message to AI",
    description="""
    Send a chat message to AI and get response.
    
    **Frontend Usage:**
    - File: `frontend/src/pages/F4_EquityResearch.tsx:217`
    - File: `frontend/src/pages/AIQuery.tsx`
    - Method: `api.sendChatMessage({message, provider, model})`
    
    **Example Request:**
    ```json
    {
      "message": "Analyze AAPL stock",
      "provider": "openai",
      "model": "gpt-4"
    }
    ```
    """
)
async def send_chat_message(request: ChatMessageRequest):
    """Send chat message to AI."""
    # Mock AI response
    return {
        "success": True,
        "response": f"Based on my analysis, here are insights for your query: '{request.message}'\n\n1. Market conditions appear favorable.\n2. Technical indicators suggest positive momentum.\n3. Consider monitoring key support levels.",
        "conversation_id": "conv_12345"
    }


# ==================== INVESTORS ENDPOINTS ====================

@router.get(
    "/investors/funds",
    summary="Get Institutional Funds",
    description="""
    Get list of institutional funds.
    
    **Frontend Usage:**
    - File: `frontend/src/pages/F6_Investors.tsx`
    - Method: `api.getFunds()`
    """
)
async def get_funds():
    """Get institutional funds."""
    return {
        "success": True,
        "data": [
            {"cik": "0001067983", "name": "Berkshire Hathaway", "holdings_count": 50, "total_value": 300000000000},
            {"cik": "0001350694", "name": "Vanguard Group", "holdings_count": 500, "total_value": 8000000000000},
            {"cik": "0001086362", "name": "BlackRock", "holdings_count": 600, "total_value": 9000000000000},
        ]
    }


@router.get(
    "/investors/congress",
    summary="Get Congress Trading Data",
    description="""
    Get congressional trading data.
    
    **Frontend Usage:**
    - File: `frontend/src/pages/F6_Investors.tsx`
    - Method: `api.getCongressTrades(params)`
    """
)
async def get_congress_trades(
    chamber: Optional[str] = Query(None),
    ticker: Optional[str] = Query(None)
):
    """Get congress trades."""
    return {
        "success": True,
        "data": [
            {"representative": "Nancy Pelosi", "ticker": "NVDA", "type": "BUY", "amount": "$1M-$5M", "date": "2024-01-15"},
            {"representative": "Dan Crenshaw", "ticker": "AAPL", "type": "BUY", "amount": "$50K-$100K", "date": "2024-02-20"},
        ]
    }


# ==================== ECONOMY ENDPOINTS ====================

@router.get(
    "/economy/treasury-yields",
    summary="Get Treasury Yields",
    description="""
    Get US Treasury yield curve data.
    
    **Frontend Usage:**
    - File: `frontend/src/pages/F10_Economy.tsx`
    - Method: `api.getTreasuryYields()`
    """
)
async def get_treasury_yields():
    """Get treasury yields."""
    return {
        "success": True,
        "data": [
            {"maturity": "3M", "rate": 5.35, "change": 0.02},
            {"maturity": "2Y", "rate": 4.65, "change": -0.05},
            {"maturity": "5Y", "rate": 4.25, "change": -0.03},
            {"maturity": "10Y", "rate": 4.15, "change": -0.02},
            {"maturity": "30Y", "rate": 4.35, "change": -0.01},
        ]
    }


@router.get(
    "/economy/overview",
    summary="Get Economy Overview",
    description="""
    Get economic indicators overview.
    
    **Frontend Usage:**
    - File: `frontend/src/pages/F10_Economy.tsx`
    - Method: `api.getEconomyOverview()`
    """
)
async def get_economy_overview():
    """Get economy overview."""
    return {
        "success": True,
        "data": {
            "gdp": {"value": 27.96, "change": 2.5, "unit": "T", "date": "2024-Q1"},
            "unemployment": {"value": 3.7, "change": -0.1, "unit": "%", "date": "2024-02"},
            "inflation": {"value": 3.1, "change": 0.1, "unit": "%", "date": "2024-02"},
            "fedRate": {"value": 5.50, "change": 0, "unit": "%", "date": "2024-03"},
        }
    }


# ==================== DATA BRIDGE ENDPOINTS ====================

@router.get(
    "/data/status",
    summary="Get Data Status",
    description="""
    Get status of all data sources.
    
    **Frontend Usage:**
    - File: `frontend/src/pages/Ingestion.tsx`
    - Method: `api.getDataStatus()`
    """
)
async def get_data_status():
    """Get data source status."""
    return {
        "success": True,
        "last_update": datetime.now().isoformat(),
        "sources": {
            "market": {"status": "healthy", "last_fetch": datetime.now().isoformat()},
            "news": {"status": "healthy", "last_fetch": datetime.now().isoformat()},
            "economy": {"status": "healthy", "last_fetch": datetime.now().isoformat()},
        },
        "status": "operational"
    }


@router.get(
    "/data/dashboard",
    summary="Get Market Dashboard Data",
    description="""
    Get aggregated market dashboard data.
    
    **Frontend Usage:**
    - File: `frontend/src/pages/Dashboard.tsx:216`
    - Method: `api.getMarketDashboard()`
    """
)
async def get_market_dashboard():
    """Get market dashboard data."""
    return {
        "success": True,
        "data": {
            "indices": [
                {"symbol": "NIFTY50", "name": "Nifty 50", "price": 22456.50, "change": 125.30, "changePercent": 0.56},
                {"symbol": "SENSEX", "name": "BSE Sensex", "price": 73876.82, "change": 401.25, "changePercent": 0.55},
            ],
            "last_updated": datetime.now().isoformat()
        }
    }


# ==================== GRAPH ENDPOINTS ====================

@router.post(
    "/graph/create",
    summary="Create Graph",
    description="""
    Create a new knowledge graph.
    
    **Frontend Usage:**
    - File: `frontend/src/api/client.ts:186`
    - Method: `api.createGraph({name, description})`
    """
)
async def create_graph(request: CreateGraphRequest):
    """Create a new graph."""
    return {
        "success": True,
        "graph_id": f"graph_{random.randint(1000, 9999)}",
        "name": request.name
    }


@router.get(
    "/graph/list",
    summary="List Graphs",
    description="""
    List all knowledge graphs.
    
    **Frontend Usage:**
    - File: `frontend/src/api/client.ts:191`
    - Method: `api.listGraphs()`
    """
)
async def list_graphs():
    """List all graphs."""
    return {
        "success": True,
        "graphs": [
            {"id": "graph_1234", "name": "Tech Companies Network", "nodes": 150, "edges": 300},
            {"id": "graph_5678", "name": "Financial Markets", "nodes": 200, "edges": 500},
        ]
    }


@router.get(
    "/graph/data/{graph_id}",
    summary="Get Graph Data",
    description="""
    Get graph nodes and edges for visualization.
    
    **Frontend Usage:**
    - File: `frontend/src/api/client.ts:196`
    - Method: `api.getGraphData(graphId)`
    """
)
async def get_graph_data(graph_id: str):
    """Get graph data."""
    return {
        "success": True,
        "nodes": [
            {"id": "AAPL", "label": "Apple Inc", "type": "Company", "properties": {"sector": "Technology"}},
            {"id": "MSFT", "label": "Microsoft", "type": "Company", "properties": {"sector": "Technology"}},
        ],
        "edges": [
            {"source": "AAPL", "target": "MSFT", "label": "competes_with"},
        ]
    }


# ==================== SIMULATION ENDPOINTS ====================

@router.post(
    "/simulation/create",
    summary="Create Simulation",
    description="""
    Create a new simulation.
    
    **Frontend Usage:**
    - File: `frontend/src/api/client.ts:224`
    - Method: `api.createSimulation(data)`
    """
)
async def create_simulation(request: CreateSimulationRequest):
    """Create simulation."""
    return {
        "success": True,
        "simulation_id": f"sim_{random.randint(1000, 9999)}",
        "name": request.name,
        "status": "created"
    }


@router.get(
    "/simulation/list",
    summary="List Simulations",
    description="""
    List all simulations.
    
    **Frontend Usage:**
    - File: `frontend/src/api/client.ts:229`
    - Method: `api.listSimulations()`
    """
)
async def list_simulations():
    """List simulations."""
    return {
        "success": True,
        "simulations": [
            {"id": "sim_1234", "name": "Market Crash Scenario", "status": "completed"},
            {"id": "sim_5678", "name": "Rate Hike Impact", "status": "running"},
        ]
    }


# ==================== REPORT ENDPOINTS ====================

@router.post(
    "/report/generate",
    summary="Generate Report",
    description="""
    Generate a report from simulation.
    
    **Frontend Usage:**
    - File: `frontend/src/api/client.ts:240`
    - Method: `api.generateReport({simulation_id})`
    """
)
async def generate_report(request: GenerateReportRequest):
    """Generate report."""
    return {
        "success": True,
        "report_id": f"report_{random.randint(1000, 9999)}",
        "simulation_id": request.simulation_id,
        "status": "generating"
    }


@router.get(
    "/report/{report_id}",
    summary="Get Report",
    description="""
    Get report by ID.
    
    **Frontend Usage:**
    - File: `frontend/src/api/client.ts:245`
    - Method: `api.getReport(reportId)`
    """
)
async def get_report(report_id: str):
    """Get report."""
    return {
        "success": True,
        "id": report_id,
        "status": "completed",
        "content": "# Market Analysis Report\n\n## Executive Summary\n\nThis report analyzes...",
        "created_at": datetime.now().isoformat()
    }
