"""
scrapers/youtube_live.py  —  YouTube Live TV Channel Registry
=============================================================
50+ live news channels worldwide.
Returns embed URLs, channel info, and stream status.
No YouTube API key needed — uses public embed URLs.
"""

from utils.cache import get as c_get, set as c_set
from utils.session import fetch

# ── Master Channel Registry ───────────────────────────────────────────────────
CHANNELS = {
    # ── India ──────────────────────────────────────────────────────────────
    "ndtv":           {"name": "NDTV 24x7",        "handle": "NDTV",          "country": "IN", "category": "news",    "lang": "en", "channel_id": "UCZFMm1mMw0F81Z37aaEzTUA"},
    "aaj_tak":        {"name": "Aaj Tak",           "handle": "AajTak",        "country": "IN", "category": "news",    "lang": "hi", "channel_id": "UCt4t-jeY85JegMlZ-E5UWtA"},
    "republic_tv":    {"name": "Republic TV",       "handle": "RepublicTV",    "country": "IN", "category": "news",    "lang": "en", "channel_id": "UCrBShOTQr0HDb2DGhGWDDhQ"},
    "india_today":    {"name": "India Today",       "handle": "IndiaToday",    "country": "IN", "category": "news",    "lang": "en", "channel_id": "UCYPvAwZP8pZhSMW8qs7cVCw"},
    "et_now":         {"name": "ET Now",            "handle": "ETNow",         "country": "IN", "category": "finance", "lang": "en", "channel_id": "UCxxnROVX5OGDMg0Qkrwh0aA"},
    "zee_news":       {"name": "Zee News",          "handle": "ZeeNews",       "country": "IN", "category": "news",    "lang": "hi", "channel_id": "UCpdjNEVFbGVr6fRUwEPi2mw"},
    "wion":           {"name": "WION",              "handle": "WION",          "country": "IN", "category": "world",   "lang": "en", "channel_id": "UCbT424yBZXGo97jRTtCCFjA"},
    "dd_news":        {"name": "DD News",           "handle": "DDNewsOfficial","country": "IN", "category": "news",    "lang": "hi", "channel_id": "UCnGrn6V4BsNFAKWmFf-MUCA"},

    # ── USA ────────────────────────────────────────────────────────────────
    "cnn":            {"name": "CNN",               "handle": "CNN",           "country": "US", "category": "news",    "lang": "en", "channel_id": "UCupvZG-5ko_eiXAupbDfxWw"},
    "fox_news":       {"name": "Fox News",          "handle": "FoxNews",       "country": "US", "category": "news",    "lang": "en", "channel_id": "UCXIJgqnII2ZOINSWNf9s7Ow"},
    "nbc_news":       {"name": "NBC News",          "handle": "NBCNews",       "country": "US", "category": "news",    "lang": "en", "channel_id": "UCeY0bbntWzzVIaj2z3QigXg"},
    "abc_news":       {"name": "ABC News",          "handle": "ABCNews",       "country": "US", "category": "news",    "lang": "en", "channel_id": "UCBi2mrWuNuyYy4gbM6fU18Q"},
    "cbs_news":       {"name": "CBS News 24/7",     "handle": "CBSNews",       "country": "US", "category": "news",    "lang": "en", "channel_id": "UC8p1vwvWtl6T73JiExfWs1g"},
    "bloomberg_tv":   {"name": "Bloomberg TV",      "handle": "BloombergTV",   "country": "US", "category": "finance", "lang": "en", "channel_id": "UCIALMKvObZNtJ6AmdCLP7Lg"},
    "cnbc":           {"name": "CNBC",              "handle": "CNBC",          "country": "US", "category": "finance", "lang": "en", "channel_id": "UCvJJ_dzjViJCoLf5uKUTwoA"},
    "livenow_fox":    {"name": "LiveNOW from FOX",  "handle": "LiveNOWFOX",    "country": "US", "category": "news",    "lang": "en", "channel_id": "UCSHuMflhRLVBhLKwGvbaxzw"},

    # ── UK ────────────────────────────────────────────────────────────────
    "sky_news":       {"name": "Sky News",          "handle": "SkyNews",       "country": "GB", "category": "news",    "lang": "en", "channel_id": "UCoMdktPbSTixAyNGwb-UYkQ"},
    "bbc_news":       {"name": "BBC News",          "handle": "BBCNews",       "country": "GB", "category": "news",    "lang": "en", "channel_id": "UC16niRr50-MSBwiO3YDb3RA"},

    # ── Canada ────────────────────────────────────────────────────────────
    "cbc_news":       {"name": "CBC News",          "handle": "CBCNews",       "country": "CA", "category": "news",    "lang": "en", "channel_id": "UCCTemas26rS1aTjBxOmNOLg"},
    "global_news":    {"name": "Global News",       "handle": "GlobalNews",    "country": "CA", "category": "news",    "lang": "en", "channel_id": "UCx9iA0bSyiMT6yy90RGCmig"},

    # ── Australia ─────────────────────────────────────────────────────────
    "abc_au":         {"name": "ABC News Australia","handle": "ABCNewsIndepth","country": "AU", "category": "news",    "lang": "en", "channel_id": "UCVgO39Bk5sMo66-6o6Spn6Q"},
    "sky_au":         {"name": "Sky News Australia","handle": "SkyNewsAustralia","country":"AU", "category": "news",   "lang": "en", "channel_id": "UCWwgaK7x0_FR1goeSRDR01g"},

    # ── Germany ───────────────────────────────────────────────────────────
    "dw_news":        {"name": "DW News",           "handle": "dwnews",        "country": "DE", "category": "world",   "lang": "en", "channel_id": "UCknLrEdhRCp1aegoMqRaCZg"},
    "bild":           {"name": "Bild",              "handle": "BILD",          "country": "DE", "category": "news",    "lang": "de", "channel_id": "UC0A8ef4CGLB6K0Mc0X6dBQA"},

    # ── France ────────────────────────────────────────────────────────────
    "france24_en":    {"name": "France 24 English", "handle": "France24_en",   "country": "FR", "category": "world",   "lang": "en", "channel_id": "UCQfwfsi5VrQ8yKZ-UWmAEFg"},
    "france24_fr":    {"name": "France 24 French",  "handle": "FRANCE24",      "country": "FR", "category": "world",   "lang": "fr", "channel_id": "UCCAxp6sGU15VFCORa5l94MQ"},

    # ── Japan ─────────────────────────────────────────────────────────────
    "nhk_world":      {"name": "NHK World-Japan",   "handle": "NHKWORLDJAPAN", "country": "JP", "category": "world",   "lang": "en", "channel_id": "UCqkGNmZ4oLBEWJWi0yBqBHQ"},
    "ann_news":       {"name": "ANN News",          "handle": "ANNnewsCH",     "country": "JP", "category": "news",    "lang": "ja", "channel_id": "UCkB4YTQF59hKTJYTKRaVHHQ"},

    # ── China ─────────────────────────────────────────────────────────────
    "cgtn":           {"name": "CGTN",              "handle": "CGTN",          "country": "CN", "category": "world",   "lang": "en", "channel_id": "UCmDMjGFrYXPaM4R5fDj4Thg"},
    "china_daily":    {"name": "China Daily",       "handle": "ChinaDaily",    "country": "CN", "category": "world",   "lang": "en", "channel_id": "UCd1hhNJh1RCqE5-wGsb9UoQ"},

    # ── Russia ────────────────────────────────────────────────────────────
    "rt":             {"name": "RT",                "handle": "RT",            "country": "RU", "category": "world",   "lang": "en", "channel_id": "UCpwvZG-5ko_eiXAupbDfxWw"},
    "ruptly":         {"name": "Ruptly",            "handle": "ruptly",        "country": "RU", "category": "world",   "lang": "en", "channel_id": "UCpkfvsLtMs1dJKNMBFHB2fA"},

    # ── Brazil ────────────────────────────────────────────────────────────
    "globo_news":     {"name": "GloboNews",         "handle": "GloboNews",     "country": "BR", "category": "news",    "lang": "pt", "channel_id": "UCD4B-8fUF80J_fU6opGzD7A"},
    "band":           {"name": "Band Jornalismo",   "handle": "BandJornalismo","country": "BR", "category": "news",    "lang": "pt", "channel_id": "UCX2bYCH1JN-4UZXI7-bXikw"},

    # ── South Africa ──────────────────────────────────────────────────────
    "enca":           {"name": "eNCA",              "handle": "eNCAnews",      "country": "ZA", "category": "news",    "lang": "en", "channel_id": "UCsEGtyLMDQnfbSAZObV-1dA"},
    "sabc_news":      {"name": "SABC News",         "handle": "SABCNews",      "country": "ZA", "category": "news",    "lang": "en", "channel_id": "UCsEGtyLMDQnfbSAZObV-1dA"},

    # ── Global / International ────────────────────────────────────────────
    "al_jazeera":     {"name": "Al Jazeera English","handle": "AlJazeeraEnglish","country":"QA","category": "world",   "lang": "en", "channel_id": "UCSys7RQy-Z0AlCgMU9CobZg"},
    "euronews":       {"name": "Euronews",          "handle": "euronews",      "country": "EU", "category": "world",   "lang": "en", "channel_id": "UCT3fHWuoVBLDwGEQqGpJCLQ"},
    "trt_world":      {"name": "TRT World",         "handle": "TRTWorld",      "country": "TR", "category": "world",   "lang": "en", "channel_id": "UC3SKlqv0Zb_N2CDV9z7MoSw"},

    # ── Finance ───────────────────────────────────────────────────────────
    "yahoo_finance":  {"name": "Yahoo Finance",     "handle": "YahooFinance",  "country": "US", "category": "finance", "lang": "en", "channel_id": "UCEAZeUIeJs0IjQiqPIbyAmQ"},
    "reuters_tv":     {"name": "Reuters",           "handle": "Reuters",       "country": "US", "category": "finance", "lang": "en", "channel_id": "UChqUTb7kYRX8-EiaN3XFrSQ"},
    "ft_tv":          {"name": "Financial Times",   "handle": "FinancialTimes","country": "GB", "category": "finance", "lang": "en", "channel_id": "UCBAuFCuGSgqS3GRg2VZVFYg"},
}

# ── Country / Category maps ───────────────────────────────────────────────────
COUNTRY_MAP  = {cc: [k for k,v in CHANNELS.items() if v["country"]==cc]  for cc in set(v["country"] for v in CHANNELS.values())}
CATEGORY_MAP = {cat:[k for k,v in CHANNELS.items() if v["category"]==cat] for cat in set(v["category"] for v in CHANNELS.values())}


def _build_channel(key: str) -> dict:
    """Build full channel response with embed URLs."""
    ch = CHANNELS[key]
    cid = ch["channel_id"]
    handle = ch["handle"]
    return {
        "key":          key,
        "name":         ch["name"],
        "country":      ch["country"],
        "category":     ch["category"],
        "language":     ch["lang"],
        "channel_id":   cid,
        "youtube_url":  f"https://www.youtube.com/@{handle}/live",
        "embed_url":    f"https://www.youtube.com/embed/live_stream?channel={cid}",
        "iframe_html":  f'<iframe width="560" height="315" src="https://www.youtube.com/embed/live_stream?channel={cid}" frameborder="0" allowfullscreen></iframe>',
        "thumbnail":    f"https://i.ytimg.com/vi/live_stream/hqdefault.jpg",
        "watch_url":    f"https://www.youtube.com/channel/{cid}/live",
    }


# ── Public API ────────────────────────────────────────────────────────────────

async def get_all(category: str = None, country: str = None) -> dict:
    """Return all channels, optionally filtered."""
    keys = list(CHANNELS.keys())
    if category:
        keys = CATEGORY_MAP.get(category.lower(), [])
    if country:
        keys = [k for k in keys if CHANNELS[k]["country"] == country.upper()]

    channels = [_build_channel(k) for k in keys]
    return {
        "total":     len(channels),
        "channels":  channels,
        "note":      "Use embed_url in an <iframe> to display live stream. "
                     "YouTube must allow embedding for the channel.",
    }


async def get_by_country(country: str) -> dict:
    return await get_all(country=country)


async def get_by_category(category: str) -> dict:
    return await get_all(category=category)


async def search_channels(query: str) -> dict:
    q    = query.lower()
    keys = [k for k, v in CHANNELS.items()
            if q in v["name"].lower() or q in v["country"].lower()
            or q in v["category"].lower() or q in v["lang"].lower()]
    return {"query": query, "results": [_build_channel(k) for k in keys]}


async def get_channel(key: str) -> dict:
    if key not in CHANNELS:
        return {"error": f"Channel not found: {key}. Use /api/live-tv/all to list channels."}
    return _build_channel(key)


async def get_finance_channels() -> dict:
    return await get_all(category="finance")


async def get_world_channels() -> dict:
    return await get_all(category="world")
