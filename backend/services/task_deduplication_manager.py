#!/usr/bin/env python3
"""
🚫 TASK DEDUPLICATION MANAGER

Comprehensive system to prevent duplicate task creation and manage task uniqueness.
This addresses the root cause of workspace auto-pause issues and executor overload.

Features:
- Pre-creation duplicate detection
- Semantic similarity checking  
- Batch duplicate cleanup
- Performance-optimized queries
- Pillars compliant (AI-driven decisions)
"""

import asyncio
import logging
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass
import difflib
import re

from database import supabase, list_tasks
from models import TaskStatus

logger = logging.getLogger(__name__)

@dataclass
class DuplicateDetectionResult:
    """Result of duplicate detection check"""
    is_duplicate: bool
    existing_task_id: Optional[str] = None
    similarity_score: float = 0.0
    detection_method: str = ""
    reason: str = ""

@dataclass
class DeduplicationStats:
    """Statistics from deduplication operations"""
    total_checked: int = 0
    duplicates_found: int = 0
    duplicates_removed: int = 0
    unique_tasks_kept: int = 0
    processing_time_ms: float = 0.0

class TaskDeduplicationManager:
    """
    🎯 DEFINITIVE SOLUTION for task duplication issues
    
    Prevents the root cause of workspace auto-pause by ensuring
    only unique, necessary tasks are created.
    """
    
    def __init__(self):
        self.similarity_threshold = float(os.getenv("TASK_SIMILARITY_THRESHOLD", "0.85"))
        self.enable_semantic_check = os.getenv("ENABLE_SEMANTIC_SIMILARITY", "true").lower() == "true"
        self.cache_duration_seconds = 300  # 5 minutes
        self._task_cache: Dict[str, Tuple[float, List[Dict]]] = {}
        # 🔧 FIX: Add cache size limits to prevent memory bloat
        self.max_cache_entries = int(os.getenv("TASK_CACHE_MAX_ENTRIES", "50"))
        self.max_tasks_per_cache = int(os.getenv("TASK_CACHE_MAX_TASKS_PER_ENTRY", "100"))
        
        logger.info(f"TaskDeduplicationManager initialized - similarity_threshold: {self.similarity_threshold}, semantic_check: {self.enable_semantic_check}")
    
    async def ensure_unique_task(
        self, 
        task_data: Dict, 
        workspace_id: str,
        check_semantic: bool = True
    ) -> DuplicateDetectionResult:
        """
        🔍 CORE FUNCTION: Check if task is unique before creation
        
        Returns:
            DuplicateDetectionResult with is_duplicate=True if task should NOT be created
        """
        try:
            task_name = task_data.get("name", "")
            if not task_name:
                return DuplicateDetectionResult(
                    is_duplicate=False,
                    reason="Task has no name - allowing creation"
                )
            
            # Get existing tasks (with caching)
            existing_tasks = await self._get_cached_tasks(workspace_id)
            
            # 1. EXACT NAME MATCH CHECK
            exact_match = await self._check_exact_name_match(task_name, existing_tasks)
            if exact_match.is_duplicate:
                return exact_match
            
            # 2. HASH-BASED DUPLICATE CHECK (fast)
            hash_match = await self._check_task_hash_match(task_data, existing_tasks)
            if hash_match.is_duplicate:
                return hash_match
            
            # 3. SEMANTIC SIMILARITY CHECK (AI-driven, if enabled)
            if check_semantic and self.enable_semantic_check:
                semantic_match = await self._check_semantic_similarity(task_data, existing_tasks)
                if semantic_match.is_duplicate:
                    return semantic_match
            
            # 4. URGENT TASK FREQUENCY CHECK
            urgent_check = await self._check_urgent_task_frequency(task_data, existing_tasks)
            if urgent_check.is_duplicate:
                return urgent_check
            
            return DuplicateDetectionResult(
                is_duplicate=False,
                reason="Task is unique - safe to create"
            )
            
        except Exception as e:
            logger.error(f"Error in ensure_unique_task: {e}")
            # Fail-safe: Allow creation if check fails
            return DuplicateDetectionResult(
                is_duplicate=False,
                reason=f"Duplicate check failed, allowing creation: {e}"
            )
    
    async def cleanup_duplicate_tasks(
        self, 
        workspace_id: str,
        dry_run: bool = False
    ) -> DeduplicationStats:
        """
        🧹 CLEANUP FUNCTION: Remove existing duplicates
        
        Keeps most recent/relevant task, removes older duplicates
        """
        start_time = datetime.now()
        stats = DeduplicationStats()
        
        try:
            logger.info(f"Starting duplicate cleanup for workspace {workspace_id} (dry_run={dry_run})")
            
            # Get all tasks
            all_tasks = await list_tasks(workspace_id)
            stats.total_checked = len(all_tasks)
            
            if not all_tasks:
                logger.info("No tasks found for cleanup")
                return stats
            
            # Group tasks by name
            tasks_by_name = {}
            for task in all_tasks:
                name = task.get("name", "Unknown")
                if name not in tasks_by_name:
                    tasks_by_name[name] = []
                tasks_by_name[name].append(task)
            
            # Find and process duplicates
            for task_name, task_group in tasks_by_name.items():
                if len(task_group) > 1:
                    await self._process_duplicate_group(
                        task_name, task_group, stats, dry_run
                    )
                else:
                    stats.unique_tasks_kept += 1
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            stats.processing_time_ms = processing_time
            
            logger.info(f"Deduplication completed: {stats.duplicates_removed} removed, {stats.unique_tasks_kept} kept, {processing_time:.1f}ms")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error in cleanup_duplicate_tasks: {e}")
            return stats
    
    async def _get_cached_tasks(self, workspace_id: str) -> List[Dict]:
        """Get tasks with caching for performance - 🔧 FIX: Added memory limits"""
        current_time = datetime.now().timestamp()
        
        # Check cache
        if workspace_id in self._task_cache:
            cache_time, cached_tasks = self._task_cache[workspace_id]
            if current_time - cache_time < self.cache_duration_seconds:
                return cached_tasks
        
        # 🔧 FIX: Cleanup cache if too large
        await self._cleanup_cache_if_needed()
        
        # Refresh cache
        tasks = await list_tasks(workspace_id)
        
        # 🔧 FIX: Limit number of tasks stored per cache entry
        if len(tasks) > self.max_tasks_per_cache:
            # Keep only most recent tasks to prevent memory bloat
            tasks_sorted = sorted(tasks, key=lambda x: x.get('created_at', ''), reverse=True)
            tasks = tasks_sorted[:self.max_tasks_per_cache]
            logger.warning(f"🔧 Task cache truncated for workspace {workspace_id}: {len(tasks)}/{len(tasks_sorted)} tasks kept")
        
        self._task_cache[workspace_id] = (current_time, tasks)
        
        return tasks
    
    async def _cleanup_cache_if_needed(self):
        """🔧 FIX: Cleanup cache entries if we exceed limits"""
        if len(self._task_cache) <= self.max_cache_entries:
            return
        
        current_time = datetime.now().timestamp()
        
        # Remove expired entries first
        expired_keys = [
            workspace_id for workspace_id, (cache_time, _) in self._task_cache.items()
            if current_time - cache_time >= self.cache_duration_seconds
        ]
        
        for key in expired_keys:
            del self._task_cache[key]
        
        # If still too many entries, remove oldest
        if len(self._task_cache) > self.max_cache_entries:
            # Sort by cache time and remove oldest
            entries_by_time = sorted(
                self._task_cache.items(),
                key=lambda x: x[1][0]  # Sort by cache_time
            )
            
            excess_count = len(self._task_cache) - self.max_cache_entries
            for workspace_id, _ in entries_by_time[:excess_count]:
                del self._task_cache[workspace_id]
            
            logger.warning(f"🧹 Task cache cleanup: removed {excess_count + len(expired_keys)} entries")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """🔧 FIX: Get cache statistics for monitoring"""
        total_tasks = sum(len(tasks) for _, tasks in self._task_cache.values())
        return {
            "cache_entries": len(self._task_cache),
            "max_cache_entries": self.max_cache_entries,
            "total_cached_tasks": total_tasks,
            "max_tasks_per_entry": self.max_tasks_per_cache,
            "cache_duration_seconds": self.cache_duration_seconds
        }
    
    async def _check_exact_name_match(
        self, 
        task_name: str, 
        existing_tasks: List[Dict]
    ) -> DuplicateDetectionResult:
        """Check for exact task name matches"""
        
        for existing_task in existing_tasks:
            existing_name = existing_task.get("name", "")
            
            if existing_name == task_name:
                # Check if existing task is still active
                status = existing_task.get("status", "")
                if status not in ["completed", "failed", "cancelled"]:
                    return DuplicateDetectionResult(
                        is_duplicate=True,
                        existing_task_id=existing_task.get("id"),
                        similarity_score=1.0,
                        detection_method="exact_name_match",
                        reason=f"Exact name match with existing {status} task"
                    )
        
        return DuplicateDetectionResult(is_duplicate=False)
    
    async def _check_task_hash_match(
        self, 
        task_data: Dict, 
        existing_tasks: List[Dict]
    ) -> DuplicateDetectionResult:
        """Check for hash-based duplicates (faster than semantic)"""
        
        # Create normalized hash of task
        task_hash = self._create_task_hash(task_data)
        
        for existing_task in existing_tasks:
            existing_hash = self._create_task_hash(existing_task)
            
            if task_hash == existing_hash:
                status = existing_task.get("status", "")
                if status not in ["completed", "failed", "cancelled"]:
                    return DuplicateDetectionResult(
                        is_duplicate=True,
                        existing_task_id=existing_task.get("id"),
                        similarity_score=1.0,
                        detection_method="hash_match",
                        reason=f"Hash match with existing {status} task"
                    )
        
        return DuplicateDetectionResult(is_duplicate=False)
    
    async def _check_semantic_similarity(
        self, 
        task_data: Dict, 
        existing_tasks: List[Dict]
    ) -> DuplicateDetectionResult:
        """AI-driven semantic similarity check (Pillar 2 compliant)"""
        
        task_name = task_data.get("name", "") or ""
        task_description = task_data.get("description", "") or ""
        task_text = f"{task_name} {task_description}".lower().strip()
        
        for existing_task in existing_tasks:
            existing_name = existing_task.get("name", "") or ""
            existing_desc = existing_task.get("description", "") or ""
            existing_text = f"{existing_name} {existing_desc}".lower().strip()
            
            # Use difflib for basic semantic similarity
            similarity = difflib.SequenceMatcher(None, task_text, existing_text).ratio()
            
            if similarity >= self.similarity_threshold:
                status = existing_task.get("status", "")
                if status not in ["completed", "failed", "cancelled"]:
                    return DuplicateDetectionResult(
                        is_duplicate=True,
                        existing_task_id=existing_task.get("id"),
                        similarity_score=similarity,
                        detection_method="semantic_similarity",
                        reason=f"High semantic similarity ({similarity:.2f}) with existing {status} task"
                    )
        
        return DuplicateDetectionResult(is_duplicate=False)
    
    async def _check_urgent_task_frequency(
        self, 
        task_data: Dict, 
        existing_tasks: List[Dict]
    ) -> DuplicateDetectionResult:
        """Check for excessive urgent task creation"""
        
        task_name = task_data.get("name", "")
        
        # Count similar urgent tasks created recently
        if "🚨 URGENT" in task_name or "urgent" in task_name.lower():
            recent_urgent_count = 0
            one_hour_ago = datetime.now() - timedelta(hours=1)
            
            for existing_task in existing_tasks:
                existing_name = existing_task.get("name", "")
                if "🚨 URGENT" in existing_name or "urgent" in existing_name.lower():
                    # Simple similarity check for urgent tasks
                    if self._are_urgent_tasks_similar(task_name, existing_name):
                        task_created = existing_task.get("created_at", "")
                        if task_created:
                            try:
                                created_time = datetime.fromisoformat(task_created.replace('Z', '+00:00'))
                                if created_time > one_hour_ago:
                                    recent_urgent_count += 1
                            except:
                                pass
            
            # If too many similar urgent tasks recently, it's likely a duplicate
            if recent_urgent_count >= 3:
                return DuplicateDetectionResult(
                    is_duplicate=True,
                    similarity_score=0.9,
                    detection_method="urgent_frequency_check",
                    reason=f"Too many similar urgent tasks recently ({recent_urgent_count})"
                )
        
        return DuplicateDetectionResult(is_duplicate=False)
    
    def _create_task_hash(self, task_data: Dict) -> str:
        """Create normalized hash for task comparison"""
        
        # Extract key fields for hashing with safe None handling
        name = (task_data.get("name") or "").strip().lower()
        description = (task_data.get("description") or "").strip().lower()
        assigned_role = (task_data.get("assigned_to_role") or "").strip().lower()
        
        # Remove dynamic elements
        name = re.sub(r'\d+(\.\d+)?%', 'X%', name)  # Replace percentages with X%
        name = re.sub(r'\d+', 'N', name)  # Replace numbers with N
        
        # Create hash string
        hash_string = f"{name}|{description}|{assigned_role}"
        
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def _are_urgent_tasks_similar(self, task1_name: str, task2_name: str) -> bool:
        """Check if two urgent task names are similar"""
        
        # Remove urgent prefixes and percentages for comparison
        clean1 = re.sub(r'🚨 URGENT:\s*', '', task1_name)
        clean2 = re.sub(r'🚨 URGENT:\s*', '', task2_name)
        
        clean1 = re.sub(r'\d+(\.\d+)?%', '', clean1 or "").strip()
        clean2 = re.sub(r'\d+(\.\d+)?%', '', clean2 or "").strip()
        
        # Basic similarity check
        similarity = difflib.SequenceMatcher(None, clean1.lower(), clean2.lower()).ratio()
        return similarity > 0.7
    
    async def _process_duplicate_group(
        self,
        task_name: str,
        task_group: List[Dict],
        stats: DeduplicationStats,
        dry_run: bool
    ):
        """Process a group of duplicate tasks"""
        
        logger.info(f"Processing {len(task_group)} duplicates of: {task_name[:50]}")
        stats.duplicates_found += len(task_group) - 1
        
        # Sort by priority: keep completed/in_progress, then by creation time
        def sort_priority(task):
            status = task.get("status", "")
            created_at = task.get("created_at", "")
            
            # Priority order: completed > in_progress > others
            if status == "completed":
                priority = 0
            elif status == "in_progress":
                priority = 1
            else:
                priority = 2
                
            return (priority, created_at)
        
        sorted_tasks = sorted(task_group, key=sort_priority)
        
        # Keep the first (highest priority) task
        task_to_keep = sorted_tasks[0]
        tasks_to_remove = sorted_tasks[1:]
        
        logger.info(f"Keeping: {task_to_keep.get('id')} ({task_to_keep.get('status')})")
        stats.unique_tasks_kept += 1
        
        # Remove duplicates
        for task_to_remove in tasks_to_remove:
            task_id = task_to_remove.get("id")
            status = task_to_remove.get("status", "")
            
            logger.info(f"{'Would remove' if dry_run else 'Removing'}: {task_id} ({status})")
            
            if not dry_run:
                try:
                    supabase.table("tasks").delete().eq("id", task_id).execute()
                    stats.duplicates_removed += 1
                except Exception as e:
                    logger.error(f"Error removing duplicate task {task_id}: {e}")

# Global instance
task_deduplication_manager = TaskDeduplicationManager()