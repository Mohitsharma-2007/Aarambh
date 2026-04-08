"""
scrapers/pib_scraper.py  —  Press Information Bureau (PIB) India
================================================================
URL: https://pib.gov.in

PIB is the nodal agency of the Government of India for information
dissemination. It issues press releases, circulars, policy updates
from all central ministries.

Endpoints:
  /pib/latest              → latest press releases
  /pib/search?q=query      → search releases
  /pib/ministry/{name}     → ministry-specific releases
  /pib/sector/{sector}     → sector-filtered releases
  /pib/document/{id}       → full document with metadata
  /pib/circulars           → circulars only
  /pib/ministries          → list all ministries
"""

import re, xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from utils.session import fetch, fetch_json
from utils.cache   import get as c_get, set as c_set

BASE     = "https://pib.gov.in"
RSS_BASE = "https://pib.gov.in/RssMain.aspx"

# ── All ministry slugs on PIB ─────────────────────────────────────────────────
MINISTRIES = {
    "finance":              "Ministry of Finance",
    "commerce":             "Ministry of Commerce and Industry",
    "agriculture":          "Ministry of Agriculture & Farmers' Welfare",
    "health":               "Ministry of Health & Family Welfare",
    "education":            "Ministry of Education",
    "home":                 "Ministry of Home Affairs",
    "defence":              "Ministry of Defence",
    "external":             "Ministry of External Affairs",
    "petroleum":            "Ministry of Petroleum and Natural Gas",
    "power":                "Ministry of Power",
    "railways":             "Ministry of Railways",
    "textiles":             "Ministry of Textiles",
    "msme":                 "Ministry of Micro, Small and Medium Enterprises",
    "labour":               "Ministry of Labour & Employment",
    "housing":              "Ministry of Housing and Urban Affairs",
    "rural":                "Ministry of Rural Development",
    "tribal":               "Ministry of Tribal Affairs",
    "water":                "Ministry of Jal Shakti",
    "culture":              "Ministry of Culture",
    "tourism":              "Ministry of Tourism",
    "shipping":             "Ministry of Ports, Shipping and Waterways",
    "civil_aviation":       "Ministry of Civil Aviation",
    "electronics":          "Ministry of Electronics and Information Technology",
    "chemicals":            "Ministry of Chemicals and Fertilizers",
    "steel":                "Ministry of Steel",
    "mines":                "Ministry of Mines",
    "coal":                 "Ministry of Coal",
    "new_energy":           "Ministry of New and Renewable Energy",
    "environment":          "Ministry of Environment, Forest and Climate Change",
    "fisheries":            "Ministry of Fisheries, Animal Husbandry & Dairying",
    "food":                 "Ministry of Consumer Affairs, Food & Public Distribution",
    "information":          "Ministry of Information & Broadcasting",
    "law":                  "Ministry of Law & Justice",
    "corporate":            "Ministry of Corporate Affairs",
    "science":              "Ministry of Science & Technology",
    "statistics":           "Ministry of Statistics & Programme Implementation",
    "sports":               "Ministry of Youth Affairs & Sports",
    "social_justice":       "Ministry of Social Justice and Empowerment",
    "pmu":                  "Prime Minister's Office",
    "niti":                 "NITI Aayog",
    "rbi":                  "Reserve Bank of India",
    "sebi":                 "SEBI",
}

# ── Sector → ministry mapping ─────────────────────────────────────────────────
SECTOR_MINISTRIES = {
    "agriculture":             ["agriculture", "fisheries", "rural"],
    "finance":                 ["finance", "rbi", "sebi", "corporate"],
    "health":                  ["health"],
    "education":               ["education"],
    "defence":                 ["defence", "home"],
    "energy":                  ["power", "petroleum", "new_energy", "coal"],
    "commerce":                ["commerce", "msme"],
    "infrastructure":          ["railways", "shipping", "civil_aviation", "housing"],
    "environment":             ["environment", "water"],
    "technology":              ["electronics", "science"],
    "social":                  ["labour", "social_justice", "tribal", "sports"],
}


def _parse_pib_rss(xml_text: str, source_hint: str = "PIB") -> list:
    """Parse PIB RSS feed."""
    articles = []
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
            desc  = BeautifulSoup(_t("description"), "lxml").get_text(" ", strip=True)[:500]
            link  = _t("link") or _t("guid")
            pub   = _t("pubDate")
            articles.append({
                "title":       title,
                "url":         link,
                "published":   pub,
                "summary":     desc,
                "source":      source_hint,
                "type":        _classify_pib(title, desc),
                "ministry":    _extract_ministry(title, desc),
            })
    except ET.ParseError:
        pass
    return articles


def _classify_pib(title: str, desc: str) -> str:
    t = (title + " " + desc).lower()
    if "circular"   in t: return "Circular"
    if "notice"     in t: return "Notice"
    if "scheme"     in t: return "Scheme"
    if "budget"     in t: return "Budget"
    if "policy"     in t: return "Policy"
    if "launch"     in t or "inaugurate" in t: return "Launch/Event"
    if "agreement"  in t or "mou" in t: return "MoU/Agreement"
    if "award"      in t: return "Award"
    if "data"       in t or "statistic" in t: return "Data/Statistics"
    return "Press Release"


def _extract_ministry(title: str, desc: str) -> str:
    text = (title + " " + desc[:300]).lower()
    for key, name in MINISTRIES.items():
        if key.replace("_", " ") in text or name.lower() in text:
            return name
    if "government of india" in text: return "Government of India"
    return "Unknown"


def _parse_pib_html_page(html: str, url: str = "") -> dict:
    """Parse a full PIB press release page."""
    soup   = BeautifulSoup(html, "lxml")
    title  = ""
    body   = ""
    meta   = {}

    # Title
    title_el = (soup.find("div", class_=re.compile(r"(pib-title|ContentDiv|inner-page)")) or
                soup.find("h1") or soup.find("h2"))
    if title_el:
        title = title_el.get_text(strip=True)

    # Date
    date_el = soup.find(class_=re.compile(r"(date|pdate|d-block)"))
    if date_el:
        meta["date"] = date_el.get_text(strip=True)

    # Ministry
    min_el = soup.find(class_=re.compile(r"(ministry|min-name)"))
    if min_el:
        meta["ministry"] = min_el.get_text(strip=True)

    # Body
    body_el = (soup.find("div", id=re.compile(r"(content|body|main)")) or
               soup.find("div", class_=re.compile(r"(content|body|press)")))
    if body_el:
        body = body_el.get_text(" ", strip=True)
    else:
        body = soup.get_text(" ", strip=True)[:5000]

    return {
        "url":       url,
        "title":     title,
        "body":      body[:10000],
        "metadata":  meta,
        "type":      _classify_pib(title, body),
        "source":    "PIB",
    }


# ── Public API ────────────────────────────────────────────────────────────────

async def get_latest(count: int = 30) -> dict:
    """Latest PIB press releases via RSS."""
    if c := c_get("pib_latest", {"c": count}): return c
    try:
        r = await fetch(f"{BASE}/RssMain.aspx",
                        params={"ModId": 6, "RegId": 3, "LangId": 1},
                        accept="application/rss+xml,*/*")
        articles = _parse_pib_rss(r.text)[:count]
    except Exception as ex:
        articles = []

    # Fallback: scrape homepage
    if not articles:
        try:
            r    = await fetch(f"{BASE}/allRel.aspx")
            soup = BeautifulSoup(r.text, "lxml")
            for item in soup.find_all("li", class_=re.compile(r"(press|pib)")):
                a_el = item.find("a", href=True)
                if a_el:
                    articles.append({
                        "title":  a_el.get_text(strip=True),
                        "url":    BASE + a_el["href"] if a_el["href"].startswith("/") else a_el["href"],
                        "source": "PIB",
                        "type":   "Press Release",
                    })
        except Exception:
            pass

    result = {"source": "PIB", "count": len(articles), "articles": articles}
    c_set("pib_latest", {"c": count}, result, ttl=600)
    return result


async def search_pib(query: str, count: int = 20) -> dict:
    """Search PIB press releases."""
    if c := c_get("pib_search", {"q": query}): return c
    try:
        r    = await fetch(
            f"{BASE}/PressReleasePage.aspx",
            params={"PRID": 0, "srchtype": "T", "Value": query, "LangId": 1},
        )
        soup = BeautifulSoup(r.text, "lxml")
        articles = []
        for a in soup.find_all("a", href=re.compile(r"PressReleasePage|prid")):
            text = a.get_text(strip=True)
            href = a["href"]
            if text and len(text) > 10:
                url = BASE + href if href.startswith("/") else href
                articles.append({
                    "title":  text,
                    "url":    url,
                    "source": "PIB",
                    "type":   _classify_pib(text, ""),
                })
    except Exception as ex:
        articles = []

    result = {"query": query, "count": len(articles), "articles": articles[:count]}
    c_set("pib_search", {"q": query}, result, ttl=600)
    return result


async def get_ministry_releases(ministry_key: str, count: int = 20) -> dict:
    """Get PIB releases for a specific ministry."""
    if ministry_key not in MINISTRIES:
        return {"error": f"Unknown ministry. Valid keys: {sorted(MINISTRIES.keys())}"}
    all_releases = await get_latest(100)
    ministry_name = MINISTRIES[ministry_key].lower()
    filtered = [
        a for a in all_releases.get("articles", [])
        if ministry_name in (a.get("ministry","") + a.get("title","") + a.get("summary","")).lower()
    ]
    return {
        "ministry":  MINISTRIES[ministry_key],
        "count":     len(filtered[:count]),
        "articles":  filtered[:count],
    }


async def get_sector_releases(sector: str, count: int = 25) -> dict:
    """Get PIB releases filtered by sector."""
    ministry_keys = SECTOR_MINISTRIES.get(sector.lower(), [])
    if not ministry_keys:
        return {"error": f"Unknown sector. Valid: {sorted(SECTOR_MINISTRIES.keys())}"}
    all_releases = await get_latest(200)
    ministry_names = [MINISTRIES[k].lower() for k in ministry_keys if k in MINISTRIES]
    filtered = [
        a for a in all_releases.get("articles", [])
        if any(mn in (a.get("ministry","") + a.get("title","") + a.get("summary","")).lower()
               for mn in ministry_names)
    ]
    return {"sector": sector, "count": len(filtered[:count]), "articles": filtered[:count]}


async def get_document(url: str) -> dict:
    """Fetch and parse a full PIB document."""
    try:
        r = await fetch(url)
        return _parse_pib_html_page(r.text, url)
    except Exception as ex:
        return {"error": str(ex), "url": url}


async def get_circulars(count: int = 20) -> dict:
    """Get PIB circulars and notifications."""
    all_r = await get_latest(100)
    circulars = [
        a for a in all_r.get("articles", [])
        if a.get("type") in ("Circular","Notice","Policy")
    ]
    return {"type": "Circulars/Notices", "count": len(circulars[:count]),
            "articles": circulars[:count]}
