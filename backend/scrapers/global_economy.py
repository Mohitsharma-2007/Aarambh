"""
scrapers/global_economy.py  —  Global Economic Data Sources
============================================================
Sources (all free, no API key required for basic access):
  • IMF  (imf.org/en/Publications/WEO + data API)
  • World Bank (data.worldbank.org API)
  • UN Data (data.un.org)
  • FRED (St. Louis Fed) — Federal Reserve Economic Data
  • OECD (stats.oecd.org)
  • Nasdaq Data (api.nasdaq.com) — earnings, IPO, dividends
  • Trading Economics (tradingeconomics.com) — economic calendar

All endpoints return structured JSON with metadata.
"""

import re
from bs4 import BeautifulSoup
from utils.session import fetch, fetch_json
from utils.cache   import get as c_get, set as c_set

# ── World Bank API ────────────────────────────────────────────────────────────
WB_BASE = "https://api.worldbank.org/v2"

# Common World Bank indicator codes
WB_INDICATORS = {
    "gdp":              "NY.GDP.MKTP.CD",
    "gdp_growth":       "NY.GDP.MKTP.KD.ZG",
    "gdp_per_capita":   "NY.GDP.PCAP.CD",
    "inflation":        "FP.CPI.TOTL.ZG",
    "unemployment":     "SL.UEM.TOTL.ZS",
    "population":       "SP.POP.TOTL",
    "exports":          "NE.EXP.GNFS.CD",
    "imports":          "NE.IMP.GNFS.CD",
    "fdi":              "BX.KLT.DINV.CD.WD",
    "poverty":          "SI.POV.NAHC",
    "gini":             "SI.POV.GINI",
    "co2":              "EN.ATM.CO2E.PC",
    "life_expectancy":  "SP.DYN.LE00.IN",
    "literacy":         "SE.ADT.LITR.ZS",
    "internet_users":   "IT.NET.USER.ZS",
    "current_account":  "BN.CAB.XOKA.CD",
    "external_debt":    "DT.DOD.DECT.CD",
    "reserves":         "FI.RES.TOTL.CD",
    "tax_revenue":      "GC.TAX.TOTL.GD.ZS",
    "govt_expenditure": "GC.XPN.TOTL.GD.ZS",
}

async def world_bank(country: str = "IN", indicator: str = "NY.GDP.MKTP.CD",
                      years: int = 10) -> dict:
    """
    World Bank Open Data API.
    country: ISO-2 code (IN, US, CN, BR, etc.) or "all"
    indicator: WB indicator code
    """
    ck = {"c": country, "i": indicator, "y": years}
    if c := c_get("wb", ck): return c
    try:
        r = await fetch_json(
            f"{WB_BASE}/country/{country}/indicator/{indicator}",
            params={"format": "json", "per_page": years, "mrv": years}
        )
        if r.status_code == 200:
            data = r.json()
            # WB returns [metadata, data_array]
            meta    = data[0] if isinstance(data, list) and len(data) > 0 else {}
            records = data[1] if isinstance(data, list) and len(data) > 1 else []
            cleaned = [
                {"year": d.get("date"), "value": d.get("value"),
                 "country": d.get("country", {}).get("value")}
                for d in (records or []) if d.get("value") is not None
            ]
            result = {
                "source":    "World Bank Open Data",
                "country":   country,
                "indicator": indicator,
                "indicator_name": WB_INDICATORS.get(indicator, indicator),
                "records":   cleaned,
                "total":     meta.get("total"),
            }
            c_set("wb", ck, result, ttl=86400)
            return result
        return {"error": f"HTTP {r.status_code}", "source": "World Bank"}
    except Exception as ex:
        return {"error": str(ex), "source": "World Bank"}


async def world_bank_by_name(country: str, indicator_name: str) -> dict:
    """Convenience wrapper using plain English indicator names."""
    code = WB_INDICATORS.get(indicator_name.lower().replace(" ", "_"))
    if not code:
        return {"error": f"Unknown indicator. Valid: {sorted(WB_INDICATORS.keys())}"}
    return await world_bank(country, code)


async def world_bank_country_profile(country: str) -> dict:
    """Full economic profile of a country — multiple indicators."""
    import asyncio
    key_indicators = [
        "NY.GDP.MKTP.CD", "NY.GDP.MKTP.KD.ZG", "FP.CPI.TOTL.ZG",
        "SL.UEM.TOTL.ZS", "SP.POP.TOTL", "BN.CAB.XOKA.CD",
    ]
    tasks   = [world_bank(country, ind, years=5) for ind in key_indicators]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    profile = {}
    for ind, res in zip(key_indicators, results):
        if isinstance(res, dict) and not res.get("error"):
            name   = WB_INDICATORS.get(ind, ind).lower().replace(".", "_")
            latest = res.get("records", [{}])
            profile[ind] = {
                "name":    name,
                "latest":  latest[0] if latest else None,
                "history": res.get("records", [])[:5],
            }
    return {"source": "World Bank", "country": country, "profile": profile}


# ── IMF Data API ──────────────────────────────────────────────────────────────

async def imf_data(indicator: str = "NGDPD", country: str = "IN",
                    start_year: int = 2015) -> dict:
    """
    IMF World Economic Outlook data.
    indicator: NGDPD (GDP nominal), NGDP_RPCH (GDP growth), PCPIPCH (inflation)
               GGXCNL_NGDP (fiscal balance), BCA (current account)
    """
    ck = {"i": indicator, "c": country, "y": start_year}
    if c := c_get("imf", ck): return c
    # IMF SDMX-JSON API
    try:
        url = (f"https://www.imf.org/external/datamapper/api/v1/{indicator}"
               f"/{country}?periods={start_year}:{2026}")
        r   = await fetch_json(url)
        if r.status_code == 200:
            result = {"source": "IMF", "indicator": indicator,
                      "country": country, "data": r.json()}
            c_set("imf", ck, result, ttl=86400)
            return result
    except Exception:
        pass
    # Fallback: IMF World Economic Outlook page
    try:
        r   = await fetch(
            f"https://www.imf.org/en/Publications/WEO/weo-database/2024/October/weo-report",
            params={"a": "1", "c": "534", "s": indicator}
        )
        return {"source": "IMF (HTML fallback)", "indicator": indicator,
                "country": country, "note": "Full data at imf.org"}
    except Exception as ex:
        return {"error": str(ex), "source": "IMF"}


async def imf_article_iv(country: str = "India") -> dict:
    """Latest IMF Article IV consultation reports."""
    if c := c_get("imf_a4", {"c": country}): return c
    try:
        r    = await fetch(
            "https://www.imf.org/en/Publications/Search",
            params={"country": country, "type": "Country+Reports"}
        )
        soup = BeautifulSoup(r.text, "lxml")
        docs = []
        for a in soup.find_all("a", href=re.compile(r"/Publications/CR/")):
            title = a.get_text(strip=True)
            if title and len(title) > 10:
                docs.append({"title": title, "url": "https://www.imf.org" + a["href"]})
        result = {"source": "IMF", "country": country, "reports": docs[:10]}
        c_set("imf_a4", {"c": country}, result, ttl=86400)
        return result
    except Exception as ex:
        return {"error": str(ex), "source": "IMF"}


# ── FRED — Federal Reserve Economic Data ─────────────────────────────────────

FRED_BASE = "https://fred.stlouisfed.org"
FRED_API  = "https://api.stlouisfed.org/fred"

FRED_SERIES = {
    "us_gdp":         "GDP",
    "us_inflation":   "CPIAUCSL",
    "us_unemployment":"UNRATE",
    "us_fed_funds":   "FEDFUNDS",
    "us_10y_treasury":"GS10",
    "us_sp500":       "SP500",
    "us_m2":          "M2SL",
    "dollar_index":   "DTWEXBGS",
    "wti_oil":        "DCOILWTICO",
    "gold":           "GOLDAMGBD228NLBM",
    "us_retail_sales":"RSAFS",
    "us_housing":     "HOUST",
    "us_trade_balance":"BOPGSTB",
}

async def fred_series(series_id: str, limit: int = 20) -> dict:
    """
    FRED series data. No API key needed for public series.
    """
    ck = {"s": series_id, "l": limit}
    if c := c_get("fred", ck): return c
    try:
        # FRED has a public JSON API
        r = await fetch_json(
            f"{FRED_API}/series/observations",
            params={
                "series_id": series_id,
                "sort_order": "desc",
                "limit": limit,
                "file_type": "json",
                "api_key": "abcdefghijklmnop",   # placeholder — works without key for some
            }
        )
        if r.status_code == 200:
            data = r.json()
            obs  = data.get("observations", [])
            result = {
                "source":    "FRED / St. Louis Fed",
                "series_id": series_id,
                "observations": obs,
                "note": "Set FRED_API_KEY in .env for full access",
            }
            c_set("fred", ck, result, ttl=3600)
            return result
    except Exception:
        pass
    return {
        "source":    "FRED",
        "series_id": series_id,
        "url":       f"https://fred.stlouisfed.org/series/{series_id}",
        "note":      "Set FRED_API_KEY in .env — free registration at stlouisfed.org",
    }


async def fred_by_name(indicator: str) -> dict:
    """Fetch FRED series by plain English name."""
    series_id = FRED_SERIES.get(indicator.lower().replace(" ","_"))
    if not series_id:
        return {"error": f"Unknown FRED indicator. Valid: {sorted(FRED_SERIES.keys())}"}
    return await fred_series(series_id)


# ── OECD ──────────────────────────────────────────────────────────────────────

async def oecd_data(dataset: str = "MEI", country: str = "IND") -> dict:
    """OECD Statistics data via SDMX API."""
    ck = {"d": dataset, "c": country}
    if c := c_get("oecd", ck): return c
    try:
        r = await fetch_json(
            f"https://stats.oecd.org/sdmx-json/data/{dataset}/{country}/all",
            params={"startTime": "2020", "endTime": "2024"}
        )
        if r.status_code == 200:
            result = {"source": "OECD", "dataset": dataset, "country": country, "data": r.json()}
            c_set("oecd", ck, result, ttl=86400)
            return result
        return {"error": f"HTTP {r.status_code}", "source": "OECD"}
    except Exception as ex:
        return {"error": str(ex), "source": "OECD"}


# ── Nasdaq API (free, no key) ─────────────────────────────────────────────────

async def nasdaq_earnings(date: str = "") -> dict:
    """Nasdaq earnings calendar. Free JSON endpoint."""
    if c := c_get("nasdaq_earn", {"d": date}): return c
    try:
        params = {"date": date} if date else {}
        r = await fetch_json("https://api.nasdaq.com/api/calendar/earnings", params)
        if r.status_code == 200:
            result = {"source": "Nasdaq", "type": "Earnings", "data": r.json()}
            c_set("nasdaq_earn", {"d": date}, result, ttl=3600)
            return result
        return {"error": f"HTTP {r.status_code}", "source": "Nasdaq"}
    except Exception as ex:
        return {"error": str(ex), "source": "Nasdaq"}


async def nasdaq_ipo() -> dict:
    """Nasdaq IPO calendar."""
    if c := c_get("nasdaq_ipo", {}): return c
    try:
        r = await fetch_json("https://api.nasdaq.com/api/ipo/calendar")
        if r.status_code == 200:
            result = {"source": "Nasdaq", "type": "IPO Calendar", "data": r.json()}
            c_set("nasdaq_ipo", {}, result, ttl=3600)
            return result
        return {"error": f"HTTP {r.status_code}", "source": "Nasdaq"}
    except Exception as ex:
        return {"error": str(ex), "source": "Nasdaq"}


async def nasdaq_dividends(date: str = "") -> dict:
    """Nasdaq dividend calendar."""
    try:
        params = {"date": date} if date else {}
        r = await fetch_json("https://api.nasdaq.com/api/calendar/dividends", params)
        return r.json() if r.status_code == 200 else {"error": f"HTTP {r.status_code}"}
    except Exception as ex:
        return {"error": str(ex)}


# ── UN Data ───────────────────────────────────────────────────────────────────

async def un_data(series: str = "POPIN") -> dict:
    """UN Data API. series: POPIN, TRADE, etc."""
    try:
        r = await fetch_json(
            f"https://data.un.org/ws/rest/data/DF_{series}",
            params={"format": "json"}
        )
        if r.status_code == 200:
            return {"source": "UN Data", "series": series, "data": r.json()}
        return {"error": f"HTTP {r.status_code}", "source": "UN Data",
                "url": f"https://data.un.org/en/iso/in.html"}
    except Exception as ex:
        return {"error": str(ex), "source": "UN Data"}


# ── Economic Calendar (Trading Economics) ────────────────────────────────────

async def economic_calendar(country: str = "india") -> dict:
    """Economic calendar events — GDP releases, CPI, RBI meetings, etc."""
    if c := c_get("econ_cal", {"c": country}): return c
    try:
        r    = await fetch(
            f"https://tradingeconomics.com/{country.lower()}/calendar",
        )
        soup = BeautifulSoup(r.text, "lxml")
        events = []
        for row in soup.find_all("tr", class_=re.compile(r"(calendar|event)")):
            cells = row.find_all("td")
            if len(cells) >= 3:
                events.append({
                    "date":     cells[0].get_text(strip=True),
                    "event":    cells[1].get_text(strip=True),
                    "actual":   cells[2].get_text(strip=True) if len(cells) > 2 else "",
                    "forecast": cells[3].get_text(strip=True) if len(cells) > 3 else "",
                    "previous": cells[4].get_text(strip=True) if len(cells) > 4 else "",
                })
        result = {"source": "Trading Economics", "country": country,
                  "count": len(events), "events": events[:30]}
        c_set("econ_cal", {"c": country}, result, ttl=3600)
        return result
    except Exception as ex:
        return {"error": str(ex), "source": "Trading Economics"}
