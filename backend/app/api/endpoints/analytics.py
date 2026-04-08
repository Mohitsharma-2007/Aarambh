from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.database import get_session, Event, Entity, Signal, User
from app.api.deps import get_current_user_optional

router = APIRouter()


class AnalyticsOverview(BaseModel):
    total_events: int
    total_entities: int
    active_signals: int
    events_today: int
    avg_sentiment: float
    domain_distribution: dict


class DomainStats(BaseModel):
    domain: str
    count: int
    percentage: float


class TimeSeriesPoint(BaseModel):
    date: str
    count: int


@router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    session: AsyncSession = Depends(get_session),
    user = Depends(get_current_user_optional),
):
    """Get analytics overview"""
    # Total events
    total_events = await session.scalar(select(func.count(Event.id)))

    # Total entities
    total_entities = await session.scalar(select(func.count(Entity.id)))

    # Active signals
    active_signals = await session.scalar(
        select(func.count(Signal.id)).where(Signal.status == "active")
    )

    # Events today
    today = datetime.utcnow().date()
    events_today = await session.scalar(
        select(func.count(Event.id)).where(func.date(Event.published_at) == today)
    )

    # Average sentiment
    avg_sentiment = await session.scalar(
        select(func.avg(Event.sentiment))
    ) or 0.0

    # Domain distribution
    domain_query = (
        select(Event.domain, func.count(Event.id).label("count"))
        .group_by(Event.domain)
    )
    domain_result = await session.execute(domain_query)
    domain_dist = {row.domain: row.count for row in domain_result}

    return AnalyticsOverview(
        total_events=total_events or 0,
        total_entities=total_entities or 0,
        active_signals=active_signals or 0,
        events_today=events_today or 0,
        avg_sentiment=round(avg_sentiment, 2),
        domain_distribution=domain_dist,
    )


@router.get("/domains", response_model=list[DomainStats])
async def get_domain_stats(
    session: AsyncSession = Depends(get_session),
    user = Depends(get_current_user_optional),
):
    """Get statistics by domain"""
    total = await session.scalar(select(func.count(Event.id))) or 1

    query = (
        select(Event.domain, func.count(Event.id).label("count"))
        .group_by(Event.domain)
        .order_by(func.count(Event.id).desc())
    )

    result = await session.execute(query)
    rows = result.all()

    return [
        DomainStats(
            domain=row.domain,
            count=row.count,
            percentage=round((row.count / total) * 100, 1)
        )
        for row in rows
    ]


@router.get("/timeseries", response_model=list[TimeSeriesPoint])
async def get_timeseries(
    days: int = 7,
    session: AsyncSession = Depends(get_session),
    user = Depends(get_current_user_optional),
):
    """Get event count time series"""
    start_date = datetime.utcnow() - timedelta(days=days)

    query = (
        select(
            func.date(Event.published_at).label("date"),
            func.count(Event.id).label("count")
        )
        .where(Event.published_at >= start_date)
        .group_by(func.date(Event.published_at))
        .order_by(func.date(Event.published_at))
    )

    result = await session.execute(query)
    rows = result.all()

    return [
        TimeSeriesPoint(
            date=str(row.date),
            count=row.count
        )
        for row in rows
    ]
