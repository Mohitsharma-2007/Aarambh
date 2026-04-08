"""
scrapers/google_ai.py  —  Google AI Overview + Finance Knowledge Panel
=======================================================================
Extracts Google's AI-generated summaries from search result pages.
No API key. All data from standard GET requests.

Note: Google AI Overview requires specific queries to trigger.
      Finance queries reliably produce knowledge panels.
"""

import re, json
from bs4 import BeautifulSoup
from utils.session import fetch
from utils.cache   import get as c_get, set as c_set

SEARCH = "https://www.google.com/search"

def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")

def _txt(el) -> str:
    return el.get_text(" ", strip=True) if el else ""

# ─── AI Overview extraction — 4 strategies ───────────────────────────────────

def _extract_ai(html: str) -> dict:
    soup   = _soup(html)
    result = {"found": False, "text": None, "sources": [], "type": None}

    # S1: data-attrid containing AI/SGE/description
    for el in soup.find_all(attrs={"data-attrid": re.compile(
        r"(wa:/description|SGE|ai_overview|AIMode|featured_snippet)",re.I
    )}):
        t = _txt(el)
        if len(t) > 60:
            result.update({"found": True, "text": t[:3000], "type": "data_attrid"})
            break

    # S2: Featured snippet / answer box
    if not result["found"]:
        for cls in ["hgKElc", "LGOjhe", "IZ6rdc", "yDYNvb", "kno-rdesc",
                    "LMRCfc", "g6Lsod", "wDYxhc", "NFQFxe"]:
            el = soup.find(class_=cls)
            if el:
                t = _txt(el)
                if len(t) > 60:
                    result.update({"found": True, "text": t[:3000], "type": f"css_{cls}"})
                    break

    # S3: window.__WIZ_DATA__ JSON blob (SGE/AI Mode)
    if not result["found"]:
        for s in soup.find_all("script"):
            raw = s.string or ""
            if "__WIZ_DATA__" in raw:
                m = re.search(r'__WIZ_DATA__\s*=\s*(\{.*?\});\s*(?:</script>|var )', raw, re.S)
                if m:
                    try:
                        wiz = json.loads(m.group(1))
                        # Find long strings (likely AI-generated paragraph)
                        def _scan(obj, depth=0):
                            if depth > 12: return None
                            if isinstance(obj, str) and 150 < len(obj) < 5000:
                                return obj
                            if isinstance(obj, list):
                                for v in obj:
                                    r = _scan(v, depth+1)
                                    if r: return r
                            if isinstance(obj, dict):
                                for v in obj.values():
                                    r = _scan(v, depth+1)
                                    if r: return r
                            return None
                        found = _scan(wiz)
                        if found:
                            result.update({"found": True, "text": found, "type": "wiz_data"})
                    except Exception:
                        pass
                break

    # S4: Paragraph-rich answer from knowledge graph
    if not result["found"]:
        for el in soup.find_all("div", class_=re.compile(r"(kno-rdesc|SPZz6b|co8aDb|HwtpBd)")):
            t = _txt(el)
            if len(t) > 80:
                result.update({"found": True, "text": t[:3000], "type": "knowledge_graph"})
                break

    # Extract cited sources from all strategies
    for a in soup.find_all("a", href=re.compile(r"^https?://"), class_=re.compile(
        r"(fKDtNb|UWckNb|LBgpqf|VlHyHc|bCOlv|KJDJLb)"
    )):
        txt = _txt(a)
        if txt and len(txt) < 200:
            result["sources"].append({"title": txt, "url": a["href"]})
    result["sources"] = result["sources"][:10]

    return result


def _extract_finance_panel(html: str, ticker: str) -> dict:
    """Extract the stock knowledge panel from Google Search."""
    soup   = _soup(html)
    result = {"ticker": ticker, "fields": {}, "panel_found": False}

    # data-attrid fields (very reliable for finance data)
    FINANCE_ATTRS = {
        "wa:/description":         "description",
        "Stock":                    "stock_info",
        "hw:/collection/finance":  "finance_collection",
    }
    for attr_pat, label in FINANCE_ATTRS.items():
        for el in soup.find_all(attrs={"data-attrid": re.compile(attr_pat, re.I)}):
            t = _txt(el)
            if t:
                result["fields"][label] = t[:500]
                result["panel_found"] = True

    # Price from knowledge panel
    for cls in ["IsqQVc", "wT3VGc", "NprOob", "ln5Gre", "e8fRqf"]:
        el = soup.find(class_=cls)
        if el:
            t = _txt(el)
            if t and any(c.isdigit() for c in t):
                result["price"] = t
                result["panel_found"] = True
                break

    # Company name in panel
    for cls in ["qrShPb", "oHQTuf", "SPZz6b", "DoxwDb", "kno-ecr-pt"]:
        el = soup.find(class_=cls)
        if el:
            t = _txt(el)
            if t and len(t) < 100:
                result["company_name"] = t
                break

    # Key value pairs from knowledge panel
    kv: dict = {}
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) >= 2:
            k = _txt(cells[0])
            v = _txt(cells[1])
            if k and v and len(k) < 50 and len(v) < 100:
                kv[k] = v
    if kv:
        result["table_data"] = kv
        result["panel_found"] = True

    # Related questions
    questions = []
    for q in soup.find_all(class_=re.compile(r"(dnXCYb|kno-ftr-2|LKPcQc|related-question)")):
        t = _txt(q)
        if t and t not in questions: questions.append(t)
    if questions:
        result["related_questions"] = questions[:5]

    return result


# ─── Public API ───────────────────────────────────────────────────────────────

async def get_ai_overview(query: str) -> dict:
    """
    Fetch Google AI Overview / featured snippet for any query.
    Endpoint : GET https://www.google.com/search?q={query}
    Port     : 443
    """
    ck = {"q": query}
    if c := c_get("g_ai", ck): return c

    try:
        r = await fetch(SEARCH, params={"q": query, "hl": "en", "num": "10"},
                        domain="google")
    except Exception as ex:
        return {"error": str(ex), "query": query}

    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}", "query": query}

    ai = _extract_ai(r.text)
    result = {
        "query":        query,
        "has_ai":       ai["found"],
        "ai_type":      ai["type"],
        "summary":      ai["text"],
        "sources":      ai["sources"],
        "note": "AI Overview appears for eligible queries only. "
                "For guaranteed extraction consider using Playwright headless browser.",
    }
    c_set("g_ai", ck, result, ttl=600)
    return result


async def get_finance_summary(ticker: str) -> dict:
    """
    Finance knowledge panel + AI summary for a stock ticker.
    Endpoint : GET https://www.google.com/search?q={ticker}+stock+price
    Port     : 443
    """
    ck = {"t": ticker}
    if c := c_get("g_fs", ck): return c

    query = f"{ticker.upper()} stock price"
    try:
        r = await fetch(SEARCH, params={"q": query, "hl": "en"}, domain="google")
    except Exception as ex:
        return {"error": str(ex), "ticker": ticker}

    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}", "ticker": ticker}

    panel = _extract_finance_panel(r.text, ticker)
    ai    = _extract_ai(r.text)
    result = {"ticker": ticker, "panel": panel, "ai_summary": ai}
    c_set("g_fs", ck, result, ttl=120)
    return result
