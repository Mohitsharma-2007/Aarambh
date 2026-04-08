"""Graph Service for knowledge graph operations"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from collections import defaultdict

from app.database import Entity, Relationship


class GraphService:
    """Service for knowledge graph operations"""

    async def get_graph_data(
        self,
        session: AsyncSession,
        center_entity_id: Optional[str] = None,
        depth: int = 2,
        min_weight: float = 0.0,
    ) -> dict:
        """Get graph nodes and edges for visualization with full details"""
        nodes = []
        edges = []

        if center_entity_id:
            # Get subgraph centered on entity
            entity_ids = await self._get_connected_entities(
                session, center_entity_id, depth
            )
        else:
            # Get all entities
            query = select(Entity).order_by(Entity.importance.desc()).limit(200)
            result = await session.execute(query)
            entities = result.scalars().all()
            entity_ids = [e.id for e in entities]

        # Fetch entities
        if entity_ids:
            query = select(Entity).where(Entity.id.in_(entity_ids))
            result = await session.execute(query)
            entities = result.scalars().all()

            # Build entity map for quick lookup
            entity_map = {}
            for entity in entities:
                entity_map[entity.id] = entity
                nodes.append({
                    "uuid": entity.id,
                    "name": entity.name,
                    "labels": [entity.type, "Entity"],  # Zep compatibility
                    "type": entity.type,
                    "domain": entity.domain,
                    "importance": entity.importance,
                    "attributes": entity.attributes or {},
                    "summary": entity.summary or "",
                    "created_at": entity.created_at.isoformat() if hasattr(entity.created_at, 'isoformat') else str(entity.created_at) if entity.created_at else None,
                })

            # Fetch relationships
            query = select(Relationship).where(
                Relationship.source_id.in_(entity_ids)
            ).order_by(Relationship.created_at.desc())
            result = await session.execute(query)
            relationships = result.scalars().all()

            for rel in relationships:
                # Only include if target is also in our set
                if rel.target_id not in entity_map:
                    continue

                edges.append({
                    "uuid": rel.id,
                    "source_node_uuid": rel.source_id,
                    "target_node_uuid": rel.target_id,
                    "source_node_name": entity_map[rel.source_id].name,
                    "target_node_name": entity_map[rel.target_id].name,
                    "name": rel.relation_type,
                    "fact_type": rel.relation_type,
                    "fact": rel.fact or "",
                    "weight": rel.weight,
                    "attributes": rel.attributes or {},
                    "created_at": rel.created_at.isoformat() if hasattr(rel.created_at, 'isoformat') else str(rel.created_at) if rel.created_at else None,
                    "valid_at": rel.valid_at.isoformat() if hasattr(rel.valid_at, 'isoformat') else str(rel.valid_at) if rel.valid_at else None,
                    "invalid_at": rel.invalid_at.isoformat() if hasattr(rel.invalid_at, 'isoformat') else str(rel.invalid_at) if rel.invalid_at else None,
                    "episodes": rel.metadata_json.get("episodes", []) if rel.metadata_json else [],
                    "metadata": rel.metadata_json or {},
                })

        return {"nodes": nodes, "links": edges, "node_count": len(nodes), "edge_count": len(edges)}

    async def _get_connected_entities(
        self,
        session: AsyncSession,
        entity_id: str,
        depth: int,
    ) -> list[str]:
        """Get entity IDs connected within N hops"""
        visited = set([entity_id])
        current_level = [entity_id]

        for _ in range(depth):
            next_level = []

            query = select(Relationship).where(
                (Relationship.source_id.in_(current_level)) |
                (Relationship.target_id.in_(current_level))
            )
            result = await session.execute(query)
            rels = result.scalars().all()

            for rel in rels:
                if rel.source_id not in visited:
                    next_level.append(rel.source_id)
                    visited.add(rel.source_id)
                if rel.target_id not in visited:
                    next_level.append(rel.target_id)
                    visited.add(rel.target_id)

            current_level = next_level
            if not current_level:
                break

        return list(visited)

    async def find_paths(
        self,
        session: AsyncSession,
        source_id: str,
        target_id: str,
        max_depth: int = 4,
    ) -> list[list[str]]:
        """Find paths between two entities"""
        # BFS to find all paths up to max_depth
        paths = []
        queue = [(source_id, [source_id])]

        while queue:
            current_id, path = queue.pop(0)

            if len(path) > max_depth:
                continue

            if current_id == target_id:
                paths.append(path)
                continue

            # Get neighbors
            query = select(Relationship).where(
                (Relationship.source_id == current_id) |
                (Relationship.target_id == current_id)
            )
            result = await session.execute(query)
            rels = result.scalars().all()

            for rel in rels:
                neighbor = (
                    rel.target_id if rel.source_id == current_id
                    else rel.source_id
                )
                if neighbor not in path:
                    queue.append((neighbor, path + [neighbor]))

        return paths

    async def get_entity_importance(
        self,
        session: AsyncSession,
        entity_id: str,
    ) -> float:
        """Calculate entity importance based on connections"""
        query = select(Relationship).where(
            (Relationship.source_id == entity_id) |
            (Relationship.target_id == entity_id)
        )
        result = await session.execute(query)
        rels = result.scalars().all()

        # Simple importance: sum of weighted connections
        importance = sum(r.weight for r in rels)
        return min(importance / 10, 10.0)  # Normalize to 0-10

    async def get_domain_clusters(
        self,
        session: AsyncSession,
    ) -> dict[str, list[str]]:
        """Cluster entities by domain"""
        query = select(Entity)
        result = await session.execute(query)
        entities = result.scalars().all()

        clusters = defaultdict(list)
        for entity in entities:
            clusters[entity.domain].append(entity.id)

        return dict(clusters)


# Singleton instance
graph_service = GraphService()
