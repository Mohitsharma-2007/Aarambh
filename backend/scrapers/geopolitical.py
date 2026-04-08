"""
scrapers/geopolitical.py  —  Geopolitical Intelligence Aggregator
==================================================================
Sources:
  • GDELT Project API (real-time global events database)
  • Al Jazeera, Reuters World, Foreign Affairs RSS
  • Conflict/sanctions/election keyword filtering
  • Country-level geopolitical risk scoring

GDELT: Free, no API key, real-time global event monitoring
"""

import asyncio, xml.etree.ElementTree as ET, urllib.parse
from bs4 import BeautifulSoup
from utils.session import fetch_rss, fetch_json, fetch
from utils.cache   import get as c_get, set as c_set
from utils.text_filter import (
    keyword_filter, deduplicate, geo_subcategory,
    sentiment_score, extract_entities
)

# ── Geopolitical RSS feeds ────────────────────────────────────────────────────
GEO_FEEDS = {
    "al_jazeera":     "https://www.aljazeera.com/xml/rss/all.xml",
    "reuters_world":  "https://feeds.reuters.com/Reuters/worldNews",
    "bbc_world":      "https://feeds.bbci.co.uk/news/world/rss.xml",
    "guardian_world": "https://www.theguardian.com/world/rss",
    "france24":       "https://www.france24.com/en/rss",
    "dw_world":       "https://rss.dw.com/xml/rss-en-world",
    "nhk_world":      "https://www3.nhk.or.jp/rss/news/cat0.xml",
    "foreign_affairs":"https://www.foreignaffairs.com/rss.xml",
}

GEO_SOURCE_NAMES = {
    "al_jazeera": "Al Jazeera", "reuters_world": "Reuters World",
    "bbc_world": "BBC World", "guardian_world": "The Guardian",
    "france24": "France 24", "dw_world": "DW News",
    "nhk_world": "NHK World", "foreign_affairs": "Foreign Affairs",
}

# ── Country risk scores (static baseline, news-adjusted) ─────────────────────
COUNTRY_RISK_BASE = {
    "RU": 85, "UA": 90, "IL": 85, "PS": 95, "SY": 88,
    "IR": 80, "KP": 82, "MM": 78, "YE": 87, "SD": 75,
    "AF": 80, "IQ": 72, "LY": 70, "SO": 73, "NG": 65,
    "PK": 60, "CN": 45, "IN": 35, "TR": 45, "VE": 60,
    "US": 20, "GB": 15, "DE": 12, "FR": 18, "JP": 10,
    "AU": 10, "CA": 10, "BR": 40, "ZA": 45, "MX": 50,
}


def _parse_geo_rss(xml_text: str, source: str) -> list:
    arts = []
    try:
        root  = ET.fromstring(xml_text)
        ch    = root.find("channel")
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
            subcats  = geo_subcategory(title, desc)
            entities = extract_entities(title + " " + desc)
            arts.append({
                "title":        title,
                "url":          link,
                "published":    pub,
                "summary":      desc,
                "source":       source,
                "category":     "geopolitical",
                "subcategories":subcats,
                "entities":     entities,
                "sentiment":    sentiment_score(title + " " + desc),
            })
    except ET.ParseError:
        pass
    return arts


# ── GDELT API ─────────────────────────────────────────────────────────────────

async def gdelt_search(query: str, mode: str = "artlist",
                       max_records: int = 25) -> dict:
    """
    Query GDELT Project API.
    Free, no API key, real-time global events from 250,000+ media sources.
    Docs: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
    """
    ck = {"q": query, "mode": mode}
    if c := c_get("gdelt", ck): return c

    params = {
        "query":    query,
        "mode":     mode,         # artlist | timelinevol | tonechart
        "maxrecords": max_records,
        "format":   "json",
        "sort":     "DateDesc",
        "timespan": "LAST24H",
    }
    try:
        r = await fetch_json(
            "https://api.gdeltproject.org/api/v2/doc/doc",
            params=params
        )
        if r.status_code != 200:
            return {"error": f"GDELT HTTP {r.status_code}", "query": query}
        data = r.json()
    except Exception as ex:
        return {"error": str(ex), "query": query}

    articles = []
    for art in (data.get("articles") or []):
        articles.append({
            "title":     art.get("title"),
            "url":       art.get("url"),
            "published": art.get("seendate"),
            "source":    art.get("domain"),
            "language":  art.get("language"),
            "tone":      art.get("tone"),
            "country":   art.get("sourcecountry"),
            "entities":  extract_entities(art.get("title","") + " " + art.get("seendate","")),
        })

    result = {
        "query":    query,
        "source":   "GDELT Project",
        "count":    len(articles),
        "articles": articles,
        "note":     "GDELT monitors 250,000+ media sources in real-time across 65 languages",
    }
    c_set("gdelt", ck, result, ttl=300)
    return result


async def gdelt_timeline(query: str) -> dict:
    """GDELT volume timeline for a topic (shows news intensity over time)."""
    params = {
        "query":   query,
        "mode":    "timelinevol",
        "format":  "json",
        "timespan":"LAST7DAYS",
    }
    try:
        r    = await fetch_json("https://api.gdeltproject.org/api/v2/doc/doc", params=params)
        data = r.json() if r.status_code == 200 else {}
        return {
            "query":    query,
            "timeline": data.get("timeline", []),
            "source":   "GDELT",
        }
    except Exception as ex:
        return {"error": str(ex), "query": query}


# ── Topic-specific aggregators ────────────────────────────────────────────────

async def get_conflicts() -> dict:
    """Active conflict zone news."""
    if c := c_get("geo_conflicts", {}): return c

    # GDELT query for conflicts
    gdelt  = await gdelt_search("war OR conflict OR military OR airstrike OR ceasefire")
    # RSS feeds filtered for conflict keywords
    rss_arts = await _fetch_geo_rss_filtered(
        ["al_jazeera","reuters_world","bbc_world"],
        ["war","conflict","military","airstrike","troops","missile","battle","ceasefire","invasion"],
    )
    all_arts = deduplicate((gdelt.get("articles") or []) + rss_arts)
    result   = {
        "topic":    "Active Conflicts",
        "count":    len(all_arts),
        "articles": all_arts[:40],
        "gdelt_tone_avg": _avg_tone(gdelt.get("articles",[])),
        "conflict_zones": _extract_conflict_zones(all_arts),
    }
    c_set("geo_conflicts", {}, result, ttl=300)
    return result


async def get_sanctions() -> dict:
    """Sanctions, embargoes, and trade restrictions news."""
    gdelt    = await gdelt_search("sanction OR embargo OR trade restriction OR asset freeze")
    rss_arts = await _fetch_geo_rss_filtered(
        ["reuters_world","bbc_world","guardian_world"],
        ["sanction","embargo","ban","restriction","asset freeze","tariff"],
    )
    all_arts = deduplicate((gdelt.get("articles") or []) + rss_arts)
    return {"topic": "Sanctions & Trade", "count": len(all_arts), "articles": all_arts[:40]}


async def get_elections() -> dict:
    """Global election news."""
    gdelt    = await gdelt_search("election OR vote OR ballot OR referendum OR campaign")
    rss_arts = await _fetch_geo_rss_filtered(
        ["reuters_world","bbc_world","al_jazeera","guardian_world"],
        ["election","vote","ballot","referendum","candidate","campaign","polling"],
    )
    all_arts = deduplicate((gdelt.get("articles") or []) + rss_arts)
    return {"topic": "Elections", "count": len(all_arts), "articles": all_arts[:40]}


async def get_tensions() -> dict:
    """Rising geopolitical tensions."""
    gdelt    = await gdelt_search("tension OR crisis OR standoff OR escalation OR provocation")
    rss_arts = await _fetch_geo_rss_filtered(
        ["al_jazeera","reuters_world","bbc_world","france24","dw_world"],
        ["tension","crisis","escalation","standoff","threat","dispute","protest"],
    )
    all_arts = deduplicate((gdelt.get("articles") or []) + rss_arts)
    return {"topic": "Geopolitical Tensions", "count": len(all_arts), "articles": all_arts[:40]}


async def get_treaties() -> dict:
    """International agreements, treaties, summits."""
    gdelt    = await gdelt_search("treaty OR agreement OR summit OR bilateral OR diplomatic talks")
    rss_arts = await _fetch_geo_rss_filtered(
        ["reuters_world","bbc_world","france24","foreign_affairs"],
        ["treaty","agreement","summit","bilateral","multilateral","diplomatic","talks","deal"],
    )
    all_arts = deduplicate((gdelt.get("articles") or []) + rss_arts)
    return {"topic": "Treaties & Diplomacy", "count": len(all_arts), "articles": all_arts[:40]}


async def get_geo_by_country(country_code: str) -> dict:
    """Geopolitical news for a specific country."""
    COUNTRY_NAMES = {
        "RU":"Russia","UA":"Ukraine","IL":"Israel","IR":"Iran","CN":"China",
        "US":"United States","IN":"India","PK":"Pakistan","KP":"North Korea",
        "TR":"Turkey","SA":"Saudi Arabia","SY":"Syria","AF":"Afghanistan",
        "BR":"Brazil","DE":"Germany","FR":"France","GB":"United Kingdom",
    }
    name     = COUNTRY_NAMES.get(country_code.upper(), country_code)
    gdelt    = await gdelt_search(name)
    rss_arts = await _fetch_geo_rss_filtered(
        list(GEO_FEEDS.keys()),
        [name, country_code.lower()],
    )
    all_arts = deduplicate((gdelt.get("articles") or []) + rss_arts)
    risk     = COUNTRY_RISK_BASE.get(country_code.upper(), 30)
    return {
        "country":     name,
        "risk_score":  risk,
        "risk_label":  _risk_label(risk),
        "count":       len(all_arts),
        "articles":    all_arts[:40],
    }


async def get_all_geo_news(count: int = 50) -> dict:
    """All geopolitical news aggregated."""
    if c := c_get("geo_all", {"c": count}): return c
    tasks   = [_fetch_single_geo(k, v) for k, v in GEO_FEEDS.items()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_arts = []
    for r in results:
        if isinstance(r, list): all_arts.extend(r)
    all_arts = deduplicate(all_arts)[:count]
    result   = {"count": len(all_arts), "articles": all_arts}
    c_set("geo_all", {"c": count}, result, ttl=300)
    return result


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _fetch_single_geo(key: str, url: str) -> list:
    try:
        r = await fetch_rss(url)
        return _parse_geo_rss(r.text, GEO_SOURCE_NAMES.get(key, key)) if r.status_code == 200 else []
    except Exception:
        return []


async def _fetch_geo_rss_filtered(source_keys: list, keywords: list) -> list:
    tasks   = [_fetch_single_geo(k, GEO_FEEDS[k]) for k in source_keys if k in GEO_FEEDS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_arts = []
    for r in results:
        if isinstance(r, list): all_arts.extend(r)
    return keyword_filter(all_arts, keywords)


def _avg_tone(articles: list) -> float:
    tones = [float(a["tone"]) for a in articles if a.get("tone")]
    return round(sum(tones)/len(tones), 2) if tones else 0.0


def _extract_conflict_zones(articles: list) -> list:
    from collections import Counter
    ZONES = ["Ukraine","Russia","Israel","Gaza","Palestine","Sudan","Syria",
             "Yemen","Myanmar","Ethiopia","Iran","Iraq","Libya","Somalia"]
    counter = Counter()
    for a in articles:
        text = (a.get("title","") + " " + a.get("summary","")).lower()
        for z in ZONES:
            if z.lower() in text:
                counter[z] += 1
    return [{"zone": z, "mentions": c} for z, c in counter.most_common(10)]


def _risk_label(score: int) -> str:
    if score >= 80: return "extreme"
    if score >= 60: return "high"
    if score >= 40: return "elevated"
    if score >= 20: return "moderate"
    return "low"
