"""
Social Feeds Router — Free social media data aggregation
Fetches trending economic discussions from Reddit (public JSON API)
and world leader commentary from news feeds.
"""

import httpx
import asyncio
from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime

router = APIRouter()

# ── Reddit Public API (no auth needed) ─────────────────────
REDDIT_SUBS = [
    "economics", "finance", "wallstreetbets", "stocks",
    "IndianStreetBets", "IndiaInvestments", "worldnews"
]

@router.get("/reddit/trending",
    summary="Trending economic discussions from Reddit",
    description="Fetches top posts from finance/economics subreddits using Reddit's public JSON API (no API key required).")
async def get_reddit_trending(
    subreddit: str = Query("economics", description="Subreddit name"),
    sort: str = Query("hot", description="Sort: hot, top, new, rising"),
    limit: int = Query(15, description="Number of posts (max 25)")
):
    limit = min(limit, 25)
    url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit={limit}"
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers={
                "User-Agent": "AARAMBH-EconDashboard/1.0"
            })
            resp.raise_for_status()
            data = resp.json()
        
        posts = []
        for child in data.get("data", {}).get("children", []):
            d = child.get("data", {})
            posts.append({
                "title": d.get("title", ""),
                "author": d.get("author", "[deleted]"),
                "subreddit": d.get("subreddit", subreddit),
                "score": d.get("score", 0),
                "num_comments": d.get("num_comments", 0),
                "url": f"https://reddit.com{d.get('permalink', '')}",
                "created_utc": d.get("created_utc"),
                "selftext": (d.get("selftext", "") or "")[:300],
                "thumbnail": d.get("thumbnail") if d.get("thumbnail", "").startswith("http") else None,
                "is_pinned": d.get("stickied", False),
                "upvote_ratio": d.get("upvote_ratio", 0),
                "flair": d.get("link_flair_text"),
            })
        
        return {
            "subreddit": subreddit,
            "sort": sort,
            "count": len(posts),
            "posts": posts,
            "fetched_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "subreddit": subreddit,
            "sort": sort,
            "count": 0,
            "posts": [],
            "error": str(e),
            "fetched_at": datetime.utcnow().isoformat()
        }


@router.get("/reddit/multi",
    summary="Trending posts from multiple finance subreddits",
    description="Aggregates top posts from economics, finance, wallstreetbets, stocks, IndianStreetBets, etc.")
async def get_reddit_multi(
    limit: int = Query(5, description="Posts per subreddit"),
    sort: str = Query("hot", description="Sort order")
):
    limit = min(limit, 10)
    
    async def fetch_sub(sub: str):
        url = f"https://www.reddit.com/r/{sub}/{sort}.json?limit={limit}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers={
                    "User-Agent": "AARAMBH-EconDashboard/1.0"
                })
                resp.raise_for_status()
                data = resp.json()
            
            posts = []
            for child in data.get("data", {}).get("children", []):
                d = child.get("data", {})
                posts.append({
                    "title": d.get("title", ""),
                    "author": d.get("author", "[deleted]"),
                    "subreddit": sub,
                    "score": d.get("score", 0),
                    "num_comments": d.get("num_comments", 0),
                    "url": f"https://reddit.com{d.get('permalink', '')}",
                    "selftext": (d.get("selftext", "") or "")[:200],
                    "flair": d.get("link_flair_text"),
                })
            return posts
        except:
            return []
    
    tasks = [fetch_sub(sub) for sub in REDDIT_SUBS]
    results = await asyncio.gather(*tasks)
    
    all_posts = []
    for posts in results:
        all_posts.extend(posts)
    
    # Sort by score
    all_posts.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    return {
        "subreddits": REDDIT_SUBS,
        "total_posts": len(all_posts),
        "posts": all_posts[:30],
        "fetched_at": datetime.utcnow().isoformat()
    }


@router.get("/reddit/subreddits",
    summary="Available finance/economics subreddits")
async def get_available_subreddits():
    return {
        "subreddits": [
            {"name": "economics", "description": "Academic and news-driven economics discussion"},
            {"name": "finance", "description": "General finance and market discussion"},
            {"name": "wallstreetbets", "description": "Retail investor sentiment and memes"},
            {"name": "stocks", "description": "Stock market analysis and picks"},
            {"name": "IndianStreetBets", "description": "Indian retail investor community"},
            {"name": "IndiaInvestments", "description": "Indian long-term investment discussion"},
            {"name": "worldnews", "description": "Global news with economic impact"},
        ]
    }


# ── World Leader & Corporate Commentary ────────────────────

@router.get("/world-leaders",
    summary="Recent commentary from world leaders on economy",
    description="Aggregates public statements from heads of state and central bank governors via news APIs.")
async def get_world_leader_commentary(
    limit: int = Query(10, description="Number of items")
):
    # Using Reddit worldnews as a free proxy for world leader statements
    url = f"https://www.reddit.com/r/worldnews/search.json?q=economy+OR+GDP+OR+inflation+OR+trade&sort=new&limit={min(limit, 20)}&restrict_sr=true"
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers={
                "User-Agent": "AARAMBH-EconDashboard/1.0"
            })
            resp.raise_for_status()
            data = resp.json()
        
        items = []
        for child in data.get("data", {}).get("children", []):
            d = child.get("data", {})
            items.append({
                "headline": d.get("title", ""),
                "source": d.get("domain", "reddit.com"),
                "url": d.get("url", ""),
                "reddit_url": f"https://reddit.com{d.get('permalink', '')}",
                "score": d.get("score", 0),
                "comments": d.get("num_comments", 0),
                "posted": d.get("created_utc"),
            })
        
        return {
            "count": len(items),
            "items": items,
            "fetched_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"count": 0, "items": [], "error": str(e)}


@router.get("/corporate",
    summary="Corporate economic commentary and earnings news",
    description="Trending corporate finance news from Reddit finance communities.")
async def get_corporate_commentary(
    limit: int = Query(10, description="Number of items")
):
    url = f"https://www.reddit.com/r/stocks/search.json?q=earnings+OR+CEO+OR+quarterly&sort=new&limit={min(limit, 20)}&restrict_sr=true"
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers={
                "User-Agent": "AARAMBH-EconDashboard/1.0"
            })
            resp.raise_for_status()
            data = resp.json()
        
        items = []
        for child in data.get("data", {}).get("children", []):
            d = child.get("data", {})
            items.append({
                "headline": d.get("title", ""),
                "source": d.get("domain", "reddit.com"),
                "url": d.get("url", ""),
                "score": d.get("score", 0),
                "comments": d.get("num_comments", 0),
                "flair": d.get("link_flair_text"),
                "posted": d.get("created_utc"),
            })
        
        return {
            "count": len(items),
            "items": items,
            "fetched_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"count": 0, "items": [], "error": str(e)}
