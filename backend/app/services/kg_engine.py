import json
import re
from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime

from app.services.ai_service import ai_service
from app.services.scraping_engine import scraping_engine
from app.services.validation_service import validation_service
from app.database import Entity, Relationship
from pydantic import BaseModel, Field

class DynamicNode(BaseModel):
    id: str
    name: str
    type: str
    importance: int = Field(5, ge=1, le=10)
    summary: str = ""

class DynamicEdge(BaseModel):
    source: str
    target: str
    relation: str
    fact: str = ""

class DynamicGraph(BaseModel):
    nodes: List[DynamicNode] = []
    edges: List[DynamicEdge] = []

class KGEngine:
    """
    Advanced Knowledge Graph Engine.
    Inspired by MiroFish, optimized for AARAMBH Finance & OSINT.
    Extracts entities and relationships from news and live search data.
    """

    # Semantic Categories for AARAMBH Knowledge Graph
    ENTITY_TYPES = [
        "Company", "CEO", "Investor", "Industry", "Country", 
        "EconomicIndicator", "Technology", "GeopoliticalEvent", 
        "Person", "Organization"
    ]

    RELATION_TYPES = [
        "ACQUIRED", "PARTNERED_WITH", "CEO_OF", "REGULATES", "INVESTED_IN",
        "LOCATED_IN", "COMPETES_WITH", "REPORTS_ON", "AFFECTS", "BELONGS_TO"
    ]

    async def build_dynamic_graph(self, query: str = "Indian Stock Market", depth: int = 1, provider: str = None, model: str = None) -> Dict[str, Any]:
        """
        Builds a real-time knowledge graph based on a search query.
        1. Scrapes news and AI snippets.
        2. Uses LLM to extract nodes and relationships.
        3. Returns a graph structure.
        """
        logger.info(f"Building dynamic graph for query: {query}")
        
        # 1. Gather context data
        news = await scraping_engine.google_news_search(query, limit=5)
        ai_snippet = await scraping_engine.google_ai_mode(query)
        
        context_text = f"Query: {query}\n\nAI Summary: {ai_snippet.get('answer', '')}\n\nLatest News:\n"
        for idx, item in enumerate(news):
            context_text += f"{idx+1}. {item['title']} (from {item['source']})\n"

        # 2. Extract Entities via LLM
        extraction_prompt = f"""
        Analyze the following financial/geopolitical context and extract a knowledge graph.
        
        CONTEXT:
        {context_text}
        
        TASK:
        Identify key entities and their relationships. 
        Use the following types ONLY:
        ENTITIES: {', '.join(self.ENTITY_TYPES)}
        RELATIONS: {', '.join(self.RELATION_TYPES)}
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "nodes": [
                {{"id": "entity_id", "name": "Name", "type": "Company/CEO/etc", "importance": 1-10, "summary": "Brief description"}}
            ],
            "edges": [
                {{"source": "source_id", "target": "target_id", "relation": "ACQUIRED/etc", "fact": "Description of why"}}
            ]
        }}
        
        Rules:
        1. 'id' should be a short lowercase slug (e.g. 'reliance_ind').
        2. Be precise. Only include clearly stated relationships.
        3. If a node is a CEO, link them to their Company.
        """

        try:
            # Use passed settings or defaults
            target_provider = provider or ai_service.provider
            target_model = model or ai_service.model

            response_text = await ai_service.query(
                extraction_prompt, 
                provider=target_provider, 
                model=target_model
            )
            
            validated = validation_service.parse_and_validate(response_text, DynamicGraph)
            if not validated:
                logger.error("LLM failed to return valid JSON for KG extraction")
                return {"nodes": [], "edges": [], "error": "Validation failed"}
            
            graph_data = validated.model_dump()
            
            # 3. Post-process: Add UUIDs (for frontend compatibility) and metadata
            for node in graph_data.get("nodes", []):
                node["uuid"] = node["id"]
                node["labels"] = [node["type"], "Entity"]
            
            for edge in graph_data.get("edges", []):
                edge["source_node_uuid"] = edge["source"]
                edge["target_node_uuid"] = edge["target"]
                edge["name"] = edge["relation"]
                edge["fact_type"] = edge["relation"]

            logger.info(f"Graph built: {len(graph_data.get('nodes', []))} nodes, {len(graph_data.get('edges', []))} edges")
            return graph_data

        except Exception as e:
            logger.error(f"KG Engine error: {e}")
            return {"nodes": [], "edges": [], "error": str(e)}

kg_engine = KGEngine()
