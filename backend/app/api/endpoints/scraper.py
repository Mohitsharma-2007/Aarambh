"""Web Scraping API endpoints — Google Finance, News, Social Media"""
from fastapi import APIRouter, Query
from typing import Optional

from app.services.scraping_engine import scraping_engine

router = APIRouter()


# ── Google Finance ──

@router.get("/google-finance/{symbol}")
async def google_finance_quote(symbol: str):
    """Get stock quote from Google Finance (scrapes google.com/finance)"""
    data = await scraping_engine.google_finance_quote(symbol.upper())
    if not data:
        return {"error": f"No data for {symbol}", "symbol": symbol}
    return data


@router.get("/google-finance/batch")
async def google_finance_batch(
    symbols: str = Query(..., description="Comma-separated stock symbols"),
):
    """Get multiple stock quotes from Google Finance"""
    import asyncio
    tickers = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    tasks = [scraping_engine.google_finance_quote(t) for t in tickers[:20]]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [
        r if isinstance(r, dict) else {"symbol": t, "error": str(r) if isinstance(r, Exception) else "No data"}
        for t, r in zip(tickers, results)
    ]


# ── Yahoo Finance ──

@router.get("/yahoo-finance/{symbol}")
async def yahoo_finance_quote(symbol: str):
    """Get stock quote from Yahoo Finance"""
    data = await scraping_engine.yahoo_finance_quote(symbol.upper())
    if not data:
        return {"error": f"No Yahoo data for {symbol}"}
    return data


# ── Google News ──

@router.get("/google-news")
async def google_news_search(
    q: str = Query(..., description="Search query"),
    country: str = Query("IN", description="Country code"),
    limit: int = Query(20, ge=1, le=50),
):
    """Search Google News for articles"""
    return await scraping_engine.google_news_search(q, country, limit)


@router.get("/ai-mode")
async def google_ai_mode(
    q: str = Query(..., description="Query for AI overview/snippet"),
):
    """Extract Google AI overview or descriptive snippet"""
    return await scraping_engine.google_ai_mode(q)


@router.get("/google-news/india")
async def google_news_india():
    """Get latest India financial news"""
    return await scraping_engine.google_news_search("India stock market finance", "IN", 20)


@router.get("/google-news/stocks")
async def google_news_stocks(symbol: str = Query("NIFTY", description="Stock symbol")):
    """Get news for a specific stock"""
    return await scraping_engine.google_news_search(f"{symbol} stock NSE BSE", "IN", 15)


# ── Google Events ──

@router.get("/google-events")
async def google_events(
    q: str = Query("stock market India", description="Event search query"),
):
    """Search for upcoming financial events"""
    return await scraping_engine.google_events_search(q)


# ── Social Media ──

@router.get("/reddit/india-finance")
async def reddit_india_finance(limit: int = Query(20, ge=1, le=50)):
    """Get trending posts from Indian finance subreddits"""
    return await scraping_engine.reddit_india_finance(limit)


@router.get("/trends/india")
async def trends_india():
    """Get trending topics in India (via Google Trends)"""
    return await scraping_engine.twitter_trends_india()


# ── Unified Search ──

@router.get("/search")
async def unified_search(
    q: str = Query(..., description="Search query or stock symbol"),
    type: str = Query("all", description="Search type: all, news, finance, social, events"),
):
    """
    Unified search across all sources (SerpAPI-like).
    Returns combined results from Google Finance, News, Reddit, and Trends.
    """
    return await scraping_engine.unified_search(q, type)


# ── Available Stocks ──

@router.get("/stocks/list")
async def list_available_stocks():
    """List all trackable Indian and global stocks"""
    from app.services.scraping_engine import WebScrapingEngine
    stocks = []
    for symbol, exchange in WebScrapingEngine.INDIAN_STOCKS.items():
        market = "NSE" if ":NSE" in exchange else "BSE" if ":BSE" in exchange else "US"
        stocks.append({"symbol": symbol, "exchange": exchange, "market": market})
    return {"total": len(stocks), "stocks": stocks}
