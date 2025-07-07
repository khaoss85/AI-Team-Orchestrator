# backend/routes/websocket.py
"""
WebSocket endpoint per aggiornamenti real-time dello stato dei task
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import logging
import asyncio
from datetime import datetime
from websockets.exceptions import ConnectionClosedError

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # workspace_id -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # task_id -> set of websockets
        self.task_subscribers: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, workspace_id: str, already_accepted: bool = False):
        # 🔧 FIX: Only accept WebSocket if not already accepted
        if not already_accepted:
            await websocket.accept()
        
        if workspace_id not in self.active_connections:
            self.active_connections[workspace_id] = set()
        self.active_connections[workspace_id].add(websocket)
        
        logger.info(f"WebSocket connected for workspace {workspace_id}")
        
        # Send connection confirmation with error handling
        try:
            await websocket.send_text(json.dumps({
                "type": "connection_confirmed",
                "workspace_id": workspace_id,
                "timestamp": datetime.now().isoformat()
            }))
        except Exception as e:
            logger.warning(f"Failed to send connection confirmation: {e}")
            # Don't raise, just log the warning
    
    def disconnect(self, websocket: WebSocket, workspace_id: str):
        if workspace_id in self.active_connections:
            self.active_connections[workspace_id].discard(websocket)
            if not self.active_connections[workspace_id]:
                del self.active_connections[workspace_id]
        
        # Remove from task subscribers
        for task_id, subscribers in list(self.task_subscribers.items()):
            subscribers.discard(websocket)
            if not subscribers:
                del self.task_subscribers[task_id]
        
        logger.info(f"WebSocket disconnected from workspace {workspace_id}")
    
    async def subscribe_to_task(self, websocket: WebSocket, task_id: str):
        """Subscribe websocket to specific task updates"""
        if task_id not in self.task_subscribers:
            self.task_subscribers[task_id] = set()
        self.task_subscribers[task_id].add(websocket)
        
        logger.info(f"WebSocket subscribed to task {task_id}")
    
    async def broadcast_to_workspace(self, workspace_id: str, message: dict):
        """Broadcast message to all connections in a workspace - ENHANCED with health management"""
        # 🔗 STABILITY ENHANCEMENT: Use health-aware broadcasting
        from utils.websocket_health_manager import broadcast_to_workspace_healthy
        
        # Try health-managed broadcast first
        try:
            successful_broadcasts = await broadcast_to_workspace_healthy(workspace_id, message)
            if successful_broadcasts > 0:
                logger.debug(f"📡 Health-managed broadcast: {successful_broadcasts} clients in {workspace_id}")
                return
        except Exception as e:
            logger.warning(f"Health-managed broadcast failed, falling back to legacy: {e}")
        
        # Fallback to legacy broadcast
        if workspace_id not in self.active_connections:
            return
        
        dead_connections = set()
        for websocket in self.active_connections[workspace_id]:
            try:
                # 🔧 FIX: Check WebSocket state before sending
                try:
                    if websocket.client_state.name in ['DISCONNECTED', 'CLOSED']:
                        dead_connections.add(websocket)
                        continue
                except AttributeError:
                    pass  # Some WebSocket implementations don't have client_state
                
                await websocket.send_text(json.dumps(message))
            except ConnectionClosedError as e:
                logger.debug(f"WebSocket connection closed during broadcast: {e}")
                dead_connections.add(websocket)
            except Exception as e:
                logger.error(f"Error sending message to websocket: {e}")
                dead_connections.add(websocket)
        
        # Clean up dead connections
        for dead_ws in dead_connections:
            self.active_connections[workspace_id].discard(dead_ws)
    
    async def broadcast_thinking_step(self, workspace_id: str, thinking_step: dict):
        """🧠 Broadcast real-time thinking step like Claude/o3"""
        message = {
            "type": "thinking_step",
            "workspace_id": workspace_id,
            "data": thinking_step,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_workspace(workspace_id, message)
        logger.debug(f"🧠 Broadcasted thinking step to workspace {workspace_id}: {thinking_step.get('step_type', 'unknown')}")
    
    async def broadcast_goal_decomposition_start(self, workspace_id: str, goal_data: dict):
        """🎯 Broadcast goal decomposition start like Claude thinking"""
        message = {
            "type": "goal_decomposition_start",
            "workspace_id": workspace_id,
            "data": {
                "goal_id": goal_data.get("id"),
                "goal_name": goal_data.get("description", goal_data.get("name", "Unknown Goal")),
                "status": "starting_decomposition"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_workspace(workspace_id, message)
        logger.info(f"🎯 Broadcasted goal decomposition start for workspace {workspace_id}")
    
    async def broadcast_goal_decomposition_complete(self, workspace_id: str, decomposition_result: dict):
        """✅ Broadcast goal decomposition completion"""
        message = {
            "type": "goal_decomposition_complete", 
            "workspace_id": workspace_id,
            "data": decomposition_result,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_workspace(workspace_id, message)
        logger.info(f"✅ Broadcasted goal decomposition complete for workspace {workspace_id}")
    
    async def broadcast_task_update(self, task_id: str, task_data: dict):
        """Broadcast task update to all subscribers"""
        if task_id not in self.task_subscribers:
            return
        
        message = {
            "type": "task_update",
            "task_id": task_id,
            "data": task_data,
            "timestamp": datetime.now().isoformat()
        }
        
        dead_connections = set()
        for websocket in self.task_subscribers[task_id]:
            try:
                # 🔧 FIX: Check WebSocket state before sending task update
                try:
                    if websocket.client_state.name in ['DISCONNECTED', 'CLOSED']:
                        dead_connections.add(websocket)
                        continue
                except AttributeError:
                    pass  # Some WebSocket implementations don't have client_state
                
                await websocket.send_text(json.dumps(message))
            except ConnectionClosedError as e:
                logger.debug(f"WebSocket connection closed during task update: {e}")
                dead_connections.add(websocket)
            except Exception as e:
                logger.error(f"Error sending task update to websocket: {e}")
                dead_connections.add(websocket)
        
        # Clean up dead connections
        for dead_ws in dead_connections:
            self.task_subscribers[task_id].discard(dead_ws)

# Global connection manager
manager = ConnectionManager()

router = APIRouter()

@router.websocket("/ws/{workspace_id}")
async def websocket_endpoint(websocket: WebSocket, workspace_id: str):
    # 🔗 STABILITY ENHANCEMENT: Use advanced health management
    from utils.websocket_health_manager import (
        register_websocket_connection, 
        unregister_websocket_connection,
        update_websocket_activity
    )
    import uuid
    
    client_id = str(uuid.uuid4())
    
    # Accept WebSocket connection
    await websocket.accept()
    
    # Register with health manager
    if not await register_websocket_connection(websocket, workspace_id, client_id):
        await websocket.close(code=1008, reason="Connection limit reached")
        return
    
    # Also register with legacy manager for backwards compatibility (WebSocket already accepted)
    await manager.connect(websocket, workspace_id, already_accepted=True)
    
    try:
        logger.info(f"🔗 WebSocket client {client_id} connected to workspace {workspace_id}")
        
        while True:
            # Listen for client messages with timeout - reduced for faster detection
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                await update_websocket_activity(client_id)
                
                message = json.loads(data)
                
                # Handle heartbeat response
                if message.get("type") == "heartbeat_response":
                    logger.debug(f"💓 Heartbeat response from {client_id}")
                    continue
                
                # Handle task subscription
                elif message.get("type") == "subscribe_task":
                    task_id = message.get("task_id")
                    if task_id:
                        await manager.subscribe_to_task(websocket, task_id)
                        await websocket.send_json({
                            "type": "subscription_confirmed",
                            "task_id": task_id,
                            "client_id": client_id
                        })
                
                # Handle other message types
                else:
                    logger.debug(f"📩 Received message from {client_id}: {message.get('type', 'unknown')}")
            
            except asyncio.TimeoutError:
                # Send ping to check connection health
                try:
                    # 🔧 FIX: Use proper ping with timeout and proper close frame handling
                    pong_waiter = await websocket.ping()
                    await asyncio.wait_for(pong_waiter, timeout=10.0)
                    await update_websocket_activity(client_id)
                except asyncio.TimeoutError:
                    logger.warning(f"🔌 Ping timeout for client {client_id}, disconnecting")
                    break
                except Exception as e:
                    logger.warning(f"🔌 Ping failed for client {client_id}: {e}, disconnecting")
                    break
            
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket client {client_id} disconnected normally")
    except Exception as e:
        logger.error(f"❌ WebSocket error for client {client_id}: {e}")
    finally:
        # 🔧 FIX: Proper WebSocket close with close frame handling
        try:
            # Send proper close frame if connection is still alive
            if websocket.client_state.name not in ['DISCONNECTED', 'CLOSED']:
                await websocket.close(code=1000, reason="Server shutdown")
        except Exception as e:
            logger.debug(f"WebSocket close frame error (expected): {e}")
        
        # Clean up both managers
        await unregister_websocket_connection(client_id, "endpoint_exit")
        manager.disconnect(websocket, workspace_id)

# Helper function to broadcast task updates (to be called from executor.py)
async def broadcast_task_status_update(task_id: str, task_data: dict):
    """Call this function when a task status changes"""
    await manager.broadcast_task_update(task_id, task_data)

# Helper function to broadcast workspace updates
async def broadcast_workspace_update(workspace_id: str, update_type: str, data: dict):
    """Call this function for general workspace updates"""
    message = {
        "type": update_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast_to_workspace(workspace_id, message)

# 🧠 Real-time Thinking Broadcast Functions (Claude/o3 style)
async def broadcast_thinking_step(workspace_id: str, thinking_step: dict):
    """🧠 Broadcast real-time thinking step updates"""
    await manager.broadcast_thinking_step(workspace_id, thinking_step)

async def broadcast_goal_decomposition_start(workspace_id: str, goal_data: dict):
    """🎯 Broadcast goal decomposition start"""
    await manager.broadcast_goal_decomposition_start(workspace_id, goal_data)

async def broadcast_goal_decomposition_complete(workspace_id: str, decomposition_result: dict):
    """✅ Broadcast goal decomposition completion"""
    await manager.broadcast_goal_decomposition_complete(workspace_id, decomposition_result)