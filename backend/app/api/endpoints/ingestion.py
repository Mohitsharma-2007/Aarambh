"""Data ingestion API endpoints — wired to ingestion_service (System A)"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio

from app.services.ingestion_service import ingestion_service
from app.config import settings

router = APIRouter()


# ── Response Models ──

class ConnectorInfo(BaseModel):
    name: str
    tier: str          # green / yellow / red
    type: str          # api / rss / scraper
    domain: str
    status: str        # ok / error / pending
    last_fetch: Optional[str] = None
    item_count: int = 0
    error: Optional[str] = None


class IngestionStatus(BaseModel):
    running: bool
    last_run: Optional[str]
    total_connectors: int
    connectors: Dict[str, Any]


class DetailedStatus(BaseModel):
    connectors: List[ConnectorInfo]
    total_events: int
    last_run: Optional[str]


# ── Background helper ──

async def _run_ingestion_background(session_factory):
    """Run full ingestion + save to DB in background"""
    try:
        result = await ingestion_service.run_full_ingestion()
        async with session_factory() as session:
            saved = await ingestion_service.save_to_db(result["items"], session)
        from loguru import logger
        logger.info(f"Background ingestion: fetched {result['total_items']}, saved {saved}")
    except Exception as e:
        from loguru import logger
        logger.error(f"Background ingestion failed: {e}")


async def _run_scraping_background(session_factory):
    """Run all scrapers + save to DB in background"""
    try:
        from app.services.scraping_service import scraping_service
        result = await scraping_service.run_all_scrapers()
        async with session_factory() as session:
            saved = await ingestion_service.save_to_db(result["items"], session)
        from loguru import logger
        logger.info(f"Background scraping: fetched {result['total_items']}, saved {saved}")
    except Exception as e:
        from loguru import logger
        logger.error(f"Background scraping failed: {e}")


# ── Endpoints ──

@router.get("/status")
async def get_ingestion_status() -> Dict[str, Any]:
    """Get current ingestion status"""
    status = ingestion_service.get_status()
    return {
        "running": False,
        "last_run": status.get("last_run"),
        "total_connectors": status.get("total_connectors", 0),
        "connectors": status.get("connectors", {}),
    }


@router.get("/connectors")
async def get_connectors() -> List[Dict[str, Any]]:
    """Get all registered connectors with their metadata"""
    registry = ingestion_service.get_source_registry()
    status_map = ingestion_service.connector_status

    connectors = []
    for name, meta in registry.items():
        st = status_map.get(name, {})
        connectors.append({
            "name": name,
            "tier": meta.get("tier", "yellow"),
            "type": meta.get("type", "rss"),
            "domain": meta.get("domain", "geopolitics"),
            "url": meta.get("url", ""),
            "status": st.get("status", "pending"),
            "last_fetch": st.get("last_fetch"),
            "item_count": st.get("count", 0),
            "error": st.get("error"),
        })
    return connectors


@router.get("/connectors/detailed")
async def get_detailed_connectors() -> Dict[str, Any]:
    """Detailed per-connector status grouped by tier"""
    registry = ingestion_service.get_source_registry()
    status_map = ingestion_service.connector_status

    green, yellow, red = [], [], []
    total_events = 0

    for name, meta in registry.items():
        st = status_map.get(name, {})
        count = st.get("count", 0)
        total_events += count

        entry = {
            "name": name,
            "tier": meta.get("tier", "yellow"),
            "type": meta.get("type", "rss"),
            "domain": meta.get("domain", "geopolitics"),
            "status": st.get("status", "pending"),
            "last_fetch": st.get("last_fetch"),
            "item_count": count,
            "error": st.get("error"),
        }
        tier = meta.get("tier", "yellow")
        if tier == "green":
            green.append(entry)
        elif tier == "red":
            red.append(entry)
        else:
            yellow.append(entry)

    return {
        "green": green,
        "yellow": yellow,
        "red": red,
        "total_connectors": len(registry),
        "total_events": total_events,
        "last_run": ingestion_service.last_run.isoformat() if ingestion_service.last_run else None,
    }


@router.get("/sources")
async def get_available_sources() -> Dict[str, Any]:
    """Get all available data sources with metadata"""
    registry = ingestion_service.get_source_registry()

    by_domain: Dict[str, list] = {}
    for name, meta in registry.items():
        domain = meta.get("domain", "geopolitics")
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append({
            "id": name.lower().replace(" ", "_"),
            "name": name,
            "type": meta.get("type", "rss").upper(),
            "tier": meta.get("tier", "yellow"),
            "url": meta.get("url", ""),
        })

    return {
        **by_domain,
        "total_sources": len(registry),
        "domains": list(by_domain.keys()),
    }


@router.post("/trigger-background")
async def trigger_ingestion_background(background_tasks: BackgroundTasks):
    """Trigger full ingestion in background"""
    from app.database import async_session
    background_tasks.add_task(_run_ingestion_background, async_session)
    return {"message": "Ingestion triggered in background", "status": "started"}


@router.post("/scrape")
async def trigger_scraping_background(background_tasks: BackgroundTasks):
    """Trigger web scraping in background"""
    from app.database import async_session
    background_tasks.add_task(_run_scraping_background, async_session)
    return {"message": "Scraping triggered in background", "status": "started"}


@router.post("/fetch-source/{source_name}")
async def fetch_single_source(source_name: str) -> Dict[str, Any]:
    """Manually trigger ingestion for a single source"""
    try:
        items = await ingestion_service.fetch_single_source(source_name)
        if items is None:
            raise HTTPException(status_code=404, detail=f"Source '{source_name}' not found")

        # Save to DB
        from app.database import async_session
        async with async_session() as session:
            saved = await ingestion_service.save_to_db(items, session)

        return {
            "source": source_name,
            "status": "success",
            "events_fetched": len(items),
            "events_saved": saved,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch from {source_name}: {str(e)}")


@router.get("/scheduler")
async def get_scheduler_status() -> Dict[str, Any]:
    """Get background scheduler status"""
    try:
        from app.services.scheduler_service import ingestion_scheduler
        return ingestion_scheduler.get_status()
    except ImportError:
        return {"running": False, "error": "Scheduler not available"}


@router.post("/scheduler/start")
async def start_scheduler() -> Dict[str, Any]:
    """Start the background ingestion scheduler"""
    try:
        from app.services.scheduler_service import ingestion_scheduler
        await ingestion_scheduler.start()
        return {"status": "started", "interval": ingestion_scheduler.interval}
    except ImportError:
        raise HTTPException(status_code=500, detail="Scheduler not available")


@router.post("/scheduler/stop")
async def stop_scheduler() -> Dict[str, Any]:
    """Stop the background ingestion scheduler"""
    try:
        from app.services.scheduler_service import ingestion_scheduler
        await ingestion_scheduler.stop()
        return {"status": "stopped"}
    except ImportError:
        raise HTTPException(status_code=500, detail="Scheduler not available")
