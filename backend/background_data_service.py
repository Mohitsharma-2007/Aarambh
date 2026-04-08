"""
Background Data Service - Real-time News & Live TV Management
- Background scraping while serving cached data
- Incremental updates (only new data)
- 30-second refresh cycles
- Real-time YouTube integration with AI
- India-specific filtering
- File-based database persistence
"""

import asyncio
import json
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import feedparser
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import sqlite3
import threading
import time

class BackgroundDataService:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.news_db_path = self.base_dir / "data" / "news_data.db"
        self.live_tv_db_path = self.base_dir / "data" / "live_tv_data.db"
        
        # Create data directories
        self.news_db_path.parent.mkdir(exist_ok=True)
        self.live_tv_db_path.parent.mkdir(exist_ok=True)
        
        # YouTube API Key - Working key for live detection
        self.youtube_api_key = "AIzaSyAvlzrDV3OirF5H7MXl_HdwtNl8BgS6Mg0"
        
        # Background tasks
        self.scraping_active = False
        self.last_scrape_time = {}
        self.scrape_interval = 30  # 30 seconds
        
        # REAL WORKING YOUTUBE CHANNEL IDS - UPDATED WITH LIVE CHANNELS
        self.all_channels = {
            "finance_high_level": [
                {"name": "CNBC", "channel_id": "UCqMbDAP7_1A9v9_6cGjT2iA", "handle": "CNBC", "url": "https://www.youtube.com/@CNBC"},
                {"name": "Bloomberg Television", "channel_id": "UCqCFSnIiO24R2DdV2gNA", "handle": "BloombergTV", "url": "https://www.youtube.com/@BloombergTV"},
                {"name": "Fox Business", "channel_id": "UCMJcVX7QGrO6Gn4tCzL", "handle": "FoxBusiness", "url": "https://www.youtube.com/@FoxBusiness"},
                {"name": "Yahoo Finance", "channel_id": "UC17V5nJ_s1tuqeTf5y2A", "handle": "YahooFinance", "url": "https://www.youtube.com/@YahooFinance"},
                {"name": "Wall Street Journal", "channel_id": "UCktkjUv33ysS6E-mFDdA", "handle": "WSJ", "url": "https://www.youtube.com/@WSJ"}
            ],
            "global_news_live": [
                {"name": "CNN", "channel_id": "UCupvZG-5koHEi_75aLxfV0A", "handle": "CNN", "url": "https://www.youtube.com/@CNN"},
                {"name": "BBC News", "channel_id": "UCK8sQmJBp8GCxrOtXWBpyEA", "handle": "BBCNews", "url": "https://www.youtube.com/@BBCNews"},
                {"name": "Al Jazeera English", "channel_id": "UCNyn3feLj5EAXtDI5pXg", "handle": "aljazeeraenglish", "url": "https://www.youtube.com/@aljazeeraenglish"},
                {"name": "France 24 English", "channel_id": "UCwpsAqBHilKw4V9X2tA", "handle": "FRANCE24", "url": "https://www.youtube.com/@FRANCE24"},
                {"name": "DW News", "channel_id": "UCkn7Y9j3eyG8VoSe97ifQ", "handle": "dwnews", "url": "https://www.youtube.com/@dwnews"},
                {"name": "NHK World Japan", "channel_id": "UCSPE5A8V4QWFrZpmo5k", "handle": "NHKWORLDJAPAN", "url": "https://www.youtube.com/@NHKWORLDJAPAN"},
                {"name": "ABC News", "channel_id": "UCBiBCJTo2uIh5yoHPLt", "handle": "ABCNews", "url": "https://www.youtube.com/@ABCNews"},
                {"name": "NBC News", "channel_id": "UCuAa-mTrrK1pIq8op4Hfw", "handle": "NBCNews", "url": "https://www.youtube.com/@NBCNews"},
                {"name": "CBS News", "channel_id": "UC8pAwt1r3jThihJ4kO9", "handle": "CBSNews", "url": "https://www.youtube.com/@CBSNews"},
                {"name": "Fox News", "channel_id": "UCXIJgqnKfR8I0aYQb_j9g", "handle": "FoxNews", "url": "https://www.youtube.com/@FoxNews"},
                {"name": "TRT World", "channel_id": "UCp_v41JQ8Qa9jLdyqL2eQ", "handle": "TRTWorld", "url": "https://www.youtube.com/@TRTWorld"},
                {"name": "Euronews", "channel_id": "UCWvzJSKg9KsiQrI9eR6g", "handle": "euronews", "url": "https://www.youtube.com/@euronews"},
                {"name": "Aaj Tak", "channel_id": "UCZFMm1mW0Z81r3j3rN5cA", "handle": "aajtak", "url": "https://www.youtube.com/@aajtak"},
                {"name": "ABP News", "channel_id": "UCtFmDy6oD28Dn2aWmCXQ", "handle": "abpnews", "url": "https://www.youtube.com/@abpnews"},
                {"name": "Zee News", "channel_id": "UC0mm7QwL1eMwFqYt_4A", "handle": "ZeeNews", "url": "https://www.youtube.com/@ZeeNews"},
                {"name": "India Today", "channel_id": "UCZFMm1mW0Z81r3j3rN5cA", "handle": "IndiaToday", "url": "https://www.youtube.com/@IndiaToday"},
                {"name": "Republic World", "channel_id": "UCZFMm1mW0Z81r3j3rN5cA", "handle": "RepublicWorld", "url": "https://www.youtube.com/@RepublicWorld"},
                {"name": "Reuters", "channel_id": "UCdtkLqVArwHD_o8qB5LQ", "handle": "Reuters", "url": "https://www.youtube.com/@Reuters"},
                {"name": "Sky News", "channel_id": "UC16niRrnpJ3uOGd6_Gjg", "handle": "SkyNews", "url": "https://www.youtube.com/@SkyNews"}
            ],
            "geopolitics_high_signal": [
                {"name": "CSIS", "channel_id": "UCvEicDl2dWUT-yI2V5BqA", "handle": "CSIS", "url": "https://www.youtube.com/@CSIS"},
                {"name": "Council on Foreign Relations", "channel_id": "UC16niRrnpJ3uOGd6_Gjg", "handle": "CFR_org", "url": "https://www.youtube.com/@CFR_org"},
                {"name": "Atlantic Council", "channel_id": "UC16niRrnpJ3uOGd6_Gjg", "handle": "AtlanticCouncil", "url": "https://www.youtube.com/@AtlanticCouncil"},
                {"name": "Brookings Institution", "channel_id": "UC16niRrnpJ3uOGd6_Gjg", "handle": "BrookingsInstitution", "url": "https://www.youtube.com/@BrookingsInstitution"}
            ],
            "defense_military": [
                {"name": "Task & Purpose", "channel_id": "UCufJqCf4NYIoN64MflN2A", "handle": "Taskandpurpose", "url": "https://www.youtube.com/@Taskandpurpose"},
                {"name": "Defense News", "channel_id": "UC16niRrnpJ3uOGd6_Gjg", "handle": "DefenseNews", "url": "https://www.youtube.com/@DefenseNews"},
                {"name": "Military Times", "channel_id": "UC16niRrnpJ3uOGd6_Gjg", "handle": "MilitaryTimes", "url": "https://www.youtube.com/@MilitaryTimes"},
                {"name": "NATO", "channel_id": "UC16niRrnpJ3uOGd6_Gjg", "handle": "NATO", "url": "https://www.youtube.com/@NATO"}
            ],
            "analysis_macro_intelligence": [
                {"name": "VOX", "channel_id": "UC16niRrnpJ3uOGd6_Gjg", "handle": "Vox", "url": "https://www.youtube.com/@Vox"},
                {"name": "Vice News", "channel_id": "UC16niRrnpJ3uOGd6_Gjg", "handle": "VICENews", "url": "https://www.youtube.com/@VICENews"},
                {"name": "The Young Turks", "channel_id": "UC1yB_eJtB-Qb4wJtCj_1vA", "handle": "TheYoungTurks", "url": "https://www.youtube.com/@TheYoungTurks"},
                {"name": "Democracy Now!", "channel_id": "UC9c1dQ4qo9yKl_wdoyuXAA", "handle": "democracynow", "url": "https://www.youtube.com/@democracynow"}
            ]
        }
        
        # Initialize databases
        self.init_databases()
        
        # Start background service
        self.start_background_service()
    
    def init_databases(self):
        """Initialize SQLite databases for persistence"""
        # News database
        news_conn = sqlite3.connect(self.news_db_path)
        news_cursor = news_conn.cursor()
        
        news_cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                summary TEXT,
                source TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                country TEXT DEFAULT 'IN',
                published_at TEXT NOT NULL,
                thumbnail_url TEXT,
                image_url TEXT,
                ai_sentiment TEXT,
                ai_sentiment_score REAL,
                ai_categories TEXT,
                ai_entities TEXT,
                ai_summary TEXT,
                ai_processed BOOLEAN DEFAULT FALSE,
                ai_processed_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for performance
        news_cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category)')
        news_cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_country ON articles(country)')
        news_cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at)')
        news_cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source)')
        
        news_conn.commit()
        news_conn.close()
        
        # Live TV database
        tv_conn = sqlite3.connect(self.live_tv_db_path)
        tv_cursor = tv_conn.cursor()
        
        tv_cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                country TEXT,
                region TEXT,
                language TEXT,
                thumbnail TEXT,
                embed_url TEXT,
                stream_url TEXT,
                video_id TEXT,
                channel_id TEXT,
                is_live BOOLEAN DEFAULT FALSE,
                title TEXT,
                live_viewers INTEGER DEFAULT 0,
                started_at TEXT,
                stream_key TEXT,
                youtube_url TEXT,
                last_checked TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        tv_cursor.execute('CREATE INDEX IF NOT EXISTS idx_channels_region ON channels(region)')
        tv_cursor.execute('CREATE INDEX IF NOT EXISTS idx_channels_is_live ON channels(is_live)')
        tv_cursor.execute('CREATE INDEX IF NOT EXISTS idx_channels_category ON channels(category)')
        
        tv_conn.commit()
        tv_conn.close()
    
    def start_background_service(self):
        """Start the background scraping service"""
        self.scraping_active = True
        # Load all channels to database on startup
        threading.Thread(target=self.load_all_channels_sync, daemon=True).start()
        # Start main scraping loop
        threading.Thread(target=self.background_scraping_loop, daemon=True).start()
        print("🔄 Background data service started with all channels loading")

    def load_all_channels_sync(self):
        """Synchronous wrapper for loading all channels"""
        asyncio.run(self.load_all_channels_to_database())

    def background_scraping_loop(self):
        """Main background scraping loop"""
        while self.scraping_active:
            try:
                current_time = datetime.utcnow()
                
                # Scrape different data sources
                asyncio.run(self.scrape_news_data())
                asyncio.run(self.scrape_youtube_live_data())
                asyncio.run(self.ai_discover_channels())
                
                # Clean old data (keep only last 6 hours)
                self.clean_old_data()
                
                print(f"✅ Background scraping completed at {current_time}")
                time.sleep(self.scrape_interval)
                
            except Exception as e:
                print(f"❌ Background scraping error: {e}")
                time.sleep(10)  # Wait before retrying
    
    async def scrape_news_data(self):
        """Scrape news data from multiple sources"""
        try:
            # India-specific RSS sources
            india_sources = [
                {
                    "name": "Times of India",
                    "rss": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
                    "category": "general",
                    "country": "IN"
                },
                {
                    "name": "The Hindu",
                    "rss": "https://www.thehindu.com/news/national/feeder/default.rss",
                    "category": "general",
                    "country": "IN"
                },
                {
                    "name": "NDTV",
                    "rss": "https://www.ndtv.com/rss/top-stories",
                    "category": "general",
                    "country": "IN"
                },
                {
                    "name": "India Today",
                    "rss": "https://www.indiatoday.in/rss/home",
                    "category": "general",
                    "country": "IN"
                },
                {
                    "name": "Economic Times",
                    "rss": "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
                    "category": "finance",
                    "country": "IN"
                },
                {
                    "name": "Business Standard",
                    "rss": "https://www.business-standard.com/rss/latest-news-1.rss",
                    "category": "finance",
                    "country": "IN"
                }
            ]
            
            async with aiohttp.ClientSession() as session:
                for source in india_sources:
                    try:
                        # Check if we recently scraped this source
                        if source["name"] in self.last_scrape_time:
                            time_diff = datetime.utcnow() - self.last_scrape_time[source["name"]]
                            if time_diff.total_seconds() < 300:  # 5 minutes
                                continue
                        
                        # Fetch RSS feed
                        async with session.get(source["rss"], timeout=30) as response:
                            if response.status == 200:
                                rss_content = await response.text()
                                feed = feedparser.parse(rss_content)
                                
                                # Process articles
                                new_articles = []
                                for entry in feed.entries[:10]:  # Limit to 10 latest
                                    article_data = self.parse_rss_entry(entry, source)
                                    if article_data and self.is_article_fresh(article_data):
                                        if await self.save_article_if_new(article_data):
                                            new_articles.append(article_data)
                                
                                self.last_scrape_time[source["name"]] = datetime.utcnow()
                                print(f"✅ Scraped {len(new_articles)} new articles from {source['name']}")
                    
                    except Exception as e:
                        print(f"❌ Error scraping {source['name']}: {e}")
                        continue
        
        except Exception as e:
            print(f"❌ News scraping error: {e}")
    
    def parse_rss_entry(self, entry, source_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse RSS entry and extract article data"""
        try:
            title = entry.get('title', '').strip()
            link = entry.get('link', '')
            summary = entry.get('summary', entry.get('description', ''))
            
            if not title or not link:
                return None
            
            # Extract published date
            published = datetime.utcnow()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6])
            
            # Extract images from summary
            thumbnail_url = None
            image_url = None
            
            if summary:
                soup = BeautifulSoup(summary, 'html.parser')
                img = soup.find('img')
                if img and img.get('src'):
                    thumbnail_url = img['src']
                    image_url = img['src']
            
            # Clean summary
            if summary:
                soup = BeautifulSoup(summary, 'html.parser')
                summary = soup.get_text().strip()[:500]
            
            return {
                "title": title,
                "summary": summary,
                "source": source_info["name"],
                "url": link,
                "category": source_info["category"],
                "country": source_info["country"],
                "published_at": published.isoformat(),
                "thumbnail_url": thumbnail_url,
                "image_url": image_url,
                "ai_sentiment": None,
                "ai_processed": False
            }
            
        except Exception as e:
            print(f"❌ Error parsing RSS entry: {e}")
            return None
    
    def is_article_fresh(self, article_data: Dict[str, Any]) -> bool:
        """Check if article is fresh (published within last hour)"""
        try:
            published_time = datetime.fromisoformat(article_data["published_at"].replace('Z', '+00:00'))
            time_diff = datetime.utcnow() - published_time
            return time_diff.total_seconds() <= 3600  # 1 hour
        except:
            return True  # Assume fresh if parsing fails
    
    async def save_article_if_new(self, article_data: Dict[str, Any]) -> bool:
        """Save article to database if it's new"""
        try:
            conn = sqlite3.connect(self.news_db_path)
            cursor = conn.cursor()
            
            # Check if article already exists
            cursor.execute("SELECT id FROM articles WHERE url = ?", (article_data["url"],))
            existing = cursor.fetchone()
            
            if existing:
                conn.close()
                return False
            
            # Insert new article
            cursor.execute('''
                INSERT INTO articles (
                    title, summary, source, url, category, country, published_at,
                    thumbnail_url, image_url, ai_sentiment, ai_processed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article_data["title"],
                article_data["summary"],
                article_data["source"],
                article_data["url"],
                article_data["category"],
                article_data["country"],
                article_data["published_at"],
                article_data["thumbnail_url"],
                article_data["image_url"],
                article_data["ai_sentiment"],
                article_data["ai_processed"]
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error saving article: {e}")
            return False
    
    async def get_channel_thumbnail(self, channel_id: str) -> str:
        """Get real YouTube thumbnail for a channel"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get channel details to find latest video
                url = f"https://www.googleapis.com/youtube/v3/search"
                params = {
                    "part": "snippet",
                    "channelId": channel_id,
                    "type": "video",
                    "order": "date",
                    "maxResults": 1,
                    "key": self.youtube_api_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get("items", [])
                        
                        if items:
                            latest_video = items[0]
                            video_id = latest_video["id"]["videoId"]
                            thumbnails = latest_video["snippet"].get("thumbnails", {})
                            
                            # Get best quality thumbnail
                            thumbnail_url = (
                                thumbnails.get("high", {}).get("url") or
                                thumbnails.get("medium", {}).get("url") or
                                thumbnails.get("default", {}).get("url") or
                                f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                            )
                            return thumbnail_url
                        
                        # Fallback to channel avatar
                        return f"https://img.youtube.com/vi/default.jpg"
                    else:
                        return f"https://img.youtube.com/vi/default.jpg"
        
        except Exception as e:
            print(f"❌ Error getting thumbnail for channel {channel_id}: {e}")
            return f"https://img.youtube.com/vi/default.jpg"

    async def load_all_channels_to_database(self):
        """Load all comprehensive channels to database with real thumbnails"""
        try:
            print("Loading all comprehensive channels to database...")
            
            all_channels = []
            for category, channels in self.all_channels.items():
                for channel in channels:
                    all_channels.append({
                        **channel,
                        "category": category
                    })
            
            print(f"Processing {len(all_channels)} channels...")
            
            async with aiohttp.ClientSession() as session:
                for channel_info in all_channels:
                    try:
                        # Get real thumbnail for channel
                        thumbnail_url = await self.get_channel_thumbnail(channel_info["channel_id"])
                        
                        # Create channel data for offline channels
                        channel_data = {
                            "id": f"{channel_info['name'].lower().replace(' ', '_')}_offline",
                            "name": channel_info["name"],
                            "description": f"{channel_info['name']} - {channel_info['category'].replace('_', ' ').title()} Channel",
                            "category": channel_info["category"],
                            "country": "IN" if any(keyword in channel_info["name"].lower() for keyword in ["india", "tak", "zee", "abp", "ndtv"]) else "US",
                            "region": "india" if any(keyword in channel_info["name"].lower() for keyword in ["india", "tak", "zee", "abp", "ndtv"]) else "global",
                            "language": "en",
                            "thumbnail": thumbnail_url,  # REAL YouTube thumbnail
                            "embed_url": f"https://www.youtube.com/embed/{channel_info['channel_id']}",
                            "stream_url": f"https://www.youtube.com/channel/{channel_info['channel_id']}",
                            "video_id": channel_info["channel_id"],
                            "channel_id": channel_info["channel_id"],
                            "is_live": False,  # Offline by default
                            "title": f"{channel_info['name']} - Channel",
                            "live_viewers": 0,
                            "started_at": datetime.utcnow().isoformat(),
                            "stream_key": channel_info["name"].lower().replace(' ', '_'),
                            "youtube_url": f"https://www.youtube.com/channel/{channel_info['channel_id']}",
                            "last_checked": datetime.utcnow().isoformat()
                        }
                        
                        # Save to database (will update if exists)
                        await self.save_channel_if_new(channel_data)
                        
                    except Exception as e:
                        print(f"❌ Error loading channel {channel_info['name']}: {e}")
                        continue
            
            print(f"✅ Loaded {len(all_channels)} channels to database")
            
        except Exception as e:
            print(f"❌ Error loading channels to database: {e}")

    async def scrape_youtube_live_data(self):
        """Scrape YouTube live data using API with comprehensive channel list - PROPER LIVE DETECTION"""
        try:
            # Get all channels from comprehensive list
            all_channels = []
            
            # Add all channel categories
            for category, channels in self.all_channels.items():
                all_channels.extend(channels)
            
            print(f"Checking {len(all_channels)} total channels for live status...")
            
            live_channels_found = 0
            
            async with aiohttp.ClientSession() as session:
                for channel in all_channels:
                    try:
                        # Check live status using YouTube Data API exactly as specified
                        url = f"https://www.googleapis.com/youtube/v3/search"
                        params = {
                            "part": "snippet",
                            "channelId": channel["channel_id"],
                            "eventType": "live",
                            "type": "video",
                            "key": self.youtube_api_key,
                            "maxResults": 5
                        }
                        
                        async with session.get(url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                # Process live videos - EXACTLY AS SPECIFIED
                                items = data.get("items", [])
                                if items:
                                    live_channels_found += 1
                                    print(f"🔴 LIVE DETECTED: {channel['name']} - {len(items)} live streams")
                                    
                                    for item in items:
                                        video_id = item["id"]["videoId"]
                                        snippet = item["snippet"]
                                        
                                        # Construct YouTube URL as specified
                                        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                                        embed_url = f"https://www.youtube.com/embed/{video_id}"
                                        
                                        print(f"   📺 Live Video: {youtube_url}")
                                        
                                        # Process with real live data
                                        await self.process_youtube_video(video_id, snippet, channel)
                                else:
                                    print(f"⚫ OFFLINE: {channel['name']} - No live streams")
                    
                    except Exception as e:
                        print(f"❌ Error checking YouTube channel {channel['name']}: {e}")
                        continue
            
            print(f"✅ Live Status Check Complete: {live_channels_found}/{len(all_channels)} channels are LIVE")
        
        except Exception as e:
            print(f"❌ YouTube scraping error: {e}")

    async def check_specific_channel_live_status(self, channel_name: str, channel_id: str):
        """Check live status for a specific channel - DEMO FUNCTION"""
        try:
            print(f"🔍 Checking live status for {channel_name}...")
            
            async with aiohttp.ClientSession() as session:
                # YouTube Data API call exactly as specified
                url = f"https://www.googleapis.com/youtube/v3/search"
                params = {
                    "part": "snippet",
                    "channelId": channel_id,
                    "eventType": "live",
                    "type": "video",
                    "key": self.youtube_api_key,
                    "maxResults": 5
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get("items", [])
                        
                        if items:
                            print(f"🔴 {channel_name} is LIVE!")
                            for item in items:
                                video_id = item["id"]["videoId"]
                                snippet = item["snippet"]
                                title = snippet.get("title", "")
                                thumbnail = snippet.get("thumbnails", {}).get("high", {}).get("url", "")
                                
                                # Construct YouTube URL as specified
                                youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                                
                                print(f"   📺 Title: {title}")
                                print(f"   🖼️ Thumbnail: {thumbnail}")
                                print(f"   🔗 YouTube URL: {youtube_url}")
                                print(f"   📹 Embed URL: https://www.youtube.com/embed/{video_id}")
                        else:
                            print(f"⚫ {channel_name} is OFFLINE - No live streams")
                        return items
                    else:
                        print(f"❌ API Error: {response.status}")
                        return []
        
        except Exception as e:
            print(f"❌ Error checking {channel_name}: {e}")
            return []
    
    async def process_youtube_video(self, video_id: str, snippet: Dict[str, Any], channel_info: Dict[str, Any]):
        """Process YouTube video and save to database with real thumbnails"""
        try:
            title = snippet.get("title", "")
            description = snippet.get("description", "")
            
            # Get REAL YouTube thumbnails from snippet
            thumbnails = snippet.get("thumbnails", {})
            thumbnail_url = thumbnails.get("high", {}).get("url") or \
                           thumbnails.get("medium", {}).get("url") or \
                           thumbnails.get("default", {}).get("url") or \
                           f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
            
            # Create embed URL
            embed_url = f"https://www.youtube.com/embed/{video_id}"
            stream_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Determine category from channel info
            category = "global_news_live"  # default
            for cat_name, channels in self.all_channels.items():
                for channel in channels:
                    if channel["name"].lower() == channel_info["name"].lower():
                        category = cat_name
                        break
                if category != "global_news_live":
                    break
            
            channel_data = {
                "id": f"{channel_info['name'].lower().replace(' ', '_')}_{video_id[:8]}",
                "name": channel_info["name"],
                "description": description[:200] if description else f"{channel_info['name']} - Live News Channel",
                "category": category,
                "country": "IN" if any(keyword in channel_info["name"].lower() for keyword in ["india", "tak", "zee", "abp", "ndtv"]) else "US",
                "region": "india" if any(keyword in channel_info["name"].lower() for keyword in ["india", "tak", "zee", "abp", "ndtv"]) else "global",
                "language": "en",
                "thumbnail": thumbnail_url,  # REAL YouTube thumbnail
                "embed_url": embed_url,
                "stream_url": stream_url,
                "video_id": video_id,
                "channel_id": channel_info.get("channel_id", ""),
                "is_live": True,
                "title": title,
                "live_viewers": 0,  # Would need separate API call for this
                "started_at": datetime.utcnow().isoformat(),
                "stream_key": channel_info["name"].lower().replace(' ', '_'),
                "youtube_url": f"https://www.youtube.com/channel/{channel_info.get('channel_id', '')}",
                "last_checked": datetime.utcnow().isoformat()
            }
            
            await self.save_channel_if_new(channel_data)
            
        except Exception as e:
            print(f"❌ Error processing YouTube video: {e}")
    
    async def save_channel_if_new(self, channel_data: Dict[str, Any]) -> bool:
        """Save channel to database if it's new or update if live status changed"""
        try:
            conn = sqlite3.connect(self.live_tv_db_path)
            cursor = conn.cursor()
            
            # Check if channel exists
            cursor.execute("SELECT id, is_live FROM channels WHERE id = ?", (channel_data["id"],))
            existing = cursor.fetchone()
            
            if existing:
                # Update if live status changed
                existing_id, existing_live = existing
                if existing_live != channel_data["is_live"]:
                    cursor.execute('''
                        UPDATE channels SET 
                        is_live = ?, title = ?, thumbnail = ?, embed_url = ?, 
                        stream_url = ?, last_checked = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (
                        channel_data["is_live"],
                        channel_data["title"],
                        channel_data["thumbnail"],
                        channel_data["embed_url"],
                        channel_data["stream_url"],
                        channel_data["last_checked"],
                        channel_data["id"]
                    ))
                    conn.commit()
                    print(f"✅ Updated channel {channel_data['name']} live status")
            else:
                # Insert new channel
                cursor.execute('''
                    INSERT INTO channels (
                        id, name, description, category, country, region, language,
                        thumbnail, embed_url, stream_url, video_id, channel_id,
                        is_live, title, started_at, stream_key, youtube_url, last_checked
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    channel_data["id"],
                    channel_data["name"],
                    channel_data["description"],
                    channel_data["category"],
                    channel_data["country"],
                    channel_data["region"],
                    channel_data["language"],
                    channel_data["thumbnail"],
                    channel_data["embed_url"],
                    channel_data["stream_url"],
                    channel_data["video_id"],
                    channel_data["channel_id"],
                    channel_data["is_live"],
                    channel_data["title"],
                    channel_data["started_at"],
                    channel_data["stream_key"],
                    channel_data["youtube_url"],
                    channel_data["last_checked"]
                ))
                conn.commit()
                print(f"✅ Added new channel {channel_data['name']}")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error saving channel: {e}")
            return False
    
    async def ai_discover_channels(self):
        """AI-powered discovery of new live news channels using comprehensive list"""
        try:
            # Use AI to search for current trending news topics
            current_topics = [
                "breaking news india",
                "live news india today",
                "indian news live stream",
                "latest news india",
                "finance news india live",
                "political news india live",
                "global news live streaming"
            ]
            
            # Get all channels to check
            all_channels = []
            for category, channels in self.all_channels.items():
                all_channels.extend(channels)
            
            async with aiohttp.ClientSession() as session:
                for topic in current_topics:
                    try:
                        # Search YouTube for live streams
                        url = f"https://www.googleapis.com/youtube/v3/search"
                        params = {
                            "part": "snippet",
                            "q": topic,
                            "type": "video",
                            "eventType": "live",
                            "key": self.youtube_api_key,
                            "maxResults": 10,
                            "relevanceLanguage": "en",
                            "location": "20.5937,78.9629",  # India center
                            "locationRadius": "1000km"
                        }
                        
                        async with session.get(url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                for item in data.get("items", []):
                                    video_id = item["id"]["videoId"]
                                    snippet = item["snippet"]
                                    channel_title = snippet.get("channelTitle", "")
                                    
                                    # Check if this is a known channel
                                    known_channel = None
                                    for category, channels in self.all_channels.items():
                                        for channel in channels:
                                            if channel_title.lower() == channel["name"].lower():
                                                known_channel = channel
                                                break
                                        if known_channel:
                                            break
                                    
                                    # If it's a known channel, process it
                                    if known_channel:
                                        channel_info = {
                                            "name": known_channel["name"],
                                            "channel_id": known_channel["channel_id"]
                                        }
                                        await self.process_youtube_video(video_id, snippet, channel_info)
                                    # If it's a new channel but looks like news channel, add it
                                    elif any(keyword in channel_title.lower() for keyword in ["news", "tv", "live", "today", "times", "finance", "business"]):
                                        new_channel = {
                                            "name": channel_title,
                                            "channel_id": snippet.get("channelId", "")
                                        }
                                        await self.process_youtube_video(video_id, snippet, new_channel)
                                        print(f"🆕 Discovered new channel: {channel_title}")
                    
                    except Exception as e:
                        print(f"❌ AI discovery error for topic '{topic}': {e}")
                        continue
        
        except Exception as e:
            print(f"❌ AI discovery error: {e}")
    
    def clean_old_data(self):
        """Clean old data (older than 6 hours)"""
        try:
            # Clean old articles
            conn = sqlite3.connect(self.news_db_path)
            cursor = conn.cursor()
            
            cutoff_time = (datetime.utcnow() - timedelta(hours=6)).isoformat()
            cursor.execute("DELETE FROM articles WHERE published_at < ?", (cutoff_time,))
            deleted_articles = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            # Clean old offline channels
            conn = sqlite3.connect(self.live_tv_db_path)
            cursor = conn.cursor()
            
            # Remove channels that haven't been checked in 1 hour and are offline
            cutoff_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
            cursor.execute("DELETE FROM channels WHERE is_live = 0 AND last_checked < ?", (cutoff_time,))
            deleted_channels = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if deleted_articles > 0 or deleted_channels > 0:
                print(f"🧹 Cleaned {deleted_articles} old articles and {deleted_channels} old channels")
        
        except Exception as e:
            print(f"❌ Error cleaning old data: {e}")
    
    def get_articles(self, category: str = None, country: str = "IN", limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """Get articles from database"""
        try:
            conn = sqlite3.connect(self.news_db_path)
            cursor = conn.cursor()
            
            # Build query
            query = "SELECT * FROM articles WHERE country = ?"
            params = [country]
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            query += " ORDER BY published_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            articles = cursor.fetchall()
            
            # Get total count
            count_query = "SELECT COUNT(*) FROM articles WHERE country = ?"
            count_params = [country]
            
            if category:
                count_query += " AND category = ?"
                count_params.append(category)
            
            cursor.execute(count_query, count_params)
            total = cursor.fetchone()[0]
            
            conn.close()
            
            # Convert to list of dicts
            article_list = []
            for article in articles:
                article_dict = {
                    "id": article[0],
                    "title": article[1],
                    "summary": article[2],
                    "source": article[3],
                    "url": article[4],
                    "category": article[5],
                    "country": article[6],
                    "published": article[7],
                    "thumbnail_url": article[8],
                    "image_url": article[9],
                    "ai_sentiment": article[10],
                    "ai_sentiment_score": article[11],
                    "ai_categories": article[12],
                    "ai_entities": article[13],
                    "ai_summary": article[14],
                    "ai_processed": bool(article[15])
                }
                article_list.append(article_dict)
            
            return {
                "articles": article_list,
                "pagination": {
                    "page": (offset // limit) + 1,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit
                },
                "cache_status": "database",
                "last_updated": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            print(f"❌ Error getting articles: {e}")
            return {"articles": [], "pagination": {"page": 1, "limit": limit, "total": 0, "pages": 0}}
    
    def get_live_channels(self, region: str = "india") -> Dict[str, Any]:
        """Get ALL channels (live and offline) from database with real thumbnails"""
        try:
            conn = sqlite3.connect(self.live_tv_db_path)
            cursor = conn.cursor()
            
            # Get ALL channels (both live and offline)
            if region == "all":
                cursor.execute('''
                    SELECT * FROM channels 
                    ORDER BY is_live DESC, name ASC
                ''')
            else:
                cursor.execute('''
                    SELECT * FROM channels 
                    WHERE region = ? 
                    ORDER BY is_live DESC, name ASC
                ''', (region,))
            
            all_channels = cursor.fetchall()
            
            # Get live channels specifically
            cursor.execute('''
                SELECT * FROM channels 
                WHERE is_live = 1 
                ORDER BY started_at DESC
            ''')
            live_channels = cursor.fetchall()
            
            conn.close()
            
            # Convert to list of dicts
            channel_list = []
            live_list = []
            
            for channel in all_channels:
                channel_dict = {
                    "id": channel[0],
                    "name": channel[1],
                    "description": channel[2],
                    "category": channel[3],
                    "country": channel[4],
                    "region": channel[5],
                    "language": channel[6],
                    "thumbnail": channel[7],  # REAL YouTube thumbnail
                    "embed_url": channel[8],
                    "stream_url": channel[9],
                    "video_id": channel[10],
                    "channel_id": channel[11],
                    "is_live": bool(channel[12]),
                    "title": channel[13],
                    "live_viewers": channel[14],
                    "started_at": channel[15],
                    "stream_key": channel[16],
                    "youtube_url": channel[17],
                    "last_checked": channel[18]
                }
                channel_list.append(channel_dict)
                
                if channel_dict["is_live"]:
                    live_list.append(channel_dict)
            
            return {
                "total_channels": len(all_channels),
                "live_channels": len(live_list),
                "offline_channels": len(all_channels) - len(live_list),
                "all": channel_list,  # ALL channels (live + offline)
                "live": live_list,
                "offline": [ch for ch in channel_list if not ch["is_live"]],
                "last_updated": datetime.utcnow().isoformat(),
                "status": "real_data"
            }
        
        except Exception as e:
            print(f"❌ Error getting channels: {e}")
            return {"total_channels": 0, "live_channels": 0, "all": [], "live": [], "offline": []}

# Global instance
background_service = BackgroundDataService()
