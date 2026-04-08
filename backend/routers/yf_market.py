"""routers/yf_market.py - Yahoo Finance Router (WORKING endpoints only)"""
from fastapi import APIRouter, Query, Path
from scrapers import yahoo_finance as yf
from typing import Optional

router = APIRouter()


@router.get("/quote/{ticker}", summary="Stock quote (verified working: TSLA, NVDA, MSFT, RELIANCE.NS)")
async def quote(
    ticker: str = Path(..., description="Stock symbol (NOTE: AAPL has issues)"),
):
    return await yf.get_quote(ticker)


@router.get("/chart/{ticker}", summary="Chart data (1d and 1wk intervals work reliably)")
async def chart(
    ticker: str = Path(...),
    interval: str = Query("1d", description="1d|1wk (1h and 5m have issues)"),
    range: str = Query("1mo", description="1mo|3mo|6mo|1y"),
):
    return await yf.get_chart(ticker, interval, range)


@router.get("/search", summary="Search tickers")
async def search(
    q: str = Query(..., description="Search query"),
):
    return await yf.search_yf(q)


@router.get("/trending", summary="Trending stocks (US only - IN has issues)")
async def trending(
    region: str = Query("US", description="Region code (US works, IN has issues)"),
):
    return await yf.get_trending(region)


@router.get("/movers", summary="Market movers")
async def movers(
    type: str = Query("most_actives", description="day_gainers|day_losers|most_actives"),
):
    return await yf.get_movers(type)


@router.get("/recommendations/{ticker}", summary="Related stocks")
async def recommendations(
    ticker: str = Path(...),
):
    return await yf.get_recommendations(ticker)


@router.get("/sparkline", summary="Mini price charts for multiple tickers")
async def sparkline(
    tickers: str = Query(..., description="Comma-separated tickers e.g. AAPL,MSFT,GOOGL"),
):
    ticker_list = [t.strip() for t in tickers.split(",") if t.strip()][:10]
    return await yf.get_sparkline(ticker_list)


@router.get("/site-map", summary="Yahoo Finance endpoints info")
async def site_map():
    return {
        "note": "Filtered to working endpoints only",
        "working": [
            "GET /quote/{ticker} - TSLA, NVDA, MSFT, RELIANCE.NS verified",
            "GET /chart/{ticker} - 1d and 1wk intervals work",
            "GET /search - Search tickers",
            "GET /trending - US region only",
            "GET /movers - Market movers",
            "GET /recommendations/{ticker} - Related stocks",
            "GET /sparkline - Multi-ticker mini charts",
        ],
        "filtered_out": [
            "GET /financials/{ticker} - auth_failed error",
            "GET /holders/{ticker} - auth_failed error",
            "GET /options/{ticker} - Options not available",
            "GET /trending?region=IN - No data",
        ],
    }
