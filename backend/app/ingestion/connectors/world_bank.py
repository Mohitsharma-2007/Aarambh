"""World Bank API connector for economic data"""
import aiohttp
import json
from datetime import datetime
from ..base_connector import BaseConnector, RawEvent
from app.config import settings


class WorldBankConnector(BaseConnector):
    """World Bank API connector for economic indicators"""
    
    def __init__(self):
        super().__init__()
        self.source_id = "world_bank_economics"
        self.domain = "economics"
        self.update_interval = 3600  # 1 hour
        self.rate_limit = 60
        self.seed_type = "financial_signal"
        
    async def fetch(self) -> list[RawEvent]:
        """Fetch World Bank economic indicators for India"""
        try:
            # Key economic indicators for India
            indicators = [
                "NY.GDP.MKTP.CD",  # GDP (current US$)
                "FP.CPI.TOTL.ZG",  # Inflation, consumer prices (annual %)
                "FR.INR.RINL",  # Interest rate, real (%)
                "BN.GSR.GNFS.CD",  # Gross capital formation (% of GDP)
                "NE.EXP.GNFS.CD",  # Exports of goods and services (% of GDP)
                "NE.IMP.GNFS.CD",  # Imports of goods and services (% of GDP)
            ]
            
            events = []
            
            async with aiohttp.ClientSession() as session:
                for indicator in indicators:
                    try:
                        url = f"{settings.WORLD_BANK_API}/country/IND/indicator/{indicator}?format=json&date=2023:2024&per_page=1"
                        async with session.get(url, timeout=30) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                if data and len(data) > 1:
                                    indicator_data = data[1]  # Get latest data
                                    
                                    for entry in indicator_data:
                                        if entry.get('value') is not None:
                                            event = RawEvent(
                                                source=self.source_id,
                                                domain=self.domain,
                                                title=f"India Economic Update: {entry.get('indicator', {}).get('value', '')}",
                                                text=f"{entry.get('indicator', {}).get('value', '')}: {entry.get('value', '')} for {entry.get('date', '')}",
                                                url=f"https://data.worldbank.org/indicator/{indicator}",
                                                published_at=entry.get('date', datetime.now().isoformat()),
                                                language='en',
                                                raw_data={'world_bank_data': entry},
                                                seed_type=self.seed_type,
                                                importance=self._calculate_economic_importance(indicator, entry.get('value'))
                                            )
                                            events.append(event)
                    except Exception as e:
                        print(f"World Bank indicator {indicator} error: {e}")
                        continue
                        
            return events[:10]  # Limit to 10 events
            
        except Exception as e:
            print(f"World Bank fetch error: {e}")
            return []
    
    def _calculate_economic_importance(self, indicator: str, value: float) -> int:
        """Calculate importance based on economic indicator type and value"""
        try:
            base_importance = 5
            
            # Higher importance for key indicators
            if 'GDP' in indicator:
                base_importance += 3
            elif 'CPI' in indicator or 'inflation' in indicator.lower():
                base_importance += 3
            elif 'interest' in indicator.lower():
                base_importance += 2
                
            # Adjust based on significant changes
            if value and abs(value) > 5:  # Significant change
                base_importance += 2
                
            return min(base_importance, 10)
        except:
            return 5


# Singleton instance
world_bank_connector = WorldBankConnector()
