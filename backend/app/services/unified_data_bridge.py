"""
Unified Data Bridge Service
===========================
Aggregates data from finance_api, news_platform, economy_platform
into a single unified API layer for the AARAMBH frontend.

Ports:
- finance_api: 8000
- news_platform: 8001
- economy_platform: 8002
- aarambh_backend: 5001
"""

import asyncio
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

# Data source URLs (Microservices managed natively by launcher)
FINANCE_API_URL = "http://127.0.0.1:8000"
NEWS_API_URL = "http://127.0.0.1:8001"
ECONOMY_API_URL = "http://127.0.0.1:8002"

# HTTP client with connection pooling
async def fetch_json(url: str, params: dict = None) -> Dict[str, Any]:
    """Fetch JSON from URL with error handling (scoped client for thread safety)"""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e), "success": False}


# ==================== FINANCE DATA ====================

async def get_stock_quote(ticker: str, exchange: str = "NASDAQ") -> Dict[str, Any]:
    """Get stock quote from Yahoo Finance (primary) + Google Finance (fallback)"""
    # Try Yahoo first (more complete data)
    yf_data = await fetch_json(f"{FINANCE_API_URL}/api/yahoo-finance/quote/{ticker}")
    
    if yf_data.get("error"):
        # Fallback to Google Finance
        gf_data = await fetch_json(f"{FINANCE_API_URL}/api/google-finance/quote/{ticker}/{exchange}")
        return gf_data
    
    return yf_data


async def get_stock_chart(ticker: str, interval: str = "1d", range: str = "1mo") -> Dict[str, Any]:
    """Get historical chart data"""
    return await fetch_json(
        f"{FINANCE_API_URL}/api/yahoo-finance/chart/{ticker}",
        params={"interval": interval, "range": range}
    )


async def get_stock_financials(ticker: str) -> Dict[str, Any]:
    """Get financial statements"""
    return await fetch_json(f"{FINANCE_API_URL}/api/yahoo-finance/financials/{ticker}")


async def get_stock_holders(ticker: str) -> Dict[str, Any]:
    """Get institutional and insider holders"""
    return await fetch_json(f"{FINANCE_API_URL}/api/yahoo-finance/holders/{ticker}")


async def get_market_movers(mover_type: str = "day_gainers", count: int = 25) -> Dict[str, Any]:
    """Get market movers (gainers, losers, most active)"""
    return await fetch_json(
        f"{FINANCE_API_URL}/api/yahoo-finance/movers",
        params={"type": mover_type, "count": count}
    )


async def get_market_indices() -> Dict[str, Any]:
    """Get global market indices"""
    return await fetch_json(f"{FINANCE_API_URL}/api/google-finance/market/indexes")


async def get_market_overview() -> Dict[str, Any]:
    """Get full market overview"""
    return await fetch_json(f"{FINANCE_API_URL}/api/google-finance/overview")


async def get_crypto_prices() -> Dict[str, Any]:
    """Get cryptocurrency prices"""
    return await fetch_json(f"{FINANCE_API_URL}/api/google-finance/market/crypto")


async def get_forex_rates() -> Dict[str, Any]:
    """Get forex/currency rates"""
    return await fetch_json(f"{FINANCE_API_URL}/api/google-finance/market/currencies")


async def get_trending_tickers(region: str = "US") -> Dict[str, Any]:
    """Get trending tickers"""
    return await fetch_json(f"{FINANCE_API_URL}/api/yahoo-finance/trending", params={"region": region})


async def search_stocks(query: str) -> Dict[str, Any]:
    """Search stocks across Yahoo and Google"""
    results = await asyncio.gather(
        fetch_json(f"{FINANCE_API_URL}/api/yahoo-finance/search", params={"q": query}),
        fetch_json(f"{FINANCE_API_URL}/api/google-finance/search", params={"q": query}),
        return_exceptions=True
    )
    return {
        "yahoo": results[0] if isinstance(results[0], dict) else {},
        "google": results[1] if isinstance(results[1], dict) else {},
        "query": query
    }


# ==================== NEWS DATA ====================

async def get_news_headlines(count: int = 50) -> Dict[str, Any]:
    """Get top news headlines"""
    return await fetch_json(f"{NEWS_API_URL}/api/news/headlines", params={"count": count})


async def get_finance_news(count: int = 50) -> Dict[str, Any]:
    """Get finance-specific news"""
    return await fetch_json(f"{NEWS_API_URL}/api/news/finance", params={"count": count})


async def get_news_by_category(category: str, count: int = 40) -> Dict[str, Any]:
    """Get news by category"""
    return await fetch_json(f"{NEWS_API_URL}/api/news/category/{category}", params={"count": count})


async def get_news_by_country(country: str, count: int = 40) -> Dict[str, Any]:
    """Get news by country code"""
    return await fetch_json(f"{NEWS_API_URL}/api/news/country/{country}", params={"count": count})


async def search_news(query: str, count: int = 30) -> Dict[str, Any]:
    """Search news across all sources"""
    return await fetch_json(f"{NEWS_API_URL}/api/news/search", params={"q": query, "count": count})


async def get_trending_topics() -> Dict[str, Any]:
    """Get trending news topics"""
    return await fetch_json(f"{NEWS_API_URL}/api/news/trending")


async def get_geopolitical_news() -> Dict[str, Any]:
    """Get geopolitical intelligence"""
    return await fetch_json(f"{NEWS_API_URL}/api/geo/conflicts")


async def get_health_news() -> Dict[str, Any]:
    """Get health news"""
    return await fetch_json(f"{NEWS_API_URL}/api/health/news")


async def get_live_tv_streams(country: str = None, category: str = None) -> Dict[str, Any]:
    """Get live TV streams"""
    if country:
        return await fetch_json(f"{NEWS_API_URL}/api/live-tv/country/{country}")
    elif category:
        return await fetch_json(f"{NEWS_API_URL}/api/live-tv/category/{category}")
    return await fetch_json(f"{NEWS_API_URL}/api/live-tv/all")


# ==================== ECONOMY DATA ====================

async def get_economic_calendar(country: str = "india") -> Dict[str, Any]:
    """Get economic calendar events"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/global/calendar", params={"country": country})


async def get_world_bank_data(country: str = "IN", indicator: str = "NY.GDP.MKTP.CD") -> Dict[str, Any]:
    """Get World Bank economic data"""
    return await fetch_json(
        f"{ECONOMY_API_URL}/api/global/world-bank",
        params={"country": country, "indicator": indicator}
    )


async def get_imf_data(indicator: str = "NGDPD", country: str = "IN") -> Dict[str, Any]:
    """Get IMF World Economic Outlook data"""
    return await fetch_json(
        f"{ECONOMY_API_URL}/api/global/imf",
        params={"indicator": indicator, "country": country}
    )


async def get_fred_data(series: str = "GDP", limit: int = 20) -> Dict[str, Any]:
    """Get FRED economic series"""
    return await fetch_json(
        f"{ECONOMY_API_URL}/api/global/fred",
        params={"series": series, "limit": limit}
    )


async def get_pib_latest() -> Dict[str, Any]:
    """Get latest PIB (Press Information Bureau) releases"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/pib/latest")


async def get_india_gdp() -> Dict[str, Any]:
    """Get India GDP data"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/india/indicator/gdp")


async def get_sector_data(sector: str) -> Dict[str, Any]:
    """Get data for a specific sector"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/sectors/{sector}")


async def get_ipo_calendar() -> Dict[str, Any]:
    """Get IPO calendar"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/global/ipo")


async def get_earnings_calendar(date: str = "") -> Dict[str, Any]:
    """Get earnings calendar"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/global/earnings", params={"date": date})


async def get_dividend_calendar(date: str = "") -> Dict[str, Any]:
    """Get dividend calendar"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/global/dividends", params={"date": date})


# ==================== AGGREGATED ENDPOINTS ====================

async def get_stock_overview(ticker: str) -> Dict[str, Any]:
    """
    Get complete stock overview - aggregates data from multiple sources
    Returns: quote, chart, financials, news, holders in one call
    """
    results = await asyncio.gather(
        get_stock_quote(ticker),
        get_stock_chart(ticker, "1d", "1mo"),
        get_stock_financials(ticker),
        get_stock_holders(ticker),
        search_news(f"{ticker} stock", 10),
        return_exceptions=True
    )
    
    return {
        "ticker": ticker,
        "quote": results[0] if isinstance(results[0], dict) else {},
        "chart": results[1] if isinstance(results[1], dict) else {},
        "financials": results[2] if isinstance(results[2], dict) else {},
        "holders": results[3] if isinstance(results[3], dict) else {},
        "news": results[4] if isinstance(results[4], dict) else {},
        "timestamp": datetime.utcnow().isoformat()
    }


async def get_market_dashboard() -> Dict[str, Any]:
    """
    Get complete market dashboard - indices, movers, crypto, forex, news
    """
    results = await asyncio.gather(
        get_market_indices(),
        get_market_movers("day_gainers", 10),
        get_market_movers("day_losers", 10),
        get_market_movers("most_actives", 10),
        get_crypto_prices(),
        get_forex_rates(),
        get_finance_news(20),
        get_trending_tickers(),
        return_exceptions=True
    )
    
    return {
        "indices": results[0] if isinstance(results[0], dict) else {},
        "gainers": results[1] if isinstance(results[1], dict) else {},
        "losers": results[2] if isinstance(results[2], dict) else {},
        "most_active": results[3] if isinstance(results[3], dict) else {},
        "crypto": results[4] if isinstance(results[4], dict) else {},
        "forex": results[5] if isinstance(results[5], dict) else {},
        "news": results[6] if isinstance(results[6], dict) else {},
        "trending": results[7] if isinstance(results[7], dict) else {},
        "timestamp": datetime.utcnow().isoformat()
    }


async def get_economy_dashboard() -> Dict[str, Any]:
    """
    Get complete economy dashboard - calendar, indicators, PIB, sectors
    """
    results = await asyncio.gather(
        get_economic_calendar(),
        get_world_bank_data(),
        get_imf_data(),
        get_pib_latest(),
        get_ipo_calendar(),
        get_earnings_calendar(),
        return_exceptions=True
    )
    
    return {
        "calendar": results[0] if isinstance(results[0], dict) else {},
        "world_bank": results[1] if isinstance(results[1], dict) else {},
        "imf": results[2] if isinstance(results[2], dict) else {},
        "pib": results[3] if isinstance(results[3], dict) else {},
        "ipo": results[4] if isinstance(results[4], dict) else {},
        "earnings": results[5] if isinstance(results[5], dict) else {},
        "timestamp": datetime.utcnow().isoformat()
    }


async def get_global_intelligence() -> Dict[str, Any]:
    """
    Get global intelligence - news, geopolitical, health, economy
    """
    results = await asyncio.gather(
        get_news_headlines(30),
        get_geopolitical_news(),
        get_health_news(),
        get_trending_topics(),
        get_economic_calendar(),
        return_exceptions=True
    )
    
    return {
        "headlines": results[0] if isinstance(results[0], dict) else {},
        "geopolitical": results[1] if isinstance(results[1], dict) else {},
        "health": results[2] if isinstance(results[2], dict) else {},
        "trending": results[3] if isinstance(results[3], dict) else {},
        "economy": results[4] if isinstance(results[4], dict) else {},
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== ADDITIONAL FINANCE ENDPOINTS ====================

async def get_stock_options(ticker: str, expiry_date: str = None) -> Dict[str, Any]:
    """Get stock options chain"""
    params = {"expiry_date": expiry_date} if expiry_date else {}
    return await fetch_json(f"{FINANCE_API_URL}/api/yahoo-finance/options/{ticker}", params=params)


async def get_stock_recommendations(ticker: str) -> Dict[str, Any]:
    """Get stock recommendations"""
    return await fetch_json(f"{FINANCE_API_URL}/api/yahoo-finance/recommendations/{ticker}")


async def get_stock_sparkline(tickers: str, range: str = "1d") -> Dict[str, Any]:
    """Get sparkline data for multiple tickers"""
    return await fetch_json(f"{FINANCE_API_URL}/api/yahoo-finance/sparkline",
                            params={"tickers": tickers, "range": range})


async def get_google_finance_chart(ticker: str, window: str = "1Y", exchange: str = "NASDAQ") -> Dict[str, Any]:
    """Get Google Finance chart data"""
    return await fetch_json(f"{FINANCE_API_URL}/api/google-finance/chart/{ticker}",
                            params={"exchange": exchange, "window": window})


async def get_google_finance_news(ticker: str) -> Dict[str, Any]:
    """Get Google Finance news for a ticker"""
    return await fetch_json(f"{FINANCE_API_URL}/api/google-finance/news/{ticker}")


async def get_google_ai_overview(query: str) -> Dict[str, Any]:
    """Get Google AI overview for any query"""
    return await fetch_json(f"{FINANCE_API_URL}/api/google-ai/overview", params={"q": query})


async def get_google_ai_finance_summary(ticker: str) -> Dict[str, Any]:
    """Get Google AI finance summary for a ticker"""
    return await fetch_json(f"{FINANCE_API_URL}/api/google-ai/finance-summary/{ticker}")


async def get_google_news_search(query: str, count: int = 20) -> Dict[str, Any]:
    """Search Google News"""
    return await fetch_json(f"{FINANCE_API_URL}/api/google-news/search",
                            params={"q": query, "count": count})


async def get_google_news_topic(topic: str, count: int = 30) -> Dict[str, Any]:
    """Get Google News by topic"""
    return await fetch_json(f"{FINANCE_API_URL}/api/google-news/topic/{topic}",
                            params={"count": count})


async def get_google_news_headlines(country: str = "US", count: int = 30) -> Dict[str, Any]:
    """Get Google News headlines"""
    return await fetch_json(f"{FINANCE_API_URL}/api/google-news/headlines",
                            params={"country": country, "count": count})


# ==================== ADDITIONAL NEWS ENDPOINTS ====================

async def get_news_sources() -> Dict[str, Any]:
    """Get all news sources metadata"""
    return await fetch_json(f"{NEWS_API_URL}/api/news/sources")


async def get_news_aggregate(sources: str, count: int = 40) -> Dict[str, Any]:
    """Aggregate news from multiple specified sources"""
    return await fetch_json(f"{NEWS_API_URL}/api/news/aggregate",
                            params={"sources": sources, "count": count})


async def get_live_tv_all(category: str = None, country: str = None) -> Dict[str, Any]:
    """Get all live TV channels"""
    params = {}
    if category: params["category"] = category
    if country: params["country"] = country
    return await fetch_json(f"{NEWS_API_URL}/api/live-tv/all", params=params)


async def get_live_tv_finance() -> Dict[str, Any]:
    """Get finance live TV channels"""
    return await fetch_json(f"{NEWS_API_URL}/api/live-tv/finance")


async def get_live_tv_directory() -> Dict[str, Any]:
    """Get live TV channel directory"""
    return await fetch_json(f"{NEWS_API_URL}/api/live-tv/directory")


async def get_who_alerts() -> Dict[str, Any]:
    """Get WHO health alerts"""
    return await fetch_json(f"{NEWS_API_URL}/api/health/who-alerts")


async def get_geo_sanctions() -> Dict[str, Any]:
    """Get sanctions and trade news"""
    return await fetch_json(f"{NEWS_API_URL}/api/geo/sanctions")


async def get_geo_elections() -> Dict[str, Any]:
    """Get election news"""
    return await fetch_json(f"{NEWS_API_URL}/api/geo/elections")


async def get_geo_tensions() -> Dict[str, Any]:
    """Get geopolitical tensions"""
    return await fetch_json(f"{NEWS_API_URL}/api/geo/tensions")


async def get_geo_risk_map() -> Dict[str, Any]:
    """Get geopolitical risk map"""
    return await fetch_json(f"{NEWS_API_URL}/api/geo/risk-map")


async def get_geo_country(country: str) -> Dict[str, Any]:
    """Get geopolitical news for a specific country"""
    return await fetch_json(f"{NEWS_API_URL}/api/geo/country/{country}")


async def get_ai_briefing() -> Dict[str, Any]:
    """Get AI-powered daily news briefing"""
    return await fetch_json(f"{NEWS_API_URL}/api/ai/briefing")


async def get_ai_sentiment(topic: str) -> Dict[str, Any]:
    """Get AI sentiment analysis for a topic"""
    return await fetch_json(f"{NEWS_API_URL}/api/ai/sentiment", params={"topic": topic})


async def get_ai_trends() -> Dict[str, Any]:
    """Get AI-powered trend analysis"""
    return await fetch_json(f"{NEWS_API_URL}/api/ai/trends")


# ==================== ADDITIONAL ECONOMY ENDPOINTS ====================

async def get_pib_search(query: str, count: int = 20) -> Dict[str, Any]:
    """Search PIB releases"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/pib/search", params={"q": query, "count": count})


async def get_pib_ministry(ministry: str, count: int = 20) -> Dict[str, Any]:
    """Get PIB releases by ministry"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/pib/ministry/{ministry}", params={"count": count})


async def get_rbi_feed(feed: str = "press_releases") -> Dict[str, Any]:
    """Get RBI feed (press_releases|circulars|notifications|publications|speeches)"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/india/rbi/{feed}")


async def get_rbi_rates() -> Dict[str, Any]:
    """Get current RBI key rates"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/india/rbi-rates")


async def get_sebi_feed(feed: str = "circulars") -> Dict[str, Any]:
    """Get SEBI feed (circulars|press_releases|orders|notices)"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/india/sebi/{feed}")


async def get_india_indicator(name: str) -> Dict[str, Any]:
    """Get India indicator (gdp|inflation|unemployment|exports|imports|fdi|poverty|forex_reserves)"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/india/indicator/{name}")


async def get_mospi_data(indicator: str = "gdp") -> Dict[str, Any]:
    """Get MoSPI data (gdp|cpi|iip|nso)"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/mospi/{indicator}")


async def get_mospi_releases() -> Dict[str, Any]:
    """Get MoSPI releases"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/mospi/releases")


async def get_india_schemes_search(query: str = "", category: str = "") -> Dict[str, Any]:
    """Search Indian government schemes"""
    params = {}
    if query: params["q"] = query
    if category: params["category"] = category
    return await fetch_json(f"{ECONOMY_API_URL}/api/india/schemes/search", params=params)


async def get_ndap_datasets(query: str = "", sector: str = "") -> Dict[str, Any]:
    """Search NDAP datasets"""
    params = {}
    if query: params["q"] = query
    if sector: params["sector"] = sector
    return await fetch_json(f"{ECONOMY_API_URL}/api/ndap/datasets", params=params)


async def get_sectors_list() -> Dict[str, Any]:
    """Get all 31 economy sectors"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/sectors/list")


async def get_world_bank_profile(country: str = "IN") -> Dict[str, Any]:
    """Get World Bank country profile"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/global/world-bank/profile/{country}")


async def get_world_bank_indicators() -> Dict[str, Any]:
    """Get all World Bank indicators"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/global/world-bank/indicators")


async def get_fred_indicators() -> Dict[str, Any]:
    """Get all FRED indicators"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/global/fred/indicators")


async def get_india_vs_world(indicator: str = "gdp") -> Dict[str, Any]:
    """Compare India with other countries"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/global/india-vs-world/{indicator}")


async def get_oecd_data(dataset: str = "MEI", country: str = "IND") -> Dict[str, Any]:
    """Get OECD data"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/global/oecd",
                            params={"dataset": dataset, "country": country})


async def parse_document(url: str) -> Dict[str, Any]:
    """Parse a document (PDF, XLSX, CSV, etc.) by URL"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/docs/parse", params={"url": url})


async def get_economy_ai_briefing() -> Dict[str, Any]:
    """Get AI economy briefing"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/ai/briefing")


async def get_economy_ai_summarize(topic: str) -> Dict[str, Any]:
    """Get AI summary for an economy topic"""
    return await fetch_json(f"{ECONOMY_API_URL}/api/ai/summarize", params={"topic": topic})


# ==================== HEALTH CHECK ====================

async def check_data_sources() -> Dict[str, Any]:
    """Check health of all data source APIs"""
    results = await asyncio.gather(
        fetch_json(f"{FINANCE_API_URL}/health"),
        fetch_json(f"{NEWS_API_URL}/health"),
        fetch_json(f"{ECONOMY_API_URL}/health"),
        return_exceptions=True
    )
    
    return {
        "finance_api": {
            "url": FINANCE_API_URL,
            "status": "ok" if isinstance(results[0], dict) and results[0].get("status") == "ok" else "error"
        },
        "news_platform": {
            "url": NEWS_API_URL,
            "status": "ok" if isinstance(results[1], dict) and results[1].get("status") == "ok" else "error"
        },
        "economy_platform": {
            "url": ECONOMY_API_URL,
            "status": "ok" if isinstance(results[2], dict) and results[2].get("status") == "ok" else "error"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# Export all functions
__all__ = [
    # Finance (core)
    'get_stock_quote', 'get_stock_chart', 'get_stock_financials', 'get_stock_holders',
    'get_market_movers', 'get_market_indices', 'get_market_overview', 'get_crypto_prices',
    'get_forex_rates', 'get_trending_tickers', 'search_stocks', 'get_stock_overview',
    # Finance (extended)
    'get_stock_options', 'get_stock_recommendations', 'get_stock_sparkline',
    'get_google_finance_chart', 'get_google_finance_news',
    'get_google_ai_overview', 'get_google_ai_finance_summary',
    'get_google_news_search', 'get_google_news_topic', 'get_google_news_headlines',

    # News (core)
    'get_news_headlines', 'get_finance_news', 'get_news_by_category', 'get_news_by_country',
    'search_news', 'get_trending_topics', 'get_geopolitical_news', 'get_health_news',
    'get_live_tv_streams',
    # News (extended)
    'get_news_sources', 'get_news_aggregate',
    'get_live_tv_all', 'get_live_tv_finance', 'get_live_tv_directory',
    'get_who_alerts', 'get_geo_sanctions', 'get_geo_elections', 'get_geo_tensions',
    'get_geo_risk_map', 'get_geo_country',
    'get_ai_briefing', 'get_ai_sentiment', 'get_ai_trends',

    # Economy (core)
    'get_economic_calendar', 'get_world_bank_data', 'get_imf_data', 'get_fred_data',
    'get_pib_latest', 'get_india_gdp', 'get_sector_data', 'get_ipo_calendar',
    'get_earnings_calendar', 'get_dividend_calendar',
    # Economy (extended)
    'get_pib_search', 'get_pib_ministry', 'get_rbi_feed', 'get_rbi_rates', 'get_sebi_feed',
    'get_india_indicator', 'get_mospi_data', 'get_mospi_releases',
    'get_india_schemes_search', 'get_ndap_datasets', 'get_sectors_list',
    'get_world_bank_profile', 'get_world_bank_indicators', 'get_fred_indicators',
    'get_india_vs_world', 'get_oecd_data', 'parse_document',
    'get_economy_ai_briefing', 'get_economy_ai_summarize',

    # Aggregated
    'get_market_dashboard', 'get_economy_dashboard', 'get_global_intelligence',

    # Health
    'check_data_sources'
]
