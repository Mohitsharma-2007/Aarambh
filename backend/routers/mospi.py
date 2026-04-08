"""routers/mospi.py"""
from fastapi import APIRouter, Query, Path
from scrapers.india_portals import mospi_get, mospi_releases

router = APIRouter()

@router.get("/gdp",           summary="GDP data from MoSPI/eSankhyiki")
async def gdp():       return await mospi_get("gdp")

@router.get("/cpi",           summary="Consumer Price Index")
async def cpi():       return await mospi_get("cpi")

@router.get("/iip",           summary="Index of Industrial Production")
async def iip():       return await mospi_get("iip")

@router.get("/releases",      summary="MoSPI press releases and reports")
async def releases():  return await mospi_releases()

@router.get("/indicator/{name}", summary="Any MoSPI indicator")
async def indicator(name: str = Path(..., description="gdp|cpi|iip|nso|census")):
    return await mospi_get(name)

@router.get("/esankhyiki",    summary="eSankhyiki portal info and links")
async def esankhyiki():
    return {
        "portal":       "eSankhyiki",
        "url":          "https://esankhyiki.mospi.gov.in",
        "description":  "Ministry of Statistics & Programme Implementation statistical portal",
        "datasets": [
            {"name": "National Accounts Statistics", "type": "GDP, GVA, NDP"},
            {"name": "Consumer Price Index",          "type": "Inflation"},
            {"name": "Index of Industrial Production","type": "IIP"},
            {"name": "Periodic Labour Force Survey",  "type": "Employment"},
            {"name": "Annual Survey of Industries",   "type": "Manufacturing"},
            {"name": "Economic Census",               "type": "Enterprise data"},
            {"name": "National Sample Survey",         "type": "Household surveys"},
        ],
        "direct_access": "https://esankhyiki.mospi.gov.in/esankhyiki/data-catalogue"
    }
