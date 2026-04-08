"""routers/health.py"""
from fastapi import APIRouter, Query, Path
from scrapers.health_scraper import (
    get_who_alerts, get_cdc_updates, get_health_news,
    filter_health_news, get_by_subcategory,
    get_health_by_country, get_health_categories
)

router = APIRouter()

@router.get("/news", summary="All health news (sorted by severity)")
async def health_news(count: int = Query(50)):
    return await get_health_news(count)

@router.get("/who-alerts", summary="WHO disease alerts and outbreak news")
async def who_alerts():
    return await get_who_alerts()

@router.get("/cdc-updates", summary="CDC health updates")
async def cdc_updates():
    return await get_cdc_updates()

@router.get("/filter", summary="Filter health news by keyword")
async def filter_news(
    keyword: str = Query(..., description="e.g. covid, cancer, vaccine, mental health"),
    count:   int = Query(30),
):
    return await filter_health_news(keyword, count)

@router.get("/subcategory/{subcat}", summary="Health news by sub-category")
async def by_subcategory(
    subcat: str = Path(...,
        description="infectious_disease|mental_health|cancer|cardiovascular|nutrition|pharmaceutical|public_health|medical_research"),
):
    return await get_by_subcategory(subcat)

@router.get("/country/{country}", summary="Health news for a country")
async def by_country(country: str = Path(..., description="IN|US|GB|DE|FR|AU etc.")):
    return await get_health_by_country(country)

@router.get("/categories", summary="All health sub-categories")
async def categories():
    return await get_health_categories()
