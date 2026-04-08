"""routers/ai_analysis.py"""

from fastapi import APIRouter, Body, Query
from scrapers.ai_analyzer import (
    analyze_sentiment,
    analyze_text,
    compare_topics,
    get_ai_trends,
    get_daily_briefing,
    summarize_topic,
)

router = APIRouter()


@router.get("/summarize", summary="AI summary of news on any topic")
async def summarize(
    topic: str = Query(..., description="Any topic e.g. 'India stock market'"),
):
    return await summarize_topic(topic)


@router.get("/sentiment", summary="Sentiment analysis of news coverage")
async def sentiment(topic: str = Query(..., description="Topic to analyze")):
    return await analyze_sentiment(topic)


@router.get("/briefing", summary="AI-powered daily news briefing")
async def briefing():
    return await get_daily_briefing()


@router.get("/compare", summary="Compare coverage of two topics")
async def compare(
    topic1: str = Query(..., description="First topic"),
    topic2: str = Query(..., description="Second topic"),
):
    return await compare_topics(topic1, topic2)


@router.post("/analyze", summary="Analyze custom news text")
async def analyze(
    text: str = Body(..., embed=True, description="News text to analyze"),
):
    return await analyze_text(text)


@router.get("/trends", summary="AI-detected trending themes")
async def trends():
    return await get_ai_trends()


@router.get("/setup", summary="AI setup status")
async def setup():
    import os

    has_key = bool(os.getenv("GROQ_API_KEY", ""))
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    return {
        "ai_enabled": has_key,
        "provider": "Groq (free tier)",
        "model": model if has_key else "rule-based fallback",
        "available_models": [
            "llama-3.1-8b-instant",
            "llama3-8b-8192",
            "gemma2-9b-it",
            "llama-3.3-70b-versatile",
        ],
        "setup": "Set GROQ_API_KEY environment variable to enable AI features",
        "env_example": "GROQ_API_KEY=gsk_... python main.py",
        "without_key": "All endpoints still work using rule-based analysis (no AI)",
        "groq_docs": "https://console.groq.com/",
    }
