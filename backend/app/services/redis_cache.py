"""
Redis Caching Layer for AARAMBH
================================
Provides caching for API responses, market data, news, and computed results.
"""

import redis
import json
import os
from typing import Optional, Any, Dict, List
from datetime import datetime
import hashlib

# Redis configuration
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
REDIS_ENABLED = False

# Cache TTLs (in seconds)
CACHE_TTL = {
    "stock_quote": 60,           # 1 minute for live quotes
    "stock_chart": 300,          # 5 minutes for charts
    "stock_financials": 3600,    # 1 hour for financials
    "market_indices": 120,       # 2 minutes for indices
    "market_movers": 120,        # 2 minutes for movers
    "crypto": 60,                # 1 minute for crypto
    "forex": 120,                # 2 minutes for forex
    "news_headlines": 300,       # 5 minutes for news
    "news_search": 600,          # 10 minutes for search results
    "economic_calendar": 1800,   # 30 minutes for calendar
    "world_bank": 86400,         # 24 hours for WB data
    "imf": 86400,                # 24 hours for IMF data
    "fred": 86400,               # 24 hours for FRED data
    "earnings": 3600,            # 1 hour for earnings
    "ipo": 3600,                 # 1 hour for IPO
    "pib": 1800,                 # 30 minutes for PIB
    "trending": 300,             # 5 minutes for trending
    "geopolitical": 600,         # 10 minutes for geo news
    "default": 300,              # 5 minutes default
}


class RedisCache:
    """Redis caching manager"""
    
    _client: Optional[redis.Redis] = None
    _connected: bool = False
    
    @classmethod
    def get_client(cls) -> Optional[redis.Redis]:
        """Get Redis client with connection check"""
        if not REDIS_ENABLED:
            return None
            
        if cls._client is None:
            try:
                cls._client = redis.from_url(REDIS_URL, decode_responses=True)
                cls._client.ping()
                cls._connected = True
            except Exception as e:
                print(f"Redis connection failed: {e}")
                cls._connected = False
                return None
        return cls._client
    
    @classmethod
    def is_connected(cls) -> bool:
        """Check if Redis is connected"""
        return cls._connected and cls.get_client() is not None
    
    @classmethod
    def _make_key(cls, category: str, identifier: str) -> str:
        """Create a cache key"""
        return f"aarambh:{category}:{identifier}"
    
    @classmethod
    def _hash_key(cls, data: Any) -> str:
        """Create hash for complex data"""
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
    
    @classmethod
    def get(cls, category: str, identifier: str) -> Optional[Any]:
        """Get cached data"""
        client = cls.get_client()
        if not client:
            return None
        
        try:
            key = cls._make_key(category, identifier)
            data = client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            print(f"Cache get error: {e}")
        return None
    
    @classmethod
    def set(cls, category: str, identifier: str, data: Any, ttl: int = None) -> bool:
        """Set cached data"""
        client = cls.get_client()
        if not client:
            return False
        
        try:
            key = cls._make_key(category, identifier)
            ttl = ttl or CACHE_TTL.get(category, CACHE_TTL["default"])
            
            # Add timestamp
            if isinstance(data, dict):
                data["_cached_at"] = datetime.utcnow().isoformat()
            
            client.setex(key, ttl, json.dumps(data, default=str))
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    @classmethod
    def delete(cls, category: str, identifier: str) -> bool:
        """Delete cached data"""
        client = cls.get_client()
        if not client:
            return False
        
        try:
            key = cls._make_key(category, identifier)
            client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    @classmethod
    def delete_pattern(cls, pattern: str) -> int:
        """Delete all keys matching pattern"""
        client = cls.get_client()
        if not client:
            return 0
        
        try:
            keys = client.keys(f"aarambh:{pattern}*")
            if keys:
                return client.delete(*keys)
        except Exception as e:
            print(f"Cache delete pattern error: {e}")
        return 0
    
    @classmethod
    def clear_category(cls, category: str) -> int:
        """Clear all cached data for a category"""
        return cls.delete_pattern(category)
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Get cache statistics"""
        client = cls.get_client()
        if not client:
            return {"connected": False, "enabled": REDIS_ENABLED}
        
        try:
            info = client.info()
            keys = client.keys("aarambh:*")
            return {
                "connected": True,
                "enabled": REDIS_ENABLED,
                "total_keys": len(keys),
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}
    
    @classmethod
    def get_or_set(cls, category: str, identifier: str, 
                   fetch_func: callable, ttl: int = None) -> Any:
        """Get from cache or fetch and cache"""
        # Try cache first
        cached = cls.get(category, identifier)
        if cached is not None:
            return cached
        
        # Fetch fresh data
        import asyncio
        try:
            if asyncio.iscoroutinefunction(fetch_func):
                data = asyncio.run(fetch_func())
            else:
                data = fetch_func()
        except Exception as e:
            print(f"Fetch function error: {e}")
            return None
        
        # Cache the result
        if data is not None:
            cls.set(category, identifier, data, ttl)
        
        return data


# Convenience functions
def cache_get(category: str, identifier: str) -> Optional[Any]:
    """Get from cache"""
    return RedisCache.get(category, identifier)


def cache_set(category: str, identifier: str, data: Any, ttl: int = None) -> bool:
    """Set in cache"""
    return RedisCache.set(category, identifier, data, ttl)


def cache_delete(category: str, identifier: str) -> bool:
    """Delete from cache"""
    return RedisCache.delete(category, identifier)


def cache_stats() -> Dict[str, Any]:
    """Get cache stats"""
    return RedisCache.get_stats()


def cached_response(category: str, identifier: str, ttl: int = None):
    """Decorator for caching function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Try cache first
            cached = RedisCache.get(category, identifier)
            if cached is not None:
                return cached
            
            # Call function
            result = func(*args, **kwargs)
            
            # Cache result
            if result is not None:
                RedisCache.set(category, identifier, result, ttl)
            
            return result
        return wrapper
    return decorator


# Export
__all__ = [
    "RedisCache", "cache_get", "cache_set", "cache_delete", 
    "cache_stats", "cached_response", "CACHE_TTL"
]
