"""
Enhanced News Scraper with Thumbnails and Location Support
Optimized for performance with lazy loading capabilities
"""

import httpx
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import re
from urllib.parse import urljoin, urlparse

class EnhancedNewsScraper:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        
        # Enhanced news sources with image support
        self.news_sources = {
            "india_today": {
                "url": "https://www.indiatoday.in/rssfeeds/rss_story.xml",
                "country": "IN",
                "category": "general",
                "has_images": True
            },
            "the_hindu": {
                "url": "https://www.thehindu.com/news/national/?service=rss",
                "country": "IN", 
                "category": "general",
                "has_images": True
            },
            "times_of_india": {
                "url": "https://timesofindia.indiatimes.com/rssfeeds/1081478006.cms",
                "country": "IN",
                "category": "general", 
                "has_images": True
            },
            "hindustan_times": {
                "url": "https://www.hindustantimes.com/rssfeeds/topstories.xml",
                "country": "IN",
                "category": "general",
                "has_images": True
            },
            "ndtv": {
                "url": "https://feeds.feedburner.com/NdtvNews-TopStories",
                "country": "IN",
                "category": "general",
                "has_images": True
            },
            "bbc_news": {
                "url": "http://feeds.bbci.co.uk/news/rss.xml",
                "country": "GB",
                "category": "world",
                "has_images": True
            },
            "cnn": {
                "url": "http://rss.cnn.com/rss/edition.rss",
                "country": "US",
                "category": "world",
                "has_images": True
            },
            "reuters": {
                "url": "https://www.reuters.com/rssFeed/worldNews",
                "country": "US",
                "category": "world",
                "has_images": True
            }
        }

    async def fetch_news_with_thumbnails(self, source_key: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch news with thumbnail images from a specific source"""
        source = self.news_sources.get(source_key)
        if not source:
            return []
        
        try:
            response = await self.client.get(
                source["url"],
                headers={"User-Agent": self.user_agent}
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item")[:limit]
            
            articles = []
            for item in items:
                article = await self._parse_rss_item(item, source)
                if article:
                    articles.append(article)
            
            return articles
            
        except Exception as e:
            print(f"Error fetching from {source_key}: {e}")
            return []

    async def _parse_rss_item(self, item, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse RSS item with enhanced image extraction"""
        try:
            # Basic fields
            title = self._clean_text(item.find("title").text if item.find("title") else "")
            link = item.find("link").text if item.find("link") else ""
            description = item.find("description").text if item.find("description") else ""
            pub_date = item.find("pubDate").text if item.find("pubDate") else ""
            
            if not title or not link:
                return None
            
            # Extract thumbnail from description or media content
            thumbnail_url = await self._extract_thumbnail(item, description, link)
            
            # Extract summary from description
            summary = self._extract_summary(description)
            
            # Parse publication date
            published_at = self._parse_date(pub_date)
            
            return {
                "title": title,
                "summary": summary,
                "url": link,
                "source": source_key.replace("_", " ").title(),
                "category": source["category"],
                "country": source["country"],
                "published_at": published_at,
                "thumbnail_url": thumbnail_url,
                "image_url": thumbnail_url,  # Use thumbnail as main image for now
                "content": description
            }
            
        except Exception as e:
            print(f"Error parsing item: {e}")
            return None

    async def _extract_thumbnail(self, item, description: str, link: str) -> Optional[str]:
        """Extract thumbnail image from RSS item"""
        # Method 1: Check for media:content in RSS
        media_content = item.find("media:content")
        if media_content and media_content.get("url"):
            return media_content.get("url")
        
        # Method 2: Check for media:thumbnail
        media_thumbnail = item.find("media:thumbnail")
        if media_thumbnail and media_thumbnail.get("url"):
            return media_thumbnail.get("url")
        
        # Method 3: Extract from description (HTML img tags)
        if description:
            soup = BeautifulSoup(description, "html.parser")
            img = soup.find("img")
            if img and img.get("src"):
                img_src = img.get("src")
                # Convert relative URLs to absolute
                if img_src.startswith("/"):
                    parsed_link = urlparse(link)
                    img_src = f"{parsed_link.scheme}://{parsed_link.netloc}{img_src}"
                elif img_src.startswith("//"):
                    img_src = f"https:{img_src}"
                return img_src
        
        # Method 4: Try to fetch from article page
        return await self._fetch_image_from_article(link)

    async def _fetch_image_from_article(self, url: str) -> Optional[str]:
        """Fetch main image from article page as fallback"""
        try:
            response = await self.client.get(
                url,
                headers={"User-Agent": self.user_agent}
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Look for common image selectors
            selectors = [
                "meta[property='og:image']",
                "meta[name='twitter:image']",
                "article img",
                ".story-image img",
                ".featured-image img",
                "img[src*='story'], img[src*='article']"
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    img_src = element.get("content") if element.name == "meta" else element.get("src")
                    if img_src:
                        if img_src.startswith("//"):
                            img_src = f"https:{img_src}"
                        elif img_src.startswith("/"):
                            parsed_url = urlparse(url)
                            img_src = f"{parsed_url.scheme}://{parsed_url.netloc}{img_src}"
                        return img_src
            
        except Exception as e:
            print(f"Error fetching image from {url}: {e}")
        
        return None

    def _extract_summary(self, description: str) -> str:
        """Extract clean summary from description"""
        if not description:
            return ""
        
        # Remove HTML tags
        soup = BeautifulSoup(description, "html.parser")
        text = soup.get_text()
        
        # Clean up text
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Limit to reasonable length
        if len(text) > 300:
            text = text[:300].rsplit(' ', 1)[0] + "..."
        
        return text

    def _clean_text(self, text: str) -> str:
        """Clean text content"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip())

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object"""
        try:
            # Try common date formats
            formats = [
                "%a, %d %b %Y %H:%M:%S %Z",
                "%a, %d %b %Y %H:%M:%S %z",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d %H:%M:%S"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # Fallback to current time
            return datetime.utcnow()
            
        except Exception:
            return datetime.utcnow()

    async def get_location_based_news(self, country_code: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get news based on location/country"""
        location_sources = [
            k for k, v in self.news_sources.items() 
            if v.get("country") == country_code.upper()
        ]
        
        if not location_sources:
            # Fallback to general international sources
            location_sources = ["bbc_news", "cnn", "reuters"]
        
        # Fetch from multiple sources in parallel
        tasks = []
        for source in location_sources[:3]:  # Limit to 3 sources for performance
            task = self.fetch_news_with_thumbnails(source, limit // 3)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_articles = []
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
        
        # Sort by publication date
        all_articles.sort(key=lambda x: x.get("published_at", datetime.utcnow()), reverse=True)
        
        return all_articles[:limit]

    async def get_featured_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get featured/top stories with images"""
        # Get from top sources
        featured_sources = ["india_today", "times_of_india", "the_hindu", "bbc_news"]
        
        tasks = []
        for source in featured_sources:
            task = self.fetch_news_with_thumbnails(source, limit // len(featured_sources))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        featured_articles = []
        for result in results:
            if isinstance(result, list):
                # Only include articles with thumbnails for featured section
                articles_with_images = [a for a in result if a.get("thumbnail_url")]
                featured_articles.extend(articles_with_images)
        
        # Sort by publication date and take top stories
        featured_articles.sort(key=lambda x: x.get("published_at", datetime.utcnow()), reverse=True)
        
        return featured_articles[:limit]

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Global scraper instance
enhanced_scraper = EnhancedNewsScraper()
