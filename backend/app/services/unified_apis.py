"""
AARAMBH Unified API v3.0 — Integration of all platform APIs
===========================================================

This module integrates:
- Economy Platform (GDP, indicators, government data)
- Finance API (Market data, quotes, charts)
- News Platform (News feeds, geopolitical, health)

All APIs use real online data sources with caching.
"""

import httpx
import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Cache configuration
_cache = {}
CACHE_TTL = 300  # 5 minutes

def _get_cache(key: str) -> Optional[Any]:
    if key in _cache:
        data, timestamp = _cache[key]
        if datetime.now() - timestamp < timedelta(seconds=CACHE_TTL):
            return data
    return None

def _set_cache(key: str, data: Any):
    _cache[key] = (data, datetime.now())

# API Keys from .env
FMP_API_KEY = os.getenv("FMP_API_KEY", "cjD3BCLxnYk8hBgcEpeH702txwLXc6TU")
INDIANAPI_KEY = os.getenv("INDIANAPI_KEY", "sk-live-dAo38cJjbWyutmX4YdJLobfTP8uHk5nUYBJbg0zY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FRED_API_KEY = os.getenv("FRED_API_KEY", "7263eaa18d73a57b7077f890e55a23ee")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "f89faec2ba214837966241244a22a54b")

# ==================== ECONOMY PLATFORM APIs ====================

class EconomyPlatformAPI:
    """Wrapper for economy_platform APIs"""
    BASE_URL = "http://localhost:8002"
    
    @staticmethod
    async def get_india_indicator(indicator: str) -> Dict[str, Any]:
        """Get India economic indicators (GDP, inflation, etc.)"""
        cache_key = f"economy:india:{indicator}"
        cached = _get_cache(cache_key)
        if cached:
            return cached
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{EconomyPlatformAPI.BASE_URL}/api/india/indicator/{indicator}", timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    _set_cache(cache_key, data)
                    return data
        except Exception as e:
            print(f"Economy API error: {e}")
        return {"error": "Failed to fetch India indicator"}
    
    @staticmethod
    async def get_pib_latest() -> Dict[str, Any]:
        """Get latest PIB press releases"""
        cache_key = "economy:pib:latest"
        cached = _get_cache(cache_key)
        if cached:
            return cached
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{EconomyPlatformAPI.BASE_URL}/api/pib/latest", timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    _set_cache(cache_key, data)
                    return data
        except Exception as e:
            print(f"PIB API error: {e}")
        return {"error": "Failed to fetch PIB data"}
    
    @staticmethod
    async def get_global_imf(indicator: str = "NGDPD", country: str = "IN") -> Dict[str, Any]:
        """Get IMF global economic data"""
        cache_key = f"economy:imf:{indicator}:{country}"
        cached = _get_cache(cache_key)
        if cached:
            return cached
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{EconomyPlatformAPI.BASE_URL}/api/global/imf",
                    params={"indicator": indicator, "country": country},
                    timeout=30
                )
                if resp.status_code == 200:
                    data = resp.json()
                    _set_cache(cache_key, data)
                    return data
        except Exception as e:
            print(f"IMF API error: {e}")
        return {"error": "Failed to fetch IMF data"}
    
    @staticmethod
    async def get_world_bank(country: str = "IN", indicator: str = "NY.GDP.MKTP.CD") -> Dict[str, Any]:
        """Get World Bank data"""
        cache_key = f"economy:wb:{country}:{indicator}"
        cached = _get_cache(cache_key)
        if cached:
            return cached
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{EconomyPlatformAPI.BASE_URL}/api/global/world-bank",
                    params={"country": country, "indicator": indicator},
                    timeout=30
                )
                if resp.status_code == 200:
                    data = resp.json()
                    _set_cache(cache_key, data)
                    return data
        except Exception as e:
            print(f"World Bank API error: {e}")
        return {"error": "Failed to fetch World Bank data"}


# ==================== FINANCE API ====================

class FinancePlatformAPI:
    """Wrapper for finance_api endpoints"""
    BASE_URL = "http://localhost:8000"
    
    @staticmethod
    async def get_google_finance_quote(ticker: str, exchange: str = "NASDAQ") -> Dict[str, Any]:
        """Get Google Finance quote"""
        cache_key = f"finance:google:{ticker}:{exchange}"
        cached = _get_cache(cache_key)
        if cached:
            return cached
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{FinancePlatformAPI.BASE_URL}/api/finance/google-finance/quote/{ticker}/{exchange}",
                    timeout=30
                )
                if resp.status_code == 200:
                    data = resp.json()
                    _set_cache(cache_key, data)
                    return data
        except Exception as e:
            print(f"Google Finance error: {e}")
        return {"error": "Failed to fetch Google Finance data"}
    
    @staticmethod
    async def get_yahoo_finance_quote(ticker: str) -> Dict[str, Any]:
        """Get Yahoo Finance comprehensive quote"""
        cache_key = f"finance:yahoo:{ticker}"
        cached = _get_cache(cache_key)
        if cached:
            return cached
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{FinancePlatformAPI.BASE_URL}/api/finance/yahoo-finance/quote/{ticker}",
                    timeout=30
                )
                if resp.status_code == 200:
                    data = resp.json()
                    _set_cache(cache_key, data)
                    return data
        except Exception as e:
            print(f"Yahoo Finance error: {e}")
        return {"error": "Failed to fetch Yahoo Finance data"}
    
    @staticmethod
    async def get_yahoo_chart(ticker: str, interval: str = "1d", range: str = "3mo") -> Dict[str, Any]:
        """Get Yahoo Finance chart data"""
        cache_key = f"finance:chart:{ticker}:{interval}:{range}"
        cached = _get_cache(cache_key)
        if cached:
            return cached
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{FinancePlatformAPI.BASE_URL}/api/finance/yahoo-finance/chart/{ticker}",
                    params={"interval": interval, "range": range},
                    timeout=30
                )
                if resp.status_code == 200:
                    data = resp.json()
                    _set_cache(cache_key, data)
                    return data
        except Exception as e:
            print(f"Yahoo Chart error: {e}")
        return {"error": "Failed to fetch chart data"}
    
    @staticmethod
    async def get_market_movers(type: str = "day_gainers") -> Dict[str, Any]:
        """Get market movers from Yahoo Finance"""
        cache_key = f"finance:movers:{type}"
        cached = _get_cache(cache_key)
        if cached:
            return cached
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{FinancePlatformAPI.BASE_URL}/api/finance/yahoo-finance/movers",
                    params={"type": type},
                    timeout=30
                )
                if resp.status_code == 200:
                    data = resp.json()
                    _set_cache(cache_key, data)
                    return data
        except Exception as e:
            print(f"Movers API error: {e}")
        return {"error": "Failed to fetch market movers"}


# ==================== NEWS PLATFORM APIs ====================

class NewsPlatformAPI:
    """Wrapper for news_platform APIs"""
    BASE_URL = "http://localhost:8001"
    
    @staticmethod
    async def get_headlines() -> Dict[str, Any]:
        """Get top headlines from all sources"""
        cache_key = "news:headlines"
        cached = _get_cache(cache_key)
        if cached:
            return cached
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{NewsPlatformAPI.BASE_URL}/api/news/headlines", timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    _set_cache(cache_key, data)
                    return data
        except Exception as e:
            print(f"News headlines error: {e}")
        return {"error": "Failed to fetch headlines"}
    
    @staticmethod
    async def get_finance_news() -> Dict[str, Any]:
        """Get finance/business news"""
        cache_key = "news:finance"
        cached = _get_cache(cache_key)
        if cached:
            return cached
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{NewsPlatformAPI.BASE_URL}/api/news/category/finance", timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    _set_cache(cache_key, data)
                    return data
        except Exception as e:
            print(f"Finance news error: {e}")
        return {"error": "Failed to fetch finance news"}
    
    @staticmethod
    async def search_news(query: str) -> Dict[str, Any]:
        """Search news across all sources"""
        cache_key = f"news:search:{query}"
        cached = _get_cache(cache_key)
        if cached:
            return cached
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{NewsPlatformAPI.BASE_URL}/api/news/search",
                    params={"q": query},
                    timeout=30
                )
                if resp.status_code == 200:
                    data = resp.json()
                    _set_cache(cache_key, data)
                    return data
        except Exception as e:
            print(f"News search error: {e}")
        return {"error": "Failed to search news"}
    
    @staticmethod
    async def get_geopolitical(query: str = "geopolitical") -> Dict[str, Any]:
        """Get geopolitical intelligence from GDELT"""
        cache_key = f"news:geo:{query}"
        cached = _get_cache(cache_key)
        if cached:
            return cached
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{NewsPlatformAPI.BASE_URL}/api/geo/gdelt",
                    params={"query": query},
                    timeout=30
                )
                if resp.status_code == 200:
                    data = resp.json()
                    _set_cache(cache_key, data)
                    return data
        except Exception as e:
            print(f"Geopolitical error: {e}")
        return {"error": "Failed to fetch geopolitical data"}


# ==================== FMP API (Direct) ====================

class FMPAPI:
    """Direct FMP API integration"""
    BASE_URL = "https://financialmodelingprep.com"
    
    @staticmethod
    async def get_quote(symbol: str) -> Dict[str, Any]:
        """Get stock quote from FMP"""
        cache_key = f"fmp:quote:{symbol}"
        cached = _get_cache(cache_key)
        if cached:
            return cached
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{FMPAPI.BASE_URL}/stable/quote",
                    params={"symbol": symbol, "apikey": FMP_API_KEY},
                    timeout=30
                )
                if resp.status_code == 200:
                    data = resp.json()
                    result = data[0] if data else {}
                    _set_cache(cache_key, result)
                    return result
        except Exception as e:
            print(f"FMP quote error: {e}")
        return {}
    
    @staticmethod
    async def get_profile(symbol: str) -> Dict[str, Any]:
        """Get company profile from FMP"""
        cache_key = f"fmp:profile:{symbol}"
        cached = _get_cache(cache_key)
        if cached:
            return cached
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{FMPAPI.BASE_URL}/stable/company-profile",
                    params={"symbol": symbol, "apikey": FMP_API_KEY},
                    timeout=30
                )
                if resp.status_code == 200:
                    data = resp.json()
                    result = data[0] if data else {}
                    _set_cache(cache_key, result)
                    return result
        except Exception as e:
            print(f"FMP profile error: {e}")
        return {}
    
    @staticmethod
    async def get_screener() -> List[Dict[str, Any]]:
        """Get stock screener data"""
        cache_key = "fmp:screener"
        cached = _get_cache(cache_key)
        if cached:
            return cached
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{FMPAPI.BASE_URL}/api/v3/stock-screener",
                    params={"limit": 100, "apikey": FMP_API_KEY},
                    timeout=30
                )
                if resp.status_code == 200:
                    data = resp.json()
                    _set_cache(cache_key, data)
                    return data
        except Exception as e:
            print(f"FMP screener error: {e}")
        return []
    
    @staticmethod
    async def get_market_movers(type: str = "gainers") -> List[Dict[str, Any]]:
        """Get market movers"""
        cache_key = f"fmp:movers:{type}"
        cached = _get_cache(cache_key)
        if cached:
            return cached
        
        endpoint_map = {
            "gainers": "stock_market/gainers",
            "losers": "stock_market/losers",
            "most-active": "stock_market/actives"
        }
        endpoint = endpoint_map.get(type, "stock_market/gainers")
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{FMPAPI.BASE_URL}/api/v3/{endpoint}",
                    params={"apikey": FMP_API_KEY},
                    timeout=30
                )
                if resp.status_code == 200:
                    data = resp.json()
                    _set_cache(cache_key, data)
                    return data
        except Exception as e:
            print(f"FMP movers error: {e}")
        return []
    
    @staticmethod
    async def get_news(symbol: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get stock or general news"""
        cache_key = f"fmp:news:{symbol}:{limit}"
        cached = _get_cache(cache_key)
        if cached:
            return cached
        
        try:
            params = {"limit": limit, "apikey": FMP_API_KEY}
            if symbol:
                params["tickers"] = symbol
                url = f"{FMPAPI.BASE_URL}/api/v3/stock_news"
            else:
                url = f"{FMPAPI.BASE_URL}/stable/news/general-latest"
            
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    _set_cache(cache_key, data)
                    return data
        except Exception as e:
            print(f"FMP news error: {e}")
        return []


# Export unified API instances
economy_api = EconomyPlatformAPI()
finance_api = FinancePlatformAPI()
news_api = NewsPlatformAPI()
fmp_api = FMPAPI()
