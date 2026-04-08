"""
Enhanced Live TV Router with YouTube Data API Integration
Automatically detects live streams and provides working video IDs
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import List, Dict, Any, Optional
from youtube_live_detector import youtube_detector
import asyncio
from datetime import datetime

router = APIRouter()

@router.get("/live-status", summary="Check live status of all configured channels")
async def check_all_channels_live_status():
    """Check live status for all configured news channels using YouTube Data API"""
    try:
        channels = await youtube_detector.check_all_channels_live_status()
        
        # Separate live and offline channels
        live_channels = [ch for ch in channels if ch.get("is_live", False)]
        offline_channels = [ch for ch in channels if not ch.get("is_live", False)]
        
        return {
            "total_channels": len(channels),
            "live_channels": len(live_channels),
            "offline_channels": len(offline_channels),
            "live": live_channels,
            "offline": offline_channels,
            "last_updated": datetime.utcnow().isoformat(),
            "api_source": "youtube_data_api"
        }
        
    except Exception as e:
        print(f"Error checking live status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check live status: {str(e)}")

@router.get("/live-only", summary="Get only channels that are currently live")
async def get_live_channels_only():
    """Get only channels that are currently streaming live"""
    try:
        live_channels = await youtube_detector.get_live_channels_only()
        
        return {
            "live_channels": live_channels,
            "total": len(live_channels),
            "last_updated": datetime.utcnow().isoformat(),
            "description": "Channels currently streaming live content"
        }
        
    except Exception as e:
        print(f"Error getting live channels: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get live channels: {str(e)}")

@router.get("/war-live", summary="Get live streams covering war/conflict news")
async def get_war_live_streams():
    """Get live streams that are covering war/conflict related content"""
    try:
        war_streams = await youtube_detector.get_war_live_streams()
        
        # If no war-specific streams, get general live news
        if not war_streams:
            all_live = await youtube_detector.get_live_channels_only()
            # Take top 3 live news channels
            war_streams = all_live[:3]
            for stream in war_streams:
                stream["category"] = "war"
                stream["description"] = f"{stream['name']} - Live News Coverage"
        
        return {
            "war_streams": war_streams,
            "total": len(war_streams),
            "last_updated": datetime.utcnow().isoformat(),
            "description": "Live streams covering war and conflict zones"
        }
        
    except Exception as e:
        print(f"Error getting war streams: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get war streams: {str(e)}")

@router.get("/channel/{channel_key}/status", summary="Check live status of specific channel")
async def check_channel_status(channel_key: str):
    """Check live status of a specific channel by key"""
    try:
        channel_status = await youtube_detector.check_channel_live_status(channel_key)
        
        if not channel_status:
            raise HTTPException(status_code=404, detail=f"Channel '{channel_key}' not found")
        
        return {
            "channel": channel_status,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error checking channel status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check channel status: {str(e)}")

@router.get("/channel/{channel_key}/embed", summary="Get embed URL for live channel")
async def get_channel_embed_url(channel_key: str):
    """Get the embed URL for a specific channel if it's live"""
    try:
        channel_status = await youtube_detector.check_channel_live_status(channel_key)
        
        if not channel_status:
            raise HTTPException(status_code=404, detail=f"Channel '{channel_key}' not found")
        
        if not channel_status.get("is_live", False):
            return {
                "channel_key": channel_key,
                "name": channel_status["name"],
                "is_live": False,
                "embed_url": None,
                "message": f"{channel_status['name']} is currently offline"
            }
        
        return {
            "channel_key": channel_key,
            "name": channel_status["name"],
            "is_live": True,
            "embed_url": channel_status["embed_url"],
            "video_id": channel_status["video_id"],
            "stream_url": channel_status["stream_url"],
            "title": channel_status["title"],
            "live_viewers": channel_status.get("live_viewers", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting embed URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get embed URL: {str(e)}")

@router.get("/search", summary="Search for live channels by query")
async def search_live_channels(q: str = "news", limit: int = 10):
    """Search for live channels by query"""
    try:
        live_streams = await youtube_detector.search_live_channels(q, limit)
        
        return {
            "query": q,
            "live_streams": live_streams,
            "total": len(live_streams),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Error searching live channels: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search live channels: {str(e)}")

@router.get("/featured", summary="Get featured live news channels")
async def get_featured_live_channels():
    """Get top featured live news channels"""
    try:
        # Check specific major news channels
        featured_keys = ["bbc_world", "cnn_international", "al_jazeera"]
        
        tasks = []
        for channel_key in featured_keys:
            task = youtube_detector.check_channel_live_status(channel_key)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        featured_channels = []
        for result in results:
            if isinstance(result, dict) and result:
                featured_channels.append(result)
        
        # Sort by live status (live first) and then by name
        featured_channels.sort(key=lambda x: (not x.get("is_live", False), x["name"]))
        
        return {
            "featured": featured_channels,
            "total": len(featured_channels),
            "live_count": len([ch for ch in featured_channels if ch.get("is_live", False)]),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Error getting featured channels: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get featured channels: {str(e)}")

@router.get("/category/{category}", summary="Get live channels by category")
async def get_live_channels_by_category(category: str):
    """Get live channels filtered by category"""
    try:
        if category.lower() == "war":
            war_streams = await youtube_detector.get_war_live_streams()
            return {
                "category": "war",
                "channels": war_streams,
                "total": len(war_streams),
                "last_updated": datetime.utcnow().isoformat()
            }
        
        # For other categories, check relevant channels
        category_mappings = {
            "world": ["bbc_world", "cnn_international", "al_jazeera", "reuters"],
            "news": ["bbc_world", "cnn_international", "al_jazeera", "ndtv_24x7", "times_of_india"],
            "finance": ["cnbc", "reuters"],
            "us": ["cnn_international", "fox_news"],
            "uk": ["bbc_world"],
            "india": ["ndtv_24x7", "times_of_india"],
            "middle_east": ["al_jazeera"]
        }
        
        channel_keys = category_mappings.get(category.lower(), [])
        if not channel_keys:
            # Return empty if category not found
            return {
                "category": category,
                "channels": [],
                "total": 0,
                "last_updated": datetime.utcnow().isoformat()
            }
        
        tasks = []
        for channel_key in channel_keys:
            task = youtube_detector.check_channel_live_status(channel_key)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        category_channels = []
        for result in results:
            if isinstance(result, dict) and result:
                category_channels.append(result)
        
        # Sort by live status
        category_channels.sort(key=lambda x: (not x.get("is_live", False), x["name"]))
        
        return {
            "category": category,
            "channels": category_channels,
            "total": len(category_channels),
            "live_count": len([ch for ch in category_channels if ch.get("is_live", False)]),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Error getting channels by category: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get channels by category: {str(e)}")

@router.get("/health", summary="Health check for YouTube API integration")
async def health_check():
    """Health check for YouTube Data API integration"""
    try:
        # Test API by checking one channel
        test_channel = await youtube_detector.check_channel_live_status("bbc_world")
        
        return {
            "status": "healthy",
            "youtube_api_working": True,
            "test_channel": test_channel.get("name", "Unknown"),
            "test_channel_live": test_channel.get("is_live", False),
            "api_key_configured": bool(youtube_detector.api_key),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "youtube_api_working": False,
            "error": str(e),
            "api_key_configured": bool(youtube_detector.api_key),
            "last_updated": datetime.utcnow().isoformat()
        }

@router.get("/directory", summary="Get complete channel directory with live status")
async def get_channel_directory():
    """Get complete directory of all channels with current live status"""
    try:
        all_channels = await youtube_detector.check_all_channels_live_status()
        
        # Group by category
        categories = {}
        for channel in all_channels:
            category = channel.get("category", "general")
            if category not in categories:
                categories[category] = []
            categories[category].append(channel)
        
        # Group by country
        countries = {}
        for channel in all_channels:
            country = channel.get("country", "Unknown")
            if country not in countries:
                countries[country] = []
            countries[country].append(channel)
        
        return {
            "categories": categories,
            "countries": countries,
            "total_channels": len(all_channels),
            "live_channels": len([ch for ch in all_channels if ch.get("is_live", False)]),
            "last_updated": datetime.utcnow().isoformat(),
            "api_source": "youtube_data_api"
        }
        
    except Exception as e:
        print(f"Error getting directory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get directory: {str(e)}")

# Background task to periodically refresh live status
async def refresh_live_status_background():
    """Background task to refresh live status of all channels"""
    try:
        print("🔄 Refreshing live status...")
        await youtube_detector.check_all_channels_live_status()
        print("✅ Live status refreshed")
    except Exception as e:
        print(f"❌ Failed to refresh live status: {e}")
