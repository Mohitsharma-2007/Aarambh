"""routers/india_gov.py"""
from fastapi import APIRouter, Query, Path
from scrapers.india_portals import (
    india_portal_news, myscheme_search, myscheme_categories,
    nsws_search, rbi_get, rbi_key_rates, sebi_get,
    india_data_portal_search, mospi_get, mospi_releases,
    ndap_search_datasets, ndap_get_dataset, ndap_indicators,
)

router = APIRouter()

# ── india.gov.in ──────────────────────────────────────────────────────────────
@router.get("/news", summary="Latest news from india.gov.in")
async def india_news():
    return await india_portal_news()

# ── MyScheme ──────────────────────────────────────────────────────────────────
@router.get("/schemes/search", summary="Search government schemes")
async def schemes_search(q: str = Query(""), category: str = Query(""), state: str = Query("")):
    return await myscheme_search(q, category, state)

@router.get("/schemes/categories", summary="All scheme categories")
async def scheme_categories():
    return await myscheme_categories()

# ── RBI ───────────────────────────────────────────────────────────────────────
@router.get("/rbi/{feed}", summary="RBI press releases, circulars, notifications")
async def rbi(feed: str = Path(..., description="press_releases|circulars|notifications|publications|speeches")):
    return await rbi_get(feed)

@router.get("/rbi-rates", summary="RBI key policy rates")
async def rbi_rates():
    return await rbi_key_rates()

# ── SEBI ──────────────────────────────────────────────────────────────────────
@router.get("/sebi/{feed}", summary="SEBI circulars, press releases, orders, notices")
async def sebi(feed: str = Path(..., description="circulars|press_releases|orders|notices")):
    return await sebi_get(feed)

# ── NSWS ──────────────────────────────────────────────────────────────────────
@router.get("/nsws/search", summary="NSWS approvals and licenses search")
async def nsws(q: str = Query(...)):
    return await nsws_search(q)

# ── IndiaDataPortal ───────────────────────────────────────────────────────────
@router.get("/dataportal/search", summary="Search IndiaDataPortal datasets")
async def dataportal(q: str = Query(""), sector: str = Query("")):
    return await india_data_portal_search(q, sector)

# ── MoSPI ─────────────────────────────────────────────────────────────────────
@router.get("/mospi/{indicator}", summary="MoSPI statistical data")
async def mospi(indicator: str = Path(..., description="gdp|cpi|iip|nso")):
    return await mospi_get(indicator)

@router.get("/mospi-releases", summary="MoSPI press releases")
async def mospi_rel():
    return await mospi_releases()

# ── NDAP ─────────────────────────────────────────────────────────────────────
@router.get("/ndap/search", summary="Search NDAP datasets")
async def ndap_search(q: str = Query(""), sector: str = Query("")):
    return await ndap_search_datasets(q, sector)

@router.get("/ndap/dataset/{dataset_id}", summary="Get NDAP dataset by ID")
async def ndap_dataset(dataset_id: str):
    return await ndap_get_dataset(dataset_id)

@router.get("/ndap/indicators", summary="NDAP indicator catalogue")
async def ndap_ind():
    return await ndap_indicators()

# ── Indicator quick-access ────────────────────────────────────────────────────
@router.get("/indicator/{name}", summary="Key India economic indicator")
async def india_indicator(name: str = Path(...,
    description="gdp|inflation|unemployment|exports|imports|fdi|poverty|forex_reserves")):
    from scrapers.global_economy import world_bank_by_name
    return await world_bank_by_name("IN", name)
