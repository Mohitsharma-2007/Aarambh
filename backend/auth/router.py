"""
auth/router.py — Credential management API endpoints
"""
from fastapi import APIRouter, Body, HTTPException
from auth.credential_manager import (
    set_google_cookies, set_yahoo_credentials,
    set_yahoo_crumb as _set_crumb, status, load, save
)
from auth.auth_session import get_crumb_now
from typing import Optional

router = APIRouter()


@router.get("/status",
    summary="Auth status — which credentials are loaded",
    description="""
Shows current authentication status for Google Finance and Yahoo Finance.

Tells you:
- Which cookies are stored (names only, values masked)
- Whether crumb is valid
- Which endpoints need auth vs work freely
""")
async def auth_status():
    return status()


@router.post("/google/cookies",
    summary="Set Google Finance cookies",
    description="""
Set Google Finance authentication cookies.

**How to get your cookies:**
1. Open Chrome → go to https://finance.google.com
2. Sign into your Google account (optional but improves reliability)
3. Press F12 → Network tab → refresh page
4. Click any request to google.com
5. In Request Headers, copy the entire `cookie:` value

**Key cookies (most important):**
- `__Secure-1PSID` — primary auth (modern Chrome)
- `__Secure-3PSID` — secondary auth
- `SID`, `HSID`, `SSID`, `APISID`, `SAPISID` — session cookies

**Note:** Basic endpoints (quotes, markets, charts) work WITHOUT cookies.
Cookies help with: search results, overview page, less bot detection.
""")
async def set_google(
    cookie_string: str = Body(..., embed=True,
        description="Full cookie string from DevTools e.g. 'SID=xxx; HSID=xxx; ...'"),
    bearer_token: Optional[str] = Body(None, embed=True,
        description="Optional Authorization Bearer token (starts with ya29.)"),
):
    if len(cookie_string) < 10:
        raise HTTPException(400, "Cookie string too short — paste the full value from DevTools")

    set_google_cookies(
        cookie_string=cookie_string,
        bearer_token=bearer_token or "",
        source="api"
    )
    s = status()
    return {
        "success":      True,
        "message":      "Google cookies saved",
        "cookie_count": s["google"]["cookie_count"],
        "key_cookies":  s["google"]["key_cookies"],
        "source":       "api",
    }


@router.post("/yahoo/cookies",
    summary="Set Yahoo Finance cookies",
    description="""
Set Yahoo Finance authentication cookies.

**How to get your cookies:**
1. Open Chrome → go to https://finance.yahoo.com
2. Press F12 → Network tab → refresh page
3. Click any request to finance.yahoo.com
4. In Request Headers, copy the `cookie:` value

**Key cookies:**
- `A1` — main session cookie (REQUIRED for crumb)
- `A3` — authentication
- `GUC` — geo/user cookie

**Why needed:** Yahoo Finance v10 (full quote data) requires a crumb token.
The crumb is fetched automatically using these cookies.
""")
async def set_yahoo(
    cookie_string: str = Body(..., embed=True,
        description="Full Yahoo cookie string e.g. 'A1=xxx; A3=xxx; GUC=xxx; ...'"),
    crumb: Optional[str] = Body(None, embed=True,
        description="Optional: pre-fetched crumb value"),
):
    if len(cookie_string) < 5:
        raise HTTPException(400, "Cookie string too short")

    set_yahoo_credentials(
        cookie_string=cookie_string,
        crumb=crumb or "",
        source="api"
    )
    s = status()
    return {
        "success":      True,
        "message":      "Yahoo cookies saved",
        "cookie_count": s["yahoo"]["cookie_count"],
        "key_cookies":  s["yahoo"]["key_cookies"],
        "crumb_stored": bool(crumb),
        "note":         "Crumb will be auto-fetched on next v10 request if not provided",
    }


@router.post("/yahoo/crumb",
    summary="Set Yahoo crumb directly",
    description="""
Set a Yahoo Finance crumb token directly.

**How to get your crumb:**
Run this in browser console on finance.yahoo.com:
```javascript
fetch('https://query1.finance.yahoo.com/v1/test/getcrumb', {credentials:'include'})
  .then(r => r.text()).then(t => console.log('CRUMB:', t))
```

**Crumb validity:** ~5 minutes. The API auto-refreshes it using stored cookies.
""")
async def set_crumb(
    crumb: str = Body(..., embed=True, description="Yahoo crumb value"),
):
    _set_crumb(crumb)
    save()
    return {"success": True, "crumb_set": True, "note": "Crumb valid for ~5 minutes, then auto-refreshes"}


@router.post("/yahoo/refresh-crumb",
    summary="Force-refresh Yahoo crumb now",
    description="Fetches a fresh crumb from Yahoo using stored cookies. Requires Yahoo cookies to be set.")
async def refresh_crumb():
    crumb = await get_crumb_now()
    if crumb:
        return {"success": True, "crumb_refreshed": True,
                "crumb_preview": crumb[:8] + "..."}
    else:
        return {"success": False,
                "message": "Crumb fetch failed — set Yahoo cookies first via POST /auth/yahoo/cookies",
                "note": "Without cookies, Yahoo v10 endpoints will still try to work via alternative methods"}


@router.delete("/google",
    summary="Clear Google credentials")
async def clear_google():
    set_google_cookies(cookie_string="", bearer_token="", source="cleared")
    return {"success": True, "message": "Google credentials cleared"}


@router.delete("/yahoo",
    summary="Clear Yahoo credentials")
async def clear_yahoo():
    set_yahoo_credentials(cookie_string="", crumb="", source="cleared")
    return {"success": True, "message": "Yahoo credentials cleared"}


@router.get("/guide",
    summary="How to extract credentials from your browser",
    description="Step-by-step instructions for getting cookies from Chrome, Firefox, or Edge.")
async def guide():
    return {
        "method_1_devtools": {
            "title":    "Browser DevTools (Recommended — always works)",
            "steps":    [
                "Open Chrome/Edge/Firefox",
                "Go to https://finance.google.com (sign in if you want)",
                "Press F12 to open DevTools",
                "Click the 'Network' tab",
                "Refresh the page (F5)",
                "Click any request to google.com in the list",
                "In the right panel, scroll to 'Request Headers'",
                "Find the 'cookie:' line",
                "Copy EVERYTHING after 'cookie: '",
                "Paste into POST /auth/google/cookies",
            ],
            "for_yahoo": [
                "Go to https://finance.yahoo.com",
                "Press F12 → Network → refresh",
                "Click any request to finance.yahoo.com",
                "Copy the 'cookie:' header value",
                "Paste into POST /auth/yahoo/cookies",
            ],
        },
        "method_2_console": {
            "title":    "Browser Console (quick crumb extraction)",
            "steps":    [
                "Go to https://finance.yahoo.com",
                "Press F12 → Console tab",
                "Paste this code:",
                "fetch('https://query1.finance.yahoo.com/v1/test/getcrumb',{credentials:'include'}).then(r=>r.text()).then(t=>console.log('CRUMB:',t))",
                "Copy the crumb value from console output",
                "Paste into POST /auth/yahoo/crumb",
            ],
        },
        "method_3_script": {
            "title":    "Python extractor script (automated)",
            "command":  "python extract_tokens.py",
            "note":     "Interactive script — guides you through copy-paste or reads Chrome/Firefox database",
        },
        "method_4_env": {
            "title":    "Environment variables",
            "vars": {
                "GOOGLE_COOKIE_STRING": "Full cookie string for Google Finance",
                "GOOGLE_BEARER_TOKEN":  "Bearer token (ya29.xxx) if available",
                "YAHOO_COOKIE_STRING":  "Full cookie string for Yahoo Finance",
                "YAHOO_CRUMB":          "Yahoo crumb if pre-fetched",
            },
            "note": "Set before starting: python main.py",
        },
        "important_notes": [
            "Basic quotes/charts/markets work WITHOUT any credentials",
            "Credentials help with: Yahoo full quote, financials, holders",
            "Credentials reduce bot detection on Google Finance search/overview",
            "Cookies typically last 1-7 days before needing refresh",
            "Yahoo crumb expires in ~5 minutes but auto-refreshes with stored cookies",
            "Never commit credentials.json to git — it is in .gitignore",
        ],
    }
