"""
Premium API Integration - Multiple Data Sources
Integrates all provided API keys for comprehensive financial data
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd

class PremiumAPIManager:
    """Manages all premium API integrations"""
    
    def __init__(self):
        self.session = None
        self.cache = {}
        self.cache_expiry = {}
        
        # API Keys from user
        self.api_keys = {
            "alpha_vantage": "EPVBVC6GA4DTM3J0",
            "marketstack": "3a4c179ab49bc0c1b910701d5e1cae82",
            "eodhd": "69c48c1f5a4b59.80000680",
            "financial_modeling_prep": "cjD3BCLxnYk8hBgcEpeH702txwLXc6TU",
            "finnhub": "d7065m1r01qtb4r9kju0d7065m1r01qtb4r9kjug",
            "twelve_data": "9fafee9808984cd3a3c949dfc9b38ce5",
            "groww": {
                "api_key": "eyJraWQiOiJaTUtjVXciLCJhbGciOiJFUzI1NiJ9.eyJleHAiOjI1NjI4OTE0NDgsImlhdCI6MTc3NDQ5MTQ0OCwibmJmIjoxNzc0NDkxNDQ4LCJzdWIiOiJ7XCJ0b2tlblJlZklkXCI6XCJkNjE1YWYwNy0zMTE5LTRmYWMtYTVmYy1hNDIwNWI4MmEwNzhcIixcInZlbmRvckludGVncmF0aW9uS2V5XCI6XCJlMzFmZjIzYjA4NmI0MDZjODg3NGIyZjZkODQ5NTMxM1wiLFwidXNlckFjY291bnRJZFwiOlwiOTgwNzUxNTYtOTI1MS00NjQ3LWE3MDItYzM0M2QxMDY4ZmU3XCIsXCJkZXZpY2VJZFwiOlwiMDdmYjYyZDktNmUxYS01YzI4LWJmN2MtYzE2NjZmZGFhYTBhXCIsXCJzZXNzaW9uSWRcIjpcIjlkZTY4Zjg2LTVhZjEtNGY1YS04NzU0LTgzNmRlNGUxODU2ZVwiLFwiYWRkaXRpb25hbERhdGFcIjpcIno1NC9NZzltdjE2WXdmb0gvS0EwYlAwU2ljZTkxL0toOUJFK1JKZWh3bXhSTkczdTlLa2pWZDNoWjU1ZStNZERhWXBOVi9UOUxIRmtQejFFQisybTdRPT1cIixcInJvbGVcIjpcImF1dGgtdG90cFwiLFwic291cmNlSXBBZGRyZXNzXCI6XCIyNDA5OjQwZDI6NGU6NWI2MjpjZGI1OjcwZWE6Y2RkYjpkMjFkLDE3Mi43MS4xOTguOTUsMzUuMjQxLjIzLjEyM1wiLFwidHdvRmFFeHBpcnlUc1wiOjI1NjI4OTE0NDg4MzUsXCJ2ZW5kb3JOYW1lXCI6XCJncm93d0FwaVwifSIsImlzcyI6ImFwZXgtYXV0aC1wcm9kLWFwcCJ9.R0SoRTG52YyMPaDmbvxzuFw5RskIGsHSPP1KUyqgHDB_flcbzaXDATqw7EZGQTYRotxbI0sXRBy7kJZTUpWgg",
                "secret": "e#!gD1kMm&tT_kmTfj_2Tg47Uw%TF4@R"
            },
            "rapidapi": {
                "key": "53a6e6a3e8mshfe8e2039b6be021p1c4a00jsnd621a06f362d",
                "host": "indian-stock-exchange-api2.p.rapidapi.com"
            }
        }
        
        # API Base URLs
        self.base_urls = {
            "alpha_vantage": "https://www.alphavantage.co/query",
            "marketstack": "http://api.marketstack.com/v1",
            "eodhd": "https://eodhd.com/api",
            "financial_modeling_prep": "https://financialmodelingprep.com/api/v3",
            "finnhub": "https://finnhub.io/api/v1",
            "twelve_data": "https://api.twelvedata.com",
            "groww": "https://groww.in/v1/api",
            "rapidapi": "https://indian-stock-exchange-api2.p.rapidapi.com"
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Mozilla/5.0 (compatible; PremiumFinanceBot/1.0)'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_cache_key(self, method: str, symbol: str, **kwargs) -> str:
        """Generate cache key"""
        key_parts = [method, symbol] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
        return "|".join(key_parts)
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache is valid"""
        if cache_key not in self.cache:
            return False
        
        expiry = self.cache_expiry.get(cache_key, datetime.now())
        return datetime.now() < expiry
    
    def _set_cache(self, cache_key: str, data: Any, ttl_minutes: int = 5):
        """Set cache with expiry"""
        self.cache[cache_key] = data
        self.cache_expiry[cache_key] = datetime.now() + timedelta(minutes=ttl_minutes)
    
    async def get_alpha_vantage_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get quote from Alpha Vantage"""
        cache_key = self._get_cache_key("av_quote", symbol)
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            url = self.base_urls["alpha_vantage"]
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.api_keys["alpha_vantage"]
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if "Global Quote" in data:
                        quote = data["Global Quote"]
                        result = {
                            "ticker": symbol,
                            "exchange": "NASDAQ",
                            "company_name": symbol,
                            "price": quote.get("05. price", "0.00"),
                            "change": quote.get("09. change", "0.00"),
                            "change_percent": quote.get("10. change percent", "0.00%"),
                            "currency": "USD",
                            "volume": quote.get("06. volume", "0"),
                            "source": "alpha_vantage",
                            "timestamp": datetime.now().isoformat()
                        }
                        self._set_cache(cache_key, result, 5)
                        return result
        except Exception as e:
            print(f"Alpha Vantage error for {symbol}: {e}")
        
        return None
    
    async def get_twelve_data_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get quote from Twelve Data"""
        cache_key = self._get_cache_key("td_quote", symbol)
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            url = self.base_urls["twelve_data"]
            params = {
                "symbol": symbol,
                "apikey": self.api_keys["twelve_data"],
                "interval": "1min",
                "outputsize": "1"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if "values" in data and data["values"]:
                        quote = data["values"][0]
                        result = {
                            "ticker": symbol,
                            "exchange": "NASDAQ",
                            "company_name": symbol,
                            "price": quote.get("close", "0.00"),
                            "change": "0.00",  # Calculate from previous close
                            "change_percent": "0.00%",
                            "currency": "USD",
                            "volume": quote.get("volume", "0"),
                            "source": "twelve_data",
                            "timestamp": datetime.now().isoformat()
                        }
                        self._set_cache(cache_key, result, 5)
                        return result
        except Exception as e:
            print(f"Twelve Data error for {symbol}: {e}")
        
        return None
    
    async def get_fmp_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get quote from Financial Modeling Prep"""
        cache_key = self._get_cache_key("fmp_quote", symbol)
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            url = f"{self.base_urls['financial_modeling_prep']}/quote/{symbol}"
            params = {"apikey": self.api_keys["financial_modeling_prep"]}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and len(data) > 0:
                        quote = data[0]
                        result = {
                            "ticker": symbol,
                            "exchange": quote.get("exchange", "NASDAQ"),
                            "company_name": quote.get("name", symbol),
                            "price": str(quote.get("price", 0.0)),
                            "change": str(quote.get("change", 0.0)),
                            "change_percent": f"{quote.get('changesPercentage', 0.0):.2f}%",
                            "currency": "USD",
                            "volume": str(quote.get("volume", 0)),
                            "source": "financial_modeling_prep",
                            "timestamp": datetime.now().isoformat()
                        }
                        self._set_cache(cache_key, result, 5)
                        return result
        except Exception as e:
            print(f"Financial Modeling Prep error for {symbol}: {e}")
        
        return None
    
    async def get_finnhub_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get quote from Finnhub"""
        cache_key = self._get_cache_key("fh_quote", symbol)
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            url = f"{self.base_urls['finnhub']}/quote"
            params = {
                "symbol": symbol,
                "token": self.api_keys["finnhub"]
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    quote = await response.json()
                    if quote:
                        result = {
                            "ticker": symbol,
                            "exchange": "NASDAQ",
                            "company_name": symbol,
                            "price": str(quote.get("c", 0.0)),  # Current price
                            "change": str(quote.get("d", 0.0)),  # Change
                            "change_percent": f"{quote.get('dp', 0.0):.2f}%",  # Percent change
                            "currency": "USD",
                            "volume": str(quote.get("vol", 0)),
                            "source": "finnhub",
                            "timestamp": datetime.now().isoformat()
                        }
                        self._set_cache(cache_key, result, 5)
                        return result
        except Exception as e:
            print(f"Finnhub error for {symbol}: {e}")
        
        return None
    
    async def get_eodhd_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get quote from EODHD"""
        cache_key = self._get_cache_key("eodhd_quote", symbol)
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            url = f"{self.base_urls['eodhd']}/real-time/{symbol}"
            params = {
                "api_token": self.api_keys["eodhd"],
                "fmt": "json"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if "close" in data:
                        result = {
                            "ticker": symbol,
                            "exchange": data.get("exchange", "NASDAQ"),
                            "company_name": symbol,
                            "price": str(data.get("close", 0.0)),
                            "change": str(data.get("change", 0.0)),
                            "change_percent": f"{data.get('change_p', 0.0):.2f}%",
                            "currency": data.get("currency", "USD"),
                            "volume": str(data.get("volume", 0)),
                            "source": "eodhd",
                            "timestamp": datetime.now().isoformat()
                        }
                        self._set_cache(cache_key, result, 5)
                        return result
        except Exception as e:
            print(f"EODHD error for {symbol}: {e}")
        
        return None
    
    async def get_groww_data(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Get data from Groww API"""
        cache_key = self._get_cache_key("groww", endpoint)
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            url = f"{self.base_urls['groww']}/{endpoint}"
            headers = {
                "Authorization": f"Bearer {self.api_keys['groww']['api_key']}",
                "Content-Type": "application/json"
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    self._set_cache(cache_key, data, 10)
                    return data
        except Exception as e:
            print(f"Groww error for {endpoint}: {e}")
        
        return None
    
    async def get_rapidapi_indian_data(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Get Indian market data from RapidAPI"""
        cache_key = self._get_cache_key("rapidapi", endpoint)
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            url = f"{self.base_urls['rapidapi']}/{endpoint}"
            headers = {
                "x-rapidapi-key": self.api_keys["rapidapi"]["key"],
                "x-rapidapi-host": self.api_keys["rapidapi"]["host"]
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    self._set_cache(cache_key, data, 10)
                    return data
        except Exception as e:
            print(f"RapidAPI error for {endpoint}: {e}")
        
        return None
    
    async def get_universal_quote(self, symbol: str, exchange: str = "NASDAQ") -> Dict[str, Any]:
        """Universal quote fetcher using all premium APIs"""
        
        # Try different APIs in order of preference
        api_sources = [
            ("financial_modeling_prep", self.get_fmp_quote),
            ("twelve_data", self.get_twelve_data_quote),
            ("alpha_vantage", self.get_alpha_vantage_quote),
            ("finnhub", self.get_finnhub_quote),
            ("eodhd", self.get_eodhd_quote),
        ]
        
        for source_name, fetch_func in api_sources:
            try:
                result = await fetch_func(symbol)
                if result and result.get("price") and result["price"] != "0.00":
                    print(f"✅ {source_name} success: {symbol} = ${result['price']}")
                    return result
            except Exception as e:
                print(f"❌ {source_name} failed for {symbol}: {e}")
                continue
        
        # Final fallback
        return {
            "ticker": symbol,
            "exchange": exchange,
            "company_name": symbol,
            "price": "0.00",
            "change": "0.00",
            "change_percent": "0.00%",
            "currency": "USD" if exchange != "NSE" else "INR",
            "source": "premium_fallback",
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_market_data_twelve_data(self, market_type: str) -> List[Dict[str, Any]]:
        """Get market data from Twelve Data"""
        cache_key = self._get_cache_key("td_market", market_type)
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            url = self.base_urls["twelve_data"]
            params = {
                "apikey": self.api_keys["twelve_data"],
                "interval": "1day",
                "outputsize": "100"
            }
            
            # Different endpoints for different market types
            if market_type == "gainers":
                params["exchange"] = "NASDAQ"
                params["sort"] = "desc"
            elif market_type == "losers":
                params["exchange"] = "NASDAQ"
                params["sort"] = "asc"
            elif market_type == "crypto":
                params["symbol"] = "BTC,ETH,SOL"
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if "values" in data:
                        items = []
                        for item in data["values"][:20]:
                            items.append({
                                "ticker": item.get("symbol", ""),
                                "name": item.get("symbol", ""),
                                "price": item.get("close", "0.00"),
                                "change": "0.00",  # Calculate from data
                                "change_percent": "0.00%",
                                "volume": item.get("volume", "0"),
                                "exchange": "NASDAQ",
                                "source": "twelve_data"
                            })
                        self._set_cache(cache_key, items, 10)
                        return items
        except Exception as e:
            print(f"Twelve Data market error: {e}")
        
        return []
    
    async def get_market_data_fmp(self, market_type: str) -> List[Dict[str, Any]]:
        """Get market data from Financial Modeling Prep"""
        cache_key = self._get_cache_key("fmp_market", market_type)
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            endpoints = {
                "gainers": "stock_market/gainers",
                "losers": "stock_market/losers",
                "most-active": "stock_market/most_actives",
                "crypto": "cryptocurrency"
            }
            
            if market_type not in endpoints:
                return []
            
            url = f"{self.base_urls['financial_modeling_prep']}/{endpoints[market_type]}"
            params = {"apikey": self.api_keys["financial_modeling_prep"]}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    items = []
                    for item in data[:20]:
                        items.append({
                            "ticker": item.get("ticker", ""),
                            "name": item.get("companyName", item.get("name", "")),
                            "price": str(item.get("price", 0.0)),
                            "change": str(item.get("change", 0.0)),
                            "change_percent": f"{item.get('changesPercentage', 0.0):.2f}%",
                            "volume": str(item.get("volume", 0)),
                            "exchange": item.get("exchange", "NASDAQ"),
                            "source": "financial_modeling_prep"
                        })
                    self._set_cache(cache_key, items, 10)
                    return items
        except Exception as e:
            print(f"Financial Modeling Prep market error: {e}")
        
        return []
    
    async def get_indian_market_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get comprehensive Indian market data"""
        try:
            # Get data from RapidAPI
            nse_data = await self.get_rapidapi_indian_data("nse/gainers")
            bse_data = await self.get_rapidapi_indian_data("bse/gainers")
            
            # Get data from Groww
            groww_data = await self.get_groww_data("market/gainers")
            
            return {
                "nse_gainers": self._process_indian_data(nse_data, "NSE"),
                "nse_losers": self._process_indian_data(bse_data, "BSE"),
                "nse_active": self._process_indian_data(groww_data, "NSE")
            }
        except Exception as e:
            print(f"Indian market data error: {e}")
            return {}
    
    def _process_indian_data(self, data: Dict[str, Any], exchange: str) -> List[Dict[str, Any]]:
        """Process Indian market data"""
        if not data:
            return []
        
        items = []
        for item in data.get("data", [])[:20]:
            items.append({
                "ticker": item.get("symbol", ""),
                "name": item.get("name", ""),
                "price": str(item.get("price", 0.0)),
                "change": str(item.get("change", 0.0)),
                "change_percent": f"{item.get('changePercent', 0.0):.2f}%",
                "volume": str(item.get("volume", 0)),
                "exchange": exchange,
                "currency": "INR",
                "source": "indian_premium_api"
            })
        
        return items

# Global premium API manager
premium_api = PremiumAPIManager()
