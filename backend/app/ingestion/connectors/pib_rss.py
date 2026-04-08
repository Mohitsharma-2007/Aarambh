"""PIB (Press Information Bureau) RSS connector"""
import aiohttp
from ..base_connector import BaseConnector, RawEvent
from app.config import settings


class PIBConnector(BaseConnector):
    """PIB RSS connector for India government press releases"""
    
    def __init__(self):
        super().__init__()
        self.source_id = "pib_press_releases"
        self.domain = "geopolitics"
        self.update_interval = 900  # 15 minutes
        self.rate_limit = 30
        self.seed_type = "policy_draft"  # MiroFish integration
        
    async def fetch(self) -> list[RawEvent]:
        """Fetch PIB RSS feed"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(settings.PIB_RSS_URL, timeout=30) as response:
                    if response.status == 200:
                        content = await response.text()
                        return self.parse_rss(content)
                    else:
                        print(f"PIB RSS error: HTTP {response.status}")
                        return []
        except Exception as e:
            print(f"PIB fetch error: {e}")
            return []


# Singleton instance
pib_connector = PIBConnector()
