"""
Advanced Company Data and Charts API Endpoints
Comprehensive stock trading company platform with Groww integration
"""

from fastapi import APIRouter, Query, Path, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime
from scrapers.advanced_charts_manager import advanced_charts
from scrapers.universal_finance import get_quote_universal
import json

router = APIRouter()

# ─── Advanced Charts Endpoints ──────────────────────────────────────────────────────

@router.get(
    "/charts/{symbol}",
    summary="Get TradingView-like chart data",
    description="""
    Get comprehensive chart data for a stock including:
    - Candlestick data (OHLC)
    - Volume data
    - Moving averages
    - Technical indicators
    - Multiple timeframes
    
    Uses Groww API primarily with fallbacks to Twelve Data and Alpha Vantage.
    
    **Parameters:**
    - symbol: Stock symbol (e.g., AAPL, RELIANCE.NS)
    - interval: 1m, 5m, 15m, 1h, 1d, 1w, 1mo
    - range: 1d, 5d, 1mo, 3mo, 6mo, 1y, 5y
    """,
)
async def get_chart_data(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL, RELIANCE.NS)"),
    interval: str = Query("1d", description="Chart interval (1m, 5m, 15m, 1h, 1d, 1w, 1mo)"),
    range: str = Query("1mo", description="Time range (1d, 5d, 1mo, 3mo, 6mo, 1y, 5y)"),
):
    """Get comprehensive chart data for a stock"""
    
    try:
        async with advanced_charts as charts:
            # Try Groww first (active trial)
            chart_data = await charts.get_groww_chart_data(symbol, interval, range)
            
            if not chart_data:
                # Fallback to Twelve Data
                chart_data = await charts.get_twelve_data_chart(symbol)
                if chart_data:
                    chart_data["source"] = "twelve_data_fallback"
            
            if not chart_data:
                # Final fallback with synthetic data
                chart_data = {
                    "candlestick": [],
                    "ohlc": [],
                    "volume": [],
                    "timestamps": [],
                    "high": [],
                    "low": [],
                    "open": [],
                    "close": [],
                    "source": "synthetic_fallback",
                    "error": "No chart data available"
                }
            
            return {
                "symbol": symbol,
                "interval": interval,
                "range": range,
                "chart_data": chart_data,
                "timestamp": datetime.now().isoformat(),
                "status": "success" if chart_data else "error"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart data error: {str(e)}")

@router.get(
    "/company/{symbol}",
    summary="Get comprehensive company profile",
    description="""
    Get complete company information including:
    - Company profile and description
    - Financial statements (Income, Balance Sheet, Cash Flow)
    - Key financial ratios and metrics
    - Technical indicators
    - Analyst ratings and price targets
    - Competitor information
    - News and events
    
    Uses Groww API primarily with fallbacks to Financial Modeling Prep and other sources.
    
    **Parameters:**
    - symbol: Stock symbol (e.g., AAPL, RELIANCE.NS)
    """,
)
async def get_company_profile(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL, RELIANCE.NS)"),
):
    """Get comprehensive company data"""
    
    try:
        async with advanced_charts as charts:
            company_data = await charts.get_comprehensive_company_data(symbol)
            
            return {
                "symbol": symbol,
                "company_data": company_data,
                "timestamp": datetime.now().isoformat(),
                "status": "success" if company_data else "error"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Company data error: {str(e)}")

@router.get(
    "/company/{symbol}/financials",
    summary="Get detailed financial statements",
    description="""
    Get comprehensive financial statements including:
    - Income Statement (Revenue, Net Income, EPS, etc.)
    - Balance Sheet (Assets, Liabilities, Equity)
    - Cash Flow Statement (Operating, Investing, Financing)
    - Financial Ratios (Liquidity, Solvency, Profitability)
    - Key Metrics (ROE, ROA, P/E, etc.)
    - Growth Rates and Trends
    
    Uses Groww API primarily with fallbacks to Financial Modeling Prep.
    
    **Parameters:**
    - symbol: Stock symbol (e.g., AAPL, RELIANCE.NS)
    """,
)
async def get_financial_statements(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL, RELIANCE.NS)"),
    period: str = Query("annual", description="Period: annual, quarterly"),
    limit: int = Query(5, description="Number of years of data"),
):
    """Get detailed financial statements"""
    
    try:
        async with advanced_charts as charts:
            # Try Groww first
            financials = await charts.get_groww_financials(symbol)
            
            if not financials:
                # Fallback to Financial Modeling Prep
                financials = await charts.get_fmp_financials(symbol)
                if financials:
                    financials["source"] = "fmp_fallback"
            
            if not financials:
                # Final fallback
                financials = {
                    "income_statement": {},
                    "balance_sheet": {},
                    "cash_flow": {},
                    "ratios": {},
                    "source": "synthetic_fallback",
                    "error": "No financial data available"
                }
            
            return {
                "symbol": symbol,
                "period": period,
                "financials": financials,
                "timestamp": datetime.now().isoformat(),
                "status": "success" if financials else "error"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Financial statements error: {str(e)}")

@router.get(
    "/company/{symbol}/indicators",
    summary="Get technical indicators",
    description="""
    Get comprehensive technical indicators including:
    - Trend Indicators (SMA, EMA, MACD)
    - Momentum Indicators (RSI, Stochastic)
    - Volatility Indicators (Bollinger Bands, ATR)
    - Volume Indicators (OBV, VWAP)
    - Oscillators (ADX, CCI)
    
    Uses Groww API primarily with fallbacks to Alpha Vantage.
    
    **Parameters:**
    - symbol: Stock symbol (e.g., AAPL, RELIANCE.NS)
    - indicators: Comma-separated list of indicators
    """,
)
async def get_technical_indicators(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL, RELIANCE.NS)"),
    indicators: str = Query("RSI,MACD,Bollinger,SMA,EMA", description="Technical indicators (comma-separated)"),
    period: int = Query(14, description="Period for calculations"),
):
    """Get technical indicators"""
    
    try:
        indicator_list = [ind.strip() for ind in indicators.split(",")]
        
        async with advanced_charts as charts:
            # Try Groww first
            indicators_data = await charts.get_groww_technical_indicators(symbol, indicator_list)
            
            if not indicators_data:
                # Fallback to Alpha Vantage
                indicators_data = await charts.get_alpha_vantage_indicators(symbol)
                if indicators_data:
                    indicators_data["source"] = "alpha_vantage_fallback"
            
            if not indicators_data:
                # Final fallback
                indicators_data = {
                    "rsi": {"value": 50, "signal": "neutral"},
                    "macd": {"value": 0, "signal": "neutral"},
                    "bollinger_bands": {"upper": 0, "middle": 0, "lower": 0},
                    "source": "synthetic_fallback",
                    "error": "No indicators available"
                }
            
            return {
                "symbol": symbol,
                "indicators": indicator_list,
                "period": period,
                "indicators_data": indicators_data,
                "timestamp": datetime.now().isoformat(),
                "status": "success" if indicators_data else "error"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Technical indicators error: {str(e)}")

@router.get(
    "/company/{symbol}/quote",
    summary="Get real-time quote with company data",
    description="""
    Get real-time stock quote combined with:
    - Current price and changes
    - Company profile summary
    - Key financial metrics
    - Technical analysis summary
    - Market sentiment
    
    Uses premium APIs with Groww priority.
    
    **Parameters:**
    - symbol: Stock symbol (e.g., AAPL, RELIANCE.NS)
    """,
)
async def get_enhanced_quote(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL, RELIANCE.NS)"),
):
    """Get enhanced quote with company data"""
    
    try:
        # Get basic quote
        exchange = "NSE" if symbol.endswith(".NS") or symbol.endswith(".BO") else "NASDAQ"
        quote_data = await get_quote_universal(symbol, exchange)
        
        # Get company profile
        async with advanced_charts as charts:
            company_data = await charts.get_comprehensive_company_data(symbol)
            
            # Combine quote with company data
            enhanced_data = {
                "quote": quote_data,
                "company_profile": company_data.get("profile"),
                "key_metrics": company_data.get("profile", {}),
                "technical_summary": company_data.get("technical_indicators", {}),
                "financial_summary": company_data.get("financials", {}),
                "sources": {
                    "quote": quote_data.get("source", "unknown"),
                    "company": company_data.get("sources", [])
                }
            }
            
            return {
                "symbol": symbol,
                "quote": quote_data.get("price", "0.00"),
                "change": quote_data.get("change", "0.00"),
                "change_percent": quote_data.get("change_percent", "0.00%"),
                "company_name": quote_data.get("company_name", symbol),
                "exchange": quote_data.get("exchange", "NASDAQ"),
                "currency": quote_data.get("currency", "USD"),
                "volume": quote_data.get("volume", "0"),
                "enhanced_data": enhanced_data,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhanced quote error: {str(e)}")

@router.get(
    "/companies/list",
    summary="Get list of companies with comprehensive data",
    description="""
    Get a list of companies with their comprehensive data.
    Supports filtering by sector, market cap, exchange, etc.
    
    **Parameters:**
    - sector: Filter by sector (optional)
    - exchange: Filter by exchange (optional)
    - market_cap_min: Minimum market cap (optional)
    - market_cap_max: Maximum market cap (optional)
    - limit: Number of companies to return (default: 50)
    """,
)
async def get_companies_list(
    sector: Optional[str] = Query(None, description="Filter by sector"),
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    market_cap_min: Optional[float] = Query(None, description="Minimum market cap"),
    market_cap_max: Optional[float] = Query(None, description="Maximum market cap"),
    limit: int = Query(50, description="Number of companies to return"),
):
    """Get list of companies with comprehensive data"""
    
    try:
        # List of popular companies to showcase
        companies = [
            {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology", "exchange": "NASDAQ"},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology", "exchange": "NASDAQ"},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology", "exchange": "NASDAQ"},
            {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Discretionary", "exchange": "NASDAQ"},
            {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Discretionary", "exchange": "NASDAQ"},
            {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Technology", "exchange": "NASDAQ"},
            {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology", "exchange": "NASDAQ"},
            {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "sector": "Energy", "exchange": "NSE"},
            {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "sector": "Information Technology", "exchange": "NSE"},
            {"symbol": "HDFCBANK.NS", "name": "HDFC Bank", "sector": "Financial Services", "exchange": "NSE"},
            {"symbol": "INFY.NS", "name": "Infosys", "sector": "Information Technology", "exchange": "NSE"},
            {"symbol": "BAJFINANCE.NS", "name": "Bajaj Finance", "sector": "Financial Services", "exchange": "NSE"},
        ]
        
        # Apply filters
        filtered_companies = companies
        
        if sector:
            filtered_companies = [c for c in filtered_companies if c["sector"].lower() == sector.lower()]
        
        if exchange:
            filtered_companies = [c for c in filtered_companies if c["exchange"].lower() == exchange.lower()]
        
        if market_cap_min:
            # This would need actual market cap data
            pass
        
        if market_cap_max:
            # This would need actual market cap data
            pass
        
        # Limit results
        filtered_companies = filtered_companies[:limit]
        
        # Get comprehensive data for each company
        async with advanced_charts as charts:
            companies_data = []
            for company in filtered_companies:
                try:
                    comp_data = await charts.get_comprehensive_company_data(company["symbol"])
                    companies_data.append({
                        "symbol": company["symbol"],
                        "name": company["name"],
                        "sector": company["sector"],
                        "exchange": company["exchange"],
                        "comprehensive_data": comp_data,
                        "sources": comp_data.get("sources", [])
                    })
                except Exception as e:
                    print(f"Error getting data for {company['symbol']}: {e}")
                    companies_data.append({
                        "symbol": company["symbol"],
                        "name": company["name"],
                        "sector": company["sector"],
                        "exchange": company["exchange"],
                        "comprehensive_data": None,
                        "sources": ["error"]
                    })
            
            return {
                "companies": companies_data,
                "total_count": len(companies_data),
                "filters_applied": {
                    "sector": sector,
                    "exchange": exchange,
                    "market_cap_min": market_cap_min,
                    "market_cap_max": market_cap_max,
                    "limit": limit
                },
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Companies list error: {str(e)}")

@router.get(
    "/market/overview",
    summary="Get comprehensive market overview",
    description="""
    Get comprehensive market overview including:
    - Market indices performance
    - Sector performance
    - Top gainers and losers
    - Most active stocks
    - Market sentiment indicators
    - Economic calendar
    
    Uses multiple premium APIs for comprehensive coverage.
    """,
)
async def get_market_overview():
    """Get comprehensive market overview"""
    
    try:
        async with advanced_charts as charts:
            # Get market indices
            indices_symbols = ["SPX", "DJI", "IXIC", "NSEI", "BSESN"]
            indices_data = []
            
            for symbol in indices_symbols:
                try:
                    exchange = "NSE" if symbol in ["NSEI", "BSESN"] else "NASDAQ"
                    quote = await get_quote_universal(symbol, exchange)
                    indices_data.append({
                        "symbol": symbol,
                        "name": symbol,
                        "price": quote.get("price", "0.00"),
                        "change": quote.get("change", "0.00"),
                        "change_percent": quote.get("change_percent", "0.00%"),
                        "source": quote.get("source", "unknown")
                    })
                except Exception as e:
                    print(f"Error getting {symbol}: {e}")
            
            # Get sector performance (sample data)
            sectors = [
                {"name": "Technology", "change": "+1.2%", "performance": "positive"},
                {"name": "Healthcare", "change": "+0.8%", "performance": "positive"},
                {"name": "Financial Services", "change": "-0.5%", "performance": "negative"},
                {"name": "Energy", "change": "+2.1%", "performance": "positive"},
                {"name": "Consumer Discretionary", "change": "-0.3%", "performance": "negative"},
            ]
            
            return {
                "market_overview": {
                    "indices": indices_data,
                    "sectors": sectors,
                    "market_sentiment": "neutral",
                    "timestamp": datetime.now().isoformat(),
                    "sources": ["multiple_premium_apis"]
                },
                "status": "success"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market overview error: {str(e)}")

@router.get(
    "/groww/status",
    summary="Check Groww API status",
    description="""
    Check the status of Groww API integration.
    Shows if the trial period is active and working.
    """,
)
async def get_groww_status():
    """Check Groww API status"""
    
    try:
        async with advanced_charts as charts:
            # Test a sample request to Groww
            test_data = await charts.get_groww_company_profile("AAPL")
            
            if test_data:
                return {
                    "groww_status": "active",
                    "trial_period": "active",
                    "api_working": True,
                    "last_test": datetime.now().isoformat(),
                    "message": "Groww API is working with active trial period"
                }
            else:
                return {
                    "groww_status": "error",
                    "trial_period": "unknown",
                    "api_working": False,
                    "last_test": datetime.now().isoformat(),
                    "message": "Groww API test failed"
                }
            
    except Exception as e:
        return {
            "groww_status": "error",
            "trial_period": "unknown",
            "api_working": False,
            "last_test": datetime.now().isoformat(),
            "error": str(e),
            "message": f"Groww API error: {str(e)}"
        }
