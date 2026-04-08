"""Economy data endpoints - Real-time data from FRED, World Bank, CoinGecko, yfinance"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from loguru import logger
import httpx
from datetime import datetime

from app.services.economy_service import economy_service

router = APIRouter()

WORLD_BANK_BASE = "https://api.worldbank.org/v2"


class EconomyIndicator(BaseModel):
    id: str
    label: str
    value: str
    change: str
    trend: str
    period: str
    source: str


class MarketIndex(BaseModel):
    name: str
    value: str
    change: str
    change_pct: str
    trend: str


class TradeData(BaseModel):
    label: str
    value: str
    change: str
    trend: str


class SectorData(BaseModel):
    sector: str
    gva: str
    growth: str


class EconomyOverview(BaseModel):
    macro_indicators: List[EconomyIndicator]
    market_indices: List[MarketIndex]
    trade_data: List[TradeData]
    sector_performance: List[SectorData]
    rbi_rates: dict
    last_updated: str


async def fetch_world_bank_indicator(indicator: str, country: str = "IND") -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{WORLD_BANK_BASE}/country/{country}/indicator/{indicator}?format=json&per_page=2&mrv=2"
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                if len(data) > 1 and data[1]:
                    latest = data[1][0]
                    prev = data[1][1] if len(data[1]) > 1 else None
                    return {
                        "value": latest.get("value"),
                        "date": latest.get("date"),
                        "prev_value": prev.get("value") if prev else None,
                    }
    except Exception as e:
        logger.warning(f"World Bank API error for {indicator}: {e}")
    return None


@router.get("/overview", response_model=EconomyOverview)
async def get_economy_overview():
    """Get comprehensive economy overview with real data where available"""
    from app.services.market_service import market_service

    indicators = []

    # GDP growth from World Bank
    gdp_data = await fetch_world_bank_indicator("NY.GDP.MKTP.KD.ZG")
    if gdp_data and gdp_data["value"] is not None:
        prev = gdp_data.get("prev_value")
        change = round(gdp_data["value"] - prev, 2) if prev else 0
        indicators.append(EconomyIndicator(
            id="gdp_growth", label="GDP Growth", value=f"{gdp_data['value']:.1f}%",
            change=f"{'+' if change >= 0 else ''}{change}%", trend="up" if change >= 0 else "down",
            period=f"CY{gdp_data['date']}", source="World Bank",
        ))
    else:
        indicators.append(EconomyIndicator(id="gdp_growth", label="GDP Growth", value="8.2%",
            change="+1.4%", trend="up", period="Q2 FY25", source="MOSPI"))

    # CPI from World Bank
    cpi_data = await fetch_world_bank_indicator("FP.CPI.TOTL.ZG")
    if cpi_data and cpi_data["value"] is not None:
        prev = cpi_data.get("prev_value")
        change = round(cpi_data["value"] - prev, 2) if prev else 0
        indicators.append(EconomyIndicator(
            id="inflation", label="Inflation (CPI)", value=f"{cpi_data['value']:.1f}%",
            change=f"{'+' if change >= 0 else ''}{change}%", trend="down" if change <= 0 else "up",
            period=f"CY{cpi_data['date']}", source="World Bank",
        ))
    else:
        indicators.append(EconomyIndicator(id="inflation", label="Inflation (CPI)", value="4.9%",
            change="-0.3%", trend="down", period="Feb 2025", source="MOSPI"))

    indicators.extend([
        EconomyIndicator(id="repo_rate", label="Repo Rate", value="6.50%",
            change="0%", trend="neutral", period="RBI MPC", source="RBI"),
        EconomyIndicator(id="forex_reserves", label="Forex Reserves", value="$625B",
            change="+$3.2B", trend="up", period="Weekly", source="RBI"),
        EconomyIndicator(id="fiscal_deficit", label="Fiscal Deficit", value="5.6%",
            change="-0.3%", trend="down", period="FY25 RE", source="MOF"),
        EconomyIndicator(id="current_account", label="Current Account", value="-1.0%",
            change="+0.2%", trend="up", period="Q2 FY25", source="RBI"),
    ])

    # Real market indices from yfinance
    indices_data = await market_service.get_indices()
    market_indices = []
    for idx in indices_data:
        if idx["ticker"] in ("SENSEX", "NIFTY"):
            market_indices.append(MarketIndex(
                name=idx["name"], value=f"{idx['value']:,.0f}",
                change=f"{'+' if idx['change']>=0 else ''}{idx['change']:,.0f}",
                change_pct=f"{'+' if idx['changePercent']>=0 else ''}{idx['changePercent']:.2f}%",
                trend=idx["trend"],
            ))

    # Add INR/USD via yfinance
    import asyncio
    loop = asyncio.get_event_loop()
    def fetch_inr():
        try:
            t = yf.Ticker("USDINR=X")
            info = t.fast_info
            return {"price": round(float(info.last_price), 2), "prev": round(float(info.previous_close), 2)}
        except Exception:
            return None
    import yfinance as yf
    from concurrent.futures import ThreadPoolExecutor
    _exec = ThreadPoolExecutor(max_workers=1)
    inr = await loop.run_in_executor(_exec, fetch_inr)
    if inr:
        change = round(inr["price"] - inr["prev"], 2)
        market_indices.append(MarketIndex(
            name="INR/USD", value=str(inr["price"]),
            change=f"{'+' if change>=0 else ''}{change}",
            change_pct=f"{change/inr['prev']*100:+.2f}%", trend="up" if change >= 0 else "down",
        ))

    # Treasury from FRED
    treasury = await market_service.get_treasury_yields()
    if "10Y" in treasury:
        t10 = treasury["10Y"]
        market_indices.append(MarketIndex(
            name="10Y Bond", value=f"{t10['value']}%",
            change=f"{t10['change']:+.2f}", change_pct=f"{t10['change']/t10['previous']*100 if t10['previous'] else 0:+.2f}%",
            trend="up" if t10["change"] >= 0 else "down",
        ))

    # Crypto
    crypto = await market_service.get_crypto()
    for c in crypto:
        if c["symbol"] in ("BTC",):
            market_indices.append(MarketIndex(
                name=f"{c['symbol']}", value=f"${c['price']:,.0f}",
                change=f"{c['changePercent']:+.1f}%", change_pct=f"{c['changePercent']:+.1f}%",
                trend=c["trend"],
            ))

    trade_data = [
        TradeData(label="Exports", value="$462B", change="+8.2%", trend="up"),
        TradeData(label="Imports", value="$698B", change="+4.1%", trend="up"),
        TradeData(label="Trade Deficit", value="$236B", change="-3.8%", trend="down"),
    ]

    sector_performance = [
        SectorData(sector="Manufacturing", gva="17.8%", growth="+9.1%"),
        SectorData(sector="Services", gva="53.9%", growth="+7.6%"),
        SectorData(sector="Agriculture", gva="14.8%", growth="+4.2%"),
        SectorData(sector="Construction", gva="8.6%", growth="+10.8%"),
        SectorData(sector="Mining", gva="4.9%", growth="+5.8%"),
    ]

    rbi_rates = {
        "repo_rate": {"label": "Repo Rate", "value": "6.50%", "source": "RBI"},
        "reverse_repo": {"label": "Reverse Repo", "value": "3.35%", "source": "RBI"},
        "msf_rate": {"label": "MSF Rate", "value": "6.75%", "source": "RBI"},
        "crr": {"label": "CRR", "value": "4.50%", "source": "RBI"},
        "slr": {"label": "SLR", "value": "18.00%", "source": "RBI"},
    }

    return EconomyOverview(
        macro_indicators=indicators, market_indices=market_indices,
        trade_data=trade_data, sector_performance=sector_performance,
        rbi_rates=rbi_rates, last_updated=datetime.utcnow().isoformat(),
    )


@router.get("/indicators/{indicator_id}")
async def get_indicator_detail(indicator_id: str):
    """Get detailed data for a specific economic indicator"""
    indicator_map = {
        "gdp_growth": "NY.GDP.MKTP.KD.ZG", "inflation": "FP.CPI.TOTL.ZG",
        "unemployment": "SL.UEM.TOTL.ZS", "fdi": "BX.KLT.DINV.CD.WD",
        "trade_balance": "NE.RSB.GNFS.ZS", "population": "SP.POP.TOTL",
    }
    wb_indicator = indicator_map.get(indicator_id)
    if not wb_indicator:
        raise HTTPException(status_code=404, detail=f"Unknown indicator: {indicator_id}")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{WORLD_BANK_BASE}/country/IND/indicator/{wb_indicator}?format=json&per_page=10&mrv=10"
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                if len(data) > 1 and data[1]:
                    return {"indicator": indicator_id, "data": [
                        {"year": item["date"], "value": item["value"]}
                        for item in data[1] if item["value"] is not None
                    ]}
    except Exception as e:
        logger.error(f"Error fetching indicator detail: {e}")
    raise HTTPException(status_code=500, detail="Failed to fetch indicator data")


# ── New tab-specific endpoints ──

@router.get("/sentiment")
async def get_sentiment():
    """Fear & Greed, VIX, Consumer Sentiment, Financial Stress"""
    return await economy_service.get_sentiment()


@router.get("/crypto")
async def get_crypto():
    """Crypto market data: global stats, top 20 coins, fear & greed"""
    return await economy_service.get_crypto()


@router.get("/growth")
async def get_growth():
    """GDP growth, industrial production, real GDP"""
    return await economy_service.get_growth()


@router.get("/inflation")
async def get_inflation():
    """CPI, PPI, PCE, breakeven rates"""
    return await economy_service.get_inflation()


@router.get("/employment")
async def get_employment():
    """Unemployment, payrolls, jobless claims, labor participation"""
    return await economy_service.get_employment()


@router.get("/rates")
async def get_rates():
    """Fed funds, treasury yields, SOFR, prime rate"""
    return await economy_service.get_rates()


@router.get("/housing")
async def get_housing():
    """Housing starts, permits, home prices, mortgage rates"""
    return await economy_service.get_housing()


@router.get("/consumer")
async def get_consumer():
    """Consumer sentiment, retail sales, personal income/spending"""
    return await economy_service.get_consumer()


@router.get("/liquidity")
async def get_liquidity():
    """M2 money supply, fed balance sheet, TGA, reverse repo"""
    return await economy_service.get_liquidity()


@router.get("/global")
async def get_global():
    """World Bank data for major economies"""
    return await economy_service.get_global()


@router.get("/fedwatch")
async def get_fedwatch():
    """Fed funds rate and rate cut/hike probabilities"""
    return await economy_service.get_fedwatch()
