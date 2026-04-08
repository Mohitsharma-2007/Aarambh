"""Al Jazeera RSS connector for Middle East and international news"""
import aiohttp
from ..base_connector import BaseConnector, RawEvent


class AlJazeeraRSSConnector(BaseConnector):
    """Al Jazeera RSS feed connector for international and Middle East news"""

    FEEDS = [
        "https://www.aljazeera.com/xml/rss/all.xml",
    ]

    def __init__(self):
        super().__init__()
        self.source_id = "aljazeera_global"
        self.domain = "geopolitics"
        self.update_interval = 900  # 15 minutes
        self.rate_limit = 20
        self.seed_type = "geopolitical_event"

    async def fetch(self) -> list[RawEvent]:
        """Fetch Al Jazeera RSS feeds"""
        all_events = []
        try:
            async with aiohttp.ClientSession() as session:
                for feed_url in self.FEEDS:
                    try:
                        async with session.get(feed_url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                            if response.status == 200:
                                content = await response.text()
                                all_events.extend(self.parse_rss(content))
                    except Exception as e:
                        print(f"Al Jazeera feed error: {e}")
        except Exception as e:
            print(f"Al Jazeera fetch error: {e}")
        return all_events


aljazeera_connector = AlJazeeraRSSConnector()
