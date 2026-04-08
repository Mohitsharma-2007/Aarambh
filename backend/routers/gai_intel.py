"""routers/gai_intel.py - Google AI Router (WORKING endpoints only)"""
from fastapi import APIRouter, Query, Path
from scrapers import google_ai as gai

router = APIRouter()


@router.get("/overview", summary="AI Overview for any query")
async def overview(
    q: str = Query(..., description="Query e.g. 'Apple stock price today'"),
):
    return await gai.get_ai_overview(q)


@router.get("/finance-summary/{ticker}", summary="AI Finance summary for a ticker")
async def finance_summary(
    ticker: str = Path(..., description="Stock symbol e.g. AAPL, TSLA, NVDA"),
):
    return await gai.get_finance_summary(ticker)
