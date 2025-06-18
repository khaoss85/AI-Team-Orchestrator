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