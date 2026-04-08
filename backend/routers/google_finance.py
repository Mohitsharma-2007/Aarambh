"""routers/google_finance.py"""
from fastapi import APIRouter, Query, Path
from fastapi.responses import JSONResponse
from scrapers import google_finance as gf
from scrapers.universal_finance import get_quote_universal, get_market_universal
from utils.background_tasks import background_manager
from typing import Optional, List
from datetime import datetime

router = APIRouter()

# ─── Quote endpoints ──────────────────────────────────────────────────────────

@router.get(
    "/quote/{ticker}/{exchange}",
    summary="Stock quote with full data",
    description="""
Fetch a complete stock quote from Google Finance.

**Uses 5 independent extraction strategies** — if one fails, the next runs automatically.

**Exchange examples:**
- US stocks: `NASDAQ`, `NYSE`, `NYSEARCA`, `NYSEAMERICAN`
- India: `NSE`, `BSE`
- UK: `LON`
- Germany: `FRA`
- Japan: `TYO`
- Hong Kong: `HKG`

**Returns:** price, change, change%, prev_close, after_hours, key stats, about, news
""",
)
async def quote(
    ticker:   str = Path(..., description="Stock symbol e.g. AAPL, RELIANCE, TSLA"),
    exchange: str = Path(..., description="Exchange e.g. NASDAQ, NSE, NYSE"),
):
    # Try to get from cache first
    cached_data = background_manager.get_quote_data(ticker, exchange)
    if cached_data and cached_data.get("price") and cached_data.get("price") != "0.00":
        return cached_data
    
    # If no cache or invalid data, fetch fresh data
    try:
        result = await get_quote_universal(ticker, exchange)
        return result
    except Exception as e:
        # Return cached data even if old, or fallback
        if cached_data:
            return cached_data
        
        # Final fallback
        return {
            "ticker": ticker,
            "exchange": exchange,
            "company_name": ticker,
            "price": "0.00",
            "change": "0.00",
            "change_percent": "0.00%",
            "currency": "USD" if exchange != "NSE" else "INR",
            "source": "emergency_fallback",
            "error": str(e)
        }


@router.get(
    "/quote/{ticker}",
    summary="Stock quote (NASDAQ default)",
    description="Fetch a stock quote, defaulting exchange to NASDAQ.",
)
async def quote_default(
    ticker: str = Path(..., description="Stock symbol e.g. AAPL, MSFT, GOOGL"),
    exchange: str = Query("NASDAQ", description="Override exchange"),
):
    # Try to get from cache first
    cached_data = background_manager.get_quote_data(ticker, exchange)
    if cached_data and cached_data.get("price") and cached_data.get("price") != "0.00":
        return cached_data
    
    # If no cache or invalid data, fetch fresh data
    try:
        result = await get_quote_universal(ticker, exchange)
        return result
    except Exception as e:
        # Return cached data even if old, or fallback
        if cached_data:
            return cached_data
        
        # Final fallback
        return {
            "ticker": ticker,
            "exchange": exchange,
            "company_name": ticker,
            "price": "0.00",
            "change": "0.00",
            "change_percent": "0.00%",
            "currency": "USD" if exchange != "NSE" else "INR",
            "source": "emergency_fallback",
            "error": str(e)
        }


@router.get(
    "/multi-quote",
    summary="Multiple quotes at once",
    description="Fetch quotes for up to 10 tickers in one request.",
)
async def multi_quote(
    tickers:  str = Query(..., description="Comma-separated tickers e.g. AAPL,MSFT,GOOGL"),
    exchange: str = Query("NASDAQ", description="Exchange for all tickers"),
):
    ticker_list = [t.strip() for t in tickers.split(",") if t.strip()][:10]
    return await gf.get_multi_quote(ticker_list, exchange)


# ─── Market section endpoints ─────────────────────────────────────────────────

@router.get(
    "/market/{section}",
    summary="Market section (indexes, gainers, losers etc.)",
    description="""
Fetch a market section from Google Finance.

**Available sections:**
| Section | Description |
|---|---|
| `indexes` | Global indexes — S&P 500, NIFTY 50, DAX, Nikkei |
| `most-active` | Most traded stocks today |
| `gainers` | Top gaining stocks today |
| `losers` | Top losing stocks today |
| `crypto` | Cryptocurrency prices |
| `currencies` | Forex / currency pairs |
| `futures` | Futures market |
| `etfs` | Exchange-traded funds |
""",
)
async def market(
    section: str = Path(..., description="indexes | most-active | gainers | losers | crypto | currencies | futures | etfs | nse-gainers | nse-losers | nse-active"),
):
    # Try to get from cache first
    cached_data = background_manager.get_market_data(section)
    if cached_data and cached_data.get("items") and len(cached_data["items"]) > 0:
        return cached_data
    
    # If no cache or empty data, fetch fresh data
    try:
        result = await get_market_universal(section)
        return result
    except Exception as e:
        # Return cached data even if old, or fallback
        if cached_data:
            return cached_data
        
        # Final fallback
        return {
            "section": section,
            "title": section.replace("-", " ").title(),
            "count": 0,
            "items": [],
            "source": "emergency_fallback",
            "error": str(e)
        }


@router.get(
    "/cache-status",
    summary="Cache status and health",
    description="Get current cache status and background task health.",
)
async def cache_status():
    """Get cache status and background task information"""
    try:
        status = background_manager.get_cache_status()
        return {
            "status": "healthy",
            "background_tasks_running": status["running"],
            "cached_items": status["total_cached_items"],
            "last_updates": status["last_updates"],
            "cache_keys": status["cache_keys"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ─── Overview ─────────────────────────────────────────────────────────────────

@router.get(
    "/overview",
    summary="Full Google Finance homepage",
    description="All market sections from the Google Finance homepage in one call.",
)
async def overview():
    return await gf.get_overview()


# ─── Search ───────────────────────────────────────────────────────────────────

@router.get(
    "/search",
    summary="Search stocks / ETFs / crypto",
    description="Search Google Finance for any stock, ETF, index, or cryptocurrency.",
)
async def search(
    q: str = Query(..., description="Search query — company name, ticker, or keyword"),
):
    return await gf.search_gf(q)


# ─── Chart data ───────────────────────────────────────────────────────────────

@router.get(
    "/chart/{ticker}",
    summary="Historical price chart data",
    description="""
Fetch historical chart data for a stock from Google Finance.

**Window options:** `1D` | `5D` | `1M` | `6M` | `YTD` | `1Y` | `5Y` | `MAX`
""",
)
async def chart(
    ticker:   str = Path(..., description="Stock symbol"),
    exchange: str = Query("NASDAQ"),
    window:   str = Query("1Y", description="1D | 5D | 1M | 6M | YTD | 1Y | 5Y | MAX"),
):
    return await gf.get_chart(ticker, exchange, window)


# ─── News ─────────────────────────────────────────────────────────────────────

@router.get(
    "/news/{ticker}",
    summary="News articles for a ticker",
    description="News articles shown on the Google Finance quote page for this ticker.",
)
async def news(
    ticker:   str = Path(...),
    exchange: str = Query("NASDAQ"),
):
    data = await gf.get_quote(ticker, exchange)
    return {
        "ticker":   ticker,
        "exchange": exchange,
        "count":    len(data.get("news", [])),
        "news":     data.get("news", []),
    }


# ─── Site map ─────────────────────────────────────────────────────────────────

@router.get(
    "/site-map",
    summary="All Google Finance URL patterns, ports, and request details",
)
async def site_map():
    return {
        "host":     "www.google.com",
        "port":     443,
        "protocol": "HTTPS / TLS 1.3",
        "http":     "HTTP/2 (falls back to HTTP/1.1)",
        "base_path":"/finance",
        "endpoints": [
            {
                "path":    "/finance",
                "method":  "GET",
                "params":  {"hl": "en"},
                "returns": "Market overview — indexes, watchlists, news sections",
            },
            {
                "path":    "/finance/quote/{TICKER}:{EXCHANGE}",
                "example": "/finance/quote/AAPL:NASDAQ",
                "method":  "GET",
                "params":  {"hl": "en", "window": "1D|5D|1M|6M|YTD|1Y|5Y|MAX"},
                "returns": "Price, change, market cap, key stats, about, news, chart data",
            },
            {
                "path":    "/finance/markets/indexes",
                "method":  "GET",
                "returns": "Major global indexes (S&P 500, Nifty, DAX…)",
            },
            {
                "path":    "/finance/markets/most-active",  "returns": "Most actively traded",
            },
            {
                "path":    "/finance/markets/gainers",      "returns": "Top gaining stocks",
            },
            {
                "path":    "/finance/markets/losers",       "returns": "Top losing stocks",
            },
            {
                "path":    "/finance/markets/crypto",       "returns": "Crypto prices",
            },
            {
                "path":    "/finance/markets/currencies",   "returns": "Forex rates",
            },
            {
                "path":    "/finance/markets/futures",      "returns": "Futures market",
            },
            {
                "path":    "/finance/markets/etfs",         "returns": "ETF list",
            },
        ],
        "extraction_strategies": {
            "S1": "data-* HTML attributes  (most reliable)",
            "S2": "AF_initDataCallback JSON blobs in <script> tags",
            "S3": "JSON-LD structured data (<script type='application/ld+json'>)",
            "S4": "CSS class selectors (30+ known variant classes)",
            "S5": "Regex text mining (last resort — always returns something)",
        },
        "request_headers": {
            "User-Agent":            "Rotating pool of 6 real browser UAs",
            "Accept":                "text/html,application/xhtml+xml,application/xml",
            "Accept-Language":       "en-US,en;q=0.9",
            "Sec-Fetch-Dest":        "document",
            "Sec-Fetch-Mode":        "navigate",
            "Sec-CH-UA":             "Chrome 124 header",
            "DNT":                   "1",
        },
        "rate_limiting":  "1.5 req/sec per domain (token bucket)",
        "retry_strategy": "Exponential backoff: 2^attempt + jitter on 429/503",
        "cache_ttl": {
            "quote":  "60 seconds",
            "market": "120 seconds",
            "search": "300 seconds",
            "chart":  "300 seconds",
        },
    }
