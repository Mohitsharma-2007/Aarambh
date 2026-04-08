"""routers/health_intel.py - Health Router (WORKING endpoints only)"""
from fastapi import APIRouter, Query, Path
from scrapers import health_intel as health

router = APIRouter()


@router.get("/news", summary="Health & medical news")
async def health_news():
    return await health.get_health_news()


@router.get("/filter", summary="Filter health news by keyword")
async def filter_news(
    keyword: str = Query(..., description="Keyword e.g. covid, vaccine, cancer"),
):
    return await health.filter_by_keyword(keyword)


@router.get("/subcategory/{sub}", summary="Health subcategories")
async def subcategory(
    sub: str = Path(..., description="infectious_disease|mental_health|cancer|cardiovascular|diabetes"),
):
    return await health.get_by_subcategory(sub)


@router.get("/categories", summary="List health categories")
async def categories():
    return await health.get_categories()


@router.get("/site-map", summary="Working endpoints info")
async def site_map():
    return {
        "note": "Filtered to working endpoints only",
        "working": [
            "GET /news - Health news",
            "GET /filter?keyword=X - Filter by keyword",
            "GET /subcategory/{sub} - Subcategories",
            "GET /categories - List categories",
        ],
        "filtered_out": [
            "GET /who-alerts - No substantive data",
            "GET /cdc-updates - No substantive data",
            "GET /country/{code} - No substantive data",
        ],
    }
