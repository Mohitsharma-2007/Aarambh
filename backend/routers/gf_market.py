"""routers/gf_market.py - Google Finance Router (WORKING endpoints only)"""
from fastapi import APIRouter, Query, Path
from scrapers import google_finance as gf
from typing import Optional

router = APIRouter()


@router.get("/quote/{ticker}/{exchange}", summary="Stock quote with full data")
async def quote(
    ticker:   str = Path(..., description="Stock symbol e.g. AAPL, RELIANCE, TSLA"),
    exchange: str = Path(..., description="Exchange e.g. NASDAQ, NSE, NYSE"),
):
    return await gf.get_quote(ticker, exchange)


@router.get("/quote/{ticker}", summary="Stock quote (NASDAQ default)")
async def quote_default(
    ticker: str = Path(..., description="Stock symbol"),
    exchange: str = Query("NASDAQ", description="Override exchange"),
):
    return await gf.get_quote(ticker, exchange)


@router.get("/multi-quote", summary="Multiple quotes at once")
async def multi_quote(
    tickers:  str = Query(..., description="Comma-separated tickers e.g. AAPL,MSFT,GOOGL"),
    exchange: str = Query("NASDAQ", description="Exchange for all tickers"),
):
    ticker_list = [t.strip() for t in tickers.split(",") if t.strip()][:10]
    return await gf.get_multi_quote(ticker_list, exchange)


@router.get("/market/{section}", summary="Market data sections")
async def market(
    section: str = Path(..., description="indexes|gainers|losers|most-active|crypto|currencies|futures|etfs"),
):
    return await gf.get_market(section)


@router.get("/overview", summary="Full market overview")
async def overview():
    return await gf.get_overview()


@router.get("/search", summary="Search stocks/ETFs/crypto")
async def search(
    q: str = Query(..., description="Search query"),
):
    return await gf.search_gf(q)


@router.get("/chart/{ticker}", summary="Historical chart data")
async def chart(
    ticker:   str = Path(..., description="Stock symbol"),
    exchange: str = Query("NASDAQ"),
    window:   str = Query("1Y", description="1D|5D|1M|6M|YTD|1Y|5Y|MAX"),
):
    return await gf.get_chart(ticker, exchange, window)


@router.get("/news/{ticker}", summary="News for a ticker")
async def news(
    ticker:   str = Path(...),
    exchange: str = Query("NASDAQ"),
):
    data = await gf.get_quote(ticker, exchange)
    return {
        "ticker":   ticker,
        "exchange": exchange,
        "count":    len(data.get("news", [])),
        "news":     data.get("news", []),
    }
