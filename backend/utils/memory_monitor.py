# backend/utils/memory_monitor.py
"""
🔧 MEMORY MONITORING UTILITIES

Provides memory usage tracking and leak detection for the AI Team Orchestrator system.
This helps identify and resolve memory leaks that can cause high memory usage issues.
"""

import os
import psutil
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MemoryStats:
    """Memory usage statistics"""
    rss_mb: float  # Resident Set Size (physical memory)
    vms_mb: float  # Virtual Memory Size
    percent: float  # Memory percentage
    available_mb: float  # Available system memory
    timestamp: datetime
    
    @property
    def is_high_usage(self) -> bool:
        """Check if memory usage is considered high (>4GB RSS)"""
        return self.rss_mb > 4096

class MemoryMonitor:
    """
    🔧 MEMORY LEAK DETECTION SYSTEM
    
    Features:
    - Real-time memory usage tracking
    - Memory leak detection over time
    - Component-specific memory reporting
    - Automatic cleanup recommendations
    """
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.baseline_memory: Optional[MemoryStats] = None
        self.peak_memory: Optional[MemoryStats] = None
        self.monitoring_enabled = True
        
    def get_current_memory_stats(self) -> MemoryStats:
        """Get current memory usage statistics"""
        try:
            memory_info = self.process.memory_info()
            system_memory = psutil.virtual_memory()
            
            stats = MemoryStats(
                rss_mb=memory_info.rss / 1024 / 1024,  # Convert bytes to MB
                vms_mb=memory_info.vms / 1024 / 1024,
                percent=self.process.memory_percent(),
                available_mb=system_memory.available / 1024 / 1024,
                timestamp=datetime.now()
            )
            
            # Track peak memory
            if not self.peak_memory or stats.rss_mb > self.peak_memory.rss_mb:
                self.peak_memory = stats
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return MemoryStats(0, 0, 0, 0, datetime.now())
    
    def set_baseline(self):
        """Set baseline memory usage for leak detection"""
        self.baseline_memory = self.get_current_memory_stats()
        logger.info(f"🔧 Memory baseline set: {self.baseline_memory.rss_mb:.1f}MB RSS")
    
    def get_memory_increase_since_baseline(self) -> float:
        """Get memory increase since baseline in MB"""
        if not self.baseline_memory:
            return 0.0
        
        current = self.get_current_memory_stats()
        return current.rss_mb - self.baseline_memory.rss_mb
    
    def detect_memory_leak(self, threshold_mb: float = 500) -> bool:
        """Detect if there's likely a memory leak (increase > threshold)"""
        if not self.baseline_memory:
            return False
        
        increase = self.get_memory_increase_since_baseline()
        return increase > threshold_mb
    
    async def get_component_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics from various system components"""
        stats = {}
        
        try:
            # WebSocket connections
            from utils.websocket_health_manager import get_websocket_health_stats
            ws_stats = get_websocket_health_stats()
            stats["websocket"] = {
                "active_connections": ws_stats.get("active_connections", 0),
                "total_connections": ws_stats.get("total_connections", 0)
            }
        except Exception:
            stats["websocket"] = {"error": "not_available"}
        
        try:
            # Task deduplication cache
            from services.task_deduplication_manager import task_deduplication_manager
            cache_stats = task_deduplication_manager.get_cache_stats()
            stats["task_deduplication"] = cache_stats
        except Exception:
            stats["task_deduplication"] = {"error": "not_available"}
        
        try:
            # Goal monitor cache
            from automated_goal_monitor import automated_goal_monitor
            goal_stats = automated_goal_monitor.get_cache_stats()
            stats["goal_monitor"] = goal_stats
        except Exception:
            stats["goal_monitor"] = {"error": "not_available"}
        
        return stats
    
    async def generate_memory_report(self) -> Dict[str, Any]:
        """Generate comprehensive memory usage report"""
        current_stats = self.get_current_memory_stats()
        component_stats = await self.get_component_memory_stats()
        
        report = {
            "current_memory": {
                "rss_mb": current_stats.rss_mb,
                "vms_mb": current_stats.vms_mb,
                "percent": current_stats.percent,
                "available_mb": current_stats.available_mb,
                "is_high_usage": current_stats.is_high_usage,
                "timestamp": current_stats.timestamp.isoformat()
            },
            "baseline_memory": {
                "rss_mb": self.baseline_memory.rss_mb if self.baseline_memory else None,
                "timestamp": self.baseline_memory.timestamp.isoformat() if self.baseline_memory else None
            } if self.baseline_memory else None,
            "peak_memory": {
                "rss_mb": self.peak_memory.rss_mb if self.peak_memory else None,
                "timestamp": self.peak_memory.timestamp.isoformat() if self.peak_memory else None
            } if self.peak_memory else None,
            "memory_increase_mb": self.get_memory_increase_since_baseline(),
            "leak_detected": self.detect_memory_leak(),
            "component_stats": component_stats
        }
        
        return report
    
    def log_memory_summary(self):
        """Log a summary of current memory usage"""
        current = self.get_current_memory_stats()
        
        if current.is_high_usage:
            level = logging.WARNING
            icon = "⚠️"
        else:
            level = logging.INFO  
            icon = "📊"
        
        increase_text = ""
        if self.baseline_memory:
            increase = self.get_memory_increase_since_baseline()
            increase_text = f", +{increase:.1f}MB since baseline"
        
        logger.log(level, 
            f"{icon} Memory: {current.rss_mb:.1f}MB RSS ({current.percent:.1f}%){increase_text}"
        )
        
        if self.detect_memory_leak():
            logger.warning(f"🚨 MEMORY LEAK DETECTED: {self.get_memory_increase_since_baseline():.1f}MB increase since baseline")

# Global memory monitor instance
memory_monitor = MemoryMonitor()

# Convenience functions
def get_memory_stats() -> MemoryStats:
    """Get current memory statistics"""
    return memory_monitor.get_current_memory_stats()

def set_memory_baseline():
    """Set memory baseline for leak detection"""
    memory_monitor.set_baseline()

def log_memory_status():
    """Log current memory status"""
    memory_monitor.log_memory_summary()

async def generate_memory_report() -> Dict[str, Any]:
    """Generate comprehensive memory report"""
    return await memory_monitor.generate_memory_report()

def check_memory_leak(threshold_mb: float = 500) -> bool:
    """Check if there's a memory leak"""
    return memory_monitor.detect_memory_leak(threshold_mb)