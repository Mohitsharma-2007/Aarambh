"""
scrapers/ai_analyzer.py  —  AI-powered News Analysis
======================================================
Uses Groq API (llama-3.1-8b-instant) for fast, free inference:
  • Summarize news topics
  • Sentiment analysis
  • Daily briefings
  • Topic comparison
  • Trend detection
  • Custom text analysis

Set GROQ_API_KEY in .env or environment variable.
Free models: llama-3.1-8b-instant, gemma2-9b-it, llama3-8b-8192
"""

import asyncio
import json
import os
from typing import Optional

from utils.cache import get as c_get
from utils.cache import set as c_set
from utils.text_filter import sentiment_score

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# ── Groq API call ─────────────────────────────────────────────────────────────


async def _groq(prompt: str, max_tokens: int = 1000) -> Optional[str]:
    """Call Groq API (free tier). Falls back to rule-based if no key."""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return None

    import httpx

    try:
        async with httpx.AsyncClient(timeout=30) as cli:
            r = await cli.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": os.getenv("GROQ_MODEL", GROQ_MODEL),
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            if r.status_code == 200:
                data = r.json()
                return data["choices"][0]["message"]["content"]
            return None
    except Exception:
        return None


# ── Fetch news for analysis ───────────────────────────────────────────────────


async def _get_news_for_topic(topic: str, count: int = 10) -> list:
    """Fetch recent news articles on a topic for AI analysis."""
    from scrapers.rss_scraper import search_all

    result = await search_all(topic, count=count)
    return result.get("articles", [])


def _articles_to_text(articles: list, max_arts: int = 8) -> str:
    lines = []
    for i, a in enumerate(articles[:max_arts], 1):
        lines.append(f"{i}. {a.get('title', '')}")
        if a.get("summary"):
            lines.append(f"   {a['summary'][:200]}")
        lines.append(f"   Source: {a.get('source', '')} | {a.get('published', '')}")
    return "\n".join(lines)


# ── Rule-based fallbacks (when no API key) ───────────────────────────────────


def _rule_based_summary(articles: list, topic: str) -> str:
    if not articles:
        return f"No recent articles found for '{topic}'."
    headlines = [a.get("title", "") for a in articles[:5]]
    sources = list(set(a.get("source", "") for a in articles[:8]))
    return (
        f"Based on {len(articles)} recent articles about '{topic}':\n\n"
        f"Key headlines:\n"
        + "\n".join(f"• {h}" for h in headlines)
        + f"\n\nCovered by: {', '.join(sources[:5])}"
    )


def _rule_based_sentiment(articles: list, topic: str) -> dict:
    texts = [a.get("title", "") + " " + a.get("summary", "") for a in articles]
    combined = " ".join(texts)
    sent = sentiment_score(combined)
    return {
        "topic": topic,
        "overall": sent["label"],
        "score": sent["score"],
        "articles_analyzed": len(articles),
        "positive_signals": sent["positive_signals"],
        "negative_signals": sent["negative_signals"],
    }


def _rule_based_trends(all_articles: list) -> list:
    import re
    from collections import Counter

    stopwords = {
        "the",
        "a",
        "an",
        "in",
        "of",
        "to",
        "is",
        "was",
        "for",
        "on",
        "at",
        "by",
        "with",
        "and",
        "or",
        "but",
        "news",
        "report",
        "says",
        "said",
        "new",
        "will",
        "has",
        "have",
        "after",
        "before",
        "over",
        "under",
        "from",
        "this",
        "that",
    }
    counter = Counter()
    for a in all_articles:
        words = re.findall(r"\b[A-Za-z]{5,}\b", a.get("title", ""))
        for w in words:
            if w.lower() not in stopwords:
                counter[w.lower()] += 1
    return [
        {"theme": w, "mentions": c, "significance": "high" if c > 5 else "medium"}
        for w, c in counter.most_common(15)
    ]


# ── Public API ────────────────────────────────────────────────────────────────


async def summarize_topic(topic: str) -> dict:
    """AI summary of current news on any topic."""
    ck = {"t": "sum", "q": topic}
    if c := c_get("ai_sum", ck):
        return c

    articles = await _get_news_for_topic(topic, count=10)
    arts_text = _articles_to_text(articles)

    prompt = f"""You are a financial news analyst. Based on these recent news headlines and summaries about '{topic}', provide a concise 3-4 sentence summary of what is happening right now. Focus on key developments, trends, and impact.

News Articles:
{arts_text}

Provide a clear, factual summary in 3-4 sentences."""

    ai_text = await _groq(prompt, max_tokens=300)
    summary = ai_text if ai_text else _rule_based_summary(articles, topic)

    result = {
        "topic": topic,
        "summary": summary,
        "articles_used": len(articles),
        "sources": list(set(a.get("source", "") for a in articles[:8])),
        "ai_powered": bool(ai_text),
        "model": GROQ_MODEL if ai_text else "rule-based",
        "top_headlines": [a.get("title", "") for a in articles[:5]],
    }
    c_set("ai_sum", ck, result, ttl=600)
    return result


async def analyze_sentiment(topic: str) -> dict:
    """Sentiment analysis of news coverage on a topic."""
    ck = {"t": "sent", "q": topic}
    if c := c_get("ai_sent", ck):
        return c

    articles = await _get_news_for_topic(topic, count=15)
    arts_text = _articles_to_text(articles)

    prompt = f"""Analyze the sentiment of news coverage about '{topic}' based on these articles.
Return a JSON object with these exact fields:
- overall: "positive", "negative", or "neutral"
- score: float between -1.0 (very negative) and 1.0 (very positive)
- reasoning: one sentence explaining the sentiment
- key_themes: list of 3 main themes in the coverage
- risk_level: "low", "medium", "high", or "critical"

News Articles:
{arts_text}

Respond with only valid JSON."""

    ai_text = await _groq(prompt, max_tokens=300)
    if ai_text:
        try:
            ai_data = json.loads(ai_text)
            result = {
                "topic": topic,
                "overall": ai_data.get("overall", "neutral"),
                "score": ai_data.get("score", 0.0),
                "reasoning": ai_data.get("reasoning", ""),
                "key_themes": ai_data.get("key_themes", []),
                "risk_level": ai_data.get("risk_level", "medium"),
                "articles_analyzed": len(articles),
                "ai_powered": True,
                "model": GROQ_MODEL,
            }
        except Exception:
            result = {**_rule_based_sentiment(articles, topic), "ai_powered": False}
    else:
        result = {**_rule_based_sentiment(articles, topic), "ai_powered": False}

    c_set("ai_sent", ck, result, ttl=600)
    return result


async def get_daily_briefing() -> dict:
    """AI-powered daily news briefing across all categories."""
    ck = {"t": "briefing"}
    if c := c_get("ai_brief", ck):
        return c

    from scrapers.rss_scraper import get_by_category, get_headlines

    headlines_task = get_headlines(30)
    finance_task = get_by_category("finance", 15)
    geo_task = get_by_category("geopolitical", 15)
    health_task = get_by_category("health", 10)

    headlines, finance, geo, health = await asyncio.gather(
        headlines_task, finance_task, geo_task, health_task
    )

    def _top_headlines(data, n=5):
        return [a.get("title", "") for a in data.get("articles", [])[:n]]

    headlines_text = "\n".join(f"• {h}" for h in _top_headlines(headlines, 8))
    finance_text = "\n".join(f"• {h}" for h in _top_headlines(finance, 5))
    geo_text = "\n".join(f"• {h}" for h in _top_headlines(geo, 5))
    health_text = "\n".join(f"• {h}" for h in _top_headlines(health, 4))

    prompt = f"""You are a world-class news analyst. Create a concise daily briefing based on today's top news.

TOP HEADLINES:
{headlines_text}

MARKETS & FINANCE:
{finance_text}

GEOPOLITICS:
{geo_text}

HEALTH:
{health_text}

Write a professional 5-section briefing:
1. Executive Summary (2 sentences)
2. Markets & Economy (2-3 sentences)
3. Geopolitics (2-3 sentences)
4. Health & Science (1-2 sentences)
5. Key Things to Watch (3 bullet points)

Be concise and factual."""

    ai_text = await _groq(prompt, max_tokens=600)

    if not ai_text:
        ai_text = (
            "**Daily Briefing** (Set GROQ_API_KEY for AI-powered briefings)\n\n"
            f"**Top Headlines:**\n{headlines_text}\n\n"
            f"**Markets:**\n{finance_text}\n\n"
            f"**Geopolitics:**\n{geo_text}\n\n"
            f"**Health:**\n{health_text}"
        )

    result = {
        "briefing": ai_text,
        "ai_powered": bool(os.getenv("GROQ_API_KEY")),
        "model": GROQ_MODEL if os.getenv("GROQ_API_KEY") else "rule-based",
        "sections": [
            "executive_summary",
            "markets",
            "geopolitics",
            "health",
            "watch_list",
        ],
        "articles_analyzed": (
            len(headlines.get("articles", []))
            + len(finance.get("articles", []))
            + len(geo.get("articles", []))
            + len(health.get("articles", []))
        ),
    }
    c_set("ai_brief", ck, result, ttl=1800)
    return result


async def compare_topics(topic1: str, topic2: str) -> dict:
    """Compare news coverage and sentiment of two topics."""
    arts1_task = _get_news_for_topic(topic1, 8)
    arts2_task = _get_news_for_topic(topic2, 8)
    arts1, arts2 = await asyncio.gather(arts1_task, arts2_task)

    text1 = _articles_to_text(arts1)
    text2 = _articles_to_text(arts2)

    prompt = f"""Compare the news coverage of '{topic1}' vs '{topic2}'.

{topic1} News:
{text1}

{topic2} News:
{text2}

Provide a JSON with:
- topic1_sentiment: positive/negative/neutral
- topic2_sentiment: positive/negative/neutral
- coverage_volume: which topic has more coverage
- key_differences: list of 3 key differences in coverage
- market_implications: brief impact statement
Respond with only valid JSON."""

    ai_text = await _groq(prompt, max_tokens=400)
    sent1 = _rule_based_sentiment(arts1, topic1)
    sent2 = _rule_based_sentiment(arts2, topic2)

    if ai_text:
        try:
            ai_data = json.loads(ai_text)
            return {
                "topic1": topic1,
                "topic2": topic2,
                "comparison": ai_data,
                "topic1_article_count": len(arts1),
                "topic2_article_count": len(arts2),
                "ai_powered": True,
                "model": GROQ_MODEL,
            }
        except Exception:
            pass

    return {
        "topic1": topic1,
        "topic2": topic2,
        "topic1_sentiment": sent1["overall"],
        "topic2_sentiment": sent2["overall"],
        "topic1_score": sent1["score"],
        "topic2_score": sent2["score"],
        "topic1_article_count": len(arts1),
        "topic2_article_count": len(arts2),
        "ai_powered": False,
    }


async def analyze_text(text: str) -> dict:
    """Analyze any custom text — sentiment, entities, summary."""
    from utils.text_filter import categorize, extract_entities

    sent = sentiment_score(text)
    ents = extract_entities(text)
    cats = categorize(text[:200])
    words = len(text.split())

    prompt = f"""Analyze this news text and return JSON with:
- summary: one sentence summary
- category: main category (finance/health/geopolitical/technology/sports/world)
- key_facts: list of 3 key facts
- bias_detected: boolean
- credibility_signals: list of credibility indicators

Text: {text[:1000]}

Respond with only valid JSON."""

    ai_text = await _groq(prompt, max_tokens=300)
    base = {
        "word_count": words,
        "sentiment": sent,
        "entities": ents,
        "categories": cats,
        "ai_powered": bool(ai_text),
    }

    if ai_text:
        try:
            base.update(json.loads(ai_text))
        except Exception:
            pass

    return base


async def get_ai_trends() -> dict:
    """AI-detected trending themes across all news."""
    from scrapers.rss_scraper import get_headlines

    headlines = await get_headlines(150)
    articles = headlines.get("articles", [])
    trends = _rule_based_trends(articles)

    arts_text = "\n".join(a.get("title", "") for a in articles[:30])
    prompt = f"""Based on these recent news headlines, identify the top 5 trending themes globally.
For each theme, provide: name, 1-sentence description, sentiment (positive/negative/neutral), affected_regions.
Return as JSON array.

Headlines:
{arts_text}

Return only valid JSON array."""

    ai_text = await _groq(prompt, max_tokens=400)
    ai_themes = []
    if ai_text:
        try:
            ai_themes = json.loads(ai_text)
        except Exception:
            pass

    return {
        "rule_based_trends": trends,
        "ai_themes": ai_themes,
        "articles_analyzed": len(articles),
        "ai_powered": bool(ai_themes),
        "model": GROQ_MODEL if ai_themes else "rule-based",
    }
