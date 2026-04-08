"""MEA (Ministry of External Affairs) RSS connector"""
import aiohttp
from ..base_connector import BaseConnector, RawEvent
from app.config import settings


class MEAConnector(BaseConnector):
    """MEA RSS connector for India foreign policy"""
    
    def __init__(self):
        super().__init__()
        self.source_id = "mea_foreign_policy"
        self.domain = "geopolitics"
        self.update_interval = 1800  # 30 minutes
        self.rate_limit = 30
        self.seed_type = "diplomatic_signal"
        
    async def fetch(self) -> list[RawEvent]:
        """Fetch MEA RSS feed"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(settings.MEA_RSS_URL, timeout=30) as response:
                    if response.status == 200:
                        content = await response.text()
                        return self.parse_rss(content)
                    else:
                        print(f"MEA RSS error: HTTP {response.status}")
                        return []
        except Exception as e:
            print(f"MEA fetch error: {e}")
            return []


# Singleton instance
mea_connector = MEAConnector()
