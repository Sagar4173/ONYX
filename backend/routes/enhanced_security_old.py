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
from functools import wraps

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
        
        # Connect the components
        metrics_engine.set_components(vuln_manager, threat_intel_engine)
        
        logger.info("Enhanced security services initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize enhanced security services: {e}")

# Request/Response models
class ThreatScanRequest(BaseModel):
    repository_path: str
    patterns_only: bool = False

class VulnerabilityCreateRequest(BaseModel):
    title: str
    description: str
    severity: str
    asset_id: str
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = 0.0
    epss_score: Optional[float] = 0.0
    assignee: Optional[str] = None
    tags: List[str] = []
    source: str = "manual"
    metadata: Dict[str, Any] = {}

class VulnerabilityStatusUpdate(BaseModel):
    status: str
    assignee: Optional[str] = None
    notes: str = ""

class ComplianceAssessmentRequest(BaseModel):
    assessor: str = "system"

# ===== THREAT INTELLIGENCE ENDPOINTS =====

@router.get("/threat-intel/status")
async def get_threat_intel_status():
    """Get threat intelligence system status"""
    if not threat_intel_engine:
        raise HTTPException(status_code=503, detail="Threat intelligence engine not initialized")
    
    try:
        status = await threat_intel_engine.get_system_status()
        return {
            "status": "success",
            "data": {
                "engine_status": status.engine_status.value,
                "last_feed_update": status.last_feed_update.isoformat() if status.last_feed_update else None,
                "feed_count": status.feed_count,
                "cve_count": status.cve_count,
                "active_alerts": status.active_alerts,
                "zero_day_indicators": status.zero_day_indicators,
                "database_size_mb": status.database_size_mb,
                "uptime_hours": status.uptime_hours
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get threat intel status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/threat-intel/feeds")
async def get_threat_feeds():
    """Get threat intelligence feeds"""
    if not threat_intel_engine:
        raise HTTPException(status_code=503, detail="Threat intelligence engine not initialized")
    
    try:
        feeds = await threat_intel_engine.get_active_feeds()
        return {
            "status": "success",
            "data": {
                "feeds": [
                    {
                        "name": feed.name,
                        "url": feed.url,
                        "feed_type": feed.feed_type.value,
                        "update_interval": feed.update_interval,
                        "last_updated": feed.last_updated.isoformat() if feed.last_updated else None,
                        "is_active": feed.is_active,
                        "error_count": feed.error_count
                    }
                    for feed in feeds
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get threat feeds: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/threat-intel/feeds/update")
async def update_threat_feeds(
    background_tasks: BackgroundTasks,
    feed_names: Optional[List[str]] = Body(default=None)
):
    """Update threat intelligence feeds"""
    if not threat_intel_engine:
        raise HTTPException(status_code=503, detail="Threat intelligence engine not initialized")
    
    try:
        if feed_names:
            results = {}
            for feed_name in feed_names:
                background_tasks.add_task(threat_intel_engine.update_feed, feed_name)
                results[feed_name] = "scheduled"
        else:
            # Update all feeds
            background_tasks.add_task(threat_intel_engine.update_all_feeds)
            results = {"all_feeds": "scheduled"}
        
        return {
            "status": "success",
            "data": {
                "update_results": results,
                "scheduled_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to update threat feeds: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/threat-intel/alerts")
async def get_threat_alerts(
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get threat alerts"""
    if not threat_intel_engine:
        raise HTTPException(status_code=503, detail="Threat intelligence engine not initialized")
    
    try:
        alerts = await threat_intel_engine.get_active_alerts()
        
        # Filter by severity if specified
        if severity:
            try:
                severity_enum = ThreatSeverity(severity.lower())
                alerts = [alert for alert in alerts if alert.severity == severity_enum]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
        
        # Apply pagination
        total_alerts = len(alerts)
        alerts = alerts[offset:offset + limit]
        
        return {
            "status": "success",
            "data": {
                "alerts": [
                    {
                        "id": alert.id,
                        "title": alert.title,
                        "description": alert.description,
                        "severity": alert.severity.value,
                        "created_at": alert.created_at.isoformat(),
                        "updated_at": alert.updated_at.isoformat(),
                        "source": alert.source,
                        "indicators": alert.indicators,
                        "affected_assets": alert.affected_assets,
                        "recommended_actions": alert.recommended_actions,
                        "is_active": alert.is_active
                    }
                    for alert in alerts
                ],
                "pagination": {
                    "total": total_alerts,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_alerts
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get threat alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/threat-intel/cve/{cve_id}")
async def get_cve_details(cve_id: str):
    """Get CVE details"""
    if not threat_intel_engine:
        raise HTTPException(status_code=503, detail="Threat intelligence engine not initialized")
    
    try:
        cve_data = await threat_intel_engine.get_cve_details(cve_id)
        
        if not cve_data:
            raise HTTPException(status_code=404, detail=f"CVE {cve_id} not found")
        
        return {
            "status": "success",
            "data": {
                "cve_id": cve_data.cve_id,
                "description": cve_data.description,
                "cvss_score": cve_data.cvss_score,
                "severity": cve_data.severity.value,
                "published_date": cve_data.published_date.isoformat() if cve_data.published_date else None,
                "modified_date": cve_data.modified_date.isoformat() if cve_data.modified_date else None,
                "cwe_ids": cve_data.cwe_ids,
                "affected_products": cve_data.affected_products,
                "references": cve_data.references,
                "exploits_available": cve_data.exploits_available,
                "epss_score": cve_data.epss_score,
                "in_kev": cve_data.in_kev
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get CVE details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/threat-intel/scan")
async def scan_repository_threats(scan_request: ThreatScanRequest):
    """Scan repository for threat indicators"""
    if not threat_intel_engine:
        raise HTTPException(status_code=503, detail="Threat intelligence engine not initialized")
    
    try:
        scan_results = await threat_intel_engine.scan_repository(
            scan_request.repository_path, 
            scan_request.patterns_only
        )
        
        return {
            "status": "success",
            "data": {
                "repository_path": scan_request.repository_path,
                "scan_completed_at": datetime.now(timezone.utc).isoformat(),
                "threat_matches": [
                    {
                        "indicator_id": match.indicator_id,
                        "file_path": match.file_path,
                        "line_number": match.line_number,
                        "matched_content": match.matched_content,
                        "confidence": match.confidence,
                        "severity": match.severity.value,
                        "threat_type": match.threat_type
                    }
                    for match in scan_results
                ],
                "total_matches": len(scan_results)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to scan repository for threats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/threat-intel/zero-day")
async def get_zero_day_indicators():
    """Get zero-day threat indicators"""
    if not threat_intel_engine:
        raise HTTPException(status_code=503, detail="Threat intelligence engine not initialized")
    
    try:
        indicators = await threat_intel_engine.get_zero_day_indicators()
        
        return {
            "status": "success",
            "data": {
                "indicators": [
                    {
                        "id": indicator.id,
                        "pattern": indicator.pattern,
                        "threat_type": indicator.threat_type,
                        "description": indicator.description,
                        "severity": indicator.severity.value,
                        "confidence": indicator.confidence,
                        "first_seen": indicator.first_seen.isoformat(),
                        "last_seen": indicator.last_seen.isoformat(),
                        "source": indicator.source,
                        "tags": indicator.tags
                    }
                    for indicator in indicators
                ],
                "total_indicators": len(indicators)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get zero-day indicators: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== VULNERABILITY MANAGEMENT ENDPOINTS =====

@router.get("/vuln-mgmt/status")
async def get_vuln_management_status():
    """Get vulnerability management system status"""
    if not vuln_manager:
        raise HTTPException(status_code=503, detail="Vulnerability manager not initialized")
    
    try:
        metrics = await vuln_manager.calculate_risk_metrics()
        
        return {
            "status": "success",
            "data": {
                "total_vulnerabilities": metrics.total_vulnerabilities,
                "critical_count": metrics.critical_count,
                "high_count": metrics.high_count,
                "medium_count": metrics.medium_count,
                "low_count": metrics.low_count,
                "mean_time_to_fix": metrics.mean_time_to_fix,
                "sla_compliance_rate": metrics.sla_compliance_rate,
                "overdue_count": metrics.overdue_count,
                "total_assets": metrics.total_assets,
                "high_risk_assets": metrics.high_risk_assets
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get vulnerability management status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vuln-mgmt/vulnerabilities")
async def get_vulnerabilities(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    asset_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get vulnerabilities with filtering and pagination"""
    if not vuln_manager:
        raise HTTPException(status_code=503, detail="Vulnerability manager not initialized")
    
    try:
        # Build filters
        filters = {}
        if status:
            try:
                filters['status'] = VulnerabilityStatus(status.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        if priority:
            try:
                filters['priority'] = VulnerabilityPriority(priority.upper())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid priority: {priority}")
        
        if asset_id:
            filters['asset_id'] = asset_id
        
        vulnerabilities = await vuln_manager.get_vulnerabilities(filters, limit, offset)
        total_count = await vuln_manager.count_vulnerabilities(filters)
        
        return {
            "status": "success",
            "data": {
                "vulnerabilities": [
                    {
                        "id": vuln.id,
                        "title": vuln.title,
                        "description": vuln.description,
                        "cve_id": vuln.cve_id,
                        "severity": vuln.severity.value,
                        "priority": vuln.priority.value,
                        "status": vuln.status.value,
                        "cvss_score": vuln.cvss_score,
                        "epss_score": vuln.epss_score,
                        "asset_id": vuln.asset_id,
                        "discovered_date": vuln.discovered_date.isoformat(),
                        "due_date": vuln.due_date.isoformat() if vuln.due_date else None,
                        "fixed_date": vuln.fixed_date.isoformat() if vuln.fixed_date else None,
                        "assignee": vuln.assignee,
                        "tags": vuln.tags,
                        "source": vuln.source
                    }
                    for vuln in vulnerabilities
                ],
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get vulnerabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vuln-mgmt/vulnerabilities")
async def create_vulnerability(vuln_request: VulnerabilityCreateRequest):
    """Create a new vulnerability"""
    if not vuln_manager:
        raise HTTPException(status_code=503, detail="Vulnerability manager not initialized")
    
    try:
        # Validate severity
        try:
            severity = ThreatSeverity(vuln_request.severity.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {vuln_request.severity}")
        
        # Create vulnerability object
        vulnerability = Vulnerability(
            id=f"VULN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=vuln_request.title,
            description=vuln_request.description,
            cve_id=vuln_request.cve_id,
            severity=severity,
            priority=VulnerabilityPriority.MEDIUM,  # Default priority
            status=VulnerabilityStatus.OPEN,
            cvss_score=vuln_request.cvss_score,
            epss_score=vuln_request.epss_score,
            asset_id=vuln_request.asset_id,
            discovered_date=datetime.now(timezone.utc),
            due_date=None,
            fixed_date=None,
            assignee=vuln_request.assignee,
            tags=vuln_request.tags,
            source=vuln_request.source,
            metadata=vuln_request.metadata
        )
        
        # Add vulnerability
        await vuln_manager.add_vulnerability(vulnerability)
        
        return {
            "status": "success",
            "data": {
                "vulnerability_id": vulnerability.id,
                "created_at": vulnerability.discovered_date.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to create vulnerability: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/vuln-mgmt/vulnerabilities/{vuln_id}/status")
async def update_vulnerability_status(vuln_id: str, status_update: VulnerabilityStatusUpdate):
    """Update vulnerability status"""
    if not vuln_manager:
        raise HTTPException(status_code=503, detail="Vulnerability manager not initialized")
    
    try:
        # Validate status
        try:
            new_status = VulnerabilityStatus(status_update.status.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status_update.status}")
        
        success = await vuln_manager.update_vulnerability_status(
            vuln_id, new_status, status_update.assignee, status_update.notes
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Vulnerability {vuln_id} not found")
        
        return {
            "status": "success",
            "data": {
                "vulnerability_id": vuln_id,
                "new_status": new_status.value,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to update vulnerability status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vuln-mgmt/assets")
async def get_assets(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get assets with vulnerability information"""
    if not vuln_manager:
        raise HTTPException(status_code=503, detail="Vulnerability manager not initialized")
    
    try:
        assets = await vuln_manager.get_assets(limit, offset)
        total_count = await vuln_manager.count_assets()
        
        return {
            "status": "success",
            "data": {
                "assets": [
                    {
                        "id": asset.id,
                        "name": asset.name,
                        "asset_type": asset.asset_type,
                        "ip_address": asset.ip_address,
                        "hostname": asset.hostname,
                        "operating_system": asset.operating_system,
                        "environment": asset.environment,
                        "owner": asset.owner,
                        "criticality": asset.criticality.value,
                        "exposure_score": asset.exposure_score,
                        "vulnerability_count": asset.vulnerability_count,
                        "high_risk_vulns": asset.high_risk_vulns,
                        "last_scanned": asset.last_scanned.isoformat() if asset.last_scanned else None,
                        "tags": asset.tags,
                        "is_active": asset.is_active
                    }
                    for asset in assets
                ],
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vuln-mgmt/metrics")
async def get_risk_metrics():
    """Get detailed risk metrics"""
    if not vuln_manager:
        raise HTTPException(status_code=503, detail="Vulnerability manager not initialized")
    
    try:
        metrics = await vuln_manager.calculate_risk_metrics()
        
        return {
            "status": "success",
            "data": {
                "vulnerability_metrics": {
                    "total_vulnerabilities": metrics.total_vulnerabilities,
                    "by_severity": {
                        "critical": metrics.critical_count,
                        "high": metrics.high_count,
                        "medium": metrics.medium_count,
                        "low": metrics.low_count
                    },
                    "by_status": {
                        "open": await vuln_manager.count_vulnerabilities({"status": VulnerabilityStatus.OPEN}),
                        "triaged": await vuln_manager.count_vulnerabilities({"status": VulnerabilityStatus.TRIAGED}),
                        "in_progress": await vuln_manager.count_vulnerabilities({"status": VulnerabilityStatus.IN_PROGRESS}),
                        "fixed": await vuln_manager.count_vulnerabilities({"status": VulnerabilityStatus.FIXED}),
                        "verified": await vuln_manager.count_vulnerabilities({"status": VulnerabilityStatus.VERIFIED})
                    }
                },
                "time_metrics": {
                    "mean_time_to_fix": metrics.mean_time_to_fix,
                    "mean_time_to_triage": 24.0,  # Placeholder
                    "sla_compliance_rate": metrics.sla_compliance_rate,
                    "overdue_count": metrics.overdue_count
                },
                "asset_metrics": {
                    "total_assets": metrics.total_assets,
                    "high_risk_assets": metrics.high_risk_assets,
                    "assets_with_critical_vulns": 0  # Placeholder
                },
                "calculated_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get risk metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== SECURITY METRICS & KPIs ENDPOINTS =====

@router.get("/metrics/posture")
async def get_security_posture(repository: Optional[str] = Query(None)):
    """Get security posture score"""
    if not metrics_engine:
        raise HTTPException(status_code=503, detail="Security metrics engine not initialized")
    
    try:
        posture_score = await metrics_engine.calculate_security_posture(repository)
        
        return {
            "status": "success",
            "data": {
                "overall_score": posture_score.overall_score,
                "component_scores": {
                    "vulnerability_score": posture_score.vulnerability_score,
                    "compliance_score": posture_score.compliance_score,
                    "threat_score": posture_score.threat_score,
                    "configuration_score": posture_score.configuration_score
                },
                "trend": posture_score.trend.value,
                "last_updated": posture_score.last_updated.isoformat(),
                "recommendations": posture_score.recommendations,
                "components_detail": posture_score.components
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get security posture: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/compliance")
async def get_compliance_status(framework: Optional[str] = Query(None)):
    """Get compliance assessment status"""
    if not metrics_engine:
        raise HTTPException(status_code=503, detail="Security metrics engine not initialized")
    
    try:
        framework_enum = None
        
        if framework:
            try:
                framework_enum = ComplianceFramework(framework.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid framework: {framework}")
        
        compliance_results = await metrics_engine.get_compliance_results(framework_enum)
        
        return {
            "status": "success",
            "data": {
                "compliance_results": [
                    {
                        "framework": result.framework.value,
                        "framework_name": result.framework.value.replace('_', ' ').upper(),
                        "total_controls": result.total_controls,
                        "passed_controls": result.passed_controls,
                        "failed_controls": result.failed_controls,
                        "not_applicable_controls": result.not_applicable_controls,
                        "pass_percentage": result.pass_percentage,
                        "score": result.score,
                        "status": result.status,
                        "last_assessment": result.last_assessment.isoformat(),
                        "next_assessment": result.next_assessment.isoformat() if result.next_assessment else None,
                        "findings_count": len(result.findings),
                        "gaps_count": len(result.gaps)
                    }
                    for result in compliance_results
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get compliance status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/metrics/compliance/{framework}/assess")
async def assess_compliance_framework(framework: str, assessment_request: ComplianceAssessmentRequest):
    """Assess compliance for a specific framework"""
    if not metrics_engine:
        raise HTTPException(status_code=503, detail="Security metrics engine not initialized")
    
    try:
        # Validate framework
        try:
            framework_enum = ComplianceFramework(framework.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid framework: {framework}")
        
        result = await metrics_engine.assess_compliance_framework(framework_enum, assessment_request.assessor)
        
        return {
            "status": "success",
            "data": {
                "assessment_result": {
                    "framework": result.framework.value,
                    "total_controls": result.total_controls,
                    "passed_controls": result.passed_controls,
                    "failed_controls": result.failed_controls,
                    "not_applicable_controls": result.not_applicable_controls,
                    "pass_percentage": result.pass_percentage,
                    "score": result.score,
                    "status": result.status,
                    "assessment_date": result.last_assessment.isoformat(),
                    "next_assessment": result.next_assessment.isoformat() if result.next_assessment else None,
                    "findings": result.findings,
                    "gaps": result.gaps
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to assess compliance framework: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/kpis")
async def get_security_kpis():
    """Get security KPIs"""
    if not metrics_engine:
        raise HTTPException(status_code=503, detail="Security metrics engine not initialized")
    
    try:
        kpis = await metrics_engine.calculate_kpis()
        
        return {
            "status": "success",
            "data": {
                "kpis": [
                    {
                        "name": kpi.name,
                        "value": kpi.value,
                        "target": kpi.target,
                        "unit": kpi.unit,
                        "trend": kpi.trend.value,
                        "last_period_value": kpi.last_period_value,
                        "change_percentage": kpi.change_percentage,
                        "status": kpi.status,
                        "description": kpi.description,
                        "recommendations": kpi.recommendations
                    }
                    for kpi in kpis
                ],
                "calculated_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get security KPIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/trends")
async def get_risk_trends(days: int = Query(30, ge=1, le=365)):
    """Get risk trend analysis"""
    if not metrics_engine:
        raise HTTPException(status_code=503, detail="Security metrics engine not initialized")
    
    try:
        risk_trend = await metrics_engine.generate_risk_trend_analysis(days)
        
        return {
            "status": "success",
            "data": {
                "period": risk_trend.period,
                "analysis_days": days,
                "trends": {
                    "critical_vulnerabilities": {
                        "values": risk_trend.critical_trend.values,
                        "trend_direction": risk_trend.critical_trend.trend_direction.value,
                        "slope": risk_trend.critical_trend.slope,
                        "forecast_7d": risk_trend.critical_trend.forecast_7d,
                        "forecast_30d": risk_trend.critical_trend.forecast_30d
                    },
                    "high_vulnerabilities": {
                        "values": risk_trend.high_trend.values,
                        "trend_direction": risk_trend.high_trend.trend_direction.value,
                        "slope": risk_trend.high_trend.slope,
                        "forecast_7d": risk_trend.high_trend.forecast_7d,
                        "forecast_30d": risk_trend.high_trend.forecast_30d
                    },
                    "medium_vulnerabilities": {
                        "values": risk_trend.medium_trend.values,
                        "trend_direction": risk_trend.medium_trend.trend_direction.value,
                        "slope": risk_trend.medium_trend.slope
                    },
                    "low_vulnerabilities": {
                        "values": risk_trend.low_trend.values,
                        "trend_direction": risk_trend.low_trend.trend_direction.value,
                        "slope": risk_trend.low_trend.slope
                    },
                    "overall_risk": {
                        "values": risk_trend.overall_risk_trend.values,
                        "trend_direction": risk_trend.overall_risk_trend.trend_direction.value,
                        "slope": risk_trend.overall_risk_trend.slope,
                        "forecast_7d": risk_trend.overall_risk_trend.forecast_7d,
                        "forecast_30d": risk_trend.overall_risk_trend.forecast_30d
                    },
                    "new_vulnerabilities": {
                        "values": risk_trend.new_vulnerabilities_trend.values,
                        "trend_direction": risk_trend.new_vulnerabilities_trend.trend_direction.value,
                        "slope": risk_trend.new_vulnerabilities_trend.slope
                    },
                    "resolved_vulnerabilities": {
                        "values": risk_trend.resolved_vulnerabilities_trend.values,
                        "trend_direction": risk_trend.resolved_vulnerabilities_trend.trend_direction.value,
                        "slope": risk_trend.resolved_vulnerabilities_trend.slope
                    }
                },
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get risk trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== SYSTEM STATUS AND HEALTH ENDPOINTS =====

@router.get("/status")
async def get_system_status():
    """Get overall enhanced security system status"""
    try:
        status = {
            "overall_status": "operational",
            "components": {},
            "last_checked": datetime.now(timezone.utc).isoformat()
        }
        
        # Check threat intelligence engine
        if threat_intel_engine:
            try:
                ti_status = await threat_intel_engine.get_system_status()
                status["components"]["threat_intelligence"] = {
                    "status": "operational",
                    "engine_status": ti_status.engine_status.value,
                    "feed_count": ti_status.feed_count,
                    "active_alerts": ti_status.active_alerts
                }
            except Exception as e:
                status["components"]["threat_intelligence"] = {
                    "status": "error",
                    "error": str(e)
                }
                status["overall_status"] = "degraded"
        else:
            status["components"]["threat_intelligence"] = {
                "status": "not_initialized"
            }
            status["overall_status"] = "degraded"
        
        # Check vulnerability manager
        if vuln_manager:
            try:
                vm_metrics = await vuln_manager.calculate_risk_metrics()
                status["components"]["vulnerability_management"] = {
                    "status": "operational",
                    "total_vulnerabilities": vm_metrics.total_vulnerabilities,
                    "critical_count": vm_metrics.critical_count
                }
            except Exception as e:
                status["components"]["vulnerability_management"] = {
                    "status": "error",
                    "error": str(e)
                }
                status["overall_status"] = "degraded"
        else:
            status["components"]["vulnerability_management"] = {
                "status": "not_initialized"
            }
            status["overall_status"] = "degraded"
        
        # Check metrics engine
        if metrics_engine:
            try:
                posture = await metrics_engine.calculate_security_posture()
                status["components"]["security_metrics"] = {
                    "status": "operational",
                    "posture_score": posture.overall_score
                }
            except Exception as e:
                status["components"]["security_metrics"] = {
                    "status": "error",
                    "error": str(e)
                }
                status["overall_status"] = "degraded"
        else:
            status["components"]["security_metrics"] = {
                "status": "not_initialized"
            }
            status["overall_status"] = "degraded"
        
        return {
            "status": "success",
            "data": status
        }
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "enhanced_security_api"
    }

# Initialize services when module is imported
init_enhanced_security_services()

# Export router
__all__ = ['router']

# Note: The following routes need to be converted from Flask to FastAPI
# Temporarily commented out to resolve import issues

"""
@router.get('/threat-intel/feeds')
async def get_threat_feeds():
    # Threat intelligence feeds endpoint - needs implementation
    pass

# Additional routes would be implemented here
"""
            for feed_name in feed_names:
                success = await threat_intel_engine.update_feed(feed_name)
                results[feed_name] = "success" if success else "failed"
        else:
            # Update all feeds
            await threat_intel_engine.update_all_feeds()
            results = {"all_feeds": "success"}
        
        return jsonify({
            "status": "success",
            "data": {
                "update_results": results,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to update threat feeds: {e}")
        return jsonify({"error": str(e)}), 500

@enhanced_security_bp.route('/threat-intel/alerts', methods=['GET'])
@async_route
async def get_threat_alerts():
    """Get threat alerts"""
    if not threat_intel_engine:
        return jsonify({"error": "Threat intelligence engine not initialized"}), 503
    
    try:
        # Parse query parameters
        severity = request.args.get('severity')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        alerts = await threat_intel_engine.get_active_alerts()
        
        # Filter by severity if specified
        if severity:
            try:
                severity_enum = ThreatSeverity(severity.lower())
                alerts = [alert for alert in alerts if alert.severity == severity_enum]
            except ValueError:
                return jsonify({"error": f"Invalid severity: {severity}"}), 400
        
        # Apply pagination
        total_alerts = len(alerts)
        alerts = alerts[offset:offset + limit]
        
        return jsonify({
            "status": "success",
            "data": {
                "alerts": [
                    {
                        "id": alert.id,
                        "title": alert.title,
                        "description": alert.description,
                        "severity": alert.severity.value,
                        "created_at": alert.created_at.isoformat(),
                        "updated_at": alert.updated_at.isoformat(),
                        "source": alert.source,
                        "indicators": alert.indicators,
                        "affected_assets": alert.affected_assets,
                        "recommended_actions": alert.recommended_actions,
                        "is_active": alert.is_active
                    }
                    for alert in alerts
                ],
                "pagination": {
                    "total": total_alerts,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_alerts
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get threat alerts: {e}")
        return jsonify({"error": str(e)}), 500

@enhanced_security_bp.route('/threat-intel/cve/<cve_id>', methods=['GET'])
@async_route
async def get_cve_details(cve_id: str):
    """Get CVE details"""
    if not threat_intel_engine:
        return jsonify({"error": "Threat intelligence engine not initialized"}), 503
    
    try:
        cve_data = await threat_intel_engine.get_cve_details(cve_id)
        
        if not cve_data:
            return jsonify({"error": f"CVE {cve_id} not found"}), 404
        
        return jsonify({
            "status": "success",
            "data": {
                "cve_id": cve_data.cve_id,
                "description": cve_data.description,
                "cvss_score": cve_data.cvss_score,
                "severity": cve_data.severity.value,
                "published_date": cve_data.published_date.isoformat() if cve_data.published_date else None,
                "modified_date": cve_data.modified_date.isoformat() if cve_data.modified_date else None,
                "cwe_ids": cve_data.cwe_ids,
                "affected_products": cve_data.affected_products,
                "references": cve_data.references,
                "exploits_available": cve_data.exploits_available,
                "epss_score": cve_data.epss_score,
                "in_kev": cve_data.in_kev
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get CVE details: {e}")
        return jsonify({"error": str(e)}), 500

@enhanced_security_bp.route('/threat-intel/scan', methods=['POST'])
@validate_json('repository_path')
@async_route
async def scan_repository_threats():
    """Scan repository for threat indicators"""
    if not threat_intel_engine:
        return jsonify({"error": "Threat intelligence engine not initialized"}), 503
    
    try:
        data = request.get_json()
        repository_path = data['repository_path']
        patterns_only = data.get('patterns_only', False)
        
        scan_results = await threat_intel_engine.scan_repository(repository_path, patterns_only)
        
        return jsonify({
            "status": "success",
            "data": {
                "repository_path": repository_path,
                "scan_completed_at": datetime.now(timezone.utc).isoformat(),
                "threat_matches": [
                    {
                        "indicator_id": match.indicator_id,
                        "file_path": match.file_path,
                        "line_number": match.line_number,
                        "matched_content": match.matched_content,
                        "confidence": match.confidence,
                        "severity": match.severity.value,
                        "threat_type": match.threat_type
                    }
                    for match in scan_results
                ],
                "total_matches": len(scan_results)
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to scan repository for threats: {e}")
        return jsonify({"error": str(e)}), 500

@enhanced_security_bp.route('/threat-intel/zero-day', methods=['GET'])
@async_route
async def get_zero_day_indicators():
    """Get zero-day threat indicators"""
    if not threat_intel_engine:
        return jsonify({"error": "Threat intelligence engine not initialized"}), 503
    
    try:
        indicators = await threat_intel_engine.get_zero_day_indicators()
        
        return jsonify({
            "status": "success",
            "data": {
                "indicators": [
                    {
                        "id": indicator.id,
                        "pattern": indicator.pattern,
                        "threat_type": indicator.threat_type,
                        "description": indicator.description,
                        "severity": indicator.severity.value,
                        "confidence": indicator.confidence,
                        "first_seen": indicator.first_seen.isoformat(),
                        "last_seen": indicator.last_seen.isoformat(),
                        "source": indicator.source,
                        "tags": indicator.tags
                    }
                    for indicator in indicators
                ],
                "total_indicators": len(indicators)
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get zero-day indicators: {e}")
        return jsonify({"error": str(e)}), 500

# ===== VULNERABILITY MANAGEMENT ENDPOINTS =====

@enhanced_security_bp.route('/vuln-mgmt/status', methods=['GET'])
@async_route
async def get_vuln_management_status():
    """Get vulnerability management system status"""
    if not vuln_manager:
        return jsonify({"error": "Vulnerability manager not initialized"}), 503
    
    try:
        metrics = await vuln_manager.calculate_risk_metrics()
        
        return jsonify({
            "status": "success",
            "data": {
                "total_vulnerabilities": metrics.total_vulnerabilities,
                "critical_count": metrics.critical_count,
                "high_count": metrics.high_count,
                "medium_count": metrics.medium_count,
                "low_count": metrics.low_count,
                "mean_time_to_fix": metrics.mean_time_to_fix,
                "sla_compliance_rate": metrics.sla_compliance_rate,
                "overdue_count": metrics.overdue_count,
                "total_assets": metrics.total_assets,
                "high_risk_assets": metrics.high_risk_assets
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get vulnerability management status: {e}")
        return jsonify({"error": str(e)}), 500

@enhanced_security_bp.route('/vuln-mgmt/vulnerabilities', methods=['GET'])
@async_route
async def get_vulnerabilities():
    """Get vulnerabilities with filtering and pagination"""
    if not vuln_manager:
        return jsonify({"error": "Vulnerability manager not initialized"}), 503
    
    try:
        # Parse query parameters
        status = request.args.get('status')
        priority = request.args.get('priority')
        asset_id = request.args.get('asset_id')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Build filters
        filters = {}
        if status:
            try:
                filters['status'] = VulnerabilityStatus(status.lower())
            except ValueError:
                return jsonify({"error": f"Invalid status: {status}"}), 400
        
        if priority:
            try:
                filters['priority'] = VulnerabilityPriority(priority.upper())
            except ValueError:
                return jsonify({"error": f"Invalid priority: {priority}"}), 400
        
        if asset_id:
            filters['asset_id'] = asset_id
        
        vulnerabilities = await vuln_manager.get_vulnerabilities(filters, limit, offset)
        total_count = await vuln_manager.count_vulnerabilities(filters)
        
        return jsonify({
            "status": "success",
            "data": {
                "vulnerabilities": [
                    {
                        "id": vuln.id,
                        "title": vuln.title,
                        "description": vuln.description,
                        "cve_id": vuln.cve_id,
                        "severity": vuln.severity.value,
                        "priority": vuln.priority.value,
                        "status": vuln.status.value,
                        "cvss_score": vuln.cvss_score,
                        "epss_score": vuln.epss_score,
                        "asset_id": vuln.asset_id,
                        "discovered_date": vuln.discovered_date.isoformat(),
                        "due_date": vuln.due_date.isoformat() if vuln.due_date else None,
                        "fixed_date": vuln.fixed_date.isoformat() if vuln.fixed_date else None,
                        "assignee": vuln.assignee,
                        "tags": vuln.tags,
                        "source": vuln.source
                    }
                    for vuln in vulnerabilities
                ],
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get vulnerabilities: {e}")
        return jsonify({"error": str(e)}), 500

@enhanced_security_bp.route('/vuln-mgmt/vulnerabilities', methods=['POST'])
@validate_json('title', 'description', 'severity', 'asset_id')
@async_route
async def create_vulnerability():
    """Create a new vulnerability"""
    if not vuln_manager:
        return jsonify({"error": "Vulnerability manager not initialized"}), 503
    
    try:
        data = request.get_json()
        
        # Validate severity
        try:
            severity = ThreatSeverity(data['severity'].lower())
        except ValueError:
            return jsonify({"error": f"Invalid severity: {data['severity']}"}), 400
        
        # Create vulnerability object
        vulnerability = Vulnerability(
            id=f"VULN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=data['title'],
            description=data['description'],
            cve_id=data.get('cve_id'),
            severity=severity,
            priority=VulnerabilityPriority.MEDIUM,  # Default priority
            status=VulnerabilityStatus.OPEN,
            cvss_score=data.get('cvss_score', 0.0),
            epss_score=data.get('epss_score', 0.0),
            asset_id=data['asset_id'],
            discovered_date=datetime.now(timezone.utc),
            due_date=None,
            fixed_date=None,
            assignee=data.get('assignee'),
            tags=data.get('tags', []),
            source=data.get('source', 'manual'),
            metadata=data.get('metadata', {})
        )
        
        # Add vulnerability
        await vuln_manager.add_vulnerability(vulnerability)
        
        return jsonify({
            "status": "success",
            "data": {
                "vulnerability_id": vulnerability.id,
                "created_at": vulnerability.discovered_date.isoformat()
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to create vulnerability: {e}")
        return jsonify({"error": str(e)}), 500

@enhanced_security_bp.route('/vuln-mgmt/vulnerabilities/<vuln_id>/status', methods=['PUT'])
@validate_json('status')
@async_route
async def update_vulnerability_status(vuln_id: str):
    """Update vulnerability status"""
    if not vuln_manager:
        return jsonify({"error": "Vulnerability manager not initialized"}), 503
    
    try:
        data = request.get_json()
        
        # Validate status
        try:
            new_status = VulnerabilityStatus(data['status'].lower())
        except ValueError:
            return jsonify({"error": f"Invalid status: {data['status']}"}), 400
        
        assignee = data.get('assignee')
        notes = data.get('notes', '')
        
        success = await vuln_manager.update_vulnerability_status(
            vuln_id, new_status, assignee, notes
        )
        
        if not success:
            return jsonify({"error": f"Vulnerability {vuln_id} not found"}), 404
        
        return jsonify({
            "status": "success",
            "data": {
                "vulnerability_id": vuln_id,
                "new_status": new_status.value,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to update vulnerability status: {e}")
        return jsonify({"error": str(e)}), 500

@enhanced_security_bp.route('/vuln-mgmt/assets', methods=['GET'])
@async_route
async def get_assets():
    """Get assets with vulnerability information"""
    if not vuln_manager:
        return jsonify({"error": "Vulnerability manager not initialized"}), 503
    
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        assets = await vuln_manager.get_assets(limit, offset)
        total_count = await vuln_manager.count_assets()
        
        return jsonify({
            "status": "success",
            "data": {
                "assets": [
                    {
                        "id": asset.id,
                        "name": asset.name,
                        "asset_type": asset.asset_type,
                        "ip_address": asset.ip_address,
                        "hostname": asset.hostname,
                        "operating_system": asset.operating_system,
                        "environment": asset.environment,
                        "owner": asset.owner,
                        "criticality": asset.criticality.value,
                        "exposure_score": asset.exposure_score,
                        "vulnerability_count": asset.vulnerability_count,
                        "high_risk_vulns": asset.high_risk_vulns,
                        "last_scanned": asset.last_scanned.isoformat() if asset.last_scanned else None,
                        "tags": asset.tags,
                        "is_active": asset.is_active
                    }
                    for asset in assets
                ],
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get assets: {e}")
        return jsonify({"error": str(e)}), 500

@enhanced_security_bp.route('/vuln-mgmt/metrics', methods=['GET'])
@async_route
async def get_risk_metrics():
    """Get detailed risk metrics"""
    if not vuln_manager:
        return jsonify({"error": "Vulnerability manager not initialized"}), 503
    
    try:
        metrics = await vuln_manager.calculate_risk_metrics()
        
        return jsonify({
            "status": "success",
            "data": {
                "vulnerability_metrics": {
                    "total_vulnerabilities": metrics.total_vulnerabilities,
                    "by_severity": {
                        "critical": metrics.critical_count,
                        "high": metrics.high_count,
                        "medium": metrics.medium_count,
                        "low": metrics.low_count
                    },
                    "by_status": {
                        "open": await vuln_manager.count_vulnerabilities({"status": VulnerabilityStatus.OPEN}),
                        "triaged": await vuln_manager.count_vulnerabilities({"status": VulnerabilityStatus.TRIAGED}),
                        "in_progress": await vuln_manager.count_vulnerabilities({"status": VulnerabilityStatus.IN_PROGRESS}),
                        "fixed": await vuln_manager.count_vulnerabilities({"status": VulnerabilityStatus.FIXED}),
                        "verified": await vuln_manager.count_vulnerabilities({"status": VulnerabilityStatus.VERIFIED})
                    }
                },
                "time_metrics": {
                    "mean_time_to_fix": metrics.mean_time_to_fix,
                    "mean_time_to_triage": 24.0,  # Placeholder
                    "sla_compliance_rate": metrics.sla_compliance_rate,
                    "overdue_count": metrics.overdue_count
                },
                "asset_metrics": {
                    "total_assets": metrics.total_assets,
                    "high_risk_assets": metrics.high_risk_assets,
                    "assets_with_critical_vulns": 0  # Placeholder
                },
                "calculated_at": datetime.now(timezone.utc).isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get risk metrics: {e}")
        return jsonify({"error": str(e)}), 500

# ===== SECURITY METRICS & KPIs ENDPOINTS =====

@enhanced_security_bp.route('/metrics/posture', methods=['GET'])
@async_route
async def get_security_posture():
    """Get security posture score"""
    if not metrics_engine:
        return jsonify({"error": "Security metrics engine not initialized"}), 503
    
    try:
        repository = request.args.get('repository')
        posture_score = await metrics_engine.calculate_security_posture(repository)
        
        return jsonify({
            "status": "success",
            "data": {
                "overall_score": posture_score.overall_score,
                "component_scores": {
                    "vulnerability_score": posture_score.vulnerability_score,
                    "compliance_score": posture_score.compliance_score,
                    "threat_score": posture_score.threat_score,
                    "configuration_score": posture_score.configuration_score
                },
                "trend": posture_score.trend.value,
                "last_updated": posture_score.last_updated.isoformat(),
                "recommendations": posture_score.recommendations,
                "components_detail": posture_score.components
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get security posture: {e}")
        return jsonify({"error": str(e)}), 500

@enhanced_security_bp.route('/metrics/compliance', methods=['GET'])
@async_route
async def get_compliance_status():
    """Get compliance assessment status"""
    if not metrics_engine:
        return jsonify({"error": "Security metrics engine not initialized"}), 503
    
    try:
        framework_param = request.args.get('framework')
        framework = None
        
        if framework_param:
            try:
                framework = ComplianceFramework(framework_param.lower())
            except ValueError:
                return jsonify({"error": f"Invalid framework: {framework_param}"}), 400
        
        compliance_results = await metrics_engine.get_compliance_results(framework)
        
        return jsonify({
            "status": "success",
            "data": {
                "compliance_results": [
                    {
                        "framework": result.framework.value,
                        "framework_name": result.framework.value.replace('_', ' ').upper(),
                        "total_controls": result.total_controls,
                        "passed_controls": result.passed_controls,
                        "failed_controls": result.failed_controls,
                        "not_applicable_controls": result.not_applicable_controls,
                        "pass_percentage": result.pass_percentage,
                        "score": result.score,
                        "status": result.status,
                        "last_assessment": result.last_assessment.isoformat(),
                        "next_assessment": result.next_assessment.isoformat() if result.next_assessment else None,
                        "findings_count": len(result.findings),
                        "gaps_count": len(result.gaps)
                    }
                    for result in compliance_results
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get compliance status: {e}")
        return jsonify({"error": str(e)}), 500

@enhanced_security_bp.route('/metrics/compliance/<framework>/assess', methods=['POST'])
@async_route
async def assess_compliance_framework(framework: str):
    """Assess compliance for a specific framework"""
    if not metrics_engine:
        return jsonify({"error": "Security metrics engine not initialized"}), 503
    
    try:
        # Validate framework
        try:
            framework_enum = ComplianceFramework(framework.lower())
        except ValueError:
            return jsonify({"error": f"Invalid framework: {framework}"}), 400
        
        data = request.get_json() or {}
        assessor = data.get('assessor', 'system')
        
        result = await metrics_engine.assess_compliance_framework(framework_enum, assessor)
        
        return jsonify({
            "status": "success",
            "data": {
                "assessment_result": {
                    "framework": result.framework.value,
                    "total_controls": result.total_controls,
                    "passed_controls": result.passed_controls,
                    "failed_controls": result.failed_controls,
                    "not_applicable_controls": result.not_applicable_controls,
                    "pass_percentage": result.pass_percentage,
                    "score": result.score,
                    "status": result.status,
                    "assessment_date": result.last_assessment.isoformat(),
                    "next_assessment": result.next_assessment.isoformat() if result.next_assessment else None,
                    "findings": result.findings,
                    "gaps": result.gaps
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to assess compliance framework: {e}")
        return jsonify({"error": str(e)}), 500

@enhanced_security_bp.route('/metrics/kpis', methods=['GET'])
@async_route
async def get_security_kpis():
    """Get security KPIs"""
    if not metrics_engine:
        return jsonify({"error": "Security metrics engine not initialized"}), 503
    
    try:
        kpis = await metrics_engine.calculate_kpis()
        
        return jsonify({
            "status": "success",
            "data": {
                "kpis": [
                    {
                        "name": kpi.name,
                        "value": kpi.value,
                        "target": kpi.target,
                        "unit": kpi.unit,
                        "trend": kpi.trend.value,
                        "last_period_value": kpi.last_period_value,
                        "change_percentage": kpi.change_percentage,
                        "status": kpi.status,
                        "description": kpi.description,
                        "recommendations": kpi.recommendations
                    }
                    for kpi in kpis
                ],
                "calculated_at": datetime.now(timezone.utc).isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get security KPIs: {e}")
        return jsonify({"error": str(e)}), 500

@enhanced_security_bp.route('/metrics/trends', methods=['GET'])
@async_route
async def get_risk_trends():
    """Get risk trend analysis"""
    if not metrics_engine:
        return jsonify({"error": "Security metrics engine not initialized"}), 503
    
    try:
        days = int(request.args.get('days', 30))
        if days <= 0 or days > 365:
            return jsonify({"error": "Days must be between 1 and 365"}), 400
        
        risk_trend = await metrics_engine.generate_risk_trend_analysis(days)
        
        return jsonify({
            "status": "success",
            "data": {
                "period": risk_trend.period,
                "analysis_days": days,
                "trends": {
                    "critical_vulnerabilities": {
                        "values": risk_trend.critical_trend.values,
                        "trend_direction": risk_trend.critical_trend.trend_direction.value,
                        "slope": risk_trend.critical_trend.slope,
                        "forecast_7d": risk_trend.critical_trend.forecast_7d,
                        "forecast_30d": risk_trend.critical_trend.forecast_30d
                    },
                    "high_vulnerabilities": {
                        "values": risk_trend.high_trend.values,
                        "trend_direction": risk_trend.high_trend.trend_direction.value,
                        "slope": risk_trend.high_trend.slope,
                        "forecast_7d": risk_trend.high_trend.forecast_7d,
                        "forecast_30d": risk_trend.high_trend.forecast_30d
                    },
                    "medium_vulnerabilities": {
                        "values": risk_trend.medium_trend.values,
                        "trend_direction": risk_trend.medium_trend.trend_direction.value,
                        "slope": risk_trend.medium_trend.slope
                    },
                    "low_vulnerabilities": {
                        "values": risk_trend.low_trend.values,
                        "trend_direction": risk_trend.low_trend.trend_direction.value,
                        "slope": risk_trend.low_trend.slope
                    },
                    "overall_risk": {
                        "values": risk_trend.overall_risk_trend.values,
                        "trend_direction": risk_trend.overall_risk_trend.trend_direction.value,
                        "slope": risk_trend.overall_risk_trend.slope,
                        "forecast_7d": risk_trend.overall_risk_trend.forecast_7d,
                        "forecast_30d": risk_trend.overall_risk_trend.forecast_30d
                    },
                    "new_vulnerabilities": {
                        "values": risk_trend.new_vulnerabilities_trend.values,
                        "trend_direction": risk_trend.new_vulnerabilities_trend.trend_direction.value,
                        "slope": risk_trend.new_vulnerabilities_trend.slope
                    },
                    "resolved_vulnerabilities": {
                        "values": risk_trend.resolved_vulnerabilities_trend.values,
                        "trend_direction": risk_trend.resolved_vulnerabilities_trend.trend_direction.value,
                        "slope": risk_trend.resolved_vulnerabilities_trend.slope
                    }
                },
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get risk trends: {e}")
        return jsonify({"error": str(e)}), 500

# ===== SYSTEM STATUS AND HEALTH ENDPOINTS =====

@enhanced_security_bp.route('/status', methods=['GET'])
@async_route
async def get_system_status():
    """Get overall enhanced security system status"""
    try:
        status = {
            "overall_status": "operational",
            "components": {},
            "last_checked": datetime.now(timezone.utc).isoformat()
        }
        
        # Check threat intelligence engine
        if threat_intel_engine:
            try:
                ti_status = await threat_intel_engine.get_system_status()
                status["components"]["threat_intelligence"] = {
                    "status": "operational",
                    "engine_status": ti_status.engine_status.value,
                    "feed_count": ti_status.feed_count,
                    "active_alerts": ti_status.active_alerts
                }
            except Exception as e:
                status["components"]["threat_intelligence"] = {
                    "status": "error",
                    "error": str(e)
                }
                status["overall_status"] = "degraded"
        else:
            status["components"]["threat_intelligence"] = {
                "status": "not_initialized"
            }
            status["overall_status"] = "degraded"
        
        # Check vulnerability manager
        if vuln_manager:
            try:
                vm_metrics = await vuln_manager.calculate_risk_metrics()
                status["components"]["vulnerability_management"] = {
                    "status": "operational",
                    "total_vulnerabilities": vm_metrics.total_vulnerabilities,
                    "critical_count": vm_metrics.critical_count
                }
            except Exception as e:
                status["components"]["vulnerability_management"] = {
                    "status": "error",
                    "error": str(e)
                }
                status["overall_status"] = "degraded"
        else:
            status["components"]["vulnerability_management"] = {
                "status": "not_initialized"
            }
            status["overall_status"] = "degraded"
        
        # Check metrics engine
        if metrics_engine:
            try:
                posture = await metrics_engine.calculate_security_posture()
                status["components"]["security_metrics"] = {
                    "status": "operational",
                    "posture_score": posture.overall_score
                }
            except Exception as e:
                status["components"]["security_metrics"] = {
                    "status": "error",
                    "error": str(e)
                }
                status["overall_status"] = "degraded"
        else:
            status["components"]["security_metrics"] = {
                "status": "not_initialized"
            }
            status["overall_status"] = "degraded"
        
        return jsonify({
            "status": "success",
            "data": status
        })
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        return jsonify({"error": str(e)}), 500

@enhanced_security_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "enhanced_security_api"
    })

# Error handlers
@enhanced_security_bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@enhanced_security_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

@enhanced_security_bp.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# Initialize services when blueprint is registered
init_enhanced_security_services()

# Export blueprint
__all__ = ['enhanced_security_bp']
