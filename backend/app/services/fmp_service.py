"""
FMP API Service - Fetches real-time market data from Financial Modeling Prep
API Key: cjD3BCLxnYk8hBgcEpeH702txwLXc6TU
"""

import httpx
import os
from typing import Optional, List, Dict, Any
from fastapi import HTTPException

FMP_API_KEY = "cjD3BCLxnYk8hBgcEpeH702txwLXc6TU"
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"
FMP_STABLE_URL = "https://financialmodelingprep.com/stable"


class FMPService:
    """Service to fetch market data from FMP API"""
    
    def __init__(self):
        self.api_key = FMP_API_KEY
        self.base_url = FMP_BASE_URL
        self.stable_url = FMP_STABLE_URL
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time stock quote"""
        try:
            url = f"{self.stable_url}/quote"
            params = {"symbol": symbol, "apikey": self.api_key}
            response = await self.client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data[0] if data else None
            return None
        except Exception as e:
            print(f"FMP Quote Error: {e}")
            return None
    
    async def get_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get company profile"""
        try:
            url = f"{self.stable_url}/company-profile"
            params = {"symbol": symbol, "apikey": self.api_key}
            response = await self.client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data[0] if data else None
            return None
        except Exception as e:
            print(f"FMP Profile Error: {e}")
            return None
    
    async def get_income_statement(self, symbol: str, limit: int = 1) -> List[Dict[str, Any]]:
        """Get income statement data"""
        try:
            url = f"{self.base_url}/income-statement/{symbol}"
            params = {"limit": limit, "apikey": self.api_key}
            response = await self.client.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"FMP Income Statement Error: {e}")
            return []
    
    async def get_stock_news(self, symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get stock news"""
        try:
            url = f"{self.base_url}/stock_news"
            params = {"tickers": symbol, "limit": limit, "apikey": self.api_key}
            response = await self.client.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"FMP News Error: {e}")
            return []
    
    async def get_general_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get general market news"""
        try:
            url = f"{self.stable_url}/news/general-latest"
            params = {"apikey": self.api_key}
            response = await self.client.get(url, params=params)
            if response.status_code == 200:
                return response.json()[:limit]
            return []
        except Exception as e:
            print(f"FMP General News Error: {e}")
            return []
    
    async def get_stock_screener(self) -> List[Dict[str, Any]]:
        """Get list of active stocks"""
        try:
            url = f"{self.base_url}/stock-screener"
            params = {"apikey": self.api_key, "limit": 100}
            response = await self.client.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"FMP Screener Error: {e}")
            return []
    
    async def get_market_movers(self, type: str = "gainers") -> List[Dict[str, Any]]:
        """Get market movers - gainers, losers, most active"""
        try:
            endpoint_map = {
                "gainers": "stock_market/gainers",
                "losers": "stock_market/losers",
                "most-active": "stock_market/actives"
            }
            endpoint = endpoint_map.get(type, "stock_market/gainers")
            url = f"{self.base_url}/{endpoint}"
            params = {"apikey": self.api_key}
            response = await self.client.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"FMP Market Movers Error: {e}")
            return []
    
    async def get_cot_data(self, symbol: str = "EUR") -> Dict[str, Any]:
        """Get Commitment of Traders data"""
        try:
            # Using forex COT data endpoint
            url = f"{self.base_url}/cot/forex"
            params = {"apikey": self.api_key}
            response = await self.client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                # Filter for the requested symbol if provided
                if symbol:
                    filtered = [d for d in data if symbol.upper() in str(d.get('commodity', '')).upper()]
                    return {"symbol": symbol, "cot_data": filtered[:5]}
                return {"cot_data": data[:5]}
            return {"symbol": symbol, "cot_data": []}
        except Exception as e:
            print(f"FMP COT Error: {e}")
            return {"symbol": symbol, "cot_data": [], "error": str(e)}
    
    async def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """Search for stocks by name or ticker"""
        try:
            url = f"{self.base_url}/search"
            params = {"query": query, "apikey": self.api_key}
            response = await self.client.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"FMP Search Error: {e}")
            return []


# Global instance
fmp_service = FMPService()
