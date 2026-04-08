"""Investor endpoints - SEC EDGAR 13F filings + Congress trading data"""
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.services.investors_service import investors_service

router = APIRouter()


@router.get("/funds")
async def get_funds():
    """Get top institutional funds from SEC EDGAR"""
    return await investors_service.get_funds()


@router.get("/funds/{cik}/holdings")
async def get_fund_holdings(cik: str):
    """Get a fund's latest 13F holdings by CIK"""
    data = await investors_service.get_fund_holdings(cik)
    if not data:
        raise HTTPException(status_code=404, detail=f"No holdings found for CIK {cik}")
    return data


@router.get("/portfolios")
async def get_portfolios():
    """Get notable investor portfolio summary"""
    return await investors_service.get_portfolios()


@router.get("/congress")
async def get_congress_trades(
    chamber: str = Query(None, description="Filter by chamber: House, Senate"),
    ticker: str = Query(None, description="Filter by ticker symbol"),
):
    """Get recent congressional stock trades"""
    trades = await investors_service.get_congress_trades()
    if chamber:
        trades = [t for t in trades if t["chamber"].lower() == chamber.lower()]
    if ticker:
        trades = [t for t in trades if t["ticker"].upper() == ticker.upper()]
    return trades
