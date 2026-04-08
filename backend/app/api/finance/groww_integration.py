"""
Groww API Integration using official Python SDK
This replaces mock data with real Groww API calls
"""

from growwapi import GrowwAPI
import os
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

class GrowwIntegration:
    """Real Groww API integration using official SDK"""
    
    def __init__(self):
        # Use environment variables for API credentials
        self.api_key = os.getenv("GROWW_API_KEY", "YOUR_API_KEY")
        self.secret = os.getenv("GROWW_API_SECRET", "YOUR_API_SECRET")
        self.totp_secret = os.getenv("GROWW_TOTP_SECRET", "YOUR_TOTP_SECRET")
        
        if not all([self.api_key, self.secret]):
            print("⚠️  Groww API credentials not configured in environment variables")
            print("Please set GROWW_API_KEY and GROWW_API_SECRET or GROWW_TOTP_SECRET")
    
    async def get_access_token(self) -> Optional[str]:
        """Get access token using API key and secret"""
        try:
            if self.totp_secret:
                # Use TOTP flow
                import pyotp
                totp = pyotp.TOTP(self.totp_secret)
                current_totp = totp.now()
                
                print(f"🔐 TOTP Code: {current_totp}")
                access_token = GrowwAPI.get_access_token(
                    api_key=self.api_key,
                    totp=current_totp
                )
            else:
                # Use API key and secret flow
                access_token = GrowwAPI.get_access_token(
                    api_key=self.api_key,
                    secret=self.secret
                )
            
            print("✅ Groww API access token obtained successfully")
            return access_token
        except Exception as e:
            print(f"❌ Error getting Groww access token: {str(e)}")
            return None
    
    async def initialize_client(self, access_token: str) -> Optional[GrowwAPI]:
        """Initialize Groww API client"""
        try:
            groww = GrowwAPI(access_token=access_token)
            print("✅ Groww API client initialized successfully")
            return groww
        except Exception as e:
            print(f"❌ Error initializing Groww client: {str(e)}")
            return None
    
    async def get_stock_quote(self, symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
        """Get real-time stock quote using Groww API"""
        try:
            access_token = await self.get_access_token()
            if not access_token:
                return {"error": "Failed to get access token", "symbol": symbol}
            
            groww = await self.initialize_client(access_token)
            if not groww:
                return {"error": "Failed to initialize client", "symbol": symbol}
            
            # Get quote using Groww API
            quote_response = await asyncio.to_thread(
                groww.get_quote,
                symbol=symbol,
                exchange_segment=exchange
            )
            
            if quote_response and hasattr(quote_response, 'data'):
                quote_data = quote_response.data
                return {
                    "symbol": symbol,
                    "price": getattr(quote_data, 'ltp', None),
                    "change": getattr(quote_data, 'change', 0),
                    "change_percent": getattr(quote_data, 'change_percentage', 0),
                    "volume": getattr(quote_data, 'volume', 0),
                    "high": getattr(quote_data, 'high', None),
                    "low": getattr(quote_data, 'low', None),
                    "open": getattr(quote_data, 'open', None),
                    "source": "groww_api",
                    "exchange": exchange
                }
            else:
                return {"error": "No quote data available", "symbol": symbol}
                
        except Exception as e:
            print(f"❌ Error getting stock quote: {str(e)}")
            return {"error": str(e), "symbol": symbol}
    
    async def get_company_profile(self, symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
        """Get company profile using Groww API"""
        try:
            access_token = await self.get_access_token()
            if not access_token:
                return {"error": "Failed to get access token", "symbol": symbol}
            
            groww = await self.initialize_client(access_token)
            if not groww:
                return {"error": "Failed to initialize client", "symbol": symbol}
            
            # Get company info using Groww API
            profile_response = await asyncio.to_thread(
                groww.get_company_info,
                symbol=symbol,
                exchange_segment=exchange
            )
            
            if profile_response and hasattr(profile_response, 'data'):
                company_data = profile_response.data
                return {
                    "symbol": symbol,
                    "name": getattr(company_data, 'company_name', None),
                    "description": getattr(company_data, 'description', None),
                    "sector": getattr(company_data, 'sector', None),
                    "industry": getattr(company_data, 'industry', None),
                    "website": getattr(company_data, 'website', None),
                    "logo": getattr(company_data, 'logo', None),
                    "country": getattr(company_data, 'country', None),
                    "ceo": getattr(company_data, 'ceo', None),
                    "employees": getattr(company_data, 'employees', None),
                    "market_cap": getattr(company_data, 'market_cap', None),
                    "source": "groww_api",
                    "exchange": exchange
                }
            else:
                return {"error": "No profile data available", "symbol": symbol}
                
        except Exception as e:
            print(f"❌ Error getting company profile: {str(e)}")
            return {"error": str(e), "symbol": symbol}
    
    async def get_chart_data(self, symbol: str, exchange: str = "NSE", interval: str = "5m") -> Dict[str, Any]:
        """Get historical chart data using Groww API"""
        try:
            access_token = await self.get_access_token()
            if not access_token:
                return {"error": "Failed to get access token", "symbol": symbol}
            
            groww = await self.initialize_client(access_token)
            if not groww:
                return {"error": "Failed to initialize client", "symbol": symbol}
            
            # Get chart data using Groww API
            chart_response = await asyncio.to_thread(
                groww.get_historical_data,
                symbol=symbol,
                exchange_segment=exchange,
                interval=interval
            )
            
            if chart_response and hasattr(chart_response, 'data'):
                chart_data = chart_response.data
                # Transform to expected format
                formatted_data = []
                if isinstance(chart_data, list):
                    for point in chart_data:
                        formatted_data.append({
                            "date": getattr(point, 'date', ''),
                            "open": getattr(point, 'open', 0),
                            "high": getattr(point, 'high', 0),
                            "low": getattr(point, 'low', 0),
                            "close": getattr(point, 'close', 0),
                            "volume": getattr(point, 'volume', 0),
                        })
                
                return {
                    "chart_data": formatted_data,
                    "source": "groww_api"
                }
            else:
                return {"error": "No chart data available", "symbol": symbol}
                
        except Exception as e:
            print(f"❌ Error getting chart data: {str(e)}")
            return {"error": str(e), "symbol": symbol}
    
    async def get_news(self, symbol: str) -> Dict[str, Any]:
        """Get news using Groww API"""
        try:
            access_token = await self.get_access_token()
            if not access_token:
                return {"error": "Failed to get access token", "symbol": symbol}
            
            groww = await self.initialize_client(access_token)
            if not groww:
                return {"error": "Failed to initialize client", "symbol": symbol}
            
            # Get news using Groww API (if available)
            # Note: Groww API might not have a dedicated news endpoint
            # We'll return empty for now
            return {
                "articles": [],
                "source": "groww_api"
            }
                
        except Exception as e:
            print(f"❌ Error getting news: {str(e)}")
            return {"error": str(e), "symbol": symbol}
    
    async def get_financials(self, symbol: str) -> Dict[str, Any]:
        """Get financial data using Groww API"""
        try:
            access_token = await self.get_access_token()
            if not access_token:
                return {"error": "Failed to get access token", "symbol": symbol}
            
            groww = await self.initialize_client(access_token)
            if not groww:
                return {"error": "Failed to initialize client", "symbol": symbol}
            
            # Get financial data using Groww API (if available)
            # Note: Groww API might not have dedicated financials endpoint
            # We'll return empty for now
            return {
                "revenue": None,
                "net_income": None,
                "total_assets": None,
                "total_liabilities": None,
                "source": "groww_api"
            }
                
        except Exception as e:
            print(f"❌ Error getting financials: {str(e)}")
            return {"error": str(e), "symbol": symbol}
