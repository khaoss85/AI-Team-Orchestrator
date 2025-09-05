#!/usr/bin/env python3
"""
OpenAI Quota Tracker Service
Monitors OpenAI API usage, quota limits, and provides real-time notifications
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Literal
from enum import Enum
import json
from collections import defaultdict

# Import Usage API client for real data
from services.openai_usage_api_client import get_usage_client

logger = logging.getLogger(__name__)

class QuotaStatus(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    RATE_LIMITED = "rate_limited"
    QUOTA_EXCEEDED = "quota_exceeded"
    DEGRADED = "degraded"

class WorkspaceQuotaTracker:
    """
    Tracks OpenAI API usage and quota status for a specific workspace
    """
    
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.request_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.last_reset = datetime.now()
        self.current_status = QuotaStatus.NORMAL
        self.connected_websockets: List[Any] = []
        
        # Rate limits (configurable via environment variables)
        self.rate_limits = {
            "requests_per_minute": int(os.getenv("OPENAI_RATE_LIMIT_PER_MINUTE", "500")),
            "requests_per_day": int(os.getenv("OPENAI_RATE_LIMIT_PER_DAY", "10000")),
            "tokens_per_minute": int(os.getenv("OPENAI_TOKEN_LIMIT_PER_MINUTE", "150000")),
            "tokens_per_day": int(os.getenv("OPENAI_DAILY_TOKEN_LIMIT", "2000000")),
            "monthly_budget_usd": float(os.getenv("OPENAI_MONTHLY_BUDGET_USD", "100")),
            "warning_threshold": float(os.getenv("OPENAI_WARNING_THRESHOLD_PERCENT", "80")) / 100,
            "critical_threshold": float(os.getenv("OPENAI_CRITICAL_THRESHOLD_PERCENT", "95")) / 100
        }
        
        # Usage tracking
        self.usage_stats = {
            "requests_today": 0,
            "requests_this_minute": 0,
            "tokens_used": 0,
            "tokens_today": 0,
            "tokens_this_minute": 0,
            "errors_count": 0,
            "last_error_time": None,
            "quota_reset_time": None,
            "daily_cost_usd": 0.0
        }
        
        # Enhanced tracking
        self.enhanced_stats = {
            "models_used": defaultdict(int),  # model -> request count
            "api_methods_used": defaultdict(int),  # api_method -> request count
            "tokens_by_model": defaultdict(int),  # model -> total tokens
            "errors_by_method": defaultdict(int),  # api_method -> error count
            "recent_activity": [],  # Last 10 API calls with details
            "daily_limits_configured": False
        }
        
        # Real usage data integration
        self.usage_client = None
        self.real_usage_data = None
        self.last_real_usage_fetch = None
        self.real_usage_cache_minutes = 5  # Cache real data for 5 minutes
    
    def add_websocket(self, websocket):
        """Add WebSocket connection for real-time updates"""
        self.connected_websockets.append(websocket)
        logger.info(f"✅ WebSocket added to quota tracker: {len(self.connected_websockets)} connections")
    
    def remove_websocket(self, websocket):
        """Remove WebSocket connection"""
        if websocket in self.connected_websockets:
            self.connected_websockets.remove(websocket)
            logger.info(f"🔄 WebSocket removed from quota tracker: {len(self.connected_websockets)} connections")
    
    async def broadcast_status_update(self, status_data: Dict):
        """Broadcast status update to all connected WebSockets"""
        if not self.connected_websockets:
            return
            
        message = json.dumps({
            "type": "quota_update",
            "data": status_data,
            "timestamp": datetime.now().isoformat()
        })
        
        # Remove disconnected websockets
        active_websockets = []
        for ws in self.connected_websockets:
            try:
                await ws.send_text(message)
                active_websockets.append(ws)
            except:
                # WebSocket is disconnected, skip it
                pass
        
        self.connected_websockets = active_websockets
        logger.info(f"📡 Broadcasted quota update to {len(active_websockets)} clients")
    
    def record_request(self, success: bool = True, tokens_used: int = 0):
        """Record an API request"""
        now = datetime.now()
        minute_key = now.replace(second=0, microsecond=0)
        day_key = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Reset minute counters if new minute
        if hasattr(self, '_last_minute_key') and self._last_minute_key != minute_key:
            self.usage_stats["requests_this_minute"] = 0
            self.usage_stats["tokens_this_minute"] = 0
        self._last_minute_key = minute_key
        
        # Reset daily counters if new day
        if hasattr(self, '_last_day_key') and self._last_day_key != day_key:
            self.usage_stats["requests_today"] = 0
            self.usage_stats["tokens_today"] = 0
            self.usage_stats["daily_cost_usd"] = 0.0
        self._last_day_key = day_key
        
        if success:
            self.request_counts[minute_key] += 1
            self.request_counts[day_key] += 1
            self.usage_stats["requests_this_minute"] += 1
            self.usage_stats["requests_today"] += 1
            self.usage_stats["tokens_used"] += tokens_used
            self.usage_stats["tokens_today"] += tokens_used
            self.usage_stats["tokens_this_minute"] += tokens_used
            
            # Estimate cost (rough approximation - adjust based on your model pricing)
            # GPT-4: ~$0.03/1K tokens, GPT-3.5: ~$0.002/1K tokens
            estimated_cost = (tokens_used / 1000) * 0.01  # Average estimate
            self.usage_stats["daily_cost_usd"] += estimated_cost
        else:
            self.error_counts[minute_key] += 1
            self.usage_stats["errors_count"] += 1
            self.usage_stats["last_error_time"] = now.isoformat()
        
        # Update status
        self._update_quota_status()
    
    def record_openai_error(self, error_type: str, error_message: str = ""):
        """Record OpenAI-specific errors"""
        logger.warning(f"🚨 OpenAI API Error: {error_type} - {error_message}")
        
        # Check error type and message for quota issues
        error_lower = error_type.lower()
        message_lower = error_message.lower()
        
        # Check for rate limiting
        if "ratelimit" in error_lower or "rate" in error_lower or "429" in str(error_type):
            self.current_status = QuotaStatus.RATE_LIMITED
            logger.info(f"📊 Status changed to RATE_LIMITED due to: {error_type}")
        # Check for quota exceeded
        elif "insufficient_quota" in message_lower or "quota" in error_lower or "exceeded" in message_lower:
            self.current_status = QuotaStatus.QUOTA_EXCEEDED
            logger.info(f"📊 Status changed to QUOTA_EXCEEDED due to: {error_message}")
        
        # Record the failed request
        self.record_request(success=False)
        
        # Broadcast immediate update
        asyncio.create_task(self.broadcast_status_update(self.get_status_data()))
    
    def _update_quota_status(self):
        """Update current quota status based on usage"""
        # Don't override critical statuses set by error handling
        if self.current_status in [QuotaStatus.RATE_LIMITED, QuotaStatus.QUOTA_EXCEEDED]:
            return
            
        current_minute = datetime.now().replace(second=0, microsecond=0)
        requests_this_minute = self.request_counts.get(current_minute, 0)
        
        previous_status = self.current_status
        
        if requests_this_minute >= self.rate_limits["requests_per_minute"]:
            self.current_status = QuotaStatus.RATE_LIMITED
        elif requests_this_minute >= self.rate_limits["requests_per_minute"] * 0.9:
            self.current_status = QuotaStatus.WARNING
        elif self.usage_stats["requests_today"] >= self.rate_limits["requests_per_day"] * 0.9:
            self.current_status = QuotaStatus.WARNING
        else:
            self.current_status = QuotaStatus.NORMAL
        
        # Broadcast if status changed
        if previous_status != self.current_status:
            asyncio.create_task(self.broadcast_status_update(self.get_status_data()))
    
    def record_enhanced_usage(self, success: bool, tokens_used: int = 0, model: str = "unknown", 
                             api_method: str = "unknown", error: str = None):
        """Record enhanced usage with model and API method tracking"""
        now = datetime.now()
        
        # Track models and API methods
        if success:
            self.enhanced_stats["models_used"][model] += 1
            self.enhanced_stats["api_methods_used"][api_method] += 1
            self.enhanced_stats["tokens_by_model"][model] += tokens_used
        else:
            self.enhanced_stats["errors_by_method"][api_method] += 1
        
        # Track recent activity (keep last 10)
        activity_entry = {
            "timestamp": now.isoformat(),
            "model": model,
            "api_method": api_method,
            "tokens_used": tokens_used,
            "success": success,
            "error": error if not success else None
        }
        
        self.enhanced_stats["recent_activity"].insert(0, activity_entry)
        if len(self.enhanced_stats["recent_activity"]) > 10:
            self.enhanced_stats["recent_activity"] = self.enhanced_stats["recent_activity"][:10]
    
    def get_status_data(self) -> Dict[str, Any]:
        """Get comprehensive quota status data"""
        current_minute = datetime.now().replace(second=0, microsecond=0)
        requests_this_minute = self.request_counts.get(current_minute, 0)
        
        return {
            "status": self.current_status.value,
            "requests_per_minute": {
                "current": requests_this_minute,
                "limit": self.rate_limits["requests_per_minute"],
                "percentage": (requests_this_minute / self.rate_limits["requests_per_minute"]) * 100,
                "unit": "requests"
            },
            "requests_per_day": {
                "current": self.usage_stats["requests_today"],
                "limit": self.rate_limits["requests_per_day"],
                "percentage": (self.usage_stats["requests_today"] / self.rate_limits["requests_per_day"]) * 100,
                "unit": "requests"
            },
            "tokens_per_minute": {
                "current": self.usage_stats.get("tokens_this_minute", 0),
                "limit": self.rate_limits["tokens_per_minute"],
                "percentage": (self.usage_stats.get("tokens_this_minute", 0) / self.rate_limits["tokens_per_minute"]) * 100,
                "unit": "tokens"
            },
            "errors": {
                "count": self.usage_stats["errors_count"],
                "last_error": self.usage_stats["last_error_time"]
            },
            "last_updated": datetime.now().isoformat()
        }
    
    async def fetch_real_usage_data(self) -> Optional[Dict[str, Any]]:
        """Fetch real usage data from OpenAI Usage API"""
        try:
            # Check cache
            if self.last_real_usage_fetch:
                cache_age = (datetime.now() - self.last_real_usage_fetch).total_seconds() / 60
                if cache_age < self.real_usage_cache_minutes and self.real_usage_data:
                    return self.real_usage_data
            
            # Initialize client if needed
            if not self.usage_client:
                self.usage_client = get_usage_client()
            
            # Fetch real data
            logger.info("📊 Fetching real usage data from OpenAI API...")
            
            # Get today's usage
            today_usage = await self.usage_client.get_today_usage()
            
            # Get budget status
            budget_status = await self.usage_client.check_budget_status()
            
            # Get model comparison for the last 7 days
            model_comparison = await self.usage_client.get_model_comparison(days=7)
            
            # Store and cache
            self.real_usage_data = {
                "today": {
                    "total_cost": today_usage.total_cost,
                    "total_tokens": today_usage.total_tokens,
                    "total_requests": today_usage.total_requests,
                    "hourly_breakdown": today_usage.hourly_breakdown
                },
                "budget": budget_status,
                "model_comparison": model_comparison,
                "last_updated": datetime.now().isoformat()
            }
            
            self.last_real_usage_fetch = datetime.now()
            
            # Update internal cost estimate with real data
            if today_usage.total_cost > 0:
                # Calibrate our estimates
                estimated_vs_real_ratio = self.usage_stats["daily_cost_usd"] / today_usage.total_cost
                if 0.5 < estimated_vs_real_ratio < 2.0:  # Sanity check
                    logger.info(f"📊 Calibrating estimates: ratio {estimated_vs_real_ratio:.2f}")
            
            return self.real_usage_data
            
        except Exception as e:
            logger.warning(f"Could not fetch real usage data: {e}")
            return None
    
    def get_enhanced_status_data(self) -> Dict[str, Any]:
        """Get enhanced status data with model and API method breakdown"""
        # Convert defaultdicts to regular dicts for JSON serialization
        models_data = {}
        for model, count in self.enhanced_stats["models_used"].items():
            models_data[model] = {
                "request_count": count,
                "tokens_used": self.enhanced_stats["tokens_by_model"].get(model, 0)
            }
        
        api_methods_data = {}
        for method, count in self.enhanced_stats["api_methods_used"].items():
            api_methods_data[method] = {
                "request_count": count,
                "error_count": self.enhanced_stats["errors_by_method"].get(method, 0)
            }
        
        enhanced_data = {
            "enhanced_tracking": {
                "models_breakdown": models_data,
                "api_methods_breakdown": api_methods_data,
                "recent_activity": self.enhanced_stats["recent_activity"][:5],  # Last 5 for UI
                "total_unique_models": len(models_data),
                "total_unique_methods": len(api_methods_data)
            }
        }
        
        # Add real usage data if available
        if self.real_usage_data:
            enhanced_data["real_usage"] = self.real_usage_data
        
        return enhanced_data
    
    def get_notification_data(self) -> Dict[str, Any]:
        """Get user-friendly notification data"""
        status = self.current_status
        status_data = self.get_status_data()
        
        notifications = {
            "show_notification": status != QuotaStatus.NORMAL,
            "level": "info",
            "title": "",
            "message": "",
            "suggested_actions": [],
            "status_data": status_data
        }
        
        if status == QuotaStatus.WARNING:
            notifications.update({
                "level": "warning",
                "title": "API Quota Warning",
                "message": "OpenAI API usage is approaching limits. Some features may slow down.",
                "suggested_actions": [
                    "Consider upgrading your OpenAI plan",
                    "Reduce API-intensive operations",
                    "Monitor usage in real-time"
                ]
            })
        elif status == QuotaStatus.RATE_LIMITED:
            notifications.update({
                "level": "warning",
                "title": "Rate Limited",
                "message": "OpenAI API rate limit reached. Please wait a moment before trying again.",
                "suggested_actions": [
                    "Wait 60 seconds before retrying",
                    "Reduce concurrent API requests",
                    "Check your OpenAI dashboard"
                ]
            })
        elif status == QuotaStatus.QUOTA_EXCEEDED:
            notifications.update({
                "level": "error",
                "title": "Quota Exceeded",
                "message": "OpenAI API quota exceeded. Some features may be limited until quota resets.",
                "suggested_actions": [
                    "Upgrade your OpenAI plan immediately",
                    "Wait for quota reset (usually monthly)",
                    "Contact support if this persists"
                ]
            })
        elif status == QuotaStatus.DEGRADED:
            notifications.update({
                "level": "warning",
                "title": "Degraded Service",
                "message": "API service is operating with reduced capacity due to quota constraints.",
                "suggested_actions": [
                    "Some features may be temporarily unavailable",
                    "Essential functions continue to work",
                    "Consider upgrading for full functionality"
                ]
            })
        
        return notifications
    
    def can_make_request(self) -> bool:
        """Check if API request can be made"""
        return self.current_status not in [QuotaStatus.QUOTA_EXCEEDED, QuotaStatus.RATE_LIMITED]
    
    def cleanup_old_data(self):
        """Clean up old request count data"""
        cutoff = datetime.now() - timedelta(days=1)
        
        # Remove old entries
        old_keys = [key for key in self.request_counts.keys() if key < cutoff]
        for key in old_keys:
            del self.request_counts[key]
        
        old_error_keys = [key for key in self.error_counts.keys() if key < cutoff]
        for key in old_error_keys:
            del self.error_counts[key]
        
        logger.info(f"🧹 Cleaned up {len(old_keys)} old quota tracking entries")

class MultiWorkspaceQuotaManager:
    """
    Manages quota tracking for multiple workspaces with proper isolation
    """
    
    def __init__(self):
        self.workspace_trackers: Dict[str, WorkspaceQuotaTracker] = {}
        self._lock = None  # For thread safety if needed
    
    def get_tracker(self, workspace_id: str) -> WorkspaceQuotaTracker:
        """Get or create quota tracker for a workspace"""
        if not workspace_id:
            workspace_id = "global"  # Fallback for non-workspace requests
            
        if workspace_id not in self.workspace_trackers:
            self.workspace_trackers[workspace_id] = WorkspaceQuotaTracker(workspace_id)
            logger.info(f"📊 Created new quota tracker for workspace: {workspace_id}")
        
        return self.workspace_trackers[workspace_id]
    
    def remove_tracker(self, workspace_id: str):
        """Remove quota tracker for a workspace"""
        if workspace_id in self.workspace_trackers:
            del self.workspace_trackers[workspace_id]
            logger.info(f"🗑️ Removed quota tracker for workspace: {workspace_id}")
    
    def get_all_trackers(self) -> Dict[str, WorkspaceQuotaTracker]:
        """Get all workspace trackers for monitoring"""
        return self.workspace_trackers.copy()

# Global manager instance
quota_manager = MultiWorkspaceQuotaManager()

# Backward compatibility - global tracker
quota_tracker = quota_manager.get_tracker("global")