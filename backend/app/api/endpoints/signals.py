from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.database import get_session, Signal
from app.api.deps import get_current_user_optional
from app.services.signal_service import signal_service

router = APIRouter()


class SignalResponse(BaseModel):
    id: str
    name: str
    type: str
    status: str
    severity: str
    trigger_count: int
    last_triggered: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class SignalCreate(BaseModel):
    name: str
    type: str  # keyword, entity, pattern, anomaly
    severity: str = "medium"
    config: dict = {}


class SignalListResponse(BaseModel):
    signals: List[SignalResponse]
    total: int


@router.get("/", response_model=SignalListResponse)
async def list_signals(
    status: str = None,
    session: AsyncSession = Depends(get_session),
    user = Depends(get_current_user_optional),
):
    """List signals"""
    query = select(Signal)

    if status:
        query = query.where(Signal.status == status)

    query = query.order_by(Signal.created_at.desc())
    result = await session.execute(query)
    signals = result.scalars().all()

    return SignalListResponse(
        signals=[SignalResponse.model_validate(s) for s in signals],
        total=len(signals),
    )


@router.post("/", response_model=SignalResponse)
async def create_signal(
    signal_data: SignalCreate,
    session: AsyncSession = Depends(get_session),
    user = Depends(get_current_user_optional),
):
    """Create a new signal"""
    signal = Signal(
        name=signal_data.name,
        type=signal_data.type,
        severity=signal_data.severity,
        config=signal_data.config,
    )

    session.add(signal)
    await session.commit()
    await session.refresh(signal)

    return SignalResponse.model_validate(signal)


@router.put("/{signal_id}/pause", response_model=SignalResponse)
async def pause_signal(
    signal_id: str,
    session: AsyncSession = Depends(get_session),
    user = Depends(get_current_user_optional),
):
    """Pause a signal"""
    query = select(Signal).where(Signal.id == signal_id)
    result = await session.execute(query)
    signal = result.scalar_one_or_none()

    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    signal.status = "paused"
    await session.commit()
    await session.refresh(signal)

    return SignalResponse.model_validate(signal)


@router.put("/{signal_id}/resume", response_model=SignalResponse)
async def resume_signal(
    signal_id: str,
    session: AsyncSession = Depends(get_session),
    user = Depends(get_current_user_optional),
):
    """Resume a paused signal"""
    query = select(Signal).where(Signal.id == signal_id)
    result = await session.execute(query)
    signal = result.scalar_one_or_none()

    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    signal.status = "active"
    await session.commit()
    await session.refresh(signal)

    return SignalResponse.model_validate(signal)


@router.get("/scan")
async def scan_signals(
    tickers: Optional[str] = Query(None, description="Comma-separated tickers to scan"),
):
    """Scan watchlist for real technical analysis signals (RSI, MACD, Bollinger, etc.)"""
    ticker_list = [t.strip().upper() for t in tickers.split(",")] if tickers else None
    return await signal_service.scan_signals(ticker_list)


@router.get("/quant/{ticker}")
async def get_quant_metrics(ticker: str):
    """Get full quantitative metrics for a single ticker"""
    data = await signal_service.get_quant_metrics(ticker.upper())
    if not data:
        raise HTTPException(status_code=404, detail=f"No quant data for {ticker}")
    return data


@router.get("/quant/{ticker}/analyze")
async def analyze_quant_metrics(
    ticker: str,
    provider: Optional[str] = Query(None),
    model: Optional[str] = Query(None)
):
    """Use AI to interpret a ticker's technical metrics"""
    ticker = ticker.upper()
    data = await signal_service.get_quant_metrics(ticker)
    if not data:
        raise HTTPException(status_code=404, detail=f"No data to analyze for {ticker}")
    
    analysis = await signal_service.analyze_quant_metrics(ticker, data, provider=provider, model=model)
    return {"ticker": ticker, "analysis": analysis}
