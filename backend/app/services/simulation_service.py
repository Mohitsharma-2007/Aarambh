"""Simulation Service - Simplified multi-agent simulation (ported from MiroFish)"""
import uuid
import random
from datetime import datetime
from typing import Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import Entity, Relationship
from app.services.ai_service import ai_service
from app.services.validation_service import validation_service
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class SimulationEvent(BaseModel):
    actor: str
    action: str
    target: str = "general"
    impact: str = "neutral"
    significance: int = Field(5, ge=1, le=10)

class RelationshipChange(BaseModel):
    source: str
    target: str
    change: str
    reason: str = ""

class SimulationRound(BaseModel):
    round: int
    timestamp: str = ""
    events: List[SimulationEvent] = []
    relationship_changes: List[RelationshipChange] = []
    analysis: str = ""


SIMULATION_PROMPT = """You are simulating a geopolitical scenario. Given these entities and their relationships, simulate {rounds} rounds of interaction.

Entities:
{entities}

Relationships:
{relationships}

Scenario: {scenario}

For each round, describe:
1. What actions each major entity takes
2. How relationships change
3. Key events that occur
4. Sentiment shifts

Return a JSON array of rounds:
[
  {{
    "round": 1,
    "timestamp": "Day 1",
    "events": [
      {{"actor": "Entity Name", "action": "description", "target": "Target Entity", "impact": "positive|negative|neutral", "significance": 1-10}}
    ],
    "relationship_changes": [
      {{"source": "Entity A", "target": "Entity B", "change": "strengthened|weakened|new|broken", "reason": "brief reason"}}
    ],
    "analysis": "Brief strategic analysis of this round"
  }}
]

Return ONLY valid JSON."""


class SimulationService:
    """Simplified multi-agent geopolitical simulation"""

    async def run_simulation(
        self,
        entity_ids: list[str],
        scenario: str,
        rounds: int = 5,
        session: AsyncSession = None,
        provider: str = None,
        model: str = None,
    ) -> dict:
        """Run a simplified simulation"""
        simulation_id = f"sim_{uuid.uuid4().hex[:8]}"
        logger.info(f"Starting simulation {simulation_id}: {scenario}")

        # ... (Fetch entities and relationships - unchanged logic)
        # Fetch entities
        entities_info = []
        relationships_info = []

        if session and entity_ids:
            query = select(Entity).where(Entity.id.in_(entity_ids))
            result = await session.execute(query)
            entities = result.scalars().all()

            for e in entities:
                entities_info.append(f"- {e.name} ({e.type}, {e.domain}, importance: {e.importance})")

            # Fetch relationships between these entities
            rel_query = select(Relationship).where(
                Relationship.source_id.in_(entity_ids),
                Relationship.target_id.in_(entity_ids),
            )
            rel_result = await session.execute(rel_query)
            rels = rel_result.scalars().all()

            # Build name lookup
            name_lookup = {e.id: e.name for e in entities}
            for r in rels:
                src_name = name_lookup.get(r.source_id, r.source_id)
                tgt_name = name_lookup.get(r.target_id, r.target_id)
                relationships_info.append(f"- {src_name} --[{r.relation_type}]--> {tgt_name} (weight: {r.weight})")

        if not entities_info:
            entities_info = ["- India (GPE, geopolitics, importance: 10)", "- China (GPE, geopolitics, importance: 9)", "- USA (GPE, geopolitics, importance: 9)"]
            relationships_info = ["- India --[OPPOSES]--> China", "- India --[ALLIED_WITH]--> USA", "- USA --[OPPOSES]--> China"]

        if not scenario:
            scenario = "Simulate the next month of geopolitical interactions between these entities, focusing on strategic moves, diplomatic shifts, and potential flashpoints."

        # Run LLM simulation
        try:
            prompt = SIMULATION_PROMPT.format(
                entities="\n".join(entities_info),
                relationships="\n".join(relationships_info),
                scenario=scenario,
                rounds=min(rounds, 10),
            )

            # Use passed settings or defaults
            target_provider = provider or ai_service.provider
            target_model = model or ai_service.model

            response = await ai_service.query(prompt, provider=target_provider, model=target_model)
            
            validated = validation_service.parse_and_validate(response, List[SimulationRound])
            sim_results = [r.model_dump() for r in validated] if validated else []

            if not sim_results:
                # Fallback if validation or parsing failed but query succeeded
                sim_results = [{"round": 1, "analysis": response[:1000], "events": [], "relationship_changes": []}]

            return {
                "simulation_id": simulation_id,
                "status": "completed",
                "rounds_completed": len(sim_results),
                "results": sim_results,
            }
        except Exception as e:
            logger.error(f"Simulation {simulation_id} failed: {e}")

            # Return basic simulation with random events
            return {
                "simulation_id": simulation_id,
                "status": "completed_with_fallback",
                "rounds_completed": rounds,
                "results": self._generate_fallback(entity_ids, rounds),
            }

    def _generate_fallback(self, entity_ids: list[str], rounds: int) -> list[dict]:
        """Generate basic fallback simulation data"""
        actions = ["diplomatic engagement", "military exercise", "trade negotiation", "sanctions threat", "intelligence operation", "cyber incident"]
        impacts = ["positive", "negative", "neutral"]

        results = []
        for r in range(1, rounds + 1):
            events = []
            for _ in range(random.randint(2, 4)):
                if len(entity_ids) >= 2:
                    actor = random.choice(entity_ids)
                    target = random.choice([e for e in entity_ids if e != actor])
                else:
                    actor = entity_ids[0] if entity_ids else "unknown"
                    target = "unknown"

                events.append({
                    "actor": actor,
                    "action": random.choice(actions),
                    "target": target,
                    "impact": random.choice(impacts),
                    "significance": random.randint(3, 8),
                })

            results.append({
                "round": r,
                "timestamp": f"Day {r * 3}",
                "events": events,
                "relationship_changes": [],
                "analysis": f"Round {r}: Multiple developments across tracked entities.",
            })

        return results


# Singleton
simulation_service = SimulationService()
