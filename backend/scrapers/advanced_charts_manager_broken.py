"""
Advanced Charts and Company Fundamentals Manager
Implements TradingView-like charts, comprehensive company data, and Groww API integration
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class AdvancedChartsManager:
    """Advanced charts and company fundamentals manager"""
    
    def __init__(self):
        self.session = None
        self.cache = {}
        self.cache_expiry = {}
        
        # Groww API configuration (active trial)
        self.groww_config = {
            "api_key": "eyJraWQiOiJaTUtjVXciLCJhbGciOiJFUzI1NiJ9.eyJleHAiOjI1NjI4OTE0NDgsImlhdCI6MTc3NDQ5MTQ0OCwibmJmIjoxNzc0NDkxNDQ4LCJzdWIiOiJ7XCJ0b2tlblJlZklkXCI6XCJkNjE1YWYwNy0zMTE5LTRmYWMtYTVmYy1hNDIwNWI4MmEwNzhcIixcInZlbmRvckludGVncmF0aW9uS2V5XCI6XCJlMzFmZjIzYjA4NmI0MDZjODg3NGIyZjZkODQ5NTMxM1wiLFwidXNlckFjY291bnRJZFwiOlwiOTgwNzUxNTYtOTI1MS00NjQ3LWE3MDItYzM0M2QxMDY4ZmU3XCIsXCJkZXZpY2VJZFwiOlwiMDdmYjYyZDktNmUxYS01YzI4LWJmN2MtYzE2NjZmRhYTBhXCIsXCJzZXNzaW9uSWRcIjpcIjlkZTY4Zjg2LTVhZjEtNGY1YS04NzU0LTgzNmRlNGUxODU2ZVwiLFwiYWRkaXRpb25hbERhdGFcIjpcIno1NC9NZzltdjE2WXdmb0gvS0EwYlAwU2ljZTkxL0toOUJFK1JKZWh3bXhSTkczdTlLa2pWZDNoWjU1ZStNZERhWXBOVi9UOUxIRmtQejFFQisybTdRPT1cIixcInJvbGVcIjpcImF1dGgtdG90cFwiLFwic291cmNlSXBBZGRyZXNzXCI6XCIyNDA5OjQwZDI6NGU6NWI2MjpjZGI1OjcwZWE6Y2RkYjpkMjFkLDE3Mi43MS4xOTguOTUsMzUuMjQxLjIzLjEyM1wiLFwidHdvRmFFeHBpcnlUc1wiOjI1NjI4OTE0NDg4MzUsXCJ2ZW5kb3JOYW1lXCI6XCJncm93d0FwaVwifSIsImlzcyI6ImFwZXgtYXV0aC1wcm9kLWFwcCJ9.R0SoRTG52YyMPaDmbvxzuFw5RskIGsHSPP1KUyqgHDB_flcbzaXDATqw7EZGQTYRotxbI0sXRBy7kJZTUpWgg",
            "secret": "e#!gD1kMm&tT_kmTfj_2Tg47Uw%TF4@R",
            "base_url": "https://groww.in/v1/api"
        }
        
        # Other premium APIs
        self.api_keys = {
            "alpha_vantage": "EPVBVC6GA4DTM3J0",
            "financial_modeling_prep": "cjD3BCLxnYk8hBgcEpeH702txwLXc6TU",
            "finnhub": "d7065m1r01qtb4r9kju0d7065m1r01qtb4r9kjug",
            "twelve_data": "9fafee9808984cd3a3c949dfc9b38ce5",
            "eodhd": "69c48c1f5a4b59.80000680"
        }
        
        self.base_urls = {
            "groww": "https://groww.in/v1/api",
            "alpha_vantage": "https://www.alphavantage.co/query",
            "financial_modeling_prep": "https://financialmodelingprep.com/api/v3",
            "finnhub": "https://finnhub.io/api/v1",
            "twelve_data": "https://api.twelvedata.com",
            "eodhd": "https://eodhd.com/api"
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Mozilla/5.0 (compatible; AdvancedChartsBot/1.0)'}
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
    
    async def get_groww_chart_data(self, symbol: str, interval: str = "1d", range: str = "1mo") -> Optional[Dict[str, Any]]:
        """Get chart data from Groww API"""
        cache_key = self._get_cache_key("groww_chart", symbol, interval=interval, range=range)
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            url = f"{self.base_urls['groww']}/stocks/charts"
            params = {
                "symbol": symbol,
                "interval": interval,
                "range": range
            }
            
            headers = {
                "Authorization": f"Bearer {self.groww_config['api_key']}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'Mozilla/5.0 (compatible; AdvancedChartsBot/1.0)'}
            ) as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "data" in data:
                            chart_data = self._process_chart_data(data["data"])
                            self._set_cache(cache_key, chart_data, 5)
                            return chart_data
        except Exception as e:
            print(f"Groww chart error for {symbol}: {e}")
        
        return None
    
    async def get_groww_company_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive company profile from Groww"""
        cache_key = self._get_cache_key("groww_profile", symbol)
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            url = f"{self.base_urls['groww']}/stocks/profile"
            params = {"symbol": symbol}
            
            headers = {
                "Authorization": f"Bearer {self.groww_config['api_key']}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'Mozilla/5.0 (compatible; AdvancedChartsBot/1.0)'}
            ) as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "data" in data:
                            profile = self._process_company_profile(data["data"])
                            self._set_cache(cache_key, profile, 30)
                            return profile
        except Exception as e:
            print(f"Groww profile error for {symbol}: {e}")
        
        return None
    
    async def get_groww_financials(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get financial statements from Groww"""
        cache_key = self._get_cache_key("groww_financials", symbol)
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            url = f"{self.base_urls['groww']}/stocks/financials"
            params = {"symbol": symbol}
            
            headers = {
                "Authorization": f"Bearer {self.groww_config['api_key']}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'Mozilla/5.0 (compatible; AdvancedChartsBot/1.0)'}
            ) as session:
                async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if "data" in data:
                        financials = self._process_financial_statements(data["data"])
                        self._set_cache(cache_key, financials, 60)
                        return financials
        except Exception as e:
            print(f"Groww financials error for {symbol}: {e}")
        
        return None
    
    async def get_groww_technical_indicators(self, symbol: str, indicators: List[str]) -> Optional[Dict[str, Any]]:
        """Get technical indicators from Groww"""
        cache_key = self._get_cache_key("groww_indicators", symbol, indicators=",".join(indicators))
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            url = f"{self.base_urls['groww']}/stocks/indicators"
            params = {
                "symbol": symbol,
                "indicators": ",".join(indicators)
            }
            
            headers = {
                "Authorization": f"Bearer {self.groww_config['api_key']}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'Mozilla/5.0 (compatible; AdvancedChartsBot/1.0)'}
            ) as session:
                async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if "data" in data:
                        indicators_data = self._process_technical_indicators(data["data"])
                        self._set_cache(cache_key, indicators_data, 10)
                        return indicators_data
        except Exception as e:
            print(f"Groww indicators error for {symbol}: {e}")
        
        return None
    
    async def get_comprehensive_company_data(self, symbol: str) -> Dict[str, Any]:
        """Get complete company data from multiple sources"""
        
        result = {
            "symbol": symbol,
            "profile": None,
            "financials": None,
            "chart_data": None,
            "technical_indicators": None,
            "news": None,
            "analyst_ratings": None,
            "insider_trading": None,
            "competitors": None,
            "sources": []
        }
        
        # Use a single session for all requests
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Mozilla/5.0 (compatible; AdvancedChartsBot/1.0)'}
        ) as session:
            self.session = session
            
            # Try Groww first (active trial)
            try:
                # Get company profile
                profile = await self.get_groww_company_profile(symbol)
                if profile:
                    result["profile"] = profile
                    result["sources"].append("groww_profile")
                
                # Get financial statements
                financials = await self.get_groww_financials(symbol)
                if financials:
                    result["financials"] = financials
                    result["sources"].append("groww_financials")
                
                # Get chart data
                chart_data = await self.get_groww_chart_data(symbol)
                if chart_data:
                    result["chart_data"] = chart_data
                    result["sources"].append("groww_chart")
                
                # Get technical indicators
                indicators = ["RSI", "MACD", "Bollinger", "SMA", "EMA", "Volume"]
                technical_data = await self.get_groww_technical_indicators(symbol, indicators)
                if technical_data:
                    result["technical_indicators"] = technical_data
                    result["sources"].append("groww_indicators")
            except Exception as e:
                print(f"Groww comprehensive data error for {symbol}: {e}")
            
            # Fallback to other APIs for missing data
            if not result["profile"]:
                try:
                    profile = await self.get_fmp_company_profile(symbol)
                    if profile:
                        result["profile"] = profile
                        result["sources"].append("fmp_profile")
                except Exception as e:
                    print(f"FMP profile fallback error for {symbol}: {e}")
            
            if not result["financials"]:
                try:
                    financials = await self.get_fmp_financials(symbol)
                    if financials:
                        result["financials"] = financials
                        result["sources"].append("fmp_financials")
                except Exception as e:
                    print(f"FMP financials fallback error for {symbol}: {e}")
            
            if not result["chart_data"]:
                try:
                    chart_data = await self.get_twelve_data_chart(symbol)
                    if chart_data:
                        result["chart_data"] = chart_data
                        result["sources"].append("twelve_chart")
                except Exception as e:
                    print(f"Twelve Data chart fallback error for {symbol}: {e}")
            
            if not result["technical_indicators"]:
                try:
                    indicators_data = await self.get_alpha_vantage_indicators(symbol)
                    if indicators_data:
                        result["technical_indicators"] = indicators_data
                        result["sources"].append("alpha_vantage_indicators")
                except Exception as e:
                    print(f"Alpha Vantage indicators fallback error for {symbol}: {e}")
        
        return result
    
    def _process_chart_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process chart data for TradingView-like display"""
        return {
            "candlestick": data.get("candlestick", []),
            "ohlc": data.get("ohlc", []),
            "volume": data.get("volume", []),
            "vwap": data.get("vwap", []),
            "moving_averages": data.get("ma", {}),
            "timestamps": data.get("timestamps", []),
            "high": data.get("high", []),
            "low": data.get("low", []),
            "open": data.get("open", []),
            "close": data.get("close", []),
            "adjusted_close": data.get("adj_close", []),
            "source": "groww"
        }
    
    def _process_company_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process company profile data"""
        return {
            "symbol": data.get("symbol", ""),
            "name": data.get("name", ""),
            "description": data.get("description", ""),
            "sector": data.get("sector", ""),
            "industry": data.get("industry", ""),
            "market_cap": data.get("market_cap", 0),
            "enterprise_value": data.get("enterprise_value", 0),
            "pe_ratio": data.get("pe_ratio", 0),
            "pb_ratio": data.get("pb_ratio", 0),
            "dividend_yield": data.get("dividend_yield", 0),
            "eps": data.get("eps", 0),
            "revenue": data.get("revenue", 0),
            "net_income": data.get("net_income", 0),
            "book_value": data.get("book_value", 0),
            "debt_to_equity": data.get("debt_to_equity", 0),
            "roe": data.get("roe", 0),
            "roa": data.get("roa", 0),
            "current_ratio": data.get("current_ratio", 0),
            "quick_ratio": data.get("quick_ratio", 0),
            "employees": data.get("employees", 0),
            "website": data.get("website", ""),
            "ceo": data.get("ceo", ""),
            "headquarters": data.get("headquarters", ""),
            "founded": data.get("founded", ""),
            "exchange": data.get("exchange", ""),
            "currency": data.get("currency", "USD"),
            "country": data.get("country", ""),
            "listing_date": data.get("listing_date", ""),
            "beta": data.get("beta", 1.0),
            "analyst_rating": data.get("analyst_rating", ""),
            "target_price": data.get("target_price", 0),
            "high_52w": data.get("high_52w", 0),
            "low_52w": data.get("low_52w", 0),
            "source": "groww"
        }
    
    def _process_financial_statements(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process financial statements data"""
        return {
            "income_statement": data.get("income_statement", {}),
            "balance_sheet": data.get("balance_sheet", {}),
            "cash_flow": data.get("cash_flow", {}),
            "ratios": data.get("ratios", {}),
            "key_metrics": data.get("key_metrics", {}),
            "growth_rates": data.get("growth_rates", {}),
            "profitability": data.get("profitability", {}),
            "liquidity": data.get("liquidity", {}),
            "solvency": data.get("solvency", {}),
            "efficiency": data.get("efficiency", {}),
            "valuation": data.get("valuation", {}),
            "source": "groww"
        }
    
    def _process_technical_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process technical indicators data"""
        return {
            "rsi": data.get("rsi", {}),
            "macd": data.get("macd", {}),
            "bollinger_bands": data.get("bollinger", {}),
            "moving_averages": data.get("ma", {}),
            "exponential_moving_averages": data.get("ema", {}),
            "volume_indicators": data.get("volume", {}),
            "momentum": data.get("momentum", {}),
            "volatility": data.get("volatility", {}),
            "trend": data.get("trend", {}),
            "oscillators": data.get("oscillators", {}),
            "source": "groww"
        }
    
    async def get_fmp_company_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get company profile from Financial Modeling Prep"""
        cache_key = self._get_cache_key("fmp_profile", symbol)
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            url = f"{self.base_urls['financial_modeling_prep']}/profile/{symbol}"
            params = {"apikey": self.api_keys["financial_modeling_prep"]}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        profile = {
                            "symbol": data.get("symbol", symbol),
                            "name": data.get("companyName", ""),
                            "description": data.get("description", ""),
                            "sector": data.get("sector", ""),
                            "industry": data.get("industry", ""),
                            "market_cap": data.get("mktCap", 0),
                            "enterprise_value": data.get("enterpriseValue", 0),
                            "pe_ratio": data.get("pe", 0),
                            "pb_ratio": data.get("pb", 0),
                            "dividend_yield": data.get("lastDividend", 0),
                            "eps": data.get("eps", 0),
                            "website": data.get("website", ""),
                            "ceo": data.get("ceo", ""),
                            "employees": data.get("fullTimeEmployees", 0),
                            "exchange": data.get("exchange", ""),
                            "currency": data.get("currency", "USD"),
                            "country": data.get("country", ""),
                            "beta": data.get("beta", 1.0),
                            "analyst_rating": data.get("analystRating", ""),
                            "target_price": data.get("priceTarget", 0),
                            "high_52w": data.get("high", 0),
                            "low_52w": data.get("low", 0),
                            "source": "financial_modeling_prep"
                        }
                        self._set_cache(cache_key, profile, 30)
                        return profile
        except Exception as e:
            print(f"FMP profile error for {symbol}: {e}")
        
        return None
    
    async def get_fmp_financials(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get financial statements from Financial Modeling Prep"""
        cache_key = self._get_cache_key("fmp_financials", symbol)
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            # Get income statement
            income_url = f"{self.base_urls['financial_modeling_prep']}/income-statement/{symbol}"
            params = {"apikey": self.api_keys["financial_modeling_prep"]}
            
            async with self.session.get(income_url, params=params) as response:
                if response.status == 200:
                    income_data = await response.json()
                    
                    # Get balance sheet
                    balance_url = f"{self.base_urls['financial_modeling_prep']}/balance-sheet-statement/{symbol}"
                    async with self.session.get(balance_url, params=params) as balance_response:
                        if balance_response.status == 200:
                            balance_data = await balance_response.json()
                            
                            # Get cash flow
                            cashflow_url = f"{self.base_urls['financial_modeling_prep']}/cash-flow-statement/{symbol}"
                            async with self.session.get(cashflow_url, params=params) as cashflow_response:
                                if cashflow_response.status == 200:
                                    cashflow_data = await cashflow_response.json()
                                    
                                    financials = {
                                        "income_statement": income_data[0] if income_data else {},
                                        "balance_sheet": balance_data[0] if balance_data else {},
                                        "cash_flow": cashflow_data[0] if cashflow_data else {},
                                        "source": "financial_modeling_prep"
                                    }
                                    
                                    self._set_cache(cache_key, financials, 60)
                                    return financials
        except Exception as e:
            print(f"FMP financials error for {symbol}: {e}")
        
        return None
    
    async def get_twelve_data_chart(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get chart data from Twelve Data"""
        cache_key = self._get_cache_key("twelve_chart", symbol)
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            url = self.base_urls["twelve_data"]
            params = {
                "symbol": symbol,
                "interval": "1day",
                "outputsize": "365",
                "apikey": self.api_keys["twelve_data"]
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if "values" in data:
                        values = data["values"]
                        chart_data = {
                            "candlestick": [],
                            "ohlc": [],
                            "volume": [],
                            "timestamps": [],
                            "high": [],
                            "low": [],
                            "open": [],
                            "close": [],
                            "source": "twelve_data"
                        }
                        
                        for item in reversed(values):
                            chart_data["timestamps"].append(item.get("datetime", ""))
                            chart_data["open"].append(float(item.get("open", 0)))
                            chart_data["high"].append(float(item.get("high", 0)))
                            chart_data["low"].append(float(item.get("low", 0)))
                            chart_data["close"].append(float(item.get("close", 0)))
                            chart_data["volume"].append(int(item.get("volume", 0)))
                            
                            # Create candlestick format
                            chart_data["candlestick"].append({
                                "time": item.get("datetime", ""),
                                "open": float(item.get("open", 0)),
                                "high": float(item.get("high", 0)),
                                "low": float(item.get("low", 0)),
                                "close": float(item.get("close", 0)),
                                "volume": int(item.get("volume", 0))
                            })
                        
                        self._set_cache(cache_key, chart_data, 5)
                        return chart_data
        except Exception as e:
            print(f"Twelve Data chart error for {symbol}: {e}")
        
        return None
    
    async def get_alpha_vantage_indicators(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get technical indicators from Alpha Vantage"""
        cache_key = self._get_cache_key("av_indicators", symbol)
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            url = self.base_urls["alpha_vantage"]
            params = {
                "function": "OVERLAP",
                "symbol": symbol,
                "interval": "daily",
                "time_period": "14",
                "series_type": "close",
                "apikey": self.api_keys["alpha_vantage"]
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if "Technical Analysis: Overlap" in data:
                        analysis = data["Technical Analysis: Overlap"]
                        indicators_data = {
                            "sma": analysis.get("SMA", {}),
                            "ema": analysis.get("EMA", {}),
                            "wma": analysis.get("WMA", {}),
                            "source": "alpha_vantage"
                        }
                        self._set_cache(cache_key, indicators_data, 10)
                        return indicators_data
        except Exception as e:
            print(f"Alpha Vantage indicators error for {symbol}: {e}")
        
        return None

# Global advanced charts manager
advanced_charts = AdvancedChartsManager()
