# utils/validation_cache.py
"""
🗄️ Validation Cache System
Reduces OpenAI API calls by caching validation results
"""

import json
import time
import hashlib
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ValidationCache:
    """In-memory cache for validation results"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        
        # 🔧 MEMORY FIX: Add size limits to prevent memory leaks
        import os
        self.max_cache_entries = int(os.getenv("VALIDATION_CACHE_MAX_ENTRIES", "500"))
        logger.info(f"🗄️ ValidationCache initialized: TTL={default_ttl}s, Max={self.max_cache_entries} entries")
        
    def _generate_key(self, workspace_id: str, goals_data: list) -> str:
        """Generate cache key from workspace and goals"""
        # Create a stable hash from goals data
        goals_str = json.dumps(sorted(goals_data, key=lambda x: x.get('id', '')))
        content = f"{workspace_id}:{goals_str}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, workspace_id: str, goals_data: list) -> Optional[Dict[str, Any]]:
        """Get cached validation result"""
        key = self._generate_key(workspace_id, goals_data)
        
        if key not in self.cache:
            return None
            
        cached_item = self.cache[key]
        
        # Check if expired
        if time.time() > cached_item['expires_at']:
            del self.cache[key]
            logger.info(f"🗑️ Expired validation cache for workspace {workspace_id}")
            return None
            
        logger.info(f"✅ Using cached validation for workspace {workspace_id}")
        return cached_item['data']
    
    def set(self, workspace_id: str, goals_data: list, validation_result: Dict[str, Any], ttl: Optional[int] = None):
        """Cache validation result"""
        key = self._generate_key(workspace_id, goals_data)
        expires_at = time.time() + (ttl or self.default_ttl)
        
        # 🔧 MEMORY FIX: Enforce cache size limits before storing
        if len(self.cache) >= self.max_cache_entries:
            self._enforce_cache_size_limit()
        
        self.cache[key] = {
            'data': validation_result,
            'expires_at': expires_at,
            'workspace_id': workspace_id,
            'cached_at': datetime.now().isoformat()
        }
        
        logger.info(f"💾 Cached validation for workspace {workspace_id} (TTL: {ttl or self.default_ttl}s)")
    
    def invalidate_workspace(self, workspace_id: str):
        """Invalidate all cache entries for a workspace"""
        keys_to_remove = []
        for key, value in self.cache.items():
            if value.get('workspace_id') == workspace_id:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
            
        if keys_to_remove:
            logger.info(f"🗑️ Invalidated {len(keys_to_remove)} cache entries for workspace {workspace_id}")
    
    def cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, value in self.cache.items() 
            if current_time > value['expires_at']
        ]
        
        for key in expired_keys:
            del self.cache[key]
            
        if expired_keys:
            logger.info(f"🗑️ Cleaned up {len(expired_keys)} expired cache entries")
    
    def _enforce_cache_size_limit(self):
        """🔧 MEMORY FIX: Enforce cache size limits using LRU eviction."""
        if len(self.cache) <= self.max_cache_entries:
            return
        
        # Sort cache entries by expires_at (oldest first) for LRU eviction
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: x[1]['expires_at']
        )
        
        # Remove oldest entries until we're under the limit
        entries_to_remove = len(self.cache) - self.max_cache_entries + 50  # Remove extra for buffer
        removed_count = 0
        
        for cache_key, _ in sorted_entries[:entries_to_remove]:
            del self.cache[cache_key]
            removed_count += 1
        
        logger.info(f"🗑️ Validation cache size limit enforced: removed {removed_count} oldest entries, cache size now: {len(self.cache)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        current_time = time.time()
        active_entries = sum(1 for value in self.cache.values() if current_time <= value['expires_at'])
        
        return {
            "total_entries": len(self.cache),
            "active_entries": active_entries,
            "expired_entries": len(self.cache) - active_entries,
            "cache_hit_potential": f"{(active_entries / max(len(self.cache), 1)) * 100:.1f}%"
        }

# Global cache instance
validation_cache = ValidationCache(default_ttl=600)  # 10 minutes cache

# Decorator for caching validation functions
def cached_validation(ttl: int = 600):
    """Decorator for caching validation results"""
    def decorator(func):
        async def wrapper(workspace_id: str, goals_data: list, *args, **kwargs):
            # Try to get from cache first
            cached_result = validation_cache.get(workspace_id, goals_data)
            if cached_result is not None:
                return cached_result
            
            # Call the actual function
            result = await func(workspace_id, goals_data, *args, **kwargs)
            
            # Cache the result
            validation_cache.set(workspace_id, goals_data, result, ttl)
            
            return result
        
        return wrapper
    return decorator