"""Tavily Search API connector for AI-powered news search"""
import aiohttp
import json
from ..base_connector import BaseConnector, RawEvent
from app.config import settings


class TavilyConnector(BaseConnector):
    """Tavily Search API connector for AI-powered real-time news search"""

    SEARCH_TOPICS = [
        ("latest geopolitical developments today", "geopolitical_event", "geopolitics"),
        ("military defense news conflicts", "defense_event", "defense"),
        ("India foreign policy diplomatic relations", "diplomatic_signal", "geopolitics"),
        ("global cybersecurity threats incidents", "cyber_event", "cybersecurity"),
        ("global economic policy trade agreements", "economic_signal", "economy"),
    ]

    def __init__(self):
        super().__init__()
        self.source_id = "tavily_search"
        self.domain = "geopolitics"
        self.update_interval = 3600  # 1 hour
        self.rate_limit = 5
        self.seed_type = "breaking_event"
        self.api_key = getattr(settings, 'TAVILY_API_KEY', '')
        self.base_url = "https://api.tavily.com/search"

    async def fetch(self) -> list[RawEvent]:
        """Fetch results from Tavily Search API"""
        if not self.api_key:
            print("Tavily API key not configured, skipping")
            return []

        all_events = []
        try:
            async with aiohttp.ClientSession() as session:
                for query, seed_type, domain in self.SEARCH_TOPICS:
                    try:
                        payload = {
                            'api_key': self.api_key,
                            'query': query,
                            'search_depth': 'basic',
                            'max_results': 10,
                            'include_answer': False,
                        }
                        async with session.post(self.base_url, json=payload, timeout=aiohttp.ClientTimeout(total=20)) as response:
                            if response.status == 200:
                                data = await response.json()
                                results = data.get('results', [])
                                for result in results:
                                    event = RawEvent(
                                        source=self.source_id,
                                        domain=domain,
                                        title=result.get('title', ''),
                                        text=result.get('content', ''),
                                        url=result.get('url', ''),
                                        published_at=result.get('published_date', ''),
                                        language='en',
                                        seed_type=seed_type,
                                        raw_data={
                                            'score': result.get('score', 0),
                                        }
                                    )
                                    all_events.append(event)
                    except Exception as e:
                        print(f"Tavily search error ({query[:30]}): {e}")
        except Exception as e:
            print(f"Tavily fetch error: {e}")
        return all_events


tavily_connector = TavilyConnector()
