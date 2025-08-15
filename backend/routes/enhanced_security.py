"""
Enhanced Security API Routes
Threat Intelligence, Vulnerability Management, and Security Metrics endpoints
"""
import asyncio
import logging
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Body
from pydantic import BaseModel

from services.threat_intelligence import (
    ThreatIntelligenceEngine, ThreatFeed, ThreatSeverity, 
    ThreatAlert, CVEData, ZeroDayIndicator
)
from services.vulnerability_management import (
    VulnerabilityManager, VulnerabilityStatus, VulnerabilityPriority,
    Asset, Vulnerability, RiskMetrics
)
from services.security_metrics import (
    SecurityMetricsEngine, ComplianceFramework, SecurityScore,
    ComplianceResult, SecurityKPI, RiskTrend
)

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/enhanced", tags=["enhanced-security"])

# Global instances (would be properly initialized in app factory)
threat_intel_engine: Optional[ThreatIntelligenceEngine] = None
vuln_manager: Optional[VulnerabilityManager] = None
metrics_engine: Optional[SecurityMetricsEngine] = None

def init_enhanced_security_services():
    """Initialize enhanced security services"""
    global threat_intel_engine, vuln_manager, metrics_engine
    
    try:
        threat_intel_engine = ThreatIntelligenceEngine()
        vuln_manager = VulnerabilityManager()
        metrics_engine = SecurityMetricsEngine()
        
        logger.info("Enhanced security services initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize enhanced security services: {e}")

@router.get("/health")
async def health_check():
    """Health check endpoint for enhanced security services"""
    return {
        "status": "healthy",
        "services": {
            "threat_intelligence": threat_intel_engine is not None,
            "vulnerability_management": vuln_manager is not None,
            "security_metrics": metrics_engine is not None
        }
    }

@router.get("/status")
async def get_status():
    """Get status of enhanced security services"""
    return {
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "threat_intelligence": "initialized" if threat_intel_engine else "not_initialized",
            "vulnerability_management": "initialized" if vuln_manager else "not_initialized",
            "security_metrics": "initialized" if metrics_engine else "not_initialized"
        }
    }

# Initialize services when module is imported
init_enhanced_security_services()

# Export router
__all__ = ['router']
