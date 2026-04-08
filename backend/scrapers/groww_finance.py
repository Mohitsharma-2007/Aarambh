"""
Groww Finance API Scraper — Primary data source for Indian market stocks.

Uses JWT Bearer token authentication.
Endpoints are reverse-engineered (no public docs), use carefully.
"""

import os
import httpx
from typing import Optional

GROWW_TOKEN = os.getenv("GROWW_API_KEY", "")
GROWW_BASE = "https://groww.in/v1/api"

_HEADERS = {
    "Authorization": f"Bearer {GROWW_TOKEN}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://groww.in",
    "Referer": "https://groww.in/",
}


async def _fetch(url: str, params: dict = None, timeout: float = 10.0):
    """HTTP GET with Groww auth headers."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url, params=params, headers=_HEADERS)
            if r.status_code == 200:
                return r.json()
            return {"error": f"HTTP {r.status_code}", "url": url}
    except Exception as e:
        return {"error": str(e), "url": url}


async def get_quote(symbol: str, exchange: str = "NSE"):
    """
    Get stock quote from Groww.
    Works best with Indian symbols like RELIANCE, TCS, INFY.
    """
    # Groww uses different endpoint paths for search vs direct quote
    # Try the stocks endpoint first
    data = await _fetch(
        f"{GROWW_BASE}/stocks_data/v1/accord_points/exchange/{exchange}/segment/CASH/{symbol}/latest"
    )
    if data and not data.get("error"):
        # Normalize to unified schema
        return {
            "price": data.get("ltp") or data.get("close"),
            "change": data.get("dayChange"),
            "change_percent": data.get("dayChangePerc"),
            "company_name": data.get("companyName") or symbol,
            "currency": "INR" if exchange in ("NSE", "BSE") else "USD",
            "volume": data.get("volume"),
            "open": data.get("open"),
            "high": data.get("high"),
            "low": data.get("low"),
            "prev_close": data.get("close"),
            "key_stats": {
                "market_cap": data.get("marketCap"),
                "pe_ratio": data.get("pe"),
                "52_week_high": data.get("high52"),
                "52_week_low": data.get("low52"),
                "volume": data.get("volume"),
            },
            "source": "groww",
            "raw": data,
        }

    # Fallback: try search-based lookup
    search_data = await _fetch(
        f"{GROWW_BASE}/search/v1/entity",
        {"page": 0, "query": symbol, "size": 1, "web": True},
    )
    if search_data and not search_data.get("error"):
        content = search_data.get("content", [])
        if content:
            entity = content[0]
            return {
                "price": None,
                "company_name": entity.get("title") or entity.get("name") or symbol,
                "currency": "INR",
                "source": "groww_search",
                "raw": entity,
            }

    return None


async def search(query: str, limit: int = 10):
    """Search stocks/ETFs/MFs on Groww."""
    data = await _fetch(
        f"{GROWW_BASE}/search/v1/entity",
        {"page": 0, "query": query, "size": limit, "web": True},
    )
    if data and not data.get("error"):
        results = []
        for item in data.get("content", []):
            results.append({
                "symbol": item.get("search_id") or item.get("isin") or "",
                "name": item.get("title") or item.get("name") or "",
                "exchange": item.get("exchange") or "NSE",
                "type": item.get("entity_type") or "STOCK",
            })
        return results
    return []


async def get_stock_data(symbol: str):
    """Get detailed stock data from Groww company page API."""
    data = await _fetch(
        f"{GROWW_BASE}/stocks_data/v1/company/search_id/{symbol}"
    )
    if data and not data.get("error"):
        return {
            "name": data.get("header", {}).get("companyName"),
            "nse_symbol": data.get("header", {}).get("nseScripCode"),
            "bse_code": data.get("header", {}).get("bseScripCode"),
            "sector": data.get("header", {}).get("sector"),
            "industry": data.get("header", {}).get("industry"),
            "market_cap": data.get("header", {}).get("marketCap"),
            "pe_ratio": data.get("header", {}).get("pe"),
            "book_value": data.get("header", {}).get("bookValue"),
            "dividend_yield": data.get("header", {}).get("dividendYield"),
            "eps": data.get("header", {}).get("eps"),
            "face_value": data.get("header", {}).get("faceValue"),
            "source": "groww",
            "raw": data,
        }
    return None
