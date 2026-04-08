"""NewsAPI connector for aggregated global news"""
import aiohttp
import json
from datetime import datetime, timedelta
from ..base_connector import BaseConnector, RawEvent
from app.config import settings


class NewsAPIConnector(BaseConnector):
    """NewsAPI.org connector for aggregated global news articles"""

    TOPIC_QUERIES = [
        ("geopolitics OR diplomacy OR sanctions OR conflict", "geopolitical_event", "geopolitics"),
        ("defense OR military OR weapons OR armed forces", "defense_event", "defense"),
        ("economy OR GDP OR inflation OR trade", "economic_signal", "economy"),
        ("cybersecurity OR cyberattack OR data breach", "cyber_event", "cybersecurity"),
        ("India foreign policy OR India diplomacy", "diplomatic_signal", "geopolitics"),
    ]

    def __init__(self):
        super().__init__()
        self.source_id = "newsapi_aggregated"
        self.domain = "geopolitics"
        self.update_interval = 1800  # 30 minutes
        self.rate_limit = 10
        self.seed_type = "breaking_event"
        self.api_key = getattr(settings, 'NEWSAPI_KEY', '')
        self.base_url = "https://newsapi.org/v2/everything"

    async def fetch(self) -> list[RawEvent]:
        """Fetch news from NewsAPI across multiple topic queries"""
        if not self.api_key:
            print("NewsAPI key not configured, skipping")
            return []

        all_events = []
        from_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        try:
            async with aiohttp.ClientSession() as session:
                for query, seed_type, domain in self.TOPIC_QUERIES:
                    try:
                        params = {
                            'q': query,
                            'from': from_date,
                            'sortBy': 'publishedAt',
                            'pageSize': 20,
                            'language': 'en',
                            'apiKey': self.api_key,
                        }
                        async with session.get(self.base_url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                            if response.status == 200:
                                data = await response.json()
                                articles = data.get('articles', [])
                                for article in articles:
                                    if not article.get('title') or article['title'] == '[Removed]':
                                        continue
                                    event = RawEvent(
                                        source=self.source_id,
                                        domain=domain,
                                        title=article.get('title', ''),
                                        text=article.get('description', '') or article.get('content', ''),
                                        url=article.get('url', ''),
                                        published_at=article.get('publishedAt', ''),
                                        language='en',
                                        seed_type=seed_type,
                                        raw_data={
                                            'source_name': article.get('source', {}).get('name', ''),
                                            'author': article.get('author', ''),
                                            'image_url': article.get('urlToImage', ''),
                                        }
                                    )
                                    all_events.append(event)
                    except Exception as e:
                        print(f"NewsAPI query error ({query[:30]}): {e}")
        except Exception as e:
            print(f"NewsAPI fetch error: {e}")
        return all_events


newsapi_connector = NewsAPIConnector()
