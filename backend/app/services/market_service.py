"""Market data service - fetches real stock data via yfinance (primary) with Alpha Vantage fallback"""
import asyncio
import yfinance as yf
import httpx
from typing import List, Optional, Dict
from loguru import logger
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

from app.config import settings, LLMProvider
from app.services.indian_market_service import indian_market_service

_executor = ThreadPoolExecutor(max_workers=8)


class MarketService:
    """Service for fetching real-time market data using yfinance"""

    ALPHA_VANTAGE_BASE = "https://www.alphavantage.co/query"

    TRACKED_STOCKS = [
        {"ticker": "NVDA", "name": "NVIDIA Corp", "sector": "Technology", "industry": "Semiconductors"},
        {"ticker": "AVGO", "name": "Broadcom Inc", "sector": "Technology", "industry": "Semiconductors"},
        {"ticker": "AMD", "name": "Advanced Micro Devices", "sector": "Technology", "industry": "Semiconductors"},
        {"ticker": "ASML", "name": "ASML Holding", "sector": "Technology", "industry": "Semiconductors"},
        {"ticker": "INTC", "name": "Intel Corp", "sector": "Technology", "industry": "Semiconductors"},
        {"ticker": "TXN", "name": "Texas Instruments", "sector": "Technology", "industry": "Semiconductors"},
        {"ticker": "QCOM", "name": "Qualcomm Inc", "sector": "Technology", "industry": "Semiconductors"},
        {"ticker": "MSFT", "name": "Microsoft Corp", "sector": "Technology", "industry": "Software Infrastructure"},
        {"ticker": "ORCL", "name": "Oracle Corp", "sector": "Technology", "industry": "Software Infrastructure"},
        {"ticker": "PLTR", "name": "Palantir Technologies", "sector": "Technology", "industry": "Software Infrastructure"},
        {"ticker": "GOOG", "name": "Alphabet Inc", "sector": "Technology", "industry": "Internet Content"},
        {"ticker": "META", "name": "Meta Platforms", "sector": "Technology", "industry": "Internet Content"},
        {"ticker": "AAPL", "name": "Apple Inc", "sector": "Technology", "industry": "Consumer Electronics"},
        {"ticker": "RELIANCE.NS", "name": "Reliance Industries", "sector": "Energy", "industry": "Oil & Gas"},
        {"ticker": "TCS.NS", "name": "Tata Consultancy Services", "sector": "Technology", "industry": "IT Services"},
        {"ticker": "HDFCBANK.NS", "name": "HDFC Bank", "sector": "Financial Services", "industry": "Banks"},
        {"ticker": "INFY.NS", "name": "Infosys", "sector": "Technology", "industry": "IT Services"},
        {"ticker": "ICICIBANK.NS", "name": "ICICI Bank", "sector": "Financial Services", "industry": "Banks"},
        {"ticker": "BHARTIARTL.NS", "name": "Bharti Airtel", "sector": "Communication Services", "industry": "Telecom Services"},
        {"ticker": "SBIN.NS", "name": "State Bank of India", "sector": "Financial Services", "industry": "Banks"},
        {"ticker": "AMZN", "name": "Amazon.com Inc", "sector": "Consumer Cyclical", "industry": "Internet Retail"},
        {"ticker": "TSLA", "name": "Tesla Inc", "sector": "Consumer Cyclical", "industry": "Auto Manufacturers"},
        {"ticker": "HD", "name": "Home Depot", "sector": "Consumer Cyclical", "industry": "Home Improvement"},
        {"ticker": "MCD", "name": "McDonald's Corp", "sector": "Consumer Cyclical", "industry": "Restaurants"},
        {"ticker": "NKE", "name": "Nike Inc", "sector": "Consumer Cyclical", "industry": "Apparel"},
        {"ticker": "JPM", "name": "JPMorgan Chase", "sector": "Financial Services", "industry": "Banks"},
        {"ticker": "BAC", "name": "Bank of America", "sector": "Financial Services", "industry": "Banks"},
        {"ticker": "GS", "name": "Goldman Sachs", "sector": "Financial Services", "industry": "Capital Markets"},
        {"ticker": "MS", "name": "Morgan Stanley", "sector": "Financial Services", "industry": "Capital Markets"},
        {"ticker": "BLK", "name": "BlackRock Inc", "sector": "Financial Services", "industry": "Capital Markets"},
        {"ticker": "SPGI", "name": "S&P Global", "sector": "Financial Services", "industry": "Financial Data"},
        {"ticker": "LLY", "name": "Eli Lilly & Co", "sector": "Healthcare", "industry": "Drug Manufacturers"},
        {"ticker": "ABBV", "name": "AbbVie Inc", "sector": "Healthcare", "industry": "Drug Manufacturers"},
        {"ticker": "PFE", "name": "Pfizer Inc", "sector": "Healthcare", "industry": "Drug Manufacturers"},
        {"ticker": "UNH", "name": "UnitedHealth Group", "sector": "Healthcare", "industry": "Healthcare Plans"},
        {"ticker": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare", "industry": "Drug Manufacturers"},
        {"ticker": "BA", "name": "Boeing Co", "sector": "Industrials", "industry": "Aerospace & Defense"},
        {"ticker": "GD", "name": "General Dynamics", "sector": "Industrials", "industry": "Aerospace & Defense"},
        {"ticker": "LMT", "name": "Lockheed Martin", "sector": "Industrials", "industry": "Aerospace & Defense"},
        {"ticker": "NOC", "name": "Northrop Grumman", "sector": "Industrials", "industry": "Aerospace & Defense"},
        {"ticker": "CAT", "name": "Caterpillar Inc", "sector": "Industrials", "industry": "Industrial Machinery"},
        {"ticker": "HON", "name": "Honeywell Intl", "sector": "Industrials", "industry": "Conglomerates"},
        {"ticker": "XOM", "name": "Exxon Mobil Corp", "sector": "Energy", "industry": "Oil & Gas Integrated"},
        {"ticker": "CVX", "name": "Chevron Corp", "sector": "Energy", "industry": "Oil & Gas Integrated"},
        {"ticker": "COP", "name": "ConocoPhillips", "sector": "Energy", "industry": "Oil & Gas Exploration"},
        {"ticker": "SLB", "name": "Schlumberger NV", "sector": "Energy", "industry": "Oil & Gas Equipment"},
        {"ticker": "NFLX", "name": "Netflix Inc", "sector": "Communication Services", "industry": "Entertainment"},
        {"ticker": "DIS", "name": "Walt Disney Co", "sector": "Communication Services", "industry": "Entertainment"},
        {"ticker": "CMCSA", "name": "Comcast Corp", "sector": "Communication Services", "industry": "Telecom Services"},
        {"ticker": "VZ", "name": "Verizon Communications", "sector": "Communication Services", "industry": "Telecom Services"},
        {"ticker": "NEE", "name": "NextEra Energy", "sector": "Utilities", "industry": "Utilities"},
        {"ticker": "DUK", "name": "Duke Energy Corp", "sector": "Utilities", "industry": "Utilities"},
        {"ticker": "WMT", "name": "Walmart Inc", "sector": "Consumer Defensive", "industry": "Discount Stores"},
        {"ticker": "COST", "name": "Costco Wholesale", "sector": "Consumer Defensive", "industry": "Discount Stores"},
        {"ticker": "PG", "name": "Procter & Gamble", "sector": "Consumer Defensive", "industry": "Household Products"},
        {"ticker": "KO", "name": "Coca-Cola Co", "sector": "Consumer Defensive", "industry": "Beverages"},
        {"ticker": "PEP", "name": "PepsiCo Inc", "sector": "Consumer Defensive", "industry": "Beverages"},
        {"ticker": "EQIX", "name": "Equinix Inc", "sector": "Real Estate", "industry": "REITs"},
        {"ticker": "AMT", "name": "American Tower", "sector": "Real Estate", "industry": "REITs"},
        {"ticker": "PLD", "name": "Prologis Inc", "sector": "Real Estate", "industry": "REITs"},
        {"ticker": "NEM", "name": "Newmont Corp", "sector": "Basic Materials", "industry": "Gold"},
        {"ticker": "APD", "name": "Air Products & Chemicals", "sector": "Basic Materials", "industry": "Chemicals"},
        {"ticker": "SHW", "name": "Sherwin-Williams", "sector": "Basic Materials", "industry": "Chemicals"},
    ]

    INDEX_TICKERS = [
        {"ticker": "^GSPC", "name": "S&P 500", "display": "SPY"},
        {"ticker": "^IXIC", "name": "NASDAQ Composite", "display": "QQQ"},
        {"ticker": "^DJI", "name": "Dow Jones", "display": "DIA"},
        {"ticker": "^RUT", "name": "Russell 2000", "display": "IWM"},
        {"ticker": "^FTSE", "name": "FTSE 100", "display": "FTSE"},
        {"ticker": "^GDAXI", "name": "DAX", "display": "DAX"},
        {"ticker": "^N225", "name": "Nikkei 225", "display": "N225"},
        {"ticker": "^HSI", "name": "Hang Seng", "display": "HSI"},
        {"ticker": "^BSESN", "name": "BSE SENSEX", "display": "SENSEX"},
        {"ticker": "^NSEI", "name": "NIFTY 50", "display": "NIFTY"},
    ]

    CRYPTO_TICKERS = [
        {"ticker": "BTC-USD", "name": "Bitcoin", "symbol": "BTC"},
        {"ticker": "ETH-USD", "name": "Ethereum", "symbol": "ETH"},
        {"ticker": "SOL-USD", "name": "Solana", "symbol": "SOL"},
        {"ticker": "BNB-USD", "name": "Binance Coin", "symbol": "BNB"},
        {"ticker": "XRP-USD", "name": "XRP", "symbol": "XRP"},
        {"ticker": "ADA-USD", "name": "Cardano", "symbol": "ADA"},
    ]

    FX_TICKERS = [
        {"ticker": "USDINR=X", "name": "USD/INR", "symbol": "INR"},
        {"ticker": "EURUSD=X", "name": "EUR/USD", "symbol": "EUR"},
        {"ticker": "GBPUSD=X", "name": "GBP/USD", "symbol": "GBP"},
        {"ticker": "USDJPY=X", "name": "USD/JPY", "symbol": "JPY"},
        {"ticker": "AUDUSD=X", "name": "AUD/USD", "symbol": "AUD"},
    ]

    COMMODITY_TICKERS = [
        {"ticker": "GC=F", "name": "Gold", "symbol": "Gold"},
        {"ticker": "SI=F", "name": "Silver", "symbol": "Silver"},
        {"ticker": "CL=F", "name": "Crude Oil", "symbol": "Oil"},
        {"ticker": "BZ=F", "name": "Brent Oil", "symbol": "Brent"},
        {"ticker": "NG=F", "name": "Natural Gas", "symbol": "Gas"},
    ]

    SECTOR_ETFS = [
        {"ticker": "XLK", "name": "Technology", "sector": "Technology"},
        {"ticker": "XLF", "name": "Financial", "sector": "Financial Services"},
        {"ticker": "XLE", "name": "Energy", "sector": "Energy"},
        {"ticker": "XLV", "name": "Healthcare", "sector": "Healthcare"},
        {"ticker": "XLI", "name": "Industrial", "sector": "Industrials"},
        {"ticker": "XLY", "name": "Consumer Disc.", "sector": "Consumer Cyclical"},
        {"ticker": "XLP", "name": "Consumer Staples", "sector": "Consumer Defensive"},
        {"ticker": "XLU", "name": "Utilities", "sector": "Utilities"},
        {"ticker": "XLRE", "name": "Real Estate", "sector": "Real Estate"},
        {"ticker": "XLB", "name": "Materials", "sector": "Basic Materials"},
        {"ticker": "XLC", "name": "Communications", "sector": "Communication Services"},
    ]

    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self._cache: Dict[str, dict] = {}
        self._cache_time: Dict[str, datetime] = {}

    def _cache_get(self, key: str, ttl: int = 60) -> Optional[dict]:
        if key in self._cache and self._cache_time.get(key, datetime.min) > datetime.now() - timedelta(seconds=ttl):
            return self._cache[key]
        return None

    def _cache_set(self, key: str, value):
        self._cache[key] = value
        self._cache_time[key] = datetime.now()

    def _yf_fetch_quote(self, ticker: str) -> Optional[dict]:
        """Synchronous yfinance fetch (run in thread pool)"""
        try:
            t = yf.Ticker(ticker)
            info = t.fast_info
            price = float(info.last_price) if hasattr(info, 'last_price') and info.last_price else 0
            prev_close = float(info.previous_close) if hasattr(info, 'previous_close') and info.previous_close else price
            market_cap = float(info.market_cap) if hasattr(info, 'market_cap') and info.market_cap else 0
            change_pct = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0

            # Try to get 52w high/low
            high52 = float(info.year_high) if hasattr(info, 'year_high') and info.year_high else None
            low52 = float(info.year_low) if hasattr(info, 'year_low') and info.year_low else None

            return {
                "price": round(price, 2),
                "priceChange": round(change_pct, 2),
                "marketCap": market_cap,
                "volume": int(info.last_volume) if hasattr(info, 'last_volume') and info.last_volume else 0,
                "high52w": round(high52, 2) if high52 else None,
                "low52w": round(low52, 2) if low52 else None,
                "previousClose": round(prev_close, 2),
            }
        except Exception as e:
            logger.warning(f"yfinance quote error for {ticker}: {e}")
            return None

    def _yf_fetch_profile(self, ticker: str) -> Optional[dict]:
        """Fetch company profile from yfinance"""
        try:
            t = yf.Ticker(ticker)
            info = t.info
            return {
                "ticker": ticker,
                "name": info.get("longName") or info.get("shortName", ticker),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "description": info.get("longBusinessSummary", ""),
                "website": info.get("website", ""),
                "employees": info.get("fullTimeEmployees", 0),
                "ceo": info.get("companyOfficers", [{}])[0].get("name", "N/A") if info.get("companyOfficers") else "N/A",
                "country": info.get("country", ""),
                "exchange": info.get("exchange", ""),
                "currency": info.get("currency", "USD"),
                "ipoDate": info.get("firstTradeDateEpochUtc", ""),
                "marketCap": info.get("marketCap", 0),
                "enterpriseValue": info.get("enterpriseValue", 0),
                "trailingPE": info.get("trailingPE"),
                "forwardPE": info.get("forwardPE"),
                "pegRatio": info.get("pegRatio"),
                "priceToBook": info.get("priceToBook"),
                "priceToSales": info.get("priceToSalesTrailing12Months"),
                "dividendYield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "targetMeanPrice": info.get("targetMeanPrice"),
                "recommendationKey": info.get("recommendationKey"),
            }
        except Exception as e:
            logger.warning(f"yfinance profile error for {ticker}: {e}")
            return None

    def _yf_fetch_history(self, ticker: str, period: str = "1mo", interval: str = "1d") -> List[dict]:
        """Fetch historical OHLCV data"""
        try:
            t = yf.Ticker(ticker)
            df = t.history(period=period, interval=interval)
            if df.empty:
                return []
            result = []
            for idx, row in df.iterrows():
                result.append({
                    "date": idx.strftime("%Y-%m-%d %H:%M") if interval in ("1m", "5m", "15m", "1h") else idx.strftime("%Y-%m-%d"),
                    "open": round(float(row["Open"]), 2),
                    "high": round(float(row["High"]), 2),
                    "low": round(float(row["Low"]), 2),
                    "close": round(float(row["Close"]), 2),
                    "volume": int(row["Volume"]),
                })
            return result
        except Exception as e:
            logger.warning(f"yfinance history error for {ticker}: {e}")
            return []

    def _yf_fetch_financials(self, ticker: str) -> Optional[dict]:
        """Fetch financial statements"""
        try:
            t = yf.Ticker(ticker)
            result = {}

            # Income statement
            inc = t.income_stmt
            if inc is not None and not inc.empty:
                result["income_statement"] = []
                for col in inc.columns[:4]:  # last 4 years
                    period_data = {"period": col.strftime("%Y") if hasattr(col, 'strftime') else str(col)}
                    for idx_name in inc.index:
                        val = inc.at[idx_name, col]
                        period_data[str(idx_name)] = float(val) if val == val else None  # NaN check
                    result["income_statement"].append(period_data)

            # Balance sheet
            bs = t.balance_sheet
            if bs is not None and not bs.empty:
                result["balance_sheet"] = []
                for col in bs.columns[:4]:
                    period_data = {"period": col.strftime("%Y") if hasattr(col, 'strftime') else str(col)}
                    for idx_name in bs.index:
                        val = bs.at[idx_name, col]
                        period_data[str(idx_name)] = float(val) if val == val else None
                    result["balance_sheet"].append(period_data)

            # Cash flow
            cf = t.cashflow
            if cf is not None and not cf.empty:
                result["cash_flow"] = []
                for col in cf.columns[:4]:
                    period_data = {"period": col.strftime("%Y") if hasattr(col, 'strftime') else str(col)}
                    for idx_name in cf.index:
                        val = cf.at[idx_name, col]
                        period_data[str(idx_name)] = float(val) if val == val else None
                    result["cash_flow"].append(period_data)

            return result if result else None
        except Exception as e:
            logger.warning(f"yfinance financials error for {ticker}: {e}")
            return None

    def _yf_fetch_holders(self, ticker: str) -> Optional[dict]:
        """Fetch ownership data"""
        try:
            t = yf.Ticker(ticker)
            result = {}

            mh = t.major_holders
            if mh is not None and not mh.empty:
                result["major_holders"] = []
                for _, row in mh.iterrows():
                    result["major_holders"].append({"value": str(row.iloc[0]), "label": str(row.iloc[1])})

            ih = t.institutional_holders
            if ih is not None and not ih.empty:
                result["institutional_holders"] = []
                for _, row in ih.head(20).iterrows():
                    result["institutional_holders"].append({
                        "holder": str(row.get("Holder", "")),
                        "shares": int(row.get("Shares", 0)) if row.get("Shares") == row.get("Shares") else 0,
                        "value": float(row.get("Value", 0)) if row.get("Value") == row.get("Value") else 0,
                        "pctHeld": float(row.get("pctHeld", 0)) if row.get("pctHeld") == row.get("pctHeld") else 0,
                    })

            mfh = t.mutualfund_holders
            if mfh is not None and not mfh.empty:
                result["mutualfund_holders"] = []
                for _, row in mfh.head(20).iterrows():
                    result["mutualfund_holders"].append({
                        "holder": str(row.get("Holder", "")),
                        "shares": int(row.get("Shares", 0)) if row.get("Shares") == row.get("Shares") else 0,
                        "value": float(row.get("Value", 0)) if row.get("Value") == row.get("Value") else 0,
                        "pctHeld": float(row.get("pctHeld", 0)) if row.get("pctHeld") == row.get("pctHeld") else 0,
                    })

            return result if result else None
        except Exception as e:
            logger.warning(f"yfinance holders error for {ticker}: {e}")
            return None

    def _yf_fetch_recommendations(self, ticker: str) -> Optional[list]:
        """Fetch analyst recommendations"""
        try:
            t = yf.Ticker(ticker)
            rec = t.recommendations
            if rec is None or rec.empty:
                return None
            result = []
            for _, row in rec.tail(20).iterrows():
                result.append({
                    "period": str(row.get("period", "")),
                    "strongBuy": int(row.get("strongBuy", 0)),
                    "buy": int(row.get("buy", 0)),
                    "hold": int(row.get("hold", 0)),
                    "sell": int(row.get("sell", 0)),
                    "strongSell": int(row.get("strongSell", 0)),
                })
            return result
        except Exception as e:
            logger.warning(f"yfinance recommendations error for {ticker}: {e}")
            return None

    # ── Async wrappers ──

    async def get_stock_quote(self, ticker: str) -> Optional[dict]:
        ticker = ticker.upper()
        # Handle Indian stocks via IndianAPI
        if ticker.endswith(".NS") or ticker.endswith(".BO"):
            base_symbol = ticker.split(".")[0]
            return await indian_market_service.get_indian_stock_quote(base_symbol)

        cached = self._cache_get(f"quote:{ticker}", ttl=60)
        if cached:
            return cached

        loop = asyncio.get_event_loop()
        quote = await loop.run_in_executor(_executor, self._yf_fetch_quote, ticker)
        if quote:
            stock_info = next((s for s in self.TRACKED_STOCKS if s["ticker"] == ticker), None)
            quote["ticker"] = ticker
            quote["name"] = stock_info["name"] if stock_info else ticker
            quote["sector"] = stock_info["sector"] if stock_info else "Unknown"
            quote["industry"] = stock_info["industry"] if stock_info else "Unknown"
            self._cache_set(f"quote:{ticker}", quote)
            return quote
        return None

    async def get_stock_profile(self, ticker: str) -> Optional[dict]:
        ticker = ticker.upper()
        # Prefer FMP for profile if available
        if settings.fmp_api_key:
            fmp_ticker = ticker.split(".")[0] if "." in ticker else ticker
            profile = await indian_market_service.fmp_company_profile(fmp_ticker)
            if profile:
                return {
                    "ticker": ticker,
                    "name": profile.get("companyName"),
                    "sector": profile.get("sector"),
                    "industry": profile.get("industry"),
                    "description": profile.get("description"),
                    "website": profile.get("website"),
                    "ceo": profile.get("ceo"),
                    "exchange": profile.get("exchangeShortName"),
                    "currency": profile.get("currency"),
                    "marketCap": profile.get("mktCap"),
                }

        cached = self._cache_get(f"profile:{ticker}", ttl=3600)
        if cached:
            return cached
        loop = asyncio.get_event_loop()
        profile = await loop.run_in_executor(_executor, self._yf_fetch_profile, ticker)
        if profile:
            # Augment with FMP data if available
            if settings.fmp_api_key:
                try:
                    fmp_ticker = ticker.split(".")[0] if "." in ticker else ticker
                    fmp_profile = await indian_market_service.fmp_company_profile(fmp_ticker)
                    if fmp_profile:
                        profile["fmp_data"] = fmp_profile
                except Exception:
                    pass
            self._cache_set(f"profile:{ticker}", profile)
        return profile

    async def get_stock_financials(self, ticker: str) -> Optional[dict]:
        ticker = ticker.upper()
        # Prefer FMP for financials
        if settings.fmp_api_key:
            fmp_ticker = ticker.split(".")[0] if "." in ticker else ticker
            return await indian_market_service.fmp_financial_statements(fmp_ticker)

        cached = self._cache_get(f"financials:{ticker}", ttl=86400)
        if cached:
            return cached
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(_executor, self._yf_fetch_financials, ticker)
        if data:
            self._cache_set(f"financials:{ticker}", data)
        return data

    async def get_stock_holders(self, ticker: str) -> Optional[dict]:
        ticker = ticker.upper()
        cached = self._cache_get(f"holders:{ticker}", ttl=86400)
        if cached:
            return cached
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(_executor, self._yf_fetch_holders, ticker)
        if data:
            self._cache_set(f"holders:{ticker}", data)
        return data

    async def get_recommendations(self, ticker: str) -> Optional[list]:
        ticker = ticker.upper()
        cached = self._cache_get(f"rec:{ticker}", ttl=86400)
        if cached:
            return cached
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(_executor, self._yf_fetch_recommendations, ticker)
        if data:
            self._cache_set(f"rec:{ticker}", data)
        return data

    async def get_historical_data(self, ticker: str, period: str = "1mo", interval: str = "1d") -> List[dict]:
        ticker = ticker.upper()
        cache_key = f"hist:{ticker}:{period}:{interval}"
        cached = self._cache_get(cache_key, ttl=300)
        if cached:
            return cached
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(_executor, self._yf_fetch_history, ticker, period, interval)
        if data:
            self._cache_set(cache_key, data)
        return data

    async def get_candles(self, ticker: str, timeframe: str = "1d", period: str = "6mo") -> List[dict]:
        """Get OHLCV candle data for charting"""
        tf_map = {
            "1m": ("1m", "1d"), "5m": ("5m", "5d"), "15m": ("15m", "5d"),
            "1h": ("1h", "1mo"), "4h": ("1h", "3mo"),
            "1d": ("1d", period), "1w": ("1wk", "2y"), "1M": ("1mo", "5y"),
        }
        interval, auto_period = tf_map.get(timeframe, ("1d", "6mo"))
        return await self.get_historical_data(ticker, auto_period, interval)

    async def get_deep_ticker_research(self, ticker: str, provider: str = None, model: str = None) -> Dict[str, Any]:
        """Exhaustive research combining YF, FMP, News, and Search"""
        ticker = ticker.upper()
        
        # 1. Concurrent fetching of core data
        quote_task = self.get_stock_quote(ticker)
        profile_task = self.get_stock_profile(ticker)
        fin_task = self.get_stock_financials(ticker)
        holders_task = self.get_stock_holders(ticker)
        rec_task = self.get_recommendations(ticker)
        
        core_data = await asyncio.gather(
            quote_task, profile_task, fin_task, holders_task, rec_task,
            return_exceptions=True
        )
        
        results = {
            "ticker": ticker,
            "quote": core_data[0] if not isinstance(core_data[0], Exception) else None,
            "profile": core_data[1] if not isinstance(core_data[1], Exception) else None,
            "financials": core_data[2] if not isinstance(core_data[2], Exception) else None,
            "holders": core_data[3] if not isinstance(core_data[3], Exception) else None,
            "recommendations": core_data[4] if not isinstance(core_data[4], Exception) else None,
            "timestamp": datetime.utcnow().isoformat(),
            "elaborated_analysis": ""
        }
        
        # 2. Add search-based "Elaborated Data" using DDGS
        from duckduckgo_search import AsyncDDGS
        search_query = f"{ticker} stock company deep analysis strategic outlook 2026 financial health competitive moat"
        news_query = f"{ticker} stock latest news major developments 2024 2025"
        
        try:
            ddgs = AsyncDDGS()
            search_results = await ddgs.text(search_query, max_results=10)
            news_results = await ddgs.text(news_query, max_results=8)
            
            results["web_research"] = [
                {"title": r.get("title"), "url": r.get("href"), "snippet": r.get("body")}
                for r in search_results
            ]
            results["recent_news"] = [
                {"title": r.get("title"), "url": r.get("href"), "snippet": r.get("body")}
                for r in news_results
            ]
        except Exception as e:
            logger.warning(f"Web research failed for {ticker}: {e}")
            results["web_research"] = []
            results["recent_news"] = []

        # 3. Generate detailed AI summary if core data exists
        if results["profile"] or results["quote"]:
            from app.services.ai_service import ai_service
            
            # Format financials for AI context
            fin_context = "N/A"
            if results["financials"]:
                try:
                    inc = results["financials"].get("income_statement", [])
                    if inc:
                        fin_context = f"Latest Revenue: {inc[0].get('Total Revenue')}, Net Income: {inc[0].get('Net Income Common Stock')}"
                except Exception:
                    pass

            context = f"Company: {ticker}\n"
            if results["profile"]:
                context += f"Description: {results['profile'].get('description', '')[:1200]}\n"
                context += f"Sector: {results['profile'].get('sector')}, Industry: {results['profile'].get('industry')}\n"
                context += f"Market Cap: {results['profile'].get('marketCap')}, PE: {results['profile'].get('trailingPE')}\n"
            if results["quote"]:
                context += f"Current Price: {results['quote'].get('price')}, Change: {results['quote'].get('priceChange')}%\n"
            
            if results["profile"]:
                context += f"Price Target (Mean): {results['profile'].get('targetMeanPrice')}, Rec: {results['profile'].get('recommendationKey')}\n"

            context += f"Financial Pulse: {fin_context}\n"
            
            web_text = "\n".join([f"SOURCE: {r['title']}\nCONTENT: {r['snippet']}" for r in results["web_research"][:6]])
            news_text = "\n".join([f"NEWS: {r['title']}\nSUMMARY: {r['snippet']}" for r in results.get("recent_news", [])[:5]])
            
            prompt = f"""[CRITICAL TASK] Conduct an EXHAUSTIVE STRATEGIC INTELLIGENCE DEEP DIVE on {ticker}.
            You are a lead sovereign wealth fund analyst. Your analysis must be dense, insightful, and highly technical.
            
            DATA INPUTS:
            --- CORE METRICS ---
            {context}
            
            --- GLOBAL WEB INTELLIGENCE ---
            {web_text[:3500]}
            
            --- RECENT COGENT DEVELOPMENTS ---
            {news_text[:2000]}
            
            REQUIRED STRUCTURE FOR ANALYSIS (ELABORATE EXTENSIVELY):
            
            1. EXECUTIVE STRATEGIC SYNOPSIS
            Provide a high-level master narrative of where the company stands in the global hierarchy.
            
            2. REVENUE ARCHITECTURE & MARGIN DYNAMICS
            Analyze how they make money, the durability of their pricing power, and margin trends.
            
            3. COMPETITIVE MOAT & ECOSYSTEM DOMINANCE
            Evaluate their defensibility using Porter's 5 Forces. What is their 'unfair advantage'?
            
            4. GEOPOLITICAL & MACROECONOMIC EXPOSURE
            How does current global instability, trade wars (US-China), and interest rate regimes affect them specifically?
            
            5. THE 'INDIA ANGLE' (STRATEGIC SYNERGY)
            Analyze their presence, growth potential, or strategic importance to India's economy/defense/technology mission.
            
            6. FUTURE ALPHA PROJECTIONS (BULL/BEAR SCENARIOS)
            Construct a sophisticated forward-looking model. Identify the 'Black Swan' risks and the 'Moonshot' catalysts.
            
            FINAL VERDICT: 
            A definitive technical stance on the stock's role in a strategic portfolio.
            
            [INSTRUCTION] DO NOT BE BRIEF. ELABORATE ON EVERY POINT. USE QUANTITATIVE DATA WHEREVER MENTIONED IN INPUTS. 
            Maintain a tone of extreme professional rigor. No fluff. No boilerplate."""
            
            try:
                results["elaborated_analysis"] = await ai_service.query(prompt, model=model, provider=provider)
            except Exception as e:
                logger.warning(f"AI analysis failed for {ticker}: {e}")

        return results

    async def get_all_stocks(self) -> List[dict]:
        """Fetch quotes for all tracked stocks via yfinance"""
        loop = asyncio.get_event_loop()
        seen = set()
        unique_stocks = []
        for s in self.TRACKED_STOCKS:
            if s["ticker"] not in seen:
                seen.add(s["ticker"])
                unique_stocks.append(s)

        def batch_fetch():
            tickers_str = " ".join(s["ticker"] for s in unique_stocks)
            try:
                data = yf.download(tickers_str, period="2d", group_by="ticker", threads=True, progress=False)
                results = []
                for stock_info in unique_stocks:
                    t = stock_info["ticker"]
                    try:
                        if len(unique_stocks) == 1:
                            ticker_data = data
                        else:
                            ticker_data = data[t] if t in data.columns.get_level_values(0) else None

                        if ticker_data is not None and not ticker_data.empty and len(ticker_data) >= 1:
                            last_row = ticker_data.iloc[-1]
                            prev_row = ticker_data.iloc[-2] if len(ticker_data) >= 2 else last_row
                            price = float(last_row["Close"]) if last_row["Close"] == last_row["Close"] else 0
                            prev_close = float(prev_row["Close"]) if prev_row["Close"] == prev_row["Close"] else price
                            change_pct = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0
                            volume = int(last_row["Volume"]) if last_row["Volume"] == last_row["Volume"] else 0

                            results.append({
                                **stock_info,
                                "price": round(price, 2),
                                "priceChange": round(change_pct, 2),
                                "marketCap": price * self._estimate_shares(t),
                                "volume": volume,
                                "high52w": None,
                                "low52w": None,
                            })
                        else:
                            results.append({**stock_info, "price": 0, "priceChange": 0, "marketCap": 0, "volume": 0, "high52w": None, "low52w": None})
                    except Exception:
                        results.append({**stock_info, "price": 0, "priceChange": 0, "marketCap": 0, "volume": 0, "high52w": None, "low52w": None})
                return results
            except Exception as e:
                logger.error(f"Batch stock fetch error: {e}")
                return [{**s, "price": 0, "priceChange": 0, "marketCap": 0, "volume": 0, "high52w": None, "low52w": None} for s in unique_stocks]

        cached = self._cache_get("all_stocks", ttl=60)
        if cached:
            return cached

        result = await loop.run_in_executor(_executor, batch_fetch)
        self._cache_set("all_stocks", result)
        return result

    async def get_indices(self) -> List[dict]:
        """Get real-time index data (Global + Indian)"""
        cached = self._cache_get("indices_combined", ttl=60)
        if cached:
            return cached

        loop = asyncio.get_event_loop()

        def fetch_us_indices():
            results = []
            us_tickers = [t for t in self.INDEX_TICKERS if not t["display"] in ["SENSEX", "NIFTY"]]
            tickers_str = " ".join(i["ticker"] for i in us_tickers)
            try:
                data = yf.download(tickers_str, period="2d", group_by="ticker", threads=True, progress=False)
                for idx_info in us_tickers:
                    t = idx_info["ticker"]
                    try:
                        ticker_data = data[t] if t in data.columns.get_level_values(0) else None
                        if ticker_data is not None and not ticker_data.empty and len(ticker_data) >= 1:
                            last = ticker_data.iloc[-1]
                            prev = ticker_data.iloc[-2] if len(ticker_data) >= 2 else last
                            price = float(last["Close"])
                            prev_close = float(prev["Close"])
                            # Skip indices with NaN values
                            if price != price or prev_close != prev_close:
                                continue
                            change = price - prev_close
                            change_pct = (change / prev_close * 100) if prev_close > 0 else 0
                            results.append({
                                "ticker": idx_info["display"],
                                "name": idx_info["name"],
                                "value": round(price, 2),
                                "change": round(change, 2),
                                "changePercent": round(change_pct, 2),
                                "trend": "up" if change >= 0 else "down",
                            })
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"US Index fetch error: {e}")
            return results

        # Fetch US and Indian in parallel
        us_results, in_results = await asyncio.gather(
            loop.run_in_executor(_executor, fetch_us_indices),
            indian_market_service.get_indian_indices(),
            return_exceptions=True
        )

        combined = []
        if isinstance(us_results, list):
            combined.extend(us_results)
        
        if isinstance(in_results, list):
            for idx in in_results:
                val = idx.get("value", 0)
                chg = idx.get("change", 0)
                chg_pct = idx.get("changePercent", 0)
                # Skip entries with NaN values
                if val != val or chg != chg or chg_pct != chg_pct:
                    continue
                combined.append({
                    "ticker": idx["name"].replace(" ", ""),
                    "name": idx["name"],
                    "value": val,
                    "change": chg,
                    "changePercent": chg_pct,
                    "trend": "up" if chg >= 0 else "down",
                })

        if combined:
            self._cache_set("indices_combined", combined)
        return combined

    async def get_crypto(self) -> List[dict]:
        """Get cryptocurrency prices via yfinance"""
        cached = self._cache_get("crypto", ttl=60)
        if cached:
            return cached

        loop = asyncio.get_event_loop()

        def fetch_crypto():
            results = []
            tickers_str = " ".join(c["ticker"] for c in self.CRYPTO_TICKERS)
            try:
                data = yf.download(tickers_str, period="2d", group_by="ticker", threads=True, progress=False)
                for c in self.CRYPTO_TICKERS:
                    t = c["ticker"]
                    try:
                        ticker_data = data[t] if t in data.columns.get_level_values(0) else None
                        if ticker_data is not None and not ticker_data.empty:
                            last = ticker_data.iloc[-1]
                            prev = ticker_data.iloc[-2] if len(ticker_data) >= 2 else last
                            price = float(last["Close"])
                            prev_close = float(prev["Close"])
                            change_pct = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0
                            results.append({
                                "symbol": c["symbol"],
                                "name": c["name"],
                                "price": round(price, 2),
                                "changePercent": round(change_pct, 2),
                                "trend": "up" if change_pct >= 0 else "down",
                            })
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Crypto fetch error: {e}")
            return results

        result = await loop.run_in_executor(_executor, fetch_crypto)
        if result:
            self._cache_set("crypto", result)
        return result

    async def get_fx(self) -> List[dict]:
        """Get FX rates via yfinance"""
        cached = self._cache_get("fx_rates", ttl=60)
        if cached:
            return cached

        loop = asyncio.get_event_loop()

        def fetch_fx():
            results = []
            tickers_str = " ".join(c["ticker"] for c in self.FX_TICKERS)
            try:
                data = yf.download(tickers_str, period="2d", group_by="ticker", threads=True, progress=False)
                for c in self.FX_TICKERS:
                    t = c["ticker"]
                    try:
                        ticker_data = data[t] if t in data.columns.get_level_values(0) else None
                        if ticker_data is not None and not ticker_data.empty:
                            last = ticker_data.iloc[-1]
                            prev = ticker_data.iloc[-2] if len(ticker_data) >= 2 else last
                            price = float(last["Close"])
                            prev_close = float(prev["Close"])
                            change_pct = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0
                            results.append({
                                "symbol": c["symbol"],
                                "name": c["name"],
                                "price": round(price, 4),
                                "changePercent": round(change_pct, 2),
                                "trend": "up" if change_pct >= 0 else "down",
                            })
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"FX fetch error: {e}")
            return results

        result = await loop.run_in_executor(_executor, fetch_fx)
        if result:
            self._cache_set("fx_rates", result)
        return result

    async def get_commodities(self) -> List[dict]:
        """Get commodity prices via yfinance"""
        cached = self._cache_get("commodities", ttl=300)
        if cached:
            return cached

        loop = asyncio.get_event_loop()

        def fetch_cmd():
            results = []
            tickers_str = " ".join(c["ticker"] for c in self.COMMODITY_TICKERS)
            try:
                data = yf.download(tickers_str, period="2d", group_by="ticker", threads=True, progress=False)
                for c in self.COMMODITY_TICKERS:
                    t = c["ticker"]
                    try:
                        ticker_data = data[t] if t in data.columns.get_level_values(0) else None
                        if ticker_data is not None and not ticker_data.empty:
                            last = ticker_data.iloc[-1]
                            prev = ticker_data.iloc[-2] if len(ticker_data) >= 2 else last
                            price = float(last["Close"])
                            prev_close = float(prev["Close"])
                            change_pct = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0
                            results.append({
                                "symbol": c["symbol"],
                                "name": c["name"],
                                "price": round(price, 2),
                                "changePercent": round(change_pct, 2),
                                "trend": "up" if change_pct >= 0 else "down",
                            })
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Commodities fetch error: {e}")
            return results

        result = await loop.run_in_executor(_executor, fetch_cmd)
        if result:
            self._cache_set("commodities", result)
        return result

    async def get_treasury_yields(self) -> dict:
        """Get treasury yields from FRED API"""
        cached = self._cache_get("treasury", ttl=3600)
        if cached:
            return cached

        series = {"DGS2": "2Y", "DGS5": "5Y", "DGS10": "10Y", "DGS30": "30Y"}
        result = {}

        if settings.fred_api_key:
            try:
                for series_id, label in series.items():
                    resp = await self.http_client.get(
                        "https://api.stlouisfed.org/fred/series/observations",
                        params={"series_id": series_id, "api_key": settings.fred_api_key,
                                "file_type": "json", "sort_order": "desc", "limit": 2}
                    )
                    if resp.status_code == 200:
                        obs = resp.json().get("observations", [])
                        if obs:
                            val = obs[0].get("value", ".")
                            prev_val = obs[1].get("value", ".") if len(obs) > 1 else val
                            if val != ".":
                                result[label] = {
                                    "value": float(val),
                                    "previous": float(prev_val) if prev_val != "." else float(val),
                                    "change": round(float(val) - (float(prev_val) if prev_val != "." else float(val)), 3),
                                }
            except Exception as e:
                logger.error(f"FRED treasury error: {e}")

        if result:
            self._cache_set("treasury", result)
        return result

    async def get_sector_summary(self) -> List[dict]:
        """Get real sector performance from sector ETFs"""
        cached = self._cache_get("sectors", ttl=300)
        if cached:
            return cached

        loop = asyncio.get_event_loop()

        def fetch_sectors():
            results = []
            tickers_str = " ".join(e["ticker"] for e in self.SECTOR_ETFS)
            try:
                data = yf.download(tickers_str, period="5d", group_by="ticker", threads=True, progress=False)
                for etf in self.SECTOR_ETFS:
                    t = etf["ticker"]
                    try:
                        ticker_data = data[t] if t in data.columns.get_level_values(0) else None
                        if ticker_data is not None and not ticker_data.empty:
                            last = ticker_data.iloc[-1]
                            prev = ticker_data.iloc[-2] if len(ticker_data) >= 2 else last
                            price = float(last["Close"])
                            prev_close = float(prev["Close"])
                            change_pct = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0

                            # Weekly change
                            first = ticker_data.iloc[0]
                            week_start = float(first["Close"])
                            week_change = ((price - week_start) / week_start * 100) if week_start > 0 else 0

                            results.append({
                                "name": etf["name"],
                                "sector": etf["sector"],
                                "etf": etf["ticker"],
                                "price": round(price, 2),
                                "avgChange": round(change_pct, 2),
                                "weekChange": round(week_change, 2),
                                "stockCount": 0,
                            })
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Sector fetch error: {e}")
            return results

        result = await loop.run_in_executor(_executor, fetch_sectors)
        if result:
            self._cache_set("sectors", result)
        return result

    async def get_compare(self, tickers: List[str]) -> List[dict]:
        """Compare multiple tickers side-by-side"""
        results = []
        for ticker in tickers[:10]:  # max 10
            profile = await self.get_stock_profile(ticker)
            quote = await self.get_stock_quote(ticker)
            if profile and quote:
                results.append({**profile, **quote})
            elif quote:
                results.append(quote)
        return results

    def _estimate_shares(self, ticker: str) -> float:
        shares_estimate = {
            "AAPL": 15.5e9, "MSFT": 7.5e9, "GOOG": 12.5e9, "AMZN": 10.5e9,
            "NVDA": 2.5e9, "META": 2.6e9, "TSLA": 3.2e9, "JPM": 2.9e9,
            "JNJ": 2.6e9, "XOM": 4.0e9, "WMT": 2.7e9, "PG": 2.4e9,
            "HD": 1.0e9, "CVX": 1.9e9, "LLY": 0.95e9, "ABBV": 1.8e9,
            "PEP": 1.4e9, "KO": 4.3e9, "COST": 0.44e9, "MCD": 0.72e9,
            "NKE": 1.5e9, "INTC": 4.2e9, "AMD": 1.6e9, "QCOM": 1.1e9,
            "TXN": 0.92e9, "AVGO": 0.47e9, "ORCL": 2.8e9, "BA": 0.6e9,
            "HON": 0.66e9, "GS": 0.32e9, "MS": 1.7e9, "BLK": 0.15e9,
            "SPGI": 0.31e9, "CAT": 0.5e9, "LMT": 0.24e9, "NOC": 0.15e9,
            "GD": 0.28e9, "UNH": 0.93e9, "PFE": 5.6e9, "VZ": 4.2e9,
            "DIS": 1.8e9, "NFLX": 0.44e9, "CMCSA": 4.1e9, "PLTR": 2.2e9,
            "BAC": 8.0e9, "ASML": 0.4e9, "SLB": 1.4e9, "COP": 1.2e9,
            "NEE": 2.1e9, "DUK": 0.77e9, "EQIX": 0.094e9, "AMT": 0.47e9,
            "PLD": 0.93e9, "NEM": 0.79e9, "APD": 0.22e9, "SHW": 0.25e9,
        }
        return shares_estimate.get(ticker, 1e9)

    async def close(self):
        await self.http_client.aclose()


market_service = MarketService()
