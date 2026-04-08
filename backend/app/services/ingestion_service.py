"""Data Ingestion Service — Fetch real data from 60+ free intelligence sources"""
import asyncio
import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional
import httpx
from loguru import logger


# ── Source Registry (metadata for dashboard) ──

SOURCE_REGISTRY: dict[str, dict] = {
    # ── GREEN: Structured APIs (no key required) ──
    "GDELT": {"tier": "green", "type": "api", "domain": "geopolitics", "url": "https://api.gdeltproject.org/api/v2/doc/doc"},
    "USGS": {"tier": "green", "type": "api", "domain": "climate", "url": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson"},
    "World Bank": {"tier": "green", "type": "api", "domain": "economics", "url": "https://api.worldbank.org/v2/country/IN/indicator/NY.GDP.MKTP.CD?format=json"},
    "NVD": {"tier": "green", "type": "api", "domain": "technology", "url": "https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=20"},
    "Hacker News": {"tier": "green", "type": "api", "domain": "technology", "url": "https://hacker-news.firebaseio.com/v0/topstories.json"},
    "WHO GHO": {"tier": "green", "type": "api", "domain": "society", "url": "https://ghoapi.azureedge.net/api/WHOSIS_000001?$filter=SpatialDim eq 'IND'"},
    "OpenAlex": {"tier": "green", "type": "api", "domain": "technology", "url": "https://api.openalex.org/works?filter=title.search:india+policy&sort=cited_by_count:desc"},
    "CrossRef": {"tier": "green", "type": "api", "domain": "technology", "url": "https://api.crossref.org/works?query=india+geopolitics&rows=20&sort=published&order=desc"},
    "IMF": {"tier": "green", "type": "api", "domain": "economics", "url": "https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH"},
    "UN Population": {"tier": "green", "type": "api", "domain": "society", "url": "https://population.un.org/dataportalapi/api/v1/indicators?limit=50"},
    "Open Meteo AQ": {"tier": "green", "type": "api", "domain": "climate", "url": "https://air-quality-api.open-meteo.com/v1/air-quality?latitude=28.61&longitude=77.20&current=pm10,pm2_5"},
    "Carbon Monitor": {"tier": "green", "type": "api", "domain": "climate", "url": "https://carbonmonitor.org/api/getCountryData?country=IND"},
    "REST Countries": {"tier": "green", "type": "api", "domain": "geopolitics", "url": "https://restcountries.com/v3.1/name/india"},
    "GDACS API": {"tier": "green", "type": "api", "domain": "climate", "url": "https://www.gdacs.org/gdacsapi/api/events/geteventlist/FEEDS?limit=50"},

    # ── YELLOW: RSS Feeds ──
    # India Government
    "PIB": {"tier": "yellow", "type": "rss", "domain": "geopolitics", "url": "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3"},
    "MEA": {"tier": "yellow", "type": "rss", "domain": "geopolitics", "url": "https://www.mea.gov.in/rss-feed.htm"},
    # Global News
    "BBC World": {"tier": "yellow", "type": "rss", "domain": "geopolitics", "url": "http://feeds.bbci.co.uk/news/world/rss.xml"},
    "Al Jazeera": {"tier": "yellow", "type": "rss", "domain": "geopolitics", "url": "https://www.aljazeera.com/xml/rss/all.xml"},
    "DW News": {"tier": "yellow", "type": "rss", "domain": "geopolitics", "url": "https://rss.dw.com/xml/rss-en-all"},
    "France24": {"tier": "yellow", "type": "rss", "domain": "geopolitics", "url": "https://www.france24.com/en/rss"},
    "TASS": {"tier": "yellow", "type": "rss", "domain": "geopolitics", "url": "https://tass.com/rss/v2.xml"},
    "UN News": {"tier": "yellow", "type": "rss", "domain": "geopolitics", "url": "https://news.un.org/feed/subscribe/en/news/all/rss.xml"},
    "Reuters Business": {"tier": "yellow", "type": "rss", "domain": "economics", "url": "http://feeds.reuters.com/reuters/businessNews"},
    "Bloomberg Tech": {"tier": "yellow", "type": "rss", "domain": "technology", "url": "https://www.bloomberg.com/technology/rss"},
    # India News
    "The Hindu": {"tier": "yellow", "type": "rss", "domain": "geopolitics", "url": "https://www.thehindu.com/feeder/default.rss"},
    "Hindustan Times": {"tier": "yellow", "type": "rss", "domain": "geopolitics", "url": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml"},
    "NDTV": {"tier": "yellow", "type": "rss", "domain": "geopolitics", "url": "https://feeds.feedburner.com/ndtvnews-india-news"},
    "Indian Express": {"tier": "yellow", "type": "rss", "domain": "geopolitics", "url": "https://indianexpress.com/feed/"},
    "Times of India": {"tier": "yellow", "type": "rss", "domain": "geopolitics", "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"},
    "Scroll": {"tier": "yellow", "type": "rss", "domain": "geopolitics", "url": "https://scroll.in/feed"},
    "The Wire": {"tier": "yellow", "type": "rss", "domain": "geopolitics", "url": "https://thewire.in/feed"},
    "ThePrint": {"tier": "yellow", "type": "rss", "domain": "geopolitics", "url": "https://theprint.in/feed/"},
    "LiveMint": {"tier": "yellow", "type": "rss", "domain": "economics", "url": "https://www.livemint.com/rss/news"},
    "Economic Times": {"tier": "yellow", "type": "rss", "domain": "economics", "url": "https://economictimes.indiatimes.com/rssfeedstopstories.cms"},
    "MoneyControl": {"tier": "yellow", "type": "rss", "domain": "economics", "url": "https://www.moneycontrol.com/rss/latestnews.xml"},
    # Social Media / Reddit
    "Reddit WorldNews": {"tier": "yellow", "type": "rss", "domain": "geopolitics", "url": "https://www.reddit.com/r/worldnews/.rss"},
    "Reddit Geopolitics": {"tier": "yellow", "type": "rss", "domain": "geopolitics", "url": "https://www.reddit.com/r/geopolitics/.rss"},
    "Reddit India": {"tier": "yellow", "type": "rss", "domain": "geopolitics", "url": "https://www.reddit.com/r/india/.rss"},
    "Reddit IndianStockMarket": {"tier": "yellow", "type": "rss", "domain": "economics", "url": "https://www.reddit.com/r/IndianStockMarket/.rss"},
    "Reddit Technology": {"tier": "yellow", "type": "rss", "domain": "technology", "url": "https://www.reddit.com/r/technology/.rss"},
    "Reddit CyberSecurity": {"tier": "yellow", "type": "rss", "domain": "defense", "url": "https://www.reddit.com/r/cybersecurity/.rss"},
    # Defense & Cyber
    "CISA": {"tier": "yellow", "type": "rss", "domain": "defense", "url": "https://www.cisa.gov/news.xml"},
    "Breaking Defense": {"tier": "yellow", "type": "rss", "domain": "defense", "url": "https://breakingdefense.com/feed/"},
    "Hacker News RSS": {"tier": "yellow", "type": "rss", "domain": "technology", "url": "https://feeds.feedburner.com/TheHackersNews"},
    "Krebs Security": {"tier": "yellow", "type": "rss", "domain": "defense", "url": "https://krebsonsecurity.com/feed/"},
    "War on the Rocks": {"tier": "yellow", "type": "rss", "domain": "defense", "url": "https://warontherocks.com/feed"},
    "Bellingcat": {"tier": "yellow", "type": "rss", "domain": "defense", "url": "https://www.bellingcat.com/feed/"},
    "SANS ISC": {"tier": "yellow", "type": "rss", "domain": "defense", "url": "https://isc.sans.edu/rssfeed.xml"},
    # Climate
    "GDACS RSS": {"tier": "yellow", "type": "rss", "domain": "climate", "url": "https://www.gdacs.org/xml/rss.xml"},
    "UNFCCC": {"tier": "yellow", "type": "rss", "domain": "climate", "url": "https://unfccc.int/news/feed"},
    "Carbon Brief": {"tier": "yellow", "type": "rss", "domain": "climate", "url": "https://www.carbonbrief.org/feed"},
    "Down to Earth": {"tier": "yellow", "type": "rss", "domain": "climate", "url": "https://www.downtoearth.org.in/feed"},
    "Mongabay India": {"tier": "yellow", "type": "rss", "domain": "climate", "url": "https://india.mongabay.com/feed/"},
    "Third Pole": {"tier": "yellow", "type": "rss", "domain": "climate", "url": "https://www.thethirdpole.net/en/feed/"},
    "ReliefWeb": {"tier": "yellow", "type": "rss", "domain": "climate", "url": "https://reliefweb.int/updates/rss.xml"},
    # Technology
    "HN Frontpage": {"tier": "yellow", "type": "rss", "domain": "technology", "url": "https://hnrss.org/frontpage"},
    "MIT Tech Review": {"tier": "yellow", "type": "rss", "domain": "technology", "url": "https://www.technologyreview.com/feed/"},
    "Wired": {"tier": "yellow", "type": "rss", "domain": "technology", "url": "https://www.wired.com/feed/rss"},
    "TechCrunch": {"tier": "yellow", "type": "rss", "domain": "technology", "url": "https://techcrunch.com/feed/"},
    "Google AI Blog": {"tier": "yellow", "type": "rss", "domain": "technology", "url": "https://blog.google/technology/ai/rss/"},
    "HuggingFace": {"tier": "yellow", "type": "rss", "domain": "technology", "url": "https://huggingface.co/blog/feed.xml"},
    "arXiv AI": {"tier": "yellow", "type": "rss", "domain": "technology", "url": "http://export.arxiv.org/rss/cs.AI"},
    "YourStory": {"tier": "yellow", "type": "rss", "domain": "technology", "url": "https://yourstory.com/feed"},
    "Inc42": {"tier": "yellow", "type": "rss", "domain": "technology", "url": "https://inc42.com/feed/"},
    # Economics
    "IMF Blog": {"tier": "yellow", "type": "rss", "domain": "economics", "url": "https://www.imf.org/en/News/RSS?Language=ENG"},
    "WEF Agenda": {"tier": "yellow", "type": "rss", "domain": "economics", "url": "https://www.weforum.org/feed"},
    "ADB News": {"tier": "yellow", "type": "rss", "domain": "economics", "url": "https://www.adb.org/news/feed"},
    "Hindu BL": {"tier": "yellow", "type": "rss", "domain": "economics", "url": "https://www.thehindubusinessline.com/feeder/default.rss"},
    "Financial Express": {"tier": "yellow", "type": "rss", "domain": "economics", "url": "https://www.financialexpress.com/feed/"},
    "Yahoo Finance": {"tier": "yellow", "type": "rss", "domain": "economics", "url": "https://finance.yahoo.com/news/rssindex"},

    # ── RED: Scraping targets (handled by scraping_service) ──
    "RBI": {"tier": "red", "type": "scraper", "domain": "economics", "url": "https://rbi.org.in"},
    "MOSPI": {"tier": "red", "type": "scraper", "domain": "economics", "url": "https://mospi.gov.in"},
    "SEBI": {"tier": "red", "type": "scraper", "domain": "economics", "url": "https://www.sebi.gov.in"},
    "NITI Aayog": {"tier": "red", "type": "scraper", "domain": "geopolitics", "url": "https://www.niti.gov.in"},
    "ORF": {"tier": "red", "type": "scraper", "domain": "geopolitics", "url": "https://www.orfonline.org/research/"},
    "India Budget": {"tier": "red", "type": "scraper", "domain": "economics", "url": "https://www.indiabudget.gov.in"},
}


# Domain classification by source name
SOURCE_DOMAIN_MAP = {name: meta["domain"] for name, meta in SOURCE_REGISTRY.items()}


def classify_domain(source: str, title: str = "", summary: str = "") -> str:
    """Classify domain based on source and content keywords"""
    domain = SOURCE_DOMAIN_MAP.get(source, "geopolitics")

    text = (title + " " + summary).lower()
    defense_keywords = ["military", "army", "navy", "missile", "defense", "defence", "weapon", "troop", "war", "combat", "nuclear", "submarine"]
    econ_keywords = ["gdp", "inflation", "trade", "economy", "market", "bank", "fiscal", "export", "import", "tariff", "stock"]
    tech_keywords = ["cyber", "hack", "software", "ai ", "artificial intelligence", "satellite", "chip", "semiconductor", "quantum"]
    climate_keywords = ["earthquake", "cyclone", "flood", "climate", "emission", "disaster", "tsunami", "drought", "wildfire"]
    society_keywords = ["election", "protest", "refugee", "human rights", "education", "health", "pandemic", "population"]

    for kw in defense_keywords:
        if kw in text:
            return "defense"
    for kw in econ_keywords:
        if kw in text:
            return "economics"
    for kw in tech_keywords:
        if kw in text:
            return "technology"
    for kw in climate_keywords:
        if kw in text:
            return "climate"
    for kw in society_keywords:
        if kw in text:
            return "society"

    return domain


def score_importance(title: str, summary: str = "") -> int:
    """Basic importance scoring 1-10"""
    text = (title + " " + summary).lower()
    score = 5

    critical = ["war", "nuclear", "invasion", "attack", "crisis", "emergency", "killed", "explosion"]
    high = ["military", "missile", "sanctions", "summit", "alliance", "hack", "earthquake", "tsunami"]
    medium = ["agreement", "talks", "election", "protest", "trade", "deal", "launch"]

    for kw in critical:
        if kw in text:
            score = max(score, 9)
    for kw in high:
        if kw in text:
            score = max(score, 7)
    for kw in medium:
        if kw in text:
            score = max(score, 6)

    india_keywords = ["india", "indian", "modi", "delhi", "mumbai", "isro", "drdo"]
    for kw in india_keywords:
        if kw in text:
            score = min(score + 1, 10)
            break

    return score


def dedup_key(title: str, source: str) -> str:
    """Generate dedup key for an event"""
    return hashlib.md5(f"{title.strip().lower()}:{source}".encode()).hexdigest()


class IngestionService:
    """Service to fetch real data from 60+ free intelligence sources"""

    def __init__(self):
        self.http_client = httpx.AsyncClient(
            timeout=20.0, 
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Upgrade-Insecure-Requests": "1"
            }
        )
        self.seen_keys: set = set()
        self.connector_status: dict = {}
        self.last_run: Optional[datetime] = None

    async def close(self):
        await self.http_client.aclose()

    def get_source_registry(self) -> dict:
        """Return the full source registry for dashboard"""
        return SOURCE_REGISTRY

    # ── RSS Feed Parser ──
    async def fetch_rss(self, url: str, source_name: str) -> list[dict]:
        """Fetch and parse an RSS/Atom feed with robust XML handling"""
        items = []
        try:
            resp = await self.http_client.get(url)
            resp.raise_for_status()

            content = resp.text

            # Try to parse raw XML first (most feeds are well-formed)
            root = None
            try:
                root = ET.fromstring(content)
            except ET.ParseError:
                # Clean common issues: double-escaped ampersands, naked ampersands
                cleaned = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#)', '&amp;', content)
                try:
                    root = ET.fromstring(cleaned)
                except ET.ParseError as xml_error:
                    logger.debug(f"XML parse failed for {source_name}: {xml_error}")
                    self.connector_status[source_name] = {"status": "error", "error": f"XML parse: {xml_error}", "last_fetch": datetime.utcnow().isoformat()}
                    return []

            if root is None:
                return []

            # ── Phase 1: RSS 2.0 items (<item> tags) ──
            for item in root.iter("item"):
                title = (item.findtext("title") or "").strip()
                summary = (item.findtext("description") or "").strip()
                link = (item.findtext("link") or "").strip()
                pub_date = item.findtext("pubDate") or item.findtext("dc:date") or ""

                if not title:
                    continue

                key = dedup_key(title, source_name)
                if key in self.seen_keys:
                    continue
                self.seen_keys.add(key)

                summary = re.sub(r'<[^>]+>', '', summary)[:500]
                published_at = self._parse_date(pub_date)
                domain = classify_domain(source_name, title, summary)
                importance = score_importance(title, summary)

                items.append({
                    "title": title,
                    "summary": summary or title,
                    "domain": domain,
                    "source": source_name,
                    "source_url": link,
                    "published_at": published_at,
                    "importance": importance,
                    "sentiment": 0.0,
                    "entities": [],
                })

            # ── Phase 2: Atom feeds (try multiple namespace patterns) ──
            atom_ns_list = [
                {"atom": "http://www.w3.org/2005/Atom"},
                {},  # default namespace fallback
            ]

            for ns in atom_ns_list:
                prefix = "atom:" if "atom" in ns else ""
                entries = root.findall(f".//{prefix}entry", ns) if ns else []
                # Also try without namespace for feeds that use default ns
                if not entries:
                    entries = root.findall(".//entry")
                if not entries:
                    # Try finding entries with full namespace in tag
                    entries = [el for el in root.iter() if el.tag.endswith('}entry') or el.tag == 'entry']

                for entry in entries:
                    # Extract title - try namespace-aware first, then bare
                    title = ""
                    for tag in [f"{prefix}title", "title"]:
                        title = (entry.findtext(tag, namespaces=ns if ns else None) or "").strip()
                        if title:
                            break
                    # Try child elements directly
                    if not title:
                        for child in entry:
                            if child.tag.endswith('}title') or child.tag == 'title':
                                title = (child.text or "").strip()
                                break

                    if not title:
                        continue

                    key = dedup_key(title, source_name)
                    if key in self.seen_keys:
                        continue
                    self.seen_keys.add(key)

                    # Extract summary/content
                    summary = ""
                    for tag in [f"{prefix}summary", f"{prefix}content", "summary", "content"]:
                        summary = (entry.findtext(tag, namespaces=ns if ns else None) or "").strip()
                        if summary:
                            break
                    if not summary:
                        for child in entry:
                            if child.tag.endswith('}summary') or child.tag.endswith('}content') or child.tag in ('summary', 'content'):
                                summary = (child.text or "").strip()
                                break

                    # Extract link
                    link = ""
                    link_el = entry.find(f"{prefix}link", ns) if ns else entry.find("link")
                    if link_el is None:
                        for child in entry:
                            if child.tag.endswith('}link') or child.tag == 'link':
                                link_el = child
                                break
                    if link_el is not None:
                        link = link_el.get("href", "") or (link_el.text or "").strip()

                    # Extract date
                    updated = ""
                    for tag in [f"{prefix}updated", f"{prefix}published", "updated", "published"]:
                        updated = (entry.findtext(tag, namespaces=ns if ns else None) or "").strip()
                        if updated:
                            break
                    if not updated:
                        for child in entry:
                            if child.tag.endswith('}updated') or child.tag.endswith('}published') or child.tag in ('updated', 'published'):
                                updated = (child.text or "").strip()
                                break

                    summary = re.sub(r'<[^>]+>', '', summary)[:500]
                    published_at = self._parse_date(updated)
                    domain = classify_domain(source_name, title, summary)
                    importance = score_importance(title, summary)

                    items.append({
                        "title": title,
                        "summary": summary or title,
                        "domain": domain,
                        "source": source_name,
                        "source_url": link,
                        "published_at": published_at,
                        "importance": importance,
                        "sentiment": 0.0,
                        "entities": [],
                    })

                if items:  # Found entries with this namespace, stop
                    break

            self.connector_status[source_name] = {"status": "ok", "count": len(items), "last_fetch": datetime.utcnow().isoformat()}
        except httpx.HTTPStatusError as e:
            logger.warning(f"RSS HTTP error for {source_name}: {e.response.status_code}")
            self.connector_status[source_name] = {"status": "error", "error": f"HTTP {e.response.status_code}", "last_fetch": datetime.utcnow().isoformat()}
        except Exception as e:
            logger.warning(f"RSS fetch failed for {source_name}: {e}")
            self.connector_status[source_name] = {"status": "error", "error": str(e)[:200], "last_fetch": datetime.utcnow().isoformat()}

        return items

    # ── JSON API Fetcher ──
    async def fetch_json_api(self, url: str, source_name: str, parser_fn=None) -> list[dict]:
        """Fetch from JSON API endpoint"""
        items = []
        try:
            resp = await self.http_client.get(url)
            resp.raise_for_status()
            data = resp.json()

            if parser_fn:
                items = parser_fn(data, source_name)

            # Dedup
            deduped = []
            for item in items:
                key = dedup_key(item["title"], item["source"])
                if key not in self.seen_keys:
                    self.seen_keys.add(key)
                    deduped.append(item)
            items = deduped

            self.connector_status[source_name] = {"status": "ok", "count": len(items), "last_fetch": datetime.utcnow().isoformat()}
        except Exception as e:
            logger.warning(f"API fetch failed for {source_name}: {e}")
            self.connector_status[source_name] = {"status": "error", "error": str(e), "last_fetch": datetime.utcnow().isoformat()}

        return items

    # ── GDELT Connector ──
    async def fetch_gdelt(self) -> list[dict]:
        """Fetch from GDELT Doc Search API"""
        items = []
        try:
            url = "https://api.gdeltproject.org/api/v2/doc/doc?query=india OR china OR pakistan OR defense OR military&mode=artlist&maxrecords=30&format=json&sort=datedesc"
            resp = await self.http_client.get(url)
            resp.raise_for_status()
            data = resp.json()

            for article in data.get("articles", [])[:30]:
                title = article.get("title", "").strip()
                if not title:
                    continue

                key = dedup_key(title, "GDELT")
                if key in self.seen_keys:
                    continue
                self.seen_keys.add(key)

                domain = classify_domain("GDELT", title)
                importance = score_importance(title)

                items.append({
                    "title": title,
                    "summary": title,
                    "domain": domain,
                    "source": "GDELT",
                    "source_url": article.get("url", ""),
                    "published_at": self._parse_date(article.get("seendate", "")),
                    "importance": importance,
                    "sentiment": float(article.get("tone", 0)) / 10.0,
                    "entities": [],
                })

            self.connector_status["GDELT"] = {"status": "ok", "count": len(items), "last_fetch": datetime.utcnow().isoformat()}
        except Exception as e:
            logger.warning(f"GDELT fetch failed: {e}")
            self.connector_status["GDELT"] = {"status": "error", "error": str(e), "last_fetch": datetime.utcnow().isoformat()}

        return items

    # ── Source Definitions ──
    def get_rss_sources(self) -> list[tuple[str, str]]:
        """Return (url, source_name) pairs for all RSS feeds"""
        return [
            (meta["url"], name)
            for name, meta in SOURCE_REGISTRY.items()
            if meta["type"] == "rss"
        ]

    def _get_api_sources(self) -> list[tuple[str, str, callable]]:
        """Return (url, source_name, parser_fn) for structured APIs"""
        return [
            ("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson", "USGS", self._parse_usgs),
            ("https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=10", "NVD", self._parse_nvd),
            ("https://api.worldbank.org/v2/country/IND/indicator/NY.GDP.MKTP.CD?format=json&per_page=5", "World Bank", self._parse_worldbank),
            ("https://ghoapi.azureedge.net/api/WHOSIS_000001?$filter=SpatialDim eq 'IND'", "WHO GHO", self._parse_who_gho),
            ("https://api.openalex.org/works?filter=title.search:india+policy&sort=cited_by_count:desc&per_page=20", "OpenAlex", self._parse_openalex),
            ("https://api.crossref.org/works?query=india+geopolitics&rows=15&sort=published&order=desc", "CrossRef", self._parse_crossref),
            ("https://air-quality-api.open-meteo.com/v1/air-quality?latitude=28.61&longitude=77.20&current=pm10,pm2_5", "Open Meteo AQ", self._parse_open_meteo_aq),
        ]

    # ── Specialized Parsers ──

    def _parse_usgs(self, data: dict, source_name: str) -> list[dict]:
        """Parse USGS earthquake GeoJSON"""
        items = []
        for feature in data.get("features", [])[:20]:
            props = feature.get("properties", {})
            title = props.get("title", "Earthquake")
            mag = props.get("mag", 0)
            place = props.get("place", "Unknown")
            ts = props.get("time", 0)

            items.append({
                "title": f"Earthquake M{mag}: {place}",
                "summary": title,
                "domain": "climate",
                "source": source_name,
                "source_url": props.get("url", ""),
                "published_at": datetime.utcfromtimestamp(ts / 1000) if ts else datetime.utcnow(),
                "importance": min(int(mag) + 2, 10) if mag else 5,
                "sentiment": -0.5,
                "entities": [],
            })
        return items

    def _parse_hackernews(self, data: list, source_name: str) -> list[dict]:
        """Parse Hacker News top stories"""
        items = []
        for story in data[:20]:
            if isinstance(story, dict):
                title = story.get("title", "")
                if title:
                    items.append({
                        "title": title,
                        "summary": title,
                        "domain": "technology",
                        "source": source_name,
                        "source_url": story.get("url", f"https://news.ycombinator.com/item?id={story.get('id', '')}"),
                        "published_at": datetime.utcfromtimestamp(story.get("time", 0)) if story.get("time") else datetime.utcnow(),
                        "importance": min(5 + story.get("score", 0) // 100, 8),
                        "sentiment": 0.0,
                        "entities": [],
                    })
        return items

    def _parse_nvd(self, data: dict, source_name: str) -> list[dict]:
        """Parse NVD CVE feed"""
        items = []
        for vuln in data.get("vulnerabilities", [])[:20]:
            cve = vuln.get("cve", {})
            cve_id = cve.get("id", "")
            descriptions = cve.get("descriptions", [])
            desc = ""
            for d in descriptions:
                if d.get("lang") == "en":
                    desc = d.get("value", "")
                    break

            if cve_id:
                metrics = cve.get("metrics", {})
                cvss_data = metrics.get("cvssMetricV31", [{}])
                score = cvss_data[0].get("cvssData", {}).get("baseScore", 5.0) if cvss_data else 5.0

                items.append({
                    "title": f"CVE: {cve_id}",
                    "summary": desc[:500],
                    "domain": "technology",
                    "source": source_name,
                    "source_url": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
                    "published_at": datetime.utcnow(),
                    "importance": min(int(score), 10),
                    "sentiment": -0.6,
                    "entities": [],
                })
        return items

    def _parse_worldbank(self, data: list, source_name: str) -> list[dict]:
        """Parse World Bank API response"""
        items = []
        if len(data) >= 2 and isinstance(data[1], list):
            for indicator in data[1][:20]:
                country = indicator.get("country", {}).get("value", "")
                indicator_name = indicator.get("indicator", {}).get("value", "")
                value = indicator.get("value")
                year = indicator.get("date", "")

                if value is not None and country:
                    items.append({
                        "title": f"{country}: {indicator_name} ({year})",
                        "summary": f"{indicator_name} for {country} in {year}: {value}",
                        "domain": "economics",
                        "source": source_name,
                        "source_url": "https://data.worldbank.org",
                        "published_at": datetime.utcnow(),
                        "importance": 5,
                        "sentiment": 0.0,
                        "entities": [country],
                    })
        return items

    def _parse_who_gho(self, data: dict, source_name: str) -> list[dict]:
        """Parse WHO Global Health Observatory API"""
        items = []
        for record in data.get("value", [])[:20]:
            indicator = record.get("IndicatorCode", "")
            dim = record.get("SpatialDim", "")
            year = record.get("TimeDim", "")
            value = record.get("NumericValue")

            if value is not None:
                items.append({
                    "title": f"WHO: {indicator} for {dim} ({year})",
                    "summary": f"Health indicator {indicator} in {dim}: {value} ({year})",
                    "domain": "society",
                    "source": source_name,
                    "source_url": "https://www.who.int/data/gho",
                    "published_at": datetime.utcnow(),
                    "importance": 5,
                    "sentiment": 0.0,
                    "entities": [dim] if dim else [],
                })
        return items

    def _parse_openalex(self, data: dict, source_name: str) -> list[dict]:
        """Parse OpenAlex research works"""
        items = []
        for work in data.get("results", [])[:20]:
            title = work.get("display_name", "") or work.get("title", "")
            if not title:
                continue

            pub_date = work.get("publication_date", "")
            cited = work.get("cited_by_count", 0)
            doi = work.get("doi", "")

            items.append({
                "title": title,
                "summary": f"Research paper. Citations: {cited}. Published: {pub_date}",
                "domain": "technology",
                "source": source_name,
                "source_url": doi or work.get("id", ""),
                "published_at": self._parse_date(pub_date) if pub_date else datetime.utcnow(),
                "importance": min(5 + cited // 50, 8),
                "sentiment": 0.0,
                "entities": [],
            })
        return items

    def _parse_crossref(self, data: dict, source_name: str) -> list[dict]:
        """Parse CrossRef papers"""
        items = []
        for work in data.get("message", {}).get("items", [])[:15]:
            title_parts = work.get("title", [])
            title = title_parts[0] if title_parts else ""
            if not title:
                continue

            doi = work.get("DOI", "")
            published = work.get("published-print", work.get("published-online", {}))
            date_parts = published.get("date-parts", [[]])
            year = date_parts[0][0] if date_parts and date_parts[0] else ""

            items.append({
                "title": title,
                "summary": f"Academic paper (CrossRef). Year: {year}. DOI: {doi}",
                "domain": "technology",
                "source": source_name,
                "source_url": f"https://doi.org/{doi}" if doi else "",
                "published_at": datetime.utcnow(),
                "importance": 5,
                "sentiment": 0.0,
                "entities": [],
            })
        return items

    def _parse_open_meteo_aq(self, data: dict, source_name: str) -> list[dict]:
        """Parse Open-Meteo current air quality measurements"""
        items = []
        current = data.get("current", {})
        time_str = current.get("time", "")
        pm10 = current.get("pm10")
        pm2_5 = current.get("pm2_5")

        if pm10 is not None or pm2_5 is not None:
            # Taking the worse of the two for overall rating representation
            value = max(pm10 or 0, pm2_5 or 0)
            level = "Hazardous" if value > 150 else "Unhealthy" if value > 55 else "Moderate" if value > 25 else "Good"
            importance = 8 if value > 150 else 6 if value > 55 else 5

            msg = []
            if pm10 is not None: msg.append(f"PM10: {pm10} μg/m³")
            if pm2_5 is not None: msg.append(f"PM2.5: {pm2_5} μg/m³")
            summary_desc = " | ".join(msg)

            items.append({
                "title": f"Air Quality (Delhi): {level}",
                "summary": f"Current Air Quality in New Delhi: {summary_desc} ({level})",
                "domain": "climate",
                "source": source_name,
                "source_url": "https://open-meteo.com/en/docs/air-quality-api",
                "published_at": self._parse_date(time_str) if time_str else datetime.utcnow(),
                "importance": importance,
                "sentiment": -0.3 if value > 55 else 0.0,
                "entities": ["Delhi"],
            })
        return items

    # ── Single Source Fetch ──
    async def fetch_single_source(self, source_name: str) -> Optional[list[dict]]:
        """Fetch data from a single named source. Returns None if not found."""
        meta = SOURCE_REGISTRY.get(source_name)
        if not meta:
            return None

        if meta["type"] == "rss":
            return await self.fetch_rss(meta["url"], source_name)

        if meta["type"] == "scraper":
            # Delegate to scraping service
            try:
                from app.services.scraping_service import scraping_service
                scraper_map = {
                    "RBI": scraping_service.scrape_rbi,
                    "MOSPI": scraping_service.scrape_mospi,
                    "SEBI": scraping_service.scrape_sebi,
                    "NITI Aayog": scraping_service.scrape_niti_aayog,
                    "ORF": scraping_service.scrape_orf,
                    "India Budget": scraping_service.scrape_india_budget,
                }
                fn = scraper_map.get(source_name)
                if fn:
                    return await fn()
            except ImportError:
                logger.warning("Scraping service not available")
            return []

        # API source
        if source_name == "GDELT":
            return await self.fetch_gdelt()

        if source_name == "Hacker News":
            return await self._fetch_hackernews()

        # Check structured API list
        for url, name, parser in self._get_api_sources():
            if name == source_name:
                return await self.fetch_json_api(url, name, parser)

        return []

    async def _fetch_hackernews(self) -> list[dict]:
        """Fetch Hacker News top stories"""
        try:
            resp = await self.http_client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
            top_ids = resp.json()[:15]
            stories = []
            for sid in top_ids:
                try:
                    story_resp = await self.http_client.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
                    stories.append(story_resp.json())
                except Exception:
                    pass
            items = self._parse_hackernews(stories, "Hacker News")
            self.connector_status["Hacker News"] = {"status": "ok", "count": len(items), "last_fetch": datetime.utcnow().isoformat()}
            return items
        except Exception as e:
            logger.warning(f"HN fetch failed: {e}")
            self.connector_status["Hacker News"] = {"status": "error", "error": str(e)}
            return []

    # ── Main Ingestion Pipeline ──
    async def run_full_ingestion(self) -> dict:
        """Run all connectors and return ingested items"""
        logger.info("Starting full data ingestion (60+ sources)...")
        all_items = []

        # Phase 1: RSS Feeds in batches of 10 with 1s delay
        rss_sources = self.get_rss_sources()
        batch_size = 10
        for i in range(0, len(rss_sources), batch_size):
            batch = rss_sources[i:i + batch_size]
            tasks = [self.fetch_rss(url, name) for url, name in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, list):
                    all_items.extend(result)
            if i + batch_size < len(rss_sources):
                await asyncio.sleep(1)

        logger.info(f"RSS phase complete: {len(all_items)} items from {len(rss_sources)} feeds")

        # Phase 2: Structured APIs sequentially with 0.5s delays
        for url, name, parser in self._get_api_sources():
            try:
                items = await self.fetch_json_api(url, name, parser)
                all_items.extend(items)
            except Exception as e:
                logger.warning(f"API {name} failed: {e}")
            await asyncio.sleep(0.5)

        # Phase 3: GDELT
        gdelt_items = await self.fetch_gdelt()
        all_items.extend(gdelt_items)

        # Phase 4: Hacker News
        hn_items = await self._fetch_hackernews()
        all_items.extend(hn_items)

        self.last_run = datetime.utcnow()
        logger.info(f"Ingestion complete: {len(all_items)} items from {len(self.connector_status)} sources")

        return {
            "total_items": len(all_items),
            "items": all_items,
            "connector_status": self.connector_status,
            "timestamp": self.last_run.isoformat(),
        }

    async def save_to_db(self, items: list[dict], session) -> int:
        """Save ingested items to database efficiently"""
        from app.database import Event
        from sqlalchemy import select

        if not items:
            return 0

        # Extract all unique titles from the incoming items
        item_titles = {item.get("title") for item in items if item.get("title")}

        if not item_titles:
            return 0

        # Batch query database ONCE for existing events
        existing_result = await session.scalars(
            select(Event.title).where(Event.title.in_(item_titles))
        )
        existing_titles = set(existing_result.all())

        saved = 0
        for item in items:
            title = item.get("title", "")
            if not title or title in existing_titles:
                continue

            event = Event(
                title=title[:500],
                summary=(item.get("summary") or "")[:2000],
                domain=item.get("domain", "geopolitics"),
                source=item.get("source", "Unknown"),
                source_url=item.get("source_url"),
                published_at=item.get("published_at") or datetime.utcnow(),
                importance=item.get("importance", 5),
                sentiment=item.get("sentiment", 0.0),
                entities=item.get("entities", []),
                is_new=True,
            )
            session.add(event)
            existing_titles.add(title)  # Prevent dupes within same batch
            saved += 1

        if saved > 0:
            await session.commit()
        logger.info(f"Saved {saved} new events to database")
        return saved

    def get_status(self) -> dict:
        """Get ingestion status for all connectors"""
        return {
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "connectors": self.connector_status,
            "total_connectors": len(SOURCE_REGISTRY),
        }

    # ── Helpers ──
    def _parse_date(self, date_str: str) -> datetime:
        """Try multiple date formats"""
        if not date_str:
            return datetime.utcnow()

        formats = [
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y%m%dT%H%M%SZ",
            "%Y%m%d%H%M%S",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.replace(tzinfo=None) if dt.tzinfo else dt
            except (ValueError, TypeError):
                continue

        return datetime.utcnow()


# Singleton
ingestion_service = IngestionService()
