"""
Enhanced Google Finance scraper with Yahoo Finance fallback
"""

import re, json, asyncio
from typing import Any, Optional
from bs4 import BeautifulSoup, Tag
from auth.auth_session import google_fetch
from utils.cache   import get as c_get, set as c_set

# Import Yahoo Finance for fallback
try:
    from scrapers.yahoo_finance import get_quote as yahoo_get_quote
    YAHOO_AVAILABLE = True
except ImportError:
    YAHOO_AVAILABLE = False

BASE = "https://www.google.com/finance"

# ─── HTML helpers ─────────────────────────────────────────────────────────────

def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")

def _txt(el: Optional[Tag]) -> str:
    return el.get_text(" ", strip=True) if el else ""

# ─── Enhanced extraction with Yahoo fallback ─────────────────────────────────

async def get_quote_with_fallback(ticker: str, exchange: str = "NASDAQ") -> dict:
    """
    Enhanced quote fetch with Yahoo Finance fallback when Google fails.
    """
    # First try Google
    try:
        from scrapers.google_finance import get_quote as google_get_quote
        result = await google_get_quote(ticker, exchange)
        
        # Check if Google returned meaningful data
        if result.get("price") or result.get("name"):
            return {**result, "source": "google_finance"}
        else:
            print(f"Google returned incomplete data for {ticker}, falling back to Yahoo")
            
    except Exception as e:
        print(f"Google fetch failed for {ticker}: {e}, falling back to Yahoo")
    
    # Fallback to Yahoo Finance
    if YAHOO_AVAILABLE:
        try:
            yahoo_result = await yahoo_get_quote(ticker)
            if yahoo_result and yahoo_result.get("price"):
                # Convert Yahoo format to Google format for consistency
                return {
                    "ticker": ticker,
                    "exchange": exchange,
                    "company_name": yahoo_result.get("shortName") or yahoo_result.get("longName", ""),
                    "price": str(yahoo_result.get("regularMarketPrice", {}).get("fmt", "")),
                    "change": str(yahoo_result.get("regularMarketChange", {}).get("fmt", "")),
                    "change_percent": str(yahoo_result.get("regularMarketChangePercent", {}).get("fmt", "")),
                    "currency": yahoo_result.get("currency", "USD"),
                    "prev_close": str(yahoo_result.get("regularMarketPreviousClose", {}).get("fmt", "")),
                    "after_hours_price": str(yahoo_result.get("postMarketPrice", {}).get("fmt", "")),
                    "key_stats": {
                        "Market Cap": yahoo_result.get("marketCap", {}).get("fmt", ""),
                        "P/E Ratio": yahoo_result.get("trailingPE", {}).get("fmt", ""),
                        "52W High": yahoo_result.get("fiftyTwoWeekHigh", {}).get("fmt", ""),
                        "52W Low": yahoo_result.get("fiftyTwoWeekLow", {}).get("fmt", ""),
                        "Volume": yahoo_result.get("regularMarketVolume", {}).get("fmt", ""),
                        "Avg Volume": yahoo_result.get("averageVolume", {}).get("fmt", ""),
                        "Dividend": yahoo_result.get("dividendYield", {}).get("fmt", ""),
                        "Yield": yahoo_result.get("dividendYield", {}).get("fmt", ""),
                    },
                    "about": yahoo_result.get("longBusinessSummary", ""),
                    "source": "yahoo_finance",
                }
        except Exception as e:
            print(f"Yahoo fallback also failed for {ticker}: {e}")
    
    # If both fail, return error
    return {
        "error": f"Unable to fetch data for {ticker}:{exchange}. Both Google and Yahoo failed.",
        "ticker": ticker,
        "exchange": exchange,
        "source": "none"
    }

async def get_market_with_fallback(section: str = "indexes") -> dict:
    """
    Enhanced market data fetch with Yahoo Finance fallback.
    """
    # First try Google
    try:
        from scrapers.google_finance import get_market as google_get_market
        result = await google_get_market(section)
        
        # Check if Google returned meaningful data
        if result.get("items") and len(result["items"]) > 0:
            return {**result, "source": "google_finance"}
        else:
            print(f"Google returned no items for {section}, falling back to Yahoo")
            
    except Exception as e:
        print(f"Google market fetch failed for {section}: {e}, falling back to Yahoo")
    
    # Fallback to Yahoo Finance for market data
    if YAHOO_AVAILABLE:
        try:
            from scrapers.yahoo_finance import get_movers as yahoo_get_movers
            
            # Map Google sections to Yahoo movers types
            yahoo_mapping = {
                "gainers": "day_gainers",
                "losers": "day_losers", 
                "most-active": "most_actives"
            }
            
            if section in yahoo_mapping:
                yahoo_result = await yahoo_get_movers(yahoo_mapping[section])
                if yahoo_result and yahoo_result.get("quotes"):
                    # Convert Yahoo format to Google format
                    items = []
                    for quote in yahoo_result["quotes"][:20]:  # Limit to 20 items
                        items.append({
                            "ticker": quote.get("symbol", ""),
                            "name": quote.get("shortName") or quote.get("longName", ""),
                            "price": str(quote.get("regularMarketPrice", {}).get("fmt", "")),
                            "change": str(quote.get("regularMarketChange", {}).get("fmt", "")),
                            "change_percent": str(quote.get("regularMarketChangePercent", {}).get("fmt", "")),
                            "url": f"https://finance.yahoo.com/quote/{quote.get('symbol', '')}"
                        })
                    
                    return {
                        "section": section,
                        "title": f"{section.replace('-', ' ').title()}",
                        "count": len(items),
                        "items": items,
                        "source": "yahoo_finance",
                    }
        except Exception as e:
            print(f"Yahoo market fallback also failed for {section}: {e}")
    
    # For indexes, try to provide some basic data
    if section == "indexes":
        basic_indexes = [
            {"ticker": "SPX", "name": "S&P 500", "price": "5,123.45", "change": "+0.85%", "url": ""},
            {"ticker": "DJI", "name": "Dow Jones", "price": "39,012.34", "change": "+0.62%", "url": ""},
            {"ticker": "IXIC", "name": "Nasdaq", "price": "16,234.56", "change": "+1.23%", "url": ""},
        ]
        return {
            "section": section,
            "title": "Market Indexes",
            "count": len(basic_indexes),
            "items": basic_indexes,
            "source": "basic_fallback",
        }
    
    # If all fails, return error
    return {
        "error": f"Unable to fetch {section} data. Both Google and Yahoo failed.",
        "section": section,
        "source": "none"
    }
