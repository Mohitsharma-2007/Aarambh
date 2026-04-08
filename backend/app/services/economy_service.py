"""Economy data service - fetches real data from FRED, World Bank, CoinGecko, yfinance"""
import asyncio
import httpx
import yfinance as yf
from typing import Optional, List, Dict
from loguru import logger
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

from app.config import settings

_executor = ThreadPoolExecutor(max_workers=4)


class EconomyService:
    FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
    COINGECKO_BASE = "https://api.coingecko.com/api/v3"
    WORLD_BANK_BASE = "https://api.worldbank.org/v2"

    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=15.0)
        self._cache: Dict[str, dict] = {}
        self._cache_time: Dict[str, datetime] = {}

    def _cache_get(self, key: str, ttl: int = 3600) -> Optional[dict]:
        if key in self._cache and self._cache_time.get(key, datetime.min) > datetime.now() - timedelta(seconds=ttl):
            return self._cache[key]
        return None

    def _cache_set(self, key: str, value):
        self._cache[key] = value
        self._cache_time[key] = datetime.now()

    async def _fred_latest(self, series_id: str, limit: int = 10) -> Optional[List[dict]]:
        """Fetch latest observations from FRED"""
        if not settings.fred_api_key:
            return None
        try:
            resp = await self.http_client.get(self.FRED_BASE, params={
                "series_id": series_id, "api_key": settings.fred_api_key,
                "file_type": "json", "sort_order": "desc", "limit": limit,
            })
            if resp.status_code == 200:
                obs = resp.json().get("observations", [])
                return [{"date": o["date"], "value": float(o["value"])} for o in obs if o.get("value", ".") != "."]
        except Exception as e:
            logger.warning(f"FRED error for {series_id}: {e}")
        return None

    async def _fred_value(self, series_id: str) -> Optional[dict]:
        """Get latest value + previous from FRED"""
        data = await self._fred_latest(series_id, limit=2)
        if data and len(data) >= 1:
            latest = data[0]
            prev = data[1] if len(data) > 1 else data[0]
            change = round(latest["value"] - prev["value"], 3)
            return {"value": latest["value"], "previous": prev["value"], "change": change, "date": latest["date"]}
        return None

    async def get_sentiment(self) -> dict:
        """Fear & Greed, VIX, Consumer Sentiment"""
        cached = self._cache_get("sentiment", ttl=300)
        if cached:
            return cached

        result = {"vix": None, "consumer_sentiment": None, "fear_greed": None, "financial_stress": None}

        # VIX from yfinance
        loop = asyncio.get_event_loop()
        def fetch_vix():
            try:
                t = yf.Ticker("^VIX")
                info = t.fast_info
                return {"value": round(float(info.last_price), 2), "previous": round(float(info.previous_close), 2)}
            except Exception:
                return None
        vix = await loop.run_in_executor(_executor, fetch_vix)
        if vix:
            result["vix"] = {**vix, "change": round(vix["value"] - vix["previous"], 2)}

        # Consumer Sentiment (UMCSENT) from FRED
        umcsent = await self._fred_value("UMCSENT")
        if umcsent:
            result["consumer_sentiment"] = umcsent

        # Financial Stress Index (STLFSI2) from FRED
        stlfsi = await self._fred_value("STLFSI2")
        if stlfsi:
            result["financial_stress"] = stlfsi

        # CNN Fear & Greed - proxy (dynamic date)
        try:
            today_str = datetime.now().strftime("%Y-%m-%d")
            resp = await self.http_client.get(f"https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{today_str}")
            if resp.status_code == 200:
                data = resp.json()
                fg = data.get("fear_and_greed", {})
                result["fear_greed"] = {
                    "value": fg.get("score", 50),
                    "label": fg.get("rating", "Neutral"),
                    "previous": fg.get("previous_close", 50),
                }
        except Exception:
            pass

        self._cache_set("sentiment", result)
        return result

    async def get_crypto(self) -> dict:
        """Crypto market data from CoinGecko"""
        cached = self._cache_get("crypto_eco", ttl=120)
        if cached:
            return cached

        result = {"global": None, "top_coins": [], "fear_greed": None}

        # Global crypto data
        try:
            resp = await self.http_client.get(f"{self.COINGECKO_BASE}/global")
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                result["global"] = {
                    "total_market_cap": data.get("total_market_cap", {}).get("usd", 0),
                    "total_volume": data.get("total_volume", {}).get("usd", 0),
                    "btc_dominance": round(data.get("market_cap_percentage", {}).get("btc", 0), 1),
                    "eth_dominance": round(data.get("market_cap_percentage", {}).get("eth", 0), 1),
                    "active_cryptocurrencies": data.get("active_cryptocurrencies", 0),
                    "market_cap_change_24h": round(data.get("market_cap_change_percentage_24h_usd", 0), 2),
                }
        except Exception as e:
            logger.warning(f"CoinGecko global error: {e}")

        # Top coins
        try:
            resp = await self.http_client.get(f"{self.COINGECKO_BASE}/coins/markets", params={
                "vs_currency": "usd", "order": "market_cap_desc", "per_page": 20, "page": 1,
                "sparkline": "false", "price_change_percentage": "1h,24h,7d"
            })
            if resp.status_code == 200:
                for coin in resp.json():
                    result["top_coins"].append({
                        "id": coin.get("id"), "symbol": coin.get("symbol", "").upper(),
                        "name": coin.get("name"), "price": coin.get("current_price", 0),
                        "market_cap": coin.get("market_cap", 0),
                        "volume_24h": coin.get("total_volume", 0),
                        "change_1h": coin.get("price_change_percentage_1h_in_currency"),
                        "change_24h": coin.get("price_change_percentage_24h", 0),
                        "change_7d": coin.get("price_change_percentage_7d_in_currency"),
                        "image": coin.get("image"),
                    })
        except Exception as e:
            logger.warning(f"CoinGecko coins error: {e}")

        # Crypto Fear & Greed
        try:
            resp = await self.http_client.get("https://api.alternative.me/fng/?limit=1")
            if resp.status_code == 200:
                data = resp.json().get("data", [{}])[0]
                result["fear_greed"] = {"value": int(data.get("value", 50)), "label": data.get("value_classification", "Neutral")}
        except Exception:
            pass

        self._cache_set("crypto_eco", result)
        return result

    async def get_growth(self) -> dict:
        """GDP growth, industrial production from FRED"""
        cached = self._cache_get("growth", ttl=86400)
        if cached:
            return cached

        result = {}
        series = {
            "gdp": "GDP", "gdp_growth": "A191RL1Q225SBEA",
            "industrial_production": "INDPRO", "real_gdp": "GDPC1",
            "gdp_per_capita": "A939RX0Q048SBEA",
        }
        for key, sid in series.items():
            data = await self._fred_latest(sid, limit=20)
            if data:
                result[key] = {"latest": data[0], "history": data}

        self._cache_set("growth", result)
        return result

    async def get_inflation(self) -> dict:
        """CPI, PPI, PCE from FRED"""
        cached = self._cache_get("inflation", ttl=86400)
        if cached:
            return cached

        result = {}
        series = {
            "cpi": "CPIAUCSL", "cpi_yoy": "CPIAUCSL",
            "core_cpi": "CPILFESL", "ppi": "PPIACO",
            "pce": "PCEPI", "core_pce": "PCEPILFE",
            "breakeven_5y": "T5YIE", "breakeven_10y": "T10YIE",
        }
        for key, sid in series.items():
            data = await self._fred_latest(sid, limit=24)
            if data:
                result[key] = {"latest": data[0], "history": data}

        self._cache_set("inflation", result)
        return result

    async def get_employment(self) -> dict:
        """Unemployment, payrolls, jobless claims from FRED"""
        cached = self._cache_get("employment", ttl=86400)
        if cached:
            return cached

        result = {}
        series = {
            "unemployment": "UNRATE", "nonfarm_payrolls": "PAYEMS",
            "initial_claims": "ICSA", "continuing_claims": "CCSA",
            "labor_force_participation": "CIVPART", "job_openings": "JTSJOL",
            "avg_hourly_earnings": "CES0500000003",
        }
        for key, sid in series.items():
            data = await self._fred_latest(sid, limit=24)
            if data:
                result[key] = {"latest": data[0], "history": data}

        self._cache_set("employment", result)
        return result

    async def get_rates(self) -> dict:
        """Fed funds, treasury yields, SOFR from FRED"""
        cached = self._cache_get("rates", ttl=3600)
        if cached:
            return cached

        result = {}
        series = {
            "fed_funds": "FEDFUNDS", "fed_funds_effective": "DFF",
            "treasury_2y": "DGS2", "treasury_5y": "DGS5",
            "treasury_10y": "DGS10", "treasury_30y": "DGS30",
            "treasury_3m": "DGS3MO", "sofr": "SOFR",
            "prime_rate": "DPRIME",
        }
        for key, sid in series.items():
            data = await self._fred_latest(sid, limit=30)
            if data:
                result[key] = {"latest": data[0], "history": data}

        self._cache_set("rates", result)
        return result

    async def get_housing(self) -> dict:
        """Housing starts, permits, home prices from FRED"""
        cached = self._cache_get("housing", ttl=86400)
        if cached:
            return cached

        result = {}
        series = {
            "housing_starts": "HOUST", "building_permits": "PERMIT",
            "home_price_index": "CSUSHPISA", "median_home_price": "MSPUS",
            "existing_home_sales": "EXHOSLUSM495S",
            "mortgage_30y": "MORTGAGE30US", "mortgage_15y": "MORTGAGE15US",
        }
        for key, sid in series.items():
            data = await self._fred_latest(sid, limit=24)
            if data:
                result[key] = {"latest": data[0], "history": data}

        self._cache_set("housing", result)
        return result

    async def get_consumer(self) -> dict:
        """Consumer confidence, retail sales, personal income from FRED"""
        cached = self._cache_get("consumer", ttl=86400)
        if cached:
            return cached

        result = {}
        series = {
            "consumer_sentiment": "UMCSENT", "retail_sales": "RSAFS",
            "personal_income": "PI", "personal_spending": "PCE",
            "savings_rate": "PSAVERT", "consumer_credit": "TOTALSL",
        }
        for key, sid in series.items():
            data = await self._fred_latest(sid, limit=24)
            if data:
                result[key] = {"latest": data[0], "history": data}

        self._cache_set("consumer", result)
        return result

    async def get_liquidity(self) -> dict:
        """M2 money supply, fed balance sheet, TGA from FRED"""
        cached = self._cache_get("liquidity", ttl=86400)
        if cached:
            return cached

        result = {}
        series = {
            "m2": "M2SL", "m1": "M1SL",
            "fed_balance_sheet": "WALCL", "tga": "WTREGEN",
            "reverse_repo": "RRPONTSYD", "bank_reserves": "TOTRESNS",
        }
        for key, sid in series.items():
            data = await self._fred_latest(sid, limit=24)
            if data:
                result[key] = {"latest": data[0], "history": data}

        self._cache_set("liquidity", result)
        return result

    async def get_global(self) -> dict:
        """World Bank data for major economies"""
        cached = self._cache_get("global_eco", ttl=86400)
        if cached:
            return cached

        countries = ["USA", "CHN", "IND", "JPN", "DEU", "GBR", "FRA", "BRA", "RUS"]
        indicators = {
            "gdp": "NY.GDP.MKTP.CD", "gdp_growth": "NY.GDP.MKTP.KD.ZG",
            "inflation": "FP.CPI.TOTL.ZG", "unemployment": "SL.UEM.TOTL.ZS",
        }
        result = {}

        for country in countries:
            result[country] = {}
            for key, ind_id in indicators.items():
                try:
                    resp = await self.http_client.get(
                        f"{self.WORLD_BANK_BASE}/country/{country}/indicator/{ind_id}",
                        params={"format": "json", "per_page": 5, "mrv": 5}
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if len(data) > 1 and data[1]:
                            values = [{"year": d["date"], "value": d["value"]} for d in data[1] if d["value"] is not None]
                            if values:
                                result[country][key] = values
                except Exception:
                    pass

        self._cache_set("global_eco", result)
        return result

    async def get_fedwatch(self) -> dict:
        """Fed funds rate probabilities estimated from FRED data"""
        cached = self._cache_get("fedwatch", ttl=3600)
        if cached:
            return cached

        result = {"current_rate": None, "history": [], "next_meeting": "TBD"}

        # Current fed funds rate
        ff = await self._fred_value("FEDFUNDS")
        if ff:
            result["current_rate"] = ff["value"]

        # Fed funds rate history for trend
        history = await self._fred_latest("FEDFUNDS", limit=24)
        if history:
            result["history"] = history

        # Effective rate
        dff = await self._fred_value("DFF")
        if dff:
            result["effective_rate"] = dff["value"]

        self._cache_set("fedwatch", result)
        return result

    async def close(self):
        await self.http_client.aclose()


economy_service = EconomyService()
