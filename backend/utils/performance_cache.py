"""
Smart Caching Layer for Expensive Database Operations
Reduces API costs by caching expensive operations with intelligent TTL
"""

import asyncio
import time
from typing import Any, Dict, Optional, Callable, Union
from functools import wraps
import logging
import hashlib
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PerformanceCache:
    """
    High-performance caching system for expensive operations.
    Features:
    - TTL (Time To Live) support
    - Intelligent cache invalidation 
    - Memory-efficient storage
    - Hit rate tracking for optimization
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }
        
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate unique cache key from function signature"""
        try:
            # Create deterministic hash from function name and parameters
            key_data = {
                'func': func_name,
                'args': args,
                'kwargs': {k: v for k, v in sorted(kwargs.items())}
            }
            key_json = json.dumps(key_data, sort_keys=True, default=str)
            return hashlib.md5(key_json.encode()).hexdigest()
        except Exception as e:
            # Fallback to simple string concatenation
            logger.warning(f"Cache key generation failed, using fallback: {e}")
            return f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
    
    def _is_expired(self, cache_entry: dict) -> bool:
        """Check if cache entry has expired"""
        return time.time() > cache_entry['expires_at']
    
    def _evict_oldest(self):
        """Remove oldest cache entries when max_size is reached"""
        if len(self.cache) >= self.max_size:
            # Remove 10% of oldest entries
            entries_to_remove = max(1, len(self.cache) // 10)
            oldest_keys = sorted(
                self.cache.keys(), 
                key=lambda k: self.cache[k]['created_at']
            )[:entries_to_remove]
            
            for key in oldest_keys:
                del self.cache[key]
                self.stats['evictions'] += 1
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache if exists and not expired"""
        self.stats['total_requests'] += 1
        
        if key not in self.cache:
            self.stats['misses'] += 1
            return None
            
        entry = self.cache[key]
        
        if self._is_expired(entry):
            del self.cache[key]
            self.stats['misses'] += 1
            return None
            
        # Update access time for LRU behavior
        entry['last_accessed'] = time.time()
        self.stats['hits'] += 1
        logger.debug(f"Cache HIT for key: {key[:10]}...")
        return entry['data']
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Store item in cache with TTL"""
        self._evict_oldest()
        
        ttl = ttl or self.default_ttl
        now = time.time()
        
        self.cache[key] = {
            'data': data,
            'created_at': now,
            'last_accessed': now,
            'expires_at': now + ttl
        }
        logger.debug(f"Cache SET for key: {key[:10]}... (TTL: {ttl}s)")
    
    def invalidate(self, pattern: str = None) -> int:
        """Invalidate cache entries matching pattern"""
        if pattern is None:
            # Clear all
            count = len(self.cache)
            self.cache.clear()
            logger.info(f"Cache cleared: {count} entries removed")
            return count
            
        # Pattern-based invalidation
        keys_to_remove = [k for k in self.cache.keys() if pattern in k]
        for key in keys_to_remove:
            del self.cache[key]
        
        logger.info(f"Cache invalidated: {len(keys_to_remove)} entries removed (pattern: {pattern})")
        return len(keys_to_remove)
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total = self.stats['total_requests']
        hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            **self.stats,
            'hit_rate_percent': round(hit_rate, 2),
            'cache_size': len(self.cache),
            'memory_usage': f"{len(self.cache)}/{self.max_size}"
        }

# Global cache instance
_cache_instance = PerformanceCache(max_size=500, default_ttl=300)  # 5 minute default TTL

def cached(ttl: int = 300, cache_key: Optional[str] = None):
    """
    Decorator for caching expensive function results.
    
    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        cache_key: Custom cache key (optional)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if cache_key:
                key = cache_key
            else:
                key = _cache_instance._generate_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            cached_result = _cache_instance.get(key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                _cache_instance.set(key, result, ttl)
                return result
                
            except Exception as e:
                logger.error(f"Error executing cached function {func.__name__}: {e}")
                raise
        
        # Add cache management methods to function
        wrapper.cache_invalidate = lambda pattern=None: _cache_instance.invalidate(pattern or func.__name__)
        wrapper.cache_stats = lambda: _cache_instance.get_stats()
        
        return wrapper
    return decorator

# Workspace-specific caching helpers
def invalidate_workspace_cache(workspace_id: str) -> int:
    """Invalidate all cache entries for a workspace"""
    return _cache_instance.invalidate(workspace_id)

def get_cache_stats() -> dict:
    """Get global cache statistics"""
    return _cache_instance.get_stats()

# Rate limiting using cache
def rate_limited(max_requests: int = 10, window_seconds: int = 60):
    """
    Rate limiting decorator using cache backend.
    
    Args:
        max_requests: Maximum requests allowed in time window
        window_seconds: Time window in seconds
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get client identifier (you might want to use IP, user ID, etc.)
            # For now, use function name + first argument as identifier
            client_id = f"rate_limit_{func.__name__}_{str(args[0]) if args else 'global'}"
            
            # Check current request count
            current_count = _cache_instance.get(client_id) or 0
            
            if current_count >= max_requests:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429, 
                    detail=f"Rate limit exceeded. Max {max_requests} requests per {window_seconds} seconds"
                )
            
            # Increment counter
            _cache_instance.set(client_id, current_count + 1, window_seconds)
            
            # Execute function
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Export functions
__all__ = [
    'PerformanceCache', 
    'cached', 
    'rate_limited',
    'invalidate_workspace_cache', 
    'get_cache_stats'
]