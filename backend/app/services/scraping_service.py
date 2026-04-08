"""Web Scraping Service - BeautifulSoup scrapers for India government and research sources"""
import asyncio
import re
from datetime import datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from loguru import logger


class ScrapingService:
    """Scrapes 6 Indian government and research websites for intelligence data."""

    def __init__(self):
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "AARAMBH-Intelligence/2.0 (Research)"},
        )
        self.connector_status: dict = {}
        self.last_run: Optional[datetime] = None

    async def close(self):
        await self.http_client.aclose()

    # ── Helpers ──────────────────────────────────────────────────────────

    def _parse_date(self, date_str: str) -> datetime:
        """Try multiple date formats common on Indian government sites."""
        if not date_str:
            return datetime.utcnow()

        date_str = date_str.strip()

        formats = [
            "%b %d, %Y",
            "%d %b %Y",
            "%d %B %Y",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%B %d, %Y",
            "%d.%m.%Y",
            "%a, %d %b %Y %H:%M:%S %z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%d %b, %Y",
            "%d-%b-%Y",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.replace(tzinfo=None) if dt.tzinfo else dt
            except (ValueError, TypeError):
                continue

        return datetime.utcnow()

    @staticmethod
    def _clean_text(text: str) -> str:
        """Strip excessive whitespace and normalize a scraped string."""
        if not text:
            return ""
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    # ── 1. RBI Press Releases ────────────────────────────────────────────

    async def scrape_rbi(self) -> list[dict]:
        """Scrape Reserve Bank of India press releases.

        Target: https://rbi.org.in/scripts/BS_PressReleaseDisplay.aspx
        Structure: HTML table with rows containing date, title, and link.
        """
        url = "https://rbi.org.in/scripts/BS_PressReleaseDisplay.aspx"
        items: list[dict] = []

        try:
            resp = await self.http_client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # RBI lists press releases in table rows or repeating div/table patterns.
            # Try multiple selectors to be resilient to minor redesigns.
            rows = soup.select("table.tablebg tr")
            if not rows:
                rows = soup.select("table tr")

            for row in rows:
                try:
                    cells = row.find_all("td")
                    if len(cells) < 2:
                        continue

                    # Look for an anchor tag in the row for the title/link
                    link_tag = row.find("a")
                    if not link_tag:
                        continue

                    title = self._clean_text(link_tag.get_text())
                    if not title or len(title) < 5:
                        continue

                    href = link_tag.get("href", "")
                    if href and not href.startswith("http"):
                        href = f"https://rbi.org.in/scripts/{href}"

                    # Try to extract date from the first or last cell
                    date_text = ""
                    for cell in cells:
                        cell_text = self._clean_text(cell.get_text())
                        if re.search(r"\d{1,2}\s+\w+\s+\d{4}|\d{2}[/\-]\d{2}[/\-]\d{4}", cell_text):
                            date_text = cell_text
                            break

                    published_at = self._parse_date(date_text)

                    items.append({
                        "title": title[:500],
                        "summary": f"RBI Press Release: {title[:300]}",
                        "domain": "economics",
                        "source": "RBI",
                        "source_url": href,
                        "published_at": published_at,
                        "importance": 6,
                        "sentiment": 0.0,
                        "entities": ["RBI", "India"],
                    })
                except Exception as e:
                    logger.debug(f"RBI row parse error: {e}")
                    continue

            logger.info(f"RBI scraper: found {len(items)} press releases")

        except Exception as e:
            logger.warning(f"RBI scraper failed: {e}")
            return []

        return items

    # ── 2. MOSPI Press Releases ──────────────────────────────────────────

    async def scrape_mospi(self) -> list[dict]:
        """Scrape Ministry of Statistics press releases (GDP, CPI, IIP).

        Target: https://mospi.gov.in/press-release
        Structure: Article listing with title, date, and download links.
        """
        url = "https://mospi.gov.in/press-release"
        items: list[dict] = []

        try:
            resp = await self.http_client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # MOSPI uses Drupal-style views with article nodes or div listings
            articles = soup.select(".view-content .views-row")
            if not articles:
                articles = soup.select(".view-content .node")
            if not articles:
                # Fallback: any div that looks like a listing item
                articles = soup.select("article, .content-list-item, .list-item, .field-content")

            for article in articles:
                try:
                    # Extract title from heading or link
                    title_tag = article.find(["h2", "h3", "h4", "a"])
                    if not title_tag:
                        continue

                    if title_tag.name == "a":
                        link_tag = title_tag
                    else:
                        link_tag = title_tag.find("a")

                    title = self._clean_text(title_tag.get_text())
                    if not title or len(title) < 5:
                        continue

                    href = ""
                    if link_tag and link_tag.get("href"):
                        href = link_tag["href"]
                        if href and not href.startswith("http"):
                            href = f"https://mospi.gov.in{href}"

                    # Extract date from a date field or span
                    date_el = article.find(class_=re.compile(r"date|time|field-name-field-date|created"))
                    date_text = self._clean_text(date_el.get_text()) if date_el else ""
                    if not date_text:
                        time_tag = article.find("time")
                        if time_tag:
                            date_text = time_tag.get("datetime", "") or self._clean_text(time_tag.get_text())

                    published_at = self._parse_date(date_text)

                    items.append({
                        "title": title[:500],
                        "summary": f"MOSPI Statistical Release: {title[:300]}",
                        "domain": "economics",
                        "source": "MOSPI",
                        "source_url": href or url,
                        "published_at": published_at,
                        "importance": 5,
                        "sentiment": 0.0,
                        "entities": ["MOSPI", "India"],
                    })
                except Exception as e:
                    logger.debug(f"MOSPI article parse error: {e}")
                    continue

            logger.info(f"MOSPI scraper: found {len(items)} releases")

        except Exception as e:
            logger.warning(f"MOSPI scraper failed: {e}")
            return []

        return items

    # ── 3. SEBI Orders ───────────────────────────────────────────────────

    async def scrape_sebi(self) -> list[dict]:
        """Scrape SEBI (Securities and Exchange Board of India) recent orders.

        Target: https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=1&smid=0
        Structure: HTML table with order date, subject, and PDF link.
        """
        url = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=1&smid=0"
        items: list[dict] = []

        try:
            resp = await self.http_client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # SEBI uses a table listing or div-based listing for orders
            rows = soup.select("table tr")
            if not rows:
                rows = soup.select(".list-items li, .order-list li")

            for row in rows:
                try:
                    cells = row.find_all("td")
                    link_tag = row.find("a")

                    if not link_tag:
                        continue

                    title = self._clean_text(link_tag.get_text())
                    if not title or len(title) < 5:
                        continue

                    href = link_tag.get("href", "")
                    if href and not href.startswith("http"):
                        href = f"https://www.sebi.gov.in{href}"

                    # Try to pull date from cells
                    date_text = ""
                    if cells:
                        for cell in cells:
                            cell_text = self._clean_text(cell.get_text())
                            if re.search(r"\d{1,2}[/\-]\d{1,2}[/\-]\d{4}|\w+\s+\d{1,2},?\s+\d{4}", cell_text):
                                date_text = cell_text
                                break
                    else:
                        # Div-based layout: look for date span
                        date_el = row.find(class_=re.compile(r"date|time"))
                        if date_el:
                            date_text = self._clean_text(date_el.get_text())

                    published_at = self._parse_date(date_text)

                    items.append({
                        "title": title[:500],
                        "summary": f"SEBI Order: {title[:300]}",
                        "domain": "economics",
                        "source": "SEBI",
                        "source_url": href,
                        "published_at": published_at,
                        "importance": 6,
                        "sentiment": 0.0,
                        "entities": ["SEBI", "India"],
                    })
                except Exception as e:
                    logger.debug(f"SEBI row parse error: {e}")
                    continue

            logger.info(f"SEBI scraper: found {len(items)} orders")

        except Exception as e:
            logger.warning(f"SEBI scraper failed: {e}")
            return []

        return items

    # ── 4. NITI Aayog Reports ────────────────────────────────────────────

    async def scrape_niti_aayog(self) -> list[dict]:
        """Scrape NITI Aayog policy reports and documents.

        Target: https://www.niti.gov.in/documents/reports
        Structure: Document listing page with titles, dates, and PDF links.
        """
        url = "https://www.niti.gov.in/documents/reports"
        items: list[dict] = []

        try:
            resp = await self.http_client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # NITI Aayog is a Drupal site with views-based listings
            entries = soup.select(".view-content .views-row")
            if not entries:
                entries = soup.select(".view-content .node, .content-list .item")
            if not entries:
                # Broad fallback: any container with links that look like report listings
                entries = soup.select("article, .field-content, .list-group-item")

            for entry in entries:
                try:
                    # Find title from heading or first prominent link
                    heading = entry.find(["h2", "h3", "h4"])
                    if heading:
                        link_tag = heading.find("a") or heading
                        title = self._clean_text(heading.get_text())
                    else:
                        link_tag = entry.find("a")
                        if not link_tag:
                            continue
                        title = self._clean_text(link_tag.get_text())

                    if not title or len(title) < 5:
                        continue

                    href = ""
                    if hasattr(link_tag, "get") and link_tag.get("href"):
                        href = link_tag["href"]
                        if not href.startswith("http"):
                            href = f"https://www.niti.gov.in{href}"

                    # Extract date
                    date_el = entry.find(class_=re.compile(r"date|time|field-name-field-date"))
                    date_text = self._clean_text(date_el.get_text()) if date_el else ""
                    if not date_text:
                        time_tag = entry.find("time")
                        if time_tag:
                            date_text = time_tag.get("datetime", "") or self._clean_text(time_tag.get_text())

                    published_at = self._parse_date(date_text)

                    items.append({
                        "title": title[:500],
                        "summary": f"NITI Aayog Report: {title[:300]}",
                        "domain": "geopolitics",
                        "source": "NITI Aayog",
                        "source_url": href or url,
                        "published_at": published_at,
                        "importance": 5,
                        "sentiment": 0.0,
                        "entities": ["NITI Aayog", "India"],
                    })
                except Exception as e:
                    logger.debug(f"NITI Aayog entry parse error: {e}")
                    continue

            logger.info(f"NITI Aayog scraper: found {len(items)} reports")

        except Exception as e:
            logger.warning(f"NITI Aayog scraper failed: {e}")
            return []

        return items

    # ── 5. ORF Research ──────────────────────────────────────────────────

    async def scrape_orf(self) -> list[dict]:
        """Scrape Observer Research Foundation research articles.

        Target: https://www.orfonline.org/research/
        Structure: Article cards with title, date, author, and excerpt.
        """
        url = "https://www.orfonline.org/research/"
        items: list[dict] = []

        try:
            resp = await self.http_client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # ORF uses card-based layouts for research articles
            cards = soup.select(".post-card, .article-card, .research-card, .card")
            if not cards:
                cards = soup.select("article, .post-item, .research-item")
            if not cards:
                # Broad fallback: divs with heading + link combos
                cards = soup.select(".row .col, .listing-item, .content-item")

            for card in cards:
                try:
                    # Extract title
                    heading = card.find(["h2", "h3", "h4", "h5"])
                    if heading:
                        link_tag = heading.find("a") or heading
                        title = self._clean_text(heading.get_text())
                    else:
                        link_tag = card.find("a")
                        if not link_tag:
                            continue
                        title = self._clean_text(link_tag.get_text())

                    if not title or len(title) < 10:
                        continue

                    href = ""
                    if hasattr(link_tag, "get") and link_tag.get("href"):
                        href = link_tag["href"]
                        if href and not href.startswith("http"):
                            href = f"https://www.orfonline.org{href}"

                    # Extract summary/excerpt
                    excerpt_el = card.find(class_=re.compile(r"excerpt|summary|description|teaser|body"))
                    if not excerpt_el:
                        excerpt_el = card.find("p")
                    summary = self._clean_text(excerpt_el.get_text()) if excerpt_el else ""
                    if not summary:
                        summary = f"ORF Research: {title[:300]}"
                    summary = summary[:500]

                    # Extract date
                    date_el = card.find(class_=re.compile(r"date|time|meta|published"))
                    date_text = ""
                    if date_el:
                        date_text = self._clean_text(date_el.get_text())
                    if not date_text:
                        time_tag = card.find("time")
                        if time_tag:
                            date_text = time_tag.get("datetime", "") or self._clean_text(time_tag.get_text())

                    published_at = self._parse_date(date_text)

                    # Extract author if available
                    author_el = card.find(class_=re.compile(r"author|byline|writer"))
                    entities = ["ORF", "India"]
                    if author_el:
                        author_name = self._clean_text(author_el.get_text())
                        if author_name and len(author_name) < 100:
                            entities.append(author_name)

                    items.append({
                        "title": title[:500],
                        "summary": summary,
                        "domain": "geopolitics",
                        "source": "ORF",
                        "source_url": href or url,
                        "published_at": published_at,
                        "importance": 6,
                        "sentiment": 0.0,
                        "entities": entities,
                    })
                except Exception as e:
                    logger.debug(f"ORF card parse error: {e}")
                    continue

            logger.info(f"ORF scraper: found {len(items)} research articles")

        except Exception as e:
            logger.warning(f"ORF scraper failed: {e}")
            return []

        return items

    # ── 6. India Budget Documents ────────────────────────────────────────

    async def scrape_india_budget(self) -> list[dict]:
        """Scrape India Budget website for budget document links.

        Target: https://www.indiabudget.gov.in/
        Structure: Document listing page with links to PDFs and budget papers.
        """
        url = "https://www.indiabudget.gov.in/"
        items: list[dict] = []

        try:
            resp = await self.http_client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # The India Budget site links to key documents from the homepage.
            # Look for links that point to budget documents (PDFs, HTML pages).
            seen_titles: set = set()

            # Strategy 1: Find all links in content sections that point to documents
            content_areas = soup.select(
                ".content-area, .main-content, #content, .container, .budget-docs, .doc-list"
            )
            if not content_areas:
                # Fallback: use the whole page body
                content_areas = [soup.body] if soup.body else [soup]

            for area in content_areas:
                links = area.find_all("a", href=True)
                for link in links:
                    try:
                        title = self._clean_text(link.get_text())
                        href = link["href"]

                        # Skip empty, navigation, or very short titles
                        if not title or len(title) < 5:
                            continue

                        # Skip common navigation links
                        skip_words = [
                            "home", "contact", "login", "sign", "skip",
                            "sitemap", "disclaimer", "feedback", "javascript",
                        ]
                        if any(sw in title.lower() for sw in skip_words):
                            continue

                        # Normalize URL
                        if not href.startswith("http"):
                            if href.startswith("/"):
                                href = f"https://www.indiabudget.gov.in{href}"
                            else:
                                href = f"https://www.indiabudget.gov.in/{href}"

                        # Dedup by title within this scrape
                        title_key = title.lower().strip()
                        if title_key in seen_titles:
                            continue
                        seen_titles.add(title_key)

                        # Filter for budget-related content (PDFs, doc pages)
                        is_document = (
                            href.endswith(".pdf")
                            or href.endswith(".xls")
                            or href.endswith(".xlsx")
                            or "doc" in href.lower()
                            or "budget" in href.lower()
                            or "speech" in href.lower()
                            or "receipt" in href.lower()
                            or "expenditure" in href.lower()
                            or "finance" in href.lower()
                            or "economic" in href.lower()
                            or "annual" in href.lower()
                        )

                        is_budget_title = any(
                            kw in title.lower()
                            for kw in [
                                "budget", "speech", "finance", "receipt",
                                "expenditure", "economic", "survey", "annual",
                                "statement", "memorandum", "demand", "grant",
                                "fiscal", "revenue", "tax", "allocation",
                            ]
                        )

                        if not (is_document or is_budget_title):
                            continue

                        items.append({
                            "title": title[:500],
                            "summary": f"India Budget Document: {title[:300]}",
                            "domain": "economics",
                            "source": "India Budget",
                            "source_url": href,
                            "published_at": datetime.utcnow(),
                            "importance": 5,
                            "sentiment": 0.0,
                            "entities": ["India", "Ministry of Finance"],
                        })
                    except Exception as e:
                        logger.debug(f"India Budget link parse error: {e}")
                        continue

            logger.info(f"India Budget scraper: found {len(items)} documents")

        except Exception as e:
            logger.warning(f"India Budget scraper failed: {e}")
            return []

        return items

    # ── Run All Scrapers ─────────────────────────────────────────────────

    async def run_all_scrapers(self) -> dict:
        """Run all scrapers sequentially with 2s polite delays between them.

        Each scraper is isolated -- if one fails, the rest still run.
        Returns a summary dict with all collected items and per-connector status.
        """
        all_items: list[dict] = []
        scrapers = [
            ("RBI", self.scrape_rbi),
            ("MOSPI", self.scrape_mospi),
            ("SEBI", self.scrape_sebi),
            ("NITI Aayog", self.scrape_niti_aayog),
            ("ORF", self.scrape_orf),
            ("India Budget", self.scrape_india_budget),
        ]

        for name, scraper_fn in scrapers:
            try:
                items = await scraper_fn()
                all_items.extend(items)
                self.connector_status[name] = {
                    "status": "ok",
                    "count": len(items),
                    "last_fetch": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                logger.warning(f"Scraper failed for {name}: {e}")
                self.connector_status[name] = {
                    "status": "error",
                    "error": str(e),
                    "last_fetch": datetime.utcnow().isoformat(),
                }
            await asyncio.sleep(2)  # Polite delay between targets

        self.last_run = datetime.utcnow()
        return {
            "total_items": len(all_items),
            "items": all_items,
            "connector_status": self.connector_status,
            "timestamp": self.last_run.isoformat(),
        }

    def get_status(self) -> dict:
        """Return current scraping status for all connectors."""
        return {
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "connectors": self.connector_status,
            "total_scrapers": 6,
        }


# Singleton
scraping_service = ScrapingService()
