"""Indian Market Service - NSE/BSE data via IndianAPI + FMP integration"""
import asyncio
import httpx
from typing import Optional, List, Dict, Any
from loguru import logger
from datetime import datetime, timedelta

from app.config import settings


# ── NSE/BSE tracked indices and stocks ──
INDIAN_INDICES = [
    "NIFTY 50", "NIFTY BANK", "NIFTY IT", "NIFTY PHARMA", "NIFTY AUTO",
    "NIFTY METAL", "NIFTY REALTY", "NIFTY ENERGY", "NIFTY FMCG", "NIFTY MEDIA",
    "SENSEX",
]

NIFTY50_STOCKS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK",
    "LT", "AXISBANK", "BAJFINANCE", "ASIAN PAINTS", "MARUTI",
    "HCLTECH", "SUNPHARMA", "TITAN", "WIPRO", "ULTRACEMCO",
    "NESTLEIND", "TATAMOTORS", "JSWSTEEL", "POWERGRID", "NTPC",
    "COALINDIA", "ADANIENT", "ADANIPORTS", "TECHM", "ONGC",
    "DRREDDY", "HEROMOTOCO", "CIPLA", "BAJAJ AUTO", "GRASIM",
    "DIVISLAB", "BPCL", "EICHERMOT", "TATACONSUM", "APOLLOHOSP",
    "BRITANNIA", "TATASTEEL", "INDUSINDBK", "SHRIRAMFIN", "HINDALCO",
    "HDFCLIFE", "SBILIFE", "M&M", "BAJAJFINSV", "BEL",
]


class IndianMarketService:
    """Integrates IndianAPI, FMP, and NSE/BSE data providers"""

    INDIAN_API_BASE = "https://stock.indianapi.in"
    FMP_BASE = "https://financialmodelingprep.com/stable"
    NSE_API_BASE = "https://www.nseindia.com/api"

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_time: Dict[str, datetime] = {}

    def _cache_get(self, key: str, ttl: int = 300):
        if key in self._cache and self._cache_time.get(key, datetime.min) > datetime.now() - timedelta(seconds=ttl):
            return self._cache[key]
        return None

    def _cache_set(self, key: str, value: Any):
        self._cache[key] = value
        self._cache_time[key] = datetime.now()

    # ── IndianAPI Endpoints ──

    async def _indianapi_get(self, path: str, params: dict = None) -> Optional[dict]:
        """Call IndianAPI with auth header"""
        try:
            async with httpx.AsyncClient(timeout=25.0, follow_redirects=True, headers={"User-Agent": "AARAMBH/2.0"}) as client:
                headers = {"X-Api-Key": settings.indianapi_key}
                url = f"{self.INDIAN_API_BASE}{path}"
                resp = await client.get(url, headers=headers, params=params or {})
                if resp.status_code == 200:
                    return resp.json()
                logger.warning(f"IndianAPI {path}: HTTP {resp.status_code}")
                return None
        except Exception as e:
            logger.warning(f"IndianAPI {path} error: {e}")
            return None

    async def get_indian_stock_quote(self, symbol: str) -> Optional[dict]:
        """Get live quote for an Indian stock"""
        cached = self._cache_get(f"instock:{symbol}", ttl=120)
        if cached:
            return cached

        data = await self._indianapi_get(f"/stock", {"name": symbol})
        if not data:
            return None

        def safe_extract(val, default=0):
            if isinstance(val, dict):
                val = val.get("NSE", val.get("BSE", default))
            if val is None:
                return default
            try:
                return float(val)
            except (ValueError, TypeError):
                return default

        result = {
            "symbol": symbol,
            "name": data.get("companyName", symbol),
            "price": safe_extract(data.get("currentPrice", 0)),
            "change": safe_extract(data.get("dayChange", 0)),
            "changePercent": safe_extract(data.get("dayChangePerc", 0)),
            "high": safe_extract(data.get("dayHigh", 0)),
            "low": safe_extract(data.get("dayLow", 0)),
            "open": safe_extract(data.get("open", 0)),
            "previousClose": safe_extract(data.get("previousClose", 0)),
            "volume": safe_extract(data.get("totalTradedVolume", 0)),
            "marketCap": safe_extract(data.get("marketCap", 0)),
            "pe": safe_extract(data.get("pe", 0)),
            "eps": safe_extract(data.get("eps", 0)),
            "bookValue": safe_extract(data.get("bookValue", 0)),
            "dividendYield": safe_extract(data.get("dividendYield", 0)),
            "industry": data.get("industry", ""),
            "sector": data.get("sector", ""),
            "high52w": safe_extract(data.get("high52", 0)),
            "low52w": safe_extract(data.get("low52", 0)),
            "exchange": "NSE",
            "source": "indianapi",
        }
        self._cache_set(f"instock:{symbol}", result)
        return result

    async def get_nifty50_heatmap(self) -> List[dict]:
        """Get heatmap data for all NIFTY 50 stocks"""
        cached = self._cache_get("nifty50_heatmap", ttl=300)
        if cached:
            return cached

        data = await self._indianapi_get("/stock", {"name": "NIFTY 50"})
        if not data:
            return []

        def safe_extract(val, default=0):
            if isinstance(val, dict):
                val = val.get("NSE", val.get("BSE", default))
            if val is None:
                return default
            try:
                return float(val)
            except (ValueError, TypeError):
                return default

        stocks_data = data.get("stocks", [])
        result = []
        for stock in stocks_data:
            result.append({
                "symbol": stock.get("symbol", ""),
                "name": stock.get("name", ""),
                "price": safe_extract(stock.get("ltp", 0)),
                "change": safe_extract(stock.get("change", 0)),
                "changePercent": safe_extract(stock.get("changePerc", 0)),
                "sector": stock.get("sector", ""),
                "exchange": "NSE",
            })

        self._cache_set("nifty50_heatmap", result)
        return result

    async def get_indian_indices(self) -> List[dict]:
        """Get all Indian market indices"""
        cached = self._cache_get("indian_indices", ttl=120)
        if cached:
            return cached

        def safe_extract(val, default=0):
            if isinstance(val, dict):
                val = val.get("NSE", val.get("BSE", default))
            if val is None:
                return default
            try:
                return float(val)
            except (ValueError, TypeError):
                return default

        data = await self._indianapi_get("/stock", {"name": "NIFTY 50"})
        indices = []

        if data:
            # Main index data
            indices.append({
                "name": "NIFTY 50",
                "value": safe_extract(data.get("currentPrice", 0)),
                "change": safe_extract(data.get("dayChange", 0)),
                "changePercent": safe_extract(data.get("dayChangePerc", 0)),
                "exchange": "NSE",
            })

        # Fetch additional indices
        for idx_name in ["NIFTY BANK", "SENSEX"]:
            idx_data = await self._indianapi_get("/stock", {"name": idx_name})
            if idx_data:
                indices.append({
                    "name": idx_name,
                    "value": safe_extract(idx_data.get("currentPrice", 0)),
                    "change": safe_extract(idx_data.get("dayChange", 0)),
                    "changePercent": safe_extract(idx_data.get("dayChangePerc", 0)),
                    "exchange": "BSE" if "SENSEX" in idx_name else "NSE",
                })

        self._cache_set("indian_indices", indices)
        return indices

    async def get_ipo_data(self) -> dict:
        """Get upcoming, current and listed IPOs"""
        cached = self._cache_get("ipo_data", ttl=1800)
        if cached:
            return cached

        data = await self._indianapi_get("/ipo")
        if not data:
            return {"upcoming": [], "current": [], "listed": []}

        result = {
            "upcoming": data.get("upcomingIpos", [])[:20],
            "current": data.get("currentIpos", [])[:10],
            "listed": data.get("listedIpos", [])[:20],
        }
        self._cache_set("ipo_data", result)
        return result

    async def get_mutual_funds(self) -> List[dict]:
        """Get mutual fund data"""
        cached = self._cache_get("mutual_funds", ttl=3600)
        if cached:
            return cached

        data = await self._indianapi_get("/mutual_funds")
        if not data:
            return []

        result = data if isinstance(data, list) else data.get("funds", [])
        self._cache_set("mutual_funds", result[:50])
        return result[:50]

    # ── FMP (Financial Modeling Prep) Endpoints ──

    async def _fmp_get(self, path: str, params: dict = None) -> Optional[Any]:
        """Call FMP Stable API with API key"""
        try:
            url = f"{self.FMP_BASE}{path}"
            p = params or {}
            p["apikey"] = settings.fmp_api_key
            resp = await self.http_client.get(url, params=p)
            if resp.status_code == 200:
                return resp.json()
            logger.warning(f"FMP {path}: HTTP {resp.status_code} - {resp.text[:200]}")
            return None
        except Exception as e:
            logger.warning(f"FMP {path} error: {e}")
            return None

    async def fmp_quote(self, symbol: str) -> Optional[dict]:
        """Get FMP quote for any global stock using stable endpoint"""
        cached = self._cache_get(f"fmp_quote:{symbol}", ttl=120)
        if cached:
            return cached

        # Use /quote?symbol=... for stable
        data = await self._fmp_get("/quote", {"symbol": symbol})
        if data and isinstance(data, list) and len(data) > 0:
            q = data[0]
            result = {
                "symbol": q.get("symbol"),
                "name": q.get("name", ""),
                "price": q.get("price", 0),
                "change": q.get("change", 0),
                "changePercent": q.get("changePercentage", 0),
                "volume": q.get("volume", 0),
                "avgVolume": q.get("priceAvg50", 0),  # fallback
                "marketCap": q.get("marketCap", 0),
                "pe": q.get("pe", 0),
                "eps": q.get("eps", 0),
                "beta": q.get("beta", 0),
                "high52w": q.get("yearHigh", 0),
                "low52w": q.get("yearLow", 0),
                "exchange": q.get("exchange", ""),
                "open": q.get("open", 0),
                "previousClose": q.get("previousClose", 0),
                "source": "fmp",
            }
            self._cache_set(f"fmp_quote:{symbol}", result)
            return result
        return None

    async def fmp_market_gainers(self) -> List[dict]:
        """Get top gainers from FMP"""
        cached = self._cache_get("fmp_gainers", ttl=300)
        if cached:
            return cached
        data = await self._fmp_get("/biggest-gainers")
        if data and isinstance(data, list):
            self._cache_set("fmp_gainers", data[:20])
            return data[:20]
        return []

    async def fmp_market_losers(self) -> List[dict]:
        """Get top losers from FMP"""
        cached = self._cache_get("fmp_losers", ttl=300)
        if cached:
            return cached
        data = await self._fmp_get("/biggest-losers")
        if data and isinstance(data, list):
            self._cache_set("fmp_losers", data[:20])
            return data[:20]
        return []

    async def fmp_market_active(self) -> List[dict]:
        """Get most active stocks from FMP"""
        cached = self._cache_get("fmp_active", ttl=300)
        if cached:
            return cached
        data = await self._fmp_get("/most-active")
        if data and isinstance(data, list):
            self._cache_set("fmp_active", data[:20])
            return data[:20]
        return []

    async def fmp_financial_statements(self, symbol: str) -> dict:
        """Get income statement, balance sheet, cash flow from FMP"""
        cached = self._cache_get(f"fmp_fin:{symbol}", ttl=86400)
        if cached:
            return cached

        income, balance, cash = await asyncio.gather(
            self._fmp_get("/income-statement", {"symbol": symbol, "limit": 4}),
            self._fmp_get("/balance-sheet-statement", {"symbol": symbol, "limit": 4}),
            self._fmp_get("/cash-flow-statement", {"symbol": symbol, "limit": 4}),
            return_exceptions=True,
        )

        result = {
            "income_statement": income if isinstance(income, list) else [],
            "balance_sheet": balance if isinstance(balance, list) else [],
            "cash_flow": cash if isinstance(cash, list) else [],
        }
        self._cache_set(f"fmp_fin:{symbol}", result)
        return result

    async def fmp_company_profile(self, symbol: str) -> Optional[dict]:
        """Get company profile from FMP stable endpoint"""
        cached = self._cache_get(f"fmp_profile:{symbol}", ttl=86400)
        if cached:
            return cached

        data = await self._fmp_get("/profile", {"symbol": symbol})
        if data and isinstance(data, list) and len(data) > 0:
            profile = data[0]
            # Standardize for AARAMBH
            res = {
                "ticker": profile.get("symbol"),
                "name": profile.get("companyName"),
                "sector": profile.get("sector"),
                "industry": profile.get("industry"),
                "description": profile.get("description"),
                "website": profile.get("website"),
                "ceo": profile.get("ceo"),
                "exchange": profile.get("exchangeShortName"),
                "currency": profile.get("currency"),
                "marketCap": profile.get("mktCap"),
                "full_data": profile
            }
            self._cache_set(f"fmp_profile:{symbol}", res)
            return res
        return None

    async def fmp_stock_screener(self, market_cap_min: int = 10_000_000_000, limit: int = 30) -> List[dict]:
        """Screen stocks with filters"""
        cached = self._cache_get(f"fmp_screen:{market_cap_min}", ttl=3600)
        if cached:
            return cached

        data = await self._fmp_get("/stock-screener", {
            "marketCapMoreThan": market_cap_min,
            "limit": limit,
        })
        if data and isinstance(data, list):
            self._cache_set(f"fmp_screen:{market_cap_min}", data)
            return data
        return []

    async def fmp_economic_calendar(self) -> List[dict]:
        """Get economic calendar from FMP"""
        cached = self._cache_get("fmp_econ_cal", ttl=3600)
        if cached:
            return cached

        today = datetime.now().strftime("%Y-%m-%d")
        future = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        data = await self._fmp_get("/economic-calendar", {"from": today, "to": future})
        if data and isinstance(data, list):
            self._cache_set("fmp_econ_cal", data[:50])
            return data[:50]
        return []

    async def fmp_earnings_calendar(self) -> List[dict]:
        """Get earnings calendar from FMP"""
        cached = self._cache_get("fmp_earn_cal", ttl=3600)
        if cached:
            return cached

        today = datetime.now().strftime("%Y-%m-%d")
        future = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        data = await self._fmp_get("/earning-calendar", {"from": today, "to": future})
        if data and isinstance(data, list):
            self._cache_set("fmp_earn_cal", data[:50])
            return data[:50]
        return []

    # ── Unified Data Providers ──

    async def get_combined_market_overview(self) -> dict:
        """Get combined market overview from all providers"""
        cached = self._cache_get("combined_overview", ttl=180)
        if cached:
            return cached

        # Fetch data from multiple sources concurrently
        nifty_data, gainers, losers, active = await asyncio.gather(
            self.get_nifty50_heatmap(),
            self.fmp_market_gainers(),
            self.fmp_market_losers(),
            self.fmp_market_active(),
            return_exceptions=True,
        )

        result = {
            "nifty50": nifty_data if isinstance(nifty_data, list) else [],
            "gainers": gainers if isinstance(gainers, list) else [],
            "losers": losers if isinstance(losers, list) else [],
            "most_active": active if isinstance(active, list) else [],
            "last_updated": datetime.utcnow().isoformat(),
        }
        self._cache_set("combined_overview", result)
        return result


# Singleton - now safe since clients are created per-request
indian_market_service = IndianMarketService()
