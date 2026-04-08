"""routers/ndap.py"""
from fastapi import APIRouter, Query, Path
from scrapers.india_portals import ndap_search_datasets, ndap_get_dataset, ndap_indicators

router = APIRouter()

@router.get("/datasets", summary="Search NDAP dataset catalogue")
async def datasets(q: str = Query("", description="Search keyword"),
                   sector: str = Query("", description="Sector filter"),
                   page: int = Query(1), size: int = Query(20)):
    return await ndap_search_datasets(q, sector, page, size)

@router.get("/dataset/{id}", summary="Fetch NDAP dataset by ID")
async def dataset(id: str = Path(...)):
    return await ndap_get_dataset(id)

@router.get("/indicators", summary="All NDAP indicators")
async def indicators():
    return await ndap_indicators()

@router.get("/sectors", summary="NDAP sector list")
async def sectors():
    return {
        "source": "NDAP / NITI Aayog",
        "sectors": [
            "Agriculture", "Animal Husbandry", "Commerce", "Defence",
            "Education", "Employment", "Energy", "Environment", "Finance",
            "Food", "Forestry", "Governance", "Health", "Housing",
            "Industry", "Infrastructure", "Law", "Petroleum", "Rural",
            "Science", "Social Welfare", "Statistics", "Tourism", "Transport"
        ]
    }
