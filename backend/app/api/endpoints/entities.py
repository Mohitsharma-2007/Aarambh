from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.database import get_session, Entity, Relationship
from app.api.deps import get_current_user_optional

router = APIRouter()


class EntityResponse(BaseModel):
    id: str
    name: str
    type: str
    domain: str
    attributes: Optional[dict] = {}
    importance: int
    created_at: datetime

    class Config:
        from_attributes = True


class EntityDetailResponse(EntityResponse):
    relationships: List[dict]
    recent_events: List[dict]


class EntityListResponse(BaseModel):
    entities: List[EntityResponse]
    total: int
    page: int
    page_size: int


@router.get("/", response_model=EntityListResponse)
async def list_entities(
    type: Optional[str] = None,
    domain: Optional[str] = None,
    search: Optional[str] = None,
    min_importance: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    user = Depends(get_current_user_optional),
):
    """List entities with filters"""
    query = select(Entity)

    if type:
        query = query.where(Entity.type == type)
    if domain:
        query = query.where(Entity.domain == domain)
    if min_importance:
        query = query.where(Entity.importance >= min_importance)
    if search:
        query = query.where(Entity.name.ilike(f"%{search}%"))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query)

    # Paginate
    query = query.order_by(Entity.importance.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    entities = result.scalars().all()

    return EntityListResponse(
        entities=[EntityResponse.model_validate(e) for e in entities],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.get("/{entity_id}", response_model=EntityDetailResponse)
async def get_entity(
    entity_id: str,
    session: AsyncSession = Depends(get_session),
    user = Depends(get_current_user_optional),
):
    """Get entity details with relationships"""
    query = select(Entity).where(Entity.id == entity_id)
    result = await session.execute(query)
    entity = result.scalar_one_or_none()

    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # Get relationships
    rel_query = select(Relationship).where(
        (Relationship.source_id == entity_id) | (Relationship.target_id == entity_id)
    )
    rel_result = await session.execute(rel_query)
    relationships = rel_result.scalars().all()

    rel_data = [
        {
            "id": r.id,
            "source_id": r.source_id,
            "target_id": r.target_id,
            "type": r.relation_type,
            "weight": r.weight,
        }
        for r in relationships
    ]

    return EntityDetailResponse(
        id=entity.id,
        name=entity.name,
        type=entity.type,
        domain=entity.domain,
        attributes=entity.attributes or {},
        importance=entity.importance,
        created_at=entity.created_at,
        relationships=rel_data,
        recent_events=[],  # Would fetch from events table
    )
