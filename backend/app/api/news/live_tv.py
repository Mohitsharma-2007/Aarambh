"""routers/live_tv.py"""
from fastapi import APIRouter, Query, Path
from scrapers.youtube_live import (
    get_all, get_by_country, get_by_category,
    search_channels, get_channel, get_finance_channels,
    get_world_channels, CHANNELS, COUNTRY_MAP, CATEGORY_MAP
)

router = APIRouter()

@router.get("/all", summary="All 50+ YouTube live TV channels")
async def all_channels(
    category: str = Query(None, description="Filter: news|finance|world"),
    country:  str = Query(None, description="Filter: IN|US|GB|CA|AU|DE|FR|JP etc."),
):
    return await get_all(category=category, country=country)

@router.get("/country/{country}", summary="Live TV channels by country")
async def by_country(country: str = Path(..., description="IN|US|GB|CA|AU|DE|FR|JP|CN|RU|BR|ZA")):
    return await get_by_country(country)

@router.get("/category/{category}", summary="Live TV by category")
async def by_category(category: str = Path(..., description="news|finance|world")):
    return await get_by_category(category)

@router.get("/finance", summary="Finance/Markets live channels")
async def finance_channels():
    return await get_finance_channels()

@router.get("/search", summary="Search live TV channels")
async def search(q: str = Query(..., description="Search query")):
    return await search_channels(q)

@router.get("/stream/{channel_key}", summary="Get embed URL for a channel")
async def stream(channel_key: str = Path(..., description="Channel key e.g. bloomberg_tv, cnbc")):
    return await get_channel(channel_key)

@router.get("/directory", summary="Full channel directory")
async def directory():
    return {
        "total":      len(CHANNELS),
        "countries":  list(COUNTRY_MAP.keys()),
        "categories": list(CATEGORY_MAP.keys()),
        "channels": {
            k: {"name": v["name"], "country": v["country"],
                "category": v["category"], "lang": v["lang"],
                "youtube": f"https://www.youtube.com/@{v['handle']}/live"}
            for k, v in CHANNELS.items()
        },
    }
