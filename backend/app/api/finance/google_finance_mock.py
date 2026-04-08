"""
Mock Finance Router - Temporary solution while fixing scraping issues
"""

from fastapi import APIRouter, Path, Query
from mock_data import get_mock_market_data, get_mock_quote, get_mock_overview

router = APIRouter()

@router.get("/market/{section}")
async def get_market_section(section: str = Path(..., description="Market section")):
    """Get market section data (mock)"""
    return get_mock_market_data(section)

@router.get("/quote/{ticker}/{exchange}")
async def get_quote_full(ticker: str = Path(...), exchange: str = Path(...)):
    """Get stock quote with exchange (mock)"""
    return get_mock_quote(ticker)

@router.get("/quote/{ticker}")
async def get_quote_default(ticker: str = Path(...), exchange: str = Query("NASDAQ")):
    """Get stock quote with default exchange (mock)"""
    return get_mock_quote(ticker)

@router.get("/overview")
async def get_overview():
    """Get market overview (mock)"""
    return get_mock_overview()

@router.get("/search")
async def search_stocks(q: str = Query(...)):
    """Search stocks (mock)"""
    # Simple mock search
    mock_results = [
        {"ticker": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "type": "stock"},
        {"ticker": "GOOGL", "name": "Alphabet Inc.", "exchange": "NASDAQ", "type": "stock"},
        {"ticker": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ", "type": "stock"},
        {"ticker": "TSLA", "name": "Tesla Inc.", "exchange": "NASDAQ", "type": "stock"},
        {"ticker": "AMZN", "name": "Amazon.com Inc.", "exchange": "NASDAQ", "type": "stock"},
    ]
    
    # Filter by query if provided
    if q:
        q = q.lower()
        mock_results = [
            result for result in mock_results 
            if q in result["ticker"].lower() or q in result["name"].lower()
        ]
    
    return {"query": q, "results": mock_results}
