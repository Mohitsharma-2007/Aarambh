"""AI Chat endpoints with multi-provider support and model selection"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from loguru import logger
import uuid
from datetime import datetime

from app.services.ai_service import ai_service, FREE_MODELS
from app.config import settings, LLMProvider

router = APIRouter()


class Source(BaseModel):
    title: str
    url: str
    snippet: str


class ChatRequest(BaseModel):
    message: str
    mode: Optional[str] = 'default'  # 'rag' or 'opensource' (deprecated, uses provider instead)
    provider: Optional[str] = None  # 'openrouter', 'groq', 'glm', 'google_ai'
    model: Optional[str] = None
    context: Optional[str] = None
    conversation_id: Optional[str] = None
    stream: Optional[bool] = False
    tools: Optional[List[str]] = []
    agent: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[Source]] = None
    conversation_id: str
    provider: str
    model: str
    tool_calls: Optional[List[dict]] = None


class ChatMessage(BaseModel):
    id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str


class ProviderInfo(BaseModel):
    id: str
    name: str
    models: List[dict]
    available: bool


# In-memory conversation storage (use Redis in production)
conversations: dict = {}


class AnalyzeImpactRequest(BaseModel):
    event_id: Optional[str] = None
    title: str
    summary: str
    domain: str
    entities: List[str]
    provider: Optional[str] = None
    model: Optional[str] = None


class DeepResearchRequest(BaseModel):
    query: str
    provider: Optional[str] = None
    model: Optional[str] = None
    depth: Optional[str] = 'standard'


@router.post("/deep-research")
async def run_multi_step_deep_research(request: DeepResearchRequest):
    """
    Run a multi-step deep research pipeline using AI.
    Steps: Query Analysis -> Source Retrieval -> NLP Processing -> Cross-Reference -> Report Generation
    """
    import time
    from duckduckgo_search import AsyncDDGS
    from app.database import async_session, ResearchRecord
    
    research_id = str(uuid.uuid4())
    provider = request.provider or settings.default_llm_provider
    model = request.model or settings.default_llm_model
    steps = []
    all_sources = []
    tokens_used = 0

    try:
        # Step 1: Query Analysis
        t0 = time.time()
        analysis_prompt = f"""Analyze this research query for AARAMBH:
        Query: {request.query}
        
        Identify:
        1. Core entities and their roles
        2. Specific technical or geopolitical domains involved
        3. Strategic questions that need answering
        4. Optimal search parameters
        
        Respond with a structured mental map of the research task."""
        
        analysis = await ai_service.query(analysis_prompt, provider=provider, model=model)
        tokens_used += len(analysis.split()) * 2
        steps.append({
            "id": "1", "label": "Query Analysis", "status": "completed",
            "duration": round(time.time() - t0, 1), "output": analysis[:1000]
        })

        # Step 2: Source Retrieval
        t0 = time.time()
        search_query = request.query
        try:
            ddgs_results = await AsyncDDGS().text(search_query, max_results=10)
            sources_text = "\n\n".join([f"Source: {r['title']}\nContent: {r['body']}" for r in ddgs_results])
            all_sources = [{"title": r["title"], "url": r["href"], "snippet": r["body"]} for r in ddgs_results]
            
            retrieval_prompt = f"Summarize the key intelligence found in these search results for: {request.query}\n\n{sources_text[:5000]}"
            source_summary = await ai_service.query(retrieval_prompt, provider=provider, model=model)
            tokens_used += len(source_summary.split()) * 2
            
            steps.append({
                "id": "2", "label": "Source Retrieval", "status": "completed",
                "duration": round(time.time() - t0, 1), "output": source_summary[:1000]
            })
        except Exception as e:
            logger.error(f"Search failed: {e}")
            source_summary = "Search failed, proceeding with linguistic analysis."
            steps.append({
                "id": "2", "label": "Source Retrieval", "status": "warning",
                "duration": round(time.time() - t0, 1), "output": source_summary
            })

        # Step 3: Deep NLP Analysis
        t0 = time.time()
        nlp_prompt = f"""Perform deep multi-dimensional analysis on: {request.query}
        Context: {source_summary}
        
        Analyze:
        - Network of influence between entities
        - Hidden incentives and power dynamics
        - Temporal progression (Past -> Present -> Future)
        - Confidence rating for various interpretations"""
        
        analysis_detail = await ai_service.query(nlp_prompt, provider=provider, model=model)
        tokens_used += len(analysis_detail.split()) * 2
        steps.append({
            "id": "3", "label": "Deep Analysis", "status": "completed",
            "duration": round(time.time() - t0, 1), "output": analysis_detail[:1000]
        })

        # Step 4: Cross-Reference & Validation
        t0 = time.time()
        validation_prompt = f"""Critique the following analysis for biases, gaps, or inconsistencies:
        {analysis_detail[:2000]}
        
        Ensure accuracy for AARAMBH sovereign standards. Identify any 'low confidence' areas."""
        
        validation = await ai_service.query(validation_prompt, provider=provider, model=model)
        tokens_used += len(validation.split()) * 2
        steps.append({
            "id": "4", "label": "Cross-Reference Validation", "status": "completed",
            "duration": round(time.time() - t0, 1), "output": validation[:1000]
        })

        # Step 5: Final Report Generation
        t0 = time.time()
        report_prompt = f"""Generate a professional intelligence report for: {request.query}
        Original Analysis: {analysis_detail}
        Validation Feedback: {validation}
        
        The report should be structured with:
        - Executive Summary (Strategic highlights)
        - Detailed Findings (Entity-by-entity breakdown)
        - Sovereign Impact Analysis (Implications for national interests)
        - Future Scenarios (Most likely developments)
        - Strategic Recommendations (Actionable intelligence)"""
        
        report = await ai_service.query(report_prompt, provider=provider, model=model)
        tokens_used += len(report.split()) * 2
        steps.append({
            "id": "5", "label": "Report Generation", "status": "completed",
            "duration": round(time.time() - t0, 1), "output": "Full report generated successfully."
        })

        # Save to database
        try:
            async with async_session() as session:
                new_record = ResearchRecord(
                    id=research_id,
                    query=request.query,
                    report=report,
                    entities=[], # Extracting is complex, leave for now
                    research_data=all_sources,
                    simulation_results={"steps": steps}
                )
                session.add(new_record)
                await session.commit()
                logger.info(f"Deep Research result saved to DB: {research_id}")
        except Exception as db_err:
            logger.error(f"Failed to save deep research to DB: {db_err}")

        return {
            "research_id": research_id,
            "query": request.query,
            "status": "completed",
            "steps": steps,
            "result": report,
            "sources": all_sources,
            "tokens_used": tokens_used,
        }

    except Exception as e:
        logger.error(f"Deep research error: {e}")
        return {
            "research_id": research_id,
            "query": request.query,
            "status": "error",
            "steps": steps,
            "result": f"Research failed: {str(e)}",
            "sources": all_sources,
            "tokens_used": tokens_used,
        }


@router.post("/chat")
async def chat(request: ChatRequest):
    """AI Chat endpoint with multi-provider support"""
    # Use selected provider/model or defaults from settings
    provider = request.provider or settings.default_llm_provider
    model = request.model or settings.default_llm_model
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    logger.info(f"AI Chat Request: provider={provider}, model={model}, conversation={conversation_id}")
    
    try:
        # Construct messages from context if provided, else just get message
        # For simplicity in this endpoint:
        response_text = await ai_service.query(
            prompt=request.message,
            provider=provider,
            model=model,
            stream=False # Streaming handled via separate logic if needed
        )
        
        return ChatResponse(
            response=response_text,
            conversation_id=conversation_id,
            provider=provider,
            model=model
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(conversation_id: Optional[str] = None):
    """Get chat history (mock)"""
    history = []
    if conversation_id and conversation_id in conversations:
        for idx, msg in enumerate(conversations[conversation_id]):
            history.append(ChatMessage(
                id=f"{conversation_id}-{idx}",
                role=msg["role"],
                content=msg["content"],
                timestamp="2024-01-01T00:00:00Z",
            ))
    
    return history


def _models_to_dicts(model_list: list) -> list:
    """Convert plain model ID strings to {id, name} dicts for frontend."""
    result = []
    for m in model_list:
        if isinstance(m, dict):
            result.append(m)
        else:
            name = m.split("/")[-1] if "/" in str(m) else str(m)
            name = name.replace(":free", " (Free)").replace("-", " ").title()
            result.append({"id": str(m), "name": name})
    return result


@router.get("/providers")
async def get_providers():
    """
    Get available AI providers and their models.
    """
    providers = []

    # Check OpenRouter
    providers.append(ProviderInfo(
        id="openrouter",
        name="OpenRouter",
        models=_models_to_dicts(FREE_MODELS.get(LLMProvider.OPENROUTER, [])),
        available=bool(settings.openrouter_api_key),
    ))

    # Check Groq
    providers.append(ProviderInfo(
        id="groq",
        name="Groq (Fast Inference)",
        models=_models_to_dicts(FREE_MODELS.get(LLMProvider.GROQ, [])),
        available=bool(settings.groq_api_key),
    ))

    # Check GLM
    providers.append(ProviderInfo(
        id="glm",
        name="GLM / Zhipu AI",
        models=_models_to_dicts(FREE_MODELS.get(LLMProvider.GLM, [])),
        available=bool(settings.glm_api_key),
    ))

    # Check Google AI
    providers.append(ProviderInfo(
        id="google_ai",
        name="Google AI (Gemini)",
        models=_models_to_dicts(FREE_MODELS.get(LLMProvider.GOOGLE_AI, [])),
        available=bool(settings.google_ai_api_key),
    ))

    return {"providers": providers, "default": settings.default_llm_provider}


@router.post("/analyze-impact")
async def analyze_news_impact(request: AnalyzeImpactRequest):
    """
    Analyze the potential impact of a news event across multiple dimensions.
    Used for the Overview page AI insight popup.
    """
    provider = request.provider or settings.default_llm_provider
    model = request.model or settings.default_llm_model

    try:
        prompt = f"""You are an expert intelligence analyst for AARAMBH, India's sovereign OSINT platform.
        Analyze the potential impact of this news event:
        
        Title: {request.title}
        Domain: {request.domain}
        Summary: {request.summary}
        Entities Involved: {', '.join(request.entities)}
        
        Provide a structured analysis in JSON format with:
        {{
            "impact_analysis": "Overall analysis (2-3 paragraphs)",
            "affected_sectors": [{{"sector": "name", "impact": "desc", "severity": "high/medium/low"}}],
            "affected_entities": [{{"name": "name", "impact": "desc"}}],
            "geopolitical_implications": "analysis",
            "economic_implications": "analysis",
            "recommendations": ["list"],
            "risk_level": "critical/high/medium/low"
        }}
        """

        response_text = await ai_service.query(prompt, provider=provider, model=model)

        import json
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            try:
                result = json.loads(json_match.group())
                result["sources"] = []
                return result
            except json.JSONDecodeError:
                pass

        return {
            "impact_analysis": response_text,
            "affected_sectors": [{"sector": request.domain, "impact": "Primary domain affected", "severity": "high"}],
            "affected_entities": [{"name": e, "impact": "Directly mentioned"} for e in request.entities[:5]],
            "geopolitical_implications": "Analysis in progress",
            "economic_implications": "Analysis in progress",
            "recommendations": ["Monitor situation closely"],
            "risk_level": "medium",
            "sources": [],
        }

    except Exception as e:
        logger.error(f"Impact analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class CountryInsightRequest(BaseModel):
    country: str
    events: List[dict]  # [{title, domain, summary, importance}]
    provider: Optional[str] = None
    model: Optional[str] = None


@router.post("/country-insight")
async def get_country_insight(request: CountryInsightRequest):
    """
    Generate AI-processed intelligence insight for a specific country
    based on recent events. Used by the Globe page for country popups.
    """
    provider = request.provider or settings.default_llm_provider
    model = request.model or settings.default_llm_model

    events_text = "\n".join([
        f"- [{e.get('domain', 'unknown')}] {e.get('title', 'N/A')} (importance: {e.get('importance', 5)})"
        for e in request.events[:20]
    ])

    try:
        prompt = f"""You are a geopolitical intelligence analyst for AARAMBH.
        Generate a concise intelligence briefing for {request.country} based on these recent events:

        {events_text}

        Respond in JSON format:
        {{
            "summary": "2-3 sentence intelligence overview",
            "threat_level": "critical/high/moderate/low/stable",
            "dominant_domain": "the primary domain of concern",
            "key_developments": ["top 3 developments"],
            "sentiment": "positive/negative/neutral/mixed",
            "trend": "escalating/stable/de-escalating",
            "strategic_note": "1-sentence strategic implication for India"
        }}"""

        response_text = await ai_service.query(prompt, provider=provider, model=model)

        import json as json_mod
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            try:
                result = json_mod.loads(json_match.group())
                result["country"] = request.country
                result["event_count"] = len(request.events)
                return result
            except json_mod.JSONDecodeError:
                pass

        return {
            "country": request.country,
            "summary": response_text[:500],
            "threat_level": "moderate",
            "dominant_domain": "geopolitics",
            "key_developments": [e.get("title", "") for e in request.events[:3]],
            "sentiment": "neutral",
            "trend": "stable",
            "strategic_note": "Monitoring required",
            "event_count": len(request.events),
        }

    except Exception as e:
        logger.error(f"Country insight error for {request.country}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
