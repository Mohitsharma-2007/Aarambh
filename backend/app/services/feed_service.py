"""Feed Service for intelligence feed management"""
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import httpx
from loguru import logger

from app.database import Event, Entity
from app.services.ai_service import ai_service


class FeedService:
    """Service for managing intelligence feeds"""

    # Known sources
    SOURCES = {
        "MEA": "Ministry of External Affairs",
        "ORF": "Observer Research Foundation",
        "IDS": "Integrated Defence Staff",
        "DRDO": "Defence Research and Development Organisation",
        "ISRO": "Indian Space Research Organisation",
        "RBI": "Reserve Bank of India",
        "MOSPI": "Ministry of Statistics and Programme Implementation",
        "PRS": "PRS Legislative Research",
    }

    async def get_feed(
        self,
        session: AsyncSession,
        domain: Optional[str] = None,
        source: Optional[str] = None,
        min_importance: int = 0,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Event]:
        """Get filtered intelligence feed"""
        query = select(Event)

        conditions = []
        if domain:
            conditions.append(Event.domain == domain)
        if source:
            conditions.append(Event.source == source)
        if min_importance > 0:
            conditions.append(Event.importance >= min_importance)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(Event.published_at.desc())
        query = query.limit(limit).offset(offset)

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_trending(
        self,
        session: AsyncSession,
        hours: int = 24,
        limit: int = 10,
    ) -> list[Event]:
        """Get trending events in time window"""
        since = datetime.utcnow() - timedelta(hours=hours)

        query = (
            select(Event)
            .where(Event.published_at >= since)
            .order_by(Event.importance.desc())
            .limit(limit)
        )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def mark_as_read(
        self,
        session: AsyncSession,
        event_ids: list[str],
    ) -> int:
        """Mark events as read (not new)"""
        query = select(Event).where(Event.id.in_(event_ids))
        result = await session.execute(query)
        events = result.scalars().all()

        for event in events:
            event.is_new = False

        await session.commit()
        return len(events)

    async def get_domain_distribution(
        self,
        session: AsyncSession,
    ) -> dict[str, int]:
        """Get event count by domain"""
        query = (
            select(Event.domain, func.count(Event.id).label("count"))
            .group_by(Event.domain)
        )

        result = await session.execute(query)
        rows = result.all()

        return {row.domain: row.count for row in rows}

    async def ingest_event(
        self,
        session: AsyncSession,
        title: str,
        summary: str,
        domain: str,
        source: str,
        source_url: Optional[str] = None,
        published_at: Optional[datetime] = None,
        importance: int = 5,
    ) -> Event:
        """Ingest a new event into the feed"""
        # Analyze sentiment
        sentiment = await ai_service.analyze_sentiment(f"{title}\n{summary}")

        # Extract entities
        entities = await ai_service.extract_entities(f"{title}\n{summary}")
        entity_names = [e.get("name", "") for e in entities if e.get("name")]

        event = Event(
            title=title,
            summary=summary,
            domain=domain,
            source=source,
            source_url=source_url,
            published_at=published_at or datetime.utcnow(),
            importance=importance,
            sentiment=sentiment,
            entities=entity_names,
            is_new=True,
        )

        session.add(event)
        await session.commit()
        await session.refresh(event)

        logger.info(f"Ingested event: {event.id}")
        return event

    async def get_stats(
        self,
        session: AsyncSession,
    ) -> dict:
        """Get feed statistics"""
        total = await session.scalar(select(func.count(Event.id)))
        new_count = await session.scalar(
            select(func.count(Event.id)).where(Event.is_new == True)
        )
        today = datetime.utcnow().date()
        today_count = await session.scalar(
            select(func.count(Event.id)).where(func.date(Event.published_at) == today)
        )
        avg_sentiment = await session.scalar(
            select(func.avg(Event.sentiment))
        ) or 0.0

        return {
            "total_events": total or 0,
            "new_events": new_count or 0,
            "events_today": today_count or 0,
            "avg_sentiment": round(avg_sentiment, 2),
        }


# Singleton instance
feed_service = FeedService()
