"""
Unified Finance & News API  —  v3.0
=====================================
Combined API from finance_api (port 8000) + news_platform (port 8001)
ONLY includes WORKING endpoints verified by test results.

Run:
  pip install -r requirements.txt
  python main.py  →  http://localhost:8000/docs

Working APIs (verified from test_results/):
───────────────────────────────────────────
FINANCE (Port 8000):
  ✓ Google Finance: ALL endpoints (quotes, markets, search, charts, news)
  ✓ Yahoo Finance: quotes (most), charts (some), search, trending US, movers
  ✓ Google News: ALL endpoints
  ✓ Google AI: ALL endpoints (overview, finance-summary)

NEWS PLATFORM (Port 8001):
  ✓ News: headlines, search, categories, country, sources, finance, trending
  ✓ Live TV: all channels, finance, country, search, stream
  ✓ Health: news, filter, subcategories (no WHO/CDC/country-specific)
  ✓ Geo: conflicts, sanctions, elections, tensions, country, risk-map
  ✓ AI: setup, summarize, sentiment, compare, trends (no briefing)

Filtered OUT (broken/empty):
  ✗ Yahoo: financials, holders, options, trending IN, some charts
  ✗ Health: WHO alerts, CDC updates, country-specific
  ✗ Geo: GDELT endpoints, treaties
  ✗ AI: briefing (timeout)
"""

from dotenv import load_dotenv
load_dotenv()

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import routers

app = FastAPI(
    title="Unified Finance & News API",
    description="Combined working APIs from finance_api + news_platform. Only verified working endpoints.",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers dynamically — skips any that failed to import
_ROUTER_MAP = [
    ("gf_market",       "/api/finance/google",   "Finance - Google"),
    ("yf_market",       "/api/finance/yahoo",    "Finance - Yahoo"),
    ("unified_finance", "/api/finance/unified",  "Finance - Unified"),
    ("gn_feed",         "/api/news/google",      "News - Google"),
    ("gai_intel",       "/api/ai/google",        "AI - Google"),
    ("news_feed",       "/api/news/platform",    "News - Platform"),
    ("live_tv",         "/api/tv",               "Live TV"),
    ("health_intel",    "/api/health",           "Health"),
    ("geo_intel",       "/api/geo",              "Geopolitical"),
    ("ai_analysis",     "/api/ai/analysis",      "AI Analysis"),
]

_loaded = []
for _name, _prefix, _tag in _ROUTER_MAP:
    _mod = getattr(routers, _name, None)
    if _mod and hasattr(_mod, "router"):
        app.include_router(_mod.router, prefix=_prefix, tags=[_tag])
        _loaded.append(_name)
    else:
        print(f"[main] Router '{_name}' not available, skipping")

print(f"[main] Loaded {len(_loaded)} routers: {', '.join(_loaded)}")


@app.get("/", tags=["Root"])
def root():
    return {
        "status": "running",
        "version": "3.0.0",
        "description": "Unified Finance & News API - Only Working Endpoints",
        "docs": "http://localhost:8000/docs",
        "apis": {
            "finance": {
                "google": "/api/finance/google",
                "yahoo": "/api/finance/yahoo",
            },
            "news": {
                "google": "/api/news/google",
                "platform": "/api/news/platform",
            },
            "tv": "/api/tv",
            "health": "/api/health",
            "geo": "/api/geo",
            "ai": {
                "google": "/api/ai/google",
                "analysis": "/api/ai/analysis",
            },
        },
        "quick_start": {
            "apple_quote": "/api/finance/google/quote/AAPL/NASDAQ",
            "market_gainers": "/api/finance/google/market/gainers",
            "market_losers": "/api/finance/google/market/losers",
            "top_headlines": "/api/news/platform/headlines",
            "finance_news": "/api/news/platform/category/finance",
            "live_tv": "/api/tv/all",
            "geo_conflicts": "/api/geo/conflicts",
            "ai_summary": "/api/ai/analysis/summarize?topic=markets",
        },
    }


@app.get("/health", tags=["Root"])
def health():
    return {"status": "ok"}


@app.get("/api/site-index", tags=["Root"])
def site_index():
    """Complete working API index - only verified endpoints."""
    return {
        "version": "3.0.0",
        "note": "ONLY working endpoints from test results",
        "finance_google": {
            "GET /api/finance/google/quote/{ticker}/{exchange}": "Stock quote with stats & news",
            "GET /api/finance/google/quote/{ticker}": "Quote with default exchange",
            "GET /api/finance/google/multi-quote": "Multiple quotes",
            "GET /api/finance/google/market/indexes": "Global market indexes",
            "GET /api/finance/google/market/gainers": "Top gaining stocks",
            "GET /api/finance/google/market/losers": "Top losing stocks",
            "GET /api/finance/google/market/most-active": "Most active stocks",
            "GET /api/finance/google/market/crypto": "Crypto prices",
            "GET /api/finance/google/market/currencies": "Forex rates",
            "GET /api/finance/google/market/futures": "Futures",
            "GET /api/finance/google/market/etfs": "ETFs",
            "GET /api/finance/google/overview": "Full market overview",
            "GET /api/finance/google/search": "Search stocks",
            "GET /api/finance/google/chart/{ticker}": "Historical charts",
            "GET /api/finance/google/news/{ticker}": "Stock news",
        },
        "finance_yahoo": {
            "GET /api/finance/yahoo/quote/{ticker}": "Stock quote (TSLA, NVDA, MSFT, RELIANCE.NS work)",
            "GET /api/finance/yahoo/chart/{ticker}": "Chart data (1d, 1wk intervals work)",
            "GET /api/finance/yahoo/search": "Search tickers",
            "GET /api/finance/yahoo/trending": "Trending stocks (US only)",
            "GET /api/finance/yahoo/movers": "Market movers",
            "GET /api/finance/yahoo/recommendations/{ticker}": "Related stocks",
            "GET /api/finance/yahoo/sparkline": "Mini price charts",
            "NOTE": "Financials, holders, options, AAPL quote, trending IN are BROKEN",
        },
        "news_google": {
            "GET /api/news/google/search": "Search news",
            "GET /api/news/google/topic/{topic}": "Topics: business|tech|finance|world",
            "GET /api/news/google/ticker/{ticker}": "News for ticker",
            "GET /api/news/google/headlines": "Top headlines",
            "GET /api/news/google/company/{name}": "Company news",
        },
        "news_platform": {
            "GET /api/news/platform/headlines": "Top headlines",
            "GET /api/news/platform/search": "Search news",
            "GET /api/news/platform/category/{cat}": "Categories: finance|world|health|tech|geo",
            "GET /api/news/platform/country/{code}": "Country news: IN|US|GB",
            "GET /api/news/platform/source/{name}": "Source: bbc|bloomberg|et_markets",
            "GET /api/news/platform/finance": "Finance news",
            "GET /api/news/platform/trending": "Trending topics",
            "GET /api/news/platform/sources": "List all sources",
        },
        "live_tv": {
            "GET /api/tv/all": "All channels",
            "GET /api/tv/finance": "Finance channels",
            "GET /api/tv/country/{code}": "By country: IN|US|GB",
            "GET /api/tv/category/{cat}": "Categories: news|world",
            "GET /api/tv/search": "Search channels",
            "GET /api/tv/stream/{channel}": "Stream embed: bloomberg|cnbc|wion",
        },
        "health": {
            "GET /api/health/news": "Health news",
            "GET /api/health/filter": "Filter by keyword",
            "GET /api/health/subcategory/{sub}": "Subcategories: infectious|mental|cancer",
            "GET /api/health/categories": "List categories",
            "NOTE": "WHO alerts, CDC updates, country-specific are BROKEN",
        },
        "geopolitical": {
            "GET /api/geo/conflicts": "Active conflicts",
            "GET /api/geo/sanctions": "Sanctions news",
            "GET /api/geo/elections": "Election news",
            "GET /api/geo/tensions": "Rising tensions",
            "GET /api/geo/country/{code}": "By country: RU|CN|IN",
            "GET /api/geo/risk-map": "Risk map data",
            "GET /api/geo/all": "All geo news",
            "NOTE": "GDELT endpoints, treaties are BROKEN",
        },
        "ai_google": {
            "GET /api/ai/google/overview": "AI overview search",
            "GET /api/ai/google/finance-summary/{ticker}": "Finance summary",
        },
        "ai_analysis": {
            "GET /api/ai/analysis/setup": "AI setup status",
            "GET /api/ai/analysis/summarize": "Summarize topic",
            "GET /api/ai/analysis/sentiment": "Sentiment analysis",
            "GET /api/ai/analysis/compare": "Compare topics",
            "GET /api/ai/analysis/trends": "Trending themes",
            "NOTE": "Briefing endpoint is BROKEN (timeout)",
        },
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
