# backend/utils/websocket_health_manager.py
"""
🔗 WEBSOCKET STABILITY: Advanced Connection Health Manager

Provides proactive heartbeat, connection monitoring, and automatic cleanup
to prevent ConnectionClosedError and maintain real-time update reliability.
"""

import asyncio
import time
import logging
from typing import Dict, Set, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

logger = logging.getLogger(__name__)

class ConnectionState(Enum):
    """WebSocket connection states"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    HEARTBEAT_PENDING = "heartbeat_pending"
    RECONNECTING = "reconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"

@dataclass
class ConnectionInfo:
    """Enhanced connection information with health tracking"""
    websocket: WebSocket
    workspace_id: str
    client_id: str
    connected_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    state: ConnectionState = ConnectionState.CONNECTED
    heartbeat_failures: int = 0
    message_count: int = 0
    error_count: int = 0
    reconnection_count: int = 0
    
    @property
    def age_seconds(self) -> float:
        """Get connection age in seconds"""
        return time.time() - self.connected_at
    
    @property
    def idle_seconds(self) -> float:
        """Get idle time since last activity"""
        return time.time() - self.last_activity
    
    @property
    def is_healthy(self) -> bool:
        """Check if connection is healthy"""
        return (
            self.state == ConnectionState.CONNECTED and
            self.heartbeat_failures < 3 and
            self.idle_seconds < 180  # 3 minutes max idle - reduced from 5 minutes
        )

class WebSocketHealthManager:
    """
    🚀 ADVANCED WEBSOCKET HEALTH MANAGEMENT
    
    Features:
    - Proactive heartbeat system with configurable intervals
    - Automatic dead connection detection and cleanup
    - Connection health monitoring and metrics
    - Graceful reconnection support
    - Connection state persistence
    """
    
    def __init__(
        self,
        heartbeat_interval: int = 20,  # seconds - reduced for faster detection
        connection_timeout: int = 45,  # seconds - reduced from 60
        max_heartbeat_failures: int = 2,  # reduced from 3 for faster cleanup
        max_connections_per_workspace: int = 10,  # 🔧 FIX: Reduced to prevent memory bloat
        max_total_connections: int = 100  # 🔧 FIX: Global connection limit
    ):
        self.connections: Dict[str, ConnectionInfo] = {}
        self.workspace_connections: Dict[str, Set[str]] = {}
        
        # Configuration
        self.heartbeat_interval = heartbeat_interval
        self.connection_timeout = connection_timeout
        self.max_heartbeat_failures = max_heartbeat_failures
        self.max_connections_per_workspace = max_connections_per_workspace
        self.max_total_connections = max_total_connections
        
        # Health monitoring
        self.health_monitor_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.running = False
        
        # Statistics
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "heartbeat_successes": 0,
            "heartbeat_failures": 0,
            "auto_disconnects": 0,
            "cleanup_operations": 0
        }
        
        logger.info(f"🔗 WebSocketHealthManager initialized: heartbeat={heartbeat_interval}s, timeout={connection_timeout}s")
    
    async def start(self):
        """Start health monitoring and heartbeat tasks"""
        if self.running:
            return
        
        self.running = True
        
        # Start background tasks
        self.health_monitor_task = asyncio.create_task(self._health_monitor_loop())
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        logger.info("🚀 WebSocket health monitoring started")
    
    async def stop(self):
        """Stop all health monitoring tasks"""
        self.running = False
        
        if self.health_monitor_task:
            self.health_monitor_task.cancel()
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        # Close all connections gracefully
        await self._cleanup_all_connections()
        
        logger.info("🔗 WebSocket health monitoring stopped")
    
    async def register_connection(
        self, 
        websocket: WebSocket, 
        workspace_id: str, 
        client_id: str
    ) -> bool:
        """
        Register a new WebSocket connection with health tracking
        
        Returns False if connection should be rejected (e.g., too many connections)
        """
        try:
            # 🔧 FIX: Check global connection limit first
            if len(self.connections) >= self.max_total_connections:
                logger.warning(f"🚫 Global connection limit reached: {len(self.connections)}/{self.max_total_connections}")
                # Force cleanup of oldest connections
                await self._force_cleanup_oldest_connections(5)
                
                if len(self.connections) >= self.max_total_connections:
                    return False
            
            # Check workspace connection limits
            if workspace_id in self.workspace_connections:
                if len(self.workspace_connections[workspace_id]) >= self.max_connections_per_workspace:
                    logger.warning(f"🚫 Connection limit reached for workspace {workspace_id}")
                    return False
            
            # Create connection info
            connection_info = ConnectionInfo(
                websocket=websocket,
                workspace_id=workspace_id,
                client_id=client_id
            )
            
            # Register connection
            self.connections[client_id] = connection_info
            
            # Add to workspace tracking
            if workspace_id not in self.workspace_connections:
                self.workspace_connections[workspace_id] = set()
            self.workspace_connections[workspace_id].add(client_id)
            
            # Update statistics
            self.stats["total_connections"] += 1
            self.stats["active_connections"] = len(self.connections)
            
            logger.info(f"✅ Registered WebSocket connection: client={client_id}, workspace={workspace_id}")
            logger.info(f"📊 Active connections: {self.stats['active_connections']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to register connection {client_id}: {e}")
            return False
    
    async def unregister_connection(self, client_id: str, reason: str = "normal"):
        """Unregister a WebSocket connection"""
        try:
            if client_id not in self.connections:
                return
            
            connection_info = self.connections[client_id]
            workspace_id = connection_info.workspace_id
            
            # Remove from workspace tracking
            if workspace_id in self.workspace_connections:
                self.workspace_connections[workspace_id].discard(client_id)
                if not self.workspace_connections[workspace_id]:
                    del self.workspace_connections[workspace_id]
            
            # Remove connection
            del self.connections[client_id]
            
            # Update statistics
            self.stats["active_connections"] = len(self.connections)
            
            logger.info(f"🔌 Unregistered WebSocket connection: client={client_id}, reason={reason}")
            
        except Exception as e:
            logger.error(f"❌ Failed to unregister connection {client_id}: {e}")
    
    async def update_activity(self, client_id: str):
        """Update last activity timestamp for a connection"""
        if client_id in self.connections:
            self.connections[client_id].last_activity = time.time()
            self.connections[client_id].message_count += 1
    
    async def broadcast_to_workspace(
        self, 
        workspace_id: str, 
        message: Dict[str, Any],
        exclude_client: Optional[str] = None
    ) -> int:
        """
        Broadcast message to all healthy connections in a workspace
        
        Returns number of successful broadcasts
        """
        if workspace_id not in self.workspace_connections:
            return 0
        
        client_ids = self.workspace_connections[workspace_id].copy()
        successful_broadcasts = 0
        failed_connections = []
        
        for client_id in client_ids:
            if exclude_client and client_id == exclude_client:
                continue
            
            if client_id not in self.connections:
                continue
                
            connection_info = self.connections[client_id]
            
            # Skip unhealthy connections
            if not connection_info.is_healthy:
                continue
            
            try:
                await connection_info.websocket.send_json(message)
                await self.update_activity(client_id)
                successful_broadcasts += 1
                
            except (WebSocketDisconnect, ConnectionClosedError, ConnectionClosedOK):
                logger.debug(f"🔌 Client {client_id} disconnected during broadcast")
                failed_connections.append(client_id)
                
            except Exception as e:
                logger.error(f"❌ Broadcast failed to {client_id}: {e}")
                connection_info.error_count += 1
                failed_connections.append(client_id)
        
        # Clean up failed connections
        for client_id in failed_connections:
            await self.unregister_connection(client_id, "broadcast_failure")
        
        if failed_connections:
            logger.warning(f"🧹 Cleaned up {len(failed_connections)} failed connections")
        
        return successful_broadcasts
    
    async def _heartbeat_loop(self):
        """Proactive heartbeat loop to maintain connection health"""
        while self.running:
            try:
                current_time = time.time()
                heartbeat_tasks = []
                
                for client_id, connection_info in list(self.connections.items()):
                    # Skip if heartbeat not needed yet
                    if current_time - connection_info.last_heartbeat < self.heartbeat_interval:
                        continue
                    
                    # Create heartbeat task
                    task = self._send_heartbeat(client_id, connection_info)
                    heartbeat_tasks.append(task)
                
                # Execute heartbeats concurrently
                if heartbeat_tasks:
                    await asyncio.gather(*heartbeat_tasks, return_exceptions=True)
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"❌ Error in heartbeat loop: {e}")
                await asyncio.sleep(10)  # Back off on error
    
    async def _send_heartbeat(self, client_id: str, connection_info: ConnectionInfo):
        """Send heartbeat to a specific connection with enhanced error handling"""
        try:
            # 🔧 FIX: Check if connection still exists before heartbeat
            if client_id not in self.connections:
                return
                
            connection_info.state = ConnectionState.HEARTBEAT_PENDING
            
            heartbeat_message = {
                "type": "heartbeat",
                "timestamp": time.time(),
                "server_id": "orchestrator"
            }
            
            # 🔧 FIX: Check WebSocket state before sending
            try:
                client_state = connection_info.websocket.client_state.name
                if client_state in ['DISCONNECTED', 'CONNECTING']:
                    raise Exception(f"WebSocket in {client_state} state")
            except AttributeError:
                # Fallback for WebSocket implementations without client_state
                logger.debug(f"No client_state available for WebSocket {client_id}")
            
            await connection_info.websocket.send_json(heartbeat_message)
            
            # Update heartbeat timestamp
            connection_info.last_heartbeat = time.time()
            connection_info.state = ConnectionState.CONNECTED
            
            self.stats["heartbeat_successes"] += 1
            
        except Exception as e:
            # 🔧 FIX: Enhanced error handling with connection cleanup
            if client_id in self.connections:
                logger.warning(f"💔 Heartbeat failed for {client_id}: {e}")
                connection_info.heartbeat_failures += 1
                connection_info.error_count += 1
                connection_info.state = ConnectionState.ERROR
                
                self.stats["heartbeat_failures"] += 1
                
                # Auto-disconnect after too many failures
                if connection_info.heartbeat_failures >= self.max_heartbeat_failures:
                    logger.warning(f"🔌 Auto-disconnecting {client_id} after {connection_info.heartbeat_failures} heartbeat failures")
                    await self.unregister_connection(client_id, "heartbeat_failure")
                    self.stats["auto_disconnects"] += 1
    
    async def _health_monitor_loop(self):
        """Monitor connection health and clean up stale connections"""
        while self.running:
            try:
                await self._cleanup_stale_connections()
                await self._log_health_stats()
                await asyncio.sleep(60)  # Run every minute
                
            except Exception as e:
                logger.error(f"❌ Error in health monitor: {e}")
                await asyncio.sleep(30)
    
    async def _cleanup_stale_connections(self):
        """Clean up stale and unhealthy connections"""
        current_time = time.time()
        stale_connections = []
        
        for client_id, connection_info in list(self.connections.items()):
            # Check for various stale conditions - more aggressive cleanup
            is_stale = (
                connection_info.idle_seconds > 300 or  # 5 minutes idle - reduced from 10
                connection_info.heartbeat_failures >= self.max_heartbeat_failures or
                connection_info.error_count > 5  # reduced from 10
            )
            
            if is_stale:
                stale_connections.append(client_id)
        
        # Clean up stale connections
        for client_id in stale_connections:
            await self.unregister_connection(client_id, "stale_connection")
        
        if stale_connections:
            logger.info(f"🧹 Cleaned up {len(stale_connections)} stale connections")
            self.stats["cleanup_operations"] += 1
    
    async def _force_cleanup_oldest_connections(self, count: int):
        """🔧 FIX: Force cleanup of oldest connections to free memory"""
        try:
            # Sort connections by age (oldest first)
            connections_by_age = sorted(
                self.connections.items(),
                key=lambda x: x[1].connected_at
            )
            
            # Cleanup oldest connections
            for client_id, connection_info in connections_by_age[:count]:
                logger.warning(f"🧹 Force cleanup oldest connection: {client_id} (age: {connection_info.age_seconds:.1f}s)")
                try:
                    # Send close frame
                    if connection_info.websocket.client_state.name not in ['DISCONNECTED', 'CLOSED']:
                        await connection_info.websocket.close(code=1008, reason="Connection limit reached")
                except Exception as e:
                    logger.debug(f"Force cleanup close error: {e}")
                
                await self.unregister_connection(client_id, "force_cleanup")
                
        except Exception as e:
            logger.error(f"Force cleanup failed: {e}")
    
    async def _cleanup_all_connections(self):
        """Clean up all connections during shutdown with proper close frames"""
        for client_id in list(self.connections.keys()):
            connection_info = self.connections.get(client_id)
            if connection_info:
                try:
                    # Send proper close frame before cleanup
                    if connection_info.websocket.client_state.name not in ['DISCONNECTED', 'CLOSED']:
                        await connection_info.websocket.close(code=1001, reason="Server shutdown")
                except Exception as e:
                    logger.debug(f"Close frame error during cleanup for {client_id}: {e}")
                
            await self.unregister_connection(client_id, "shutdown")
    
    async def _log_health_stats(self):
        """Log connection health statistics"""
        if not self.connections:
            return
        
        healthy_count = sum(1 for conn in self.connections.values() if conn.is_healthy)
        avg_age = sum(conn.age_seconds for conn in self.connections.values()) / len(self.connections)
        
        logger.info(
            f"📊 WebSocket Health: {healthy_count}/{len(self.connections)} healthy, "
            f"avg_age={avg_age:.1f}s, heartbeat_success_rate="
            f"{self.stats['heartbeat_successes']/(self.stats['heartbeat_successes']+self.stats['heartbeat_failures']+1)*100:.1f}%"
        )
    
    def get_health_stats(self) -> Dict[str, Any]:
        """Get comprehensive health statistics"""
        healthy_connections = sum(1 for conn in self.connections.values() if conn.is_healthy)
        
        return {
            **self.stats,
            "healthy_connections": healthy_connections,
            "workspaces_with_connections": len(self.workspace_connections),
            "average_connection_age": sum(conn.age_seconds for conn in self.connections.values()) / len(self.connections) if self.connections else 0,
            "heartbeat_success_rate": self.stats["heartbeat_successes"] / (self.stats["heartbeat_successes"] + self.stats["heartbeat_failures"] + 1) * 100
        }

# Global health manager instance
websocket_health_manager = WebSocketHealthManager()

# Convenience functions for easy integration
async def start_websocket_health_monitoring():
    """Start WebSocket health monitoring"""
    await websocket_health_manager.start()

async def stop_websocket_health_monitoring():
    """Stop WebSocket health monitoring"""
    await websocket_health_manager.stop()

async def register_websocket_connection(websocket: WebSocket, workspace_id: str, client_id: str) -> bool:
    """Register a new WebSocket connection"""
    return await websocket_health_manager.register_connection(websocket, workspace_id, client_id)

async def unregister_websocket_connection(client_id: str, reason: str = "normal"):
    """Unregister a WebSocket connection"""
    await websocket_health_manager.unregister_connection(client_id, reason)

async def broadcast_to_workspace_healthy(workspace_id: str, message: Dict[str, Any], exclude_client: Optional[str] = None) -> int:
    """Broadcast message to healthy connections in workspace"""
    return await websocket_health_manager.broadcast_to_workspace(workspace_id, message, exclude_client)

async def update_websocket_activity(client_id: str):
    """Update activity for a WebSocket connection"""
    await websocket_health_manager.update_activity(client_id)

def get_websocket_health_stats() -> Dict[str, Any]:
    """Get WebSocket health statistics"""
    return websocket_health_manager.get_health_stats()