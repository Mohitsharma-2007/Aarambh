"""Report Service - LLM-powered analysis reports from graph data (ported from MiroFish)"""
import uuid
from datetime import datetime
from typing import Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import Entity, Relationship, Event
from app.services.ai_service import ai_service


REPORT_PROMPT = """You are a senior intelligence analyst at India's AARAMBH Intelligence Terminal. Generate a comprehensive analysis report.

Focus: {focus}

Entities under analysis:
{entities}

Relationships:
{relationships}

Recent events:
{events}

Generate a structured report with the following sections:
1. Executive Summary (2-3 paragraphs)
2. Entity Analysis (key findings for each major entity)
3. Relationship Dynamics (how relationships are evolving)
4. Threat Assessment (potential risks and flashpoints)
5. Strategic Outlook (predictions and recommendations)

Format each section with clear headers. Be specific, cite entity names, and provide actionable intelligence.
Write in professional intelligence analysis style."""


class ReportService:
    """Generate intelligence analysis reports from graph data"""

    async def generate_report(
        self,
        entity_ids: list[str],
        focus: str = "comprehensive",
        session: AsyncSession = None,
        provider: str = None,
        model: str = None,
    ) -> dict:
        """Generate an analysis report for specified entities"""
        report_id = f"report_{uuid.uuid4().hex[:8]}"
        logger.info(f"Generating report {report_id}: focus={focus}")

        # Gather data
        entities_text = []
        relationships_text = []
        events_text = []

        if session:
            # Fetch entities
            if entity_ids:
                query = select(Entity).where(Entity.id.in_(entity_ids))
            else:
                query = select(Entity).order_by(Entity.importance.desc()).limit(20)
            result = await session.execute(query)
            entities = result.scalars().all()

            for e in entities:
                attrs = e.attributes or {}
                entities_text.append(
                    f"- {e.name} ({e.type}, {e.domain}, importance: {e.importance}/10)"
                    + (f" - {attrs}" if attrs else "")
                )

            eids = [e.id for e in entities]

            # Fetch relationships
            if eids:
                rel_query = select(Relationship).where(
                    Relationship.source_id.in_(eids) | Relationship.target_id.in_(eids)
                ).limit(50)
                rel_result = await session.execute(rel_query)
                rels = rel_result.scalars().all()

                name_lookup = {e.id: e.name for e in entities}
                for r in rels:
                    src = name_lookup.get(r.source_id, r.source_id)
                    tgt = name_lookup.get(r.target_id, r.target_id)
                    relationships_text.append(f"- {src} --[{r.relation_type} ({r.weight})]--> {tgt}")

            # Fetch recent events
            events_query = select(Event).order_by(Event.published_at.desc()).limit(20)
            events_result = await session.execute(events_query)
            events = events_result.scalars().all()

            for ev in events:
                events_text.append(f"- [{ev.domain}] {ev.title} (source: {ev.source}, importance: {ev.importance})")

        # Generate report with LLM
        try:
            prompt = REPORT_PROMPT.format(
                focus=focus,
                entities="\n".join(entities_text) or "No specific entities",
                relationships="\n".join(relationships_text) or "No relationships found",
                events="\n".join(events_text) or "No recent events",
            )

            # Use passed settings or defaults
            target_provider = provider or ai_service.provider
            target_model = model or ai_service.model

            response = await ai_service.query(prompt, provider=target_provider, model=target_model)

            # Parse into sections
            sections = self._parse_sections(response)

            return {
                "report_id": report_id,
                "title": f"Intelligence Analysis Report - {focus.title()}",
                "sections": sections,
                "summary": sections[0]["content"][:500] if sections else "Report generation completed.",
            }
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {
                "report_id": report_id,
                "title": f"Intelligence Analysis Report - {focus.title()}",
                "sections": [{
                    "title": "Executive Summary",
                    "content": f"Report generation encountered an error: {str(e)}. Please try again with fewer entities or a more specific focus.",
                }],
                "summary": f"Error generating report: {str(e)}",
            }

    def _parse_sections(self, text: str) -> list[dict]:
        """Parse markdown sections from LLM response"""
        sections = []
        current_title = "Executive Summary"
        current_content = []

        for line in text.split("\n"):
            # Detect section headers (## or #)
            if line.strip().startswith("##") or (line.strip().startswith("#") and not line.strip().startswith("###")):
                # Save previous section
                if current_content:
                    sections.append({
                        "title": current_title,
                        "content": "\n".join(current_content).strip(),
                    })
                current_title = line.strip().lstrip("#").strip()
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_content:
            sections.append({
                "title": current_title,
                "content": "\n".join(current_content).strip(),
            })

        # If no sections were detected, treat entire response as one section
        if not sections:
            sections = [{"title": "Analysis", "content": text.strip()}]

        return sections


# Singleton
report_service = ReportService()
