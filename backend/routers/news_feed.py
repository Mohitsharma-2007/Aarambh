"""routers/news_feed.py - News Platform Router (WORKING endpoints only)"""
from fastapi import APIRouter, Query, Path
from scrapers import rss_scraper as nf

router = APIRouter()


@router.get("/headlines", summary="Top headlines from all sources")
async def headlines():
    return await nf.get_headlines()


@router.get("/search", summary="Search news")
async def search(
    q: str = Query(..., description="Search query"),
):
    return await nf.search_news(q)


@router.get("/category/{category}", summary="News by category")
async def category(
    category: str = Path(..., description="finance|world|health|tech|technology|geopolitical|geo|politics|sports|science"),
):
    return await nf.get_by_category(category)


@router.get("/country/{code}", summary="News by country (verified: IN, US, GB)")
async def country(
    code: str = Path(..., description="Country code: IN, US, GB"),
):
    return await nf.get_by_country(code)


@router.get("/source/{name}", summary="News by source")
async def source(
    name: str = Path(..., description="bbc|cnn|bloomberg|bloomberg_markets|et_markets|al_jazeera|dw"),
):
    return await nf.get_by_source(name)


@router.get("/finance", summary="Finance news only")
async def finance_news():
    return await nf.get_finance_news()


@router.get("/trending", summary="Trending topics")
async def trending():
    return await nf.get_trending()


@router.get("/aggregate", summary="Aggregate multiple sources")
async def aggregate(
    sources: str = Query(..., description="Comma-separated source keys"),
):
    source_list = [s.strip() for s in sources.split(",") if s.strip()][:5]
    return await nf.aggregate_sources(source_list)


@router.get("/sources", summary="List all available sources")
async def list_sources():
    return await nf.get_sources()
