"""
auth/credential_manager.py
===========================
Manages Google and Yahoo Finance credentials.

Credential types accepted:
  Google:
    - Cookie string  (copied from browser DevTools)
    - Bearer token   (Authorization header value)
    - Individual cookie dict

  Yahoo:
    - Cookie string  (A1, A3, GUC, GUCS cookies)
    - Crumb          (obtained via getcrumb endpoint)

Storage: credentials.json (gitignored)
Load:    from env vars OR credentials.json
Update:  via API endpoint or script

IMPORTANT: Never commit credentials.json to git.
"""

import json, os, time, re
from pathlib import Path
from typing import Optional, Dict

CRED_FILE = Path(__file__).parent / "credentials.json"

# ── Credential schema ──────────────────────────────────────────────────────────
DEFAULT = {
    "google": {
        "cookies":       {},          # dict of cookie name → value
        "cookie_string": "",          # raw string from browser
        "bearer_token":  "",          # Authorization: Bearer <token>
        "updated_at":    0,
        "source":        "",          # "manual" | "extractor" | "env"
    },
    "yahoo": {
        "cookies":       {},          # A1, A3, GUC, GUCS, etc.
        "cookie_string": "",
        "crumb":         "",
        "crumb_time":    0,
        "updated_at":    0,
        "source":        "",
    },
}

_creds: dict = {}

# ── Load ───────────────────────────────────────────────────────────────────────

def load() -> dict:
    """Load credentials from file → env → defaults (in that order)."""
    global _creds
    _creds = json.loads(json.dumps(DEFAULT))  # deep copy

    # 1. Load from file
    if CRED_FILE.exists():
        try:
            saved = json.loads(CRED_FILE.read_text())
            _deep_merge(_creds, saved)
        except Exception:
            pass

    # 2. Override from environment variables
    _load_from_env()

    return _creds


def _load_from_env():
    """Load credentials from environment variables."""
    # Google
    if v := os.getenv("GOOGLE_COOKIE_STRING"):
        _creds["google"]["cookie_string"] = v
        _creds["google"]["cookies"] = _parse_cookie_string(v)
        _creds["google"]["source"] = "env"

    if v := os.getenv("GOOGLE_BEARER_TOKEN"):
        _creds["google"]["bearer_token"] = v.removeprefix("Bearer ").strip()
        _creds["google"]["source"] = "env"

    # Yahoo
    if v := os.getenv("YAHOO_COOKIE_STRING"):
        _creds["yahoo"]["cookie_string"] = v
        _creds["yahoo"]["cookies"] = _parse_cookie_string(v)
        _creds["yahoo"]["source"] = "env"

    if v := os.getenv("YAHOO_CRUMB"):
        _creds["yahoo"]["crumb"] = v
        _creds["yahoo"]["crumb_time"] = time.time()
        _creds["yahoo"]["source"] = "env"


def _deep_merge(base: dict, update: dict):
    for k, v in update.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


# ── Save ───────────────────────────────────────────────────────────────────────

def save():
    """Persist credentials to file."""
    CRED_FILE.parent.mkdir(exist_ok=True)
    CRED_FILE.write_text(json.dumps(_creds, indent=2))


# ── Getters ───────────────────────────────────────────────────────────────────

def get_google_headers(extra: Dict = None) -> dict:
    """Build full HTTP headers including Google auth cookies + bearer token."""
    if not _creds:
        load()

    headers: Dict[str, str] = {}

    cookie_str = _creds["google"].get("cookie_string", "")
    if cookie_str:
        headers["Cookie"] = cookie_str

    bearer = _creds["google"].get("bearer_token", "")
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"

    if extra:
        headers.update(extra)

    return headers


def get_yahoo_cookies() -> dict:
    """Return Yahoo cookie dict for requests."""
    if not _creds:
        load()
    return _creds["yahoo"].get("cookies", {})


def get_yahoo_cookie_string() -> str:
    if not _creds:
        load()
    return _creds["yahoo"].get("cookie_string", "")


def get_yahoo_crumb() -> Optional[str]:
    if not _creds:
        load()
    crumb = _creds["yahoo"].get("crumb", "")
    crumb_age = time.time() - _creds["yahoo"].get("crumb_time", 0)
    if crumb and crumb_age < 300:   # 5-minute crumb validity
        return crumb
    return None


def has_google_auth() -> bool:
    if not _creds:
        load()
    return bool(
        _creds["google"].get("cookie_string") or
        _creds["google"].get("bearer_token") or
        _creds["google"].get("cookies")
    )


def has_yahoo_auth() -> bool:
    if not _creds:
        load()
    return bool(
        _creds["yahoo"].get("cookie_string") or
        _creds["yahoo"].get("crumb")
    )


# ── Setters ───────────────────────────────────────────────────────────────────

def set_google_cookies(cookie_string: str = "", cookie_dict: Dict = None,
                        bearer_token: str = "", source: str = "manual"):
    if not _creds:
        load()

    if cookie_string:
        _creds["google"]["cookie_string"] = cookie_string.strip()
        _creds["google"]["cookies"] = _parse_cookie_string(cookie_string)

    if cookie_dict:
        _creds["google"]["cookies"].update(cookie_dict)
        # Rebuild cookie string
        _creds["google"]["cookie_string"] = "; ".join(
            f"{k}={v}" for k, v in _creds["google"]["cookies"].items()
        )

    if bearer_token:
        _creds["google"]["bearer_token"] = bearer_token.removeprefix("Bearer ").strip()

    _creds["google"]["updated_at"] = time.time()
    _creds["google"]["source"] = source
    save()


def set_yahoo_credentials(cookie_string: str = "", cookie_dict: Dict = None,
                           crumb: str = "", source: str = "manual"):
    if not _creds:
        load()

    if cookie_string:
        _creds["yahoo"]["cookie_string"] = cookie_string.strip()
        _creds["yahoo"]["cookies"] = _parse_cookie_string(cookie_string)

    if cookie_dict:
        _creds["yahoo"]["cookies"].update(cookie_dict)
        _creds["yahoo"]["cookie_string"] = "; ".join(
            f"{k}={v}" for k, v in _creds["yahoo"]["cookies"].items()
        )

    if crumb:
        _creds["yahoo"]["crumb"] = crumb
        _creds["yahoo"]["crumb_time"] = time.time()

    _creds["yahoo"]["updated_at"] = time.time()
    _creds["yahoo"]["source"] = source
    save()


def set_yahoo_crumb(crumb: str):
    if not _creds:
        load()
    _creds["yahoo"]["crumb"] = crumb
    _creds["yahoo"]["crumb_time"] = time.time()
    save()


# ── Utilities ──────────────────────────────────────────────────────────────────

def _parse_cookie_string(cookie_str: str) -> Dict[str, str]:
    """Parse 'name=value; name2=value2' into a dict."""
    result = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            name, _, value = part.partition("=")
            result[name.strip()] = value.strip()
    return result


def status() -> dict:
    """Return credential status summary (no secrets exposed)."""
    if not _creds:
        load()

    def _mask(s: str) -> str:
        if not s: return ""
        return s[:8] + "..." + s[-4:] if len(s) > 16 else "****"

    g = _creds["google"]
    y = _creds["yahoo"]

    google_cookies = list(g.get("cookies", {}).keys())
    yahoo_cookies  = list(y.get("cookies", {}).keys())

    return {
        "google": {
            "authenticated":  has_google_auth(),
            "bearer_token":   bool(g.get("bearer_token")),
            "cookie_count":   len(google_cookies),
            "key_cookies":    [c for c in google_cookies
                               if c in ("SID","__Secure-1PSID","__Secure-3PSID","SAPISID","APISID","HSID","SSID")],
            "all_cookies":    google_cookies,
            "source":         g.get("source", "none"),
            "updated_at":     g.get("updated_at", 0),
        },
        "yahoo": {
            "authenticated":  has_yahoo_auth(),
            "crumb":          bool(y.get("crumb")),
            "crumb_age_sec":  int(time.time() - y.get("crumb_time", 0)) if y.get("crumb") else None,
            "crumb_valid":    bool(get_yahoo_crumb()),
            "cookie_count":   len(yahoo_cookies),
            "key_cookies":    [c for c in yahoo_cookies if c in ("A1","A3","GUC","GUCS","cmp","thamba")],
            "all_cookies":    yahoo_cookies,
            "source":         y.get("source", "none"),
        },
        "instructions": {
            "google_no_auth_needed": [
                "quote/{ticker}/{exchange}",
                "market/indexes,gainers,losers,crypto,currencies,futures,etfs",
                "chart/{ticker}",
                "news/{ticker}",
            ],
            "google_auth_improves": [
                "overview (fewer bot blocks)",
                "search (less bot detection)",
            ],
            "yahoo_needs_crumb": [
                "yahoo-finance/quote/{ticker} (v10 quoteSummary)",
                "yahoo-finance/financials/{ticker}",
                "yahoo-finance/holders/{ticker}",
            ],
            "yahoo_no_auth": [
                "yahoo-finance/chart/{ticker} (v8)",
                "yahoo-finance/options/{ticker} (v7)",
                "yahoo-finance/movers",
                "yahoo-finance/search",
                "yahoo-finance/trending",
                "yahoo-finance/sparkline",
            ],
        }
    }


# Auto-load on import
load()
