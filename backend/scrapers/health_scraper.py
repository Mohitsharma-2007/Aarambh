"""
scrapers/health_scraper.py  —  Health Data + News Filtering
============================================================
Sources: WHO, CDC, NIH, Medscape, HealthNews + mainstream health feeds
Filtering: keyword-based, sub-category routing, severity scoring
"""

import asyncio, xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from utils.session import fetch_rss, fetch_json, fetch
from utils.cache   import get as c_get, set as c_set
from utils.text_filter import (
    keyword_filter, deduplicate, health_subcategory, sentiment_score
)

# ── Health RSS sources ────────────────────────────────────────────────────────
HEALTH_FEEDS = {
    "who":        {"url": "https://www.who.int/feeds/entity/mediacentre/news/en/rss.xml",    "name": "WHO"},
    "cdc":        {"url": "https://tools.cdc.gov/podcasts/feed.asp?feedid=183",              "name": "CDC"},
    "nih":        {"url": "https://www.nih.gov/news-events/news-releases/feed.xml",          "name": "NIH"},
    "medscape":   {"url": "https://www.medscape.com/cx/rssfeeds/2836.xml",                  "name": "Medscape"},
    "health_day": {"url": "https://consumer.healthday.com/feed/",                           "name": "HealthDay"},
    "webmd":      {"url": "https://rss.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC",        "name": "WebMD"},
    "science_daily_health": {"url": "https://www.sciencedaily.com/rss/health_medicine.xml", "name": "ScienceDaily Health"},
    "bbc_health": {"url": "https://feeds.bbci.co.uk/news/health/rss.xml",                   "name": "BBC Health"},
    "reuters_health": {"url": "https://feeds.reuters.com/reuters/healthNews",               "name": "Reuters Health"},
    "nytimes_health": {"url": "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",    "name": "NYT Health"},
}

# ── Severity keywords ─────────────────────────────────────────────────────────
SEVERITY = {
    "critical":  ["pandemic", "outbreak", "emergency", "epidemic", "alert", "warning",
                  "death toll", "fatality", "fatalities", "mass casualty"],
    "high":      ["outbreak", "spread", "infection surge", "vaccine shortage", "hospital overload",
                  "drug recall", "side effect warning", "clinical failure"],
    "medium":    ["study shows", "research finds", "new treatment", "approval", "trial results",
                  "risk factor", "health advisory"],
    "low":       ["tips", "advice", "lifestyle", "diet", "exercise", "wellness", "prevention"],
}

def _severity(title: str, desc: str) -> str:
    text = (title + " " + desc).lower()
    for level, keywords in SEVERITY.items():
        if any(kw in text for kw in keywords):
            return level
    return "low"


def _parse_health_rss(xml_text: str, source_name: str) -> list:
    arts = []
    try:
        root = ET.fromstring(xml_text)
        ch   = root.find("channel")
        items = ch.findall("item") if ch else root.findall(".//item")
        for item in items:
            def _t(tag):
                el = item.find(tag)
                return (el.text or "").strip() if el is not None else ""
            title = _t("title")
            if not title: continue
            desc  = BeautifulSoup(_t("description"), "lxml").get_text(" ", strip=True)[:400]
            link  = _t("link") or _t("guid")
            pub   = _t("pubDate") or _t("published")
            arts.append({
                "title":        title,
                "url":          link,
                "published":    pub,
                "summary":      desc,
                "source":       source_name,
                "category":     "health",
                "subcategories":health_subcategory(title, desc),
                "severity":     _severity(title, desc),
                "sentiment":    sentiment_score(title + " " + desc),
            })
    except ET.ParseError:
        pass
    return arts


# ── WHO disease outbreaks (special endpoint) ──────────────────────────────────

async def get_who_alerts() -> dict:
    """WHO disease outbreak news and alerts."""
    if c := c_get("who_alerts", {}): return c
    feeds  = [
        "https://www.who.int/feeds/entity/mediacentre/news/en/rss.xml",
        "https://www.who.int/feeds/entity/csr/don/en/rss.xml",  # Disease outbreaks
    ]
    all_arts = []
    for url in feeds:
        try:
            r = await fetch_rss(url)
            if r.status_code == 200:
                all_arts.extend(_parse_health_rss(r.text, "WHO"))
        except Exception:
            pass

    # Filter for high-severity only
    alerts = [a for a in all_arts if a["severity"] in ("critical","high")]
    result = {
        "source":      "World Health Organization",
        "total_items": len(all_arts),
        "alerts":      alerts,
        "all_news":    all_arts[:30],
    }
    c_set("who_alerts", {}, result, ttl=600)
    return result


async def get_cdc_updates() -> dict:
    """CDC health updates and advisories."""
    if c := c_get("cdc", {}): return c
    try:
        r    = await fetch_rss(HEALTH_FEEDS["cdc"]["url"])
        arts = _parse_health_rss(r.text, "CDC") if r.status_code == 200 else []
    except Exception:
        arts = []
    result = {"source": "CDC", "count": len(arts), "articles": arts}
    c_set("cdc", {}, result, ttl=600)
    return result


async def get_health_news(count: int = 50) -> dict:
    """Aggregated health news from all sources."""
    if c := c_get("health_all", {"c": count}): return c

    tasks = []
    for key, meta in HEALTH_FEEDS.items():
        tasks.append(_fetch_feed(key, meta))
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_arts = []
    for r in results:
        if isinstance(r, list): all_arts.extend(r)

    all_arts = deduplicate(all_arts)[:count]
    # Sort by severity
    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    all_arts.sort(key=lambda a: sev_order.get(a.get("severity","low"), 3))

    result = {"count": len(all_arts), "articles": all_arts}
    c_set("health_all", {"c": count}, result, ttl=300)
    return result


async def _fetch_feed(key: str, meta: dict) -> list:
    try:
        r = await fetch_rss(meta["url"])
        return _parse_health_rss(r.text, meta["name"]) if r.status_code == 200 else []
    except Exception:
        return []


async def filter_health_news(keyword: str, count: int = 30) -> dict:
    """Filter health news by keyword."""
    base = await get_health_news(100)
    arts = keyword_filter(base.get("articles", []), keyword.split())[:count]
    return {
        "keyword":  keyword,
        "count":    len(arts),
        "articles": arts,
    }


async def get_by_subcategory(subcat: str) -> dict:
    """Get health news by sub-category."""
    VALID = [
        "infectious_disease", "mental_health", "cancer", "cardiovascular",
        "nutrition", "pharmaceutical", "public_health", "medical_research"
    ]
    if subcat not in VALID:
        return {"error": f"Invalid subcategory. Valid: {VALID}"}
    base = await get_health_news(200)
    arts = [a for a in base.get("articles",[]) if subcat in a.get("subcategories",[])]
    return {"subcategory": subcat, "count": len(arts), "articles": arts[:40]}


async def get_health_by_country(country: str) -> dict:
    """Country-specific health news (uses health + country RSS)."""
    from scrapers.rss_scraper import get_by_country, SOURCES
    country_news  = await get_by_country(country)
    health_filter = keyword_filter(
        country_news.get("articles", []),
        ["health","hospital","disease","vaccine","covid","medicine","outbreak"],
    )
    return {"country": country, "count": len(health_filter), "articles": health_filter}


async def get_health_categories() -> dict:
    """Return all available health sub-categories with descriptions."""
    return {
        "subcategories": {
            "infectious_disease":  "Viruses, bacteria, outbreaks, epidemics, pandemics",
            "mental_health":       "Depression, anxiety, psychiatry, psychology",
            "cancer":              "Oncology, tumors, chemotherapy, clinical trials",
            "cardiovascular":      "Heart disease, stroke, blood pressure, cardiology",
            "nutrition":           "Diet, obesity, vitamins, supplements",
            "pharmaceutical":      "Drug approvals, FDA, clinical trials, side effects",
            "public_health":       "WHO, CDC, health policy, healthcare systems",
            "medical_research":    "Studies, discoveries, breakthroughs, treatments",
        }
    }
