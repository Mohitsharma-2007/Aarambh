"""Debug endpoints - API health checks, log viewing, source testing"""
from fastapi import APIRouter, HTTPException
from loguru import logger
from datetime import datetime
import httpx
import asyncio

from app.config import settings

router = APIRouter()

# In-memory log buffer
_log_buffer = []
_MAX_LOGS = 500


def _add_log(level: str, source: str, message: str, details: dict = None):
    entry = {"timestamp": datetime.utcnow().isoformat(), "level": level, "source": source,
             "message": message, "details": details or {}}
    _log_buffer.append(entry)
    if len(_log_buffer) > _MAX_LOGS:
        _log_buffer.pop(0)


@router.get("/health/detailed")
async def detailed_health():
    """Comprehensive health check of all services"""
    results = {"timestamp": datetime.utcnow().isoformat(), "services": {}}

    # Database
    try:
        from app.database import async_session, Event
        from sqlalchemy import select, func
        async with async_session() as session:
            count = await session.scalar(select(func.count()).select_from(Event))
            results["services"]["database"] = {"status": "healthy", "events": count}
    except Exception as e:
        results["services"]["database"] = {"status": "error", "error": str(e)}

    # FRED API
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("https://api.stlouisfed.org/fred/series/observations",
                params={"series_id": "DGS10", "api_key": settings.fred_api_key,
                        "file_type": "json", "limit": 1, "sort_order": "desc"})
            results["services"]["fred"] = {"status": "healthy" if resp.status_code == 200 else "error",
                                           "configured": bool(settings.fred_api_key)}
    except Exception as e:
        results["services"]["fred"] = {"status": "error", "error": str(e)}

    # yfinance
    try:
        import yfinance as yf
        t = yf.Ticker("AAPL")
        price = t.fast_info.last_price
        results["services"]["yfinance"] = {"status": "healthy", "test_price": round(float(price), 2)}
    except Exception as e:
        results["services"]["yfinance"] = {"status": "error", "error": str(e)}

    # NewsAPI
    if settings.newsapi_key:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get("https://newsapi.org/v2/top-headlines",
                    params={"apiKey": settings.newsapi_key, "country": "us", "pageSize": 1})
                results["services"]["newsapi"] = {"status": "healthy" if resp.status_code == 200 else "error"}
        except Exception as e:
            results["services"]["newsapi"] = {"status": "error", "error": str(e)}
    else:
        results["services"]["newsapi"] = {"status": "not_configured"}

    # Tavily
    if settings.tavily_api_key:
        results["services"]["tavily"] = {"status": "configured", "configured": True}
    else:
        results["services"]["tavily"] = {"status": "not_configured"}

    # Alpha Vantage
    results["services"]["alpha_vantage"] = {"status": "configured" if settings.alpha_vantage_api_key else "not_configured"}

    # CoinGecko (free, no key)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("https://api.coingecko.com/api/v3/ping")
            results["services"]["coingecko"] = {"status": "healthy" if resp.status_code == 200 else "error"}
    except Exception as e:
        results["services"]["coingecko"] = {"status": "error", "error": str(e)}

    # World Bank (free, no key)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("https://api.worldbank.org/v2/country/USA/indicator/NY.GDP.MKTP.CD?format=json&per_page=1")
            results["services"]["world_bank"] = {"status": "healthy" if resp.status_code == 200 else "error"}
    except Exception as e:
        results["services"]["world_bank"] = {"status": "error", "error": str(e)}

    return results


@router.get("/logs")
async def get_logs(limit: int = 100, level: str = None):
    """Get recent log entries"""
    logs = _log_buffer[-limit:]
    if level:
        logs = [l for l in logs if l["level"] == level.upper()]
    return {"logs": logs, "total": len(_log_buffer)}


@router.get("/api-status")
async def get_api_status():
    """Test each external API and report status"""
    apis = [
        {"name": "FRED", "url": "https://api.stlouisfed.org/fred/series?series_id=DGS10&api_key=" + (settings.fred_api_key or "demo") + "&file_type=json", "requires_key": True, "has_key": bool(settings.fred_api_key)},
        {"name": "World Bank", "url": "https://api.worldbank.org/v2/country/USA?format=json", "requires_key": False, "has_key": True},
        {"name": "CoinGecko", "url": "https://api.coingecko.com/api/v3/ping", "requires_key": False, "has_key": True},
        {"name": "GDELT", "url": "https://api.gdeltproject.org/api/v2/doc/doc?query=india&mode=artlist&maxrecords=1&format=json", "requires_key": False, "has_key": True},
        {"name": "USGS Earthquake", "url": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson", "requires_key": False, "has_key": True},
        {"name": "Hacker News", "url": "https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty&limitToFirst=1&orderBy=%22$key%22", "requires_key": False, "has_key": True},
        {"name": "SEC EDGAR", "url": "https://efts.sec.gov/LATEST/search-index?q=13F&dateRange=custom&forms=13F-HR", "requires_key": False, "has_key": True},
        {"name": "Congress Trades (House)", "url": "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json", "requires_key": False, "has_key": True},
    ]

    results = []
    async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "AARAMBH/2.0"}) as client:
        for api in apis:
            try:
                start = datetime.now()
                resp = await client.get(api["url"])
                elapsed = (datetime.now() - start).total_seconds()
                results.append({
                    "name": api["name"], "status": "healthy" if resp.status_code == 200 else f"error:{resp.status_code}",
                    "response_time_ms": round(elapsed * 1000), "requires_key": api["requires_key"],
                    "has_key": api["has_key"],
                })
                _add_log("INFO", api["name"], f"API test: {resp.status_code} in {elapsed:.1f}s")
            except Exception as e:
                results.append({
                    "name": api["name"], "status": "error", "error": str(e),
                    "requires_key": api["requires_key"], "has_key": api["has_key"],
                })
                _add_log("ERROR", api["name"], f"API test failed: {e}")

    return {"apis": results, "timestamp": datetime.utcnow().isoformat()}


@router.post("/test-source/{source_name}")
async def test_source(source_name: str):
    """Test a specific data source and return detailed results"""
    from app.services.ingestion_service import ingestion_service

    _add_log("INFO", "debug", f"Testing source: {source_name}")

    try:
        result = await ingestion_service.fetch_single_source(source_name)
        _add_log("INFO", source_name, f"Source test success: {result}")
        return {"source": source_name, "status": "success", "result": result}
    except Exception as e:
        _add_log("ERROR", source_name, f"Source test failed: {e}")
        return {"source": source_name, "status": "error", "error": str(e)}
