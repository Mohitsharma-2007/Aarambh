"""
Unified Finance Service — Aggregates multiple API sources with fallback strategy.

Priority:
  1. Google Finance (scraper, free)
  2. Yahoo Finance (scraper, free)
  3. Financial Modeling Prep (FMP) — fundamentals, profile
  4. Finnhub — company news, profile
  5. TwelveData — chart data, time series
  6. Alpha Vantage — indicators (RSI, MACD)

All responses are normalized to a common schema.
"""

import os
import time
import asyncio
import asyncio
import httpx
import re
import json
from typing import Optional
from functools import lru_cache
from app.services.ai_service import ai_service

# ── API Keys ─────────────────────────────────────────────────
GROWW_KEY = os.getenv("GROWW_API_KEY", "")
FMP_KEY = os.getenv("FMP_API_KEY", "")
FINNHUB_KEY = os.getenv("FINNHUB_API_KEY", "")
TWELVEDATA_KEY = os.getenv("TWELVEDATA_API_KEY", "")
ALPHAVANTAGE_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")

FMP_BASE = "https://financialmodelingprep.com/stable"
FINNHUB_BASE = "https://finnhub.io/api/v1"
TWELVEDATA_BASE = "https://api.twelvedata.com"
ALPHAVANTAGE_BASE = "https://www.alphavantage.co/query"

# ── Simple in-memory cache ───────────────────────────────────
_cache: dict[str, tuple[float, any]] = {}
CACHE_TTL = 300  # 5 minutes


def _get_cached(key: str):
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return data
        del _cache[key]
    return None


def _set_cached(key: str, data):
    _cache[key] = (time.time(), data)


# ── HTTP Client ──────────────────────────────────────────────
async def _fetch(url: str, params: dict = None, headers: dict = None, timeout: float = 10.0):
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url, params=params, headers=headers)
            if r.status_code == 200:
                return r.json()
            return {"error": f"HTTP {r.status_code}", "url": url}
    except Exception as e:
        return {"error": str(e), "url": url}


# ══════════════════════════════════════════════════════════════
# FMP — Financial Modeling Prep
# ══════════════════════════════════════════════════════════════

async def fmp_quote(symbol: str):
    """Real-time quote from FMP (stable API)."""
    ck = f"fmp_quote:{symbol}"
    cached = _get_cached(ck)
    if cached:
        return cached
    data = await _fetch(f"{FMP_BASE}/quote", {"symbol": symbol, "apikey": FMP_KEY})
    if isinstance(data, list) and data:
        _set_cached(ck, data[0])
        return data[0]
    return data


async def fmp_profile(symbol: str):
    """Company profile from FMP (stable API)."""
    ck = f"fmp_profile:{symbol}"
    cached = _get_cached(ck)
    if cached:
        return cached
    data = await _fetch(f"{FMP_BASE}/profile", {"symbol": symbol, "apikey": FMP_KEY})
    if isinstance(data, list) and data:
        _set_cached(ck, data[0])
        return data[0]
    return data


async def fmp_income_statement(symbol: str, period: str = "annual", limit: int = 5):
    ck = f"fmp_income:{symbol}:{period}:{limit}"
    cached = _get_cached(ck)
    if cached:
        return cached
    data = await _fetch(
        f"{FMP_BASE}/income-statement",
        {"symbol": symbol, "apikey": FMP_KEY, "period": period, "limit": limit},
    )
    if isinstance(data, list):
        _set_cached(ck, data)
    return data


async def fmp_balance_sheet(symbol: str, period: str = "annual", limit: int = 5):
    ck = f"fmp_bs:{symbol}:{period}:{limit}"
    cached = _get_cached(ck)
    if cached:
        return cached
    data = await _fetch(
        f"{FMP_BASE}/balance-sheet-statement",
        {"symbol": symbol, "apikey": FMP_KEY, "period": period, "limit": limit},
    )
    if isinstance(data, list):
        _set_cached(ck, data)
    return data


async def fmp_cash_flow(symbol: str, period: str = "annual", limit: int = 5):
    ck = f"fmp_cf:{symbol}:{period}:{limit}"
    cached = _get_cached(ck)
    if cached:
        return cached
    data = await _fetch(
        f"{FMP_BASE}/cash-flow-statement",
        {"symbol": symbol, "apikey": FMP_KEY, "period": period, "limit": limit},
    )
    if isinstance(data, list):
        _set_cached(ck, data)
    return data


async def fmp_ratios(symbol: str, limit: int = 5):
    ck = f"fmp_ratios:{symbol}:{limit}"
    cached = _get_cached(ck)
    if cached:
        return cached
    data = await _fetch(
        f"{FMP_BASE}/ratios",
        {"symbol": symbol, "apikey": FMP_KEY, "limit": limit},
    )
    if isinstance(data, list):
        _set_cached(ck, data)
    return data


async def fmp_search(query: str, limit: int = 10):
    ck = f"fmp_search:{query}:{limit}"
    cached = _get_cached(ck)
    if cached:
        return cached
    # Try search-name first (works for company names), then search-ticker
    data = await _fetch(
        f"{FMP_BASE}/search-name",
        {"apikey": FMP_KEY, "query": query, "limit": limit},
    )
    if isinstance(data, list) and data:
        _set_cached(ck, data)
        return data
    data = await _fetch(
        f"{FMP_BASE}/search-ticker",
        {"apikey": FMP_KEY, "query": query, "limit": limit},
    )
    if isinstance(data, list):
        _set_cached(ck, data)
    return data


async def fmp_market_gainers():
    ck = "fmp_gainers"
    cached = _get_cached(ck)
    if cached:
        return cached
    data = await _fetch(f"{FMP_BASE}/stock_market/gainers", {"apikey": FMP_KEY})
    if isinstance(data, list):
        _set_cached(ck, data)
    return data


async def fmp_market_losers():
    ck = "fmp_losers"
    cached = _get_cached(ck)
    if cached:
        return cached
    data = await _fetch(f"{FMP_BASE}/stock_market/losers", {"apikey": FMP_KEY})
    if isinstance(data, list):
        _set_cached(ck, data)
    return data


async def fmp_historical_price(symbol: str, timeframe: str = "1day"):
    """Historical daily prices from FMP (stable API)."""
    ck = f"fmp_hist:{symbol}:{timeframe}"
    cached = _get_cached(ck)
    if cached:
        return cached
    data = await _fetch(
        f"{FMP_BASE}/historical-price-eod/full",
        {"symbol": symbol, "apikey": FMP_KEY},
    )
    # Stable API returns a flat list of price objects
    if isinstance(data, list) and data:
        result = {"historical": data[:365]}
        _set_cached(ck, result)
        return result
    if isinstance(data, dict) and not data.get("error"):
        _set_cached(ck, data)
    return data if data else {"historical": []}


# ══════════════════════════════════════════════════════════════
# FINNHUB
# ══════════════════════════════════════════════════════════════

async def finnhub_profile(symbol: str):
    ck = f"fh_profile:{symbol}"
    cached = _get_cached(ck)
    if cached:
        return cached
    data = await _fetch(
        f"{FINNHUB_BASE}/stock/profile2",
        {"symbol": symbol, "token": FINNHUB_KEY},
    )
    if data and not data.get("error"):
        _set_cached(ck, data)
    return data


async def finnhub_news(symbol: str, from_date: str = "", to_date: str = ""):
    """Company news from Finnhub."""
    import datetime
    if not to_date:
        to_date = datetime.date.today().isoformat()
    if not from_date:
        from_date = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    ck = f"fh_news:{symbol}:{from_date}:{to_date}"
    cached = _get_cached(ck)
    if cached:
        return cached
    data = await _fetch(
        f"{FINNHUB_BASE}/company-news",
        {"symbol": symbol, "from": from_date, "to": to_date, "token": FINNHUB_KEY},
    )
    if isinstance(data, list):
        _set_cached(ck, data[:20])
        return data[:20]
    return data


async def finnhub_general_news(category: str = "general"):
    ck = f"fh_gnews:{category}"
    cached = _get_cached(ck)
    if cached:
        return cached
    data = await _fetch(
        f"{FINNHUB_BASE}/news",
        {"category": category, "token": FINNHUB_KEY},
    )
    if isinstance(data, list):
        _set_cached(ck, data[:20])
        return data[:20]
    return data


async def finnhub_quote(symbol: str):
    ck = f"fh_quote:{symbol}"
    cached = _get_cached(ck)
    if cached:
        return cached
    data = await _fetch(
        f"{FINNHUB_BASE}/quote",
        {"symbol": symbol, "token": FINNHUB_KEY},
    )
    if data and not data.get("error"):
        _set_cached(ck, data)
    return data


# ══════════════════════════════════════════════════════════════
# TWELVE DATA
# ══════════════════════════════════════════════════════════════

async def twelvedata_time_series(
    symbol: str, interval: str = "1day", outputsize: int = 100
):
    """OHLCV time series data."""
    ck = f"td_ts:{symbol}:{interval}:{outputsize}"
    cached = _get_cached(ck)
    if cached:
        return cached
    data = await _fetch(
        f"{TWELVEDATA_BASE}/time_series",
        {
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize,
            "apikey": TWELVEDATA_KEY,
        },
    )
    if data and not data.get("error"):
        _set_cached(ck, data)
    return data


async def twelvedata_quote(symbol: str):
    ck = f"td_quote:{symbol}"
    cached = _get_cached(ck)
    if cached:
        return cached
    data = await _fetch(
        f"{TWELVEDATA_BASE}/quote",
        {"symbol": symbol, "apikey": TWELVEDATA_KEY},
    )
    if data and not data.get("error"):
        _set_cached(ck, data)
    return data


# ══════════════════════════════════════════════════════════════
# ALPHA VANTAGE — Technical Indicators
# ══════════════════════════════════════════════════════════════

async def alphavantage_indicator(symbol: str, function: str = "RSI", interval: str = "daily", time_period: int = 14):
    ck = f"av_{function}:{symbol}:{interval}:{time_period}"
    cached = _get_cached(ck)
    if cached:
        return cached
    data = await _fetch(
        ALPHAVANTAGE_BASE,
        {
            "function": function,
            "symbol": symbol,
            "interval": interval,
            "time_period": time_period,
            "series_type": "close",
            "apikey": ALPHAVANTAGE_KEY,
        },
    )
    if data and not data.get("error"):
        _set_cached(ck, data)
    return data


# ══════════════════════════════════════════════════════════════
# UNIFIED AGGREGATION — Fallback Strategy
# ══════════════════════════════════════════════════════════════

async def get_unified_quote(symbol: str, exchange: str = "NASDAQ"):
    """
    Get stock quote with fallback:
      Google Finance → Yahoo Finance → FMP → Finnhub
    Returns normalized response.
    """
    from scrapers import google_finance as gf, yahoo_finance as yf

    result = {
        "symbol": symbol,
        "exchange": exchange,
        "source": None,
        "price": None,
        "change": None,
        "change_percent": None,
        "name": None,
        "currency": "USD",
        "market_cap": None,
        "pe_ratio": None,
        "volume": None,
        "high_52w": None,
        "low_52w": None,
        "open": None,
        "high": None,
        "low": None,
        "prev_close": None,
        "eps": None,
        "dividend_yield": None,
        "beta": None,
        "sector": None,
        "industry": None,
        "about": None,
        "website": None,
        "logo": None,
        "raw": None,
    }

    # Strategy 0: Groww (priority for Indian stocks, try for all)
    try:
        if GROWW_KEY:
            from scrapers import groww_finance as groww
            groww_data = await groww.get_quote(symbol, exchange)
            if groww_data and groww_data.get("price"):
                result.update({
                    "source": "groww",
                    "price": groww_data.get("price"),
                    "change": groww_data.get("change"),
                    "change_percent": groww_data.get("change_percent"),
                    "name": groww_data.get("company_name"),
                    "currency": groww_data.get("currency", "INR"),
                    "open": groww_data.get("open"),
                    "high": groww_data.get("high"),
                    "low": groww_data.get("low"),
                    "prev_close": groww_data.get("prev_close"),
                    "volume": groww_data.get("volume"),
                    "raw": groww_data.get("raw"),
                })
                stats = groww_data.get("key_stats", {})
                if stats:
                    result["market_cap"] = stats.get("market_cap")
                    result["pe_ratio"] = stats.get("pe_ratio")
                    result["high_52w"] = stats.get("52_week_high")
                    result["low_52w"] = stats.get("52_week_low")
                return result
    except Exception:
        pass

    # Strategy 1: Google Finance
    try:
        gf_data = await gf.get_quote(symbol, exchange)
        if gf_data and gf_data.get("price"):
            result.update({
                "source": "google_finance",
                "price": gf_data.get("price"),
                "change": gf_data.get("change"),
                "change_percent": gf_data.get("change_percent"),
                "name": gf_data.get("company_name"),
                "currency": gf_data.get("currency", "USD"),
                "about": gf_data.get("about"),
                "raw": gf_data,
            })
            # Extract stats if available
            stats = gf_data.get("key_stats", {})
            if stats:
                result["market_cap"] = stats.get("market_cap") or stats.get("Market cap")
                result["pe_ratio"] = stats.get("pe_ratio") or stats.get("P/E ratio")
                result["volume"] = stats.get("volume") or stats.get("Avg Volume")
                result["high_52w"] = stats.get("52_week_high") or stats.get("52-wk high")
                result["low_52w"] = stats.get("52_week_low") or stats.get("52-wk low")
            return result
    except Exception:
        pass

    # Strategy 2: Yahoo Finance
    try:
        yf_ticker = f"{symbol}.NS" if exchange == "NSE" else symbol
        yf_data = await yf.get_quote(yf_ticker)
        if yf_data and yf_data.get("price"):
            result.update({
                "source": "yahoo_finance",
                "price": yf_data.get("price"),
                "change": yf_data.get("change"),
                "change_percent": yf_data.get("change_percent"),
                "name": yf_data.get("name") or yf_data.get("long_name"),
                "currency": yf_data.get("currency", "USD"),
                "market_cap": yf_data.get("market_cap"),
                "pe_ratio": yf_data.get("pe_ratio"),
                "volume": yf_data.get("volume"),
                "high_52w": yf_data.get("52w_high"),
                "low_52w": yf_data.get("52w_low"),
                "open": yf_data.get("open"),
                "high": yf_data.get("high"),
                "low": yf_data.get("low"),
                "prev_close": yf_data.get("prev_close"),
                "eps": yf_data.get("eps"),
                "dividend_yield": yf_data.get("dividend_yield"),
                "beta": yf_data.get("beta"),
                "sector": yf_data.get("sector"),
                "industry": yf_data.get("industry"),
                "about": yf_data.get("description"),
                "website": yf_data.get("website"),
                "raw": yf_data,
            })
            return result
    except Exception:
        pass

    # Strategy 3: FMP
    try:
        if FMP_KEY:
            fmp_data = await fmp_quote(symbol)
            if fmp_data and not fmp_data.get("error"):
                result.update({
                    "source": "fmp",
                    "price": fmp_data.get("price"),
                    "change": fmp_data.get("change"),
                    "change_percent": fmp_data.get("changesPercentage"),
                    "name": fmp_data.get("name"),
                    "market_cap": fmp_data.get("marketCap"),
                    "pe_ratio": fmp_data.get("pe"),
                    "volume": fmp_data.get("volume"),
                    "high_52w": fmp_data.get("yearHigh"),
                    "low_52w": fmp_data.get("yearLow"),
                    "open": fmp_data.get("open"),
                    "high": fmp_data.get("dayHigh"),
                    "low": fmp_data.get("dayLow"),
                    "prev_close": fmp_data.get("previousClose"),
                    "eps": fmp_data.get("eps"),
                    "raw": fmp_data,
                })
                return result
    except Exception:
        pass

    # Strategy 4: Finnhub
    try:
        if FINNHUB_KEY:
            fh_q, fh_p = await asyncio.gather(
                finnhub_quote(symbol),
                finnhub_profile(symbol),
            )
            if fh_q and fh_q.get("c"):
                result.update({
                    "source": "finnhub",
                    "price": fh_q.get("c"),
                    "change": fh_q.get("d"),
                    "change_percent": fh_q.get("dp"),
                    "open": fh_q.get("o"),
                    "high": fh_q.get("h"),
                    "low": fh_q.get("l"),
                    "prev_close": fh_q.get("pc"),
                })
                if fh_p and fh_p.get("name"):
                    result.update({
                        "name": fh_p.get("name"),
                        "logo": fh_p.get("logo"),
                        "website": fh_p.get("weburl"),
                        "industry": fh_p.get("finnhubIndustry"),
                        "market_cap": fh_p.get("marketCapitalization"),
                    })
                result["raw"] = {"quote": fh_q, "profile": fh_p}
                return result
    except Exception:
        pass

    result["error"] = "All sources failed"
    return result


async def get_unified_chart(
    symbol: str, exchange: str = "NASDAQ", interval: str = "1day", window: str = "1Y"
):
    """
    Get chart data with fallback:
      Google Finance → Yahoo Finance → TwelveData → FMP
    Returns normalized OHLCV data.
    """
    from scrapers import google_finance as gf, yahoo_finance as yf

    # Map window to interval/range for each API
    WINDOW_MAP_YF = {
        "1D": ("5m", "1d"), "5D": ("15m", "5d"), "1W": ("1h", "5d"),
        "1M": ("1d", "1mo"), "3M": ("1d", "3mo"), "6M": ("1d", "6mo"),
        "1Y": ("1d", "1y"), "5Y": ("1wk", "5y"), "YTD": ("1d", "ytd"),
        "MAX": ("1wk", "max"), "ALL": ("1wk", "max"),
    }
    WINDOW_MAP_TD = {
        "1D": ("5min", 78), "5D": ("30min", 60), "1W": ("1h", 40),
        "1M": ("1day", 30), "3M": ("1day", 90), "6M": ("1day", 180),
        "1Y": ("1day", 252), "5Y": ("1week", 260), "MAX": ("1month", 240),
        "ALL": ("1month", 240), "YTD": ("1day", 180),
    }

    # Strategy 1: Google Finance chart
    try:
        gf_data = await gf.get_chart(symbol, exchange, window)
        if gf_data and isinstance(gf_data, dict):
            points = gf_data.get("chart", gf_data.get("data", []))
            if points and isinstance(points, list) and len(points) > 0:
                return {
                    "symbol": symbol,
                    "source": "google_finance",
                    "interval": interval,
                    "window": window,
                    "data": points,
                }
    except Exception:
        pass

    # Strategy 2: Yahoo Finance chart
    try:
        yf_interval, yf_range = WINDOW_MAP_YF.get(window, ("1d", "1y"))
        yf_ticker = f"{symbol}.NS" if exchange == "NSE" else symbol
        yf_data = await yf.get_chart(yf_ticker, yf_interval, yf_range)
        if yf_data and isinstance(yf_data, dict):
            candles = yf_data.get("candles", yf_data.get("data", []))
            if candles and len(candles) > 0:
                return {
                    "symbol": symbol,
                    "source": "yahoo_finance",
                    "interval": yf_interval,
                    "window": window,
                    "data": candles,
                }
    except Exception:
        pass

    # Strategy 3: TwelveData
    try:
        if TWELVEDATA_KEY:
            td_interval, td_size = WINDOW_MAP_TD.get(window, ("1day", 252))
            td_data = await twelvedata_time_series(symbol, td_interval, td_size)
            if td_data and td_data.get("values"):
                normalized = []
                for v in td_data["values"]:
                    normalized.append({
                        "date": v.get("datetime"),
                        "open": float(v.get("open", 0)),
                        "high": float(v.get("high", 0)),
                        "low": float(v.get("low", 0)),
                        "close": float(v.get("close", 0)),
                        "volume": int(float(v.get("volume", 0))),
                    })
                return {
                    "symbol": symbol,
                    "source": "twelvedata",
                    "interval": td_interval,
                    "window": window,
                    "data": list(reversed(normalized)),
                }
    except Exception:
        pass

    # Strategy 4: FMP historical
    try:
        if FMP_KEY:
            fmp_data = await fmp_historical_price(symbol)
            if fmp_data and fmp_data.get("historical"):
                hist = fmp_data["historical"][:365]
                normalized = []
                for v in reversed(hist):
                    normalized.append({
                        "date": v.get("date"),
                        "open": v.get("open"),
                        "high": v.get("high"),
                        "low": v.get("low"),
                        "close": v.get("close"),
                        "volume": v.get("volume"),
                    })
                return {
                    "symbol": symbol,
                    "source": "fmp",
                    "interval": "1day",
                    "window": window,
                    "data": normalized,
                }
    except Exception:
        pass

    return {"symbol": symbol, "error": "All chart sources failed", "data": []}


async def get_unified_fundamentals(symbol: str):
    """
    Get financial fundamentals (balance sheet, income statement, cash flow)
    Priority: FMP → Yahoo Finance (if available)
    """
    result = {
        "symbol": symbol,
        "source": None,
        "income_statement": [],
        "balance_sheet": [],
        "cash_flow": [],
        "ratios": [],
    }

    if FMP_KEY:
        try:
            inc, bs, cf, ratios = await asyncio.gather(
                fmp_income_statement(symbol),
                fmp_balance_sheet(symbol),
                fmp_cash_flow(symbol),
                fmp_ratios(symbol),
            )
            result["source"] = "fmp"
            if isinstance(inc, list):
                result["income_statement"] = inc
            if isinstance(bs, list):
                result["balance_sheet"] = bs
            if isinstance(cf, list):
                result["cash_flow"] = cf
            if isinstance(ratios, list):
                result["ratios"] = ratios
            return result
        except Exception:
            pass

    result["error"] = "No fundamentals source available"
    return result


async def get_unified_company_news(symbol: str):
    """
    Get company news with fallback:
      Google Finance news → Finnhub news
    """
    from scrapers import google_finance as gf

    # Strategy 1: Google Finance news
    try:
        data = await gf.get_quote(symbol, "NASDAQ")
        news = data.get("news", [])
        if news:
            return {
                "symbol": symbol,
                "source": "google_finance",
                "count": len(news),
                "articles": news[:15],
            }
    except Exception:
        pass

    # Strategy 2: Finnhub
    try:
        if FINNHUB_KEY:
            articles = await finnhub_news(symbol)
            if isinstance(articles, list) and articles:
                normalized = []
                for a in articles[:15]:
                    normalized.append({
                        "title": a.get("headline"),
                        "source": a.get("source"),
                        "url": a.get("url"),
                        "image": a.get("image"),
                        "summary": a.get("summary"),
                        "published": a.get("datetime"),
                    })
                return {
                    "symbol": symbol,
                    "source": "finnhub",
                    "count": len(normalized),
                    "articles": normalized,
                }
    except Exception:
        pass

    return {"symbol": symbol, "error": "No news sources available", "articles": []}


async def get_unified_profile(symbol: str, exchange: str = "NASDAQ"):
    """
    Get company profile with fallback:
      FMP → Finnhub → Google Finance about
    """
    # Strategy 1: FMP
    if FMP_KEY:
        try:
            data = await fmp_profile(symbol)
            if data and not data.get("error") and data.get("companyName"):
                return {
                    "symbol": symbol,
                    "source": "fmp",
                    "name": data.get("companyName"),
                    "description": data.get("description"),
                    "sector": data.get("sector"),
                    "industry": data.get("industry"),
                    "ceo": data.get("ceo"),
                    "employees": data.get("fullTimeEmployees"),
                    "headquarters": data.get("city"),
                    "country": data.get("country"),
                    "website": data.get("website"),
                    "logo": data.get("image"),
                    "exchange": data.get("exchangeShortName"),
                    "market_cap": data.get("mktCap"),
                    "ipo_date": data.get("ipoDate"),
                }
        except Exception:
            pass

    # Strategy 2: Finnhub
    if FINNHUB_KEY:
        try:
            data = await finnhub_profile(symbol)
            if data and data.get("name"):
                return {
                    "symbol": symbol,
                    "source": "finnhub",
                    "name": data.get("name"),
                    "description": None,
                    "sector": None,
                    "industry": data.get("finnhubIndustry"),
                    "website": data.get("weburl"),
                    "logo": data.get("logo"),
                    "exchange": data.get("exchange"),
                    "market_cap": data.get("marketCapitalization"),
                    "country": data.get("country"),
                    "ipo_date": data.get("ipo"),
                }
        except Exception:
            pass

    return {"symbol": symbol, "error": "No profile source available"}


async def search_unified(query: str, limit: int = 10):
    """
    Search stocks/ETFs with fallback:
      Google Finance → FMP → Yahoo Finance
    """
    from scrapers import google_finance as gf, yahoo_finance as yf

    # Strategy 0: Groww search
    try:
        if GROWW_KEY:
            from scrapers import groww_finance as groww
            groww_results = await groww.search(query, limit)
            if groww_results:
                return {"source": "groww", "results": groww_results}
    except Exception:
        pass

    # Strategy 1: Google Finance
    try:
        data = await gf.search_gf(query)
        if data and isinstance(data, list) and len(data) > 0:
            return {"source": "google_finance", "results": data[:limit]}
        if data and isinstance(data, dict) and data.get("results"):
            return {"source": "google_finance", "results": data["results"][:limit]}
    except Exception:
        pass

    # Strategy 2: FMP
    if FMP_KEY:
        try:
            data = await fmp_search(query, limit)
            if isinstance(data, list) and data:
                results = []
                for item in data:
                    results.append({
                        "symbol": item.get("symbol"),
                        "name": item.get("name"),
                        "exchange": item.get("stockExchange") or item.get("exchangeShortName"),
                        "type": item.get("type", "stock"),
                    })
                return {"source": "fmp", "results": results}
        except Exception:
            pass

    # Strategy 3: Yahoo Finance
    try:
        data = await yf.search_yf(query)
        if data:
            return {"source": "yahoo_finance", "results": data}
    except Exception:
        pass

    return {"source": "none", "results": []}
