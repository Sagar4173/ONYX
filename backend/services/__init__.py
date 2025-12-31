"""
Services package for ONYX Security Intelligence Platform

Organized Structure:
├── auth/              # Authentication & User Management
├── scanning/          # Security Scanning Services
│   ├── base/          # Core models, config, exceptions
│   ├── scanners/      # Individual scanner implementations
│   ├── engine/        # Orchestration and workflow
│   ├── baseline/      # Baseline tracking and drift detection
│   ├── vulnerability/ # Vulnerability lifecycle management
│   ├── pentest/       # Penetration testing automation
│   ├── workflow/      # Enhanced scanning workflows
│   └── utils/         # SBOM, comparison utilities
├── compliance/        # Compliance & Governance
├── security/          # Security Services (Threat Intel, SOAR, ML)
├── ai/                # AI & Machine Learning
├── notifications/     # Email, WebSocket, Push Notifications
├── analytics/         # Metrics, Audit Logging, Data Retention
├── rules/             # Rules & Policy Engine
└── infrastructure/    # External Integrations, Project Management

Import from subpackages:
    from services.scanning.scanners import RealSecurityScanner
    from services.scanning.base import Finding, Severity
    from services.scanning.engine import ScanOrchestrator
"""

# Re-exports for convenience (optional - allows `from services import auth_service`)
from services.auth.auth_service import AuthService, auth_service
from services.auth.user_service import UserService, user_service
from services.scanning.scanners.real_scanner import RealSecurityScanner
from services.ai.ai_processor import get_ai_processor, AIProcessorError
from services.notifications.websocket_manager import ConnectionManager, ws_manager
from services.notifications.service import EmailService, email_service

__all__ = [
    "AuthService", "auth_service",
    "UserService", "user_service", 
    "RealSecurityScanner",
    "get_ai_processor", "AIProcessorError",
    "ConnectionManager", "ws_manager",
    "EmailService", "email_service",
]
