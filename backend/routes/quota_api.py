#!/usr/bin/env python3
"""
Quota API Routes
Provides REST API endpoints and WebSocket support for OpenAI quota monitoring
"""

import logging
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, Any, Optional
import asyncio
import json

from services.openai_quota_tracker import quota_tracker, quota_manager, QuotaStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quota", tags=["quota"])

def _get_availability_message(status: QuotaStatus, can_make_request: bool) -> str:
    """
    Get user-friendly message based on quota status and availability
    """
    if status == QuotaStatus.NORMAL:
        return "API is available and operating normally"
    elif status == QuotaStatus.WARNING:
        return "API usage is high but requests are still allowed"
    elif status == QuotaStatus.RATE_LIMITED:
        return "Rate limit reached - please wait before making more requests"
    elif status == QuotaStatus.QUOTA_EXCEEDED:
        return "Quota exceeded - API access limited"
    elif status == QuotaStatus.DEGRADED:
        return "Service operating with reduced capacity"
    else:
        return "API status unknown" if not can_make_request else "API available"

@router.get("/status")
async def get_quota_status(workspace_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get comprehensive quota status including usage stats and limits
    """
    try:
        tracker = quota_manager.get_tracker(workspace_id) if workspace_id else quota_tracker
        status_data = tracker.get_status_data()
        logger.info(f"📊 Quota status requested for workspace {workspace_id}: {status_data['status']}")
        return {
            "success": True,
            "data": status_data,
            "workspace_id": workspace_id
        }
    except Exception as e:
        logger.error(f"❌ Error getting quota status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get quota status: {str(e)}")

@router.get("/notifications")
async def get_quota_notifications() -> Dict[str, Any]:
    """
    Get user-friendly quota notifications and suggested actions
    """
    try:
        notifications = quota_tracker.get_notification_data()
        logger.info(f"🔔 Quota notifications requested: {notifications['level'] if notifications['show_notification'] else 'none'}")
        return {
            "success": True,
            "data": notifications
        }
    except Exception as e:
        logger.error(f"❌ Error getting quota notifications: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get quota notifications: {str(e)}")

@router.get("/usage")
async def get_quota_usage(period: str = "current") -> Dict[str, Any]:
    """
    Get detailed quota usage statistics
    """
    try:
        status_data = quota_tracker.get_status_data()
        
        usage_data = {
            "period": period,
            "requests_per_minute": status_data["requests_per_minute"],
            "requests_per_day": status_data["requests_per_day"],
            "errors": status_data["errors"],
            "last_updated": status_data["last_updated"],
            "status": status_data["status"]
        }
        
        logger.info(f"📈 Quota usage requested for period: {period}")
        return {
            "success": True,
            "data": usage_data
        }
    except Exception as e:
        logger.error(f"❌ Error getting quota usage: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get quota usage: {str(e)}")

@router.get("/check")
async def check_quota_availability() -> Dict[str, Any]:
    """
    Quick check if API requests can be made
    """
    try:
        can_make_request = quota_tracker.can_make_request()
        current_status = quota_tracker.current_status
        
        result = {
            "can_make_request": can_make_request,
            "status": current_status.value,
            "message": _get_availability_message(current_status, can_make_request)
        }
        
        # Add suggested actions based on status
        if current_status == QuotaStatus.WARNING:
            result["suggested_actions"] = ["Monitor usage", "Consider reducing API calls"]
        elif current_status == QuotaStatus.RATE_LIMITED:
            result["wait_seconds"] = 60
            result["suggested_actions"] = ["Wait before retrying", "Reduce request rate"]
        elif current_status == QuotaStatus.QUOTA_EXCEEDED:
            result["suggested_actions"] = ["Upgrade OpenAI plan", "Wait for quota reset"]
        
        logger.info(f"🔍 Quota availability check: {can_make_request} (status: {current_status.value})")
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"❌ Error checking quota availability: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check quota availability: {str(e)}")

@router.post("/reset")
async def reset_quota_stats(admin_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Reset quota statistics (admin/testing only)
    """
    # Admin key validation from environment
    expected_admin_key = os.getenv("QUOTA_ADMIN_RESET_KEY")
    if not expected_admin_key:
        raise HTTPException(status_code=503, detail="Admin functionality not configured")
    
    if admin_key != expected_admin_key:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Reset usage stats
        quota_tracker.usage_stats = {
            "requests_today": 0,
            "requests_this_minute": 0,
            "tokens_used": 0,
            "errors_count": 0,
            "last_error_time": None,
            "quota_reset_time": None
        }
        
        # Reset counts
        quota_tracker.request_counts.clear()
        quota_tracker.error_counts.clear()
        quota_tracker.current_status = QuotaStatus.NORMAL
        
        # Broadcast reset
        await quota_tracker.broadcast_status_update(quota_tracker.get_status_data())
        
        logger.info("🔄 Quota statistics reset by admin")
        return {
            "success": True,
            "message": "Quota statistics reset successfully"
        }
    except Exception as e:
        logger.error(f"❌ Error resetting quota stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset quota stats: {str(e)}")

@router.websocket("/ws")
async def quota_websocket_endpoint(websocket: WebSocket, workspace_id: Optional[str] = None):
    """
    WebSocket endpoint for real-time quota monitoring
    Provides live updates on quota status changes for specific workspace
    """
    await websocket.accept()
    
    # Get appropriate tracker for workspace
    tracker = quota_manager.get_tracker(workspace_id) if workspace_id else quota_tracker
    tracker.add_websocket(websocket)
    
    logger.info(f"🔌 WebSocket connected for quota monitoring (workspace: {workspace_id})")
    
    try:
        # Send initial status
        initial_status = tracker.get_status_data()
        await websocket.send_text(json.dumps({
            "type": "quota_initial",
            "data": initial_status
        }))
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for message with timeout to send periodic ping
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle incoming messages
                try:
                    data = json.loads(message)
                    if data.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                    elif data.get("type") == "request_status":
                        current_status = tracker.get_status_data()
                        await websocket.send_text(json.dumps({
                            "type": "quota_update",
                            "data": current_status
                        }))
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Invalid JSON received from WebSocket: {message}")
                
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except:
                    break  # Connection is dead
                    
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected from quota monitoring (workspace: {workspace_id})")
    except Exception as e:
        logger.error(f"❌ WebSocket quota error: {e}")
    finally:
        tracker.remove_websocket(websocket)

def _get_availability_message(status: QuotaStatus, can_make_request: bool) -> str:
    """Get user-friendly availability message"""
    if status == QuotaStatus.NORMAL:
        return "All systems operational. API requests proceeding normally."
    elif status == QuotaStatus.WARNING:
        return "API usage approaching limits. Requests may slow down soon."
    elif status == QuotaStatus.RATE_LIMITED:
        return "Rate limit reached. Please wait before making more requests."
    elif status == QuotaStatus.QUOTA_EXCEEDED:
        return "Quota exceeded. Some features are temporarily limited."
    elif status == QuotaStatus.DEGRADED:
        return "Service operating with reduced capacity due to quota constraints."
    else:
        return f"Unknown status: {status}"