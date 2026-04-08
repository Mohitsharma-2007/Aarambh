"""
AARAMBH Web Scraping Engine — Google Finance, Google News, Social Media
Extracts structured data similar to SerpAPI format but free
"""
import asyncio
import re
import json
import httpx
from typing import Optional, List, Dict, Any
from loguru import logger
from datetime import datetime, timedelta
from urllib.parse import quote, urlencode


class WebScrapingEngine:
    """Centralized web scraping for financial data, news and social media"""

    GOOGLE_FINANCE_BASE = "https://www.google.com/finance"
    GOOGLE_NEWS_BASE = "https://news.google.com"
    GOOGLE_SEARCH_BASE = "https://www.google.com/search"
    YAHOO_FINANCE_BASE = "https://finance.yahoo.com"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Cache-Control": "no-cache",
    }

    # Major Indian stocks for NIFTY 50 + popular mid/small caps
    INDIAN_STOCKS = {
        # NIFTY 50 constituents
        "RELIANCE": "RELIANCE:NSE", "TCS": "TCS:NSE", "HDFCBANK": "HDFCBANK:NSE",
        "INFY": "INFY:NSE", "ICICIBANK": "ICICIBANK:NSE", "HINDUNILVR": "HINDUNILVR:NSE",
        "ITC": "ITC:NSE", "SBIN": "SBIN:NSE", "BHARTIARTL": "BHARTIARTL:NSE",
        "KOTAKBANK": "KOTAKBANK:NSE", "LT": "LT:NSE", "AXISBANK": "AXISBANK:NSE",
        "BAJFINANCE": "BAJFINANCE:NSE", "ASIANPAINT": "ASIANPAINT:NSE", "MARUTI": "MARUTI:NSE",
        "HCLTECH": "HCLTECH:NSE", "SUNPHARMA": "SUNPHARMA:NSE", "TITAN": "TITAN:NSE",
        "WIPRO": "WIPRO:NSE", "ULTRACEMCO": "ULTRACEMCO:NSE", "NESTLEIND": "NESTLEIND:NSE",
        "TATAMOTORS": "TATAMOTORS:NSE", "JSWSTEEL": "JSWSTEEL:NSE", "POWERGRID": "POWERGRID:NSE",
        "NTPC": "NTPC:NSE", "COALINDIA": "COALINDIA:NSE", "ADANIENT": "ADANIENT:NSE",
        "ADANIPORTS": "ADANIPORTS:NSE", "TECHM": "TECHM:NSE", "ONGC": "ONGC:NSE",
        "DRREDDY": "DRREDDY:NSE", "HEROMOTOCO": "HEROMOTOCO:NSE", "CIPLA": "CIPLA:NSE",
        "BAJAJ-AUTO": "BAJAJ-AUTO:NSE", "GRASIM": "GRASIM:NSE", "DIVISLAB": "DIVISLAB:NSE",
        "BPCL": "BPCL:NSE", "EICHERMOT": "EICHERMOT:NSE", "TATACONSUM": "TATACONSUM:NSE",
        "APOLLOHOSP": "APOLLOHOSP:NSE", "BRITANNIA": "BRITANNIA:NSE", "TATASTEEL": "TATASTEEL:NSE",
        "INDUSINDBK": "INDUSINDBK:NSE", "SHRIRAMFIN": "SHRIRAMFIN:NSE", "HINDALCO": "HINDALCO:NSE",
        "HDFCLIFE": "HDFCLIFE:NSE", "SBILIFE": "SBILIFE:NSE", "M&M": "M&M:NSE",
        "BAJAJFINSV": "BAJAJFINSV:NSE", "BEL": "BEL:NSE",
        # Popular mid-caps
        "TATAPOWER": "TATAPOWER:NSE", "IRFC": "IRFC:NSE", "ZOMATO": "ZOMATO:NSE",
        "PAYTM": "PAYTM:NSE", "NYKAA": "NYKAA:NSE", "DELHIVERY": "DELHIVERY:NSE",
        "POLICYBZR": "POLICYBZR:NSE", "IRCTC": "IRCTC:NSE", "HAL": "HAL:NSE",
        "BHEL": "BHEL:NSE", "SAIL": "SAIL:NSE", "NHPC": "NHPC:NSE",
        "RECLTD": "RECLTD:NSE", "PFC": "PFC:NSE", "BANKBARODA": "BANKBARODA:NSE",
        "CANBK": "CANBK:NSE", "IOB": "IOB:NSE", "VEDL": "VEDL:NSE",
        "TRENT": "TRENT:NSE", "JIOFIN": "JIOFIN:NSE", "ABB": "ABB:NSE",
        "SIEMENS": "SIEMENS:NSE", "HAVELLS": "HAVELLS:NSE", "PIDILITIND": "PIDILITIND:NSE",
        # Global majors
        "AAPL": "AAPL:NASDAQ", "MSFT": "MSFT:NASDAQ", "GOOG": "GOOG:NASDAQ",
        "AMZN": "AMZN:NASDAQ", "META": "META:NASDAQ", "NVDA": "NVDA:NASDAQ",
        "TSLA": "TSLA:NASDAQ", "AMD": "AMD:NASDAQ", "AVGO": "AVGO:NASDAQ",
    }

    def __init__(self):
        self.http_client = httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
            headers=self.HEADERS,
        )
        self._cache: Dict[str, Any] = {}
        self._cache_time: Dict[str, datetime] = {}

    def _cache_get(self, key: str, ttl: int = 300):
        if key in self._cache and self._cache_time.get(key, datetime.min) > datetime.now() - timedelta(seconds=ttl):
            return self._cache[key]
        return None

    def _cache_set(self, key: str, value: Any):
        self._cache[key] = value
        self._cache_time[key] = datetime.now()

    # ─────────────────────────────────────────────────────────────────────────
    # Google Finance Scraper
    # ─────────────────────────────────────────────────────────────────────────

    async def google_finance_quote(self, symbol: str) -> Optional[dict]:
        """Scrape Google Finance for stock quote data"""
        cached = self._cache_get(f"gf_quote:{symbol}", ttl=120)
        if cached:
            return cached

        gf_ticker = self.INDIAN_STOCKS.get(symbol.upper(), f"{symbol.upper()}:NASDAQ")
        url = f"{self.GOOGLE_FINANCE_BASE}/quote/{gf_ticker}"

        try:
            resp = await self.http_client.get(url)
            if resp.status_code != 200:
                logger.warning(f"Google Finance {symbol}: HTTP {resp.status_code}")
                return None

            html = resp.text
            result = self._parse_google_finance(html, symbol)
            if result:
                self._cache_set(f"gf_quote:{symbol}", result)
            return result
        except Exception as e:
            logger.warning(f"Google Finance scrape error for {symbol}: {e}")
            return None

    def _parse_google_finance(self, html: str, symbol: str) -> Optional[dict]:
        """Parse Google Finance HTML for structured data"""
        try:
            # Extract price from data attributes or text
            price_match = re.search(r'data-last-price="([0-9,.]+)"', html)
            change_match = re.search(r'data-last-normal-market-change="([+-]?[0-9,.]+)"', html)
            pct_match = re.search(r'data-last-normal-market-change-percent="([+-]?[0-9,.]+)"', html)

            # Fallback: parse from visible text
            if not price_match:
                price_match = re.search(r'class="YMlKec fxKbKc"[^>]*>[\$₹€£]?([0-9,]+\.?[0-9]*)', html)
            if not price_match:
                price_match = re.search(r'class="[^"]*fxKbKc[^"]*"[^>]*>[\$₹€£]?([0-9,]+\.?[0-9]*)', html)

            # Extract company name
            name_match = re.search(r'<div class="zzDege"[^>]*>([^<]+)</div>', html)
            if not name_match:
                name_match = re.search(r'data-company-name="([^"]+)"', html)

            # Extract exchange info
            exchange_match = re.search(r'<div class="PdOqHc"[^>]*>([^<]+)</div>', html)

            price = float(price_match.group(1).replace(',', '')) if price_match else 0
            change = float(change_match.group(1).replace(',', '')) if change_match else 0
            change_pct = float(pct_match.group(1).replace(',', '')) if pct_match else 0
            name = name_match.group(1) if name_match else symbol
            exchange = exchange_match.group(1) if exchange_match else ""

            # Extract key stats from the page
            result = {
                "symbol": symbol,
                "name": name,
                "price": price,
                "change": change,
                "changePercent": change_pct,
                "exchange": exchange,
                "currency": "INR" if ":NSE" in self.INDIAN_STOCKS.get(symbol, "") or ":BSE" in self.INDIAN_STOCKS.get(symbol, "") else "USD",
                "source": "google_finance",
                "scraped_at": datetime.utcnow().isoformat(),
            }

            # Extract additional data points from the stats table
            stats_patterns = {
                "previousClose": r'Previous close[\s\S]*?<div[^>]*>[\$₹]?([0-9,]+\.?[0-9]*)',
                "dayRange": r'Day range[\s\S]*?<div[^>]*>([0-9,]+\.?[0-9]*)\s*[-–]\s*([0-9,]+\.?[0-9]*)',
                "yearRange": r'Year range[\s\S]*?<div[^>]*>([0-9,]+\.?[0-9]*)\s*[-–]\s*([0-9,]+\.?[0-9]*)',
                "marketCap": r'Market cap[\s\S]*?<div[^>]*>([0-9,.]+[TBMK]?)',
                "pe": r'P/E ratio[\s\S]*?<div[^>]*>([0-9,.]+)',
                "dividendYield": r'Div(?:idend)? yield[\s\S]*?<div[^>]*>([0-9,.]+%?)',
                "volume": r'(?:Avg )?[Vv]olume[\s\S]*?<div[^>]*>([0-9,.]+[TBMK]?)',
            }

            for key, pattern in stats_patterns.items():
                m = re.search(pattern, html, re.IGNORECASE)
                if m:
                    if key == "dayRange" and m.lastindex and m.lastindex >= 2:
                        result["dayLow"] = float(m.group(1).replace(',', ''))
                        result["dayHigh"] = float(m.group(2).replace(',', ''))
                    elif key == "yearRange" and m.lastindex and m.lastindex >= 2:
                        result["low52w"] = float(m.group(1).replace(',', ''))
                        result["high52w"] = float(m.group(2).replace(',', ''))
                    else:
                        result[key] = m.group(1).replace(',', '')

            return result if price > 0 else None
        except Exception as e:
            logger.warning(f"Parse Google Finance error: {e}")
            return None

    # ─────────────────────────────────────────────────────────────────────────
    # Google News Scraper
    # ─────────────────────────────────────────────────────────────────────────

    async def google_news_search(self, query: str, country: str = "IN", limit: int = 20) -> List[dict]:
        """Scrape Google News search results via RSS for stability"""
        cached = self._cache_get(f"gnews:{query}:{country}", ttl=600)
        if cached:
            return cached

        # Use RSS for stability
        params = {
            "q": query,
            "hl": "en-IN" if country == "IN" else "en-US",
            "gl": country,
            "ceid": f"{country}:en"
        }
        url = f"https://news.google.com/rss/search?{urlencode(params)}"

        try:
            logger.info(f"Scraping Google News RSS: {url}")
            resp = await self.http_client.get(url)
            if resp.status_code != 200:
                logger.warning(f"Google News search RSS: HTTP {resp.status_code}")
                return []

            logger.debug(f"RSS Response received, length={len(resp.text)}")
            articles = self._parse_google_news_rss(resp.text, limit)
            logger.info(f"Extracted {len(articles)} articles from RSS")
            self._cache_set(f"gnews:{query}:{country}", articles)
            return articles
        except Exception as e:
            logger.warning(f"Google News RSS error: {e}")
            return []

    def _parse_google_news_rss(self, xml: str, limit: int) -> List[dict]:
        """Parse Google News RSS XML with robust regex"""
        articles = []
        # Support both <item> and <item ...>
        items = re.findall(r'<item[^>]*>([\s\S]*?)</item>', xml)

        for item in items[:limit]:
            title_m = re.search(r'<title[^>]*>([\s\S]*?)</title>', item)
            link_m = re.search(r'<link[^>]*>([\s\S]*?)</link>', item)
            source_m = re.search(r'<source[^>]*>([\s\S]*?)</source>', item)
            date_m = re.search(r'<pubDate[^>]*>([\s\S]*?)</pubDate>', item)
            
            if title_m:
                title_full = re.sub(r'<!\[CDATA\[|\]\]>', '', title_m.group(1)).strip()
                title = title_full
                source = re.sub(r'<!\[CDATA\[|\]\]>', '', source_m.group(1)).strip() if source_m else "News"
                if " - " in title_full:
                    title = title_full.rsplit(" - ", 1)[0]

                articles.append({
                    "title": title.strip(),
                    "source": source.strip(),
                    "link": re.sub(r'<!\[CDATA\[|\]\]>', '', link_m.group(1)).strip() if link_m else "",
                    "pubDate": date_m.group(1) if date_m else "",
                    "scraped_at": datetime.utcnow().isoformat(),
                })

        return articles

    # ─────────────────────────────────────────────────────────────────────────
    # Google AI Mode (SGE/Snippet Extractor)
    # ─────────────────────────────────────────────────────────────────────────

    async def google_ai_mode(self, query: str) -> Dict[str, Any]:
        """
        Scrapes Google for AI snippets or top descriptive content.
        Cleans HTML to avoid script/style blocks.
        """
        cached = self._cache_get(f"ai_mode:{query}", ttl=3600)
        if cached: return cached

        params = {"q": query, "hl": "en", "gl": "IN"}
        url = f"{self.GOOGLE_SEARCH_BASE}?{urlencode(params)}"
        
        try:
            resp = await self.http_client.get(url)
            html = resp.text
            
            # Clean HTML: remove script, style, nav, footer tags (case-insensitive)
            clean_html = re.sub(r'<(script|style|nav|footer|header|iframe)[^>]*>[\s\S]*?</\1>', '', html, flags=re.IGNORECASE)
            # Remove inline comments and generic tags that might contain junk
            clean_html = re.sub(r'<!--[\s\S]*?-->', '', clean_html)
            
            ai_data = {"query": query, "answer": "", "sources": [], "confidence": "high"}
            
            # Pattern 1: Look for text in high-confidence snippet classes
            # Added more modern classes seen in Google SERPs
            snippet_m = re.search(r'class="[^"]*(?:ayS70|LGOv5d|hgKElc|VwiC3b|wO508b|Uo8X3b)[^"]*"[^>]*>([\s\S]*?)</div>', clean_html)

            if snippet_m:
                text = re.sub(r'<[^>]+>', '', snippet_m.group(1)).strip()
                if len(text) > 50:
                    ai_data["answer"] = text

            if not ai_data["answer"]:
                # Pattern 2: Text density approach
                # Find the longest block of text between any tags
                candidates = re.findall(r'>([^<]{60,800})<', clean_html)
                # Sort by length, descending
                candidates.sort(key=len, reverse=True)
                
                for c in candidates:
                    text = c.strip()
                    # Basic heuristic: snippets often have a period
                    if "." in text and not text.startswith("{"):
                        ai_data["answer"] = text
                        ai_data["confidence"] = "medium"
                        break

            # 2. Extract outward links (non-google)
            links = re.findall(r'href="(https?://(?!www\.google\.)[^"]+)"', clean_html[:15000])
            ai_data["sources"] = list(set(links))[:5]

            if not ai_data["answer"]:
                ai_data["answer"] = "No summary available. Direct data tracking recommended."
                ai_data["confidence"] = "none"

            self._cache_set(f"ai_mode:{query}", ai_data)
            return ai_data
        except Exception as e:
            return {"error": str(e), "query": query}



    # ─────────────────────────────────────────────────────────────────────────
    # Google Events / Trends Scraper
    # ─────────────────────────────────────────────────────────────────────────

    async def google_events_search(self, query: str = "stock market India") -> List[dict]:
        """Scrape Google for upcoming events related to query"""
        cached = self._cache_get(f"gevents:{query}", ttl=3600)
        if cached:
            return cached

        params = {"q": f"{query} upcoming events calendar", "hl": "en", "gl": "IN"}
        url = f"{self.GOOGLE_SEARCH_BASE}?{urlencode(params)}"

        try:
            resp = await self.http_client.get(url)
            events = []

            # Parse event-like results
            event_blocks = re.findall(
                r'<div[^>]*class="[^"]*(?:mnr-c|FADMYd)[^"]*"[^>]*>([\s\S]*?)</div>',
                resp.text,
            )

            for block in event_blocks[:15]:
                title_match = re.search(r'>([^<]{10,100})<', block)
                date_match = re.search(r'(\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{1,2},?\s+\d{4})', block)
                if title_match:
                    events.append({
                        "title": title_match.group(1).strip(),
                        "date": date_match.group(1) if date_match else "",
                        "source": "google_events",
                    })

            self._cache_set(f"gevents:{query}", events)
            return events
        except Exception as e:
            logger.warning(f"Google Events scrape error: {e}")
            return []

    # ─────────────────────────────────────────────────────────────────────────
    # Yahoo Finance Scraper
    # ─────────────────────────────────────────────────────────────────────────

    async def yahoo_finance_quote(self, symbol: str) -> Optional[dict]:
        """Scrape Yahoo Finance for detailed stock data"""
        cached = self._cache_get(f"yf_scrape:{symbol}", ttl=120)
        if cached:
            return cached

        # Convert Indian stock symbols for Yahoo
        yf_symbol = symbol.upper()
        if yf_symbol in self.INDIAN_STOCKS and ":NSE" in self.INDIAN_STOCKS[yf_symbol]:
            yf_symbol = f"{yf_symbol}.NS"
        elif yf_symbol in self.INDIAN_STOCKS and ":BSE" in self.INDIAN_STOCKS[yf_symbol]:
            yf_symbol = f"{yf_symbol}.BO"

        url = f"{self.YAHOO_FINANCE_BASE}/quote/{yf_symbol}/"

        try:
            resp = await self.http_client.get(url)
            if resp.status_code != 200:
                return None

            result = self._parse_yahoo_finance(resp.text, symbol)
            if result:
                self._cache_set(f"yf_scrape:{symbol}", result)
            return result
        except Exception as e:
            logger.warning(f"Yahoo Finance scrape error for {symbol}: {e}")
            return None

    def _parse_yahoo_finance(self, html: str, symbol: str) -> Optional[dict]:
        """Parse Yahoo Finance HTML"""
        try:
            # Try JSON-LD or embedded data
            json_match = re.search(r'root\.App\.main\s*=\s*({[\s\S]*?});', html)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    # Navigate to quote data
                    stores = data.get("context", {}).get("dispatcher", {}).get("stores", {})
                    if stores:
                        quote_data = stores.get("QuoteSummaryStore", {}).get("price", {})
                        if quote_data:
                            return {
                                "symbol": symbol,
                                "name": quote_data.get("longName", symbol),
                                "price": quote_data.get("regularMarketPrice", {}).get("raw", 0),
                                "change": quote_data.get("regularMarketChange", {}).get("raw", 0),
                                "changePercent": quote_data.get("regularMarketChangePercent", {}).get("raw", 0) * 100,
                                "volume": quote_data.get("regularMarketVolume", {}).get("raw", 0),
                                "marketCap": quote_data.get("marketCap", {}).get("raw", 0),
                                "source": "yahoo_finance",
                            }
                except json.JSONDecodeError:
                    pass

            # Fallback: parse HTML directly
            price_match = re.search(r'data-testid="qsp-price"[^>]*data-value="([0-9,.]+)"', html)
            if not price_match:
                price_match = re.search(r'class="[^"]*livePrice[^"]*"[^>]*>[^<]*<span>([0-9,]+\.?[0-9]*)', html)

            name_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)

            if price_match:
                return {
                    "symbol": symbol,
                    "name": name_match.group(1).strip() if name_match else symbol,
                    "price": float(price_match.group(1).replace(',', '')),
                    "source": "yahoo_finance",
                }
            return None
        except Exception as e:
            logger.warning(f"Yahoo Finance parse error: {e}")
            return None

    # ─────────────────────────────────────────────────────────────────────────
    # Social Media Scrapers (Reddit, Twitter/X trends)
    # ─────────────────────────────────────────────────────────────────────────

    async def reddit_india_finance(self, limit: int = 20) -> List[dict]:
        """Scrape Reddit India finance subreddits via JSON API"""
        cached = self._cache_get("reddit_india", ttl=900)
        if cached:
            return cached

        subreddits = ["IndianStreetBets", "IndiaInvestments", "DalalStreetTalks"]
        all_posts = []

        for sub in subreddits:
            try:
                url = f"https://www.reddit.com/r/{sub}/hot.json?limit={limit}"
                resp = await self.http_client.get(url, headers={
                    **self.HEADERS,
                    "User-Agent": "AARAMBH/2.0 (Financial Research Platform)",
                })
                if resp.status_code == 200:
                    data = resp.json()
                    for post in data.get("data", {}).get("children", []):
                        pd = post.get("data", {})
                        all_posts.append({
                            "title": pd.get("title", ""),
                            "subreddit": sub,
                            "author": pd.get("author", ""),
                            "score": pd.get("score", 0),
                            "comments": pd.get("num_comments", 0),
                            "url": f"https://reddit.com{pd.get('permalink', '')}",
                            "created_utc": pd.get("created_utc", 0),
                            "selftext": (pd.get("selftext", "") or "")[:300],
                            "source": "reddit",
                        })
            except Exception as e:
                logger.warning(f"Reddit {sub} scrape error: {e}")

        # Sort by score
        all_posts.sort(key=lambda x: x.get("score", 0), reverse=True)
        result = all_posts[:limit]
        self._cache_set("reddit_india", result)
        return result

    async def twitter_trends_india(self) -> List[dict]:
        """Get trending topics in India via Nitter/alternatives"""
        cached = self._cache_get("twitter_trends_in", ttl=1800)
        if cached:
            return cached

        # Use Google Trends as proxy for social media trends
        try:
            url = "https://trends.google.com/trending/rss?geo=IN"
            resp = await self.http_client.get(url)
            if resp.status_code != 200:
                return []

            trends = []
            items = re.findall(r'<item>([\s\S]*?)</item>', resp.text)
            for item in items[:20]:
                title_match = re.search(r'<title>([^<]+)</title>', item)
                traffic_match = re.search(r'<ht:approx_traffic>([^<]+)</ht:approx_traffic>', item)
                news_match = re.search(r'<ht:news_item_title>([^<]+)</ht:news_item_title>', item)

                if title_match:
                    trends.append({
                        "topic": title_match.group(1),
                        "traffic": traffic_match.group(1) if traffic_match else "N/A",
                        "related_news": news_match.group(1) if news_match else "",
                        "country": "India",
                        "source": "google_trends",
                    })

            self._cache_set("twitter_trends_in", trends)
            return trends
        except Exception as e:
            logger.warning(f"Trends scrape error: {e}")
            return []

    # ─────────────────────────────────────────────────────────────────────────
    # Unified Search (like SerpAPI)
    # ─────────────────────────────────────────────────────────────────────────

    async def unified_search(self, query: str, search_type: str = "all") -> dict:
        """Unified search combining multiple sources — SerpAPI-like interface"""
        cached = self._cache_get(f"unified:{query}:{search_type}", ttl=600)
        if cached:
            return cached

        result = {
            "query": query,
            "search_type": search_type,
            "timestamp": datetime.utcnow().isoformat(),
            "results": {},
        }

        tasks = {}

        if search_type in ("all", "news"):
            tasks["news"] = self.google_news_search(query, "IN")

        if search_type in ("all", "finance"):
            # Check if query is a stock symbol
            if query.upper() in self.INDIAN_STOCKS or len(query) <= 10:
                tasks["quote"] = self.google_finance_quote(query.upper())

        if search_type in ("all", "social"):
            tasks["reddit"] = self.reddit_india_finance(10)
            tasks["trends"] = self.twitter_trends_india()

        if search_type in ("all", "events"):
            tasks["events"] = self.google_events_search(query)

        # Execute all tasks concurrently
        task_keys = list(tasks.keys())
        task_values = await asyncio.gather(*tasks.values(), return_exceptions=True)

        for key, value in zip(task_keys, task_values):
            if isinstance(value, Exception):
                result["results"][key] = {"error": str(value)}
            else:
                result["results"][key] = value

        self._cache_set(f"unified:{query}:{search_type}", result)
        return result

    async def close(self):
        await self.http_client.aclose()


# Singleton
scraping_engine = WebScrapingEngine()
