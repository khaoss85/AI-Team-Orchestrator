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

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # workspace_id -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # task_id -> set of websockets
        self.task_subscribers: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, workspace_id: str):
        await websocket.accept()
        
        if workspace_id not in self.active_connections:
            self.active_connections[workspace_id] = set()
        self.active_connections[workspace_id].add(websocket)
        
        logger.info(f"WebSocket connected for workspace {workspace_id}")
        
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_confirmed",
            "workspace_id": workspace_id,
            "timestamp": datetime.now().isoformat()
        }))
    
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
        """Broadcast message to all connections in a workspace"""
        if workspace_id not in self.active_connections:
            return
        
        dead_connections = set()
        for websocket in self.active_connections[workspace_id]:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to websocket: {e}")
                dead_connections.add(websocket)
        
        # Clean up dead connections
        for dead_ws in dead_connections:
            self.active_connections[workspace_id].discard(dead_ws)
    
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
                await websocket.send_text(json.dumps(message))
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
    await manager.connect(websocket, workspace_id)
    
    try:
        while True:
            # Listen for client messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "subscribe_task":
                task_id = message.get("task_id")
                if task_id:
                    await manager.subscribe_to_task(websocket, task_id)
                    await websocket.send_text(json.dumps({
                        "type": "subscription_confirmed",
                        "task_id": task_id
                    }))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, workspace_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
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