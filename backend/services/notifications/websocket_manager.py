"""
WebSocket Manager for ONYX Security Intelligence Platform
Handles real-time notifications and broadcast messages to connected clients
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time notifications.
    Supports broadcasting to all clients or specific users.
    """
    
    def __init__(self):
        # All active connections (WebSocket -> connection info)
        self.active_connections: Dict[WebSocket, Dict[str, Any]] = {}
        # User ID to WebSocket mapping for targeted messages
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        
        async with self._lock:
            # Store connection with metadata
            self.active_connections[websocket] = {
                "user_id": user_id,
                "connected_at": datetime.now(timezone.utc),
                "client_host": websocket.client.host if websocket.client else "unknown"
            }
            
            # Map user to connection if authenticated
            if user_id:
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = set()
                self.user_connections[user_id].add(websocket)
        
        client_host = websocket.client.host if websocket.client else "unknown"
        logger.info(f"WebSocket connected: {client_host} (user: {user_id or 'anonymous'})")
        
        # Send welcome message
        await self.send_personal(websocket, {
            "type": "connection",
            "data": {
                "message": "Connected to ONYX Platform",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "authenticated": user_id is not None
            }
        })
    
    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        async with self._lock:
            if websocket in self.active_connections:
                connection_info = self.active_connections[websocket]
                user_id = connection_info.get("user_id")
                
                # Remove from user mapping
                if user_id and user_id in self.user_connections:
                    self.user_connections[user_id].discard(websocket)
                    if not self.user_connections[user_id]:
                        del self.user_connections[user_id]
                
                # Remove from active connections
                del self.active_connections[websocket]
                
                client_host = connection_info.get("client_host", "unknown")
                logger.info(f"WebSocket disconnected: {client_host} (user: {user_id or 'anonymous'})")
    
    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send message to a specific WebSocket connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")
            await self.disconnect(websocket)
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send message to all connections of a specific user"""
        if user_id not in self.user_connections:
            return
        
        disconnected = []
        for websocket in self.user_connections[user_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to user {user_id}: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected sockets
        for ws in disconnected:
            await self.disconnect(ws)
    
    async def broadcast(self, message: dict, exclude: Optional[WebSocket] = None):
        """Broadcast message to all connected clients"""
        disconnected = []
        
        for websocket in list(self.active_connections.keys()):
            if websocket == exclude:
                continue
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to broadcast: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected sockets
        for ws in disconnected:
            await self.disconnect(ws)
    
    async def broadcast_to_authenticated(self, message: dict):
        """Broadcast message only to authenticated users"""
        disconnected = []
        
        for websocket, info in list(self.active_connections.items()):
            if not info.get("user_id"):
                continue
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to broadcast to authenticated: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected sockets
        for ws in disconnected:
            await self.disconnect(ws)
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)
    
    def get_authenticated_count(self) -> int:
        """Get number of authenticated connections"""
        return sum(1 for info in self.active_connections.values() if info.get("user_id"))
    
    # ===== Notification Helper Methods =====
    
    async def notify_scan_started(self, scan_id: str, project_name: str, user_id: Optional[str] = None):
        """Notify about scan start"""
        message = {
            "type": "scan_update",
            "data": {
                "scan_id": scan_id,
                "project_name": project_name,
                "status": "started",
                "message": f"Security scan started for {project_name}",
                "progress": 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        if user_id:
            await self.send_to_user(user_id, message)
        else:
            await self.broadcast(message)
    
    async def notify_scan_progress(self, scan_id: str, project_name: str, progress: int, 
                                    current_scanner: str, user_id: Optional[str] = None):
        """Notify about scan progress"""
        message = {
            "type": "scan_update",
            "data": {
                "scan_id": scan_id,
                "project_name": project_name,
                "status": "running",
                "progress": progress,
                "current_scanner": current_scanner,
                "message": f"Scanning: {current_scanner}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        if user_id:
            await self.send_to_user(user_id, message)
        else:
            await self.broadcast(message)
    
    async def notify_scan_completed(self, scan_id: str, project_name: str, 
                                     total_findings: int, findings_by_severity: dict,
                                     user_id: Optional[str] = None):
        """Notify about scan completion"""
        critical = findings_by_severity.get("critical", 0)
        high = findings_by_severity.get("high", 0)
        
        severity_text = ""
        if critical > 0:
            severity_text = f" - {critical} critical issues found!"
        elif high > 0:
            severity_text = f" - {high} high severity issues found"
        
        message = {
            "type": "scan_update",
            "data": {
                "scan_id": scan_id,
                "project_name": project_name,
                "status": "completed",
                "progress": 100,
                "total_findings": total_findings,
                "findings_by_severity": findings_by_severity,
                "message": f"Scan completed for {project_name}{severity_text}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        if user_id:
            await self.send_to_user(user_id, message)
        else:
            await self.broadcast(message)
    
    async def notify_scan_failed(self, scan_id: str, project_name: str, 
                                  error_message: str, user_id: Optional[str] = None):
        """Notify about scan failure"""
        message = {
            "type": "scan_update",
            "data": {
                "scan_id": scan_id,
                "project_name": project_name,
                "status": "failed",
                "progress": 0,
                "error": error_message,
                "message": f"Scan failed for {project_name}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        if user_id:
            await self.send_to_user(user_id, message)
        else:
            await self.broadcast(message)
    
    async def notify_critical_vulnerability(self, project_name: str, vulnerability_title: str,
                                             severity: str, user_id: Optional[str] = None):
        """Notify about critical/high vulnerability found"""
        message = {
            "type": "security_alert",
            "data": {
                "project_name": project_name,
                "alert_type": "vulnerability",
                "severity": severity,
                "title": vulnerability_title,
                "message": f"{severity.upper()} vulnerability found: {vulnerability_title}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        if user_id:
            await self.send_to_user(user_id, message)
        else:
            await self.broadcast(message)
    
    async def notify_login_alert(self, user_id: str, device: str, location: str, ip_address: str):
        """Notify user about new login"""
        message = {
            "type": "security_alert",
            "data": {
                "alert_type": "new_login",
                "device": device,
                "location": location,
                "ip_address": ip_address,
                "message": f"New login detected from {device}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        await self.send_to_user(user_id, message)


# Global WebSocket manager instance
ws_manager = ConnectionManager()
