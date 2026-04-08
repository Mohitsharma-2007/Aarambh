"""
Enhanced YouTube Live Detector with Comprehensive Channel List
Includes all Indian and global news channels as requested
"""

import httpx
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import re

class YouTubeLiveDetector:
    def __init__(self):
        self.api_key = "AIzaSyAvlzrDV3OirF5H7MXl_HdwtNl8BgS6Mg0"
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Comprehensive channel mappings including all requested channels
        self.channel_mappings = {
            # Indian General News Channels
            "aaj_tak": {
                "channel_id": "UCZFMm1mW0Z81r3j3rN5cA",
                "handle": "aajtak",
                "name": "Aaj Tak",
                "category": "general_news",
                "country": "IN",
                "region": "india",
                "youtube_url": "https://www.youtube.com/@aajtak"
            },
            "abp_news": {
                "channel_id": "UCtFmDy6oD28Dn2aWmCXQ",
                "handle": "abpnews",
                "name": "ABP News",
                "category": "general_news",
                "country": "IN",
                "region": "india",
                "youtube_url": "https://www.youtube.com/@abpnews"
            },
            "zee_news": {
                "channel_id": "UC0mm7QwL1eMwFqYt_4A",
                "handle": "ZeeNews",
                "name": "Zee News",
                "category": "general_news",
                "country": "IN",
                "region": "india",
                "youtube_url": "https://www.youtube.com/@ZeeNews"
            },
            "india_tv": {
                "channel_id": "UCn7sPr7o0EAn92Fm3j6p_wQ",
                "handle": "IndiaTV",
                "name": "India TV",
                "category": "general_news",
                "country": "IN",
                "region": "india",
                "youtube_url": "https://www.youtube.com/@IndiaTV"
            },
            "ndtv_24x7": {
                "channel_id": "UCZL-Y8QDBY_W2rAUbq_a5AQ",
                "handle": "ndtv",
                "name": "NDTV 24x7",
                "category": "general_news",
                "country": "IN",
                "region": "india",
                "youtube_url": "https://www.youtube.com/@ndtv"
            },
            "cnn_news18": {
                "channel_id": "UCi6X0-8d_0w2rA2Jg5H3Q",
                "handle": "CNNnews18",
                "name": "CNN-News18",
                "category": "general_news",
                "country": "IN",
                "region": "india",
                "youtube_url": "https://www.youtube.com/@CNNnews18"
            },
            "republic_world": {
                "channel_id": "UCZFMm1mW0Z81r3j3rN5cA",
                "handle": "RepublicWorld",
                "name": "Republic World",
                "category": "general_news",
                "country": "IN",
                "region": "india",
                "youtube_url": "https://www.youtube.com/@RepublicWorld"
            },
            "times_now": {
                "channel_id": "UC6RJ7-PaXg66y6zH78qf_Tw",
                "handle": "TimesNow",
                "name": "Times Now",
                "category": "general_news",
                "country": "IN",
                "region": "india",
                "youtube_url": "https://www.youtube.com/@TimesNow"
            },
            "wion": {
                "channel_id": "UC_g0wS_KNoiQZpXqF8HqYpQ",
                "handle": "WIONews",
                "name": "WION",
                "category": "general_news",
                "country": "IN",
                "region": "india",
                "youtube_url": "https://www.youtube.com/@WIONews"
            },
            
            # Indian Finance News Channels
            "cnbc_tv18": {
                "channel_id": "UC8F3k71jQ8BQ8pQ8J8Q8Q",
                "handle": "cnbctv18india",
                "name": "CNBC TV18",
                "category": "finance_news",
                "country": "IN",
                "region": "india",
                "youtube_url": "https://www.youtube.com/@cnbctv18india"
            },
            "zee_business": {
                "channel_id": "UC0mm7QwL1eMwFqYt_4A",
                "handle": "ZeeBusiness",
                "name": "Zee Business",
                "category": "finance_news",
                "country": "IN",
                "region": "india",
                "youtube_url": "https://www.youtube.com/@ZeeBusiness"
            },
            
            # Global General News Channels
            "cnn": {
                "channel_id": "UCupvZG-5koHEi_75aLxfV0A",
                "handle": "CNN",
                "name": "CNN",
                "category": "general_news",
                "country": "US",
                "region": "global",
                "youtube_url": "https://www.youtube.com/@CNN"
            },
            "bbc_news": {
                "channel_id": "UCK8sQmJBp8GCxrOtXWBpyEA",
                "handle": "BBCNews",
                "name": "BBC News",
                "category": "general_news",
                "country": "GB",
                "region": "global",
                "youtube_url": "https://www.youtube.com/@BBCNews"
            },
            "al_jazeera_english": {
                "channel_id": "UCNyn3feLj5EAXtDI5pXg",
                "handle": "aljazeeraenglish",
                "name": "Al Jazeera English",
                "category": "general_news",
                "country": "QA",
                "region": "global",
                "youtube_url": "https://www.youtube.com/@aljazeeraenglish"
            },
            "france_24": {
                "channel_id": "UCwpsAqBHilKw4V9X2tA",
                "handle": "FRANCE24",
                "name": "France 24 English",
                "category": "general_news",
                "country": "FR",
                "region": "global",
                "youtube_url": "https://www.youtube.com/@FRANCE24"
            },
            "dw_news": {
                "channel_id": "UCkn7Y9j3eyG8VoSe97ifQ",
                "handle": "dwnews",
                "name": "DW News",
                "category": "general_news",
                "country": "DE",
                "region": "global",
                "youtube_url": "https://www.youtube.com/@dwnews"
            },
            
            # Global Finance News Channels
            "bloomberg_tv": {
                "channel_id": "UCqCFSnIiO24R2DdV2gNA",
                "handle": "BloombergTV",
                "name": "Bloomberg Television",
                "category": "finance_news",
                "country": "US",
                "region": "global",
                "youtube_url": "https://www.youtube.com/@BloombergTV"
            },
            "cnbc": {
                "channel_id": "UCqMbDAP7_1A9v9_6cGjT2iA",
                "handle": "CNBC",
                "name": "CNBC",
                "category": "finance_news",
                "country": "US",
                "region": "global",
                "youtube_url": "https://www.youtube.com/@CNBC"
            },
            "reuters": {
                "channel_id": "UCdtkLqVArwHD_o8qB5LQ",
                "handle": "Reuters",
                "name": "Reuters",
                "category": "finance_news",
                "country": "US",
                "region": "global",
                "youtube_url": "https://www.youtube.com/@Reuters"
            }
        }

    async def get_live_status_scrape(self, channel_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fallback: Scrape YouTube live redirect to detect live status"""
        handle = channel_info.get("handle")
        channel_id = channel_info.get("channel_id")
        
        # Try handle first, then channel ID
        if handle:
            url = f"https://www.youtube.com/@{handle}/live"
        else:
            url = f"https://www.youtube.com/channel/{channel_id}/live"
            
        try:
            # Use a realistic User-Agent to avoid blocking
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9"
            }
            async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    return None
                    
                content = response.text
                
                # Check for live indicators in HTML/Scripts
                # Multiple possible markers for live status
                is_live = (
                    '"isLive":true' in content or 
                    '"isLive": true' in content or
                    '{"label":"LIVE"}' in content or 
                    '"style":"LIVE"' in content or
                    'watching now' in content.lower()
                )
                
                # Extract Video ID using regex - more robust patterns
                video_id = None
                patterns = [
                    r'"videoId":"([a-zA-Z0-9_-]{11})"',
                    r'href="https://www.youtube.com/watch\?v=([a-zA-Z0-9_-]{11})"',
                    r'v=([a-zA-Z0-9_-]{11})',
                    r'/embed/([a-zA-Z0-9_-]{11})',
                    r'"video_id":"([a-zA-Z0-9_-]{11})"'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, content)
                    if match:
                        video_id = match.group(1)
                        # If we found a video ID and it's a live-style page, assume it's the one
                        if is_live:
                            break
                
                if is_live and video_id:
                    # Try to extract title
                    title_match = re.search(r'"title":\{"runs":\[\{"text":"(.*?)"\}\]', content)
                    title = title_match.group(1) if title_match else f"{channel_info['name']} Live"
                    
                    return {
                        "video_id": video_id,
                        "title": title,
                        "is_live": True,
                        "thumbnail": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                    }
        except Exception as e:
            print(f"Scrape error for {channel_info['name']}: {e}")
            
        return None

    async def check_channel_live_status(self, channel_key: str) -> Optional[Dict[str, Any]]:
        """Check if a channel is currently live and return live video info"""
        if channel_key not in self.channel_mappings:
            return None
            
        channel_info = self.channel_mappings[channel_key]
        channel_id = channel_info["channel_id"]
        
        # 1. Try API first (with caching potential)
        live_data = None
        try:
            url = f"{self.base_url}/search"
            params = {
                "part": "snippet",
                "channelId": channel_id,
                "eventType": "live",
                "type": "video",
                "key": self.api_key,
                "maxResults": 1
            }
            
            response = await self.client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("items"):
                    live_item = data["items"][0]
                    video_id = live_item["id"]["videoId"]
                    snippet = live_item["snippet"]
                    
                    # Get detailed video info
                    video_info = await self.get_video_details(video_id)
                    
                    live_data = {
                        "video_id": video_id,
                        "title": snippet.get("title"),
                        "is_live": True,
                        "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                        "live_viewers": video_info.get("live_viewers", 0),
                        "started_at": video_info.get("published_at")
                    }
            elif response.status_code == 403:
                # Quota exceeded - Fallback to scraping!
                print(f"API Quota exceeded for {channel_key}, switching to scraping...")
                live_data = await self.get_live_status_scrape(channel_info)
        except Exception as e:
            print(f"API Error checking {channel_key}: {e}")
            live_data = await self.get_live_status_scrape(channel_info)

        # 2. Use live_data if found (from either API or Scrape)
        if live_data and live_data.get("is_live"):
            video_id = live_data["video_id"]
            return {
                "id": channel_key,
                "name": channel_info["name"],
                "description": live_data.get("title", channel_info["name"] + " Live Stream"),
                "category": channel_info["category"],
                "country": channel_info["country"],
                "region": channel_info["region"],
                "language": "en",
                "thumbnail": live_data.get("thumbnail"),
                "embed_url": f"https://www.youtube.com/embed/{video_id}?autoplay=1&mute=1",
                "stream_url": f"https://www.youtube.com/watch?v={video_id}",
                "video_id": video_id,
                "channel_id": channel_id,
                "is_live": True,
                "title": live_data.get("title", channel_info["name"] + " Live"),
                "live_viewers": live_data.get("live_viewers", 0),
                "started_at": live_data.get("started_at"),
                "stream_key": channel_key,
                "youtube_url": channel_info["youtube_url"]
            }
        else:
            # Channel is not live, return offline info
            return {
                "id": channel_key,
                "name": channel_info["name"],
                "description": f"{channel_info['name']} - Currently Offline",
                "category": channel_info["category"],
                "country": channel_info["country"],
                "region": channel_info["region"],
                "language": "en",
                "thumbnail": None,
                "embed_url": None,
                "stream_url": None,
                "video_id": None,
                "channel_id": channel_id,
                "is_live": False,
                "title": f"{channel_info['name']} - Offline",
                "live_viewers": 0,
                "started_at": None,
                "stream_key": channel_key,
                "youtube_url": channel_info["youtube_url"]
            }

    async def get_video_details(self, video_id: str) -> Dict[str, Any]:
        """Get detailed video information including live viewer count"""
        try:
            url = f"{self.base_url}/videos"
            params = {
                "part": "snippet,liveStreamingDetails",
                "id": video_id,
                "key": self.api_key
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("items"):
                video = data["items"][0]
                live_details = video.get("liveStreamingDetails", {})
                
                return {
                    "title": video["snippet"]["title"],
                    "description": video["snippet"]["description"],
                    "published_at": video["snippet"]["publishedAt"],
                    "live_viewers": live_details.get("concurrentViewers", 0),
                    "actual_start_time": live_details.get("actualStartTime"),
                    "scheduled_start_time": live_details.get("scheduledStartTime")
                }
        except Exception as e:
            print(f"Error getting video details for {video_id}: {e}")
        
        return {}

    async def check_all_channels_live_status(self) -> List[Dict[str, Any]]:
        """Check live status for all configured channels"""
        tasks = []
        for channel_key in self.channel_mappings.keys():
            task = self.check_channel_live_status(channel_key)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        live_channels = []
        for result in results:
            if isinstance(result, dict) and result:
                live_channels.append(result)
        
        return live_channels

    async def get_live_channels_only(self) -> List[Dict[str, Any]]:
        """Get only channels that are currently live"""
        all_channels = await self.check_all_channels_live_status()
        return [channel for channel in all_channels if channel.get("is_live", False)]

    async def get_war_live_streams(self) -> List[Dict[str, Any]]:
        """Get live streams relevant to war/conflict coverage"""
        # Channels that typically cover war/conflict
        war_channels = ["bbc_news", "cnn", "al_jazeera_english", "reuters", "dw_news", "france_24"]
        
        tasks = []
        for channel_key in war_channels:
            task = self.check_channel_live_status(channel_key)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        war_streams = []
        for result in results:
            if isinstance(result, dict) and result and result.get("is_live", False):
                # Check if title/description contains war-related keywords
                title_desc = (result.get("title", "") + " " + result.get("description", "")).lower()
                war_keywords = ["war", "conflict", "ukraine", "gaza", "israel", "russia", "military", "attack"]
                
                if any(keyword in title_desc for keyword in war_keywords):
                    result["category"] = "war"
                    war_streams.append(result)
                else:
                    # Still include major news channels in war section
                    result["category"] = "war"
                    war_streams.append(result)
        
        return war_streams

    async def get_channels_by_region(self, region: str) -> List[Dict[str, Any]]:
        """Get channels filtered by region (india/global)"""
        region_channels = []
        for channel_key, channel_info in self.channel_mappings.items():
            if channel_info.get("region") == region:
                channel_status = await self.check_channel_live_status(channel_key)
                if channel_status:
                    region_channels.append(channel_status)
        
        # Sort by live status and name
        region_channels.sort(key=lambda x: (not x.get("is_live", False), x["name"]))
        return region_channels

    async def get_channels_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get channels filtered by category"""
        category_channels = []
        for channel_key, channel_info in self.channel_mappings.items():
            if channel_info.get("category") == category:
                channel_status = await self.check_channel_live_status(channel_key)
                if channel_status:
                    category_channels.append(channel_status)
        
        # Sort by live status and name
        category_channels.sort(key=lambda x: (not x.get("is_live", False), x["name"]))
        return category_channels

    async def get_india_channels(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all Indian channels grouped by category"""
        general_news = await self.get_channels_by_region_and_category("india", "general_news")
        finance_news = await self.get_channels_by_region_and_category("india", "finance_news")
        
        return {
            "general_news": general_news,
            "finance_news": finance_news,
            "total": len(general_news) + len(finance_news)
        }

    async def get_global_channels(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all global channels grouped by category"""
        general_news = await self.get_channels_by_region_and_category("global", "general_news")
        finance_news = await self.get_channels_by_region_and_category("global", "finance_news")
        
        return {
            "general_news": general_news,
            "finance_news": finance_news,
            "total": len(general_news) + len(finance_news)
        }

    async def get_channels_by_region_and_category(self, region: str, category: str) -> List[Dict[str, Any]]:
        """Get channels filtered by both region and category"""
        channels = []
        for channel_key, channel_info in self.channel_mappings.items():
            if (channel_info.get("region") == region and 
                channel_info.get("category") == category):
                channel_status = await self.check_channel_live_status(channel_key)
                if channel_status:
                    channels.append(channel_status)
        
        # Sort by live status and name
        channels.sort(key=lambda x: (not x.get("is_live", False), x["name"]))
        return channels

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Global instance
youtube_detector = YouTubeLiveDetector()
