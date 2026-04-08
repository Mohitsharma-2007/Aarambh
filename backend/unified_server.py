"""
AARAMBH Unified Backend Server — v3.0
=====================================
Single server on port 8000 that combines:
  - Finance API (Google Finance, Yahoo Finance, AI Analysis)
  - News Platform (Headlines, Live TV, Geopolitical, Health)
  - Economy Platform (PIB, MoSPI, NDAP, Social Feeds, Global)
  - AI Services (OpenRouter, Groq, Google AI)

Run:
  cd d:\AARAMBH\backend
  python unified_server.py
"""

import os
import sys

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="AARAMBH — Unified Intelligence Platform",
    description=(
        "Single-server backend combining Finance, News, Economy, and AI services.\n\n"
        "## Finance\n"
        "Google Finance · Yahoo Finance · AI Analysis · Charts · Dashboard\n\n"
        "## News\n"
        "Headlines · Live TV · Geopolitical · Health · Science\n\n"
        "## Economy\n"
        "PIB · MoSPI · NDAP · India Gov · Sectors · Global · Social Feeds\n\n"
        "## AI\n"
        "OpenRouter (Gemini priority) · Groq · Google AI"
    ),
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────── Finance Platform Routers ────────────
try:
    from routers import google_finance, yahoo_finance, google_news, google_ai, unified_finance
    app.include_router(google_finance.router, prefix="/api/google-finance", tags=["Google Finance"])
    app.include_router(yahoo_finance.router, prefix="/api/yahoo-finance", tags=["Yahoo Finance"])
    app.include_router(google_news.router, prefix="/api/google-news", tags=["Google News"])
    app.include_router(google_ai.router, prefix="/api/google-ai", tags=["Google AI"])
    app.include_router(unified_finance.router, prefix="/api/finance/unified", tags=["Unified Finance"])
    print("✓ Finance: Google Finance, Yahoo Finance, Google News, Google AI, Unified")
except Exception as e:
    print(f"✗ Finance primary routers: {e}")

try:
    from routers import advanced_company_api, comprehensive_dashboard_api, exact_dashboard_api, multi_api_dashboard, aarambh_finance_api
    app.include_router(advanced_company_api.router, prefix="/api/advanced", tags=["Advanced Company"])
    app.include_router(comprehensive_dashboard_api.router, prefix="/api/dashboard", tags=["Dashboard"])
    app.include_router(exact_dashboard_api.router, prefix="/api/exact", tags=["Exact Dashboard"])
    app.include_router(multi_api_dashboard.router, prefix="/api/multi", tags=["Multi-API Dashboard"])
    app.include_router(aarambh_finance_api.router, prefix="/api/aarambh", tags=["AARAMBH Finance"])
    print("✓ Finance: Advanced, Dashboard, Multi-API, AARAMBH")
except Exception as e:
    print(f"✗ Finance secondary routers: {e}")

# ──────────── News Platform Routers ────────────
try:
    from routers import news, news_enhanced, live_tv_comprehensive, geopolitical, health as health_router, ai_analysis_enhanced
    # Standard News - Matches legacy Api.json endpoints
    app.include_router(news.router, prefix="/api/news", tags=["News Standard"])
    
    # Enhanced News - Frontend expects /api/news-enhanced
    app.include_router(news_enhanced.router, prefix="/api/news-enhanced", tags=["News Enhanced"])
    
    # Comprehensive Live TV - Frontend expects /api/live-tv-comprehensive
    app.include_router(live_tv_comprehensive.router, prefix="/api/live-tv-comprehensive", tags=["Live TV"])
    app.include_router(live_tv_comprehensive.router, prefix="/api/live-tv", tags=["Live TV Alias"])
    
    app.include_router(geopolitical.router, prefix="/api/geopolitical", tags=["Geopolitical"])
    app.include_router(health_router.router, prefix="/api/health-news", tags=["Health News"])
    app.include_router(ai_analysis_enhanced.router, prefix="/api/ai-analysis", tags=["AI Analysis News"])
    print("✓ News: Standard, Enhanced, Live TV, Geopolitical, Health, AI Analysis")
except Exception as e:
    print(f"✗ News routers: {e}")

# ──────────── Economy Platform Routers ────────────
try:
    from routers import pib, mospi, ndap, india_gov, sectors, global_economy, social_feeds, documents as doc_router, ai_analysis_economy
    app.include_router(india_gov.router, prefix="/api/india", tags=["India Gov"])
    app.include_router(pib.router, prefix="/api/pib", tags=["PIB"])
    app.include_router(ndap.router, prefix="/api/ndap", tags=["NDAP"])
    app.include_router(mospi.router, prefix="/api/mospi", tags=["MoSPI"])
    app.include_router(sectors.router, prefix="/api/sectors", tags=["Sectors"])
    app.include_router(global_economy.router, prefix="/api/global", tags=["Global Economy"])
    app.include_router(social_feeds.router, prefix="/api/social", tags=["Social Feeds"])
    app.include_router(doc_router.router, prefix="/api/docs", tags=["Documents"])
    app.include_router(ai_analysis_economy.router, prefix="/api/ai", tags=["AI Analysis Economy"])
    print("✓ Economy: India Gov, PIB, NDAP, MoSPI, Sectors, Global, Social, Docs, AI")
except Exception as e:
    print(f"✗ Economy routers: {e}")

# ──────────── AI Agent Endpoint ────────────
import httpx
from fastapi import Body

OPENROUTER_KEY = os.environ.get(
    "OPENROUTER_API_KEY",
    os.environ.get("LLM_API_KEY", "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")
)

AI_SYSTEM_PROMPT = """You are AARAMBH Intelligence — a Professional Financial Analyst, Macroeconomic Strategist, News Intelligence Officer, and Ontology Specialist.

Your core competencies:
- **Financial Analysis**: Stock valuation (DCF, P/E, PEG), technical patterns (RSI, MACD, Bollinger), sector rotation, portfolio construction, risk-adjusted returns.
- **Macroeconomic Intelligence**: GDP, CPI, monetary policy (RBI, Fed, ECB), fiscal policy, trade balances, sovereign debt analysis, global supply chains.
- **News & Geopolitical Analysis**: Evaluate market impact of news events, geopolitical risk scoring, sentiment decomposition, narrative analysis.
- **Ontology & Knowledge Graphs**: Entity relationships, causal inference chains, knowledge graph reasoning, multi-dimensional data correlation.

Response guidelines:
- Be precise, data-driven, and professional.
- Use specific numbers, ratios, and metrics when discussing financial topics.
- Provide actionable insights, not generic advice.
- Reference relevant economic indicators and market benchmarks.
- Format responses with clear structure using markdown.
- When uncertain, state confidence levels and cite reasoning."""


# ─── Conversation Memory (In-Memory for now) ───
CONVERSATIONS = {}

@app.get("/api/v1/ai/conversations", tags=["AI Agent"])
async def get_conversations():
    return {"conversations": [
        {"id": cid, "title": c["title"], "created_at": c["created_at"], "message_count": len(c["messages"])}
        for cid, c in CONVERSATIONS.items()
    ]}

@app.get("/api/v1/ai/conversations/{conversation_id}/messages", tags=["AI Agent"])
async def get_conversation_messages(conversation_id: str):
    if conversation_id not in CONVERSATIONS:
        return {"messages": []}
    return {"messages": CONVERSATIONS[conversation_id]["messages"]}

@app.post("/api/v1/ai/chat", tags=["AI Agent"])
async def send_chat_message(body: dict = Body(...)):
    message = body.get("message", "")
    conversation_id = body.get("conversation_id")
    
    from datetime import datetime
    import uuid

    if not conversation_id or conversation_id not in CONVERSATIONS:
        conversation_id = str(uuid.uuid4())
        CONVERSATIONS[conversation_id] = {
            "title": message[:30] + ("..." if len(message) > 30 else ""),
            "created_at": datetime.now().isoformat(),
            "messages": []
        }
    
    history = CONVERSATIONS[conversation_id]["messages"]
    messages = [{"role": "system", "content": AI_SYSTEM_PROMPT}]
    for m in history[-10:]:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": message})
    
    models = [
        "liquid/lfm-2.5-1.2b-thinking:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "mistralai/mistral-small-3.1-24b-instruct:free",
        "qwen/qwen3-coder:free",
        "google/gemma-3-4b-it:free",
        "google/gemini-2.0-flash-001"
    ]
    answer = "I am unable to process your request at this moment."
    used_model = None
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for model in models:
            try:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={"model": model, "messages": messages, "max_tokens": 2048}
                )
                if resp.status_code == 200:
                    answer = resp.json()["choices"][0]["message"]["content"]
                    used_model = model
                    break
            except: continue

    CONVERSATIONS[conversation_id]["messages"].append({"role": "user", "content": message, "timestamp": datetime.now().isoformat()})
    CONVERSATIONS[conversation_id]["messages"].append({"role": "assistant", "content": answer, "timestamp": datetime.now().isoformat()})
    
    return {
        "response": answer,
        "conversation_id": conversation_id,
        "model": used_model
    }

@app.get("/api/ai/setup", tags=["AI Agent"])
async def ai_setup():
    """Endpoint for frontend to check AI configuration."""
    return {
        "success": True,
        "providers": [
            {
                "id": "openrouter",
                "name": "OpenRouter",
                "models": [
                    {"id": "liquid/lfm-2.5-1.2b-thinking:free", "name": "Liquid LFM 2.5 (Fastest)"},
                    {"id": "meta-llama/llama-3.3-70b-instruct:free", "name": "Llama 3.3 70B"},
                    {"id": "google/gemini-2.0-flash-001", "name": "Gemini 2.0 Flash"}
                ]
            }
        ]
    }

@app.post("/api/ai/query", tags=["AI Agent"])
async def ai_query_old(body: dict = Body(...)):
    # Compatibility with older panel
    query = body.get("query", "")
    history = body.get("history", [])
    messages = [{"role": "system", "content": AI_SYSTEM_PROMPT}]
    for h in history[-6:]:
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": query})
    
    models = [
        "liquid/lfm-2.5-1.2b-thinking:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "mistralai/mistral-small-3.1-24b-instruct:free",
        "qwen/qwen3-coder:free",
        "google/gemma-3-4b-it:free",
        "google/gemini-2.0-flash-001"
    ]
    async with httpx.AsyncClient(timeout=60.0) as client:
        for model in models:
            try:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"},
                    json={"model": model, "messages": messages}
                )
                if resp.status_code == 200:
                    return {"response": resp.json()["choices"][0]["message"]["content"], "model": model}
            except: continue
    return {"response": "Service unavailable.", "model": None}


# ──────────── Root Endpoints ────────────
@app.get("/", tags=["Root"])
def root():
    return {
        "platform": "AARAMBH Unified Intelligence",
        "version": "3.0.0",
        "docs": "/docs",
        "services": {
            "finance": "/api/google-finance, /api/yahoo-finance, /api/finance/unified",
            "news": "/api/news, /api/live-tv",
            "economy": "/api/india, /api/pib, /api/social, /api/global",
            "ai": "/api/ai, /api/ai-analysis, /api/google-ai, /api/ai/query",
        }
    }


@app.get("/health", tags=["Root"])
def health():
    return {"status": "healthy", "version": "3.0.0"}


if __name__ == "__main__":
    print(f"\n{'='*65}")
    print("   AARAMBH — Unified Intelligence Platform v3.0")
    print(f"   API Docs: http://localhost:8000/docs")
    print(f"{'='*65}\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
