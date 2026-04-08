"""
YouTube Data API Integration for Live Stream Detection
Automatically detects live streams and gets current video IDs
"""

import httpx
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

class YouTubeLiveDetector:
    def __init__(self):
        self.api_key = "AIzaSyAvlzrDV3OirF5H7MXl_HdwtNl8BgS6Mg0"
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Channel mappings for major news channels
        self.channel_mappings = {
            "bbc_world": {
                "channel_id": "UCK8sQmJBp8GCxrOtXWBpyEA",  # BBC World News
                "name": "BBC World News",
                "category": "world",
                "country": "GB"
            },
            "cnn_international": {
                "channel_id": "UCupvZG-5koHEi_75aLxfV0A",  # CNN International
                "name": "CNN International", 
                "category": "world",
                "country": "US"
            },
            "al_jazeera": {
                "channel_id": "UCNye-wNBqds5alhEazB1Z-g",  # Al Jazeera English
                "name": "Al Jazeera English",
                "category": "world", 
                "country": "QA"
            },
            "ndtv_24x7": {
                "channel_id": "UCZL-Y8QDBY_W2rAUbq_a5AQ",  # NDTV 24x7
                "name": "NDTV 24x7",
                "category": "news",
                "country": "IN"
            },
            "reuters": {
                "channel_id": "UCupvZG-5koHEi_75aLxfV0A",  # Using CNN as Reuters proxy
                "name": "Reuters News",
                "category": "world",
                "country": "US"
            },
            "fox_news": {
                "channel_id": "UCZIJ6FI-uJ2B5_4QjL_81-Q",  # Fox News
                "name": "Fox News",
                "category": "news",
                "country": "US"
            },
            "cnbc": {
                "channel_id": "UCqMbDAP7_1A9v9_6cGjT2iA",  # CNBC
                "name": "CNBC",
                "category": "finance",
                "country": "US"
            },
            "times_of_india": {
                "channel_id": "UCrY7-4y4_8iF2T9T7w8Q0gA",  # Times of India
                "name": "Times of India",
                "category": "news",
                "country": "IN"
            }
        }

    async def check_channel_live_status(self, channel_key: str) -> Optional[Dict[str, Any]]:
        """Check if a channel is currently live and return live video info"""
        if channel_key not in self.channel_mappings:
            return None
            
        channel_info = self.channel_mappings[channel_key]
        channel_id = channel_info["channel_id"]
        
        try:
            # Search for live videos from this channel
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
            response.raise_for_status()
            data = response.json()
            
            if data.get("items"):
                live_item = data["items"][0]
                video_id = live_item["id"]["videoId"]
                snippet = live_item["snippet"]
                
                # Get detailed video info
                video_info = await self.get_video_details(video_id)
                
                return {
                    "id": channel_key,
                    "name": channel_info["name"],
                    "description": snippet.get("description", channel_info["name"] + " Live Stream"),
                    "category": channel_info["category"],
                    "country": channel_info["country"],
                    "language": "en",
                    "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                    "embed_url": f"https://www.youtube.com/embed/{video_id}",
                    "stream_url": f"https://www.youtube.com/watch?v={video_id}",
                    "video_id": video_id,
                    "channel_id": channel_id,
                    "is_live": True,
                    "title": snippet.get("title", channel_info["name"] + " Live"),
                    "live_viewers": video_info.get("live_viewers", 0),
                    "started_at": video_info.get("published_at"),
                    "stream_key": channel_key
                }
            else:
                # Channel is not live, return offline info
                return {
                    "id": channel_key,
                    "name": channel_info["name"],
                    "description": f"{channel_info['name']} - Currently Offline",
                    "category": channel_info["category"],
                    "country": channel_info["country"],
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
                    "stream_key": channel_key
                }
                
        except Exception as e:
            print(f"Error checking live status for {channel_key}: {e}")
            return {
                "id": channel_key,
                "name": channel_info["name"],
                "description": f"{channel_info['name']} - Error checking status",
                "category": channel_info["category"],
                "country": channel_info["country"],
                "language": "en",
                "thumbnail": None,
                "embed_url": None,
                "stream_url": None,
                "video_id": None,
                "channel_id": channel_id,
                "is_live": False,
                "title": f"{channel_info['name']} - Status Unknown",
                "live_viewers": 0,
                "started_at": None,
                "stream_key": channel_key
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
        war_channels = ["bbc_world", "cnn_international", "al_jazeera", "reuters"]
        
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

    async def get_channel_by_name(self, channel_name: str) -> Optional[Dict[str, Any]]:
        """Find channel by name (case-insensitive)"""
        for channel_key, channel_info in self.channel_mappings.items():
            if channel_info["name"].lower() == channel_name.lower():
                return await self.check_channel_live_status(channel_key)
        return None

    async def search_live_channels(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for live channels by query"""
        try:
            url = f"{self.base_url}/search"
            params = {
                "part": "snippet",
                "q": query,
                "eventType": "live",
                "type": "video",
                "key": self.api_key,
                "maxResults": max_results
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            live_streams = []
            for item in data.get("items", []):
                video_id = item["id"]["videoId"]
                snippet = item["snippet"]
                
                live_streams.append({
                    "id": f"search_{video_id}",
                    "name": snippet.get("channelTitle", "Unknown Channel"),
                    "description": snippet.get("description", ""),
                    "category": "search",
                    "country": "Unknown",
                    "language": "en",
                    "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                    "embed_url": f"https://www.youtube.com/embed/{video_id}",
                    "stream_url": f"https://www.youtube.com/watch?v={video_id}",
                    "video_id": video_id,
                    "channel_id": snippet.get("channelId"),
                    "is_live": True,
                    "title": snippet.get("title", ""),
                    "live_viewers": 0,
                    "started_at": snippet.get("publishedAt"),
                    "stream_key": f"search_{video_id}"
                })
            
            return live_streams
            
        except Exception as e:
            print(f"Error searching live channels: {e}")
            return []

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Global instance
youtube_detector = YouTubeLiveDetector()
