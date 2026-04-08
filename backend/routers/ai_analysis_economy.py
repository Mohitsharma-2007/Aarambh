"""routers/ai_analysis.py"""
from fastapi import APIRouter, Query, Body
from scrapers.ai_engine import (
    analyze_document, summarize_economic_topic,
    extract_data_insights, generate_economy_briefing,
    compare_indicators, analyze_text_custom, get_setup_status
)

router = APIRouter()

@router.get("/setup", summary="OpenRouter AI setup status and configuration")
async def setup():
    return await get_setup_status()

@router.get("/summarize", summary="AI summary of an economic topic")
async def summarize(
    topic: str   = Query(..., description="e.g. India GDP, inflation, RBI policy, budget 2025"),
    context: str = Query("", description="Optional additional context"),
):
    return await summarize_economic_topic(topic, context)

@router.get("/briefing", summary="AI daily economy briefing (India + Global)")
async def briefing():
    return await generate_economy_briefing()

@router.get("/compare", summary="Compare two economic indicators")
async def compare(
    indicator1: str = Query(..., description="First indicator e.g. GDP growth"),
    indicator2: str = Query(..., description="Second indicator e.g. inflation"),
    context:    str = Query("", description="Optional context"),
):
    return await compare_indicators(indicator1, indicator2, context)

@router.post("/analyze", summary="Analyze any text — policy doc, circular, data")
async def analyze(
    text: str = Body(..., embed=True, description="Text content to analyze"),
    task: str = Body("analyze", embed=True,
                     description="analyze|summarize|classify|sentiment|translate"),
):
    return await analyze_text_custom(text, task)

@router.post("/extract-insights", summary="Extract insights from data dict")
async def extract_insights(
    data:      dict = Body(..., embed=True),
    data_type: str  = Body("economic", embed=True),
):
    return await extract_data_insights(data, data_type)

@router.post("/analyze-document", summary="AI analysis of a parsed document")
async def analyze_doc(
    parsed_doc: dict = Body(..., embed=True, description="Output from /api/docs/parse"),
    focus:      str  = Body("", embed=True, description="Optional focus area"),
):
    return await analyze_document(parsed_doc, focus)
