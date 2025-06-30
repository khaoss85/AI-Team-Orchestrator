"""
Asset-Driven WebSocket Integration (Pillar 10: Real-Time Thinking & Explainability)
Real-time WebSocket handlers for asset progress, quality updates, and thinking process visualization.
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Set, List, Any, Optional
from uuid import UUID
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, HTTPException
from fastapi.websockets import WebSocketState

from models import AssetArtifact, QualityValidation, WorkspaceGoal
from database import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter()

# WebSocket connection management
class AssetWebSocketManager:
    """Manage WebSocket connections for asset-driven real-time updates"""
    
    def __init__(self):
        # Active connections by workspace
        self.workspace_connections: Dict[str, Set[WebSocket]] = {}
        # Asset-specific connections
        self.asset_connections: Dict[str, Set[WebSocket]] = {}
        # Quality monitoring connections
        self.quality_connections: Dict[str, Set[WebSocket]] = {}
        # General system connections
        self.system_connections: Set[WebSocket] = set()
        
        logger.info("🔗 AssetWebSocketManager initialized")

    async def connect_workspace(self, websocket: WebSocket, workspace_id: str):
        """Connect to workspace asset updates"""
        await websocket.accept()
        
        if workspace_id not in self.workspace_connections:
            self.workspace_connections[workspace_id] = set()
        
        self.workspace_connections[workspace_id].add(websocket)
        
        # Send initial connection confirmation
        await self.send_to_websocket(websocket, {
            "type": "connection_established",
            "workspace_id": workspace_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to asset progress updates"
        })
        
        logger.info(f"🔗 WebSocket connected to workspace assets: {workspace_id}")

    async def connect_quality(self, websocket: WebSocket, workspace_id: str):
        """Connect to quality monitoring updates"""
        await websocket.accept()
        
        if workspace_id not in self.quality_connections:
            self.quality_connections[workspace_id] = set()
        
        self.quality_connections[workspace_id].add(websocket)
        
        # Send initial quality status
        await self.send_to_websocket(websocket, {
            "type": "quality_connection_established",
            "workspace_id": workspace_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to quality monitoring updates"
        })
        
        logger.info(f"🛡️ WebSocket connected to quality monitoring: {workspace_id}")

    async def connect_asset(self, websocket: WebSocket, artifact_id: str):
        """Connect to specific asset updates"""
        await websocket.accept()
        
        if artifact_id not in self.asset_connections:
            self.asset_connections[artifact_id] = set()
        
        self.asset_connections[artifact_id].add(websocket)
        
        # Send current asset status
        await self.send_current_asset_status(websocket, artifact_id)
        
        logger.info(f"📦 WebSocket connected to asset: {artifact_id}")

    async def disconnect(self, websocket: WebSocket):
        """Disconnect WebSocket from all subscriptions"""
        try:
            # Remove from all connection sets
            for connections in self.workspace_connections.values():
                connections.discard(websocket)
            
            for connections in self.asset_connections.values():
                connections.discard(websocket)
            
            for connections in self.quality_connections.values():
                connections.discard(websocket)
            
            self.system_connections.discard(websocket)
            
            if websocket.client_state != WebSocketState.DISCONNECTED:
                await websocket.close()
                
            logger.info("🔌 WebSocket disconnected")
            
        except Exception as e:
            logger.error(f"Error during WebSocket disconnect: {e}")

    async def send_to_websocket(self, websocket: WebSocket, data: Dict[str, Any]):
        """Send data to a specific WebSocket"""
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(json.dumps(data))
            else:
                logger.warning("Attempted to send to disconnected WebSocket")
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")

    async def broadcast_to_workspace(self, workspace_id: str, data: Dict[str, Any]):
        """Broadcast data to all workspace connections"""
        if workspace_id not in self.workspace_connections:
            return
        
        disconnected = set()
        for websocket in self.workspace_connections[workspace_id]:
            try:
                await self.send_to_websocket(websocket, data)
            except Exception as e:
                logger.error(f"Failed to send to workspace WebSocket: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected sockets
        for websocket in disconnected:
            self.workspace_connections[workspace_id].discard(websocket)

    async def broadcast_quality_update(self, workspace_id: str, data: Dict[str, Any]):
        """Broadcast quality update to quality monitoring connections"""
        if workspace_id not in self.quality_connections:
            return
        
        disconnected = set()
        for websocket in self.quality_connections[workspace_id]:
            try:
                await self.send_to_websocket(websocket, data)
            except Exception as e:
                logger.error(f"Failed to send quality update: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected sockets
        for websocket in disconnected:
            self.quality_connections[workspace_id].discard(websocket)

    async def broadcast_asset_update(self, artifact_id: str, data: Dict[str, Any]):
        """Broadcast update to specific asset connections"""
        if artifact_id not in self.asset_connections:
            return
        
        disconnected = set()
        for websocket in self.asset_connections[artifact_id]:
            try:
                await self.send_to_websocket(websocket, data)
            except Exception as e:
                logger.error(f"Failed to send asset update: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected sockets
        for websocket in disconnected:
            self.asset_connections[artifact_id].discard(websocket)

    async def send_current_asset_status(self, websocket: WebSocket, artifact_id: str):
        """Send current status of a specific asset"""
        try:
            supabase = get_supabase_client()
            
            # Get current artifact status
            artifact_response = supabase.table("asset_artifacts") \
                .select("*") \
                .eq("id", artifact_id) \
                .execute()
            
            if artifact_response.data:
                artifact_data = artifact_response.data[0]
                
                await self.send_to_websocket(websocket, {
                    "type": "current_asset_status",
                    "artifact_id": artifact_id,
                    "artifact": artifact_data,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
        except Exception as e:
            logger.error(f"Failed to send current asset status: {e}")

    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        return {
            "workspace_connections": {
                workspace_id: len(connections)
                for workspace_id, connections in self.workspace_connections.items()
            },
            "quality_connections": {
                workspace_id: len(connections)
                for workspace_id, connections in self.quality_connections.items()
            },
            "asset_connections": {
                artifact_id: len(connections)
                for artifact_id, connections in self.asset_connections.items()
            },
            "total_connections": (
                sum(len(conns) for conns in self.workspace_connections.values()) +
                sum(len(conns) for conns in self.quality_connections.values()) +
                sum(len(conns) for conns in self.asset_connections.values()) +
                len(self.system_connections)
            )
        }

# Global WebSocket manager instance
websocket_manager = AssetWebSocketManager()

# === WEBSOCKET ENDPOINTS ===

@router.websocket("/ws/assets/{workspace_id}")
async def websocket_asset_progress(websocket: WebSocket, workspace_id: str):
    """WebSocket endpoint for real-time asset progress updates"""
    try:
        await websocket_manager.connect_workspace(websocket, workspace_id)
        
        while True:
            try:
                # Keep connection alive and handle any incoming messages
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle ping/pong for connection health
                if message.get("type") == "ping":
                    await websocket_manager.send_to_websocket(websocket, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                # Handle subscription updates
                elif message.get("type") == "subscribe_goal":
                    goal_id = message.get("goal_id")
                    if goal_id:
                        await send_goal_progress_update(websocket, goal_id)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in asset WebSocket loop: {e}")
                break
                
    except Exception as e:
        logger.error(f"Asset WebSocket connection error: {e}")
    finally:
        await websocket_manager.disconnect(websocket)

@router.websocket("/ws/quality/{workspace_id}")
async def websocket_quality_monitoring(websocket: WebSocket, workspace_id: str):
    """WebSocket endpoint for real-time quality monitoring updates"""
    try:
        await websocket_manager.connect_quality(websocket, workspace_id)
        
        while True:
            try:
                # Keep connection alive and handle messages
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket_manager.send_to_websocket(websocket, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif message.get("type") == "subscribe_artifact":
                    artifact_id = message.get("artifact_id")
                    if artifact_id:
                        await send_artifact_quality_status(websocket, artifact_id)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in quality WebSocket loop: {e}")
                break
                
    except Exception as e:
        logger.error(f"Quality WebSocket connection error: {e}")
    finally:
        await websocket_manager.disconnect(websocket)

@router.websocket("/ws/asset/{artifact_id}")
async def websocket_specific_asset(websocket: WebSocket, artifact_id: str):
    """WebSocket endpoint for specific asset updates"""
    try:
        await websocket_manager.connect_asset(websocket, artifact_id)
        
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket_manager.send_to_websocket(websocket, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif message.get("type") == "request_status":
                    await websocket_manager.send_current_asset_status(websocket, artifact_id)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in asset-specific WebSocket loop: {e}")
                break
                
    except Exception as e:
        logger.error(f"Asset-specific WebSocket connection error: {e}")
    finally:
        await websocket_manager.disconnect(websocket)

# === REAL-TIME UPDATE FUNCTIONS ===

async def broadcast_goal_progress_update(
    workspace_id: str, 
    goal_id: str, 
    progress: float, 
    asset_completion_rate: float,
    quality_score: float
):
    """Broadcast goal progress update to all workspace connections"""
    try:
        update_data = {
            "type": "goal_progress_update",
            "workspace_id": workspace_id,
            "goal_id": goal_id,
            "progress": progress,
            "asset_completion_rate": asset_completion_rate,
            "quality_score": quality_score,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await websocket_manager.broadcast_to_workspace(workspace_id, update_data)
        logger.info(f"📡 Broadcasted goal progress update: {goal_id}")
        
    except Exception as e:
        logger.error(f"Failed to broadcast goal progress update: {e}")

async def broadcast_artifact_quality_update(
    workspace_id: str,
    artifact_id: str,
    quality_score: float,
    status: str,
    validation_feedback: Optional[str] = None
):
    """Broadcast artifact quality update"""
    try:
        update_data = {
            "type": "artifact_quality_update",
            "workspace_id": workspace_id,
            "artifact_id": artifact_id,
            "quality_score": quality_score,
            "status": status,
            "validation_feedback": validation_feedback,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Broadcast to both workspace and quality connections
        await websocket_manager.broadcast_to_workspace(workspace_id, update_data)
        await websocket_manager.broadcast_quality_update(workspace_id, update_data)
        await websocket_manager.broadcast_asset_update(artifact_id, update_data)
        
        logger.info(f"📡 Broadcasted artifact quality update: {artifact_id}")
        
    except Exception as e:
        logger.error(f"Failed to broadcast artifact quality update: {e}")

async def broadcast_new_artifact_created(
    workspace_id: str,
    artifact: AssetArtifact
):
    """Broadcast new artifact creation"""
    try:
        update_data = {
            "type": "new_artifact_created",
            "workspace_id": workspace_id,
            "artifact": {
                "id": artifact.id,
                "artifact_name": artifact.artifact_name,
                "artifact_type": artifact.artifact_type,
                "status": artifact.status,
                "quality_score": artifact.quality_score,
                "created_at": artifact.created_at.isoformat() if artifact.created_at else None
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await websocket_manager.broadcast_to_workspace(workspace_id, update_data)
        logger.info(f"📡 Broadcasted new artifact created: {artifact.artifact_name}")
        
    except Exception as e:
        logger.error(f"Failed to broadcast new artifact creation: {e}")

async def broadcast_quality_validation_complete(
    workspace_id: str,
    validation: QualityValidation
):
    """Broadcast quality validation completion"""
    try:
        update_data = {
            "type": "quality_validation_complete",
            "workspace_id": workspace_id,
            "validation": {
                "id": validation.id,
                "artifact_id": validation.artifact_id,
                "score": validation.score,
                "passed": validation.passed,
                "feedback": validation.feedback,
                "validated_at": validation.validated_at.isoformat() if validation.validated_at else None
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await websocket_manager.broadcast_quality_update(workspace_id, update_data)
        logger.info(f"📡 Broadcasted quality validation complete: {validation.id}")
        
    except Exception as e:
        logger.error(f"Failed to broadcast quality validation completion: {e}")

async def broadcast_ai_enhancement_complete(
    workspace_id: str,
    artifact_id: str,
    enhanced_content: str,
    new_quality_score: float
):
    """Broadcast AI enhancement completion"""
    try:
        update_data = {
            "type": "ai_enhancement_complete",
            "workspace_id": workspace_id,
            "artifact_id": artifact_id,
            "enhanced_content": enhanced_content[:500] + "..." if len(enhanced_content) > 500 else enhanced_content,
            "new_quality_score": new_quality_score,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await websocket_manager.broadcast_quality_update(workspace_id, update_data)
        await websocket_manager.broadcast_asset_update(artifact_id, update_data)
        
        logger.info(f"📡 Broadcasted AI enhancement complete: {artifact_id}")
        
    except Exception as e:
        logger.error(f"Failed to broadcast AI enhancement completion: {e}")

async def broadcast_human_review_requested(
    workspace_id: str,
    artifact: AssetArtifact,
    review_reason: str
):
    """Broadcast human review request"""
    try:
        update_data = {
            "type": "human_review_requested",
            "workspace_id": workspace_id,
            "artifact": {
                "id": artifact.id,
                "artifact_name": artifact.artifact_name,
                "artifact_type": artifact.artifact_type,
                "quality_score": artifact.quality_score,
                "status": artifact.status
            },
            "review_reason": review_reason,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await websocket_manager.broadcast_quality_update(workspace_id, update_data)
        logger.info(f"📡 Broadcasted human review requested: {artifact.artifact_name}")
        
    except Exception as e:
        logger.error(f"Failed to broadcast human review request: {e}")

# === HELPER FUNCTIONS ===

async def send_goal_progress_update(websocket: WebSocket, goal_id: str):
    """Send current goal progress to specific WebSocket"""
    try:
        supabase = get_supabase_client()
        
        # Get goal with asset completion data
        goal_response = supabase.table("workspace_goals") \
            .select("""
                *,
                goal_asset_requirements(
                    *,
                    asset_artifacts(*)
                )
            """) \
            .eq("id", goal_id) \
            .execute()
        
        if goal_response.data:
            goal_data = goal_response.data[0]
            
            # Calculate asset completion rate
            requirements = goal_data.get('goal_asset_requirements', [])
            total_requirements = len(requirements)
            
            if total_requirements > 0:
                approved_artifacts = 0
                total_quality = 0.0
                
                for req in requirements:
                    artifacts = req.get('asset_artifacts', [])
                    approved = [a for a in artifacts if a.get('status') == 'approved']
                    if approved:
                        approved_artifacts += 1
                        total_quality += max(a.get('quality_score', 0) for a in approved)
                
                asset_completion_rate = (approved_artifacts / total_requirements) * 100
                avg_quality = total_quality / total_requirements if total_requirements > 0 else 0.0
            else:
                asset_completion_rate = 0.0
                avg_quality = 0.0
            
            await websocket_manager.send_to_websocket(websocket, {
                "type": "goal_progress_update",
                "goal_id": goal_id,
                "progress": goal_data.get('progress_percentage', 0),
                "asset_completion_rate": asset_completion_rate,
                "quality_score": avg_quality,
                "timestamp": datetime.utcnow().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Failed to send goal progress update: {e}")

async def send_artifact_quality_status(websocket: WebSocket, artifact_id: str):
    """Send current artifact quality status to specific WebSocket"""
    try:
        supabase = get_supabase_client()
        
        # Get artifact with latest validation
        artifact_response = supabase.table("asset_artifacts") \
            .select("""
                *,
                quality_validations(*)
            """) \
            .eq("id", artifact_id) \
            .execute()
        
        if artifact_response.data:
            artifact_data = artifact_response.data[0]
            validations = artifact_data.get('quality_validations', [])
            
            # Get latest validation
            latest_validation = None
            if validations:
                latest_validation = max(validations, key=lambda v: v.get('validated_at', ''))
            
            await websocket_manager.send_to_websocket(websocket, {
                "type": "artifact_quality_status",
                "artifact_id": artifact_id,
                "artifact": artifact_data,
                "latest_validation": latest_validation,
                "timestamp": datetime.utcnow().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Failed to send artifact quality status: {e}")

# === WEBSOCKET STATS ENDPOINT ===

@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    try:
        stats = await websocket_manager.get_connection_stats()
        return {
            "status": "active",
            "timestamp": datetime.utcnow().isoformat(),
            "connections": stats
        }
    except Exception as e:
        logger.error(f"Failed to get WebSocket stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Export the websocket manager for use in other modules
__all__ = [
    "websocket_manager", 
    "broadcast_goal_progress_update",
    "broadcast_artifact_quality_update", 
    "broadcast_new_artifact_created",
    "broadcast_quality_validation_complete",
    "broadcast_ai_enhancement_complete",
    "broadcast_human_review_requested"
]