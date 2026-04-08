"""
AARAMBH Intelligence Terminal - FastAPI Application Entry Point

Route organization:
  /health                         -> Health check
  /api/v1/market/*                -> Market data (inline endpoints)
  /api/v1/signals/*               -> Quant signals (inline endpoints)
  /api/v1/ai/*                    -> AI provider info (inline endpoints)
  /api/graph/*                    -> MiroFish graph API (FastAPI router)
  /api/simulation/*               -> MiroFish simulation API (FastAPI router)
  /api/report/*                   -> Report generation API (FastAPI router)
  /ontology-flask/*               -> Flask ontology app WSGI fallback
    Blueprints inside Flask resolve to:
      /ontology-flask/graph/*
      /ontology-flask/simulation/*
      /ontology-flask/report/*
    The frontend normally connects directly to Flask on port 5001,
    so this mount is only a fallback for single-port deployments.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from app.config import settings
from app.database import init_db, async_session, Entity
from sqlalchemy import select, func


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

async def run_startup_ingestion():
    """Check if DB has events, if not trigger initial ingestion."""
    from app.database import Event
    async with async_session() as session:
        event_count = await session.scalar(select(func.count(Event.id)))
        if event_count and event_count > 30:
            logger.info(f"Database has {event_count} events, skipping startup ingestion")
            return

        logger.info("Few events in database, running startup ingestion...")
        try:
            from app.services.ingestion_service import ingestion_service
            result = await ingestion_service.run_full_ingestion()
            saved = await ingestion_service.save_to_db(result["items"], session)
            logger.info(f"Startup ingestion: fetched {result['total_items']}, saved {saved}")
        except Exception as e:
            logger.warning(f"Startup ingestion failed (non-fatal): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(f"Starting {getattr(settings, 'env', 'default')} server...")
    await init_db()

    # Run startup ingestion in background
    import asyncio
    startup_task = asyncio.create_task(run_startup_ingestion())

    # Start background scheduler
    try:
        from app.services.scheduler_service import ingestion_scheduler
        await ingestion_scheduler.start()
        logger.info("Background ingestion scheduler started")
    except ImportError as e:
        logger.warning(f"Scheduler not available: {e}")
    except Exception as e:
        logger.warning(f"Scheduler failed to start: {e}")

    try:
        yield
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("Shutting down server...")
        if not startup_task.done():
            startup_task.cancel()

        # Stop scheduler
        try:
            from app.services.scheduler_service import ingestion_scheduler
            await ingestion_scheduler.stop()
            logger.info("Background ingestion scheduler stopped")
        except (ImportError, Exception):
            pass


# ---------------------------------------------------------------------------
# App creation
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AARAMBH Intelligence Terminal API",
    description="India's sovereign OSINT platform for strategic intelligence",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if getattr(settings, "debug", True) else None,
    redoc_url="/redoc" if getattr(settings, "debug", True) else None,
)

# ---------------------------------------------------------------------------
# CORS middleware - allow the frontend dev server and common origins
# ---------------------------------------------------------------------------

_cors_origins = settings.cors_origins_list
# Ensure the frontend dev server origins are always included
_frontend_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:3000",
]
if _cors_origins != ["*"]:
    for _origin in _frontend_origins:
        if _origin not in _cors_origins:
            _cors_origins.append(_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Inline V1 Market / Signal / AI endpoints
# ---------------------------------------------------------------------------

@app.get("/api/v1/market/heatmap")
async def market_heatmap():
    """Get market heatmap data."""
    try:
        from app.services.market_service import market_service
        stocks = await market_service.get_all_stocks()
        return {"success": True, "data": stocks}
    except Exception as e:
        logger.warning(f"Market heatmap error: {e}")
        return {"success": True, "data": []}


@app.get("/api/v1/market/quote/{ticker}")
async def get_stock_quote(ticker: str):
    """Get stock quote by ticker."""
    try:
        from app.services.market_service import market_service
        quote = await market_service.get_stock_quote(ticker.upper())
        if not quote:
            return {"success": False, "error": f"Stock {ticker} not found"}
        return {"success": True, "data": quote}
    except Exception as e:
        logger.warning(f"Market service error for {ticker}: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/v1/market/candles/{ticker}")
async def get_candles(ticker: str, timeframe: str = "1d", period: str = "6mo"):
    """Get OHLCV candlestick data."""
    try:
        from app.services.market_service import market_service
        data = await market_service.get_candles(ticker.upper(), timeframe, period)
        if not data:
            return {"success": False, "error": f"No data for {ticker}"}
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/v1/signals/quant/{ticker}")
async def get_quant_signals(ticker: str):
    """Get quantitative signals for ticker."""
    return {
        "success": True,
        "data": {
            "ticker": ticker.upper(),
            "signals": [],
            "recommendation": "HOLD",
        },
    }


@app.get("/api/v1/ai/providers")
async def ai_providers():
    """Get available AI providers."""
    return {
        "success": True,
        "data": {"providers": []},
    }

@app.get("/api/ai/setup")
async def ai_setup():
    """Missing endpoint requested by frontend to check AI capabilities."""
    return {
        "success": True,
        "providers": [
            {
                "id": "openrouter",
                "name": "OpenRouter",
                "models": [
                    {"id": "google/gemini-2.0-flash-001", "name": "Gemini 2.0 Flash"},
                    {"id": "meta-llama/llama-3.3-70b-instruct:free", "name": "Llama 3.3 70B"}
                ]
            }
        ]
    }


# ---------------------------------------------------------------------------
# FastAPI routers  (MiroFish graph / simulation / report)
#
# Each router already defines its own prefix:
#   mirofish_routes   -> prefix="/graph"
#   simulation_routes -> prefix="/simulation"
#   report_routes     -> prefix="/report"
#
# We mount them under "/api" so the final paths are:
#   /api/graph/...   /api/simulation/...   /api/report/...
# ---------------------------------------------------------------------------

try:
    from app.mirofish_routes import router as mirofish_router
    app.include_router(mirofish_router, prefix="/api", tags=["MiroFish Graph"])
    logger.info("MiroFish graph routes loaded   -> /api/graph/*")
except ImportError as e:
    logger.warning(f"MiroFish graph routes not available: {e}")
except Exception as e:
    logger.error(f"Error loading MiroFish graph routes: {e}")

try:
    from app.simulation_routes import router as simulation_router
    app.include_router(simulation_router, prefix="/api", tags=["MiroFish Simulation"])
    logger.info("Simulation routes loaded       -> /api/simulation/*")
except ImportError as e:
    logger.warning(f"Simulation routes not available: {e}")
except Exception as e:
    logger.error(f"Error loading simulation routes: {e}")

try:
    from app.report_routes import router as report_router
    app.include_router(report_router, prefix="/api", tags=["Report"])
    logger.info("Report routes loaded           -> /api/report/*")
except ImportError as e:
    logger.warning(f"Report routes not available: {e}")
except Exception as e:
    logger.error(f"Error loading report routes: {e}")

# ---------------------------------------------------------------------------
# Unified V1 API Routes (All Platforms Integrated)
# ---------------------------------------------------------------------------
try:
    from app.api.v1_routes_unified import router as v1_unified_router
    app.include_router(v1_unified_router, tags=["AARAMBH Unified API v3.0"])
    logger.info("Unified V1 API routes loaded    -> /api/v1/* (Grouped by Category)")
except ImportError as e:
    logger.warning(f"Unified V1 API routes not available: {e}")
except Exception as e:
    logger.error(f"Error loading Unified V1 API routes: {e}")

# ---------------------------------------------------------------------------
# Legacy V1 API Routes (Complete FastAPI endpoints for frontend)
# ---------------------------------------------------------------------------
try:
    from app.api.v1_routes import router as v1_router
    app.include_router(v1_router, tags=["V1 API Legacy"])
    logger.info("V1 API routes loaded           -> /api/v1/*")
except ImportError as e:
    logger.warning(f"V1 API routes not available: {e}")
except Exception as e:
    logger.error(f"Error loading V1 API routes: {e}")


# ---------------------------------------------------------------------------
# Flask ontology app (WSGI fallback)
#
# The canonical Flask server runs standalone on port 5001. The frontend
# (ontology.ts) connects there directly via VITE_API_URL.
#
# This WSGI mount is a **fallback** for single-port deployments where only
# the FastAPI server (port 8000) is exposed.
#
# BUG FIX: Previously the Flask app was mounted at "/api/ontology-flask" but
# its blueprints registered with url_prefix="/api/graph" etc., producing
# broken double-prefix paths like "/api/ontology-flask/api/graph/...".
#
# Fix: create a dedicated Flask app instance for WSGI mounting where
# blueprints use stripped prefixes (just "/graph", "/simulation", "/report"),
# and mount the WSGI app at "/ontology-flask".  Final paths become:
#   /ontology-flask/graph/...
#   /ontology-flask/simulation/...
#   /ontology-flask/report/...
# This avoids any route conflict with the FastAPI routers at /api/*.
# ---------------------------------------------------------------------------

try:
    from a2wsgi import WSGIMiddleware
    from flask import Flask as _Flask

    def _create_wsgi_flask_app():
        """Create a Flask app with adjusted prefixes for WSGI sub-mounting."""
        from app.api.ontology import graph_bp, simulation_bp, report_bp

        flask_app = _Flask(__name__)
        flask_app.config["SECRET_KEY"] = (
            getattr(settings, "secret_key", None)
            or getattr(settings, "SECRET_KEY", None)
            or "aarambh-ontology-secret"
        )
        flask_app.config["JSON_AS_ASCII"] = False
        flask_app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB

        # Register blueprints WITHOUT the "/api" prefix so that combined
        # with the WSGI mount point the paths stay clean and don't conflict
        # with the FastAPI routers at /api/*.
        flask_app.register_blueprint(graph_bp, url_prefix="/graph")
        flask_app.register_blueprint(simulation_bp, url_prefix="/simulation")
        flask_app.register_blueprint(report_bp, url_prefix="/report")

        @flask_app.route("/health")
        def _health():
            return {"status": "ok", "service": "Aarambh Ontology (WSGI fallback)"}

        return flask_app

    _wsgi_flask = _create_wsgi_flask_app()
    app.mount("/ontology-flask", WSGIMiddleware(_wsgi_flask))
    logger.info(
        "Flask ontology WSGI fallback mounted at /ontology-flask "
        "(graph: /ontology-flask/graph/*, "
        "simulation: /ontology-flask/simulation/*, "
        "report: /ontology-flask/report/*)"
    )
except ImportError as e:
    logger.warning(f"Could not mount Flask ontology WSGI app (missing dependency): {e}")
except Exception as e:
    logger.error(f"Error mounting Flask ontology WSGI app: {e}")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    """Health check endpoint with DB connectivity verification."""
    db_status = "unknown"
    entity_count = 0
    event_count = 0

    try:
        from app.database import Event
        async with async_session() as session:
            entity_count = await session.scalar(select(func.count(Entity.id))) or 0
            event_count = await session.scalar(select(func.count(Event.id))) or 0
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "version": "2.0.0",
        "database": db_status,
        "entities": entity_count,
        "events": event_count,
    }
