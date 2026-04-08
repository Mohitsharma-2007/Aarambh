"""
scrapers/google_news.py  —  Google News via RSS + HTML
=======================================================
Primary  : RSS feeds at news.google.com/rss  (pure XML, no JS needed)
Secondary: Google Search news tab  (?tbm=nws)

Network
  news.google.com    Port 443  HTTPS  (RSS)
  www.google.com     Port 443  HTTPS  (search news tab)
"""

import re, xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from utils.session import fetch
from utils.cache   import get as c_get, set as c_set

RSS  = "https://news.google.com/rss"
SRCH = "https://www.google.com/search"

# Google News RSS topic tokens (verified working)
TOPICS = {
    "business":      "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB",
    "technology":    "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB",
    "science":       "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y1RFU0FtVnVHZ0pWVXlnQVAB",
    "health":        "CAAqIQgKIhtDQkFTRGdvSUwyMHZNR3QwTlRFU0FtVnVHZ0FQAQ",
    "sports":        "CAAqJggKIiBDQkFTRWdvSUwyMHZNR1ptZDNjU0FtVnVHZ0pWVXlnQVAB",
    "entertainment": "CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnVHZ0pWVXlnQVAB",
    "finance":       "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB",
    "us":            "CAAqIggKIhxDQkFTRHdvSkwyMHZNRFZxYUdjU0FtVnVLQUFQAQ",
    # "world" token changed — now use search-based feed as reliable substitute
    "world":         None,
}

COUNTRY_CODES = {
    "IN": "en-IN", "US": "en-US", "GB": "en-GB",
    "AU": "en-AU", "CA": "en-CA", "SG": "en-SG",
}

def _rss_params(lang: str = "en", country: str = "US") -> dict:
    hl = COUNTRY_CODES.get(country.upper(), f"{lang}-{country}")
    return {"hl": hl, "gl": country.upper(), "ceid": f"{country.upper()}:{lang}"}

def _parse_rss(xml_text: str) -> list[dict]:
    articles = []
    try:
        root = ET.fromstring(xml_text)
        ch   = root.find("channel")
        if ch is None: return articles
        for item in ch.findall("item"):
            def _t(tag: str) -> str:
                el = item.find(tag)
                return (el.text or "").strip() if el is not None else ""
            # Strip HTML from description
            desc = BeautifulSoup(_t("description"), "lxml").get_text(" ", strip=True)
            # Source element has name attribute
            src_el  = item.find("source")
            source  = src_el.text.strip() if src_el is not None else ""
            src_url = src_el.get("url", "") if src_el is not None else ""
            articles.append({
                "title":       _t("title"),
                "url":         _t("link"),
                "published":   _t("pubDate"),
                "source":      source,
                "source_url":  src_url,
                "summary":     desc[:500] if desc else None,
                "guid":        _t("guid"),
            })
    except ET.ParseError:
        pass
    return articles

def _parse_search_news(html: str) -> list[dict]:
    soup     = BeautifulSoup(html, "lxml")
    articles = []
    seen     = set()
    for div in soup.find_all("div", class_=re.compile(r"(SoaBEf|WlydOe|dbsr|nChh6e)")):
        h_el  = div.find(re.compile(r"h[1-4]"), class_=re.compile(r"(DKV0Md|JtKRv|nDgy9d)"))
        s_el  = div.find(class_=re.compile(r"(NUnG9d|CEMjEf|KbnJ8|UPmit)"))
        t_el  = div.find("time")
        a_el  = div.find("a", href=True)
        title = (h_el.get_text(strip=True) if h_el else None) or \
                (a_el.get_text(strip=True)[:120] if a_el else None)
        if not title or title in seen: continue
        seen.add(title)
        articles.append({
            "title":     title,
            "source":    s_el.get_text(strip=True) if s_el else None,
            "published": t_el.get("datetime") if t_el else None,
            "url":       a_el["href"] if a_el else None,
        })
    return articles

# ─── Public API ───────────────────────────────────────────────────────────────

async def search_news(query: str, lang: str = "en", country: str = "US",
                      count: int = 20) -> dict:
    """
    Search Google News via RSS.
    Returns full article list with title, source, published date, URL, summary.
    """
    ck = {"q": query, "l": lang, "c": country}
    if c := c_get("gn_s", ck): return c

    params = _rss_params(lang, country)
    params["q"] = query

    try:
        r = await fetch(f"{RSS}/search", params=params, domain="rss")
    except Exception as ex:
        return {"error": str(ex), "query": query}

    if r.status_code != 200:
        # Fallback to Google Search news tab
        try:
            r2 = await fetch(SRCH, params={"q": query, "tbm": "nws", "hl": lang},
                             domain="google")
            articles = _parse_search_news(r2.text)[:count]
            return {"query": query, "source": "google_search_fallback",
                    "count": len(articles), "articles": articles}
        except Exception as ex2:
            return {"error": f"RSS: HTTP {r.status_code}, Search: {ex2}", "query": query}

    articles = _parse_rss(r.text)[:count]
    result   = {"query": query, "source": "google_news_rss",
                "count": len(articles), "articles": articles}
    c_set("gn_s", ck, result, ttl=300)
    return result


async def get_topic(topic: str = "business", lang: str = "en",
                    country: str = "US", count: int = 30) -> dict:
    """
    Fetch a full topic feed from Google News RSS.
    topic: business | technology | science | health | sports | world | finance | us | entertainment
    """
    topic = topic.lower().strip()
    if topic not in TOPICS:
        return {"error": f"Unknown topic. Valid: {sorted(TOPICS.keys())}"}

    token = TOPICS[topic]

    # "world" token is broken — fall back to RSS search
    if token is None:
        return await search_news(
            "world news international", lang=lang, country=country, count=count
        ) | {"topic": topic, "_note": "RSS topic token unavailable — using search fallback"}

    ck = {"topic": topic, "l": lang, "c": country}
    if c := c_get("gn_t", ck): return c

    params = _rss_params(lang, country)
    try:
        r = await fetch(f"{RSS}/topics/{token}", params=params, domain="rss")
    except Exception as ex:
        return {"error": str(ex), "topic": topic}

    if r.status_code == 404:
        # Token expired — fallback to search
        fallback = await search_news(f"{topic} news", lang=lang, country=country, count=count)
        return fallback | {"topic": topic, "_note": f"RSS token returned 404, used search fallback"}

    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}", "topic": topic}

    articles = _parse_rss(r.text)[:count]
    result   = {"topic": topic, "count": len(articles), "articles": articles}
    c_set("gn_t", ck, result, ttl=600)
    return result


async def get_ticker_news(ticker: str, count: int = 20) -> dict:
    """News for a specific stock ticker via Google News RSS search."""
    ck = {"t": ticker}
    if c := c_get("gn_tk", ck): return c

    params = _rss_params()
    params["q"] = f'"{ticker.upper()}" stock'
    try:
        r = await fetch(f"{RSS}/search", params=params, domain="rss")
    except Exception as ex:
        return {"error": str(ex), "ticker": ticker}

    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}", "ticker": ticker}

    articles = _parse_rss(r.text)[:count]
    result   = {"ticker": ticker, "count": len(articles), "articles": articles}
    c_set("gn_tk", ck, result, ttl=300)
    return result


async def get_headlines(country: str = "US", lang: str = "en", count: int = 30) -> dict:
    """Top headlines from Google News RSS homepage."""
    ck = {"c": country, "l": lang}
    if c := c_get("gn_h", ck): return c

    params = _rss_params(lang, country)
    try:
        r = await fetch(RSS, params=params, domain="rss")
    except Exception as ex:
        return {"error": str(ex)}

    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}"}

    articles = _parse_rss(r.text)[:count]
    result   = {"country": country, "count": len(articles), "articles": articles}
    c_set("gn_h", ck, result, ttl=600)
    return result


async def search_company_news(company: str, ticker: str = "",
                               count: int = 20) -> dict:
    """Search news for a company by name + optional ticker."""
    q = f'"{company}"'
    if ticker:
        q += f' OR "{ticker.upper()}" stock'
    return await search_news(q, count=count)
