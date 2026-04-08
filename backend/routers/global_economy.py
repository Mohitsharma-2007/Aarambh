"""routers/global_economy.py"""
from fastapi import APIRouter, Query, Path
from scrapers.global_economy import (
    world_bank, world_bank_by_name, world_bank_country_profile,
    imf_data, imf_article_iv, fred_series, fred_by_name,
    oecd_data, nasdaq_earnings, nasdaq_ipo, nasdaq_dividends,
    un_data, economic_calendar, WB_INDICATORS, FRED_SERIES
)

router = APIRouter()

# ── World Bank ─────────────────────────────────────────────────────────────
@router.get("/world-bank", summary="World Bank indicator for a country")
async def wb(country: str = Query("IN", description="ISO-2 country code"),
             indicator: str = Query("NY.GDP.MKTP.CD", description="WB indicator code"),
             years: int = Query(10)):
    return await world_bank(country, indicator, years)

@router.get("/world-bank/profile/{country}", summary="Full country economic profile")
async def wb_profile(country: str = Path(..., description="IN|US|CN|BR|DE|GB|JP")):
    return await world_bank_country_profile(country)

@router.get("/world-bank/indicators", summary="All available World Bank indicators")
async def wb_indicators():
    return {"indicators": WB_INDICATORS, "total": len(WB_INDICATORS)}

# ── IMF ────────────────────────────────────────────────────────────────────
@router.get("/imf", summary="IMF World Economic Outlook data")
async def imf(indicator: str = Query("NGDPD", description="NGDPD|NGDP_RPCH|PCPIPCH|GGXCNL_NGDP|BCA"),
              country: str = Query("IN")):
    return await imf_data(indicator, country)

@router.get("/imf/reports/{country}", summary="IMF Article IV reports for a country")
async def imf_reports(country: str = Path(..., description="India|USA|China|Brazil")):
    return await imf_article_iv(country)

# ── FRED ───────────────────────────────────────────────────────────────────
@router.get("/fred", summary="FRED (St. Louis Fed) economic series")
async def fred(series: str = Query("GDP", description="FRED series ID e.g. GDP, FEDFUNDS, UNRATE"),
               limit: int = Query(20)):
    return await fred_series(series, limit)

@router.get("/fred/indicators", summary="Named FRED indicators")
async def fred_indicators():
    return {"indicators": FRED_SERIES}

# ── OECD ───────────────────────────────────────────────────────────────────
@router.get("/oecd", summary="OECD statistics data")
async def oecd(dataset: str = Query("MEI"), country: str = Query("IND")):
    return await oecd_data(dataset, country)

# ── Nasdaq ─────────────────────────────────────────────────────────────────
@router.get("/earnings", summary="Nasdaq earnings calendar")
async def earnings(date: str = Query("", description="YYYY-MM-DD or empty for today")):
    return await nasdaq_earnings(date)

@router.get("/ipo", summary="Nasdaq IPO calendar")
async def ipo():
    return await nasdaq_ipo()

@router.get("/dividends", summary="Nasdaq dividend calendar")
async def dividends(date: str = Query("")):
    return await nasdaq_dividends(date)

# ── UN Data ────────────────────────────────────────────────────────────────
@router.get("/un", summary="UN Data API")
async def un(series: str = Query("POPIN")):
    return await un_data(series)

# ── Economic Calendar ──────────────────────────────────────────────────────
@router.get("/calendar", summary="Economic calendar events")
async def calendar(country: str = Query("india", description="india|united-states|china|germany")):
    return await economic_calendar(country)

# ── India-specific global comparison ──────────────────────────────────────
@router.get("/india-vs-world/{indicator}", summary="India vs world comparison")
async def india_vs_world(
    indicator: str = Path(..., description="gdp|inflation|unemployment|exports|fdi"),
):
    import asyncio
    countries = ["IN", "US", "CN", "DE", "JP", "BR", "GB"]
    code      = WB_INDICATORS.get(indicator)
    if not code:
        return {"error": f"Unknown indicator. Valid: {sorted(WB_INDICATORS.keys())}"}
    tasks   = [world_bank(c, code, years=3) for c in countries]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {
        "indicator": indicator,
        "code":      code,
        "countries": {
            c: r.get("records", [{}])[0] if isinstance(r, dict) and not r.get("error") else {}
            for c, r in zip(countries, results)
        }
    }
