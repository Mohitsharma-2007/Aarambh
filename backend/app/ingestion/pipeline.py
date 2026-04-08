"""Data ingestion pipeline service"""
import asyncio
import json
from typing import List, Dict, Any
from datetime import datetime
from aiokafka import AIOKafkaProducer
from loguru import logger

from app.config import settings
from app.ingestion.connectors.pib_rss import pib_connector
from app.ingestion.connectors.gdelt import gdelt_connector
from app.ingestion.connectors.world_bank import world_bank_connector
from app.ingestion.connectors.mea_rss import mea_connector
from app.ingestion.connectors.acled import acled_connector
from app.ingestion.connectors.reuters_rss import reuters_connector
from app.ingestion.connectors.aljazeera_rss import aljazeera_connector
from app.ingestion.connectors.bbc_rss import bbc_connector
from app.ingestion.connectors.newsapi_connector import newsapi_connector
from app.ingestion.connectors.tavily_connector import tavily_connector
from app.ingestion.connectors.event_registry import event_registry_connector
from app.ingestion.connectors.rss_aggregator import rss_aggregator_connector
from app.ingestion.base_connector import RawEvent


class IngestionPipeline:
    """Main data ingestion pipeline — 12 connectors across news, defense, economy, cyber"""

    def __init__(self):
        self.connectors = [
            # Original connectors
            pib_connector,
            gdelt_connector,
            world_bank_connector,
            mea_connector,
            acled_connector,
            # New wire services
            reuters_connector,
            bbc_connector,
            aljazeera_connector,
            # API-based sources
            newsapi_connector,
            tavily_connector,
            event_registry_connector,
            # Aggregated RSS (15+ feeds in one connector)
            rss_aggregator_connector,
        ]
        self.producer = None
        self.running = False
        
    async def start(self):
        """Start the ingestion pipeline"""
        logger.info("Starting AARAMBH data ingestion pipeline")
        self.running = True
        
        # Initialize Kafka producer
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        # Start concurrent ingestion tasks
        tasks = []
        for connector in self.connectors:
            task = asyncio.create_task(self._run_connector(connector))
            tasks.append(task)
            
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Ingestion pipeline error: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the ingestion pipeline"""
        logger.info("Stopping AARAMBH data ingestion pipeline")
        self.running = False
        
        if self.producer:
            await self.producer.stop()
    
    async def _run_connector(self, connector) -> None:
        """Run a single connector continuously"""
        logger.info(f"Starting connector: {connector.source_id}")
        
        while self.running:
            try:
                # Fetch data
                events = await connector.fetch()
                
                if events:
                    logger.info(f"Fetched {len(events)} events from {connector.source_id}")
                    
                    # Publish to Kafka
                    for event in events:
                        await self._publish_event(event, connector)
                        
                # Wait for next update
                await asyncio.sleep(connector.update_interval)
                
            except Exception as e:
                logger.error(f"Connector {connector.source_id} error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _publish_event(self, event: RawEvent, connector) -> None:
        """Publish event to appropriate Kafka topic"""
        try:
            topic = f"raw.{connector.domain}"
            
            # Prepare event data
            event_data = {
                'id': event.id,
                'source': event.source,
                'domain': event.domain,
                'title': event.title,
                'text': event.text,
                'url': event.url,
                'published_at': event.published_at,
                'language': event.language,
                'raw_data': event.raw_data,
                'seed_type': event.seed_type,  # MiroFish integration
                'importance': event.importance,
                'entities': event.entities,
                'sentiment': event.sentiment,
                'ingested_at': datetime.now().isoformat(),
            }
            
            # Send to Kafka
            await self.producer.send_and_wait(
                topic=topic,
                value=event_data,
                key=event.id.encode('utf-8')
            )
            
            logger.debug(f"Published event {event.id} to topic {topic}")
            
        except Exception as e:
            logger.error(f"Failed to publish event {event.id}: {e}")


# Singleton instance
ingestion_pipeline = IngestionPipeline()
