"""
scrapers/rss_scraper.py  —  50+ RSS News Feed Scraper
======================================================
Covers: Bloomberg-style finance, India, US, UK, Canada, Australia,
        Germany, France, Japan, China, Russia, Brazil, South Africa,
        and digest/AI-powered platforms.
"""

import re, xml.etree.ElementTree as ET, asyncio
from typing import Optional
from bs4 import BeautifulSoup
from utils.session import fetch_rss
from utils.cache   import get as c_get, set as c_set
from utils.text_filter import categorize, deduplicate, sentiment_score, extract_entities

# ── Master Source Registry ────────────────────────────────────────────────────
SOURCES = {
    # ── Finance / Markets ────────────────────────────────────────────────────
    "bloomberg":          {"url": "https://www.bloomberg.com/feeds/sitemap_news.xml",      "country": "US", "category": "finance",  "name": "Bloomberg"},
    "reuters_business":   {"url": "https://www.reutersagency.com/feed/?best-topics=business&post_type=best", "country": "US", "category": "finance",  "name": "Reuters Business"},
    "cnbc_top":           {"url": "https://www.cnbc.com/id/100003114/device/rss/rss.html", "country": "US", "category": "finance", "name": "CNBC Top News"},
    "cnbc_finance":       {"url": "https://www.cnbc.com/id/10000664/device/rss/rss.html",  "country": "US", "category": "finance", "name": "CNBC Finance"},
    "wsj_markets":        {"url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",         "country": "US", "category": "finance",  "name": "WSJ Markets"},
    "marketwatch":        {"url": "http://feeds.marketwatch.com/marketwatch/topstories/",  "country": "US", "category": "finance",  "name": "MarketWatch"},
    "yahoo_finance":      {"url": "https://finance.yahoo.com/news/rssindex",               "country": "US", "category": "finance",  "name": "Yahoo Finance"},
    "investing_com":      {"url": "https://www.investing.com/rss/news.rss",                "country": "US", "category": "finance",  "name": "Investing.com"},
    "fortune":            {"url": "https://fortune.com/feed/fortune-feeds-all/",           "country": "US", "category": "finance",  "name": "Fortune"},
    "zerodha_pulse":      {"url": "https://pulse.zerodha.com/feed.php",                    "country": "IN", "category": "finance",  "name": "Zerodha Pulse"},

    # ── India ────────────────────────────────────────────────────────────────
    "et_markets":         {"url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",     "country": "IN", "category": "finance",  "name": "Economic Times Markets"},
    "et_economy":         {"url": "https://economictimes.indiatimes.com/economy/rssfeeds/1373380680.cms",     "country": "IN", "category": "finance",  "name": "Economic Times Economy"},
    "business_standard":  {"url": "https://www.business-standard.com/rss/latest-news-1.rss",                   "country": "IN", "category": "finance",  "name": "Business Standard"},
    "moneycontrol":       {"url": "https://www.moneycontrol.com/rss/latestnews.xml",                          "country": "IN", "category": "finance",  "name": "Moneycontrol"},
    "livemint":           {"url": "https://www.livemint.com/rss/news",                                        "country": "IN", "category": "finance",  "name": "Mint"},
    "ndtv_profit":        {"url": "https://www.ndtv.com/business/rss",                                        "country": "IN", "category": "finance",  "name": "NDTV Profit"},
    "ndtv":               {"url": "https://www.ndtv.com/rss/top-stories",                                     "country": "IN", "category": "world",    "name": "NDTV"},
    "toi":                {"url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",              "country": "IN", "category": "world",    "name": "Times of India"},
    "finshots":           {"url": "https://finshots.in/feed/",                                                 "country": "IN", "category": "finance",  "name": "Finshots"},
    "the_hindu":          {"url": "https://www.thehindu.com/news/national/feeder/default.rss",                "country": "IN", "category": "world",    "name": "The Hindu"},

    # ── Global ──────────────────────────────────────────────────────────────────
    "cnn":                {"url": "http://rss.cnn.com/rss/edition.rss",                                       "country": "US", "category": "world",    "name": "CNN"},
    "nytimes":            {"url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",                "country": "US", "category": "world",    "name": "New York Times"},
    "bbc":                {"url": "http://feeds.bbci.co.uk/news/rss.xml",                                     "country": "GB", "category": "world",    "name": "BBC News"},
    "guardian":           {"url": "https://www.theguardian.com/world/rss",                                    "country": "GB", "category": "world",    "name": "The Guardian"},
    "al_jazeera":         {"url": "https://www.aljazeera.com/xml/rss/all.xml",                                "country": "QA", "category": "world",    "name": "Al Jazeera"},
    "reuters_world":      {"url": "https://www.reutersagency.com/feed/?best-topics=world&post_type=best",      "country": "US", "category": "world",    "name": "Reuters World"},
    "dw":                 {"url": "https://rss.dw.com/xml/rss-en-all",                                        "country": "DE", "category": "world",    "name": "Deutsche Welle"},
    "france24":           {"url": "https://www.france24.com/en/rss",                                          "country": "FR", "category": "world",    "name": "France 24"},
}

# ── Country → source mapping ──────────────────────────────────────────────────
COUNTRY_SOURCES = {
    "IN": ["et_markets","et_economy","business_standard","moneycontrol","mint","ndtv_profit","ndtv_news","toi","finshots","zee_business"],
    "US": ["cnn","cnn_business","nytimes","axios","npr","ap_news","bloomberg_markets","reuters_business","cnbc_top","wsj_markets","marketwatch","yahoo_finance_news","forbes_investing","fortune"],
    "GB": ["bbc","bbc_business","guardian","guardian_business","ft_markets"],
    "CA": ["cbc","global_news"],
    "AU": ["abc_au","sbs_au"],
    "DE": ["dw","spiegel"],
    "FR": ["france24","lemonde"],
    "JP": ["nhk","japan_times"],
    "CN": ["cgtn"],
    "RU": ["rt","tass"],
    "BR": ["globo"],
    "ZA": ["news24","ewn"],
}

CATEGORY_SOURCES = {
    "finance":      ["bloomberg_markets","reuters_business","cnbc_top","cnbc_finance","ft_markets","wsj_markets","et_markets","moneycontrol","mint","ndtv_profit","business_standard","zee_business","marketwatch","yahoo_finance_news","investing_com","forbes_investing","fortune","finshots","cnn_business","bbc_business","guardian_business","et_economy"],
    "world":        ["cnn","nytimes","bbc","guardian","dw","france24","nhk","al_jazeera","reuters_world","ap_news","axios","npr","spiegel","lemonde","cgtn","rt","tass","globo","news24","ewn","abc_au","sbs_au","cbc","global_news","japan_times"],
    "health":       ["who_news","cdc_news","nih_news","medscape","health_news","bbc","nytimes"],
    "geopolitical": ["al_jazeera","reuters_world","foreign_affairs","stratfor","bbc","guardian","dw","france24","nytimes"],
    "science":      ["nature","science_daily","nih_news","bbc","nytimes"],
    "technology":   ["axios","nytimes","bbc","guardian","cnbc_top"],
    "india":        ["et_markets","et_economy","business_standard","moneycontrol","mint","ndtv_profit","ndtv_news","toi","finshots","zee_business"],
}


# ── RSS Parser ────────────────────────────────────────────────────────────────

def _parse_rss(xml_text: str, source_key: str) -> list:
    meta   = SOURCES.get(source_key, {})
    arts   = []
    try:
        # Use a more flexible parser namespacing
        namespaces = {
            'media': 'http://search.yahoo.com/mrss/',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'content': 'http://purl.org/rss/1.0/modules/content/'
        }
        
        root = ET.fromstring(xml_text)
        ch   = root.find("channel")
        items = ch.findall("item") if ch else root.findall(".//item")
        for item in items:
            def _t(tag): 
                el = item.find(tag)
                return (el.text or "").strip() if el is not None else ""
            
            title = _t("title")
            if not title: continue
            
            desc_raw = _t("description")
            soup = BeautifulSoup(desc_raw, "lxml")
            desc = soup.get_text(" ", strip=True)[:400]
            
            # 🖼 Extract Thumbnail Logic
            thumbnail = ""
            # Try media:content
            media_content = item.find('media:content', namespaces)
            if media_content is not None and media_content.get('url'):
                thumbnail = media_content.get('url')
            
            # Try enclosure
            if not thumbnail:
                encl = item.find('enclosure')
                if encl is not None and 'image' in (encl.get('type') or ''):
                    thumbnail = encl.get('url')
                    
            # Try finding image in description html
            if not thumbnail:
                img = soup.find('img')
                if img and img.get('src'):
                    thumbnail = img.get('src')
            
            link     = _t("link") or _t("guid")
            pub      = _t("pubDate") or _t("dc:date") or _t("published")
            
            arts.append({
                "title":       title,
                "url":         link,
                "publishedAt": pub,
                "summary":     desc,
                "urlToImage":  thumbnail,
                "thumbnail":   thumbnail,
                "source":      meta.get("name", source_key),
                "source_key":  source_key,
                "country":     meta.get("country", ""),
                "category":    meta.get("category", ""),
                "sentiment":   sentiment_score(title + " " + desc),
            })
    except Exception as e:
        print(f"RSS Parse Error [{source_key}]: {e}")
    return arts


# ── Core fetch function ───────────────────────────────────────────────────────

async def fetch_source(source_key: str, max_items: int = 20) -> dict:
    """Fetch and parse a single RSS source."""
    if source_key not in SOURCES:
        return {"error": f"Unknown source: {source_key}"}
    meta = SOURCES[source_key]
    ck   = {"s": source_key}
    if c := c_get("rss", ck): return c

    try:
        r = await fetch_rss(meta["url"])
    except Exception as ex:
        return {"source": meta["name"], "error": str(ex), "articles": []}

    if r.status_code != 200:
        return {"source": meta["name"], "error": f"HTTP {r.status_code}", "articles": []}

    arts   = _parse_rss(r.text, source_key)[:max_items]
    result = {
        "source":   meta["name"],
        "country":  meta["country"],
        "category": meta["category"],
        "count":    len(arts),
        "articles": arts,
    }
    c_set("rss", ck, result, ttl=300)
    return result


async def fetch_multiple(source_keys: list, max_per_source: int = 10,
                          max_total: int = 100) -> list:
    """Fetch multiple sources concurrently."""
    tasks   = [fetch_source(k, max_per_source) for k in source_keys if k in SOURCES]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_arts = []
    for r in results:
        if isinstance(r, dict) and r.get("articles"):
            all_arts.extend(r["articles"])
    return deduplicate(all_arts)[:max_total]


async def get_headlines(count: int = 50) -> dict:
    """Top headlines from major sources."""
    ck = {"t": "headlines", "c": count}
    if c := c_get("hl", ck): return c
    keys = ["reuters_business","bbc","cnn","bloomberg_markets","al_jazeera",
            "ndtv_news","dw","france24","nhk","abc_au"]
    arts = await fetch_multiple(keys, max_per_source=8, max_total=count)
    res  = {"count": len(arts), "articles": arts}
    c_set("hl", ck, res, ttl=300)
    return res


async def search_all(query: str, count: int = 30) -> dict:
    """Search across all sources for a keyword."""
    ck = {"q": query}
    if c := c_get("search", ck): return c

    # Use Google News RSS as primary search
    from utils.session import fetch_rss as _rss
    import urllib.parse
    q_enc = urllib.parse.quote(query)
    url   = f"https://news.google.com/rss/search?q={q_enc}&hl=en-US&gl=US&ceid=US:en"
    try:
        r    = await _rss(url)
        arts = _parse_rss(r.text, "cnn")  # reuse parser
        for a in arts:
            a["source"]     = "Google News"
            a["source_key"] = "google_news"
    except Exception:
        arts = []

    # Supplement with keyword filter from cached feeds
    if len(arts) < 10:
        top   = await get_headlines(count=100)
        from utils.text_filter import keyword_filter
        extra = keyword_filter(top.get("articles", []), query.split())
        arts  = deduplicate(arts + extra)

    arts   = arts[:count]
    result = {"query": query, "count": len(arts), "articles": arts}
    c_set("search", ck, result, ttl=300)
    return result


async def get_by_category(category: str, count: int = 40) -> dict:
    """Get news by category."""
    keys = CATEGORY_SOURCES.get(category.lower(), [])
    if not keys:
        return {"error": f"Unknown category. Valid: {sorted(CATEGORY_SOURCES.keys())}"}
    ck = {"cat": category}
    if c := c_get("cat", ck): return c
    arts   = await fetch_multiple(keys, max_per_source=8, max_total=count)
    result = {"category": category, "count": len(arts), "articles": arts}
    c_set("cat", ck, result, ttl=300)
    return result


async def get_by_country(country: str, count: int = 40) -> dict:
    """Get news by country code."""
    keys = COUNTRY_SOURCES.get(country.upper(), [])
    if not keys:
        return {"error": f"Unknown country. Valid: {sorted(COUNTRY_SOURCES.keys())}"}
    ck = {"cc": country}
    if c := c_get("country", ck): return c
    arts   = await fetch_multiple(keys, max_per_source=10, max_total=count)
    result = {"country": country, "count": len(arts), "articles": arts}
    c_set("country", ck, result, ttl=300)
    return result


async def get_finance_news(count: int = 50) -> dict:
    """All finance/markets news aggregated."""
    return await get_by_category("finance", count)


async def get_trending_topics(articles_pool: int = 200) -> dict:
    """Extract trending topics from recent headlines."""
    top  = await get_headlines(articles_pool)
    arts = top.get("articles", [])
    word_count: dict = {}
    stopwords = {"the","a","an","in","of","to","is","was","for","on","at","by","with","and","or","but","news","report","says","said","new","will"}
    for a in arts:
        words = re.findall(r'\b[A-Za-z]{4,}\b', a.get("title",""))
        for w in words:
            wl = w.lower()
            if wl not in stopwords:
                word_count[wl] = word_count.get(wl, 0) + 1
    trending = sorted(word_count.items(), key=lambda x: -x[1])[:20]
    return {"trending": [{"topic": t, "mentions": c} for t, c in trending]}
