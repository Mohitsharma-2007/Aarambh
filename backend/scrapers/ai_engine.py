"""
scrapers/ai_engine.py  —  AI Analysis via OpenRouter
=====================================================
Uses OpenRouter API (https://openrouter.ai) to analyze
economic data, documents, and news using any LLM.

Default model: anthropic/claude-3-haiku (free tier available)
Alternatives:  mistralai/mixtral-8x7b, google/gemma-3-27b, meta-llama/llama-3

Set OPENROUTER_API_KEY in .env file.
"""

import asyncio
import json
import os
from typing import Optional

from utils.cache import get as c_get
from utils.cache import set as c_set

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")

# ── Core OpenRouter call ──────────────────────────────────────────────────────


async def _openrouter(
    prompt: str, system: str = "", max_tokens: int = 1000, model: str = None
) -> Optional[str]:
    """Call OpenRouter API. Returns text or None on failure."""
    api_key = OPENROUTER_KEY or os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        return None

    import httpx

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model or DEFAULT_MODEL,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    try:
        async with httpx.AsyncClient(timeout=30) as cli:
            r = await cli.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://economy-platform.local",
                    "X-Title": "Economy Data Platform",
                },
                json=payload,
            )
            if r.status_code == 200:
                data = r.json()
                return data["choices"][0]["message"]["content"]
            return None
    except Exception:
        return None


def _is_ai_available() -> bool:
    return bool(OPENROUTER_KEY or os.getenv("OPENROUTER_API_KEY", ""))


# ── Rule-based fallbacks ──────────────────────────────────────────────────────


def _rule_summary(text: str, topic: str) -> str:
    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 30][:5]
    return (
        f"Summary for '{topic}' (rule-based — set OPENROUTER_API_KEY for AI):\n\n"
        + "\n".join(f"• {l}" for l in lines[:5])
    )


def _rule_insights(text: str) -> list:
    import re

    sentences = re.split(r"[.!?]\s+", text)
    key = [s.strip() for s in sentences if len(s.strip()) > 40][:5]
    return key


def _rule_sentiment(text: str) -> dict:
    pos = [
        "growth",
        "increase",
        "rise",
        "gain",
        "improve",
        "surplus",
        "record",
        "high",
        "strong",
        "positive",
        "recovery",
        "boost",
        "achieve",
        "success",
        "advance",
    ]
    neg = [
        "decline",
        "fall",
        "drop",
        "deficit",
        "risk",
        "challenge",
        "slowdown",
        "inflation",
        "debt",
        "crisis",
        "contraction",
        "negative",
        "concern",
        "pressure",
    ]
    txt = text.lower()
    ps = sum(1 for w in pos if w in txt)
    ns = sum(1 for w in neg if w in txt)
    tot = ps + ns or 1
    scr = (ps - ns) / tot
    return {
        "label": "positive" if scr > 0.1 else ("negative" if scr < -0.1 else "neutral"),
        "score": round(scr, 3),
        "positive_signals": ps,
        "negative_signals": ns,
    }


# ── Public AI functions ───────────────────────────────────────────────────────


async def analyze_document(parsed_doc: dict, focus: str = "") -> dict:
    """
    AI analysis of a parsed document (PDF, Excel, etc.).
    Returns: summary, key_facts, sentiment, classification, insights.
    """
    text = parsed_doc.get("text", "")[:4000]
    title = parsed_doc.get("title", "Document")
    dtype = parsed_doc.get("type", "Document")
    focus_prompt = f" Focus on: {focus}." if focus else ""

    system = (
        "You are an expert Indian economy and policy analyst. "
        "Analyze government documents, circulars, and economic data accurately."
    )
    prompt = f"""Analyze this {dtype}: "{title}"{focus_prompt}

Content excerpt:
{text}

Return JSON with these fields:
- summary: 3-sentence summary
- key_facts: list of 5 specific data points or policy facts
- document_type: Press Release / Circular / Notice / Report / Data / Policy / Scheme / Other
- ministry_or_source: issuing authority
- economic_impact: brief impact statement
- sentiment: positive / neutral / negative
- action_required: any deadlines or compliance requirements
- tags: list of relevant sector/topic tags

Return ONLY valid JSON."""

    ai_text = await _openrouter(prompt, system=system, max_tokens=600)

    if ai_text:
        try:
            result = json.loads(ai_text)
            result["ai_powered"] = True
            return result
        except Exception:
            pass

    # Rule-based fallback
    return {
        "summary": _rule_summary(text, title),
        "key_facts": _rule_insights(text),
        "document_type": parsed_doc.get("doc_class", "Document"),
        "ministry_or_source": parsed_doc.get("source", ""),
        "sentiment": _rule_sentiment(text),
        "tags": [],
        "ai_powered": False,
        "note": "Set OPENROUTER_API_KEY for full AI analysis",
    }


async def summarize_economic_topic(topic: str, context: str = "") -> dict:
    """Summarize current news/data on an economic topic."""
    ck = {"t": "sum", "q": topic}
    if c := c_get("ai_sum", ck):
        return c

    # Fetch relevant news first
    from scrapers.pib_scraper import search_pib

    pib_data = await search_pib(topic, count=5)
    headlines = "\n".join(
        f"• {a.get('title', '')}" for a in pib_data.get("articles", [])[:5]
    )

    prompt = f"""You are an Indian economy expert. Summarize the current state of '{topic}'.
{"Additional context: " + context if context else ""}

Recent PIB releases:
{headlines}

Provide:
1. Current status (2-3 sentences)
2. Key data points / statistics
3. Recent government actions
4. Outlook

Keep it factual and data-driven."""

    ai_text = await _openrouter(prompt, max_tokens=400)
    result = {
        "topic": topic,
        "summary": ai_text or _rule_summary(headlines, topic),
        "headlines": [a.get("title", "") for a in pib_data.get("articles", [])[:5]],
        "ai_powered": bool(ai_text),
    }
    c_set("ai_sum", ck, result, ttl=1800)
    return result


async def extract_data_insights(data: dict, data_type: str = "economic") -> dict:
    """Extract structured insights from raw economic data."""
    data_str = json.dumps(data, default=str)[:3000]

    prompt = f"""Analyze this {data_type} data and extract key insights.

Data: {data_str}

Return JSON with:
- headline_number: single most important number/metric
- trend: "improving" / "declining" / "stable" / "volatile"
- key_insights: list of 4 specific insights
- comparison: how this compares to benchmarks/targets
- risks: list of 2-3 risk factors
- opportunities: list of 2-3 opportunities
- recommended_actions: for policymakers

Return ONLY valid JSON."""

    ai_text = await _openrouter(prompt, max_tokens=500)

    if ai_text:
        try:
            result = json.loads(ai_text)
            result["ai_powered"] = True
            return result
        except Exception:
            pass

    return {
        "headline_number": None,
        "trend": "unknown",
        "key_insights": _rule_insights(str(data)),
        "ai_powered": False,
    }


async def generate_economy_briefing() -> dict:
    """Daily AI economy briefing — India + Global."""
    ck = {"t": "briefing"}
    if c := c_get("ai_brief", ck):
        return c

    # Fetch multiple data sources concurrently
    from scrapers.global_economy import nasdaq_ipo, world_bank
    from scrapers.india_portals import rbi_key_rates
    from scrapers.pib_scraper import get_latest as pib_latest

    pib_task = pib_latest(10)
    rbi_task = rbi_key_rates()
    wb_gdp = world_bank("IN", "NY.GDP.MKTP.KD.ZG", years=3)
    ipo_task = nasdaq_ipo()

    pib, rbi, gdp, ipo = await asyncio.gather(
        pib_task, rbi_task, wb_gdp, ipo_task, return_exceptions=True
    )

    pib_headlines = "\n".join(
        f"• {a.get('title', '')}"
        for a in (pib.get("articles", []) if isinstance(pib, dict) else [])[:6]
    )
    rbi_rates_text = str(rbi.get("rates", "") if isinstance(rbi, dict) else "")[:300]
    gdp_data = str(gdp.get("records", "") if isinstance(gdp, dict) else "")[:300]

    prompt = f"""You are an elite Indian economy analyst. Create a concise daily briefing.

PIB Headlines:
{pib_headlines}

RBI Key Rates: {rbi_rates_text}
India GDP Data: {gdp_data}

Write a professional 5-section daily briefing:
1. EXECUTIVE SUMMARY (2 sentences)
2. INDIA ECONOMY (2-3 sentences with data)
3. MARKETS & FINANCE (2-3 sentences)
4. POLICY & GOVERNANCE (2-3 sentences)
5. WATCH TODAY (3 bullet points)

Be concise, data-driven, and professional."""

    ai_text = await _openrouter(prompt, max_tokens=600)

    if not ai_text:
        ai_text = (
            "**Daily Economy Briefing** (Set OPENROUTER_API_KEY for AI briefing)\n\n"
            f"**PIB Latest:**\n{pib_headlines}\n\n"
            f"**RBI Rates:** {rbi_rates_text[:200]}\n\n"
            f"**India GDP:** {gdp_data[:200]}"
        )

    result = {
        "briefing": ai_text,
        "ai_powered": _is_ai_available(),
        "data_used": {
            "pib_headlines": len(
                (pib.get("articles", []) if isinstance(pib, dict) else [])
            ),
            "rbi_rates": bool(rbi and isinstance(rbi, dict) and rbi.get("rates")),
            "gdp_records": len(
                (gdp.get("records", []) if isinstance(gdp, dict) else [])
            ),
        },
    }
    c_set("ai_brief", ck, result, ttl=3600)
    return result


async def compare_indicators(
    indicator1: str, indicator2: str, context: str = ""
) -> dict:
    """AI comparison of two economic indicators."""
    prompt = f"""Compare '{indicator1}' vs '{indicator2}' from an Indian economic perspective.
{f"Context: {context}" if context else ""}

Return JSON with:
- indicator1_summary: brief description and current status
- indicator2_summary: brief description and current status
- relationship: how they interact
- policy_implications: what policymakers should consider
- for_investors: investment angle

Return ONLY valid JSON."""

    ai_text = await _openrouter(prompt, max_tokens=500)

    if ai_text:
        try:
            result = json.loads(ai_text)
            result["ai_powered"] = True
            return result
        except Exception:
            pass

    return {
        "indicator1": indicator1,
        "indicator2": indicator2,
        "ai_powered": False,
        "note": "Set OPENROUTER_API_KEY for AI comparison",
    }


async def analyze_text_custom(text: str, task: str = "analyze") -> dict:
    """Analyze any custom text — policy document, circular, data etc."""
    TASKS = {
        "analyze": "Analyze this economic/policy content and extract key information.",
        "summarize": "Summarize this content in 5 bullet points.",
        "classify": "Classify this document and extract structured data.",
        "sentiment": "Analyze the economic sentiment and implications.",
        "translate": "Translate the key points to plain English.",
    }
    task_prompt = TASKS.get(task, TASKS["analyze"])
    prompt = f"{task_prompt}\n\nContent:\n{text[:4000]}"
    ai_text = await _openrouter(prompt, max_tokens=500)

    return {
        "task": task,
        "result": ai_text or _rule_summary(text, task),
        "word_count": len(text.split()),
        "ai_powered": bool(ai_text),
        "fallback": not bool(ai_text),
    }


async def get_setup_status() -> dict:
    key = OPENROUTER_KEY or os.getenv("OPENROUTER_API_KEY", "")
    has_key = bool(key)
    current_model = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
    return {
        "openrouter_configured": has_key,
        "model": current_model if has_key else "rule-based fallback",
        "available_free_models": [
            "meta-llama/llama-3.1-8b-instruct:free",
            "meta-llama/llama-3.2-3b-instruct:free",
            "google/gemma-3-27b-it:free",
            "google/gemma-3-12b-it:free",
            "deepseek/deepseek-r1:free",
            "mistralai/mistral-7b-instruct:free",
            "microsoft/phi-3-mini-128k-instruct:free",
        ],
        "setup_instructions": {
            "1": "Register at https://openrouter.ai",
            "2": "Get API key from https://openrouter.ai/keys",
            "3": "Create .env file: OPENROUTER_API_KEY=sk-or-...",
            "4": "Set model: OPENROUTER_MODEL=anthropic/claude-3-haiku",
            "5": "Restart server: python main.py",
        },
        "without_key": "All endpoints work with rule-based analysis. AI adds summaries, insights, and classification.",
        "cost_note": "Many OpenRouter models are free or very cheap. Claude Haiku ~$0.00025/1K tokens.",
    }
