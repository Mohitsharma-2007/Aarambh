"""
Enhanced News Scraper with All Features Working
- Thumbnail and image extraction
- All categories supported
- Fast loading with caching
- Proper date/time parsing
- Multiple sources
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import feedparser
import re
from urllib.parse import urljoin, urlparse

class EnhancedNewsScraper:
    def __init__(self):
        self.session = None
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
        # Comprehensive news sources
        self.sources = {
            "general": [
                {
                    "name": "BBC News",
                    "rss": "http://feeds.bbci.co.uk/news/rss.xml",
                    "country": "GB",
                    "language": "en"
                },
                {
                    "name": "CNN",
                    "rss": "http://rss.cnn.com/rss/edition.rss",
                    "country": "US",
                    "language": "en"
                },
                {
                    "name": "Reuters",
                    "rss": "https://www.reuters.com/rssFeed/worldNews",
                    "country": "US",
                    "language": "en"
                },
                {
                    "name": "The Hindu",
                    "rss": "https://www.thehindu.com/news/national/?service=rss",
                    "country": "IN",
                    "language": "en"
                },
                {
                    "name": "Times of India",
                    "rss": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
                    "country": "IN",
                    "language": "en"
                },
                {
                    "name": "India Today",
                    "rss": "https://www.indiatoday.in/rss/home",
                    "country": "IN",
                    "language": "en"
                }
            ],
            "finance": [
                {
                    "name": "CNBC",
                    "rss": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
                    "country": "US",
                    "language": "en"
                },
                {
                    "name": "Bloomberg",
                    "rss": "https://www.bloomberg.com/feed/news/rss.xml",
                    "country": "US",
                    "language": "en"
                },
                {
                    "name": "Economic Times",
                    "rss": "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
                    "country": "IN",
                    "language": "en"
                }
            ],
            "world": [
                {
                    "name": "Al Jazeera",
                    "rss": "https://www.aljazeera.com/xml/rss/all.xml",
                    "country": "QA",
                    "language": "en"
                },
                {
                    "name": "France 24",
                    "rss": "https://www.france24.com/en/rss/rss.xml",
                    "country": "FR",
                    "language": "en"
                },
                {
                    "name": "DW News",
                    "rss": "https://rss.dw.com/xml/rss-en-all",
                    "country": "DE",
                    "language": "en"
                }
            ],
            "health": [
                {
                    "name": "WHO",
                    "rss": "https://www.who.int/rss-feeds/news-english.xml",
                    "country": "INT",
                    "language": "en"
                },
                {
                    "name": "WebMD",
                    "rss": "https://rss.webmd.com/rss/rss.aspx",
                    "country": "US",
                    "language": "en"
                }
            ],
            "technology": [
                {
                    "name": "TechCrunch",
                    "rss": "https://techcrunch.com/feed/",
                    "country": "US",
                    "language": "en"
                },
                {
                    "name": "The Verge",
                    "rss": "https://www.theverge.com/rss/index.xml",
                    "country": "US",
                    "language": "en"
                }
            ],
            "science": [
                {
                    "name": "Science Daily",
                    "rss": "https://www.sciencedaily.com/rss/news.xml",
                    "country": "US",
                    "language": "en"
                },
                {
                    "name": "Nature",
                    "rss": "https://www.nature.com/nature/articles?type=news&format=rss",
                    "country": "INT",
                    "language": "en"
                }
            ],
            "sports": [
                {
                    "name": "ESPN",
                    "rss": "http://www.espn.com/espn/rss/news",
                    "country": "US",
                    "language": "en"
                }
            ],
            "india": [
                {
                    "name": "NDTV",
                    "rss": "https://feeds.feedburner.com/ndtvnews-top-stories",
                    "country": "IN",
                    "language": "en"
                },
                {
                    "name": "Hindustan Times",
                    "rss": "https://www.hindustantimes.com/rss/topnews/rssfeed.xml",
                    "country": "IN",
                    "language": "en"
                }
            ]
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def get_cache_key(self, method: str, **kwargs) -> str:
        """Generate cache key"""
        key_parts = [method]
        for k, v in sorted(kwargs.items()):
            if v is not None:
                key_parts.append(f"{k}:{v}")
        return "|".join(key_parts)

    def get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.utcnow().timestamp() - timestamp < self.cache_duration:
                return data
            else:
                del self.cache[key]
        return None

    def set_cache(self, key: str, data: Any):
        """Set data in cache"""
        self.cache[key] = (data, datetime.utcnow().timestamp())

    async def extract_thumbnail_from_html(self, html_content: str, base_url: str) -> Optional[str]:
        """Extract thumbnail image from HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try multiple methods to find images
            
            # 1. Open Graph meta tags
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                return og_image['content']
            
            # 2. Twitter card meta tags
            twitter_image = soup.find('meta', name='twitter:image')
            if twitter_image and twitter_image.get('content'):
                return twitter_image['content']
            
            # 3. First large image in content
            images = soup.find_all('img')
            for img in images:
                src = img.get('src')
                if src:
                    # Convert relative URLs to absolute
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = urljoin(base_url, src)
                    
                    # Filter for large images
                    width = img.get('width')
                    height = img.get('height')
                    if (not width or int(width) > 300) and (not height or int(height) > 200):
                        return src
            
            # 4. First image as fallback
            if images and images[0].get('src'):
                src = images[0]['src']
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(base_url, src)
                return src
                
        except Exception as e:
            print(f"Error extracting thumbnail: {e}")
        
        return None

    async def fetch_article_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch full article content and extract images"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    thumbnail = await self.extract_thumbnail_from_html(content, url)
                    
                    return {
                        "content": content[:5000],  # Limit content length
                        "thumbnail_url": thumbnail
                    }
        except Exception as e:
            print(f"Error fetching article content from {url}: {e}")
        
        return None

    async def parse_feed_entry(self, entry, source_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a single RSS feed entry"""
        try:
            # Extract basic info
            title = entry.get('title', '').strip()
            link = entry.get('link', '')
            summary = entry.get('summary', entry.get('description', ''))
            
            if not title or not link:
                return None
            
            # Extract published date
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6])
            else:
                published = datetime.utcnow()
            
            # Extract thumbnails from RSS
            thumbnail_url = None
            image_url = None
            
            # Media thumbnails
            if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                thumbnail_url = entry.media_thumbnail[0].get('url')
            
            # Media content
            if hasattr(entry, 'media_content') and entry.media_content:
                for media in entry.media_content:
                    if media.get('type', '').startswith('image/'):
                        image_url = media.get('url')
                        break
            
            # Extract images from summary HTML
            if not thumbnail_url and summary:
                soup = BeautifulSoup(summary, 'html.parser')
                img = soup.find('img')
                if img and img.get('src'):
                    thumbnail_url = img['src']
            
            # Clean summary
            if summary:
                soup = BeautifulSoup(summary, 'html.parser')
                summary = soup.get_text().strip()[:500]
            
            # Fetch article content for better thumbnails
            if not thumbnail_url:
                article_content = await self.fetch_article_content(link)
                if article_content and article_content.get('thumbnail_url'):
                    thumbnail_url = article_content['thumbnail_url']
            
            return {
                "title": title,
                "summary": summary,
                "source": source_info["name"],
                "url": link,
                "category": source_info.get("category", "general"),
                "country": source_info["country"],
                "published": published.isoformat(),
                "thumbnail_url": thumbnail_url,
                "image_url": image_url or thumbnail_url,
                "language": source_info.get("language", "en")
            }
            
        except Exception as e:
            print(f"Error parsing feed entry: {e}")
            return None

    async def fetch_feed(self, source_info: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch and parse RSS feed"""
        try:
            cache_key = self.get_cache_key("feed", url=source_info["rss"], limit=limit)
            cached_data = self.get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            async with self.session.get(source_info["rss"]) as response:
                if response.status == 200:
                    feed_content = await response.text()
                    feed = feedparser.parse(feed_content)
                    
                    articles = []
                    for entry in feed.entries[:limit]:
                        article = await self.parse_feed_entry(entry, source_info)
                        if article:
                            articles.append(article)
                    
                    # Sort by published date (newest first)
                    articles.sort(key=lambda x: x["published"], reverse=True)
                    
                    self.set_cache(cache_key, articles)
                    return articles
                    
        except Exception as e:
            print(f"Error fetching feed {source_info['rss']}: {e}")
        
        return []

    async def get_featured_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get featured/top stories from general sources"""
        cache_key = self.get_cache_key("featured", limit=limit)
        cached_data = self.get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        all_articles = []
        sources = self.sources["general"][:3]  # Top 3 sources
        
        tasks = []
        for source in sources:
            source["category"] = "general"
            task = self.fetch_feed(source, limit // len(sources))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
        
        # Sort by published date and limit
        all_articles.sort(key=lambda x: x["published"], reverse=True)
        featured = all_articles[:limit]
        
        self.set_cache(cache_key, featured)
        return featured

    async def get_location_based_news(self, country_code: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get news based on country/location"""
        cache_key = self.get_cache_key("location", country=country_code, limit=limit)
        cached_data = self.get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        all_articles = []
        
        # Get sources for this country
        country_sources = []
        for category_sources in self.sources.values():
            for source in category_sources:
                if source.get("country") == country_code.upper():
                    country_sources.append(source)
        
        # If no specific sources, use general sources
        if not country_sources:
            country_sources = self.sources["general"][:2]
        
        tasks = []
        for source in country_sources[:3]:  # Limit to 3 sources
            source["category"] = "general"
            task = self.fetch_feed(source, limit // len(country_sources) + 2)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
        
        # Sort and limit
        all_articles.sort(key=lambda x: x["published"], reverse=True)
        location_news = all_articles[:limit]
        
        self.set_cache(cache_key, location_news)
        return location_news

    async def get_news_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get news by category"""
        cache_key = self.get_cache_key("category", category=category, limit=limit)
        cached_data = self.get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        all_articles = []
        sources = self.sources.get(category, self.sources["general"])
        
        tasks = []
        for source in sources[:3]:  # Limit to 3 sources per category
            source_copy = source.copy()
            source_copy["category"] = category
            task = self.fetch_feed(source_copy, limit // len(sources) + 2)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
        
        # Sort by published date and limit
        all_articles.sort(key=lambda x: x["published"], reverse=True)
        category_news = all_articles[:limit]
        
        self.set_cache(cache_key, category_news)
        return category_news

    async def get_finance_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get finance news"""
        return await self.get_news_by_category("finance", limit)

    async def get_world_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get world news"""
        return await self.get_news_by_category("world", limit)

    async def get_health_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get health news"""
        return await self.get_news_by_category("health", limit)

    async def get_tech_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get technology news"""
        return await self.get_news_by_category("technology", limit)

    async def get_science_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get science news"""
        return await self.get_news_by_category("science", limit)

    async def get_sports_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sports news"""
        return await self.get_news_by_category("sports", limit)

    async def get_india_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get India-specific news"""
        return await self.get_location_based_news("IN", limit)

# Global instance
enhanced_scraper = EnhancedNewsScraper()
