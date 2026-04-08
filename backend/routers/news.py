"""routers/news.py"""
from fastapi import APIRouter, Query, Path, HTTPException, BackgroundTasks
from typing import Optional, List
from datetime import datetime
from scrapers.rss_scraper import (
    fetch_source, get_headlines, search_all, get_by_category,
    get_by_country, get_finance_news, get_trending_topics, SOURCES,
    COUNTRY_SOURCES, CATEGORY_SOURCES
)
from database import db, NewsArticle
from enhanced_scraper import enhanced_scraper

router = APIRouter()

@router.get("/headlines", summary="Top headlines from all major sources (with pagination and thumbnails)")
async def headlines(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=50, description="Articles per page"),
    country: Optional[str] = Query(None, description="Filter by country code"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Get headlines with pagination support, thumbnails, and background loading"""
    offset = (page - 1) * limit
    
    # Try to get from database first
    try:
        articles = await db.get_headlines(limit=limit, offset=offset, country=country)
        total = await db.get_article_count()
        
        if articles:
            # Trigger background refresh for older articles
            if page == 1:
                background_tasks.add_task(refresh_headlines_background)
            
            return {
                "articles": [
                    {
                        "id": article.id,
                        "title": article.title,
                        "summary": article.summary,
                        "source": article.source,
                        "url": article.url,
                        "category": article.category,
                        "country": article.country,
                        "published": article.published_at.isoformat(),
                        "thumbnail_url": article.thumbnail_url,
                        "image_url": article.image_url,
                        "ai_sentiment": article.ai_sentiment,
                        "ai_categories": article.ai_categories,
                        "ai_processed": article.ai_processed
                    } for article in articles
                ],
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit
                },
                "cache_status": "database"
            }
    except Exception as e:
        print(f"Database error: {e}")
    
    # Fallback to enhanced scraper with thumbnails
    try:
        if country:
            scraped_articles = await enhanced_scraper.get_location_based_news(country, limit)
        else:
            scraped_articles = await enhanced_scraper.get_featured_news(limit)
        
        # Store in database
        stored_articles = []
        for article in scraped_articles:
            try:
                stored_article = await db.create_article({
                    "title": article.get("title"),
                    "summary": article.get("summary", ""),
                    "source": article.get("source", "Unknown"),
                    "url": article.get("url", ""),
                    "category": article.get("category", "general"),
                    "country": article.get("country"),
                    "published_at": article.get("published_at", datetime.utcnow()),
                    "thumbnail_url": article.get("thumbnail_url"),
                    "image_url": article.get("image_url"),
                })
                stored_articles.append(stored_article)
            except Exception as e:
                print(f"Error storing article: {e}")
        
        return {
            "articles": [
                {
                    "id": article.id,
                    "title": article.title,
                    "summary": article.summary,
                    "source": article.source,
                    "url": article.url,
                    "category": article.category,
                    "country": article.country,
                    "published": article.published_at.isoformat(),
                    "thumbnail_url": article.thumbnail_url,
                    "image_url": article.image_url,
                    "ai_sentiment": article.ai_sentiment,
                    "ai_categories": article.ai_categories,
                    "ai_processed": article.ai_processed
                } for article in stored_articles
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(stored_articles),
                "pages": 1
            },
            "cache_status": "scraper"
        }
        
    except Exception as e:
        print(f"Scraper error: {e}")
        return {"articles": [], "pagination": {"page": page, "limit": limit, "total": 0, "pages": 0}}

@router.get("/featured", summary="Get featured news with thumbnails (top stories)")
async def featured_news(limit: int = Query(10, ge=1, le=20, description="Number of featured articles")):
    """Get featured/top stories with thumbnail images"""
    try:
        featured_articles = await enhanced_scraper.get_featured_news(limit)
        
        return {
            "featured": [
                {
                    "title": article.get("title"),
                    "summary": article.get("summary", ""),
                    "source": article.get("source", "Unknown"),
                    "url": article.get("url", ""),
                    "thumbnail_url": article.get("thumbnail_url"),
                    "image_url": article.get("image_url"),
                    "published": article.get("published_at", datetime.utcnow()).isoformat(),
                    "category": article.get("category", "general")
                } for article in featured_articles
            ],
            "total": len(featured_articles)
        }
    except Exception as e:
        print(f"Error fetching featured news: {e}")
        return {"featured": [], "total": 0}

@router.get("/location/{country_code}", summary="Get news based on location/country")
async def location_news(
    country_code: str = Path(..., description="Country code (IN, US, GB, etc.)"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50)
):
    """Get news based on user location"""
    offset = (page - 1) * limit
    
    try:
        location_articles = await enhanced_scraper.get_location_based_news(country_code, limit)
        
        return {
            "articles": [
                {
                    "title": article.get("title"),
                    "summary": article.get("summary", ""),
                    "source": article.get("source", "Unknown"),
                    "url": article.get("url", ""),
                    "thumbnail_url": article.get("thumbnail_url"),
                    "image_url": article.get("image_url"),
                    "published": article.get("published_at", datetime.utcnow()).isoformat(),
                    "category": article.get("category", "general"),
                    "country": country_code.upper()
                } for article in location_articles
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(location_articles),
                "pages": (len(location_articles) + limit - 1) // limit
            },
            "location": country_code.upper()
        }
    except Exception as e:
        print(f"Error fetching location news: {e}")
        return {"articles": [], "pagination": {"page": page, "limit": limit, "total": 0, "pages": 0}}

@router.get("/category/{category}", summary="News by category (with pagination)")
async def by_category(
    category: str = Path(..., description="finance|world|health|geopolitical|technology|science|sports|india"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=50, description="Articles per page"),
    country: Optional[str] = Query(None, description="Filter by country code")
):
    """Get news by category with pagination support"""
    offset = (page - 1) * limit
    
    # Try to get from database first
    try:
        articles = await db.get_articles_by_category(category, limit=limit, offset=offset, country=country)
        total = await db.get_article_count(category)
        
        if articles:
            return {
                "articles": [
                    {
                        "id": article.id,
                        "title": article.title,
                        "summary": article.summary,
                        "source": article.source,
                        "url": article.url,
                        "category": article.category,
                        "country": article.country,
                        "published": article.published_at.isoformat(),
                        "thumbnail_url": article.thumbnail_url,
                        "image_url": article.image_url,
                        "ai_sentiment": article.ai_sentiment,
                        "ai_categories": article.ai_categories,
                        "ai_processed": article.ai_processed
                    } for article in articles
                ],
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit
                }
            }
    except Exception as e:
        print(f"Database error: {e}")
    
    # Fallback to scraper
    try:
        scraped_data = await get_by_category(category, limit)
        
        # Store in database
        for article in scraped_data.get("articles", []):
            try:
                await db.create_article({
                    "title": article.get("title"),
                    "summary": article.get("summary", article.get("description", "")),
                    "source": article.get("source", article.get("publisher", "Unknown")),
                    "url": article.get("url", article.get("link", "")),
                    "category": category,
                    "country": article.get("country"),
                    "published_at": datetime.fromisoformat(article.get("published", datetime.utcnow().isoformat())),
                })
            except Exception as e:
                print(f"Error storing article: {e}")
        
        return {
            "articles": scraped_data.get("articles", []),
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(scraped_data.get("articles", [])),
                "pages": 1
            }
        }
    except Exception as e:
        print(f"Scraper error: {e}")
        return {"articles": [], "pagination": {"page": page, "limit": limit, "total": 0, "pages": 0}}

@router.get("/search", summary="Search across all 50+ news sources")
async def search(
    q:     str = Query(..., description="Search query"),
    count: int = Query(30),
):
    return await search_all(q, count)

@router.get("/country/{country}", summary="News by country code")
async def by_country(
    country: str = Path(..., description="IN|US|GB|CA|AU|DE|FR|JP|CN|RU|BR|ZA"),
    count:   int = Query(40),
):
    return await get_by_country(country, count)

@router.get("/source/{source_key}", summary="Single source feed")
async def single_source(
    source_key: str = Path(..., description="Source key e.g. bloomberg_markets, et_markets"),
    count:      int = Query(20),
):
    return await fetch_source(source_key, count)

@router.get("/finance", summary="Finance & markets news aggregated")
async def finance(count: int = Query(50)):
    return await get_finance_news(count)

@router.get("/trending", summary="Trending topics across all sources")
async def trending():
    return await get_trending_topics()

@router.get("/aggregate", summary="Aggregate specific sources")
async def aggregate(
    sources: str = Query(..., description="Comma-separated source keys"),
    count:   int = Query(40),
):
    from scrapers.rss_scraper import fetch_multiple
    keys = [s.strip() for s in sources.split(",")]
    arts = await fetch_multiple(keys, max_total=count)
    return {"sources": keys, "count": len(arts), "articles": arts}

@router.get("/sources", summary="List all 50+ available sources")
async def list_sources():
    return {
        "total": len(SOURCES),
        "sources": {k: {"name": v["name"], "country": v["country"], "category": v["category"]}
                    for k, v in SOURCES.items()},
        "countries": list(COUNTRY_SOURCES.keys()),
        "categories": list(CATEGORY_SOURCES.keys()),
    }

# Background task for refreshing headlines
async def refresh_headlines_background():
    """Background task to refresh headlines without blocking the response"""
    try:
        print("🔄 Background refresh started...")
        featured_articles = await enhanced_scraper.get_featured_news(20)
        
        stored_count = 0
        for article in featured_articles:
            try:
                await db.create_article({
                    "title": article.get("title"),
                    "summary": article.get("summary", ""),
                    "source": article.get("source", "Unknown"),
                    "url": article.get("url", ""),
                    "category": article.get("category", "general"),
                    "country": article.get("country"),
                    "published_at": article.get("published_at", datetime.utcnow()),
                    "thumbnail_url": article.get("thumbnail_url"),
                    "image_url": article.get("image_url"),
                })
                stored_count += 1
            except Exception as e:
                print(f"Background storage error: {e}")
        
        print(f"✅ Background refresh completed. Stored {stored_count} articles.")
    except Exception as e:
        print(f"❌ Background refresh failed: {e}")
