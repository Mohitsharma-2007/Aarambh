"""Signal detection service - Technical analysis signals using yfinance + pandas/numpy"""
import asyncio
import numpy as np
import pandas as pd
import yfinance as yf
from typing import List, Dict, Optional
from loguru import logger
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

_executor = ThreadPoolExecutor(max_workers=4)

WATCHLIST = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "BHARTIARTL.NS", "SBIN.NS", "LTIM.NS", 
    "LICI.NS", "ITC.NS", "HINDUNILVR.NS", "ADANIENT.NS", "BAJFINANCE.NS", "MARUTI.NS", "AXISBANK.NS", "TITAN.NS",
    "SUNPHARMA.NS", "ULTRACEMCO.NS", "WIPRO.NS", "ASIANPAINT.NS", "ONGC.NS", "HCLTECH.NS", "NTPC.NS", "TATASTEEL.NS",
    "AAPL", "MSFT", "GOOG", "AMZN", "NVDA", "META", "TSLA", "JPM", "BAC",
    "XOM", "JNJ", "WMT", "PG", "HD", "CVX", "LLY", "ABBV", "PFE",
    "KO", "PEP", "COST", "NFLX", "AMD", "INTC", "BA", "GS", "BLK",
    "CAT", "LMT", "DIS", "SPY", "QQQ"
]


def _compute_rsi(prices: pd.Series, period: int = 14) -> Optional[float]:
    if len(prices) < period + 1:
        return None
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    val = rsi.iloc[-1]
    return round(float(val), 2) if pd.notna(val) else None


def _compute_macd(prices: pd.Series) -> Optional[dict]:
    if len(prices) < 26:
        return None
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line
    return {
        "macd": round(float(macd_line.iloc[-1]), 4),
        "signal": round(float(signal_line.iloc[-1]), 4),
        "histogram": round(float(histogram.iloc[-1]), 4),
        "crossover": "bullish" if histogram.iloc[-1] > 0 and histogram.iloc[-2] <= 0 else
                     "bearish" if histogram.iloc[-1] < 0 and histogram.iloc[-2] >= 0 else "none",
    }


def _compute_bollinger(prices: pd.Series, period: int = 20) -> Optional[dict]:
    if len(prices) < period:
        return None
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = sma + 2 * std
    lower = sma - 2 * std
    price = float(prices.iloc[-1])
    return {
        "upper": round(float(upper.iloc[-1]), 2),
        "middle": round(float(sma.iloc[-1]), 2),
        "lower": round(float(lower.iloc[-1]), 2),
        "width": round(float((upper.iloc[-1] - lower.iloc[-1]) / sma.iloc[-1] * 100), 2),
        "position": "above" if price > upper.iloc[-1] else "below" if price < lower.iloc[-1] else "inside",
    }


def _compute_ma_cross(prices: pd.Series) -> Optional[dict]:
    if len(prices) < 200:
        return None
    ma20 = prices.rolling(20).mean()
    ma50 = prices.rolling(50).mean()
    ma200 = prices.rolling(200).mean()
    price = float(prices.iloc[-1])
    return {
        "ma20": round(float(ma20.iloc[-1]), 2),
        "ma50": round(float(ma50.iloc[-1]), 2),
        "ma200": round(float(ma200.iloc[-1]), 2),
        "above_ma20": bool(price > ma20.iloc[-1]),
        "above_ma50": bool(price > ma50.iloc[-1]),
        "above_ma200": bool(price > ma200.iloc[-1]),
        "golden_cross": bool(ma50.iloc[-1] > ma200.iloc[-1] and ma50.iloc[-2] <= ma200.iloc[-2]),
        "death_cross": bool(ma50.iloc[-1] < ma200.iloc[-1] and ma50.iloc[-2] >= ma200.iloc[-2]),
    }


def _detect_gap(df: pd.DataFrame) -> Optional[dict]:
    if len(df) < 2:
        return None
    today_open = float(df["Open"].iloc[-1])
    prev_close = float(df["Close"].iloc[-2])
    gap_pct = (today_open - prev_close) / prev_close * 100
    if abs(gap_pct) > 1.0:
        return {"type": "gap_up" if gap_pct > 0 else "gap_down", "percent": round(gap_pct, 2)}
    return None


def _detect_streak(prices: pd.Series) -> Optional[dict]:
    if len(prices) < 3:
        return None
    changes = prices.diff().dropna()
    streak = 0
    direction = None
    for val in reversed(changes.values):
        if direction is None:
            direction = "up" if val > 0 else "down"
            streak = 1
        elif (direction == "up" and val > 0) or (direction == "down" and val < 0):
            streak += 1
        else:
            break
    if streak >= 3:
        return {"direction": direction, "days": streak}
    return None


def _detect_volume_spike(df: pd.DataFrame) -> Optional[dict]:
    if len(df) < 21:
        return None
    avg_vol = float(df["Volume"].iloc[-21:-1].mean())
    today_vol = float(df["Volume"].iloc[-1])
    if avg_vol > 0 and today_vol > avg_vol * 2:
        return {"ratio": round(today_vol / avg_vol, 1), "volume": int(today_vol), "avg_volume": int(avg_vol)}
    return None


def _analyze_ticker(ticker: str) -> Optional[dict]:
    """Full technical analysis for a single ticker (sync, runs in thread)"""
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y", interval="1d")
        if df.empty or len(df) < 30:
            return None

        prices = df["Close"]
        price = round(float(prices.iloc[-1]), 2)
        prev = round(float(prices.iloc[-2]), 2) if len(prices) >= 2 else price
        change_pct = round((price - prev) / prev * 100, 2) if prev > 0 else 0

        rsi = _compute_rsi(prices)
        macd = _compute_macd(prices)
        bollinger = _compute_bollinger(prices)
        ma_cross = _compute_ma_cross(prices)
        gap = _detect_gap(df)
        streak = _detect_streak(prices)
        volume_spike = _detect_volume_spike(df)

        # Detect signals
        signals = []
        if rsi is not None:
            if rsi < 30:
                signals.append({"type": "RSI_OVERSOLD", "value": rsi, "severity": "high", "direction": "bullish"})
            elif rsi > 70:
                signals.append({"type": "RSI_OVERBOUGHT", "value": rsi, "severity": "high", "direction": "bearish"})

        if macd and macd["crossover"] == "bullish":
            signals.append({"type": "MACD_BULLISH_CROSS", "value": macd["histogram"], "severity": "medium", "direction": "bullish"})
        elif macd and macd["crossover"] == "bearish":
            signals.append({"type": "MACD_BEARISH_CROSS", "value": macd["histogram"], "severity": "medium", "direction": "bearish"})

        if bollinger and bollinger["position"] == "below":
            signals.append({"type": "BELOW_LOWER_BB", "value": bollinger["lower"], "severity": "medium", "direction": "bullish"})
        elif bollinger and bollinger["position"] == "above":
            signals.append({"type": "ABOVE_UPPER_BB", "value": bollinger["upper"], "severity": "medium", "direction": "bearish"})

        if ma_cross and ma_cross.get("golden_cross"):
            signals.append({"type": "GOLDEN_CROSS", "value": 0, "severity": "high", "direction": "bullish"})
        if ma_cross and ma_cross.get("death_cross"):
            signals.append({"type": "DEATH_CROSS", "value": 0, "severity": "high", "direction": "bearish"})

        if gap:
            signals.append({"type": gap["type"].upper(), "value": gap["percent"], "severity": "medium",
                           "direction": "bullish" if "up" in gap["type"] else "bearish"})

        if streak and streak["days"] >= 4:
            signals.append({"type": f"STREAK_{streak['direction'].upper()}", "value": streak["days"],
                           "severity": "low", "direction": "bullish" if streak["direction"] == "up" else "bearish"})

        if volume_spike:
            signals.append({"type": "VOLUME_SPIKE", "value": volume_spike["ratio"], "severity": "medium", "direction": "neutral"})

        return {
            "ticker": ticker, 
            "current_price": price, 
            "change": change_pct,
            "rsi": rsi,
            "macd": {
                "value": macd["macd"] if macd else 0,
                "signal": macd["signal"] if macd else 0,
                "histogram": macd["histogram"] if macd else 0
            } if macd else None,
            "bollinger": bollinger,
            "ma20": ma_cross["ma20"] if ma_cross else None,
            "ma50": ma_cross["ma50"] if ma_cross else None,
            "ma200": ma_cross["ma200"] if ma_cross else None,
            "atr": 0, # Should compute ATR if needed
            "volume_avg": volume_spike["avg_volume"] if volume_spike else 0,
            "gap": gap, 
            "streak": streak, 
            "volume_spike": volume_spike,
            "signals": signals, 
            "signal_count": len(signals),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.warning(f"Signal analysis error for {ticker}: {e}")
        return None


class SignalService:
    def __init__(self):
        self._cache: Dict[str, dict] = {}
        self._cache_time: Dict[str, datetime] = {}

    def _cache_get(self, key: str, ttl: int = 300):
        from datetime import timedelta
        if key in self._cache and self._cache_time.get(key, datetime.min) > datetime.now() - timedelta(seconds=ttl):
            return self._cache[key]
        return None

    def _cache_set(self, key: str, value):
        self._cache[key] = value
        self._cache_time[key] = datetime.now()

    async def scan_signals(self, tickers: List[str] = None) -> List[dict]:
        """Scan watchlist for technical signals and return a flat list"""
        if not tickers:
            tickers = WATCHLIST

        cache_key = f"scan_flat:{','.join(tickers[:10])}:{len(tickers)}"
        cached = self._cache_get(cache_key, ttl=300)
        if cached:
            return cached

        loop = asyncio.get_event_loop()
        all_signals = []
        
        # Parallelize ticker analysis with more workers
        with ThreadPoolExecutor(max_workers=10) as executor:
            tasks = [loop.run_in_executor(executor, _analyze_ticker, ticker) for ticker in tickers]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            ticker = tickers[i]
            if isinstance(result, Exception):
                logger.error(f"Error scanning {ticker}: {result}")
                continue
                
            if result:
                # Add a baseline signal if no TA signals triggered, so the ticker appears
                active_signals = result.get("signals", [])
                
                # Always add a PRICE_MOMENTUM signal as baseline
                price_change = result.get("change", 0)
                momentum_type = "BULLISH_MOMENTUM" if price_change > 1.5 else "BEARISH_MOMENTUM" if price_change < -1.5 else "NEUTRAL_TREND"
                momentum_severity = "medium" if abs(price_change) > 3 else "low"
                
                baseline_signal = {
                    "type": momentum_type,
                    "ticker": ticker,
                    "value": price_change,
                    "severity": momentum_severity,
                    "direction": "bullish" if price_change > 0 else "bearish" if price_change < 0 else "neutral",
                    "timestamp": result["timestamp"],
                    "description": f"Price {'up' if price_change > 0 else 'down'} {abs(price_change)}% in last session.",
                    "confidence": 0.9
                }
                
                # Use result signals or the baseline
                if not active_signals:
                    all_signals.append(baseline_signal)
                else:
                    for s in active_signals:
                        flat_s = s.copy()
                        flat_s["ticker"] = ticker
                        flat_s["timestamp"] = result["timestamp"]
                        flat_s["description"] = s.get("description") or f"{s['type']} detected for {ticker}"
                        flat_s["confidence"] = s.get("confidence") or 0.8
                        all_signals.append(flat_s)
                    # Also add baseline if it's significant
                    if abs(price_change) > 2:
                        all_signals.append(baseline_signal)

        # Sort by severity (high first)
        severity_map = {"high": 3, "medium": 2, "low": 1}
        all_signals.sort(key=lambda x: severity_map.get(x["severity"], 0), reverse=True)
        
        self._cache_set(cache_key, all_signals)
        return all_signals


    async def get_quant_metrics(self, ticker: str) -> Optional[dict]:
        """Get full quantitative metrics for a single ticker"""
        cached = self._cache_get(f"quant:{ticker}", ttl=300)
        if cached:
            return cached

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(_executor, _analyze_ticker, ticker)
        if result:
            self._cache_set(f"quant:{ticker}", result)
        return result

    async def analyze_quant_metrics(self, ticker: str, data: dict, provider: str = None, model: str = None) -> str:
        """Use AI to interpret technical analysis data for a stock"""
        from app.services.ai_service import ai_service
        
        # Prepare context for AI
        signals_summary = ", ".join([s["type"] for s in data.get("signals", [])])
        
        prompt = f"""[TECHNICAL ANALYSIS INTERPRETER]
        Ticker: {ticker}
        Price: {data.get('current_price')} ({data.get('change')}%)
        RSI: {data.get('rsi')}
        MACD Histogram: {data.get('macd', {}).get('histogram') if data.get('macd') else 'N/A'}
        Bollinger: {data.get('bollinger', {}).get('position')}
        MA Status: Price vs MA200 is {'Above' if (data.get('current_price') or 0) > (data.get('ma200') or 0) else 'Below'}
        Detected Signals: {signals_summary if signals_summary else 'No specific TA signals'}
        
        Task: Provide a concise, dense, and professional technical analysis outlook.
        Identify:
        1. Current Trend (Bullish/Bearish/Neutral)
        2. Key Support/Resistance inferred from indicators
        3. Immediate Risk/Reward profile
        4. Actionable technical recommendation
        
        Be strictly technical. No fluff."""
        
        try:
            return await ai_service.query(prompt, model=model, provider=provider)
        except Exception as e:
            logger.warning(f"AI quant analysis failed for {ticker}: {e}")
            return f"Technical analysis interpretation currently unavailable: {str(e)}"


signal_service = SignalService()
