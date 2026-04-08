"""
scrapers/google_finance.py  —  Battle-hardened Google Finance scraper
======================================================================
Google Finance is a server-side rendered page (no JS required).
All data lives in the HTML in multiple forms. We use 5 strategies:

  S1 → data-* HTML attributes  (most stable, rarely changes)
  S2 → JSON blobs inside AF_initDataCallback() script tags
  S3 → Structured JSON-LD  <script type="application/ld+json">
  S4 → CSS class selectors  (falls back across known class variants)
  S5 → Plain text regex      (last resort — always returns something)

Network
  Host     : www.google.com   Port: 443   HTTPS/TLS-1.3
  Endpoints:
    /finance                         → overview / homepage
    /finance/quote/{TICKER}:{EXCH}   → single stock
    /finance/markets/{section}       → market section
  Query params: hl=en  (force English)
"""

import re, json, asyncio
from typing import Any, Optional
from bs4 import BeautifulSoup, Tag
from auth.auth_session import google_fetch
from utils.cache   import get as c_get, set as c_set

BASE = "https://www.google.com/finance"

# ─── HTML helpers ─────────────────────────────────────────────────────────────

def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")

def _txt(el: Optional[Tag]) -> str:
    return el.get_text(" ", strip=True) if el else ""

# ─── Strategy 1: data-* attribute extraction ──────────────────────────────────

def _s1_data_attrs(soup: BeautifulSoup) -> dict:
    """
    Most reliable. Google bakes price + change into data-* attributes
    on container divs — these don't change with style refactors.
    """
    out: dict = {}
    target_attrs = {
        "data-last-price":              "price",
        "data-prev-close":              "prev_close",
        "data-last-normal-market-price":"after_hours_price",
        "data-currency-code":           "currency",
        "data-entity-id":               "entity_id",
        "data-most-searched":           "most_searched",
    }
    for attr, key in target_attrs.items():
        el = soup.find(attrs={attr: True})
        if el:
            out[key] = el.get(attr, "").strip()

    # Change and percent-change live in the same element set
    change_els = soup.find_all(class_=re.compile(
        r"(WlRRw|P2Luy|NydbP|Pcvtbt|JwB6zf|LRHKLb|oSXcfd|kf1m0)"
    ))
    vals = [_txt(e) for e in change_els if _txt(e)]
    if vals:
        out["change"]         = vals[0] if vals else None
        out["change_percent"] = next((v for v in vals if "%" in v), None)

    return out

# ─── Strategy 2: AF_initDataCallback JSON blobs ───────────────────────────────

_AF_RE  = re.compile(r'AF_initDataCallback\(\{[^}]*?data:\s*(\[.*?\])\s*\}', re.S)
_WIZ_RE = re.compile(r'window\.__WIZ_DATA__\s*=\s*(\{.*?\});\s*</script>', re.S)

def _try_json(text: str) -> Any:
    try:    return json.loads(text)
    except: return None

def _deep_find(obj: Any, pred, depth: int = 0) -> list:
    """Recursively collect all values matching pred()."""
    if depth > 12:
        return []
    results = []
    if pred(obj):
        results.append(obj)
    if isinstance(obj, dict):
        for v in obj.values():
            results += _deep_find(v, pred, depth+1)
    elif isinstance(obj, list):
        for v in obj:
            results += _deep_find(v, pred, depth+1)
    return results

def _s2_json_blobs(html: str) -> dict:
    """
    Google embeds multiple AF_initDataCallback() calls in <script> tags.
    Each contains a nested array with price, volume, market cap, etc.
    We scan all of them and collect every number > 0.
    """
    out: dict = {}
    for m in _AF_RE.finditer(html):
        blob = _try_json(m.group(1))
        if not blob:
            continue
        # Price-like numbers (positive floats)
        nums = _deep_find(blob, lambda x: isinstance(x, (int, float)) and x > 0)
        if nums and "price" not in out:
            # The first large-ish number is usually the price
            prices = sorted(set(nums))
            out["_raw_numbers"] = prices[:20]   # expose for debugging

        # String values that look like prices/percentages
        strs = _deep_find(blob, lambda x: isinstance(x, str) and len(x) < 30)
        percent = [s for s in strs if "%" in s]
        if percent and "change_percent" not in out:
            out["change_percent_blob"] = percent[0]

    return out

# ─── Strategy 3: JSON-LD structured data ─────────────────────────────────────

def _s3_json_ld(soup: BeautifulSoup) -> dict:
    """
    Some Google Finance pages include <script type="application/ld+json">
    with StockQuote / FinancialProduct schema markup.
    """
    out: dict = {}
    for tag in soup.find_all("script", type="application/ld+json"):
        blob = _try_json(tag.string or "")
        if not blob:
            continue
        if isinstance(blob, list):
            blob = blob[0] if blob else {}
        t = blob.get("@type", "")
        if any(k in t for k in ("Stock", "Finance", "Quote", "Price")):
            out.update({
                "name":        blob.get("name"),
                "description": blob.get("description"),
                "price_ld":    blob.get("price"),
                "currency_ld": blob.get("priceCurrency"),
                "url_ld":      blob.get("url"),
            })
    return {k: v for k, v in out.items() if v}

# ─── Strategy 4: CSS class selectors (with multiple fallbacks) ────────────────

# Google changes these regularly — we keep a list of all known variants
_PRICE_CLASSES = [
    "YMlKec", "fxKbKc", "IsqQVc", "ln5Gre", "wT3VGc",
    "NprOob", "tw-data-table-cell-value",
]
_NAME_CLASSES  = [
    "zzDege", "PrDSKc", "tDjLGe", "Heui5b", "d3O3Hb", "VfPpkd-WsjYwc",
]
_CHANGE_CLASSES = [
    "JwB6zf", "P2Luy", "WlRRw", "kf1m0", "oSXcfd", "LRHKLb",
]
_ABOUT_CLASSES = [
    "bLLb2d", "LPMaTe", "Yfwt5", "NCWLUp", "WwI8Hb",
]

def _first_text(soup: BeautifulSoup, classes: list[str]) -> Optional[str]:
    for cls in classes:
        el = soup.find(class_=cls)
        if el and _txt(el):
            return _txt(el)
    return None

def _s4_css(soup: BeautifulSoup) -> dict:
    out: dict = {}
    if p := _first_text(soup, _PRICE_CLASSES):  out["price_css"]  = p
    if n := _first_text(soup, _NAME_CLASSES):   out["name"]       = n
    if c := _first_text(soup, _CHANGE_CLASSES): out["change_css"] = c
    if a := _first_text(soup, _ABOUT_CLASSES):  out["about"]      = a[:800]

    # Key stats table (Market Cap, P/E, 52-wk range…)
    stats: dict = {}
    # Known stat row patterns
    for row in soup.find_all("div", class_=re.compile(r"(P6K39c|gyFHrc|XbFb5c|rcom-data)")):
        label_el = row.find(class_=re.compile(r"(mfs7Fc|ugxiwe|rcom-label)"))
        value_el = row.find(class_=re.compile(r"(P6K39c|isqDM|JwB6zf|NprOob|nMAsvb)"))
        if label_el and value_el:
            label = _txt(label_el)
            value = _txt(value_el)
            if label and value and label != value:
                stats[label] = value

    # Also try definition-list patterns
    for dl in soup.find_all("ul", class_=re.compile(r"(COaKTb|DMuAy|haONsb)")):
        items = dl.find_all("li")
        for li in items:
            spans = li.find_all("span")
            if len(spans) >= 2:
                stats[_txt(spans[0])] = _txt(spans[1])

    if stats:
        out["key_stats"] = stats

    return {k: v for k, v in out.items() if v}

# ─── Strategy 5: Regex text mining ───────────────────────────────────────────

def _s5_regex(html: str, ticker: str) -> dict:
    """
    Pure text / regex extraction — always returns price + company name
    even when DOM structure changes completely.
    """
    out: dict = {}
    txt = re.sub(r"<[^>]+>", " ", html)   # strip all tags

    # Price pattern: digits with optional comma and 1–4 decimal places
    price_pats = [
        rf"{re.escape(ticker)}\s*[:\-]?\s*\$?([\d,]+\.\d{{1,4}})",
        r"Current price[:\s]+\$?([\d,]+\.\d{1,4})",
        r'"price"\s*:\s*"?([\d.]+)"?',
        r'"regularMarketPrice"\s*:\s*\{[^}]*?"raw"\s*:\s*([\d.]+)',
    ]
    for pat in price_pats:
        m = re.search(pat, html, re.I)
        if m and "price_re" not in out:
            out["price_re"] = m.group(1)

    # Percent change
    pct = re.search(r'([+-]?\d+\.?\d*)\s*%', txt)
    if pct:
        out["change_percent_re"] = pct.group(0)

    return out

# ─── News extraction ──────────────────────────────────────────────────────────

def _extract_news(soup: BeautifulSoup) -> list[dict]:
    news = []
    seen = set()
    for article in soup.find_all(
        "div", class_=re.compile(r"(z4rs2b|yY3Lee|Yfwt5|UwIKyb|gyrT2|RoEYhd)")
    ):
        headline_el = article.find(class_=re.compile(r"(Yfwt5|Chdh3|JtKRv|F9yfQ)"))
        source_el   = article.find(class_=re.compile(r"(sfyJob|wgXBHd|bfd7rn)"))
        time_el     = article.find("time")
        link_el     = article.find("a", href=True)

        headline = _txt(headline_el) or _txt(article.find("h3")) or _txt(article.find("h4"))
        if not headline or headline in seen:
            continue
        seen.add(headline)

        url = None
        if link_el:
            href = link_el["href"]
            url  = href if href.startswith("http") else "https://www.google.com" + href

        news.append({
            "headline":  headline,
            "source":    _txt(source_el),
            "published": time_el.get("datetime") if time_el else None,
            "url":       url,
        })

    return news[:15]

# ─── Market page items ────────────────────────────────────────────────────────

def _extract_market_items(soup: BeautifulSoup) -> list[dict]:
    """
    Enhanced market item extraction with multiple fallback strategies.
    Handles both authenticated and non-authenticated page structures.
    """
    items = []
    seen  = set()

    # Strategy A — Enhanced data-row-index cards (primary method)
    for row in soup.find_all(attrs={"data-row-index": True}):
        ticker_el = row.find(class_=re.compile(r"(COaKTb|ZvmM7|SxcTic)"))
        name_el   = row.find(class_=re.compile(r"(ZvmM7|tDjLGe|Heui5b|d3O3Hb|oWDzCe)"))
        price_el  = row.find(attrs={"data-last-price": True}) or \
                    row.find(class_=re.compile(r"(YMlKec|fxKbKc|NprOob)"))
        chg_el    = row.find(class_=re.compile(r"(P2Luy|JwB6zf|WlRRw|LRHKLb)"))
        link_el   = row.find("a", href=True)

        ticker = _txt(ticker_el)
        name   = _txt(name_el) if name_el else ticker
        if not ticker or ticker in seen:
            continue
        seen.add(ticker)

        price = (price_el.get("data-last-price") if price_el and hasattr(price_el, "get") else None) \
                or _txt(price_el)
        
        # Enhanced change extraction
        change = _txt(chg_el)
        if not change and price_el:
            # Try to extract change from data attributes
            change = price_el.get("data-change", "") or price_el.get("data-percent-change", "")
        
        items.append({
            "ticker": ticker,
            "name":   name,
            "price":  price,
            "change": change,
            "url":    ("https://www.google.com" + link_el["href"]) if link_el else None,
        })

    # Strategy B — Enhanced anchor cards with price children (fallback)
    if len(items) < 10:  # Only use fallback if we didn't get enough items
        for a in soup.find_all("a", href=re.compile(r"/finance/(quote|markets)")):
            name_el  = a.find(class_=re.compile(r"(ZvmM7|tDjLGe|KpDZzb)"))
            price_el = a.find(attrs={"data-last-price": True}) or \
                       a.find(class_=re.compile(r"(YMlKec|fxKbKc)"))
            chg_el   = a.find(class_=re.compile(r"(P2Luy|JwB6zf|kf1m0)"))
            name     = _txt(name_el) or _txt(a)[:40]
            if not name or name in seen:
                continue
            seen.add(name)
            
            price = (price_el.get("data-last-price") if price_el and hasattr(price_el, "get") else None) \
                    or _txt(price_el)
            change = _txt(chg_el)
            
            items.append({
                "name":   name,
                "price":  price,
                "change": change,
                "url":    "https://www.google.com" + a["href"],
            })

    # Strategy C — Table row extraction (for different page layouts)
    if len(items) < 10:
        for tr in soup.find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) >= 3:
                # Try to identify ticker and price columns
                ticker_cell = None
                price_cell = None
                change_cell = None
                
                # Look for ticker patterns
                for i, cell in enumerate(cells):
                    text = _txt(cell)
                    if re.match(r'^[A-Z]{1,5}$', text) and i < len(cells) - 2:
                        ticker_cell = cell
                        price_cell = cells[i + 1] if i + 1 < len(cells) else None
                        change_cell = cells[i + 2] if i + 2 < len(cells) else None
                        break
                
                if ticker_cell and price_cell:
                    ticker = _txt(ticker_cell)
                    if ticker and ticker not in seen:
                        seen.add(ticker)
                        items.append({
                            "ticker": ticker,
                            "name":   ticker,  # Use ticker as name if no separate name found
                            "price":  _txt(price_cell),
                            "change": _txt(change_cell),
                            "url":    None,
                        })

    return items[:50]  # Limit to 50 items for performance

# ─── Merge all strategies into final clean quote ─────────────────────────────

def _merge_quote(ticker: str, exchange: str, soup: BeautifulSoup, html: str) -> dict:
    s1 = _s1_data_attrs(soup)
    s2 = _s2_json_blobs(html)
    s3 = _s3_json_ld(soup)
    s4 = _s4_css(soup)
    s5 = _s5_regex(html, ticker)

    # Build clean unified response — prefer in order S1 > S4 > S5 for price
    price = (s1.get("price")
             or s4.get("price_css")
             or s5.get("price_re")
             or s3.get("price_ld"))

    change = (s1.get("change")
              or s4.get("change_css"))

    change_pct = (s1.get("change_percent")
                  or s2.get("change_percent_blob")
                  or s5.get("change_percent_re"))

    return {
        "ticker":           ticker.upper(),
        "exchange":         exchange.upper(),
        "company_name":     s4.get("name") or s3.get("name"),
        "price":            price,
        "currency":         s1.get("currency") or s3.get("currency_ld") or "USD",
        "change":           change,
        "change_percent":   change_pct,
        "prev_close":       s1.get("prev_close"),
        "after_hours_price":s1.get("after_hours_price"),
        "key_stats":        s4.get("key_stats", {}),
        "about":            s4.get("about") or s3.get("description"),
        "news":             _extract_news(soup),
        "data_strategies":  {
            "s1_data_attrs": bool(s1.get("price")),
            "s2_json_blobs": bool(s2),
            "s3_json_ld":    bool(s3),
            "s4_css":        bool(s4.get("price_css")),
            "s5_regex":      bool(s5.get("price_re")),
        },
        "source_url": f"https://www.google.com/finance/quote/{ticker.upper()}:{exchange.upper()}",
    }

# ─── Public API ───────────────────────────────────────────────────────────────

KNOWN_EXCHANGES = {
    # US
    "NASDAQ","NYSE","NYSEARCA","NYSEAMERICAN","OTC","OTCMKTS",
    # India
    "NSE","BSE",
    # Europe
    "LON","FRA","EPA","AMS","STO","VIE","SWX","BIT","BME",
    # Asia
    "TYO","HKG","SHA","SHE","KRX","NSI","SGX","ASX",
    # Others
    "TSX","BVMF","BCBA",
}

async def get_quote(ticker: str, exchange: str = "NASDAQ") -> dict:
    """
    Enhanced stock quote fetch with better error handling and retry logic.
    Tries 5 independent extraction strategies — returns whichever works.
    """
    ticker   = ticker.upper().strip()
    exchange = exchange.upper().strip()
    ck       = {"t": ticker, "e": exchange}
    if cached := c_get("gf_q", ck): 
        return cached

    url  = f"{BASE}/quote/{ticker}:{exchange}"
    
    # Enhanced retry logic
    for attempt in range(3):
        try:
            resp = await google_fetch(url, params={"hl": "en"})
            
            if resp.status_code == 200:
                # Check if we got a valid page
                if "Sign in" in resp.text or "accounts.google.com" in resp.text:
                    if attempt < 2:
                        resp = await google_fetch(url, params={"hl": "en", "gl": "US"})
                        continue
                    else:
                        return {"error": "Authentication required - Google is blocking requests", "ticker": ticker, "exchange": exchange}
                
                soup   = _soup(resp.text)
                result = _merge_quote(ticker, exchange, soup, resp.text)
                
                # Check if we got meaningful data
                if result.get("price") or result.get("name"):
                    c_set("gf_q", ck, result, ttl=60)  # 1 minute cache
                    return result
                else:
                    if attempt < 2:
                        continue
                    else:
                        return {"error": "No quote data found - ticker may be invalid", "ticker": ticker, "exchange": exchange}
            
            elif resp.status_code in (429, 503):
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    return {"error": f"Rate limited - HTTP {resp.status_code}", "ticker": ticker, "exchange": exchange}
            else:
                return {
                    "error": f"HTTP {resp.status_code}",
                    "ticker": ticker,
                    "exchange": exchange,
                    "url": url,
                    "hint": "Check ticker/exchange combo. Example: AAPL:NASDAQ, RELIANCE:NSE",
                }
                
        except Exception as ex:
            if attempt < 2:
                await asyncio.sleep(1)
                continue
            else:
                return {"error": str(ex), "ticker": ticker, "exchange": exchange}

    return {"error": "Failed after multiple attempts", "ticker": ticker, "exchange": exchange}


async def get_market(section: str = "indexes") -> dict:
    """
    Enhanced market section fetch with better error handling and retry logic.
    Sections: indexes | crypto | currencies | futures | most-active | gainers | losers | etfs
    """
    VALID = {
        "indexes","crypto","currencies","futures",
        "most-active","gainers","losers","etfs",
    }
    section = section.lower().replace("_", "-")
    if section not in VALID:
        return {"error": f"Invalid section. Choose: {sorted(VALID)}"}

    ck = {"s": section}
    if cached := c_get("gf_mkt", ck): 
        return cached

    url  = f"{BASE}/markets/{section}"
    
    # Enhanced retry logic with different approaches
    for attempt in range(3):
        try:
            resp = await google_fetch(url, params={"hl": "en"})
            
            if resp.status_code == 200:
                # Check if we got a valid page (not login/redirect page)
                if "Sign in" in resp.text or "accounts.google.com" in resp.text:
                    if attempt < 2:
                        # Try with different parameters
                        resp = await google_fetch(url, params={"hl": "en", "gl": "US"})
                        continue
                    else:
                        return {"error": "Authentication required - Google is blocking requests", "section": section}
                
                soup  = _soup(resp.text)
                items = _extract_market_items(soup)
                
                # If we got items, return success
                if items:
                    result = {
                        "section":    section,
                        "title":      soup.find("h1").get_text() if soup.find("h1") else section.replace("-", " ").title(),
                        "count":      len(items),
                        "items":      items,
                        "source_url": url,
                    }
                    c_set("gf_mkt", ck, result, ttl=120)  # 2 minute cache
                    return result
                else:
                    # No items found, might be a different page structure
                    if attempt < 2:
                        continue
                    else:
                        return {"error": "No market data found - page structure may have changed", "section": section}
            
            elif resp.status_code in (429, 503):
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    return {"error": f"Rate limited - HTTP {resp.status_code}", "section": section}
            else:
                return {"error": f"HTTP {resp.status_code}", "section": section, "url": url}
                
        except Exception as ex:
            if attempt < 2:
                await asyncio.sleep(1)
                continue
            else:
                return {"error": str(ex), "section": section}

    return {"error": "Failed after multiple attempts", "section": section}


async def get_overview() -> dict:
    """
    Full market overview — aggregates individual market section pages.
    More reliable than parsing the GF homepage (which changes structure often).
    """
    if cached := c_get("gf_ov", {}): return cached

    SECTIONS = ["indexes", "most-active", "gainers", "losers", "crypto", "currencies"]
    sections: dict = {}
    errors:   list = []

    for sec in SECTIONS:
        try:
            result = await get_market(sec)
            if result.get("items"):
                sections[sec] = result["items"]
            elif result.get("error"):
                errors.append(f"{sec}: {result['error']}")
        except Exception as ex:
            errors.append(f"{sec}: {ex}")

    # Also try homepage for any additional trending items
    try:
        resp = await google_fetch(BASE, params={"hl": "en"})
        if resp.status_code == 200:
            soup = _soup(resp.text)
            # Grab any data-last-price items not already captured
            extra = []
            seen  = {item.get("ticker","") for items in sections.values() for item in items}
            for el in soup.find_all(attrs={"data-last-price": True}):
                ticker_el = el.find(class_=re.compile(r"(COaKTb|ZvmM7|SxcTic)"))
                name_el   = el.find(class_=re.compile(r"(ZvmM7|tDjLGe|Heui5b)"))
                link      = el.find_parent("a", href=True) or el.find("a", href=True)
                ticker    = _txt(ticker_el)
                if ticker and ticker not in seen:
                    seen.add(ticker)
                    extra.append({
                        "ticker": ticker,
                        "name":   _txt(name_el),
                        "price":  el.get("data-last-price"),
                        "url":    "https://www.google.com" + link["href"] if link else None,
                    })
            if extra:
                sections["trending"] = extra
    except Exception:
        pass

    result = {
        "sections":      sections,
        "section_names": list(sections.keys()),
        "total_items":   sum(len(v) for v in sections.values()),
        "errors":        errors,
        "source_url":    BASE,
    }
    c_set("gf_ov", {}, result, ttl=180)
    return result


async def search_gf(query: str) -> dict:
    """
    Search for stocks/ETFs/crypto.
    Strategy 1 → Yahoo Finance search API (most reliable JSON)
    Strategy 2 → Google Search finance tab (HTML parse)
    Strategy 3 → Google Finance direct page links
    """
    ck = {"q": query}
    if cached := c_get("gf_sr", ck): return cached

    results = []
    seen    = set()

    # ── Strategy 1: Yahoo Finance search (always returns clean JSON) ──
    try:
        from scrapers.yahoo_finance import search as yf_search
        yf = await yf_search(query)
        for q in yf.get("quotes", [])[:10]:
            sym  = q.get("symbol","")
            name = q.get("shortname") or q.get("longname") or sym
            key  = sym or name
            if key and key not in seen:
                seen.add(key)
                results.append({
                    "ticker":    sym,
                    "name":      name,
                    "exchange":  q.get("exchange") or q.get("exchDisp"),
                    "type":      q.get("quoteType"),
                    "source":    "yahoo_finance",
                })
    except Exception:
        pass

    # ── Strategy 2: Google Search finance tab ──
    try:
        resp = await fetch(
            "https://www.google.com/search",
            params={"q": f"{query} stock", "tbm": "fin", "hl": "en"},
            domain="google",
        )
        if resp.status_code == 200:
            soup = _soup(resp.text)
            # data-attrid finance panel fields
            for el in soup.find_all(attrs={"data-attrid": re.compile(r"(finance|stock|price|ticker)", re.I)}):
                t = _txt(el)
                if t and t not in seen and 5 < len(t) < 300:
                    seen.add(t)
                    results.append({"text": t[:200], "type": "google_panel",
                                    "source": "google_finance"})
            # Any price-bearing divs
            for div in soup.find_all("div", class_=re.compile(
                r"(WlydOe|SoaBEf|iUVAvc|tF2Cxc|MjjYud)"
            )):
                name_el  = div.find(class_=re.compile(r"(ZvmM7|tDjLGe|DKV0Md|LC20lb)"))
                price_el = div.find(class_=re.compile(r"(YMlKec|fxKbKc|IsqQVc|wT3VGc|ln5Gre)"))
                link_el  = div.find("a", href=True)
                if name_el:
                    name = _txt(name_el)
                    if name and name not in seen and len(name) > 1:
                        seen.add(name)
                        results.append({
                            "name":   name,
                            "price":  _txt(price_el) or None,
                            "url":    link_el["href"] if link_el else None,
                            "source": "google_finance",
                        })
    except Exception:
        pass

    # ── Strategy 3: Google Finance direct search page ──
    if len(results) < 5:
        try:
            resp2 = await google_fetch(BASE, params={"q": query, "hl": "en"})
            if resp2.status_code == 200:
                soup2 = _soup(resp2.text)
                for item in _extract_market_items(soup2):
                    key = item.get("ticker") or item.get("name","")
                    if key and key not in seen:
                        seen.add(key)
                        results.append({**item, "source": "google_finance_direct"})
        except Exception:
            pass

    data = {"query": query, "results": results, "count": len(results)}
    c_set("gf_sr", ck, data, ttl=300)
    return data


async def get_chart(ticker: str, exchange: str = "NASDAQ", window: str = "1Y") -> dict:
    """
    Fetch historical chart data embedded in the quote page.
    window: 1D | 5D | 1M | 6M | YTD | 1Y | 5Y | MAX
    """
    ticker   = ticker.upper()
    exchange = exchange.upper()
    url      = f"{BASE}/quote/{ticker}:{exchange}"

    try:
        resp = await google_fetch(url, params={"hl": "en", "window": window})
    except Exception as ex:
        return {"error": str(ex)}

    if resp.status_code != 200:
        return {"error": f"HTTP {resp.status_code}"}

    # Extract all AF_initDataCallback blobs — chart is nested inside
    blobs = []
    for m in _AF_RE.finditer(resp.text):
        b = _try_json(m.group(1))
        if b: blobs.append(b)

    # Chart data contains timestamps (large unix ints) — find that blob
    chart_blob = None
    for b in blobs:
        ts_candidates = _deep_find(b, lambda x: isinstance(x, int) and x > 1_000_000_000)
        if ts_candidates:
            chart_blob = b
            break

    return {
        "ticker":       ticker,
        "exchange":     exchange,
        "window":       window,
        "blobs_found":  len(blobs),
        "chart_data":   chart_blob,
        "source_url":   url,
    }


async def get_multi_quote(tickers: list[str], exchange: str = "NASDAQ") -> dict:
    """Fetch multiple quotes in sequence."""
    import asyncio as _aio
    results = {}
    for t in tickers[:10]:       # cap at 10
        results[t] = await get_quote(t, exchange)
        await _aio.sleep(0.5)    # polite gap
    return {"quotes": results, "count": len(results)}
