from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.database import get_session, Event
from app.api.deps import get_current_user_optional

router = APIRouter()


class EventResponse(BaseModel):
    id: str
    title: str
    summary: str
    domain: str
    source: str
    source_url: Optional[str]
    published_at: datetime
    importance: int
    sentiment: float
    entities: List[str]
    is_new: bool

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    events: List[EventResponse]
    total: int
    page: int
    page_size: int


@router.get("/", response_model=EventListResponse)
async def list_events(
    domain: Optional[str] = None,
    source: Optional[str] = None,
    min_importance: Optional[int] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    user = Depends(get_current_user_optional),
):
    """List intelligence events with filters"""
    query = select(Event)

    if domain:
        query = query.where(Event.domain == domain)
    if source:
        query = query.where(Event.source == source)
    if min_importance:
        query = query.where(Event.importance >= min_importance)
    if search:
        query = query.where(
            Event.title.ilike(f"%{search}%") | Event.summary.ilike(f"%{search}%")
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query)

    # Paginate
    query = query.order_by(Event.published_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    events = result.scalars().all()

    return EventListResponse(
        events=[EventResponse.model_validate(e) for e in events],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    session: AsyncSession = Depends(get_session),
    user = Depends(get_current_user_optional),
):
    """Get a single event by ID"""
    query = select(Event).where(Event.id == event_id)
    result = await session.execute(query)
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return EventResponse.model_validate(event)
