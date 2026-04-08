"""Ontology Engine Service - Query-driven Deep Research & Graph Construction"""
import asyncio
import json
import uuid
from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime

from app.services.ai_service import ai_service
from app.services.graph_builder_service import graph_builder_service
from app.database import async_session, Entity, Relationship
from app.config import LLMProvider
from sqlalchemy import select

class OntologyService:
    """Enterprise-grade Ontology Engine for AARAMBH"""

    async def run_ontology_research(self, query: str, rounds: int = 3, simulation: bool = True, provider: str = None, model: str = None) -> Dict[str, Any]:
        """
        Main entry point for the Ontology Engine.
        Process: Fetch Historical Data -> New Deep Research -> Combine -> Graph -> Simulation -> Save.
        """
        logger.info(f"Starting Ontology Research for query: {query}")
        
        historical_findings = []
        historical_entities = []
        
        # 0. Fetch Historical Context from Local DB
        try:
            async with async_session() as session:
                from app.database import ResearchRecord
                from sqlalchemy import select, func
                
                # Search for similar queries (case insensitive)
                stmt = select(ResearchRecord).where(ResearchRecord.query.ilike(f"%{query}%")).order_by(ResearchRecord.created_at.desc())
                past_records = await session.execute(stmt)
                past_records = past_records.scalars().all()
                
                if past_records:
                    logger.info(f"Found {len(past_records)} historical research records for: {query}")
                    for rec in past_records:
                        if rec.research_data:
                            historical_findings.extend(rec.research_data if isinstance(rec.research_data, list) else [rec.research_data])
                        if rec.entities:
                            historical_entities.extend(rec.entities if isinstance(rec.entities, list) else [rec.entities])
        except Exception as e:
            logger.warning(f"Error fetching historical research: {e}")

        research_id = str(uuid.uuid4())
        results = {
            "research_id": research_id,
            "query": query,
            "entities": [],
            "graph": {"nodes": [], "links": []},
            "research_data": [],
            "simulation_results": {},
            "final_report": "",
            "status": "processing",
            "combined_with_history": len(historical_findings) > 0
        }

        try:
            # 1. Brainstorm Entity Types (Living & Non-Living)
            entity_types = await self._brainstorm_entity_types(query, historical_entities, provider=provider, model=model)
            logger.info(f"Identified entity types: {entity_types}")
            results["entities"] = entity_types

            # 2. Parallel Deep Research (Everything, not a single thing left)
            research_tasks = []
            for etype in entity_types:
                research_tasks.append(self._deep_research_entity_type(query, etype, rounds, provider=provider, model=model))
            
            research_outputs = await asyncio.gather(*research_tasks)
            results["research_data"] = list(research_outputs)

            # Combine with historical findings for better mapping if they exist
            if historical_findings:
                # Treat historical findings as a special research fragment
                results["research_data"].append({
                    "entity_type": "HISTORICAL KNOWLEDGE BASE",
                    "content": "\n\n".join([str(h.get('content', h)) if isinstance(h, dict) else str(h) for h in historical_findings]),
                    "sources": [{"title": "AARAMBH Internal Cache", "url": "local-db", "snippet": "Consolidated historical intelligence findings"}]
                })

            # 3. Build Graph
            combined_text = "\n\n".join([r["content"] for r in research_outputs])
            async with async_session() as session:
                graph_result = await graph_builder_service.build_graph(
                    text=combined_text,
                    session=session,
                    provider=provider,
                    model=model
                )
                results["graph_summary"] = graph_result

            # 4. Run Simulations (Aspect-based thinking)
            if simulation:
                results["simulation_results"] = await self._run_entity_simulations(query, research_outputs, provider=provider, model=model)

            # 5. Generate Final Detailed Elaborated Report
            results["final_report"] = await self._generate_final_report(query, research_outputs, results["simulation_results"], provider=provider, model=model)
            
            # 6. Save to Database for History
            async with async_session() as session:
                from app.database import ResearchRecord
                new_record = ResearchRecord(
                    id=research_id,
                    query=query,
                    report=results["final_report"],
                    entities=entity_types,
                    research_data=research_outputs,
                    simulation_results=results["simulation_results"]
                )
                session.add(new_record)
                await session.commit()

            results["status"] = "completed"
            return results

        except Exception as e:
            logger.error(f"Ontology Engine Error: {e}")
            results["status"] = "error"
            results["error"] = str(e)
            return results

    async def _brainstorm_entity_types(self, query: str, historical_entities: List[str] = None, provider: str = None, model: str = None) -> List[str]:
        """Brainstorm all possible living/non-living entity types for a query"""
        hist_text = ", ".join(set(historical_entities)) if historical_entities else "None"
        prompt = f"""Given the intelligence query: '{query}'
        
        HISTORICAL RESEARCH CONTEXT (Known entities): {hist_text}
        
        Brainstorm and list ALL possible entity types that are critical to investigate for an EXHAUSTIVE research.
        Think about each aspect: 
        - LIVING: Persons (Leaders, Operatives, Scientists), Groups (Organizations, Tribes, Demographics), Social Aspects.
        - NON-LIVING: Assets (Infrastructure, Capital, Resources), States (Policies, Geopolitics), Technologies (Software, Hardware, R&D), Topics (Economics, Climate, Laws).
        
        Return a simple comma-separated list of the 8-12 most relevant entity types.
        No meta-commentary, just the list."""
        
        resp = await ai_service.query(prompt, model=model, provider=provider)
        types = [t.strip() for t in resp.split(",") if t.strip()]
        return types[:12]

    async def generate_ontology(self, text: str, provider: str = None, model: str = None) -> Dict[str, Any]:
        """
        Wizard compatibility: Brainstorms entity and edge types from text.
        Falls back to mock data if AI service fails.
        """
        logger.info(f"Generating ontology suggestion for: {text[:50]}...")
        
        try:
            # 1. Brainstorm types (Run in parallel)
            entity_types_task = self._brainstorm_entity_types(text, provider=provider, model=model)
            edge_types_task = self._brainstorm_edge_types(text, provider=provider, model=model)
            
            entity_types, edge_types = await asyncio.gather(entity_types_task, edge_types_task)
            
            # Validate that we got meaningful results
            if not entity_types or len(entity_types) < 2:
                raise ValueError("AI returned insufficient entity types")
            if not edge_types or len(edge_types) < 2:
                raise ValueError("AI returned insufficient edge types")
                
        except Exception as e:
            logger.warning(f"AI ontology generation failed, using fallback: {e}")
            # Fallback to mock data based on text analysis
            entity_types = self._generate_mock_entity_types(text)
            edge_types = self._generate_mock_edge_types(text)
        
        return {
            "entity_types": [{"name": t, "description": f"Entities related to {t}"} for t in entity_types],
            "edge_types": [{"name": t, "description": f"Relationship of type {t}"} for t in edge_types],
            "source_text_preview": text[:200]
        }
    
    def _generate_mock_entity_types(self, text: str) -> List[str]:
        """Generate mock entity types based on text keywords"""
        text_lower = text.lower()
        entity_types = []
        
        # Common entity type mappings
        keyword_map = {
            'india': 'Country',
            'china': 'Country',
            'usa': 'Country',
            'russia': 'Country',
            'pakistan': 'Country',
            'military': 'MilitaryOrganization',
            'defense': 'DefenseOrganization',
            'economy': 'EconomicEntity',
            'trade': 'TradeEntity',
            'technology': 'TechnologyCompany',
            'ai': 'AICompany',
            'geopolitics': 'GeopoliticalActor',
            'security': 'SecurityEntity',
            'intelligence': 'IntelligenceAgency',
            'government': 'GovernmentBody',
            'policy': 'PolicyMaker',
            'alliance': 'InternationalAlliance',
            'conflict': 'ConflictActor',
            'diplomacy': 'DiplomaticEntity',
            'sanctions': 'SanctionsEntity',
            'energy': 'EnergyCompany',
            'oil': 'EnergyResource',
            'nuclear': 'NuclearEntity',
            'space': 'SpaceAgency',
            'isro': 'SpaceAgency',
            'drdo': 'DefenseResearch',
            'tata': 'Conglomerate',
            'reliance': 'Conglomerate',
            'modi': 'PoliticalLeader',
            'putin': 'PoliticalLeader',
            'xi': 'PoliticalLeader',
            'trump': 'PoliticalLeader',
            'brics': 'InternationalAlliance',
            'quad': 'InternationalAlliance',
            'nato': 'MilitaryAlliance',
            'un': 'InternationalOrganization',
            'g20': 'EconomicForum',
        }
        
        for keyword, entity_type in keyword_map.items():
            if keyword in text_lower and entity_type not in entity_types:
                entity_types.append(entity_type)
        
        # Add default types if none found
        if len(entity_types) < 3:
            entity_types.extend(['Person', 'Organization', 'Location'])
        
        return entity_types[:8]
    
    def _generate_mock_edge_types(self, text: str) -> List[str]:
        """Generate mock edge types based on text keywords"""
        return [
            'LEADS',
            'MEMBER_OF',
            'COOPERATES_WITH',
            'OPPOSES',
            'ALLIED_WITH',
            'OWNS',
            'BASED_IN',
            'INFLUENCES',
            'TRADES_WITH',
            'DIPLOMATIC_RELATIONS'
        ]

    async def _brainstorm_edge_types(self, query: str, provider: str = None, model: str = None) -> List[str]:
        """Brainstorm relationship types for a query/text"""
        prompt = f"""Given the focus: '{query}'
        
        List ALL possible relationship types (edge labels) that are critical to map for EXHAUSTIVE graph research.
        Examples: INFLUENCES, ALLIED_WITH, COMPETES_WITH, FUNDED_BY, SUBSIDIARY_OF, OPERATES_IN.
        
        Return a simple comma-separated list of the 6-10 most relevant relationship types.
        No meta-commentary, just the list (use UPPERCASE_WITH_UNDERSCORES)."""
        
        resp = await ai_service.query(prompt, model=model, provider=provider)
        types = [t.strip().upper() for t in resp.replace("\n", ",").split(",") if t.strip()]
        return types[:10]

    async def _deep_research_entity_type(self, query: str, entity_type: str, rounds: int, provider: str = None, model: str = None) -> Dict[str, Any]:
        """Perform deep parallel research for a specific entity type using multiple models"""
        from duckduckgo_search import AsyncDDGS
        
        search_query = f"{query} {entity_type} details analysis"
        sources = []
        try:
            ddgs_results = await AsyncDDGS().text(search_query, max_results=rounds * 3)
            sources = [{"title": r["title"], "url": r["href"], "snippet": r["body"]} for r in ddgs_results]
        except:
            pass

        # Parallel aggregation using multiple free models
        sources_text = "\n".join([s["snippet"] for s in sources])
        prompts = [
            f"Analyze the following data about {entity_type} in context of {query}. Focus on strategic leverage. Data: {sources_text[:3000]}",
            f"Extract all key players and relationships for {entity_type} from this data: {sources_text[:3000]}",
            f"Assess the risks and future trajectory of {entity_type} related to {query}. Data: {sources_text[:3000]}"
        ]
        
        # Parallel execution
        batch_results = await ai_service.batch_query(prompts, provider=provider, model=model)
        
        combined_analysis = "\n\n".join([r["content"] for r in batch_results])
        
        return {
            "entity_type": entity_type,
            "content": combined_analysis,
            "sources": sources
        }

    async def _run_entity_simulations(self, query: str, research_data: List[dict], provider: str = None, model: str = None) -> Dict[str, Any]:
        """Run behavioral simulations for the entities found"""
        # Pick top entities from research
        summary = "\n".join([d["content"][:500] for d in research_data])
        prompt = f"""Based on this research summary, simulate the potential reactions and future actions of the primary actors involved:
        Query: {query}
        
        Research Context:
        {summary}
        
        Provide a table of Actor, Probable Action, and Impact."""
        
        resp = await ai_service.query(prompt, model=model, provider=provider)
        return {"simulation_text": resp}

    async def _generate_final_report(self, query: str, research_data: List[dict], simulations: dict, provider: str = None, model: str = None) -> str:
        """Generate the final properly elaborated report"""
        context = "\n\n".join([f"ENTITY TYPE: {d['entity_type']}\n{d['content']}" for d in research_data])
        
        prompt = f"""GENERATE AN EXHAUSTIVE, MULTI-DIMENSIONAL AND PROPERLY ELABORATED INTELLIGENCE REPORT.
        
        QUERY: {query}
        
        RESEARCH DATA ANALUTICS:
        {context[:12000]}
        
        SIMULATION MODELING:
        {simulations.get('simulation_text', '')}
        
        The report must be professional, highly detailed (3000+ words target depth), citing specific sources and data points found. 
        It must map complex relations and providing strategic, actionable insights for Indian national interests and global stability.
        
        STRICT STRUCTURE:
        1. EXECUTIVE INTELLIGENCE SUMMARY (High-level overview)
        2. ENTITY TAXONOMY & ONTOLOGY (Detailed breakdown of all living/non-living entities)
        3. DEEP ANALYTICAL CORRELATION (How entities interact, hidden networks, power dynamics)
        4. STRATEGIC LEVERAGE POINTS (Where intervention or monitoring is most effective)
        5. PROJECTED TRAJECTORIES (3-month, 1-year, and 5-year outlooks)
        6. SIMULATION OUTCOMES (Analysis of simulated reactions)
        7. VULNERABILITIES & RISKS (Specific threats identified)
        8. STRATEGIC RECOMMENDATIONS (Actionable counter-measures)
        9. SOURCE VERIFICATION INDEX (List of domains and credibility)
        
        Be precise. Use markdown for tables and hierarchy. DO NOT USE MOCK DATA. If information is missing, note it as an intelligence gap."""
        
        return await ai_service.query(prompt, model=model, provider=provider)

# Singleton
ontology_service = OntologyService()
