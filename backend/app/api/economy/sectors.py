"""routers/sectors.py"""
from fastapi import APIRouter, Query, Path
from scrapers.sectors import sector_list, get_sector_data, get_sector_news, SECTORS

router = APIRouter()

@router.get("/list", summary="All 31 sectors with metadata")
async def list_sectors():
    return sector_list()

@router.get("/{sector_key}", summary="Full data for a sector")
async def sector(sector_key: str = Path(...,
    description="e.g. Finance-Banking-Insurance, Agriculture-and-Cooperation")):
    return await get_sector_data(sector_key)

@router.get("/{sector_key}/news", summary="News and circulars for a sector")
async def sector_news(sector_key: str, count: int = Query(20)):
    return await get_sector_news(sector_key, count)

@router.get("/{sector_key}/info", summary="Sector metadata — APIs, ministries, indicators")
async def sector_info(sector_key: str):
    if sector_key not in SECTORS:
        return {"error": "Unknown sector. Use /api/sectors/list"}
    return {"sector_key": sector_key, **SECTORS[sector_key]}
