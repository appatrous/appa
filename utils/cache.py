"""
Caching utilities using Redis.
Provides decorators and utilities for caching expensive operations.
"""
import functools
import json
import hashlib
from typing import Any, Callable, Optional
import pickle


class CacheManager:
    """
    Cache manager using Redis or in-memory fallback.
    Supports multiple cache backends and automatic serialization.
    """

    def __init__(self, app=None):
        """
        Initialize cache manager.

        Args:
            app: Flask application instance
        """
        self.app = app
        self.redis_client = None
        self._memory_cache = {}

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Initialize Flask application with caching.

        Args:
            app: Flask application instance
        """
        self.app = app

        # Get cache configuration
        cache_type = app.config.get('CACHE_TYPE', 'redis')
        redis_url = app.config.get('CACHE_REDIS_URL', 'redis://localhost:6379/0')

        if cache_type == 'redis':
            try:
                import redis
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=False,  # We'll handle encoding ourselves
                    socket_connect_timeout=2
                )
                # Test connection
                self.redis_client.ping()
                app.logger.info(f"Redis cache connected: {redis_url}")
            except Exception as e:
                app.logger.warning(f"Redis connection failed, using memory cache: {e}")
                self.redis_client = None
                cache_type = 'memory'

        app.config['CACHE_TYPE_ACTIVE'] = cache_type

    def _make_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from function arguments.

        Args:
            prefix: Key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Cache key string
        """
        # Create a stable representation of arguments
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True)

        # Hash for shorter keys
        key_hash = hashlib.md5(key_str.encode()).hexdigest()

        return f"{prefix}:{key_hash}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value is not None:
                    return pickle.loads(value)
            except Exception as e:
                if self.app:
                    self.app.logger.error(f"Cache get error: {e}")
                return None
        else:
            return self._memory_cache.get(key)

        return None

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            timeout: Expiration time in seconds

        Returns:
            True if successful, False otherwise
        """
        if self.redis_client:
            try:
                pickled_value = pickle.dumps(value)
                if timeout:
                    return self.redis_client.setex(key, timeout, pickled_value)
                else:
                    return self.redis_client.set(key, pickled_value)
            except Exception as e:
                if self.app:
                    self.app.logger.error(f"Cache set error: {e}")
                return False
        else:
            self._memory_cache[key] = value
            # TODO: Implement timeout for memory cache
            return True

    def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        if self.redis_client:
            try:
                return bool(self.redis_client.delete(key))
            except Exception as e:
                if self.app:
                    self.app.logger.error(f"Cache delete error: {e}")
                return False
        else:
            if key in self._memory_cache:
                del self._memory_cache[key]
                return True
            return False

    def clear(self, pattern: Optional[str] = None) -> int:
        """
        Clear cache entries.

        Args:
            pattern: Redis key pattern (e.g., 'config:*'). If None, clears all.

        Returns:
            Number of keys deleted
        """
        if self.redis_client:
            try:
                if pattern:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        return self.redis_client.delete(*keys)
                    return 0
                else:
                    return self.redis_client.flushdb()
            except Exception as e:
                if self.app:
                    self.app.logger.error(f"Cache clear error: {e}")
                return 0
        else:
            if pattern:
                # Simple pattern matching for memory cache
                keys_to_delete = [
                    k for k in self._memory_cache.keys()
                    if pattern.replace('*', '') in k
                ]
                for key in keys_to_delete:
                    del self._memory_cache[key]
                return len(keys_to_delete)
            else:
                count = len(self._memory_cache)
                self._memory_cache.clear()
                return count

    def cached(self, timeout: int = 300, key_prefix: str = 'cache'):
        """
        Decorator for caching function results.

        Args:
            timeout: Cache expiration in seconds (default 5 minutes)
            key_prefix: Prefix for cache keys

        Returns:
            Decorated function

        Example:
            @cache_manager.cached(timeout=600, key_prefix='config')
            def generate_config(platform, hostname):
                # Expensive operation
                return config
        """
        def decorator(f: Callable) -> Callable:
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._make_cache_key(
                    f"{key_prefix}:{f.__name__}",
                    *args,
                    **kwargs
                )

                # Try to get from cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    if self.app:
                        self.app.logger.debug(f"Cache hit: {cache_key}")
                    return cached_value

                # Call function and cache result
                result = f(*args, **kwargs)
                self.set(cache_key, result, timeout)

                if self.app:
                    self.app.logger.debug(f"Cache miss: {cache_key}")

                return result

            # Add cache control methods to decorated function
            wrapper.cache_clear = lambda: self.clear(f"{key_prefix}:{f.__name__}:*")
            wrapper.cache_key = lambda *a, **kw: self._make_cache_key(
                f"{key_prefix}:{f.__name__}", *a, **kw
            )

            return wrapper

        return decorator


# Global cache instance
cache_manager = CacheManager()


def invalidate_config_cache(user_id: Optional[int] = None, platform: Optional[str] = None):
    """
    Invalidate configuration-related cache entries.

    Args:
        user_id: User ID to invalidate (all users if None)
        platform: Platform to invalidate (all platforms if None)

    Returns:
        Number of cache entries invalidated
    """
    patterns = []

    if user_id and platform:
        patterns.append(f"config:*:{user_id}:{platform}:*")
    elif user_id:
        patterns.append(f"config:*:{user_id}:*")
    elif platform:
        patterns.append(f"config:*:*:{platform}:*")
    else:
        patterns.append("config:*")

    total_deleted = 0
    for pattern in patterns:
        total_deleted += cache_manager.clear(pattern)

    return total_deleted


def cache_validation_result(timeout: int = 3600):
    """
    Decorator specifically for caching validation results.

    Args:
        timeout: Cache expiration in seconds (default 1 hour)

    Returns:
        Decorated function
    """
    return cache_manager.cached(timeout=timeout, key_prefix='validation')


def cache_template_render(timeout: int = 1800):
    """
    Decorator for caching template rendering results.

    Args:
        timeout: Cache expiration in seconds (default 30 minutes)

    Returns:
        Decorated function
    """
    return cache_manager.cached(timeout=timeout, key_prefix='template')


# Statistics tracking
class CacheStats:
    """Track cache statistics."""

    def __init__(self, cache_mgr: CacheManager):
        """
        Initialize cache statistics.

        Args:
            cache_mgr: CacheManager instance
        """
        self.cache_manager = cache_mgr

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        stats = {
            'type': 'memory',
            'keys': 0,
            'memory_usage': 0,
            'hits': 0,
            'misses': 0
        }

        if self.cache_manager.redis_client:
            try:
                info = self.cache_manager.redis_client.info()
                stats.update({
                    'type': 'redis',
                    'keys': info.get('db0', {}).get('keys', 0),
                    'memory_usage': info.get('used_memory_human', 'N/A'),
                    'hits': info.get('keyspace_hits', 0),
                    'misses': info.get('keyspace_misses', 0),
                    'hit_rate': self._calculate_hit_rate(
                        info.get('keyspace_hits', 0),
                        info.get('keyspace_misses', 0)
                    )
                })
            except Exception:
                pass
        else:
            stats['keys'] = len(self.cache_manager._memory_cache)

        return stats

    @staticmethod
    def _calculate_hit_rate(hits: int, misses: int) -> float:
        """
        Calculate cache hit rate.

        Args:
            hits: Number of cache hits
            misses: Number of cache misses

        Returns:
            Hit rate as percentage
        """
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
