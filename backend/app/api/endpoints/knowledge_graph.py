from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any

from app.database import get_session
from app.services.kg_engine import kg_engine
from app.services.graph_service import graph_service

router = APIRouter()

@router.get("/dynamic")
async def get_dynamic_graph(
    q: str = Query(..., description="Query to build graph from"),
    depth: int = Query(1, ge=1, le=3),
    provider: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
):
    """
    Builds a dynamic real-time knowledge graph using LLM extraction from live sources.
    Matches the 'Modified Backend' request inspired by MiroFish.
    """
    return await kg_engine.build_dynamic_graph(q, depth, provider=provider, model=model)

@router.get("/snapshot")
async def get_graph_snapshot(
    center_id: Optional[str] = None,
    depth: int = Query(2, ge=1, le=5),
    session: AsyncSession = Depends(get_session),
):
    """Get current graph structure from the database"""
    return await graph_service.get_graph_data(session, center_entity_id=center_id, depth=depth)

@router.post("/research")
async def run_ontology_research(
    data: Dict[str, Any],
):
    """
    Trigger exhaustive deep research and ontology build for a query.
    """
    from app.services.ontology_service import ontology_service
    query = data.get("query")
    rounds = data.get("rounds", 3)
    simulation = data.get("simulation", True)
    provider = data.get("provider")
    model = data.get("model")
    
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
        
    return await ontology_service.run_ontology_research(query, rounds, simulation, provider=provider, model=model)

@router.get("/history")
async def get_research_history(limit: int = 20):
    """Get past research records"""
    from app.database import async_session, ResearchRecord
    from sqlalchemy import select
    
    async with async_session() as session:
        stmt = select(ResearchRecord).order_by(ResearchRecord.created_at.desc()).limit(limit)
        result = await session.execute(stmt)
        records = result.scalars().all()
        return records

@router.get("/history/{research_id}")
async def get_research_detail(research_id: str):
    """Get specific research record detail"""
    from app.database import async_session, ResearchRecord
    from sqlalchemy import select
    
    async with async_session() as session:
        stmt = select(ResearchRecord).where(ResearchRecord.id == research_id)
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            raise HTTPException(status_code=404, detail="Research record not found")
        return record

