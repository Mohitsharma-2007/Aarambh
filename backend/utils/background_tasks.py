"""
Background Task Manager for Finance API
Handles automatic data refresh every 10 seconds
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any
from scrapers.universal_finance import get_quote_universal, get_market_universal
from scrapers.ai_finance_fetcher import ai_fetcher

class BackgroundTaskManager:
    """Manages background tasks for data refresh"""
    
    def __init__(self):
        self.running = False
        self.tasks = []
        self.data_cache = {}
        self.last_update = {}
        
    async def start_background_tasks(self):
        """Start all background tasks"""
        if self.running:
            return
        
        self.running = True
        
        # Start market data refresh task
        market_task = asyncio.create_task(self.refresh_market_data())
        self.tasks.append(market_task)
        
        # Start stock quotes refresh task
        quotes_task = asyncio.create_task(self.refresh_popular_quotes())
        self.tasks.append(quotes_task)
        
        print("Background tasks started - refreshing every 10 seconds")
    
    async def stop_background_tasks(self):
        """Stop all background tasks"""
        self.running = False
        
        for task in self.tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self.tasks.clear()
        print("Background tasks stopped")
    
    async def refresh_market_data(self):
        """Refresh market data every 10 seconds"""
        sections = [
            "indexes", "gainers", "losers", "most-active", 
            "crypto", "nse-gainers", "nse-losers", "nse-active"
        ]
        
        while self.running:
            try:
                timestamp = datetime.now().isoformat()
                
                # Refresh all market sections
                for section in sections:
                    try:
                        data = await get_market_universal(section)
                        if data and data.get("items"):
                            cache_key = f"market_{section}"
                            self.data_cache[cache_key] = {
                                "data": data,
                                "timestamp": timestamp,
                                "source": data.get("source", "unknown")
                            }
                            self.last_update[cache_key] = timestamp
                    except Exception as e:
                        print(f"Error refreshing {section}: {e}")
                        # Use AI fallback
                        try:
                            async with ai_fetcher as ai:
                                ai_data = await ai.get_market_data_universal(section)
                                if ai_data and ai_data.get("items"):
                                    cache_key = f"market_{section}"
                                    self.data_cache[cache_key] = {
                                        "data": ai_data,
                                        "timestamp": timestamp,
                                        "source": "ai_powered"
                                    }
                                    self.last_update[cache_key] = timestamp
                        except Exception as ai_e:
                            print(f"AI fallback failed for {section}: {ai_e}")
                
                print(f"Market data refreshed at {timestamp}")
                await asyncio.sleep(10)  # Wait 10 seconds
                
            except Exception as e:
                print(f"Background market refresh error: {e}")
                await asyncio.sleep(10)
    
    async def refresh_popular_quotes(self):
        """Refresh popular stock quotes every 10 seconds"""
        popular_stocks = [
            ("AAPL", "NASDAQ"),
            ("MSFT", "NASDAQ"),
            ("GOOGL", "NASDAQ"),
            ("TSLA", "NASDAQ"),
            ("RELIANCE.NS", "NSE"),
            ("TCS.NS", "NSE"),
            ("HDFCBANK.NS", "NSE"),
            ("INFY.NS", "NSE")
        ]
        
        while self.running:
            try:
                timestamp = datetime.now().isoformat()
                
                # Refresh all popular stocks
                for ticker, exchange in popular_stocks:
                    try:
                        data = await get_quote_universal(ticker, exchange)
                        if data and data.get("price"):
                            cache_key = f"quote_{ticker}_{exchange}"
                            self.data_cache[cache_key] = {
                                "data": data,
                                "timestamp": timestamp,
                                "source": data.get("source", "unknown")
                            }
                            self.last_update[cache_key] = timestamp
                    except Exception as e:
                        print(f"Error refreshing {ticker}: {e}")
                        # Use AI fallback
                        try:
                            async with ai_fetcher as ai:
                                ai_data = await ai.get_stock_quote_universal(ticker, exchange)
                                if ai_data and ai_data.get("price"):
                                    cache_key = f"quote_{ticker}_{exchange}"
                                    self.data_cache[cache_key] = {
                                        "data": ai_data,
                                        "timestamp": timestamp,
                                        "source": "ai_powered"
                                    }
                                    self.last_update[cache_key] = timestamp
                        except Exception as ai_e:
                            print(f"AI fallback failed for {ticker}: {ai_e}")
                
                print(f"Stock quotes refreshed at {timestamp}")
                await asyncio.sleep(10)  # Wait 10 seconds
                
            except Exception as e:
                print(f"Background quotes refresh error: {e}")
                await asyncio.sleep(10)
    
    def get_cached_data(self, cache_key: str) -> Dict[str, Any]:
        """Get cached data"""
        return self.data_cache.get(cache_key, {})
    
    def get_market_data(self, section: str) -> Dict[str, Any]:
        """Get cached market data"""
        cache_key = f"market_{section}"
        cached = self.data_cache.get(cache_key, {})
        
        if not cached:
            # Return empty data if no cache
            return {
                "section": section,
                "title": section.replace("-", " ").title(),
                "count": 0,
                "items": [],
                "source": "no_data",
                "timestamp": datetime.now().isoformat()
            }
        
        return cached["data"]
    
    def get_quote_data(self, ticker: str, exchange: str = "NASDAQ") -> Dict[str, Any]:
        """Get cached quote data"""
        cache_key = f"quote_{ticker}_{exchange}"
        cached = self.data_cache.get(cache_key, {})
        
        if not cached:
            # Return empty data if no cache
            return {
                "ticker": ticker,
                "exchange": exchange,
                "company_name": ticker,
                "price": "0.00",
                "change": "0.00",
                "change_percent": "0.00%",
                "currency": "USD" if exchange != "NSE" else "INR",
                "source": "no_data",
                "timestamp": datetime.now().isoformat()
            }
        
        return cached["data"]
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get cache status information"""
        return {
            "total_cached_items": len(self.data_cache),
            "running": self.running,
            "last_updates": self.last_update,
            "cache_keys": list(self.data_cache.keys())
        }

# Global instance
background_manager = BackgroundTaskManager()
