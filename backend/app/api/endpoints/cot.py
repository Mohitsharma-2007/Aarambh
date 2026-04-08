"""COT (Commitments of Traders) Data Endpoints"""
from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from loguru import logger

from app.services.cot_service import cot_service

router = APIRouter()

class COTData(BaseModel):
    market: str
    report_date: str
    non_commercial_long: int
    non_commercial_short: int
    commercial_long: int
    commercial_short: int
    open_interest: int
    net_non_commercial: int
    net_commercial: int


@router.get("/financial-futures", response_model=List[COTData])
async def get_cot_financial_futures():
    """
    Get COT data for financial futures markets (S&P 500, Nasdaq, etc.)
    """
    try:
        data = await cot_service.get_financial_futures_data()
        return [COTData(**item) for item in data]
    except Exception as e:
        logger.error(f"Error serving COT data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch COT data")