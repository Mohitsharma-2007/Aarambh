"""
utils/session.py — Unified Smart HTTP session for AARAMBH
======================================================
• Rotating User-Agents (Chrome / Firefox / Safari / Edge)
• Domain-aware header profiles (Google, Yahoo, RSS)
• Token-bucket rate limiter per domain
• Exponential back-off + UA rotation on 429/503
• specialized fetchers for JSON, RSS, and Binary data
"""

import httpx
import asyncio
import random
import time
from typing import Optional, Dict, Any

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

def _google_hdrs(ua: str) -> dict:
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Sec-CH-UA": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
        "DNT": "1",
    }

def _yahoo_hdrs(ua: str, ticker: str = "") -> dict:
    ref = f"https://finance.yahoo.com/quote/{ticker}/" if ticker else "https://finance.yahoo.com/"
    return {
        "User-Agent": ua,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": ref,
        "Origin": "https://finance.yahoo.com",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Sec-CH-UA": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
    }

def _rss_hdrs(ua: str) -> dict:
    return {
        "User-Agent": ua,
        "Accept": "application/rss+xml, application/xml, text/xml, */*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    }

def get_headers(domain: str = "google", ticker: str = "") -> dict:
    ua = random.choice(USER_AGENTS)
    d  = domain.lower()
    if "yahoo" in d:            return _yahoo_hdrs(ua, ticker)
    if "rss" in d or "news" in d: return _rss_hdrs(ua)
    return _google_hdrs(ua)

# ── Rate limiter ──────────────────────────────────────────────────────────────
class _Limiter:
    def __init__(self, rps: float = 1.5):
        self._iv   = 1.0 / rps
        self._last: Dict[str, float] = {}
    async def wait(self, host: str):
        now = time.monotonic()
        gap = now - self._last.get(host, 0)
        if gap < self._iv:
            await asyncio.sleep(self._iv - gap + random.uniform(0.1, 0.35))
        self._last[host] = time.monotonic()

_lim = _Limiter(1.5)

# ── Core async fetch ──────────────────────────────────────────────────────────
async def fetch(
    url:     str,
    params:  Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    domain:  str   = "google",
    ticker:  str   = "",
    timeout: float = 15.0,
    retries: int   = 2,
    accept:  Optional[str] = None
) -> httpx.Response:
    from urllib.parse import urlparse
    host = urlparse(url).netloc
    await _lim.wait(host)

    h = get_headers(domain, ticker)
    if accept: h["Accept"] = accept
    if headers: h.update(headers)

    kw: Dict[str, Any] = {"timeout": timeout, "follow_redirects": True}
    
    last_err: Optional[Exception] = None
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(**kw) as cli:
                r = await cli.get(url, params=params, headers=h)
                if r.status_code == 429:
                    await asyncio.sleep(min(10, 2**attempt + random.uniform(0.5, 1.5)))
                    h = get_headers(domain, ticker)
                    if accept: h["Accept"] = accept
                    continue
                if r.status_code in (502, 503):
                    await asyncio.sleep(3 * (attempt + 1))
                    continue
                return r
        except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as e:
            last_err = e
            if attempt < retries - 1:
                await asyncio.sleep(1.5 * (attempt + 1))

    raise ConnectionError(f"Failed after {retries} attempts [{url}]: {last_err}")

async def fetch_json(url: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
    return await fetch(url, params=params, domain="news", accept="application/json, */*;q=0.8")

async def fetch_rss(url: str) -> httpx.Response:
    return await fetch(url, domain="rss", accept="application/rss+xml, application/xml, text/xml, */*;q=0.8")

async def fetch_binary(url: str) -> bytes:
    """Download binary file (PDF, Excel, etc.)"""
    from urllib.parse import urlparse
    host = urlparse(url).netloc
    await _lim.wait(host)
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as cli:
        # Simple headers for binary
        h = {"User-Agent": random.choice(USER_AGENTS), "Accept": "application/octet-stream,*/*"}
        r = await cli.get(url, headers=h)
        r.raise_for_status()
        return r.content
