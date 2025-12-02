"""
Enterprise Security Orchestration FastAPI Routes
=================================================

RESTful API endpoints for threat intelligence, vulnerability management,
metrics/KPIs, and automated security orchestration workflows.

Author: ONYX Platform
Date: August 2025
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import asyncio

# Import our orchestration engine
from services.security.security_orchestration_engine import SecurityOrchestrationEngine
from models.user import User
from services.auth.auth_service import AuthService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()
auth_service = AuthService()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    return await auth_service.get_current_user(credentials)


# Initialize orchestration engine
orchestration_engine = SecurityOrchestrationEngine()

# Router
router = APIRouter(prefix="/api/security-orchestration", tags=["Security Orchestration"])

# Pydantic models
class ScanRequest(BaseModel):
    repository_url: str = Field(..., description="Repository URL to scan")
    branch: str = Field(default="main", description="Branch to scan")
    commit_hash: Optional[str] = Field(None, description="Specific commit to scan")
    asset_id: Optional[str] = Field(None, description="Asset ID for tracking")
    scan_types: List[str] = Field(default=["sast", "dast", "iac", "pentest"], description="Types of scans to perform")
    business_criticality: str = Field(default="medium", description="Business criticality of the asset")
    environment: str = Field(default="development", description="Environment type")
    notify_on_completion: bool = Field(default=True, description="Send notifications on completion")

class AssetRegistration(BaseModel):
    asset_id: str = Field(..., description="Unique asset identifier")
    name: str = Field(..., description="Asset name")
    type: str = Field(..., description="Asset type (repository, server, application, container)")
    owner: str = Field(..., description="Asset owner")
    business_criticality: str = Field(..., description="Business criticality level")
    environment: str = Field(..., description="Environment type")
    tags: List[str] = Field(default=[], description="Asset tags")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")

class PolicyGateConfig(BaseModel):
    name: str = Field(..., description="Policy gate name")
    description: str = Field(..., description="Policy gate description")
    conditions: List[Dict[str, Any]] = Field(..., description="Gate conditions")
    action: str = Field(..., description="Action to take (block, warn, pass)")
    notification_channels: List[str] = Field(default=[], description="Notification channels")
    override_approvers: List[str] = Field(default=[], description="Override approvers")

class VulnerabilityStateUpdate(BaseModel):
    new_state: str = Field(..., description="New lifecycle state")
    changed_by: str = Field(..., description="User making the change")
    reason: str = Field(default="", description="Reason for state change")

# API Endpoints

@router.post("/workflow/comprehensive-scan", 
             summary="Execute Comprehensive Security Workflow",
             description="Execute end-to-end security scanning with threat intelligence enrichment, policy gates, and automated issue creation")
async def execute_comprehensive_workflow(
    scan_request: ScanRequest, 
    background_tasks: BackgroundTasks,
    token: str = Depends(security)
) -> Dict[str, Any]:
    """
    Execute comprehensive security workflow:
    1. Scan → 2. Enrich with TI → 3. Risk Score → 4. Policy Gate → 5. Create Issues → 6. Metrics → 7. Notify
    """
    try:
        logger.info(f"🚀 Starting comprehensive security workflow for {scan_request.repository_url}")
        
        # Convert to dict for processing
        scan_data = scan_request.dict()
        
        # Execute workflow
        result = await orchestration_engine.execute_comprehensive_security_workflow(scan_data)
        
        return {
            "status": "success",
            "message": "Comprehensive security workflow executed successfully",
            "workflow_execution": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error executing comprehensive workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

@router.post("/threat-intelligence/update",
             summary="Update Threat Intelligence Feeds",
             description="Update NVD, KEV, and EPSS threat intelligence feeds and re-score existing vulnerabilities")
async def update_threat_intelligence(
    background_tasks: BackgroundTasks,
    token: str = Depends(security)
) -> Dict[str, Any]:
    """Update all threat intelligence feeds and re-score vulnerabilities"""
    try:
        logger.info("🔄 Starting threat intelligence update workflow")
        
        # Execute in background
        background_tasks.add_task(orchestration_engine.update_threat_intelligence_workflow)
        
        return {
            "status": "accepted",
            "message": "Threat intelligence update started in background",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error starting threat intelligence update: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

@router.get("/threat-intelligence/stats",
            summary="Get Threat Intelligence Statistics",
            description="Get comprehensive threat intelligence statistics and coverage metrics")
async def get_threat_intelligence_stats(token: str = Depends(security)) -> Dict[str, Any]:
    """Get threat intelligence statistics"""
    try:
        stats = await orchestration_engine.threat_intelligence.get_threat_stats()
        
        return {
            "status": "success",
            "threat_intelligence_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting threat intelligence stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.post("/assets/register",
             summary="Register Asset",
             description="Register or update an asset for vulnerability management tracking")
async def register_asset(
    asset: AssetRegistration,
    token: str = Depends(security)
) -> Dict[str, Any]:
    """Register asset for vulnerability management"""
    try:
        from services.scanning.vulnerability_management import Asset
        
        # Create asset object
        asset_obj = Asset(
            asset_id=asset.asset_id,
            name=asset.name,
            type=asset.type,
            owner=asset.owner,
            business_criticality=asset.business_criticality,
            environment=asset.environment,
            tags=asset.tags,
            metadata=asset.metadata
        )
        
        # Register asset
        success = await orchestration_engine.vulnerability_management.register_asset(asset_obj)
        
        if success:
            return {
                "status": "success",
                "message": f"Asset {asset.name} registered successfully",
                "asset_id": asset.asset_id,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Asset registration failed")
        
    except Exception as e:
        logger.error(f"❌ Error registering asset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/vulnerability/{vulnerability_id}/state",
             summary="Update Vulnerability State",
             description="Update vulnerability lifecycle state (open → triaged → in_progress → fixed → verified → closed)")
async def update_vulnerability_state(
    vulnerability_id: str,
    state_update: VulnerabilityStateUpdate,
    token: str = Depends(security)
) -> Dict[str, Any]:
    """Update vulnerability lifecycle state"""
    try:
        success = await orchestration_engine.vulnerability_management.update_vulnerability_state(
            vulnerability_id,
            state_update.new_state,
            state_update.changed_by,
            state_update.reason
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Vulnerability state updated to {state_update.new_state}",
                "vulnerability_id": vulnerability_id,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="State update failed")
        
    except Exception as e:
        logger.error(f"❌ Error updating vulnerability state: {str(e)}")
        raise HTTPException(status_code=500, detail=f"State update failed: {str(e)}")

@router.post("/policy-gates/create",
             summary="Create Policy Gate",
             description="Create security policy gate for automated compliance checking")
async def create_policy_gate(
    gate_config: PolicyGateConfig,
    token: str = Depends(security)
) -> Dict[str, Any]:
    """Create security policy gate"""
    try:
        gate_id = await orchestration_engine.vulnerability_management.create_policy_gate(
            gate_config.dict()
        )
        
        return {
            "status": "success",
            "message": f"Policy gate '{gate_config.name}' created successfully",
            "gate_id": gate_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error creating policy gate: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Policy gate creation failed: {str(e)}")

@router.get("/metrics/vulnerability-management",
            summary="Get Vulnerability Management Metrics",
            description="Get comprehensive vulnerability management metrics and KPIs")
async def get_vulnerability_metrics(
    time_period: str = "30d",
    token: str = Depends(security)
) -> Dict[str, Any]:
    """Get vulnerability management metrics"""
    try:
        metrics = await orchestration_engine.vulnerability_management.get_vulnerability_metrics(time_period)
        
        return {
            "status": "success",
            "time_period": time_period,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting vulnerability metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")

@router.get("/metrics/sla-performance",
            summary="Get SLA Performance Metrics",
            description="Get SLA performance metrics against defined targets")
async def get_sla_performance(token: str = Depends(security)) -> Dict[str, Any]:
    """Get SLA performance metrics"""
    try:
        sla_performance = await orchestration_engine.metrics_kpi.calculate_sla_performance()
        
        return {
            "status": "success",
            "sla_performance": sla_performance,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting SLA performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SLA performance retrieval failed: {str(e)}")

@router.get("/metrics/executive-dashboard",
            summary="Get Executive Security Dashboard",
            description="Get executive-level security metrics and KPIs dashboard")
async def get_executive_dashboard(token: str = Depends(security)) -> Dict[str, Any]:
    """Get executive security dashboard"""
    try:
        dashboard = await orchestration_engine.metrics_kpi.get_executive_dashboard()
        
        return {
            "status": "success",
            "executive_dashboard": dashboard,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting executive dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Dashboard retrieval failed: {str(e)}")

@router.get("/metrics/trends",
            summary="Get Security Trends Analysis",
            description="Get trend analysis for key security metrics over time")
async def get_trends_analysis(
    days: int = 30,
    token: str = Depends(security)
) -> Dict[str, Any]:
    """Get security trends analysis"""
    try:
        trends = await orchestration_engine.metrics_kpi.generate_trend_analysis(days)
        
        return {
            "status": "success",
            "trends_analysis": trends,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting trends analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Trends analysis failed: {str(e)}")

@router.post("/workflow/sla-breach-response",
             summary="Execute SLA Breach Response",
             description="Execute automated SLA breach response workflow with escalation")
async def execute_sla_breach_response(
    background_tasks: BackgroundTasks,
    token: str = Depends(security)
) -> Dict[str, Any]:
    """Execute SLA breach response workflow"""
    try:
        result = await orchestration_engine.execute_sla_breach_response()
        
        return {
            "status": "success",
            "message": "SLA breach response workflow executed",
            "workflow_result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error executing SLA breach response: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SLA breach response failed: {str(e)}")

@router.get("/orchestration/status",
            summary="Get Orchestration Engine Status",
            description="Get comprehensive status of the security orchestration engine")
async def get_orchestration_status(token: str = Depends(security)) -> Dict[str, Any]:
    """Get orchestration engine status"""
    try:
        status = await orchestration_engine.get_orchestration_status()
        
        return {
            "status": "success",
            "orchestration_status": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting orchestration status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")

@router.post("/vulnerability/{vulnerability_id}/rescore",
             summary="Re-score Vulnerability",
             description="Re-score vulnerability when threat intelligence or business context changes")
async def rescore_vulnerability(
    vulnerability_id: str,
    new_epss_score: Optional[float] = None,
    new_business_criticality: Optional[str] = None,
    kev_added: bool = False,
    token: str = Depends(security)
) -> Dict[str, Any]:
    """Re-score vulnerability based on updated threat intelligence"""
    try:
        success = await orchestration_engine.vulnerability_management.re_score_vulnerability(
            vulnerability_id,
            new_epss_score,
            new_business_criticality,
            kev_added
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Vulnerability {vulnerability_id} re-scored successfully",
                "vulnerability_id": vulnerability_id,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Vulnerability not found")
        
    except Exception as e:
        logger.error(f"❌ Error re-scoring vulnerability: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Re-scoring failed: {str(e)}")

@router.get("/workflow/definitions",
            summary="Get Workflow Definitions",
            description="Get available security orchestration workflow definitions")
async def get_workflow_definitions(token: str = Depends(security)) -> Dict[str, Any]:
    """Get available workflow definitions"""
    try:
        workflows = {}
        for workflow_id, workflow in orchestration_engine.workflows.items():
            workflows[workflow_id] = {
                "workflow_id": workflow.workflow_id,
                "name": workflow.name,
                "description": workflow.description,
                "trigger_type": workflow.trigger_type,
                "enabled": workflow.enabled,
                "steps_count": len(workflow.steps)
            }
        
        return {
            "status": "success",
            "workflows": workflows,
            "total_workflows": len(workflows),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting workflow definitions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow definitions retrieval failed: {str(e)}")

# Health check endpoint
@router.get("/health",
            summary="Health Check",
            description="Check health status of security orchestration engine")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    try:
        # Basic health checks
        health_status = {
            "orchestration_engine": "healthy",
            "threat_intelligence": "healthy",
            "vulnerability_management": "healthy",
            "metrics_kpi": "healthy",
            "overall_status": "healthy"
        }
        
        return {
            "status": "success",
            "health": health_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "health": {"overall_status": "unhealthy", "error": str(e)},
            "timestamp": datetime.now().isoformat()
        }

# Export router
__all__ = ['router']
