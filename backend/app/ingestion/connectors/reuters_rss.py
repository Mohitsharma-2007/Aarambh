"""Reuters RSS connector for global news articles"""
import aiohttp
from ..base_connector import BaseConnector, RawEvent


class ReutersRSSConnector(BaseConnector):
    """Reuters RSS feed connector for breaking international news"""

    FEEDS = [
        ("https://feeds.reuters.com/reuters/topNews", "breaking_event"),
        ("https://feeds.reuters.com/reuters/worldNews", "geopolitical_event"),
        ("https://feeds.reuters.com/reuters/businessNews", "economic_signal"),
        ("https://feeds.reuters.com/reuters/technologyNews", "tech_event"),
    ]

    def __init__(self):
        super().__init__()
        self.source_id = "reuters_global"
        self.domain = "geopolitics"
        self.update_interval = 600  # 10 minutes
        self.rate_limit = 30
        self.seed_type = "breaking_event"

    async def fetch(self) -> list[RawEvent]:
        """Fetch multiple Reuters RSS feeds"""
        all_events = []
        try:
            async with aiohttp.ClientSession() as session:
                for feed_url, seed_type in self.FEEDS:
                    try:
                        async with session.get(feed_url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                            if response.status == 200:
                                content = await response.text()
                                events = self.parse_rss(content)
                                for ev in events:
                                    ev.seed_type = seed_type
                                all_events.extend(events)
                    except Exception as e:
                        print(f"Reuters feed error ({feed_url}): {e}")
        except Exception as e:
            print(f"Reuters fetch error: {e}")
        return all_events


reuters_connector = ReutersRSSConnector()
