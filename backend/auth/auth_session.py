"""
auth/auth_session.py
====================
Authenticated HTTP session.
Automatically injects Google cookies, bearer token, and Yahoo crumb
into requests when available.

Falls back gracefully to anonymous requests when no credentials stored.
"""

import httpx, asyncio, random, time
from typing import Optional, Dict, Any
from auth.credential_manager import (
    load as cred_load,
    get_google_headers, get_yahoo_cookies, get_yahoo_cookie_string,
    get_yahoo_crumb, has_google_auth, has_yahoo_auth,
    set_yahoo_crumb, save as cred_save
)

# ── User-Agent pool ────────────────────────────────────────────────────────────
UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
]

# ── Rate limiter ───────────────────────────────────────────────────────────────
class _Lim:
    def __init__(self, rps=1.5):
        self._iv = 1.0/rps
        self._last: Dict[str,float] = {}
    async def wait(self, host: str):
        now = time.monotonic()
        gap = now - self._last.get(host, 0)
        if gap < self._iv:
            await asyncio.sleep(self._iv - gap + random.uniform(0.05, 0.2))
        self._last[host] = time.monotonic()

_lim = _Lim(1.5)

# ── Crumb refresh lock ─────────────────────────────────────────────────────────
_crumb_lock = asyncio.Lock()


# ── Google Finance fetch ───────────────────────────────────────────────────────

async def google_fetch(url: str, params: Optional[Dict] = None,
                        timeout: float = 12.0) -> httpx.Response:
    """
    Enhanced Google Finance fetch with improved authentication handling.
    """
    from urllib.parse import urlparse
    host = urlparse(url).netloc
    await _lim.wait(host)

    # Enhanced base headers with more realistic browser signature
    headers: Dict[str, str] = {
        "User-Agent":                random.choice(UAS),
        "Accept":                    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language":           "en-US,en;q=0.9,en-GB;q=0.8,en;q=0.7",
        "Accept-Encoding":           "gzip, deflate, br",
        "Cache-Control":             "max-age=0",
        "Connection":                "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest":            "document",
        "Sec-Fetch-Mode":            "navigate",
        "Sec-Fetch-Site":            "none",
        "Sec-Fetch-User":            "?1",
        "Sec-CH-UA":                 '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "Sec-CH-UA-Mobile":          "?0",
        "Sec-CH-UA-Platform":        '"Windows"',
        "DNT":                       "1",
        "Sec-GPC":                   "1",
        "Save-Data":                 "on",
    }

    # Inject auth headers (cookies + bearer)
    auth_hdrs = get_google_headers()
    if auth_hdrs.get("Cookie"):
        headers["Cookie"] = auth_hdrs["Cookie"]
    
    if auth_hdrs.get("Authorization"):
        headers["Authorization"] = auth_hdrs["Authorization"]

    # Enhanced retry with different strategies
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(
                timeout=timeout, 
                follow_redirects=True,
                verify=True  # Enable SSL verification
            ) as cli:
                r = await cli.get(url, params=params, headers=headers)
                
                # Check for authentication challenges
                if r.status_code == 200:
                    # Check if we got a login page instead of content
                    if "Sign in" in r.text and "accounts.google.com" in r.text:
                        if attempt < 2:
                            # Try with different approach - refresh cookies
                            headers.update({
                                "Referer": "https://www.google.com/",
                                "Origin": "https://www.google.com",
                            })
                            continue
                        else:
                            # Return the response anyway - let the scraper handle it
                            return r
                    return r
                    
                elif r.status_code in (429, 503):
                    wait_time = min(30, 5 * (2 ** attempt))  # Longer backoff
                    await asyncio.sleep(wait_time)
                    continue
                elif r.status_code == 403:
                    if attempt < 2:
                        # Try with different user agent
                        headers["User-Agent"] = random.choice(UAS)
                        continue
                    else:
                        return r
                else:
                    return r
                    
        except Exception as e:
            if attempt < 2:
                await asyncio.sleep(2 * (attempt + 1))
                continue
            else:
                raise

    raise ConnectionError(f"Failed after {3} attempts: {url}")


# ── Yahoo Finance fetch ────────────────────────────────────────────────────────

async def _fetch_yahoo_crumb(cookies: dict) -> Optional[str]:
    """Fetch Yahoo Finance crumb using stored cookies."""
    ua  = random.choice(UAS)
    hdrs = {
        "User-Agent":      ua,
        "Accept":          "text/plain,*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer":         "https://finance.yahoo.com/",
    }
    try:
        # First visit yahoo.com to get/refresh cookies
        async with httpx.AsyncClient(timeout=8, follow_redirects=True) as cli:
            r1 = await cli.get("https://finance.yahoo.com/", headers={
                **hdrs, "Accept": "text/html,*/*"
            })
            jar = {**dict(r1.cookies), **cookies}

            # Now get the crumb
            r2 = await cli.get(
                "https://query2.finance.yahoo.com/v1/test/getcrumb",
                headers=hdrs, cookies=jar
            )
            val = r2.text.strip()
            if val and len(val) < 50 and r2.status_code == 200:
                set_yahoo_crumb(val)
                cred_save()
                return val
    except Exception:
        pass

    # Try query1 as fallback
    try:
        async with httpx.AsyncClient(timeout=6, follow_redirects=True) as cli:
            r = await cli.get(
                "https://query1.finance.yahoo.com/v1/test/getcrumb",
                headers=hdrs, cookies=cookies
            )
            val = r.text.strip()
            if val and len(val) < 50 and r.status_code == 200:
                set_yahoo_crumb(val)
                cred_save()
                return val
    except Exception:
        pass

    return None


async def get_crumb_now() -> Optional[str]:
    """Get a valid crumb, refreshing if needed."""
    async with _crumb_lock:
        crumb = get_yahoo_crumb()
        if crumb:
            return crumb
        # Need to refresh
        cookies = get_yahoo_cookies()
        return await _fetch_yahoo_crumb(cookies)


async def yahoo_fetch_free(url: str, params: Optional[Dict] = None,
                            ticker: str = "", timeout: float = 8.0) -> httpx.Response:
    """
    Fetch Yahoo Finance endpoints that DON'T need crumb.
    (v8/chart, v7/options, v1/search, v1/trending, screener)
    Tries query1 then query2.
    """
    from urllib.parse import urlparse
    host = urlparse(url).netloc
    await _lim.wait(host)

    cookies_str = get_yahoo_cookie_string()
    cookies_dict = get_yahoo_cookies()

    ref = f"https://finance.yahoo.com/quote/{ticker}/" if ticker else "https://finance.yahoo.com/"
    headers: Dict[str, str] = {
        "User-Agent":      random.choice(UAS),
        "Accept":          "application/json,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer":         ref,
        "Origin":          "https://finance.yahoo.com",
        "Sec-Fetch-Dest":  "empty",
        "Sec-Fetch-Mode":  "cors",
        "Sec-Fetch-Site":  "same-site",
        "Connection":      "keep-alive",
    }
    if cookies_str:
        headers["Cookie"] = cookies_str

    for base in ["https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com"]:
        full_url = url if url.startswith("http") else base + url
        try:
            async with httpx.AsyncClient(
                timeout=timeout, follow_redirects=True,
                cookies=cookies_dict
            ) as cli:
                r = await cli.get(full_url, params=params, headers=headers)
                if r.status_code == 200: return r
                if r.status_code == 404: return r  # real 404 — don't retry
        except Exception:
            continue

    raise ConnectionError(f"Yahoo free endpoint failed: {url}")


async def yahoo_fetch_auth(path: str, params: Optional[Dict] = None,
                            ticker: str = "", timeout: float = 8.0) -> httpx.Response:
    """
    Fetch Yahoo Finance endpoints that NEED crumb.
    (v10/quoteSummary, v11/quoteSummary)
    Gets/refreshes crumb automatically. Falls back to v8 chart if crumb fails.
    """
    # Get crumb (refreshes if needed)
    crumb = await get_crumb_now()
    if crumb:
        p = {**(params or {}), "crumb": crumb}
    else:
        p = params or {}
        # No crumb available — try anyway, may work for some

    cookies_dict = get_yahoo_cookies()
    cookies_str  = get_yahoo_cookie_string()

    ref = f"https://finance.yahoo.com/quote/{ticker}/" if ticker else "https://finance.yahoo.com/"
    headers: Dict[str, str] = {
        "User-Agent":      random.choice(UAS),
        "Accept":          "application/json,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer":         ref,
        "Origin":          "https://finance.yahoo.com",
        "Connection":      "keep-alive",
    }
    if cookies_str:
        headers["Cookie"] = cookies_str

    for base in ["https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com"]:
        full_url = f"{base}{path}"
        try:
            async with httpx.AsyncClient(
                timeout=timeout, follow_redirects=True, cookies=cookies_dict
            ) as cli:
                r = await cli.get(full_url, params=p, headers=headers)
                if r.status_code == 200: return r
                if r.status_code == 401:
                    # Crumb invalid — refresh once
                    async with _crumb_lock:
                        new_crumb = await _fetch_yahoo_crumb(cookies_dict)
                    if new_crumb:
                        p2 = {**p, "crumb": new_crumb}
                        r2 = await cli.get(full_url, params=p2, headers=headers)
                        if r2.status_code == 200: return r2
                    continue
                if r.status_code == 404: return r
        except Exception:
            continue

    raise ConnectionError(f"Yahoo auth endpoint failed: {path}")


# ── Status endpoint ────────────────────────────────────────────────────────────

def auth_status() -> dict:
    """Return auth status for the /auth/status endpoint."""
    from auth.credential_manager import status
    return status()
