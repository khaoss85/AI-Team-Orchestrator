# backend/utils/workspace_goals_cache.py
"""
🚀 PERFORMANCE OPTIMIZATION: Workspace Goals Query Cache

Reduces database query explosion from 6+ queries per operation to 1 per 5-minute window.
Implements intelligent caching with TTL and workspace-level invalidation.
"""

import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class WorkspaceGoalsCache:
    """
    High-performance cache for workspace_goals queries with intelligent invalidation.
    
    Features:
    - TTL-based expiration (default 5 minutes)
    - Workspace-level invalidation
    - Batch query optimization
    - Memory-efficient storage
    """
    
    def __init__(self, ttl_minutes: int = 5):
        self.cache: Dict[str, Tuple[List[Dict[str, Any]], float]] = {}
        self.ttl_seconds = ttl_minutes * 60
        
        # 🔧 MEMORY FIX: Add size limits to prevent memory leaks
        import os
        self.max_cache_entries = int(os.getenv("WORKSPACE_GOALS_CACHE_MAX_ENTRIES", "1000"))
        logger.info(f"🗄️ WorkspaceGoalsCache initialized: TTL={self.ttl_seconds}s, Max={self.max_cache_entries} entries")
        self.hit_count = 0
        self.miss_count = 0
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
        
        logger.info(f"🚀 WorkspaceGoalsCache initialized with {ttl_minutes}-minute TTL")
    
    async def get_workspace_goals(
        self, 
        workspace_id: str, 
        force_refresh: bool = False,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get workspace goals with intelligent caching.
        
        Args:
            workspace_id: Target workspace UUID
            force_refresh: Bypass cache and fetch fresh data
            status_filter: Optional status to filter by (e.g., 'active')
        """
        await self._cleanup_expired_entries()
        
        cache_key = f"goals_{workspace_id}_{status_filter or 'all'}"
        
        # Check cache first (unless force refresh)
        if not force_refresh and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.ttl_seconds:
                self.hit_count += 1
                logger.debug(f"🎯 CACHE HIT: {cache_key} (age: {int(time.time() - timestamp)}s)")
                return cached_data
        
        # Cache miss - fetch from database
        self.miss_count += 1
        logger.debug(f"💾 CACHE MISS: {cache_key} - fetching from database")
        
        goals = await self._fetch_goals_from_db(workspace_id, status_filter)
        
        # 🔧 MEMORY FIX: Enforce cache size limits before storing
        if len(self.cache) >= self.max_cache_entries:
            self._enforce_cache_size_limit()
        
        # Store in cache
        self.cache[cache_key] = (goals, time.time())
        
        logger.info(f"✅ Cached {len(goals)} goals for workspace {workspace_id[:8]} (status: {status_filter or 'all'})")
        return goals
    
    async def _fetch_goals_from_db(
        self, 
        workspace_id: str, 
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch goals from database with optimized query."""
        try:
            from database import supabase
            
            query = supabase.table("workspace_goals").select("*").eq("workspace_id", workspace_id)
            
            if status_filter:
                query = query.eq("status", status_filter)
            
            result = query.order("priority", desc=True).execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch goals from database: {e}")
            return []
    
    async def batch_get_workspace_goals(
        self, 
        workspace_ids: List[str],
        status_filter: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        🚀 OPTIMIZATION: Batch fetch goals for multiple workspaces.
        
        Reduces N+1 query pattern to single batch query + cache.
        """
        result = {}
        uncached_workspaces = []
        
        # Check cache for each workspace
        for workspace_id in workspace_ids:
            cache_key = f"goals_{workspace_id}_{status_filter or 'all'}"
            
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if time.time() - timestamp < self.ttl_seconds:
                    result[workspace_id] = cached_data
                    self.hit_count += 1
                    continue
            
            uncached_workspaces.append(workspace_id)
        
        # Batch fetch uncached workspaces
        if uncached_workspaces:
            logger.info(f"🔄 Batch fetching goals for {len(uncached_workspaces)} workspaces")
            batch_results = await self._batch_fetch_from_db(uncached_workspaces, status_filter)
            
            # Cache and add to results
            for workspace_id, goals in batch_results.items():
                cache_key = f"goals_{workspace_id}_{status_filter or 'all'}"
                self.cache[cache_key] = (goals, time.time())
                result[workspace_id] = goals
                self.miss_count += 1
        
        logger.info(f"📊 Batch operation complete: {len(result)} workspaces (hits: {self.hit_count}, misses: {self.miss_count})")
        return result
    
    async def _batch_fetch_from_db(
        self, 
        workspace_ids: List[str], 
        status_filter: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Optimized batch query for multiple workspaces."""
        try:
            from database import supabase
            
            # Single query with IN clause instead of N separate queries
            query = supabase.table("workspace_goals").select("*").in_("workspace_id", workspace_ids)
            
            if status_filter:
                query = query.eq("status", status_filter)
            
            result = query.order("priority", desc=True).execute()
            all_goals = result.data or []
            
            # Group by workspace_id
            grouped = {}
            for goal in all_goals:
                workspace_id = goal.get("workspace_id")
                if workspace_id not in grouped:
                    grouped[workspace_id] = []
                grouped[workspace_id].append(goal)
            
            # Ensure all requested workspaces have entries (even if empty)
            for workspace_id in workspace_ids:
                if workspace_id not in grouped:
                    grouped[workspace_id] = []
            
            return grouped
            
        except Exception as e:
            logger.error(f"❌ Failed to batch fetch goals: {e}")
            return {ws_id: [] for ws_id in workspace_ids}
    
    def invalidate_workspace(self, workspace_id: str):
        """Invalidate all cache entries for a specific workspace."""
        keys_to_remove = [key for key in self.cache.keys() if key.startswith(f"goals_{workspace_id}_")]
        
        for key in keys_to_remove:
            del self.cache[key]
            
        logger.info(f"🗑️ Invalidated {len(keys_to_remove)} cache entries for workspace {workspace_id[:8]}")
    
    def invalidate_all(self):
        """Clear entire cache."""
        cache_size = len(self.cache)
        self.cache.clear()
        logger.info(f"🗑️ Cleared entire cache ({cache_size} entries)")
    
    async def _cleanup_expired_entries(self):
        """Remove expired entries from cache."""
        current_time = time.time()
        
        # Only cleanup every 5 minutes to avoid overhead
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp >= self.ttl_seconds
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")
        
        self.last_cleanup = current_time
    
    def _enforce_cache_size_limit(self):
        """🔧 MEMORY FIX: Enforce cache size limits using LRU eviction."""
        if len(self.cache) <= self.max_cache_entries:
            return
        
        # Sort cache entries by timestamp (oldest first) for LRU eviction
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: x[1][1]  # Sort by timestamp
        )
        
        # Remove oldest entries until we're under the limit
        entries_to_remove = len(self.cache) - self.max_cache_entries + 100  # Remove extra for buffer
        removed_count = 0
        
        for cache_key, _ in sorted_entries[:entries_to_remove]:
            del self.cache[cache_key]
            removed_count += 1
        
        logger.info(f"🗑️ Cache size limit enforced: removed {removed_count} oldest entries, cache size now: {len(self.cache)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_size": len(self.cache),
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate_percent": round(hit_rate, 2),
            "ttl_seconds": self.ttl_seconds,
            "total_requests": total_requests
        }

# Global cache instance
workspace_goals_cache = WorkspaceGoalsCache(ttl_minutes=5)

# Convenience functions for easy integration
async def get_workspace_goals_cached(
    workspace_id: str, 
    force_refresh: bool = False,
    status_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Convenience function to get cached workspace goals."""
    return await workspace_goals_cache.get_workspace_goals(
        workspace_id, force_refresh, status_filter
    )

async def batch_get_workspace_goals_cached(
    workspace_ids: List[str],
    status_filter: Optional[str] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """Convenience function for batch cached goals retrieval."""
    return await workspace_goals_cache.batch_get_workspace_goals(
        workspace_ids, status_filter
    )

def invalidate_workspace_goals_cache(workspace_id: str):
    """Convenience function to invalidate workspace cache."""
    workspace_goals_cache.invalidate_workspace(workspace_id)

def get_cache_stats() -> Dict[str, Any]:
    """Get cache performance statistics."""
    return workspace_goals_cache.get_stats()