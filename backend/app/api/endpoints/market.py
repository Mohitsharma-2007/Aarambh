"""Market data endpoints - Real data from yfinance with FRED for treasury yields"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from loguru import logger

from app.services.market_service import market_service

router = APIRouter()


class StockData(BaseModel):
    ticker: str
    name: str
    sector: str
    industry: str
    marketCap: float
    priceChange: float
    price: float
    volume: Optional[int] = None
    high52w: Optional[float] = None
    low52w: Optional[float] = None


class StockQuote(BaseModel):
    ticker: str
    name: str
    price: float
    change: float
    changePercent: float
    marketCap: float
    volume: int
    high52w: Optional[float] = None
    low52w: Optional[float] = None
    previousClose: Optional[float] = None


@router.get("/heatmap", response_model=List[StockData])
async def get_market_heatmap():
    """Get market heatmap data for treemap visualization (real-time via yfinance)."""
    try:
        stocks = await market_service.get_all_stocks()
        return [StockData(**stock) for stock in stocks]
    except Exception as e:
        logger.error(f"Error fetching market heatmap: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch market data")


@router.get("/quote/{ticker}")
async def get_stock_quote(ticker: str):
    """Get detailed quote for a specific stock."""
    ticker = ticker.upper()
    quote = await market_service.get_stock_quote(ticker)
    if not quote:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
    return quote


@router.get("/history/{ticker}")
async def get_stock_history(
    ticker: str,
    period: str = Query("1mo", description="Period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, ytd, max"),
    interval: str = Query("1d", description="Interval: 1m, 5m, 15m, 1h, 1d, 1wk, 1mo"),
):
    """Get historical price data for a stock (OHLCV)."""
    data = await market_service.get_historical_data(ticker.upper(), period, interval)
    if not data:
        raise HTTPException(status_code=404, detail=f"No historical data for {ticker}")
    return data


@router.get("/candles/{ticker}")
async def get_candles(
    ticker: str,
    timeframe: str = Query("1d", description="Timeframe: 1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M"),
    period: str = Query("6mo", description="Override period for daily+ timeframes"),
):
    """Get OHLCV candlestick data for charting."""
    data = await market_service.get_candles(ticker.upper(), timeframe, period)
    if not data:
        raise HTTPException(status_code=404, detail=f"No candle data for {ticker}")
    return data


@router.get("/indices")
async def get_indices():
    """Get real-time major index data (S&P 500, NASDAQ, Dow, global indices)."""
    return await market_service.get_indices()


@router.get("/crypto")
async def get_crypto():
    """Get real-time crypto prices (BTC, ETH, SOL, etc.)."""
    return await market_service.get_crypto()


@router.get("/treasury")
async def get_treasury():
    """Get treasury yield data from FRED (2Y, 5Y, 10Y, 30Y)."""
    return await market_service.get_treasury_yields()


@router.get("/fx")
async def get_fx():
    """Get real-time FX rates (USD/INR, EUR/USD, etc.)."""
    return await market_service.get_fx()


@router.get("/commodities")
async def get_commodities():
    """Get real-time commodity prices (Gold, Silver, Oil, etc.)."""
    return await market_service.get_commodities()


@router.get("/sectors")
async def get_sector_summary():
    """Get real sector performance from sector ETFs."""
    return await market_service.get_sector_summary()


@router.get("/profile/{ticker}")
async def get_stock_profile(ticker: str):
    """Get company profile (sector, industry, description, CEO, employees, etc.)."""
    profile = await market_service.get_stock_profile(ticker.upper())
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile not found for {ticker}")
    return profile


@router.get("/financials/{ticker}")
async def get_stock_financials(ticker: str):
    """Get financial statements (income, balance sheet, cash flow)."""
    data = await market_service.get_stock_financials(ticker.upper())
    if not data:
        raise HTTPException(status_code=404, detail=f"Financials not found for {ticker}")
    return data


@router.get("/ownership/{ticker}")
async def get_stock_ownership(ticker: str):
    """Get ownership data (major holders, institutional, mutual fund)."""
    data = await market_service.get_stock_holders(ticker.upper())
    if not data:
        raise HTTPException(status_code=404, detail=f"Ownership data not found for {ticker}")
    return data


@router.get("/ratings/{ticker}")
async def get_stock_ratings(ticker: str):
    """Get analyst recommendations."""
    data = await market_service.get_recommendations(ticker.upper())
    if not data:
        raise HTTPException(status_code=404, detail=f"Ratings not found for {ticker}")
    return data


@router.get("/compare")
async def compare_stocks(tickers: str = Query(..., description="Comma-separated tickers: AAPL,MSFT,GOOG")):
    """Compare multiple stocks side-by-side."""
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if not ticker_list:
        raise HTTPException(status_code=400, detail="Provide at least one ticker")
    return await market_service.get_compare(ticker_list)


@router.get("/research/{ticker}")
async def get_deep_ticker_research(
    ticker: str,
    provider: Optional[str] = Query(None),
    model: Optional[str] = Query(None)
):
    """Get exhaustive elaborated research for a specific ticker (YF + FMP + Web)."""
    data = await market_service.get_deep_ticker_research(ticker.upper(), provider=provider, model=model)
    if not data:
        raise HTTPException(status_code=404, detail=f"Research failed for {ticker}")
    return data
