"""Graph API endpoints for knowledge graph visualization and MiroFish features"""
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from pydantic import BaseModel
from loguru import logger

from app.database import get_session, Entity, Relationship
from app.api.deps import get_current_user_optional
from app.services.graph_service import graph_service

router = APIRouter()


class GraphNode(BaseModel):
    uuid: str
    name: str
    type: str
    domain: str
    importance: float
    summary: Optional[str] = None
    attributes: Optional[dict] = {}


class GraphLink(BaseModel):
    uuid: str
    source_node_uuid: str
    target_node_uuid: str
    source_node_name: Optional[str] = None
    target_node_name: Optional[str] = None
    name: str
    fact: Optional[str] = None
    weight: float
    attributes: Optional[dict] = {}


class GraphData(BaseModel):
    nodes: List[GraphNode]
    links: List[GraphLink]


class OntologyEntityType(BaseModel):
    name: str
    description: str
    color: str | None = None


class OntologyEdgeType(BaseModel):
    name: str
    description: str
    source_types: List[str] = []
    target_types: List[str] = []


class OntologyResponse(BaseModel):
    entity_types: List[OntologyEntityType]
    edge_types: List[OntologyEdgeType]
    source_text_preview: str | None = None


class GraphBuildRequest(BaseModel):
    text: str | None = None
    entity_types: List[str] = []
    edge_types: List[str] = []
    provider: Optional[str] = None
    model: Optional[str] = None
    force: bool = False  # Force rebuild by clearing existing graph first


class GraphBuildResponse(BaseModel):
    nodes_created: int
    edges_created: int
    total_entities: int = 0
    total_relationships: int = 0
    message: str


class GraphClearResponse(BaseModel):
    nodes_deleted: int
    edges_deleted: int
    message: str


class SimulationRequest(BaseModel):
    entity_ids: List[str] = []
    scenario: str = ""
    rounds: int = 5
    provider: Optional[str] = None
    model: Optional[str] = None


class SimulationResponse(BaseModel):
    simulation_id: str
    status: str
    rounds_completed: int
    results: List[dict]


class ReportRequest(BaseModel):
    entity_ids: List[str] = []
    focus: str = "comprehensive"
    provider: Optional[str] = None
    model: Optional[str] = None


class ReportResponse(BaseModel):
    report_id: str
    title: str
    sections: List[dict]
    summary: str


@router.get("/data", response_model=GraphData)
async def get_graph_data(
    center_entity_id: Optional[str] = None,
    depth: int = Query(2, ge=1, le=4),
    min_weight: float = Query(0.0, ge=0, le=1),
    domain: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user_optional),
):
    """Get knowledge graph data from database for visualization"""
    result = await graph_service.get_graph_data(
        session,
        center_entity_id=center_entity_id,
        depth=depth,
        min_weight=min_weight,
    )

    nodes = result.get("nodes", [])
    links = result.get("links", [])

    # Filter by domain if specified
    if domain:
        node_ids = {n["uuid"] for n in nodes if n.get("domain") == domain}
        nodes = [n for n in nodes if n["uuid"] in node_ids]
        links = [l for l in links if l["source_node_uuid"] in node_ids or l["target_node_uuid"] in node_ids]

    return GraphData(
        nodes=[GraphNode(**n) for n in nodes],
        links=[GraphLink(**l) for l in links],
    )


@router.get("/stats")
async def get_graph_stats(
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user_optional),
):
    """Get graph statistics"""
    node_count = await session.scalar(select(func.count(Entity.id))) or 0
    edge_count = await session.scalar(select(func.count(Relationship.id))) or 0

    # Domain distribution
    domain_query = select(Entity.domain, func.count(Entity.id).label("count")).group_by(Entity.domain)
    domain_result = await session.execute(domain_query)
    domains = {row.domain: row.count for row in domain_result}

    # Type distribution
    type_query = select(Entity.type, func.count(Entity.id).label("count")).group_by(Entity.type)
    type_result = await session.execute(type_query)
    types = {row.type: row.count for row in type_result}

    # Relationship type distribution
    rel_query = select(Relationship.relation_type, func.count(Relationship.id).label("count")).group_by(Relationship.relation_type)
    rel_result = await session.execute(rel_query)
    rel_types = {row.relation_type: row.count for row in rel_result}

    return {
        "total_nodes": node_count,
        "total_edges": edge_count,
        "domains": domains,
        "entity_types": types,
        "relationship_types": rel_types,
    }


@router.get("/paths")
async def find_paths(
    source_id: str = Query(...),
    target_id: str = Query(...),
    max_depth: int = Query(4, ge=1, le=6),
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user_optional),
):
    """Find paths between two entities"""
    paths = await graph_service.find_paths(session, source_id, target_id, max_depth)
    return {"paths": paths, "count": len(paths)}


@router.get("/clusters")
async def get_clusters(
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user_optional),
):
    """Get entity clusters by domain"""
    clusters = await graph_service.get_domain_clusters(session)
    return {"clusters": clusters}


# ── MiroFish Features ──

class OntologyGenerateRequest(BaseModel):
    text: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None


@router.post("/ontology/generate", response_model=OntologyResponse)
async def generate_ontology(
    request: OntologyGenerateRequest,
):
    """Generate ontology from text or uploaded document"""
    from app.services.ontology_service import ontology_service

    input_text = request.text or ""
    req_provider = request.provider
    req_model = request.model

    if not input_text.strip():
        raise HTTPException(status_code=400, detail="Provide text or upload a file")

    result = await ontology_service.generate_ontology(input_text, provider=req_provider, model=req_model)
    return OntologyResponse(**result)


@router.post("/clear", response_model=GraphClearResponse)
async def clear_graph(
    session: AsyncSession = Depends(get_session),
):
    """Clear all nodes and edges from the knowledge graph"""
    from sqlalchemy import delete
    
    # Count before deletion
    node_count = await session.scalar(select(func.count(Entity.id))) or 0
    edge_count = await session.scalar(select(func.count(Relationship.id))) or 0
    
    # Delete all relationships first (foreign key constraint)
    await session.execute(delete(Relationship))
    
    # Delete all entities
    await session.execute(delete(Entity))
    
    await session.commit()
    
    return GraphClearResponse(
        nodes_deleted=node_count,
        edges_deleted=edge_count,
        message=f"Cleared {node_count} nodes and {edge_count} edges from the graph"
    )


@router.post("/build", response_model=GraphBuildResponse)
async def build_graph_from_text(
    request: GraphBuildRequest,
    session: AsyncSession = Depends(get_session),
):
    """Build knowledge graph from text using LLM"""
    from app.services.graph_builder_service import graph_builder_service
    from sqlalchemy import delete
    
    if not request.text:
        raise HTTPException(status_code=400, detail="Text is required")

    # If force=True, clear existing graph first
    if request.force:
        logger.info("Force rebuild requested - clearing existing graph data")
        await session.execute(delete(Relationship))
        await session.execute(delete(Entity))
        await session.commit()

    result = await graph_builder_service.build_graph(
        text=request.text,
        entity_types=request.entity_types,
        edge_types=request.edge_types,
        session=session,
        provider=request.provider,
        model=request.model,
    )
    return GraphBuildResponse(**result)


@router.post("/extract")
async def extract_entities_from_text(
    request: GraphBuildRequest,
    use_mock: bool = Query(False, description="Force use of mock extraction (skip AI)"),
):
    """Extract entities from text without saving to database (for testing)"""
    from app.services.graph_builder_service import graph_builder_service

    if not request.text:
        raise HTTPException(status_code=400, detail="Text is required")

    entity_types = request.entity_types or ["GPE", "PERSON", "ORG", "EVENT", "ASSET", "TOPIC"]
    edge_types = request.edge_types or ["ALLIED_WITH", "OPPOSES", "COOPERATES_WITH", "LEADS", "MEMBER_OF", "RELATED_TO"]

    if use_mock:
        # Use mock extraction directly
        result = graph_builder_service._extract_mock_entities(request.text, entity_types, edge_types)
    else:
        # Use the full extraction pipeline (AI with fallback to mock)
        result = await graph_builder_service._extract_from_chunk(
            request.text, entity_types, edge_types, chunk_idx=0,
            provider=request.provider, model=request.model
        )
    
    return {
        "entities": result.get("entities", []),
        "relationships": result.get("relationships", []),
        "entity_count": len(result.get("entities", [])),
        "relationship_count": len(result.get("relationships", []))
    }


@router.post("/simulate", response_model=SimulationResponse)
async def run_simulation(
    request: SimulationRequest,
    session: AsyncSession = Depends(get_session),
):
    """Run simplified multi-agent simulation on graph entities"""
    from app.services.simulation_service import simulation_service

    result = await simulation_service.run_simulation(
        entity_ids=request.entity_ids,
        scenario=request.scenario,
        rounds=request.rounds,
        session=session,
        provider=request.provider,
        model=request.model,
    )
    return SimulationResponse(**result)


@router.post("/report", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    session: AsyncSession = Depends(get_session),
):
    """Generate analysis report from graph data"""
    from app.services.report_service import report_service

    result = await report_service.generate_report(
        entity_ids=request.entity_ids,
        focus=request.focus,
        session=session,
        provider=request.provider,
        model=request.model,
    )
    return ReportResponse(**result)
