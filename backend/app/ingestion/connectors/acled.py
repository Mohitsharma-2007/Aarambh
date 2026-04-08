"""ACLED (Armed Conflict Location & Event Data) connector"""
import aiohttp
import json
from datetime import datetime, timedelta
from ..base_connector import BaseConnector, RawEvent
from app.config import settings


class ACLEDConnector(BaseConnector):
    """ACLED connector for conflict and protest data"""
    
    def __init__(self):
        super().__init__()
        self.source_id = "acled_conflict_data"
        self.domain = "defense"
        self.update_interval = 3600  # 1 hour
        self.rate_limit = 60
        self.seed_type = "breaking_event"
        
    async def fetch(self) -> list[RawEvent]:
        """Fetch ACLED conflict data for South Asia"""
        try:
            # ACLED API for South Asia region
            url = f"{settings.ACLED_API}?region=8&event_date_where=BETWEEN&event_date_from={self._get_date_string(-30)}&event_date_to={self._get_date_string(0)}&format=json"
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Accept': 'application/json',
                    'User-Agent': 'AARAMBH-Intelligence-Terminal/1.0'
                }
                
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_acled_data(data)
                    else:
                        print(f"ACLED API error: HTTP {response.status}")
                        return []
        except Exception as e:
            print(f"ACLED fetch error: {e}")
            return []
    
    def _parse_acled_data(self, data: dict) -> list[RawEvent]:
        """Parse ACLED JSON response"""
        events = []
        
        if 'data' not in data:
            return events
            
        for event_data in data['data'][:20]:  # Limit to 20 events
            try:
                # Calculate importance based on event type and fatalities
                importance = self._calculate_conflict_importance(event_data)
                
                event = RawEvent(
                    source=self.source_id,
                    domain=self.domain,
                    title=f"Conflict Event: {event_data.get('event_type', '')}",
                    text=self._format_conflict_description(event_data),
                    url=f"https://acleddata.com/dashboard/#dashboard/map/{event_data.get('data_id', '')}",
                    published_at=event_data.get('event_date', ''),
                    language='en',
                    raw_data={'acled_data': event_data},
                    seed_type=self.seed_type,
                    importance=importance
                )
                events.append(event)
            except Exception as e:
                print(f"ACLED event parsing error: {e}")
                continue
                
        return events
    
    def _calculate_conflict_importance(self, event_data: dict) -> int:
        """Calculate importance based on conflict event attributes"""
        try:
            base_importance = 5
            
            # Higher importance for events with fatalities
            fatalities = event_data.get('fatalities', 0)
            if fatalities > 0:
                base_importance += min(fatalities // 10, 3)  # Add 1-3 points based on fatalities
            
            # Higher importance for specific event types
            event_type = event_data.get('event_type', '').lower()
            high_importance_events = ['battle', 'violence against civilians', 'remote violence', 'riot']
            if any(event_type in high_importance_events):
                base_importance += 2
            
            # Higher importance for India-related events
            actor1 = event_data.get('actor1', '').lower()
            actor2 = event_data.get('actor2', '').lower()
            if 'india' in actor1 or 'india' in actor2 or 'police' in actor1 or 'police' in actor2:
                base_importance += 2
                
            return min(base_importance, 10)
        except:
            return 5
    
    def _format_conflict_description(self, event_data: dict) -> str:
        """Format conflict event description"""
        try:
            parts = []
            
            if event_data.get('event_type'):
                parts.append(f"Event Type: {event_data['event_type']}")
            
            if event_data.get('actor1'):
                parts.append(f"Actor 1: {event_data['actor1']}")
                
            if event_data.get('actor2'):
                parts.append(f"Actor 2: {event_data['actor2']}")
                
            if event_data.get('location'):
                parts.append(f"Location: {event_data['location']}")
                
            if event_data.get('fatalities'):
                parts.append(f"Fatalities: {event_data['fatalities']}")
                
            return " | ".join(parts)
        except:
            return str(event_data)
    
    def _get_date_string(self, days_offset: int) -> str:
        """Get date string for ACLED API"""
        target_date = datetime.now() + timedelta(days=days_offset)
        return target_date.strftime("%Y-%m-%d")


# Singleton instance
acled_connector = ACLEDConnector()
