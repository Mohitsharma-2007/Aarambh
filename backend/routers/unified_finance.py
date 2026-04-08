"""
routers/unified_finance.py — Unified Finance API Router

Exposes aggregated finance data through a single set of endpoints.
Uses fallback strategy across Google Finance, Yahoo Finance, FMP, Finnhub, TwelveData.
"""

from fastapi import APIRouter, Query, Path
from services import finance_service as fs

router = APIRouter()


# ── Quote ──────────────────────────────────────────────────
@router.get("/quote/{symbol}", summary="Unified stock quote with multi-source fallback")
async def unified_quote(
    symbol: str = Path(..., description="Stock symbol e.g. AAPL, TSLA, RELIANCE"),
    exchange: str = Query("NASDAQ", description="Exchange e.g. NASDAQ, NSE, NYSE"),
):
    return await fs.get_unified_quote(symbol, exchange)


# ── Chart / Time Series ───────────────────────────────────
@router.get("/chart/{symbol}", summary="Chart data (OHLCV) with multi-source fallback")
async def unified_chart(
    symbol: str = Path(..., description="Stock symbol"),
    exchange: str = Query("NASDAQ"),
    window: str = Query("1Y", description="1D|5D|1W|1M|3M|6M|1Y|5Y|YTD|MAX"),
):
    return await fs.get_unified_chart(symbol, exchange, window=window)


# ── Company Profile ────────────────────────────────────────
@router.get("/profile/{symbol}", summary="Company profile (FMP → Finnhub fallback)")
async def unified_profile(
    symbol: str = Path(...),
    exchange: str = Query("NASDAQ"),
):
    return await fs.get_unified_profile(symbol, exchange)


# ── Fundamentals ───────────────────────────────────────────
@router.get("/fundamentals/{symbol}", summary="Financial statements (Income, Balance, Cash Flow)")
async def unified_fundamentals(
    symbol: str = Path(..., description="Stock symbol"),
):
    return await fs.get_unified_fundamentals(symbol)


# ── Company News ───────────────────────────────────────────
@router.get("/news/{symbol}", summary="Company news (Google Finance → Finnhub)")
async def unified_news(
    symbol: str = Path(..., description="Stock symbol"),
):
    return await fs.get_unified_company_news(symbol)


# ── Search ─────────────────────────────────────────────────
@router.get("/search", summary="Search stocks/ETFs (Google → FMP → Yahoo)")
async def unified_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50),
):
    return await fs.search_unified(q, limit)


# ── Groww Direct Endpoints ────────────────────────────────
@router.get("/groww/quote/{symbol}", summary="Direct Groww quote (Indian market)")
async def groww_quote(
    symbol: str = Path(..., description="Stock symbol e.g. RELIANCE, TCS, INFY"),
    exchange: str = Query("NSE", description="Exchange: NSE or BSE"),
):
    from scrapers import groww_finance as groww
    return await groww.get_quote(symbol, exchange)


@router.get("/groww/search", summary="Search on Groww")
async def groww_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50),
):
    from scrapers import groww_finance as groww
    return await groww.search(q, limit)


@router.get("/groww/stock/{symbol}", summary="Detailed stock data from Groww")
async def groww_stock_data(
    symbol: str = Path(..., description="Groww search_id or symbol"),
):
    from scrapers import groww_finance as groww
    return await groww.get_stock_data(symbol)


# ── FMP Direct Endpoints ──────────────────────────────────
@router.get("/fmp/gainers", summary="Market gainers from FMP")
async def fmp_gainers():
    return await fs.fmp_market_gainers()


@router.get("/fmp/losers", summary="Market losers from FMP")
async def fmp_losers():
    return await fs.fmp_market_losers()


@router.get("/fmp/quote/{symbol}", summary="Direct FMP quote")
async def fmp_quote(symbol: str = Path(...)):
    return await fs.fmp_quote(symbol)


@router.get("/fmp/ratios/{symbol}", summary="Financial ratios from FMP")
async def fmp_ratios(symbol: str = Path(...)):
    return await fs.fmp_ratios(symbol)


# ── Finnhub Direct ─────────────────────────────────────────
@router.get("/finnhub/news", summary="General market news from Finnhub")
async def finnhub_market_news(
    category: str = Query("general", description="general|forex|crypto|merger"),
):
    return await fs.finnhub_general_news(category)


# ── TwelveData Direct ──────────────────────────────────────
@router.get("/twelvedata/series/{symbol}", summary="Time series from TwelveData")
async def twelvedata_series(
    symbol: str = Path(...),
    interval: str = Query("1day", description="1min|5min|15min|30min|1h|1day|1week|1month"),
    outputsize: int = Query(100, ge=1, le=5000),
):
    return await fs.twelvedata_time_series(symbol, interval, outputsize)
