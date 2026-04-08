"""Graph Builder Service - Full MiroFish port using SQLite + LLM (no Zep)"""
import json
import re
import uuid
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import Entity, Relationship
from app.services.ai_service import ai_service
from app.services.validation_service import validation_service
from pydantic import BaseModel, Field

class EntityExtraction(BaseModel):
    name: str
    type: str
    domain: str = "geopolitics"
    importance: int = Field(5, ge=1, le=10)
    attributes: Dict[str, Any] = {}

class RelationshipExtraction(BaseModel):
    source: str
    target: str
    type: str
    weight: float = Field(0.5, ge=0, le=1)
    evidence: str = ""

class GraphExtraction(BaseModel):
    entities: List[EntityExtraction] = []
    relationships: List[RelationshipExtraction] = []


EXTRACT_PROMPT = """You are an expert intelligence analyst extracting structured knowledge from text.

**Ontology Definition**

Entity Types to Identify:
{entity_types_str}

Relationship Types to Identify:
{edge_types_str}

**Instructions**

1. Extract all entities that match the defined entity types.
2. For each entity, provide:
   - name: The exact name as it appears in text (normalized)
   - type: Must be one of the entity types above
   - domain: One of: geopolitics, economics, defense, technology, climate, society
   - importance: Integer 1-10 (10 = most important)
   - attributes: Any additional properties mentioned

3. Extract relationships between entities.
   - source: Exact entity name (must match an extracted entity)
   - target: Exact entity name
   - type: Must be one of the relationship types above
   - weight: Float 0.1-1.0 (confidence/strength)
   - evidence: Brief explanation from text

4. Resolve coreferences: If the same entity appears with different names, consolidate.

**Output Format**

Return ONLY valid JSON:

{{
  "entities": [
    {{
      "name": "Entity Name",
      "type": "EntityType",
      "domain": "geopolitics",
      "importance": 8,
      "attributes": {{"key": "value"}}
    }}
  ],
  "relationships": [
    {{
      "source": "Entity A",
      "target": "Entity B",
      "type": "RELATIONSHIP_TYPE",
      "weight": 0.85,
      "evidence": "Brief explanation from text"
    }}
  ]
}}

**Text to Analyze**

{text}

Return ONLY the JSON. No explanations."""


class GraphBuilderService:
    """Build knowledge graphs from text with proper entity resolution and episode tracking"""

    def __init__(self):
        self.max_chunks = 20  # Limit processing to prevent timeouts

    async def build_graph(
        self,
        text: str,
        entity_types: List[str] = None,
        edge_types: List[str] = None,
        session: AsyncSession = None,
        graph_ontology: Dict[str, Any] = None,
        provider: str = None,
        model: str = None,
    ) -> Dict[str, Any]:
        """
        Extract entities and relationships from text and save to database

        Args:
            text: Input document text
            entity_types: List of allowed entity type names
            edge_types: List of allowed relationship type names
            session: Database session
            graph_ontology: Full ontology definition (including attributes, etc.)
            provider: LLM Provider
            model: LLM Model

        Returns:
            Dict with nodes_created, edges_created, message
        """
        # Use defaults if not provided or empty
        if not entity_types:
            entity_types = ["GPE", "PERSON", "ORG", "EVENT", "ASSET", "TOPIC"]
        if not edge_types:
            edge_types = ["ALLIED_WITH", "OPPOSES", "COOPERATES_WITH", "LEADS", "MEMBER_OF", "RELATED_TO"]

        logger.info(f"Building graph with entity_types={entity_types}, edge_types={edge_types}")

        # Chunk text for processing
        chunks = self._chunk_text(text, chunk_size=3000, overlap=200)
        if len(chunks) > self.max_chunks:
            logger.warning(f"Truncating text chunks from {len(chunks)} to {self.max_chunks}")
            chunks = chunks[:self.max_chunks]

        logger.info(f"Processing {len(chunks)} text chunks for graph extraction")

        # Accumulate entities and relationships across all chunks
        all_entities: Dict[str, Dict[str, Any]] = {}
        all_relationships: List[Dict[str, Any]] = []
        chunk_episodes: List[Dict[str, Any]] = []  # Track which chunk each fact came from

        for chunk_idx, chunk in enumerate(chunks):
            try:
                result = await self._extract_from_chunk(
                    chunk, entity_types, edge_types, chunk_idx, provider=provider, model=model
                )
                if result and "entities" in result:
                    # Entity resolution: normalize names and merge duplicates
                    for ent in result["entities"]:
                        normalized_name = self._normalize_entity_name(ent.get("name", ""))
                        if not normalized_name:
                            continue

                        # Determine entity type - pass allowed types for proper mapping
                        raw_type = ent.get("type", "Organization")
                        ent_type = self._map_entity_type(raw_type, entity_types)
                        # Ensure it's in our allowed types
                        if ent_type not in entity_types:
                            # Try to find closest match
                            ent_type = self._find_closest_type(ent_type, entity_types)
                            logger.debug(f"Mapped type {raw_type} -> {ent_type}")

                        domain = ent.get("domain", "geopolitics")
                        importance = max(1, min(10, int(ent.get("importance", 5))))

                        if normalized_name not in all_entities:
                            all_entities[normalized_name] = {
                                "id": self._generate_entity_id(normalized_name),
                                "name": ent.get("name", normalized_name).strip(),
                                "normalized_name": normalized_name,
                                "type": ent_type,
                                "domain": domain,
                                "importance": importance,
                                "attributes": ent.get("attributes", {}),
                                "source_chunks": set(),  # Track which chunks mentioned this entity
                                "first_seen": chunk_idx,
                            }
                        else:
                            # Update importance if higher
                            existing = all_entities[normalized_name]
                            existing["importance"] = max(existing["importance"], importance)
                            # Merge attributes (simple dict update)
                            if ent.get("attributes"):
                                existing["attributes"].update(ent["attributes"])

                        all_entities[normalized_name]["source_chunks"].add(chunk_idx)

                if result and "relationships" in result:
                    for rel in result["relationships"]:
                        src_norm = self._normalize_entity_name(rel.get("source", ""))
                        tgt_norm = self._normalize_entity_name(rel.get("target", ""))

                        if src_norm in all_entities and tgt_norm in all_entities:
                            all_relationships.append({
                                "source_name": src_norm,
                                "target_name": tgt_norm,
                                "relation_type": rel.get("type", "RELATED_TO"),
                                "weight": min(max(float(rel.get("weight", 0.5)), 0.1), 1.0),
                                "evidence": rel.get("evidence", ""),
                                "source_chunk": chunk_idx,
                            })
            except Exception as e:
                logger.warning(f"Chunk {chunk_idx} extraction failed: {e}")
                continue

        logger.info(f"Extracted {len(all_entities)} unique entities, {len(all_relationships)} relationships")

        # Save to database if session provided
        nodes_created = 0
        edges_created = 0
        
        logger.info(f"Total entities extracted: {len(all_entities)}")
        logger.info(f"Total relationships extracted: {len(all_relationships)}")

        if session and all_entities:
            from sqlalchemy import select as sql_select

            # Create/update entities
            for norm_name, ent_data in all_entities.items():
                # Check if entity exists
                existing = await session.scalar(
                    sql_select(Entity.id).where(Entity.id == ent_data["id"]).limit(1)
                )
                if not existing:
                    # Generate summary using LLM (rich description from first mention)
                    summary = await self._generate_entity_summary(
                        ent_data["name"], ent_data["type"], ent_data["attributes"], provider=provider, model=model
                    )

                    entity = Entity(
                        id=ent_data["id"],
                        name=ent_data["name"],
                        type=ent_data["type"],
                        domain=ent_data["domain"],
                        importance=ent_data["importance"],
                        attributes=ent_data["attributes"],
                        summary=summary,
                    )
                    session.add(entity)
                    nodes_created += 1
                else:
                    # Update importance if higher
                    existing_entity = await session.get(Entity, ent_data["id"])
                    if existing_entity and ent_data["importance"] > existing_entity.importance:
                        existing_entity.importance = ent_data["importance"]
                        # Merge attributes
                        if ent_data["attributes"]:
                            existing_entity.attributes = {
                                **(existing_entity.attributes or {}),
                                **ent_data["attributes"]
                            }

            await session.flush()

            # Create relationships
            for rel in all_relationships:
                src_id = all_entities[rel["source_name"]]["id"]
                tgt_id = all_entities[rel["target_name"]]["id"]

                # Check for duplicate
                existing_rel = await session.scalar(
                    sql_select(Relationship.id).where(
                        Relationship.source_id == src_id,
                        Relationship.target_id == tgt_id,
                        Relationship.relation_type == rel["relation_type"],
                    ).limit(1)
                )
                if not existing_rel:
                    relationship = Relationship(
                        source_id=src_id,
                        target_id=tgt_id,
                        relation_type=rel["relation_type"],
                        weight=rel["weight"],
                        fact=rel["evidence"][:500] if rel["evidence"] else None,
                        metadata_json={
                            "episodes": [f"chunk_{rel['source_chunk']}"],
                            "full_evidence": rel["evidence"],
                        }
                    )
                    session.add(relationship)
                    edges_created += 1

            await session.commit()

        return {
            "nodes_created": nodes_created,
            "edges_created": edges_created,
            "total_entities": len(all_entities),
            "total_relationships": len(all_relationships),
            "chunks_processed": len(chunks),
            "message": f"Successfully extracted {len(all_entities)} entities and {len(all_relationships)} relationships from {len(chunks)} chunks. Created {nodes_created} new nodes and {edges_created} new edges."
        }

    async def _extract_from_chunk(self, text: str, entity_types: List[str], edge_types: List[str], chunk_idx: int, provider: str = None, model: str = None) -> Optional[dict]:
        """Extract entities and relationships from a single text chunk"""
        logger.info(f"Extracting from chunk {chunk_idx}, text length: {len(text)}")
        entity_types_str = ", ".join(entity_types)
        edge_types_str = ", ".join(edge_types)

        prompt = EXTRACT_PROMPT.format(
            entity_types_str=entity_types_str,
            edge_types_str=edge_types_str,
            text=text[:3000]
        )

        try:
            # Use passed settings or defaults
            target_provider = provider or ai_service.provider
            target_model = model or ai_service.model

            logger.info(f"Calling AI service with provider={target_provider}, model={target_model}")
            response = await ai_service.query(
                prompt=prompt,
                provider=target_provider,
                model=target_model,
                max_tokens=4000
            )
            logger.info(f"AI response received, length={len(response)}")

            validated = validation_service.parse_and_validate(response, GraphExtraction)
            if validated:
                result = validated.model_dump()
                logger.info(f"AI extraction successful: {len(result.get('entities', []))} entities, {len(result.get('relationships', []))} relationships")
                return result
            
            # If validation fails, try extracting from mock
            raise ValueError("AI response validation failed")
            
        except Exception as e:
            logger.warning(f"AI extraction failed for chunk {chunk_idx}, using mock extraction: {e}")
            # Fall back to mock extraction
            mock_result = self._extract_mock_entities(text, entity_types, edge_types)
            logger.info(f"Mock extraction found {len(mock_result['entities'])} entities and {len(mock_result['relationships'])} relationships")
            return mock_result
    
    def _extract_mock_entities(self, text: str, entity_types: List[str], edge_types: List[str]) -> dict:
        """Extract entities from text using pattern matching when AI is unavailable"""
        import re
        
        logger.info(f"Mock extraction called with entity_types: {entity_types}, edge_types: {edge_types}")
        logger.info(f"Text to analyze: {text[:200]}...")
        
        entities = []
        relationships = []
        found_entities = {}  # name -> entity dict
        
        # Build type mapping from standard types to custom ontology types
        # Priority order for mapping when multiple types could match
        def get_custom_type(standard_type: str, entity_name: str = '') -> str:
            """Map standard type to custom type if available in entity_types"""
            if not entity_types:
                return standard_type
            
            standard_lower = standard_type.lower()
            name_lower = entity_name.lower()
            
            # Specific entity name patterns
            alliance_keywords = ['nato', 'brics', 'quad', 'asean', 'eu', 'un', 'g20', 'opec', 'who']
            corporation_keywords = ['microsoft', 'google', 'apple', 'amazon', 'meta', 'tesla', 'tata', 'reliance', 'openai']
            tech_keywords = ['ai', 'artificial intelligence']
            
            if any(kw in name_lower for kw in tech_keywords):
                for et in entity_types:
                    if 'tech' in et.lower() or 'technology' in et.lower() or 'asset' in et.lower():
                        return et
            
            if any(kw in name_lower for kw in corporation_keywords):
                for et in entity_types:
                    if 'corporation' in et.lower() or 'company' in et.lower():
                        return et
            
            if any(kw in name_lower for kw in alliance_keywords):
                for et in entity_types:
                    if 'alliance' in et.lower():
                        return et
            
            # Build mapping from entity_types
            type_mapping = {}
            for et in entity_types:
                et_lower = et.lower()
                # Direct matches
                if et_lower in ['gpe', 'country', 'nation', 'geopolitical', 'place']:
                    type_mapping['GPE'] = et
                elif et_lower in ['person', 'leader', 'individual', 'politician']:
                    type_mapping['PERSON'] = et
                elif et_lower in ['alliance', 'organization', 'org', 'agency', 'corporation', 'company']:
                    # Store multiple mappings, prefer alliance over general org
                    if 'alliance' not in type_mapping:
                        type_mapping['ORG'] = et
                    if 'alliance' in et_lower:
                        type_mapping['alliance'] = et
                elif et_lower in ['event', 'conflict', 'incident']:
                    type_mapping['EVENT'] = et
                elif et_lower in ['asset', 'tech', 'technology', 'defense', 'weapon']:
                    type_mapping['ASSET'] = et
                elif et_lower == 'topic':
                    type_mapping['TOPIC'] = et
            
            # For ORG type, prefer alliance if available
            if standard_type.upper() == 'ORG' and 'alliance' in type_mapping:
                return type_mapping['alliance']
            
            # Return mapped type or original
            return type_mapping.get(standard_type.upper(), standard_type)
        
        # Common entity patterns with their types
        common_entities = {
            # Countries/Places
            'india': {'type': 'GPE', 'importance': 9, 'patterns': [r'\bIndia\b']},
            'china': {'type': 'GPE', 'importance': 9, 'patterns': [r'\bChina\b', r'\bChinese\b']},
            'united states': {'type': 'GPE', 'importance': 9, 'patterns': [r'\bUnited States\b', r'\bUSA\b', r'\bAmerica\b', r'\bAmerican\b']},
            'russia': {'type': 'GPE', 'importance': 8, 'patterns': [r'\bRussia\b', r'\bRussian\b']},
            'pakistan': {'type': 'GPE', 'importance': 7, 'patterns': [r'\bPakistan\b', r'\bPakistani\b']},
            'japan': {'type': 'GPE', 'importance': 7, 'patterns': [r'\bJapan\b', r'\bJapanese\b']},
            'australia': {'type': 'GPE', 'importance': 6, 'patterns': [r'\bAustralia\b', r'\bAustralian\b']},
            'israel': {'type': 'GPE', 'importance': 6, 'patterns': [r'\bIsrael\b', r'\bIsraeli\b']},
            'taiwan': {'type': 'GPE', 'importance': 7, 'patterns': [r'\bTaiwan\b']},
            'iran': {'type': 'GPE', 'importance': 6, 'patterns': [r'\bIran\b', r'\bIranian\b']},
            'france': {'type': 'GPE', 'importance': 6, 'patterns': [r'\bFrance\b', r'\bFrench\b']},
            'uk': {'type': 'GPE', 'importance': 6, 'patterns': [r'\bUK\b', r'\bUnited Kingdom\b', r'\bBritain\b', r'\bBritish\b']},
            'germany': {'type': 'GPE', 'importance': 6, 'patterns': [r'\bGermany\b', r'\bGerman\b']},
            'europe': {'type': 'GPE', 'importance': 6, 'patterns': [r'\bEurope\b', r'\bEuropean\b']},
            'asia': {'type': 'GPE', 'importance': 5, 'patterns': [r'\bAsia\b', r'\bAsian\b']},
            
            # People/Leaders
            'narendra modi': {'type': 'PERSON', 'importance': 9, 'patterns': [r'\bNarendra Modi\b', r'\bModi\b']},
            'xi jinping': {'type': 'PERSON', 'importance': 9, 'patterns': [r'\bXi Jinping\b', r'\bPresident Xi\b']},
            'vladimir putin': {'type': 'PERSON', 'importance': 8, 'patterns': [r'\bVladimir Putin\b', r'\bPutin\b']},
            'joe biden': {'type': 'PERSON', 'importance': 8, 'patterns': [r'\bJoe Biden\b', r'\bBiden\b']},
            'donald trump': {'type': 'PERSON', 'importance': 8, 'patterns': [r'\bDonald Trump\b', r'\bTrump\b']},
            'emmanuel macron': {'type': 'PERSON', 'importance': 8, 'patterns': [r'\bEmmanuel Macron\b', r'\bMacron\b']},
            
            # Organizations/Alliances
            'nato': {'type': 'ORG', 'importance': 7, 'patterns': [r'\bNATO\b']},
            'brics': {'type': 'ORG', 'importance': 7, 'patterns': [r'\bBRICS\b']},
            'quad': {'type': 'ORG', 'importance': 7, 'patterns': [r'\bQUAD\b', r'\bQuad\b']},
            'un': {'type': 'ORG', 'importance': 6, 'patterns': [r'\bUN\b', r'\bUnited Nations\b']},
            'g20': {'type': 'ORG', 'importance': 7, 'patterns': [r'\bG20\b']},
            'isro': {'type': 'ORG', 'importance': 7, 'patterns': [r'\bISRO\b']},
            'drdo': {'type': 'ORG', 'importance': 7, 'patterns': [r'\bDRDO\b']},
            'rbi': {'type': 'ORG', 'importance': 8, 'patterns': [r'\bRBI\b']},
            'tata': {'type': 'ORG', 'importance': 6, 'patterns': [r'\bTata\b']},
            'reliance': {'type': 'ORG', 'importance': 6, 'patterns': [r'\bReliance\b']},
            'hal': {'type': 'ORG', 'importance': 6, 'patterns': [r'\bHAL\b']},
            'asean': {'type': 'ORG', 'importance': 6, 'patterns': [r'\bASEAN\b']},
            'eu': {'type': 'ORG', 'importance': 6, 'patterns': [r'\bEU\b', r'\bEuropean Union\b']},
            'microsoft': {'type': 'ORG', 'importance': 6, 'patterns': [r'\bMicrosoft\b']},
            'google': {'type': 'ORG', 'importance': 6, 'patterns': [r'\bGoogle\b']},
            'apple': {'type': 'ORG', 'importance': 6, 'patterns': [r'\bApple\b']},
            'amazon': {'type': 'ORG', 'importance': 6, 'patterns': [r'\bAmazon\b']},
            
            # Events
            'war': {'type': 'EVENT', 'importance': 7, 'patterns': [r'\bwar\b', r'\bconflict\b']},
            'tension': {'type': 'EVENT', 'importance': 5, 'patterns': [r'\btension\b', r'\bcrisis\b']},
            'agreement': {'type': 'EVENT', 'importance': 5, 'patterns': [r'\bagreement\b', r'\bdeal\b', r'\bpact\b']},
            
            # Technologies/Assets
            'missile': {'type': 'ASSET', 'importance': 6, 'patterns': [r'\bmissile\b', r'\bballistic\b']},
            'satellite': {'type': 'ASSET', 'importance': 5, 'patterns': [r'\bsatellite\b', r'\bspace\b']},
            'ai': {'type': 'ASSET', 'importance': 7, 'patterns': [r'\bAI\b', r'\bartificial intelligence\b']},
        }
        
        # Type priority mapping - prefer custom types from ontology
        type_priority = {}
        for et in entity_types:
            et_upper = et.upper()
            et_lower = et.lower()
            # Map common variations
            if 'country' in et_lower or 'nation' in et_lower or 'geopolitical' in et_lower:
                type_priority['GPE'] = et_upper
            elif 'person' in et_lower or 'leader' in et_lower:
                type_priority['PERSON'] = et_upper
            elif 'organization' in et_lower or 'org' in et_lower or 'alliance' in et_lower:
                type_priority['ORG'] = et_upper
            elif 'event' in et_lower or 'conflict' in et_lower:
                type_priority['EVENT'] = et_upper
            elif 'tech' in et_lower or 'asset' in et_lower or 'defense' in et_lower:
                type_priority['ASSET'] = et_upper
        
        text_lower = text.lower()
        
        # Extract entities from known patterns
        for name, props in common_entities.items():
            for pattern in props['patterns']:
                if re.search(pattern, text):
                    # Get display name
                    display_name = name.title()
                    if name == 'un':
                        display_name = 'United Nations'
                    elif name == 'uk':
                        display_name = 'United Kingdom'
                    elif name == 'eu':
                        display_name = 'European Union'
                    elif name == 'ai':
                        display_name = 'AI'
                        base_type = 'ASSET'  # AI is a technology/asset
                    
                    # Use custom type from ontology if available
                    base_type = props['type']
                    entity_type = get_custom_type(base_type, display_name)
                    
                    if display_name not in found_entities:
                        found_entities[display_name] = {
                            'name': display_name,
                            'type': entity_type,
                            'domain': 'geopolitics',
                            'importance': props['importance'],
                            'attributes': {}
                        }
                        logger.debug(f"Found entity: {display_name} (type: {entity_type})")
                    break
        
        # Detect generic roles like "President", "Prime Minister" followed by country
        role_patterns = [
            (r'\bPresident of (\w+)\b', 'PERSON'),
            (r'\bPrime Minister of (\w+)\b', 'PERSON'),
            (r'\bChancellor of (\w+)\b', 'PERSON'),
        ]
        for pattern, base_type in role_patterns:
            for match in re.finditer(pattern, text):
                role_name = match.group(0)
                country = match.group(1)
                entity_type = get_custom_type(base_type, role_name)
                if role_name not in found_entities:
                    found_entities[role_name] = {
                        'name': role_name,
                        'type': entity_type,
                        'domain': 'geopolitics',
                        'importance': 7,
                        'attributes': {'country': country}
                    }
                    # Also ensure the country is extracted
                    if country not in found_entities:
                        country_type = get_custom_type('GPE')
                        found_entities[country] = {
                            'name': country,
                            'type': country_type,
                            'domain': 'geopolitics',
                            'importance': 6,
                            'attributes': {}
                        }
        
        # Also extract capitalized phrases that might be entities (but only multi-word names)
        # Look for proper nouns with at least 2 words to avoid common single words
        capitalized_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
        for match in re.finditer(capitalized_pattern, text):
            name = match.group(1)
            # Skip common words and already found entities
            skip_words = ['The', 'This', 'That', 'These', 'Those', 'And', 'But', 'Or', 
                         'Prime Minister', 'President Of', 'Chancellor Of', 'Head Of']
            if len(name) < 4 or name in skip_words:
                continue
            # Skip if already found or if part of a known entity
            name_lower = name.lower()
            already_found = any(name_lower == k.lower() for k in found_entities.keys())
            if not already_found:
                # Check if this is a substring of an already found entity
                is_substring = any(name_lower in k.lower() for k in found_entities.keys())
                if not is_substring:
                    entity_type = entity_types[0] if entity_types else 'ORG'
                    found_entities[name] = {
                        'name': name,
                        'type': entity_type,
                        'domain': 'geopolitics',
                        'importance': 5,
                        'attributes': {}
                    }
        
        entities = list(found_entities.values())
        logger.info(f"Extracted {len(entities)} entities")
        
        # Generate relationships between found entities
        entity_names = list(found_entities.keys())
        entity_types_map = {name: ent['type'] for name, ent in found_entities.items()}
        
        # Helper function to get relationship type from edge_types
        def get_rel_type(preferred_types: List[str]) -> str:
            """Get first matching relationship type from edge_types"""
            for pt in preferred_types:
                if pt in edge_types:
                    return pt
            # Fallback to first edge type or default
            return edge_types[0] if edge_types else 'RELATED_TO'
        
        # Relationship detection patterns
        # Format: (entity1_pattern, entity2_pattern, preferred_rel_types, text_pattern, weight)
        rel_detection = [
            # Tensions/Opposition
            (r'\b(tension|border|conflict|oppos|hostile|dispute)\b', 
             ['OPPOSES', 'CONFLICT_WITH', 'DISPUTES'], 0.9),
            # Cooperation/Partnership
            (r'\b(cooperat|partner|strategic|alliance|collaborat)\b',
             ['COOPERATES_WITH', 'PARTNERS_WITH', 'ALLIED_WITH'], 0.85),
            # Membership
            (r'\b(member|joined|part of|member of|belongs to)\b',
             ['MEMBER_OF', 'PART_OF', 'BELONGS_TO'], 1.0),
            # Leadership
            (r'\b(leads|leads the|president of|prime minister of|head of)\b',
             ['LEADS', 'RULES', 'GOVERNS'], 0.95),
        ]
        
        # Check for co-occurring entities in the same sentence
        sentences = re.split(r'[.!?\n]', text)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            entities_in_sentence = [name for name in entity_names if name.lower() in sentence_lower]
            
            if len(entities_in_sentence) >= 2:
                # Check each relationship pattern
                for pattern, preferred_types, weight in rel_detection:
                    if re.search(pattern, sentence_lower):
                        rel_type = get_rel_type(preferred_types)
                        # Create relationships between all pairs in the sentence
                        for i, e1 in enumerate(entities_in_sentence):
                            for e2 in entities_in_sentence[i+1:]:
                                # Avoid duplicates
                                existing = any(
                                    r['source'] in [e1, e2] and r['target'] in [e1, e2]
                                    for r in relationships
                                )
                                if not existing:
                                    relationships.append({
                                        'source': e1,
                                        'target': e2,
                                        'type': rel_type,
                                        'weight': weight,
                                        'evidence': f'{e1} and {e2} relationship detected'
                                    })
        
        # Also check for specific entity patterns
        member_pairs = [
            (['India', 'BRICS']), (['India', 'QUAD']), (['India', 'G20']),
            (['China', 'BRICS']), (['Russia', 'BRICS']), (['United States', 'NATO']),
        ]
        member_rel_type = get_rel_type(['MEMBER_OF', 'PART_OF'])
        
        for pair in member_pairs:
            name1, name2 = pair
            if name1 in entity_names and name2 in entity_names:
                existing = any(
                    r['source'] in [name1, name2] and r['target'] in [name1, name2]
                    for r in relationships
                )
                if not existing:
                    relationships.append({
                        'source': name1,
                        'target': name2,
                        'type': member_rel_type,
                        'weight': 1.0,
                        'evidence': f'{name1} is a member of {name2}'
                    })
        
        logger.info(f"Generated {len(relationships)} relationships")
        
        return {
            'entities': entities,
            'relationships': relationships
        }
        
        # Generate relationships between found entities
        if len(found_entities) >= 2:
            # Common relationships
            rel_patterns = [
                ('India', 'United States', 'ALLIED_WITH', 0.85),
                ('India', 'Russia', 'COOPERATES_WITH', 0.8),
                ('India', 'China', 'OPPOSES', 0.9),
                ('India', 'Pakistan', 'OPPOSES', 0.95),
                ('India', 'Japan', 'COOPERATES_WITH', 0.85),
                ('India', 'Israel', 'COOPERATES_WITH', 0.8),
                ('India', 'BRICS', 'MEMBER_OF', 1.0),
                ('India', 'QUAD', 'MEMBER_OF', 1.0),
                ('India', 'G20', 'MEMBER_OF', 1.0),
                ('China', 'Russia', 'COOPERATES_WITH', 0.75),
                ('China', 'Pakistan', 'ALLIED_WITH', 0.9),
                ('United States', 'NATO', 'MEMBER_OF', 1.0),
                ('United States', 'Taiwan', 'COOPERATES_WITH', 0.85),
                ('Modi', 'India', 'LEADS', 1.0),
                ('ISRO', 'India', 'OWNS', 1.0),
                ('DRDO', 'India', 'OWNS', 1.0),
                ('RBI', 'India', 'OWNS', 1.0),
            ]
            
            for src, tgt, rel_type, weight in rel_patterns:
                if src in found_entities and tgt in found_entities:
                    relationships.append({
                        'source': src,
                        'target': tgt,
                        'type': rel_type,
                        'weight': weight,
                        'evidence': 'Based on text analysis'
                    })
        
        return {
            'entities': entities,
            'relationships': relationships
        }

    def _chunk_text(self, text: str, chunk_size: int = 3000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk)
            start = end - overlap
            if start >= len(text):
                break
        return chunks[:20]

    def _normalize_entity_name(self, name: str) -> str:
        """Normalize entity name for deduplication"""
        if not name:
            return ""
        # Lowercase, strip whitespace, remove extra spaces
        normalized = name.strip().lower()
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized

    def _generate_entity_id(self, normalized_name: str) -> str:
        """Generate stable entity ID from normalized name"""
        # Replace spaces with underscores, keep alphanumeric and underscores
        safe_name = re.sub(r'[^a-z0-9_]', '_', normalized_name)
        safe_name = re.sub(r'_+', '_', safe_name).strip('_')
        # Ensure not empty
        if not safe_name:
            safe_name = f"entity_{uuid.uuid4().hex[:8]}"
        return safe_name[:100]  # Limit length

    def _map_entity_type(self, raw_type: str, allowed_types: List[str] = None) -> str:
        """Map extracted type to one of the allowed types, or use as-is if valid"""
        raw_lower = raw_type.lower().strip()
        
        # Direct match - if the type is already in allowed types, use it
        if allowed_types:
            for allowed in allowed_types:
                if raw_lower == allowed.lower():
                    return allowed
            # Partial match - check if raw_type is contained in allowed type
            for allowed in allowed_types:
                if raw_lower in allowed.lower() or allowed.lower() in raw_lower:
                    return allowed
        
        # Fallback mapping for common variations to standard types
        type_map = {
            "country": "GPE", "nation": "GPE", "state": "GPE", "gpe": "GPE",
            "geopoliticalactor": "GPE", "geopolitical": "GPE",
            "person": "PERSON", "leader": "PERSON", "individual": "PERSON", 
            "politician": "PERSON", "politicalleader": "PERSON",
            "organization": "ORG", "org": "ORG", "company": "ORG", "corporation": "ORG",
            "agency": "ORG", "institution": "ORG", "military": "ORG", "unit": "ORG",
            "alliance": "ORG", "internationalalliance": "ORG", "militaryalliance": "ORG",
            "defenseorganization": "ORG", "spaceagency": "ORG", "governmentbody": "ORG",
            "event": "EVENT", "incident": "EVENT", "conflict": "EVENT",
            "technology": "ASSET", "tech": "ASSET", "system": "ASSET",
            "weapon": "ASSET", "platform": "ASSET", "asset": "ASSET",
            "defense": "ASSET",
            # Map standard types to themselves
            "gpe": "GPE", "person": "PERSON", "org": "ORG", 
            "event": "EVENT", "asset": "ASSET"
        }
        
        mapped = type_map.get(raw_lower)
        if mapped:
            # If allowed_types is provided, check if mapped type is in allowed types
            if allowed_types:
                # Check if mapped type matches any allowed type
                for allowed in allowed_types:
                    if mapped.lower() == allowed.lower() or mapped in allowed.upper():
                        return allowed
                # If not found, return first allowed type
                return allowed_types[0]
            return mapped
        
        # If no mapping found, return the original type with proper casing
        # This allows custom ontology types to pass through
        return raw_type.title()

    def _find_closest_type(self, raw_type: str, allowed_types: List[str]) -> str:
        """Find closest matching allowed type"""
        raw_lower = raw_type.lower()
        
        # Direct match
        for allowed in allowed_types:
            if raw_lower == allowed.lower():
                return allowed
        
        # Partial match
        for allowed in allowed_types:
            if raw_lower in allowed.lower() or allowed.lower() in raw_lower:
                return allowed
        
        # Semantic matching
        semantic_map = {
            'country': ['gpe', 'geopolitical', 'nation', 'state'],
            'person': ['leader', 'individual', 'politician'],
            'organization': ['org', 'alliance', 'agency', 'institution'],
            'event': ['conflict', 'incident'],
            'asset': ['tech', 'technology', 'defense', 'weapon', 'system'],
        }
        
        for base_type, variations in semantic_map.items():
            if raw_lower in variations:
                for allowed in allowed_types:
                    if allowed.lower() in [base_type] + variations:
                        return allowed
        
        # Default to first allowed type
        return allowed_types[0] if allowed_types else "Organization"

    async def _generate_entity_summary(self, name: str, entity_type: str, attributes: Dict[str, Any], provider: str = None, model: str = None) -> str:
        """Generate a concise summary for an entity using LLM"""
        try:
            attr_str = ", ".join(f"{k}: {v}" for k, v in attributes.items())
            prompt = f"""Generate a concise one-sentence summary for this entity:

Name: {name}
Type: {entity_type}
Attributes: {attr_str if attr_str else "None"}

Summary (one sentence, maximum 100 characters):"""

            # Use passed settings or defaults
            target_provider = provider or ai_service.provider
            target_model = model or ai_service.model

            summary = await ai_service.query(prompt, provider=target_provider, model=target_model)
            # Clean up
            summary = summary.strip().split('\n')[0][:150]
            return summary
        except Exception as e:
            logger.warning(f"Failed to generate summary for {name}: {e}")
            return f"{entity_type}: {name}"



# Singleton
graph_builder_service = GraphBuilderService()
