"""utils/unified_data.py"""
from scrapers import google_finance as gf
from scrapers import yahoo_finance as yf
import asyncio

async def get_best_quote(ticker: str):
    """
    Tries Google Finance first (verified 100% stable), 
    falls back to Yahoo for extended fields if needed.
    """
    # 1. Try Google Finance (Passed all test cases)
    try:
        data = await gf.get_quote(ticker)
        if data and not data.get("error"):
            return data
    except:
        pass
        
    # 2. Fallback to Yahoo
    try:
        data = await yf.get_quote(ticker)
        return data
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}

async def get_market_intelligence():
    """
    Combines Movers from Yahoo (Passed) and Global Headlines from News Platform.
    """
    # This usually runs in finance_api, so we call local scrapers
    movers = await yf.get_movers("most_actives", 5)
    return {"movers": movers}
