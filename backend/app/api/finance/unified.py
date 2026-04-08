from fastapi import APIRouter, Query, Path
from utils import unified_data as ud
from routers import google_finance, yahoo_finance

router = APIRouter()

@router.get("/intelligence")
async def intelligence():
    """Consolidated market and intelligence data."""
    return await ud.get_market_intelligence()

@router.get("/quote/{ticker}")
async def quote(ticker: str, exchange: str = Query("NASDAQ")):
    """Get stock quote using Free API Stack (yfinance + Twelve Data + Finnhub)."""
    from routers.free_api_stack import FreeAPIStack
    
    try:
        print(f"🔍 Unified: Processing quote request for {ticker}")
        api_stack = FreeAPIStack()
        
        # Extract exchange from ticker (e.g., RELIANCE.NS -> NSE)
        actual_exchange = "NSE"
        base_symbol = ticker
        if "." in ticker:
            actual_exchange = ticker.split(".")[-1]
            base_symbol = ticker.split(".")[0]
        
        print(f"🔧 Unified: Calling Free API Stack with {base_symbol}, {actual_exchange}")
        quote_data = await api_stack.get_stock_quote(base_symbol, actual_exchange)
        print(f"🔧 Unified: Free API Stack returned {quote_data}")
        
        # Update symbol to match the input
        if "error" not in quote_data:
            quote_data["symbol"] = ticker
            print(f"✅ Unified: Success for {ticker}")
        else:
            print(f"❌ Unified: Free API Stack failed for {ticker}")
        
        return quote_data
    except Exception as e:
        print(f"❌ Unified Exception: {str(e)}")
        return {"error": str(e), "symbol": ticker}

@router.get("/search")
async def search(q: str = Query(..., description="Search query for stocks")):
    """Search stocks using Groww API for better results."""
    from routers.aarambh_finance_api import AarambhDataFetcher
    
    try:
        async with AarambhDataFetcher() as fetcher:
            # For search, we'll use mock data with some popular stocks
            # In real implementation, Groww API would have a search endpoint
            mock_results = [
                {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "type": "Stock"},
                {"symbol": "MSFT", "name": "Microsoft Corp.", "exchange": "NASDAQ", "type": "Stock"},
                {"symbol": "GOOGL", "name": "Alphabet Inc.", "exchange": "NASDAQ", "type": "Stock"},
                {"symbol": "AMZN", "name": "Amazon.com Inc.", "exchange": "NASDAQ", "type": "Stock"},
                {"symbol": "TSLA", "name": "Tesla Inc.", "exchange": "NASDAQ", "type": "Stock"},
                {"symbol": "NVDA", "name": "NVIDIA Corp.", "exchange": "NASDAQ", "type": "Stock"},
                {"symbol": "META", "name": "Meta Platforms", "exchange": "NASDAQ", "type": "Stock"},
                {"symbol": "RELIANCE.NS", "name": "Reliance Industries Ltd.", "exchange": "NSE", "type": "Stock"},
                {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "exchange": "NSE", "type": "Stock"},
                {"symbol": "HDFCBANK.NS", "name": "HDFC Bank Ltd.", "exchange": "NSE", "type": "Stock"},
            ]
            
            # Filter results based on query
            filtered_results = [
                result for result in mock_results 
                if q.upper() in result["symbol"].upper() or q.upper() in result["name"].upper()
            ]
            
            return {
                "query": q,
                "results": filtered_results[:10]  # Limit to 10 results
            }
    except Exception as e:
        return {
            "query": q,
            "results": [],
            "error": str(e)
        }

@router.get("/chart/{ticker}")
async def chart(ticker: str, exchange: str = Query("NASDAQ"), window: str = Query("1Y")):
    """Get chart data using Groww API with fallbacks."""
    from routers.aarambh_finance_api import AarambhDataFetcher
    
    try:
        async with AarambhDataFetcher() as fetcher:
            chart_data = await fetcher.fetch_with_fallback(ticker, "chart_data")
            return chart_data
    except Exception as e:
        return {"error": str(e), "symbol": ticker}

@router.get("/profile/{ticker}")
async def profile(ticker: str, exchange: str = Query("NASDAQ")):
    """Get company profile using Groww API with fallbacks."""
    from routers.aarambh_finance_api import AarambhDataFetcher
    
    try:
        async with AarambhDataFetcher() as fetcher:
            profile_data = await fetcher.fetch_with_fallback(ticker, "company_profile")
            return profile_data
    except Exception as e:
        return {"error": str(e), "symbol": ticker}

@router.get("/news/{ticker}")
async def news(ticker: str):
    """Get news using Groww API with fallbacks."""
    from routers.aarambh_finance_api import AarambhDataFetcher
    
    try:
        async with AarambhDataFetcher() as fetcher:
            news_data = await fetcher.fetch_with_fallback(ticker, "news")
            return news_data
    except Exception as e:
        return {"error": str(e), "symbol": ticker}

@router.get("/fundamentals/{ticker}")
async def fundamentals(ticker: str):
    """Get financial fundamentals using Groww API with fallbacks."""
    from routers.aarambh_finance_api import AarambhDataFetcher
    
    try:
        async with AarambhDataFetcher() as fetcher:
            financials_data = await fetcher.fetch_with_fallback(ticker, "financials")
            return financials_data
    except Exception as e:
        return {"error": str(e), "symbol": ticker}
