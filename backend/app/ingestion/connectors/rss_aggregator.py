"""RSS Aggregator connector for multiple international news sources"""
import aiohttp
from ..base_connector import BaseConnector, RawEvent


class RSSAggregatorConnector(BaseConnector):
    """Aggregated RSS connector for diverse international news sources"""

    FEEDS = [
        # Defense & Military
        ("https://www.defensenews.com/arc/outboundfeeds/rss/", "defense_event", "defense"),
        ("https://www.janes.com/feeds/news", "defense_event", "defense"),

        # Asia-Pacific
        ("https://www.scmp.com/rss/91/feed", "geopolitical_event", "geopolitics"),
        ("https://thediplomat.com/feed/", "diplomatic_signal", "geopolitics"),
        ("https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml", "geopolitical_event", "geopolitics"),

        # India-specific
        ("https://www.thehindu.com/news/international/feeder/default.rss", "geopolitical_event", "geopolitics"),
        ("https://economictimes.indiatimes.com/rssfeedstopstories.cms", "economic_signal", "economy"),
        ("https://www.livemint.com/rss/news", "economic_signal", "economy"),

        # Europe / Transatlantic
        ("https://www.euronews.com/rss", "geopolitical_event", "geopolitics"),
        ("https://www.dw.com/rss/en/top-stories/rss-en-all", "geopolitical_event", "geopolitics"),

        # Think tanks & Research
        ("https://feeds.feedburner.com/ForeignPolicy", "analytical_event", "geopolitics"),
        ("https://www.brookings.edu/feed/", "analytical_event", "geopolitics"),

        # Climate & Environment
        ("https://climate.nasa.gov/rss/news", "climate_event", "climate"),

        # Technology & Cyber
        ("https://feeds.feedburner.com/TheHackersNews", "cyber_event", "cybersecurity"),
        ("https://www.darkreading.com/rss.xml", "cyber_event", "cybersecurity"),
    ]

    def __init__(self):
        super().__init__()
        self.source_id = "rss_aggregator"
        self.domain = "geopolitics"
        self.update_interval = 900  # 15 minutes
        self.rate_limit = 60
        self.seed_type = "breaking_event"

    async def fetch(self) -> list[RawEvent]:
        """Fetch from all aggregated RSS feeds"""
        all_events = []
        try:
            async with aiohttp.ClientSession() as session:
                for feed_url, seed_type, domain in self.FEEDS:
                    try:
                        async with session.get(
                            feed_url,
                            timeout=aiohttp.ClientTimeout(total=10),
                            headers={'User-Agent': 'AARAMBH-OSINT/2.0'}
                        ) as response:
                            if response.status == 200:
                                content = await response.text()
                                events = self.parse_rss(content)
                                for ev in events:
                                    ev.seed_type = seed_type
                                    ev.domain = domain
                                all_events.extend(events)
                    except Exception:
                        # Silently skip failed feeds — some may be unavailable
                        pass
        except Exception as e:
            print(f"RSS Aggregator fetch error: {e}")
        return all_events


rss_aggregator_connector = RSSAggregatorConnector()
