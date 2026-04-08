"""
scrapers/india_portals.py  —  India Government Data Portals
============================================================
Covers:
  • NDAP (ndap.niti.gov.in)         → NITI Aayog dataset catalogue
  • MyScheme (myscheme.gov.in)      → Government scheme directory
  • eSankhyiki (esankhyiki.mospi)   → MoSPI statistics portal
  • IndiaDataPortal (indiadataportal.com)
  • NSWS (nsws.gov.in)              → National Single Window System
  • india.gov.in                    → National portal
  • mygov.in                        → Citizen engagement
  • RBI (rbi.org.in)                → Monetary/financial data
  • SEBI (sebi.gov.in)              → Capital markets
  • MoF DEA (dea.gov.in)            → Finance ministry
"""

import re
from bs4 import BeautifulSoup
from utils.session import fetch, fetch_json
from utils.cache   import get as c_get, set as c_set

# ─────────────────────────────────────────────────────────────────────────────
# NDAP — NITI Aayog Data Portal
# ─────────────────────────────────────────────────────────────────────────────

async def ndap_search_datasets(query: str = "", sector: str = "",
                                page: int = 1, size: int = 20) -> dict:
    """
    Search NDAP dataset catalogue.
    Endpoint: https://ndap.niti.gov.in/api/catalogue/datasets (JSON API)
    """
    if c := c_get("ndap_ds", {"q": query, "s": sector, "p": page}): return c
    try:
        params = {"page": page, "size": size}
        if query:  params["search"]   = query
        if sector: params["category"] = sector
        r = await fetch_json("https://ndap.niti.gov.in/api/catalogue/datasets", params)
        if r.status_code == 200:
            data = r.json()
        else:
            data = await _ndap_html_fallback(query)
        result = {
            "source": "NDAP / NITI Aayog",
            "query":  query,
            "sector": sector,
            "data":   data,
        }
        c_set("ndap_ds", {"q": query, "s": sector, "p": page}, result, ttl=3600)
        return result
    except Exception as ex:
        return {"error": str(ex), "source": "NDAP"}


async def _ndap_html_fallback(query: str) -> dict:
    """Scrape NDAP website if API is unavailable."""
    try:
        r    = await fetch(f"https://ndap.niti.gov.in/datasets?search={query}")
        soup = BeautifulSoup(r.text, "lxml")
        datasets = []
        for card in soup.find_all(class_=re.compile(r"(dataset|card|item)")):
            title = card.find(re.compile(r"h[1-6]|a"))
            if title:
                datasets.append({"title": title.get_text(strip=True)})
        return {"datasets": datasets, "source": "NDAP (HTML fallback)"}
    except Exception:
        return {}


async def ndap_get_dataset(dataset_id: str) -> dict:
    """Fetch a specific NDAP dataset by ID."""
    try:
        r = await fetch_json(f"https://ndap.niti.gov.in/api/catalogue/datasets/{dataset_id}")
        if r.status_code == 200:
            return {"source": "NDAP", "dataset_id": dataset_id, "data": r.json()}
        return {"error": f"HTTP {r.status_code}", "dataset_id": dataset_id}
    except Exception as ex:
        return {"error": str(ex), "dataset_id": dataset_id}


async def ndap_indicators() -> dict:
    """Get NDAP indicator catalogue."""
    if c := c_get("ndap_indicators", {}): return c
    try:
        r = await fetch_json("https://ndap.niti.gov.in/api/catalogue/indicators")
        result = r.json() if r.status_code == 200 else {}
        c_set("ndap_indicators", {}, result, ttl=86400)
        return {"source": "NDAP", "data": result}
    except Exception as ex:
        return {"error": str(ex), "source": "NDAP"}


# ─────────────────────────────────────────────────────────────────────────────
# MyScheme — Government Scheme Directory
# ─────────────────────────────────────────────────────────────────────────────

async def myscheme_search(query: str = "", category: str = "",
                           state: str = "") -> dict:
    """
    Search government schemes on myscheme.gov.in
    """
    if c := c_get("myscheme", {"q": query, "cat": category, "state": state}): return c
    try:
        # Try MyScheme API endpoint
        params = {"keyword": query, "schemeCategory": category, "state": state}
        r = await fetch_json("https://api.myscheme.gov.in/search/v4/schemes", params)
        if r.status_code == 200:
            data   = r.json()
            result = {"source": "MyScheme.gov.in", "query": query, "data": data}
            c_set("myscheme", {"q": query, "cat": category, "state": state}, result, ttl=3600)
            return result
    except Exception:
        pass
    # HTML fallback
    try:
        url  = f"https://www.myscheme.gov.in/search?keyword={query}"
        r    = await fetch(url)
        soup = BeautifulSoup(r.text, "lxml")
        schemes = []
        for card in soup.find_all(class_=re.compile(r"(scheme|card)")):
            name  = card.find(re.compile(r"h[1-5]|strong"))
            desc  = card.find("p")
            a_tag = card.find("a", href=True)
            if name:
                schemes.append({
                    "name":        name.get_text(strip=True),
                    "description": desc.get_text(strip=True)[:200] if desc else "",
                    "url":         "https://www.myscheme.gov.in" + a_tag["href"]
                                   if a_tag and a_tag["href"].startswith("/") else "",
                })
        return {"source": "MyScheme.gov.in", "query": query,
                "count": len(schemes), "schemes": schemes}
    except Exception as ex:
        return {"error": str(ex), "source": "MyScheme.gov.in"}


async def myscheme_categories() -> dict:
    """All scheme categories on MyScheme."""
    return {
        "source": "MyScheme.gov.in",
        "categories": [
            "Agriculture, Rural & Environment",
            "Banking, Financial Services and Insurance",
            "Business & Entrepreneurship",
            "Education & Learning",
            "Health & Wellness",
            "Housing & Shelter",
            "Public Safety, Law & Justice",
            "Science, IT & Communications",
            "Skills & Employment",
            "Social Welfare & Empowerment",
            "Sports & Culture",
            "Transport & Infrastructure",
            "Travel & Tourism",
            "Utility & Sanitation",
            "Women and Child",
        ],
        "url": "https://www.myscheme.gov.in/schemes",
    }


# ─────────────────────────────────────────────────────────────────────────────
# eSankhyiki / MoSPI — Statistics Portal
# ─────────────────────────────────────────────────────────────────────────────

MOSPI_ENDPOINTS = {
    "gdp":       "https://mospi.gov.in/api/national-account/gdp",
    "cpi":       "https://mospi.gov.in/api/price/cpi",
    "iip":       "https://mospi.gov.in/api/industry/iip",
    "nso":       "https://mospi.gov.in/api/nso/reports",
    "census":    "https://censusindia.gov.in/census.website/data/census-tables",
}

async def mospi_get(indicator: str = "gdp") -> dict:
    """
    Fetch MoSPI statistical data.
    Falls back to esankhyiki.mospi.gov.in API.
    """
    if c := c_get("mospi", {"i": indicator}): return c
    result = {}
    # Try eSankhyiki API
    try:
        r = await fetch_json(
            f"https://esankhyiki.mospi.gov.in/api/data/{indicator}",
            params={"format": "json"}
        )
        if r.status_code == 200:
            result = {"source": "eSankhyiki / MoSPI", "indicator": indicator, "data": r.json()}
    except Exception:
        pass
    # Try MoSPI main site
    if not result:
        try:
            r = await fetch(f"https://mospi.gov.in/{indicator}")
            soup = BeautifulSoup(r.text, "lxml")
            tables = []
            for tbl in soup.find_all("table"):
                rows = [[td.get_text(strip=True) for td in tr.find_all(["td","th"])]
                        for tr in tbl.find_all("tr")]
                if rows: tables.append(rows)
            result = {"source": "MoSPI", "indicator": indicator,
                      "tables": tables, "note": "HTML fallback"}
        except Exception as ex:
            result = {"error": str(ex), "indicator": indicator}
    c_set("mospi", {"i": indicator}, result, ttl=3600)
    return result


async def mospi_releases() -> dict:
    """Latest MoSPI press releases and statistical releases."""
    if c := c_get("mospi_rel", {}): return c
    try:
        r    = await fetch("https://mospi.gov.in/pressrelease")
        soup = BeautifulSoup(r.text, "lxml")
        items = []
        for a in soup.find_all("a", href=re.compile(r"(press|release|pdf)")):
            text = a.get_text(strip=True)
            href = a["href"]
            if text and len(text) > 10:
                url = "https://mospi.gov.in" + href if href.startswith("/") else href
                items.append({
                    "title":  text,
                    "url":    url,
                    "type":   "PDF" if href.endswith(".pdf") else "HTML",
                    "source": "MoSPI",
                })
        result = {"source": "MoSPI", "count": len(items), "releases": items[:30]}
        c_set("mospi_rel", {}, result, ttl=3600)
        return result
    except Exception as ex:
        return {"error": str(ex), "source": "MoSPI"}


# ─────────────────────────────────────────────────────────────────────────────
# IndiaDataPortal
# ─────────────────────────────────────────────────────────────────────────────

async def india_data_portal_search(query: str, sector: str = "") -> dict:
    """Search indiadataportal.com for datasets."""
    if c := c_get("idp", {"q": query, "s": sector}): return c
    try:
        r = await fetch_json(
            "https://indiadataportal.com/api/datasets",
            params={"q": query, "sector": sector, "page": 1, "limit": 20}
        )
        if r.status_code == 200:
            result = {"source": "IndiaDataPortal", "query": query, "data": r.json()}
            c_set("idp", {"q": query, "s": sector}, result, ttl=3600)
            return result
    except Exception:
        pass
    try:
        r    = await fetch(f"https://indiadataportal.com/search?q={query}")
        soup = BeautifulSoup(r.text, "lxml")
        datasets = []
        for card in soup.find_all(class_=re.compile(r"(dataset|card|result)")):
            t = card.find(re.compile(r"h[1-5]"))
            if t: datasets.append({"title": t.get_text(strip=True), "source": "IndiaDataPortal"})
        return {"source": "IndiaDataPortal", "query": query,
                "count": len(datasets), "datasets": datasets}
    except Exception as ex:
        return {"error": str(ex), "source": "IndiaDataPortal"}


# ─────────────────────────────────────────────────────────────────────────────
# NSWS — National Single Window System
# ─────────────────────────────────────────────────────────────────────────────

async def nsws_search(query: str) -> dict:
    """Search NSWS for clearances, licenses, permits."""
    try:
        r = await fetch_json(
            "https://nsws.gov.in/api/approvals/search",
            params={"q": query}
        )
        if r.status_code == 200:
            return {"source": "NSWS", "query": query, "data": r.json()}
    except Exception:
        pass
    try:
        r    = await fetch(f"https://www.nsws.gov.in/search?q={query}")
        soup = BeautifulSoup(r.text, "lxml")
        items = []
        for el in soup.find_all(class_=re.compile(r"(approval|card|item)")):
            t = el.find(re.compile(r"h[1-5]|strong"))
            if t: items.append({"title": t.get_text(strip=True), "source": "NSWS"})
        return {"source": "NSWS", "query": query, "count": len(items), "items": items}
    except Exception as ex:
        return {"error": str(ex), "source": "NSWS"}


# ─────────────────────────────────────────────────────────────────────────────
# RBI — Reserve Bank of India
# ─────────────────────────────────────────────────────────────────────────────

RBI_RSS_FEEDS = {
    "press_releases": "https://rbi.org.in/scripts/rss.aspx?Id=2",
    "circulars":      "https://rbi.org.in/scripts/rss.aspx?Id=3",
    "notifications":  "https://rbi.org.in/scripts/rss.aspx?Id=4",
    "publications":   "https://rbi.org.in/scripts/rss.aspx?Id=5",
    "speeches":       "https://rbi.org.in/scripts/rss.aspx?Id=6",
}

import xml.etree.ElementTree as ET

async def rbi_get(feed_type: str = "press_releases") -> dict:
    """Get RBI press releases, circulars, notifications."""
    feed_url = RBI_RSS_FEEDS.get(feed_type, RBI_RSS_FEEDS["press_releases"])
    if c := c_get("rbi", {"f": feed_type}): return c
    try:
        from utils.session import fetch as _fetch
        r    = await _fetch(feed_url, accept="application/rss+xml,*/*")
        root = ET.fromstring(r.text)
        ch   = root.find("channel")
        items = ch.findall("item") if ch else root.findall(".//item")
        articles = []
        for item in items:
            def _t(tag):
                el = item.find(tag)
                return (el.text or "").strip() if el is not None else ""
            articles.append({
                "title":     _t("title"),
                "url":       _t("link"),
                "published": _t("pubDate"),
                "summary":   BeautifulSoup(_t("description"), "lxml").get_text(" ", strip=True)[:300],
                "source":    "RBI",
                "type":      feed_type.replace("_", " ").title(),
            })
        result = {"source": "RBI", "feed": feed_type, "count": len(articles), "articles": articles}
        c_set("rbi", {"f": feed_type}, result, ttl=3600)
        return result
    except Exception as ex:
        return {"error": str(ex), "source": "RBI", "feed": feed_type}


async def rbi_key_rates() -> dict:
    """Scrape RBI key policy rates."""
    if c := c_get("rbi_rates", {}): return c
    try:
        r    = await fetch("https://rbi.org.in/Scripts/bs_viewcontent.aspx?Id=156")
        soup = BeautifulSoup(r.text, "lxml")
        rates = {}
        for row in soup.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) >= 2:
                name  = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                if name and value and len(name) < 60:
                    rates[name] = value
        result = {"source": "RBI", "rates": rates}
        c_set("rbi_rates", {}, result, ttl=3600)
        return result
    except Exception as ex:
        return {"error": str(ex), "source": "RBI"}


# ─────────────────────────────────────────────────────────────────────────────
# india.gov.in — National Portal
# ─────────────────────────────────────────────────────────────────────────────

async def india_portal_news() -> dict:
    """Latest news from india.gov.in national portal."""
    if c := c_get("india_gov", {}): return c
    try:
        r    = await fetch("https://india.gov.in/news")
        soup = BeautifulSoup(r.text, "lxml")
        items = []
        for a in soup.find_all("a", href=re.compile(r"(news|article)")):
            text = a.get_text(strip=True)
            if text and len(text) > 15:
                href = a["href"]
                items.append({
                    "title": text,
                    "url":   "https://india.gov.in" + href if href.startswith("/") else href,
                    "source": "india.gov.in",
                })
        result = {"source": "india.gov.in", "count": len(items), "items": items[:30]}
        c_set("india_gov", {}, result, ttl=3600)
        return result
    except Exception as ex:
        return {"error": str(ex), "source": "india.gov.in"}


# ─────────────────────────────────────────────────────────────────────────────
# SEBI
# ─────────────────────────────────────────────────────────────────────────────

SEBI_RSS = {
    "circulars":     "https://www.sebi.gov.in/sebirss.aspx?id=circulars",
    "press_releases":"https://www.sebi.gov.in/sebirss.aspx?id=press_releases",
    "orders":        "https://www.sebi.gov.in/sebirss.aspx?id=orders",
    "notices":       "https://www.sebi.gov.in/sebirss.aspx?id=notices",
}

async def sebi_get(feed_type: str = "circulars") -> dict:
    """Get SEBI circulars, press releases, orders, notices."""
    feed_url = SEBI_RSS.get(feed_type, SEBI_RSS["circulars"])
    if c := c_get("sebi", {"f": feed_type}): return c
    try:
        from utils.session import fetch as _fetch
        r    = await _fetch(feed_url, accept="application/rss+xml,*/*")
        root = ET.fromstring(r.text)
        ch   = root.find("channel")
        items_xml = ch.findall("item") if ch else root.findall(".//item")
        articles = []
        for item in items_xml:
            def _t(tag):
                el = item.find(tag)
                return (el.text or "").strip() if el is not None else ""
            articles.append({
                "title":     _t("title"),
                "url":       _t("link"),
                "published": _t("pubDate"),
                "source":    "SEBI",
                "type":      feed_type.replace("_", " ").title(),
            })
        result = {"source": "SEBI", "feed": feed_type, "count": len(articles), "articles": articles}
        c_set("sebi", {"f": feed_type}, result, ttl=3600)
        return result
    except Exception as ex:
        return {"error": str(ex), "source": "SEBI"}
