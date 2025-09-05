"""
Cache Manager Utility
Simple in-memory caching with TTL support for insights system
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import json

logger = logging.getLogger(__name__)


class CacheEntry:
    """Represents a cached item with expiration"""
    def __init__(self, data: Any, ttl_seconds: int = 300):
        self.data = data
        self.created_at = datetime.utcnow()
        self.ttl_seconds = ttl_seconds
    
    def is_valid(self) -> bool:
        """Check if cache entry is still valid"""
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age < self.ttl_seconds
    
    def time_remaining(self) -> int:
        """Get seconds remaining before expiration"""
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return max(0, int(self.ttl_seconds - age))


class CacheManager:
    """
    Simple in-memory cache manager for the insights system.
    Provides basic caching with TTL and invalidation support.
    """
    
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._hit_count = 0
        self._miss_count = 0
        self._eviction_count = 0
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = {
            'args': args,
            'kwargs': kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache if valid"""
        if key in self._cache:
            entry = self._cache[key]
            if entry.is_valid():
                self._hit_count += 1
                logger.debug(f"Cache hit for key {key[:8]}... ({entry.time_remaining()}s remaining)")
                return entry.data
            else:
                # Remove expired entry
                del self._cache[key]
                self._eviction_count += 1
                logger.debug(f"Cache expired for key {key[:8]}...")
        
        self._miss_count += 1
        return None
    
    def set(self, key: str, data: Any, ttl_seconds: int = 300):
        """Set item in cache with TTL"""
        self._cache[key] = CacheEntry(data, ttl_seconds)
        logger.debug(f"Cached data for key {key[:8]}... (TTL: {ttl_seconds}s)")
    
    def invalidate(self, key: str) -> bool:
        """Invalidate specific cache entry"""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Invalidated cache for key {key[:8]}...")
            return True
        return False
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        keys_to_remove = [k for k in self._cache.keys() if pattern in k]
        for key in keys_to_remove:
            del self._cache[key]
        
        if keys_to_remove:
            logger.debug(f"Invalidated {len(keys_to_remove)} cache entries matching '{pattern}'")
    
    def clear(self):
        """Clear entire cache"""
        size = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared cache ({size} entries)")
    
    def cleanup_expired(self):
        """Remove all expired entries"""
        expired_keys = []
        for key, entry in self._cache.items():
            if not entry.is_valid():
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
            self._eviction_count += 1
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "size": len(self._cache),
            "hits": self._hit_count,
            "misses": self._miss_count,
            "evictions": self._eviction_count,
            "hit_rate": f"{hit_rate:.1f}%",
            "total_requests": total_requests
        }
    
    def get_or_compute(self, key: str, compute_func, ttl_seconds: int = 300) -> Any:
        """Get from cache or compute if missing"""
        data = self.get(key)
        if data is None:
            data = compute_func()
            self.set(key, data, ttl_seconds)
        return data


# Global cache instance
_global_cache = None

def get_cache_manager() -> CacheManager:
    """Get or create global cache manager instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheManager()
        logger.info("Initialized global cache manager")
    return _global_cache