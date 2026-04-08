"""routers/pib.py"""
from fastapi import APIRouter, Query, Path
from scrapers.pib_scraper import (
    get_latest, search_pib, get_ministry_releases,
    get_sector_releases, get_document, get_circulars, MINISTRIES
)

router = APIRouter()

@router.get("/latest", summary="Latest PIB press releases")
async def latest(count: int = Query(30)):
    return await get_latest(count)

@router.get("/search", summary="Search PIB releases")
async def search(q: str = Query(..., description="e.g. GDP, inflation, scheme, budget"),
                 count: int = Query(20)):
    return await search_pib(q, count)

@router.get("/ministry/{key}", summary="Ministry-specific releases")
async def ministry(key: str = Path(..., description="finance|health|education|..."),
                   count: int = Query(20)):
    return await get_ministry_releases(key, count)

@router.get("/sector/{sector}", summary="Sector-filtered releases")
async def sector(sector: str = Path(..., description="agriculture|finance|health|energy|..."),
                 count: int = Query(25)):
    return await get_sector_releases(sector, count)

@router.get("/document", summary="Fetch and parse a PIB document")
async def document(url: str = Query(..., description="Full PIB document URL")):
    return await get_document(url)

@router.get("/circulars", summary="PIB circulars and notifications only")
async def circulars(count: int = Query(20)):
    return await get_circulars(count)

@router.get("/ministries", summary="List all ministries")
async def ministries():
    return {"ministries": MINISTRIES, "total": len(MINISTRIES)}
