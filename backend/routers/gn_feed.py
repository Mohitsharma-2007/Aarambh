"""routers/gn_feed.py - Google News Router (WORKING endpoints only)"""
from fastapi import APIRouter, Query, Path
from scrapers import google_news as gn

router = APIRouter()


@router.get("/search", summary="Search news")
async def search(
    q: str = Query(..., description="Search query"),
    country: str = Query(None, description="Country code e.g. US, IN"),
):
    return await gn.search_news(q, country)


@router.get("/topic/{topic}", summary="News by topic")
async def topic(
    topic: str = Path(..., description="business|tech|technology|finance|world|science|health|sports|us"),
):
    return await gn.get_topic(topic)


@router.get("/ticker/{ticker}", summary="News for a stock ticker")
async def ticker_news(
    ticker: str = Path(..., description="Stock symbol e.g. AAPL, TSLA"),
):
    return await gn.get_ticker_news(ticker)


@router.get("/headlines", summary="Top headlines")
async def headlines(
    country: str = Query("US", description="Country code: US, IN"),
):
    return await gn.get_headlines(country)


@router.get("/company/{name}", summary="News by company name")
async def company(
    name: str = Path(..., description="Company name e.g. Apple, Tesla"),
    ticker: str = Query(None, description="Optional ticker for better results"),
):
    return await gn.get_company_news(name, ticker)
