"""routers/geo_intel.py - Geopolitical Router (WORKING endpoints only)"""
from fastapi import APIRouter, Query, Path
from scrapers import geo_intel as geo

router = APIRouter()


@router.get("/conflicts", summary="Active conflicts and related news")
async def conflicts():
    return await geo.get_conflicts()


@router.get("/sanctions", summary="Sanctions and diplomatic news")
async def sanctions():
    return await geo.get_sanctions()


@router.get("/elections", summary="Election news globally")
async def elections():
    return await geo.get_elections()


@router.get("/tensions", summary="Rising geopolitical tensions")
async def tensions():
    return await geo.get_tensions()


@router.get("/country/{code}", summary="Geopolitical news by country (verified: RU, CN, IN)")
async def country_geo(
    code: str = Path(..., description="Country code: RU, CN, IN"),
):
    return await geo.get_by_country(code)


@router.get("/risk-map", summary="Risk map data")
async def risk_map():
    return await geo.get_risk_map()


@router.get("/all", summary="All geopolitical news")
async def all_geo():
    return await geo.get_all()


@router.get("/site-map", summary="Working endpoints info")
async def site_map():
    return {
        "note": "Filtered to working endpoints only",
        "working": [
            "GET /conflicts - Active conflicts",
            "GET /sanctions - Sanctions news",
            "GET /elections - Election news",
            "GET /tensions - Rising tensions",
            "GET /country/{code} - By country: RU, CN, IN",
            "GET /risk-map - Risk map",
            "GET /all - All geo news",
        ],
        "filtered_out": [
            "GET /treaties - No substantive data",
            "GET /gdelt - API errors",
            "GET /gdelt/timeline - API errors",
        ],
    }
