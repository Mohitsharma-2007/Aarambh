"""routers/geopolitical.py"""
from fastapi import APIRouter, Query, Path
from scrapers.geopolitical import (
    gdelt_search, gdelt_timeline, get_conflicts, get_sanctions,
    get_elections, get_tensions, get_treaties,
    get_geo_by_country, get_all_geo_news, COUNTRY_RISK_BASE
)

router = APIRouter()

@router.get("/conflicts", summary="Active conflict zones and war news")
async def conflicts():
    return await get_conflicts()

@router.get("/sanctions", summary="Sanctions, embargoes, trade restrictions")
async def sanctions():
    return await get_sanctions()

@router.get("/elections", summary="Global election news")
async def elections():
    return await get_elections()

@router.get("/tensions", summary="Rising geopolitical tensions")
async def tensions():
    return await get_tensions()

@router.get("/treaties", summary="International agreements and diplomacy")
async def treaties():
    return await get_treaties()

@router.get("/country/{country}", summary="Geo news + risk score for a country")
async def by_country(
    country: str = Path(..., description="Country code: RU|UA|CN|IN|US|IR|IL etc.")
):
    return await get_geo_by_country(country)

@router.get("/gdelt", summary="GDELT Project real-time event search")
async def gdelt(
    query:    str = Query(..., description="Search query e.g. 'Ukraine war'"),
    records:  int = Query(25, description="Max records"),
):
    return await gdelt_search(query, max_records=records)

@router.get("/gdelt/timeline", summary="GDELT news volume timeline for a topic")
async def gdelt_vol(query: str = Query(..., description="Topic to track")):
    return await gdelt_timeline(query)

@router.get("/risk-map", summary="Global country risk scores")
async def risk_map():
    from scrapers.geopolitical import _risk_label
    return {
        "countries": [
            {"code": code, "score": score, "label": _risk_label(score)}
            for code, score in sorted(COUNTRY_RISK_BASE.items(),
                                      key=lambda x: -x[1])
        ],
        "note": "Scores 0-100. Higher = more risk. Based on conflict + political + economic factors."
    }

@router.get("/all", summary="All geopolitical news aggregated")
async def all_geo(count: int = Query(50)):
    return await get_all_geo_news(count)
