"""
Free API Stack Integration for AARAMBH
Uses yfinance + Twelve Data + Finnhub for complete free data coverage
"""

import yfinance as yf
import twelvedata as td
import finnhub
import os
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import pandas as pd

class FreeAPIStack:
    """Complete free API stack using yfinance + Twelve Data + Finnhub"""
    
    def __init__(self):
        # Twelve Data API key (free tier: 800 credits/day)
        self.td_api_key = os.getenv("TWELVEDATA_API_KEY", "demo")
        
        # Finnhub API key (free tier: 60 calls/min)
        self.finnhub_api_key = os.getenv("FINNHUB_API_KEY", "demo")
        
        # Initialize clients
        self.td_client = None
        self.finnhub_client = None
        
        if self.td_api_key and self.td_api_key != "demo":
            try:
                self.td_client = td.TDClient(apikey=self.td_api_key)
                print("✅ Twelve Data client initialized")
            except Exception as e:
                print(f"⚠️ Twelve Data client error: {str(e)}")
        
        if self.finnhub_api_key and self.finnhub_api_key != "demo":
            try:
                self.finnhub_client = finnhub.Client(api_key=self.finnhub_api_key)
                print("✅ Finnhub client initialized")
            except Exception as e:
                print(f"⚠️ Finnhub client error: {str(e)}")
    
    async def get_stock_quote(self, symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
        """Get real-time stock quote using yfinance (primary) + Twelve Data (fallback)"""
        try:
            # Format symbol for yfinance
            yf_symbol = symbol
            if exchange == "NSE" and not symbol.endswith(".NS"):
                yf_symbol = f"{symbol}.NS"
            elif exchange == "BSE" and not symbol.endswith(".BO"):
                yf_symbol = f"{symbol}.BO"
            
            # Primary: Use yfinance (free, no API key needed)
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            
            if info and 'regularMarketPrice' in info:
                return {
                    "symbol": symbol,
                    "price": info.get('regularMarketPrice', 0),
                    "change": info.get('regularMarketChange', 0),
                    "change_percent": info.get('regularMarketChangePercent', 0),
                    "volume": info.get('volume', 0),
                    "high": info.get('dayHigh', 0),
                    "low": info.get('dayLow', 0),
                    "open": info.get('open', 0),
                    "previous_close": info.get('previousClose', 0),
                    "market_cap": info.get('marketCap', 0),
                    "pe_ratio": info.get('trailingPE', 0),
                    "eps": info.get('trailingEps', 0),
                    "beta": info.get('beta', 0),
                    "dividend_yield": info.get('dividendYield', 0),
                    "52_week_high": info.get('fiftyTwoWeekHigh', 0),
                    "52_week_low": info.get('fiftyTwoWeekLow', 0),
                    "source": "yfinance",
                    "exchange": exchange
                }
            
            # Fallback: Try Twelve Data if yfinance fails
            if self.td_client:
                try:
                    td_quote = await asyncio.to_thread(
                        self.td_client.quote,
                        symbol=symbol,
                        exchange=exchange
                    )
                    
                    if td_quote:
                        return {
                            "symbol": symbol,
                            "price": float(td_quote.get('price', 0)),
                            "change": float(td_quote.get('change', 0)),
                            "change_percent": float(td_quote.get('percent_change', 0)),
                            "volume": int(td_quote.get('volume', 0)),
                            "high": float(td_quote.get('high', 0)),
                            "low": float(td_quote.get('low', 0)),
                            "open": float(td_quote.get('open', 0)),
                            "previous_close": float(td_quote.get('previous_close', 0)),
                            "source": "twelvedata",
                            "exchange": exchange
                        }
                except Exception as e:
                    print(f"⚠️ Twelve Data quote failed: {str(e)}")
            
            return {"error": "No quote data available", "symbol": symbol}
            
        except Exception as e:
            print(f"❌ Error getting stock quote: {str(e)}")
            return {"error": str(e), "symbol": symbol}
    
    async def get_company_profile(self, symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
        """Get company profile using yfinance (primary) + Finnhub (fallback)"""
        try:
            # Format symbol for yfinance
            yf_symbol = symbol
            if exchange == "NSE" and not symbol.endswith(".NS"):
                yf_symbol = f"{symbol}.NS"
            elif exchange == "BSE" and not symbol.endswith(".BO"):
                yf_symbol = f"{symbol}.BO"
            
            # Primary: Use yfinance
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            
            if info:
                return {
                    "symbol": symbol,
                    "name": info.get('longName', info.get('shortName', symbol)),
                    "description": info.get('longBusinessSummary', ''),
                    "sector": info.get('sector', ''),
                    "industry": info.get('industry', ''),
                    "website": info.get('website', ''),
                    "country": info.get('country', ''),
                    "currency": info.get('currency', ''),
                    "employees": info.get('fullTimeEmployees', 0),
                    "market_cap": info.get('marketCap', 0),
                    "enterprise_value": info.get('enterpriseValue', 0),
                    "pe_ratio": info.get('trailingPE', 0),
                    "pb_ratio": info.get('priceToBook', 0),
                    "ps_ratio": info.get('priceToSales', 0),
                    "ev_ebitda": info.get('enterpriseToEbitda', 0),
                    "dividend_yield": info.get('dividendYield', 0),
                    "beta": info.get('beta', 0),
                    "source": "yfinance",
                    "exchange": exchange
                }
            
            # Fallback: Try Finnhub
            if self.finnhub_client:
                try:
                    profile = await asyncio.to_thread(
                        self.finnhub_client.company_profile2,
                        symbol=symbol
                    )
                    
                    if profile:
                        return {
                            "symbol": symbol,
                            "name": profile.get('name', symbol),
                            "description": profile.get('description', ''),
                            "sector": profile.get('gics', ''),
                            "industry": profile.get('industry', ''),
                            "website": profile.get('weburl', ''),
                            "country": profile.get('country', ''),
                            "currency": profile.get('currency', ''),
                            "employees": profile.get('employeeCount', 0),
                            "market_cap": profile.get('marketCapitalization', 0),
                            "exchange": exchange,
                            "source": "finnhub"
                        }
                except Exception as e:
                    print(f"⚠️ Finnhub profile failed: {str(e)}")
            
            return {"error": "No profile data available", "symbol": symbol}
            
        except Exception as e:
            print(f"❌ Error getting company profile: {str(e)}")
            return {"error": str(e), "symbol": symbol}
    
    async def get_chart_data(self, symbol: str, exchange: str = "NSE", interval: str = "1d", period: str = "1y") -> Dict[str, Any]:
        """Get historical chart data using yfinance"""
        try:
            # Format symbol for yfinance
            yf_symbol = symbol
            if exchange == "NSE" and not symbol.endswith(".NS"):
                yf_symbol = f"{symbol}.NS"
            elif exchange == "BSE" and not symbol.endswith(".BO"):
                yf_symbol = f"{symbol}.BO"
            
            # Use yfinance for historical data
            ticker = yf.Ticker(yf_symbol)
            history = ticker.history(period=period, interval=interval)
            
            if not history.empty:
                # Convert to expected format
                chart_data = []
                for date, row in history.iterrows():
                    chart_data.append({
                        "date": date.strftime('%Y-%m-%d'),
                        "datetime": date.isoformat(),
                        "open": float(row.get('Open', 0)),
                        "high": float(row.get('High', 0)),
                        "low": float(row.get('Low', 0)),
                        "close": float(row.get('Close', 0)),
                        "volume": int(row.get('Volume', 0)),
                        "price": float(row.get('Close', 0))
                    })
                
                return {
                    "chart_data": chart_data,
                    "source": "yfinance",
                    "period": period,
                    "interval": interval
                }
            
            return {"error": "No chart data available", "symbol": symbol}
            
        except Exception as e:
            print(f"❌ Error getting chart data: {str(e)}")
            return {"error": str(e), "symbol": symbol}
    
    async def get_news(self, symbol: str, days: int = 7) -> Dict[str, Any]:
        """Get news using Finnhub (primary)"""
        try:
            if not self.finnhub_client:
                return {"articles": [], "source": "mock_data"}
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get news from Finnhub
            news = await asyncio.to_thread(
                self.finnhub_client.company_news,
                symbol=symbol,
                _from=start_date.strftime('%Y-%m-%d'),
                to=end_date.strftime('%Y-%m-%d')
            )
            
            if news:
                articles = []
                for item in news[:10]:  # Limit to 10 articles
                    articles.append({
                        "headline": item.get('headline', ''),
                        "source": item.get('source', ''),
                        "url": item.get('url', ''),
                        "summary": item.get('summary', ''),
                        "datetime": item.get('datetime', ''),
                        "image": item.get('image', ''),
                        "category": "business"
                    })
                
                return {
                    "articles": articles,
                    "source": "finnhub"
                }
            
            return {"articles": [], "source": "finnhub"}
            
        except Exception as e:
            print(f"❌ Error getting news: {str(e)}")
            return {"error": str(e), "symbol": symbol}
    
    async def get_financials(self, symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
        """Get financial statements using yfinance"""
        try:
            # Format symbol for yfinance
            yf_symbol = symbol
            if exchange == "NSE" and not symbol.endswith(".NS"):
                yf_symbol = f"{symbol}.NS"
            elif exchange == "BSE" and not symbol.endswith(".BO"):
                yf_symbol = f"{symbol}.BO"
            
            # Use yfinance for financial statements
            ticker = yf.Ticker(yf_symbol)
            
            # Get all financial statements
            income_stmt = ticker.financials
            balance_sheet = ticker.balance_sheet
            cash_flow = ticker.cashflow
            info = ticker.info
            
            financial_data = {
                "symbol": symbol,
                "source": "yfinance"
            }
            
            # Income Statement data
            if not income_stmt.empty:
                latest_income = income_stmt.iloc[:, 0]  # Most recent period
                financial_data.update({
                    "revenue": float(latest_income.get('Total Revenue', 0)) if not pd.isna(latest_income.get('Total Revenue', 0)) else 0,
                    "net_income": float(latest_income.get('Net Income', 0)) if not pd.isna(latest_income.get('Net Income', 0)) else 0,
                    "gross_profit": float(latest_income.get('Gross Profit', 0)) if not pd.isna(latest_income.get('Gross Profit', 0)) else 0,
                    "operating_income": float(latest_income.get('Operating Income', 0)) if not pd.isna(latest_income.get('Operating Income', 0)) else 0,
                    "ebitda": float(latest_income.get('EBITDA', 0)) if not pd.isna(latest_income.get('EBITDA', 0)) else 0,
                })
            
            # Balance Sheet data
            if not balance_sheet.empty:
                latest_balance = balance_sheet.iloc[:, 0]  # Most recent period
                financial_data.update({
                    "total_assets": float(latest_balance.get('Total Assets', 0)) if not pd.isna(latest_balance.get('Total Assets', 0)) else 0,
                    "total_liabilities": float(latest_balance.get('Total Liabilities', 0)) if not pd.isna(latest_balance.get('Total Liabilities', 0)) else 0,
                    "shareholders_equity": float(latest_balance.get('Total Stockholder Equity', 0)) if not pd.isna(latest_balance.get('Total Stockholder Equity', 0)) else 0,
                    "cash_and_equivalents": float(latest_balance.get('Cash And Cash Equivalents', 0)) if not pd.isna(latest_balance.get('Cash And Cash Equivalents', 0)) else 0,
                })
            
            # Cash Flow data
            if not cash_flow.empty:
                latest_cash_flow = cash_flow.iloc[:, 0]  # Most recent period
                financial_data.update({
                    "operating_cash_flow": float(latest_cash_flow.get('Operating Cash Flow', 0)) if not pd.isna(latest_cash_flow.get('Operating Cash Flow', 0)) else 0,
                    "investing_cash_flow": float(latest_cash_flow.get('Investing Cash Flow', 0)) if not pd.isna(latest_cash_flow.get('Investing Cash Flow', 0)) else 0,
                    "financing_cash_flow": float(latest_cash_flow.get('Financing Cash Flow', 0)) if not pd.isna(latest_cash_flow.get('Financing Cash Flow', 0)) else 0,
                })
            
            # Additional metrics from info
            financial_data.update({
                "market_cap": info.get('marketCap', 0),
                "enterprise_value": info.get('enterpriseValue', 0),
                "pe_ratio": info.get('trailingPE', 0),
                "pb_ratio": info.get('priceToBook', 0),
                "ps_ratio": info.get('priceToSales', 0),
                "ev_ebitda": info.get('enterpriseToEbitda', 0),
                "dividend_yield": info.get('dividendYield', 0),
                "beta": info.get('beta', 0),
            })
            
            return financial_data
            
        except Exception as e:
            print(f"❌ Error getting financials: {str(e)}")
            return {"error": str(e), "symbol": symbol}
    
    async def get_company_logo(self, symbol: str, exchange: str = "NSE") -> Optional[str]:
        """Get company logo using Twelve Data"""
        try:
            if not self.td_client:
                return None
            
            # Get logo from Twelve Data
            logo_url = await asyncio.to_thread(
                self.td_client.get_logo,
                symbol=symbol,
                exchange=exchange
            )
            
            return logo_url
            
        except Exception as e:
            print(f"⚠️ Logo fetch failed: {str(e)}")
            return None
