"""Indian Market API endpoints - NSE/BSE live data + FMP integration"""
from fastapi import APIRouter, Query
from typing import Optional

from app.services.indian_market_service import indian_market_service

router = APIRouter()


@router.get("/quote/{symbol}")
async def get_indian_stock_quote(symbol: str):
    """Get live quote for an Indian stock via IndianAPI"""
    data = await indian_market_service.get_indian_stock_quote(symbol.upper())
    if not data:
        return {"error": f"No data for {symbol}", "symbol": symbol}
    return data


@router.get("/nifty50")
async def get_nifty50_heatmap():
    """Get all NIFTY 50 stocks with price changes for heatmap"""
    return await indian_market_service.get_nifty50_heatmap()


@router.get("/indices")
async def get_indian_indices():
    """Get Indian market indices (NIFTY 50, NIFTY BANK, SENSEX)"""
    return await indian_market_service.get_indian_indices()


@router.get("/ipo")
async def get_ipo_data():
    """Get upcoming, current and recently listed IPOs"""
    return await indian_market_service.get_ipo_data()


@router.get("/mutual-funds")
async def get_mutual_funds():
    """Get mutual fund data"""
    return await indian_market_service.get_mutual_funds()


@router.get("/overview")
async def get_combined_overview():
    """Get combined market overview: NIFTY 50 + FMP gainers/losers/active"""
    return await indian_market_service.get_combined_market_overview()


# ── FMP Endpoints ──

@router.get("/fmp/quote/{symbol}")
async def fmp_quote(symbol: str):
    """Get FMP quote for any global stock"""
    data = await indian_market_service.fmp_quote(symbol.upper())
    if not data:
        return {"error": f"No FMP data for {symbol}"}
    return data


@router.get("/fmp/gainers")
async def fmp_gainers():
    """Get top market gainers"""
    return await indian_market_service.fmp_market_gainers()


@router.get("/fmp/losers")
async def fmp_losers():
    """Get top market losers"""
    return await indian_market_service.fmp_market_losers()


@router.get("/fmp/active")
async def fmp_active():
    """Get most active stocks"""
    return await indian_market_service.fmp_market_active()


@router.get("/fmp/financials/{symbol}")
async def fmp_financials(symbol: str):
    """Get income statement, balance sheet, cash flow from FMP"""
    return await indian_market_service.fmp_financial_statements(symbol.upper())


@router.get("/fmp/profile/{symbol}")
async def fmp_profile(symbol: str):
    """Get company profile from FMP"""
    data = await indian_market_service.fmp_company_profile(symbol.upper())
    if not data:
        return {"error": f"No profile for {symbol}"}
    return data


@router.get("/fmp/screener")
async def fmp_screener(
    market_cap_min: int = Query(10_000_000_000, description="Minimum market cap"),
    limit: int = Query(30, ge=1, le=100),
):
    """Screen stocks by market cap"""
    return await indian_market_service.fmp_stock_screener(market_cap_min, limit)


@router.get("/fmp/economic-calendar")
async def fmp_economic_calendar():
    """Get upcoming economic events"""
    return await indian_market_service.fmp_economic_calendar()


@router.get("/fmp/earnings-calendar")
async def fmp_earnings_calendar():
    """Get upcoming earnings announcements"""
    return await indian_market_service.fmp_earnings_calendar()
