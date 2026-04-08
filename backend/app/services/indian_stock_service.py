"""
Indian Stock API Service - Fetches Indian market data from IndianAPI.in
API Key: sk-live-dAo38cJjbWyutmX4YdJLobfTP8uHk5nUYBJbg0zY
"""

import httpx
from typing import Optional, Dict, Any

INDIAN_API_KEY = "sk-live-dAo38cJjbWyutmX4YdJLobfTP8uHk5nUYBJbg0zY"
INDIAN_API_BASE = "https://indianapi.in/sandbox/indian-stock-market"


class IndianStockService:
    """Service to fetch Indian stock market data"""
    
    def __init__(self):
        self.api_key = INDIAN_API_KEY
        self.base_url = INDIAN_API_BASE
        self.client = httpx.AsyncClient(timeout=30.0)
        self.headers = {"X-Api-Key": self.api_key}
    
    async def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock data for Indian companies"""
        try:
            url = f"{self.base_url}/stock"
            params = {"name": symbol}
            response = await self.client.get(url, params=params, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Indian API Stock Error: {e}")
            return None
    
    async def get_nifty50_data(self) -> Optional[Dict[str, Any]]:
        """Get NIFTY 50 index data"""
        try:
            url = f"{self.base_url}/index/nifty50"
            response = await self.client.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Indian API Nifty Error: {e}")
            return None
    
    async def get_sensex_data(self) -> Optional[Dict[str, Any]]:
        """Get BSE Sensex data"""
        try:
            url = f"{self.base_url}/index/sensex"
            response = await self.client.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Indian API Sensex Error: {e}")
            return None
    
    async def search_stocks(self, query: str) -> list:
        """Search Indian stocks"""
        try:
            url = f"{self.base_url}/search"
            params = {"q": query}
            response = await self.client.get(url, params=params, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                return data.get("stocks", [])
            return []
        except Exception as e:
            print(f"Indian API Search Error: {e}")
            return []


# Global instance
indian_stock_service = IndianStockService()
