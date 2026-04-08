"""Event Registry connector for structured news events"""
import aiohttp
import json
from datetime import datetime, timedelta
from ..base_connector import BaseConnector, RawEvent
from app.config import settings


class EventRegistryConnector(BaseConnector):
    """Event Registry API connector for structured global news events"""

    def __init__(self):
        super().__init__()
        self.source_id = "event_registry"
        self.domain = "geopolitics"
        self.update_interval = 1800  # 30 minutes
        self.rate_limit = 10
        self.seed_type = "breaking_event"
        self.api_key = getattr(settings, 'EVENT_REGISTRY_API_KEY', '')
        self.base_url = "https://eventregistry.org/api/v1/article/getArticles"

    async def fetch(self) -> list[RawEvent]:
        """Fetch articles from Event Registry"""
        if not self.api_key:
            print("Event Registry API key not configured, skipping")
            return []

        all_events = []
        from_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'apiKey': self.api_key,
                    'resultType': 'articles',
                    'articlesSortBy': 'date',
                    'articlesCount': 50,
                    'dateStart': from_date,
                    'lang': 'eng',
                    'keyword': 'geopolitics OR conflict OR diplomacy OR sanctions OR military',
                    'keywordOper': 'or',
                }
                try:
                    async with session.post(self.base_url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            data = await response.json()
                            articles = data.get('articles', {}).get('results', [])
                            for article in articles:
                                # Determine domain from categories
                                categories = [c.get('label', '') for c in article.get('categories', [])]
                                domain = self._categorize(categories, article.get('title', ''))

                                event = RawEvent(
                                    source=self.source_id,
                                    domain=domain,
                                    title=article.get('title', ''),
                                    text=article.get('body', '')[:2000],
                                    url=article.get('url', ''),
                                    published_at=article.get('dateTimePub', ''),
                                    language='en',
                                    seed_type='breaking_event',
                                    importance=self._importance_from_sentiment(article.get('sentiment', 0)),
                                    sentiment=article.get('sentiment', 0),
                                    entities=[
                                        c.get('label', '') for c in article.get('concepts', [])[:10]
                                    ],
                                    raw_data={
                                        'source_name': article.get('source', {}).get('title', ''),
                                        'image': article.get('image', ''),
                                        'event_uri': article.get('eventUri', ''),
                                    }
                                )
                                all_events.append(event)
                except Exception as e:
                    print(f"Event Registry fetch error: {e}")
        except Exception as e:
            print(f"Event Registry connection error: {e}")
        return all_events

    def _categorize(self, categories: list, title: str) -> str:
        """Determine domain from article categories and title"""
        title_lower = title.lower()
        cat_text = ' '.join(categories).lower()
        combined = f"{cat_text} {title_lower}"

        if any(kw in combined for kw in ['military', 'defense', 'weapon', 'armed']):
            return 'defense'
        if any(kw in combined for kw in ['cyber', 'hack', 'data breach']):
            return 'cybersecurity'
        if any(kw in combined for kw in ['economy', 'gdp', 'trade', 'inflation', 'market']):
            return 'economy'
        if any(kw in combined for kw in ['terror', 'extremis']):
            return 'terrorism'
        if any(kw in combined for kw in ['climate', 'environment', 'disaster']):
            return 'climate'
        return 'geopolitics'

    def _importance_from_sentiment(self, sentiment: float) -> int:
        """Higher absolute sentiment = higher importance"""
        return min(10, max(1, int(abs(sentiment) * 10) + 3))


event_registry_connector = EventRegistryConnector()
