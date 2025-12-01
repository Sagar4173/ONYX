"""
Notification Services Package
Provides email, WebSocket, and push notification functionality for ONYX Platform

Structure:
- service.py - Main email service implementation  
- email_service.py - Legacy email service (backward compatibility)
- notification_service.py - General notification handling
- notifier.py - Notification dispatch service
- websocket_manager.py - Real-time WebSocket connections
- templates/ - Modular email template components
"""

from .service import EmailService, email_service
from .notification_service import NotificationService, notification_service
from .notifier import notification_service as notifier_service
from .websocket_manager import ConnectionManager, ws_manager

__all__ = [
    'EmailService',
    'email_service',
    'NotificationService',
    'notification_service',
    'notifier_service',
    'ConnectionManager',
    'ws_manager',
]

