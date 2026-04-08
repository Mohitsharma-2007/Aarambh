"""
Enhanced Live TV Router with Comprehensive Channel Support
Includes all Indian and global news channels
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import List, Dict
from fastapi import APIRouter
from youtube_live_detector_enhanced import youtube_detector
from background_data_service import background_service
import asyncio
from datetime import datetime

router = APIRouter()

@router.get("/live-status", summary="Get ALL channels (live and offline) with real YouTube thumbnails")
async def check_all_channels_live_status():
    """Get ALL channels from background service with real thumbnails"""
    try:
        print("Getting ALL channels (live and offline) from background service...")
        
        # Get ALL channels (live and offline) from background service
        result = background_service.get_live_channels(region="all")
        
        print(f"Background service returned {result['total_channels']} total channels ({result['live_channels']} live, {result['offline_channels']} offline)")
        
        # Add region-specific grouping
        india_channels = [ch for ch in result["all"] if ch.get("region") == "india"]
        global_channels = [ch for ch in result["all"] if ch.get("region") == "global"]
        
        # Get all channels from comprehensive list for display
        all_channels = background_service.all_channels
        
        return {
            "total_channels": result["total_channels"],
            "live_channels": result["live_channels"],
            "offline_channels": result["offline_channels"],
            "india_channels": len(india_channels),
            "global_channels": len(global_channels),
            "all": result["all"],  # ALL channels (live + offline)
            "live": result["live"],
            "offline": result["offline"],
            "india": india_channels,
            "global": global_channels,
            "all_categories": {
                "finance_high_level": len(all_channels.get("finance_high_level", [])),
                "global_news_live": len(all_channels.get("global_news_live", [])),
                "geopolitics_high_signal": len(all_channels.get("geopolitics_high_signal", [])),
                "defense_military": len(all_channels.get("defense_military", [])),
                "analysis_macro_intelligence": len(all_channels.get("analysis_macro_intelligence", []))
            },
            "total_available_channels": sum(len(channels) for channels in all_channels.values()),
            "last_updated": result["last_updated"],
            "api_source": "background_service_comprehensive",
            "status": "real_data",
            "thumbnail_quality": "real_youtube_thumbnails"
        }
        
    except Exception as e:
        print(f"Error getting all channels: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get all channels: {str(e)}")

@router.get("/categories/{category}", summary="Get ALL channels by category (live and offline)")
async def get_channels_by_category(category: str):
    """Get ALL channels from specific category with live status and real thumbnails"""
    try:
        print(f"Getting ALL channels for category: {category}")
        
        # Get ALL channels from background service
        result = background_service.get_live_channels(region="all")
        
        # Check if category exists
        all_channels = background_service.all_channels
        if category not in all_channels:
            raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
        
        # Filter channels by category
        category_channels = [ch for ch in result["all"] if ch.get("category") == category]
        live_in_category = [ch for ch in category_channels if ch.get("is_live", False)]
        offline_in_category = [ch for ch in category_channels if not ch.get("is_live", False)]
        
        return {
            "category": category,
            "total_channels": len(category_channels),
            "live_channels": len(live_in_category),
            "offline_channels": len(offline_in_category),
            "all": category_channels,  # ALL channels in category
            "live": live_in_category,
            "offline": offline_in_category,
            "last_updated": datetime.utcnow().isoformat(),
            "api_source": "background_service_comprehensive",
            "thumbnail_quality": "real_youtube_thumbnails"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting category channels: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get category channels: {str(e)}")

@router.get("/all-categories", summary="Get all channel categories")
async def get_all_categories():
    """Get all available channel categories with counts"""
    try:
        all_channels = background_service.all_channels
        
        categories = {}
        total_channels = 0
        
        for category_name, channels in all_channels.items():
            # Get live channels in this category
            live_result = background_service.get_live_channels(region="all")
            live_in_category = 0
            
            for live_channel in live_result["live"]:
                for channel in channels:
                    if live_channel["name"].lower() == channel["name"].lower():
                        live_in_category += 1
                        break
            
            categories[category_name] = {
                "name": category_name,
                "total_channels": len(channels),
                "live_channels": live_in_category,
                "offline_channels": len(channels) - live_in_category,
                "channels": channels
            }
            total_channels += len(channels)
        
        return {
            "categories": categories,
            "total_categories": len(all_channels),
            "total_channels": total_channels,
            "total_live_channels": sum(cat["live_channels"] for cat in categories.values()),
            "last_updated": datetime.utcnow().isoformat(),
            "api_source": "background_service_comprehensive"
        }
        
    except Exception as e:
        print(f"Error getting all categories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@router.get("/check-channel/{channel_name}/{channel_id}", summary="Check specific channel live status")
async def check_specific_channel_status(channel_name: str, channel_id: str):
    """Check live status for a specific channel using YouTube Data API"""
    try:
        print(f"🔍 API Request: Checking live status for {channel_name}...")
        
        # Use background service to check specific channel
        live_streams = await background_service.check_specific_channel_live_status(channel_name, channel_id)
        
        if live_streams:
            # Channel is LIVE
            first_stream = live_streams[0]
            video_id = first_stream["id"]["videoId"]
            snippet = first_stream["snippet"]
            title = snippet.get("title", "")
            thumbnail = snippet.get("thumbnails", {}).get("high", {}).get("url", "")
            
            return {
                "channel_name": channel_name,
                "channel_id": channel_id,
                "status": "LIVE",
                "live_streams_count": len(live_streams),
                "live_streams": [
                    {
                        "video_id": stream["id"]["videoId"],
                        "title": stream["snippet"].get("title", ""),
                        "description": stream["snippet"].get("description", "")[:200],
                        "thumbnail": stream["snippet"].get("thumbnails", {}).get("high", {}).get("url", ""),
                        "published_at": stream["snippet"].get("publishedAt", ""),
                        "youtube_url": f"https://www.youtube.com/watch?v={stream['id']['videoId']}",
                        "embed_url": f"https://www.youtube.com/embed/{stream['id']['videoId']}"
                    }
                    for stream in live_streams
                ],
                "api_source": "youtube_data_api",
                "last_checked": datetime.utcnow().isoformat()
            }
        else:
            # Channel is OFFLINE
            return {
                "channel_name": channel_name,
                "channel_id": channel_id,
                "status": "OFFLINE",
                "live_streams_count": 0,
                "live_streams": [],
                "message": "No live streams found",
                "api_source": "youtube_data_api",
                "last_checked": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        print(f"❌ Error checking channel {channel_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check channel status: {str(e)}")

@router.get("/check-all-channels-live", summary="Check live status for all channels")
async def check_all_channels_live_status():
    """Check live status for all 80+ channels using YouTube Data API"""
    try:
        print("🔍 API Request: Checking live status for ALL channels...")
        
        # Trigger live status check for all channels
        await background_service.scrape_youtube_live_data()
        
        # Get updated results
        result = background_service.get_live_channels(region="all")
        
        return {
            "message": "Live status check completed for all channels",
            "total_channels": result["total_channels"],
            "live_channels": result["live_channels"],
            "offline_channels": result["offline_channels"],
            "live_channels_list": [
                {
                    "name": ch["name"],
                    "video_id": ch["video_id"],
                    "title": ch["title"],
                    "youtube_url": ch["stream_url"],
                    "embed_url": ch["embed_url"],
                    "thumbnail": ch["thumbnail"],
                    "live_viewers": ch["live_viewers"],
                    "started_at": ch["started_at"]
                }
                for ch in result["live"]
            ],
            "api_source": "youtube_data_api",
            "last_checked": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error checking all channels: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check all channels: {str(e)}")

@router.get("/india", summary="Get all Indian news channels")
async def get_india_channels():
    """Get all Indian news channels with live status"""
    try:
        india_channels = await youtube_detector.get_india_channels()
        
        return {
            "region": "india",
            "channels": india_channels,
            "total": india_channels["total"],
            "general_news_count": len(india_channels["general_news"]),
            "finance_news_count": len(india_channels["finance_news"]),
            "live_count": len([ch for cat in india_channels.values() if isinstance(cat, list) for ch in cat if ch.get("is_live", False)]),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Error getting India channels: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get India channels: {str(e)}")

@router.get("/india/general-news", summary="Get Indian general news channels")
async def get_india_general_news():
    """Get Indian general news channels"""
    try:
        channels = await youtube_detector.get_channels_by_region_and_category("india", "general_news")
        
        return {
            "region": "india",
            "category": "general_news",
            "channels": channels,
            "total": len(channels),
            "live_count": len([ch for ch in channels if ch.get("is_live", False)]),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Error getting India general news: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get India general news: {str(e)}")

@router.get("/india/finance-news", summary="Get Indian finance news channels")
async def get_india_finance_news():
    """Get Indian finance news channels"""
    try:
        channels = await youtube_detector.get_channels_by_region_and_category("india", "finance_news")
        
        return {
            "region": "india",
            "category": "finance_news",
            "channels": channels,
            "total": len(channels),
            "live_count": len([ch for ch in channels if ch.get("is_live", False)]),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Error getting India finance news: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get India finance news: {str(e)}")

@router.get("/global", summary="Get all global news channels")
async def get_global_channels():
    """Get all global news channels with live status"""
    try:
        global_channels = await youtube_detector.get_global_channels()
        
        return {
            "region": "global",
            "channels": global_channels,
            "total": global_channels["total"],
            "general_news_count": len(global_channels["general_news"]),
            "finance_news_count": len(global_channels["finance_news"]),
            "live_count": len([ch for cat in global_channels.values() if isinstance(cat, list) for ch in cat if ch.get("is_live", False)]),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Error getting global channels: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get global channels: {str(e)}")

@router.get("/global/general-news", summary="Get global general news channels")
async def get_global_general_news():
    """Get global general news channels"""
    try:
        channels = await youtube_detector.get_channels_by_region_and_category("global", "general_news")
        
        return {
            "region": "global",
            "category": "general_news",
            "channels": channels,
            "total": len(channels),
            "live_count": len([ch for ch in channels if ch.get("is_live", False)]),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Error getting global general news: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get global general news: {str(e)}")

@router.get("/global/finance-news", summary="Get global finance news channels")
async def get_global_finance_news():
    """Get global finance news channels"""
    try:
        channels = await youtube_detector.get_channels_by_region_and_category("global", "finance_news")
        
        return {
            "region": "global",
            "category": "finance_news",
            "channels": channels,
            "total": len(channels),
            "live_count": len([ch for ch in channels if ch.get("is_live", False)]),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Error getting global finance news: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get global finance news: {str(e)}")

@router.get("/live-only", summary="Get only channels that are currently live")
async def get_live_channels_only():
    """Get only channels that are currently streaming live"""
    try:
        live_channels = await youtube_detector.get_live_channels_only()
        
        # Group live channels by region
        india_live = [ch for ch in live_channels if ch.get("region") == "india"]
        global_live = [ch for ch in live_channels if ch.get("region") == "global"]
        
        return {
            "live_channels": live_channels,
            "total": len(live_channels),
            "india_live": len(india_live),
            "global_live": len(global_live),
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
            # Take top 5 live news channels
            war_streams = all_live[:5]
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

@router.get("/featured", summary="Get featured live news channels")
async def get_featured_live_channels():
    """Get top featured live news channels"""
    try:
        # Get top channels from each region and category
        india_general = await youtube_detector.get_channels_by_region_and_category("india", "general_news")
        india_finance = await youtube_detector.get_channels_by_region_and_category("india", "finance_news")
        global_general = await youtube_detector.get_channels_by_region_and_category("global", "general_news")
        global_finance = await youtube_detector.get_channels_by_region_and_category("global", "finance_news")
        
        # Take top 2 from each category
        featured = []
        featured.extend(india_general[:2])
        featured.extend(india_finance[:1])
        featured.extend(global_general[:2])
        featured.extend(global_finance[:1])
        
        # Sort by live status
        featured.sort(key=lambda x: (not x.get("is_live", False), x["name"]))
        
        return {
            "featured": featured,
            "total": len(featured),
            "live_count": len([ch for ch in featured if ch.get("is_live", False)]),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Error getting featured channels: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get featured channels: {str(e)}")

@router.get("/directory", summary="Get complete channel directory")
async def get_channel_directory():
    """Get complete directory of all channels with current live status"""
    try:
        all_channels = await youtube_detector.check_all_channels_live_status()
        
        # Group by region and category
        india_general = [ch for ch in all_channels if ch.get("region") == "india" and ch.get("category") == "general_news"]
        india_finance = [ch for ch in all_channels if ch.get("region") == "india" and ch.get("category") == "finance_news"]
        global_general = [ch for ch in all_channels if ch.get("region") == "global" and ch.get("category") == "general_news"]
        global_finance = [ch for ch in all_channels if ch.get("region") == "global" and ch.get("category") == "finance_news"]
        
        return {
            "regions": {
                "india": {
                    "general_news": india_general,
                    "finance_news": india_finance,
                    "total": len(india_general) + len(india_finance)
                },
                "global": {
                    "general_news": global_general,
                    "finance_news": global_finance,
                    "total": len(global_general) + len(global_finance)
                }
            },
            "categories": {
                "general_news": india_general + global_general,
                "finance_news": india_finance + global_finance
            },
            "total_channels": len(all_channels),
            "live_channels": len([ch for ch in all_channels if ch.get("is_live", False)]),
            "india_channels": len(india_general) + len(india_finance),
            "global_channels": len(global_general) + len(global_finance),
            "last_updated": datetime.utcnow().isoformat(),
            "api_source": "youtube_data_api_enhanced"
        }
        
    except Exception as e:
        print(f"Error getting directory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get directory: {str(e)}")

@router.get("/health", summary="Health check for enhanced YouTube API integration")
async def health_check():
    """Health check for enhanced YouTube Data API integration"""
    try:
        # Test API by checking one channel from each region
        india_test = await youtube_detector.check_channel_live_status("aaj_tak")
        global_test = await youtube_detector.check_channel_live_status("bbc_news")
        
        total_configured = len(youtube_detector.channel_mappings)
        india_configured = len([ch for ch in youtube_detector.channel_mappings.values() if ch.get("region") == "india"])
        global_configured = len([ch for ch in youtube_detector.channel_mappings.values() if ch.get("region") == "global"])
        
        return {
            "status": "healthy",
            "youtube_api_working": True,
            "total_configured": total_configured,
            "india_configured": india_configured,
            "global_configured": global_configured,
            "test_channels": {
                "india": india_test.get("name", "Unknown"),
                "global": global_test.get("name", "Unknown")
            },
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
