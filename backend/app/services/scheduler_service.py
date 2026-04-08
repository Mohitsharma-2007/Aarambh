"""Background Ingestion Scheduler — asyncio-based periodic runner"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger


class IngestionScheduler:
    """Runs ingestion periodically in the background"""

    def __init__(self, interval: int = 1800):
        self.interval = interval  # seconds
        self.running = False
        self.cycle_count = 0
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self._task: Optional[asyncio.Task] = None
        self.last_error: Optional[str] = None

    async def start(self):
        """Start the scheduler loop"""
        if self.running:
            logger.info("Scheduler already running")
            return
        self.running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(f"Ingestion scheduler started (interval={self.interval}s)")

    async def stop(self):
        """Stop the scheduler loop"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Ingestion scheduler stopped")

    async def _loop(self):
        """Main scheduler loop"""
        while self.running:
            self.next_run = datetime.utcnow() + timedelta(seconds=self.interval)
            try:
                await self._run_cycle()
            except Exception as e:
                self.last_error = str(e)
                logger.error(f"Scheduler cycle failed: {e}")

            # Wait for next cycle
            try:
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break

    async def _run_cycle(self):
        """Execute one ingestion cycle"""
        from app.services.ingestion_service import ingestion_service
        from app.database import async_session

        self.cycle_count += 1
        logger.info(f"Scheduler cycle #{self.cycle_count} starting...")

        # Always run full ingestion
        try:
            result = await ingestion_service.run_full_ingestion()
            async with async_session() as session:
                saved = await ingestion_service.save_to_db(result["items"], session)
            logger.info(f"Cycle #{self.cycle_count}: ingested {result['total_items']}, saved {saved}")
        except Exception as e:
            logger.error(f"Ingestion in cycle #{self.cycle_count} failed: {e}")

        # Every 4th cycle, also run scrapers
        if self.cycle_count % 4 == 0:
            try:
                from app.services.scraping_service import scraping_service
                scrape_result = await scraping_service.run_all_scrapers()
                async with async_session() as session:
                    saved = await ingestion_service.save_to_db(scrape_result["items"], session)
                logger.info(f"Cycle #{self.cycle_count}: scraped {scrape_result['total_items']}, saved {saved}")
            except Exception as e:
                logger.error(f"Scraping in cycle #{self.cycle_count} failed: {e}")

        self.last_run = datetime.utcnow()
        self.last_error = None

    def get_status(self) -> dict:
        return {
            "running": self.running,
            "interval": self.interval,
            "interval_seconds": self.interval,
            "cycle_count": self.cycle_count,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "events_last_run": 0,
            "last_error": self.last_error,
        }


# Singleton
ingestion_scheduler = IngestionScheduler()
