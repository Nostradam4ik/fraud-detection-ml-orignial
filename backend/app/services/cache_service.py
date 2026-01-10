"""
Cache Service - Redis caching for performance

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

import json
import logging
from typing import Any, Optional
from datetime import timedelta
from functools import wraps

from ..core.config import settings

logger = logging.getLogger(__name__)

# Try to import redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not installed. Caching will be disabled.")


class CacheService:
    """Redis cache service with fallback to no-op when Redis is unavailable"""

    def __init__(self):
        self.client = None
        self.enabled = False
        self._connect()

    def _connect(self):
        """Connect to Redis if available and enabled"""
        if not REDIS_AVAILABLE:
            logger.info("Redis not available - caching disabled")
            return

        if not settings.redis_enabled:
            logger.info("Redis caching disabled in settings")
            return

        try:
            self.client = redis.from_url(
                settings.redis_url,
                decode_responses=True
            )
            # Test connection
            self.client.ping()
            self.enabled = True
            logger.info(f"Connected to Redis at {settings.redis_url}")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
            self.client = None
            self.enabled = False

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache"""
        if not self.enabled:
            return None

        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set a value in cache with TTL in seconds"""
        if not self.enabled:
            return False

        try:
            self.client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        if not self.enabled:
            return False

        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.enabled:
            return 0

        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0

    def get_or_set(self, key: str, getter, ttl: int = 300) -> Any:
        """Get from cache or compute and cache the value"""
        cached = self.get(key)
        if cached is not None:
            return cached

        value = getter()
        self.set(key, value, ttl)
        return value

    def incr(self, key: str, amount: int = 1) -> int:
        """Increment a counter"""
        if not self.enabled:
            return 0

        try:
            return self.client.incr(key, amount)
        except Exception as e:
            logger.error(f"Cache incr error for key {key}: {e}")
            return 0

    def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.enabled:
            return {"enabled": False}

        try:
            info = self.client.info()
            return {
                "enabled": True,
                "connected": True,
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_keys": self.client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            return {"enabled": True, "connected": False, "error": str(e)}


# Global cache instance
cache = CacheService()


def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Cache the result
            cache.set(cache_key, result, ttl)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}{func.__name__}:{hash(str(args) + str(kwargs))}"

            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)

            return result

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Cache key generators
def user_cache_key(user_id: int, suffix: str) -> str:
    """Generate cache key for user-specific data"""
    return f"user:{user_id}:{suffix}"


def prediction_cache_key(prediction_id: int) -> str:
    """Generate cache key for prediction data"""
    return f"prediction:{prediction_id}"


def model_cache_key(version: str) -> str:
    """Generate cache key for model data"""
    return f"model:{version}"


def stats_cache_key(stat_type: str) -> str:
    """Generate cache key for statistics"""
    return f"stats:{stat_type}"
