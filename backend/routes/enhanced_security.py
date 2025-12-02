"""
Enhanced Security API Routes
Threat Intelligence, Vulnerability Management, and Security Metrics endpoints
FastAPI Implementation
"""
import asyncio
import logging
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Body, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from services.security.threat_intelligence import (
    ThreatIntelligenceEngine, ThreatFeed, ThreatSeverity, 
    ThreatAlert, CVEData, ZeroDayIndicator
)
from services.scanning.vulnerability_management import (
    VulnerabilityManager, VulnerabilityStatus, VulnerabilityPriority,
    Asset, Vulnerability, RiskMetrics
)
from services.security.security_metrics import (
    SecurityMetricsEngine, ComplianceFramework, SecurityScore,
    ComplianceResult, SecurityKPI, RiskTrend
)
from services.scanning.penetration_testing import (
    PenetrationTestingEngine, PentestType, AttackPath
)
from models.user import User
from services.auth.auth_service import AuthService

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/enhanced", tags=["enhanced-security"])
security = HTTPBearer()
auth_service = AuthService()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    return await auth_service.get_current_user(credentials)


# Global service instances
threat_intel_engine: Optional[ThreatIntelligenceEngine] = None
vuln_manager: Optional[VulnerabilityManager] = None
metrics_engine: Optional[SecurityMetricsEngine] = None
pentest_engine: Optional[PenetrationTestingEngine] = None

def init_enhanced_security_services():
    """Initialize all enhanced security services"""
    global threat_intel_engine, vuln_manager, metrics_engine, pentest_engine
    
    try:
        # Initialize Threat Intelligence Engine
        threat_intel_engine = ThreatIntelligenceEngine()
        logger.info("✅ Threat Intelligence Engine initialized")
        
        # Initialize Vulnerability Manager
        vuln_manager = VulnerabilityManager()
        logger.info("✅ Vulnerability Manager initialized")
        
        # Initialize Security Metrics Engine
        metrics_engine = SecurityMetricsEngine()
        logger.info("✅ Security Metrics Engine initialized")
        
        # Initialize Penetration Testing Engine
        pentest_engine = PenetrationTestingEngine()
        logger.info("✅ Penetration Testing Engine initialized")
        
        logger.info("🚀 All Enhanced Security services initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Enhanced Security services: {e}")
        return False

# Pydantic models for request/response
class ThreatScanRequest(BaseModel):
    repository_path: str
    scan_types: List[str] = ["cve", "secrets", "malware"]
    severity_threshold: str = "medium"

class ComplianceAssessmentRequest(BaseModel):
    framework: str
    scope: List[str] = ["security", "privacy"]
    include_remediation: bool = True

# FastAPI Routes
@router.get("/status")
async def get_status():
    """Get enhanced security system status"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "threat_intelligence": threat_intel_engine is not None,
            "vulnerability_management": vuln_manager is not None,
            "security_metrics": metrics_engine is not None,
            "penetration_testing": pentest_engine is not None
        }
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "enhanced_security_api"
    }

# FastAPI route implementations for enhanced security features
@router.get("/threat-intel/feeds")
async def get_threat_intelligence_feeds():
    """Get threat intelligence feeds"""
    try:
        if threat_intel_engine:
            feeds = await threat_intel_engine.get_available_feeds()
            return {"feeds": feeds, "status": "active"}
        return {"feeds": [], "status": "unavailable"}
    except Exception as e:
        logger.error(f"Error getting threat intel feeds: {e}")
        raise HTTPException(status_code=500, detail="Failed to get threat intelligence feeds")

@router.post("/threat-intel/analyze")
async def analyze_threat_intelligence(request: Dict[str, Any]):
    """Analyze threat intelligence for indicators"""
    try:
        if threat_intel_engine:
            indicators = request.get("indicators", [])
            results = await threat_intel_engine.analyze_indicators(indicators)
            return {"results": results, "analyzed_count": len(indicators)}
        return {"results": [], "analyzed_count": 0}
    except Exception as e:
        logger.error(f"Error analyzing threat intel: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze threat intelligence")

@router.get("/vuln-mgmt/dashboard")
async def get_vulnerability_dashboard():
    """Get vulnerability management dashboard data"""
    try:
        if vuln_manager:
            dashboard_data = await vuln_manager.get_dashboard_data()
            return dashboard_data
        return {"vulnerabilities": [], "metrics": {}, "trends": []}
    except Exception as e:
        logger.error(f"Error getting vulnerability dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to get vulnerability dashboard")

@router.post("/vuln-mgmt/scan")
async def initiate_vulnerability_scan(request: Dict[str, Any]):
    """Initiate a vulnerability scan"""
    try:
        if vuln_manager:
            scan_config = request.get("config", {})
            result = await vuln_manager.initiate_scan(scan_config)
            return {"scan_id": result.get("scan_id"), "status": "initiated"}
        return {"scan_id": None, "status": "unavailable"}
    except Exception as e:
        logger.error(f"Error initiating vulnerability scan: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate vulnerability scan")

@router.get("/metrics/security-score")
async def get_security_score():
    """Get overall security score and metrics"""
    try:
        if metrics_engine:
            score_data = await metrics_engine.calculate_security_score()
            return score_data
        return {"score": 0, "metrics": {}, "recommendations": []}
    except Exception as e:
        logger.error(f"Error getting security score: {e}")
        raise HTTPException(status_code=500, detail="Failed to get security score")

@router.post("/pentest/execute")
async def execute_penetration_test(request: Dict[str, Any]):
    """Execute penetration testing suite"""
    try:
        if pentest_engine:
            test_config = request.get("config", {})
            result = await pentest_engine.execute_tests(test_config)
            return {"test_id": result.get("test_id"), "status": "executing"}
        return {"test_id": None, "status": "unavailable"}
    except Exception as e:
        logger.error(f"Error executing penetration test: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute penetration test")

@router.get("/compliance/frameworks")
async def get_compliance_frameworks():
    """Get available compliance frameworks"""
    try:
        frameworks = [
            {"id": "pci_dss", "name": "PCI DSS", "version": "4.0"},
            {"id": "iso_27001", "name": "ISO 27001", "version": "2022"},
            {"id": "nist_csf", "name": "NIST Cybersecurity Framework", "version": "2.0"},
            {"id": "sox", "name": "Sarbanes-Oxley", "version": "2002"},
            {"id": "gdpr", "name": "GDPR", "version": "2018"}
        ]
        return {"frameworks": frameworks}
    except Exception as e:
        logger.error(f"Error getting compliance frameworks: {e}")
        raise HTTPException(status_code=500, detail="Failed to get compliance frameworks")

# Initialize services when module is imported
init_enhanced_security_services()

# Export router
__all__ = ['router']
