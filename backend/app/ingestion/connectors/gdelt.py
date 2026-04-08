"""GDELT Project connector for global news events"""
import aiohttp
import json
from datetime import datetime, timedelta
from ..base_connector import BaseConnector, RawEvent
from app.config import settings


class GDELTConnector(BaseConnector):
    """GDELT connector for global news events"""
    
    def __init__(self):
        super().__init__()
        self.source_id = "gdelt_global_news"
        self.domain = "geopolitics"
        self.update_interval = 900  # 15 minutes
        self.rate_limit = 30
        self.seed_type = "breaking_event"
        
    async def fetch(self) -> list[RawEvent]:
        """Fetch GDELT latest updates"""
        try:
            # Get last update info
            async with aiohttp.ClientSession() as session:
                async with session.get(settings.GDELT_API_URL, timeout=30) as response:
                    if response.status != 200:
                        print(f"GDELT API error: HTTP {response.status}")
                        return []
                    
                    content = await response.text()
                    
                    # Parse GDELT format (simplified)
                    events = []
                    lines = content.strip().split('\n')
                    
                    for line in lines[:50]:  # Limit to 50 events
                        if not line.strip():
                            continue
                            
                        try:
                            # GDELT provides event data in tab-separated format
                            parts = line.split('\t')
                            if len(parts) >= 10:
                                event = RawEvent(
                                    source=self.source_id,
                                    domain=self.domain,
                                    title=f"Global Event: {parts[1] if len(parts) > 1 else 'Unknown'}",
                                    text=f"{parts[1] if len(parts) > 1 else ''} - {parts[2] if len(parts) > 2 else ''}",
                                    url=f"https://www.gdeltproject.org/events/{parts[0] if parts else ''}",
                                    published_at=parts[4] if len(parts) > 4 else datetime.now().isoformat(),
                                    language='en',
                                    raw_data={'gdelt_data': parts},
                                    seed_type=self.seed_type,
                                    importance=self._calculate_importance(parts)
                                )
                                events.append(event)
                        except Exception as e:
                            print(f"GDELT line parsing error: {e}")
                            continue
                    
                    return events
                    
        except Exception as e:
            print(f"GDELT fetch error: {e}")
            return []
    
    def _calculate_importance(self, parts: list) -> int:
        """Calculate importance based on GDELT event data"""
        try:
            # Simple importance calculation based on event attributes
            # GDELT fields: [GLOBALEVENTID, SQLDATE, MonthYear, Year, FractionDate, Actor1Code, Actor1Name, Actor1CountryCode...]
            actor_country = parts[5] if len(parts) > 5 else ''
            event_code = parts[1] if len(parts) > 1 else ''
            
            # Higher importance for major countries and significant events
            importance = 5  # Base importance
            
            if actor_country in ['USA', 'CHN', 'RUS', 'IND', 'PAK', 'GBR', 'FRA', 'DEU']:
                importance += 2
                
            if event_code in ['043', '041', '042']:  # Conflict, violence, protest codes
                importance += 3
                
            return min(importance, 10)
        except:
            return 5


# Singleton instance
gdelt_connector = GDELTConnector()
