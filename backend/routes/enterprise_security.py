"""
Enterprise Security Routes
API endpoints for enterprise security features:
- OSV/NVD Vulnerability Database Integration
- SBOM Generation (SPDX/CycloneDX)
- Security Trends Dashboard
- Scan Comparison & Delta Analysis
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Response
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import logging
import json

# Import services
from services.osv_nvd_integration import (
    get_vulnerability_database,
    VulnerabilityDatabaseIntegration
)
from services.sbom_generator import (
    get_sbom_generator,
    SBOMGenerator,
    SBOMFormat
)
from services.security_trends import (
    get_security_trends_service,
    SecurityTrendsService,
    TrendPeriod
)
from services.scan_comparison import (
    get_scan_comparison_service,
    ScanComparisonService
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/enterprise", tags=["Enterprise Security"])


# ============ Request/Response Models ============

class VulnerabilityEnrichRequest(BaseModel):
    """Request to enrich vulnerability data"""
    cve_id: Optional[str] = None
    package_name: Optional[str] = None
    package_version: Optional[str] = None
    ecosystem: str = "pypi"


class PackageVulnerabilityRequest(BaseModel):
    """Request to check package vulnerabilities"""
    packages: List[dict] = Field(
        ...,
        example=[
            {"name": "django", "version": "3.2.0", "ecosystem": "pypi"},
            {"name": "lodash", "version": "4.17.20", "ecosystem": "npm"}
        ]
    )


class SBOMGenerateRequest(BaseModel):
    """Request to generate SBOM"""
    repository_path: str = Field(..., description="Path to the repository")
    format: str = Field(default="spdx", description="SBOM format: spdx or cyclonedx")
    include_dev_deps: bool = Field(default=False, description="Include dev dependencies")
    enrich_vulnerabilities: bool = Field(default=True, description="Enrich with vulnerability data")


class TrendPeriodEnum(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"


class ScanCompareRequest(BaseModel):
    """Request to compare two scans"""
    base_scan_id: str = Field(..., description="ID of the baseline scan")
    compare_scan_id: str = Field(..., description="ID of the scan to compare")
    include_unchanged: bool = Field(default=False, description="Include unchanged findings")


# ============ OSV/NVD Integration Routes ============

@router.get("/vulnerabilities/cve/{cve_id}")
async def get_cve_details(cve_id: str):
    """
    Get detailed vulnerability information for a CVE from NVD.
    Includes CVSS scores, EPSS data, affected products, and references.
    """
    try:
        vuln_db = get_vulnerability_database()
        cve_data = await vuln_db.get_cve_details(cve_id)
        
        if not cve_data:
            raise HTTPException(status_code=404, detail=f"CVE {cve_id} not found")
        
        return {
            "success": True,
            "data": cve_data
        }
    except Exception as e:
        logger.error(f"Error fetching CVE details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vulnerabilities/packages")
async def check_package_vulnerabilities(request: PackageVulnerabilityRequest):
    """
    Check multiple packages for known vulnerabilities using Google OSV.
    Returns vulnerability data for each affected package.
    """
    try:
        vuln_db = get_vulnerability_database()
        results = []
        
        for pkg in request.packages:
            vulns = await vuln_db.get_package_vulnerabilities(
                package_name=pkg["name"],
                ecosystem=pkg.get("ecosystem", "pypi"),
                version=pkg.get("version")
            )
            results.append({
                "package": pkg["name"],
                "version": pkg.get("version"),
                "ecosystem": pkg.get("ecosystem", "pypi"),
                "vulnerabilities": vulns,
                "vulnerable": len(vulns) > 0
            })
        
        return {
            "success": True,
            "total_packages": len(request.packages),
            "vulnerable_packages": sum(1 for r in results if r["vulnerable"]),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error checking package vulnerabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vulnerabilities/enrich")
async def enrich_vulnerability(request: VulnerabilityEnrichRequest):
    """
    Enrich vulnerability data with additional context from OSV and NVD.
    Provides CVSS scores, EPSS probability, affected versions, and remediation info.
    """
    try:
        vuln_db = get_vulnerability_database()
        
        enriched_data = {}
        
        if request.cve_id:
            cve_data = await vuln_db.get_cve_details(request.cve_id)
            if cve_data:
                enriched_data["cve_details"] = cve_data
        
        if request.package_name:
            vulns = await vuln_db.get_package_vulnerabilities(
                package_name=request.package_name,
                ecosystem=request.ecosystem,
                version=request.package_version
            )
            enriched_data["package_vulnerabilities"] = vulns
        
        return {
            "success": True,
            "data": enriched_data
        }
    except Exception as e:
        logger.error(f"Error enriching vulnerability: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ SBOM Generation Routes ============

@router.post("/sbom/generate")
async def generate_sbom(request: SBOMGenerateRequest, background_tasks: BackgroundTasks):
    """
    Generate Software Bill of Materials (SBOM) for a repository.
    Supports SPDX 2.3 and CycloneDX 1.5 formats.
    """
    try:
        sbom_gen = get_sbom_generator()
        
        sbom_format = SBOMFormat.SPDX if request.format.lower() == "spdx" else SBOMFormat.CYCLONEDX
        
        sbom = await sbom_gen.generate_sbom(
            repository_path=request.repository_path,
            output_format=sbom_format,
            include_dev_dependencies=request.include_dev_deps,
            enrich_with_vulnerabilities=request.enrich_vulnerabilities
        )
        
        return {
            "success": True,
            "format": request.format,
            "sbom": sbom.to_dict() if hasattr(sbom, 'to_dict') else sbom
        }
    except Exception as e:
        logger.error(f"Error generating SBOM: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sbom/generate/download")
async def generate_sbom_download(
    repository_path: str,
    format: str = "spdx",
    output_type: str = "json"
):
    """
    Generate and download SBOM file.
    Supports JSON and XML output types.
    """
    try:
        sbom_gen = get_sbom_generator()
        
        sbom_format = SBOMFormat.SPDX if format.lower() == "spdx" else SBOMFormat.CYCLONEDX
        
        sbom = await sbom_gen.generate_sbom(
            repository_path=repository_path,
            output_format=sbom_format
        )
        
        sbom_dict = sbom.to_dict() if hasattr(sbom, 'to_dict') else sbom
        
        if output_type.lower() == "json":
            content = json.dumps(sbom_dict, indent=2)
            media_type = "application/json"
            filename = f"sbom-{format}.json"
        else:
            # Convert to XML (simplified)
            content = dict_to_xml(sbom_dict, root_name="sbom")
            media_type = "application/xml"
            filename = f"sbom-{format}.xml"
        
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error generating SBOM download: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sbom/formats")
async def get_supported_sbom_formats():
    """Get list of supported SBOM formats and their descriptions"""
    return {
        "formats": [
            {
                "id": "spdx",
                "name": "SPDX 2.3",
                "description": "Software Package Data Exchange - Linux Foundation standard",
                "output_types": ["json", "xml"],
                "compliance": ["NTIA", "Executive Order 14028"]
            },
            {
                "id": "cyclonedx",
                "name": "CycloneDX 1.5",
                "description": "OWASP lightweight SBOM standard",
                "output_types": ["json", "xml"],
                "compliance": ["OWASP", "FDA", "NTIA"]
            }
        ],
        "supported_languages": [
            "Python", "JavaScript", "TypeScript", "Go", "Rust", 
            "Java", "Ruby", ".NET/C#"
        ]
    }


# ============ Security Trends Routes ============

@router.get("/trends/dashboard")
async def get_trends_dashboard(
    project_id: Optional[str] = Query(None, description="Filter by project")
):
    """
    Get complete security trends dashboard data.
    Single endpoint for all dashboard metrics and charts.
    """
    try:
        trends_service = get_security_trends_service()
        dashboard_data = await trends_service.get_dashboard_data(project_id)
        
        return {
            "success": True,
            "data": dashboard_data
        }
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/severity")
async def get_severity_trends(
    project_id: Optional[str] = Query(None),
    period: TrendPeriodEnum = Query(TrendPeriodEnum.weekly),
    limit: int = Query(12, ge=1, le=52)
):
    """
    Get severity trends over time.
    Shows how vulnerability counts by severity change over the specified period.
    """
    try:
        trends_service = get_security_trends_service()
        
        trend_period = TrendPeriod(period.value)
        
        trends = await trends_service.get_severity_trends(
            project_id=project_id,
            period=trend_period,
            limit=limit
        )
        
        return {
            "success": True,
            "period": period.value,
            "data_points": len(trends.data_points),
            "direction": trends.direction.value,
            "improvement_percentage": trends.improvement_percentage,
            "avg_security_score": trends.avg_security_score,
            "projected_score_30d": trends.projected_security_score_30d,
            "time_to_target": trends.time_to_target_score,
            "trends": [
                {
                    "date": dp.timestamp.isoformat(),
                    "security_score": dp.security_score,
                    "risk_score": dp.risk_score,
                    "severity_counts": dp.severity_counts.to_dict(),
                    "fixed": dp.fixed_count,
                    "new": dp.new_count
                }
                for dp in trends.data_points
            ],
            "notable_changes": trends.notable_changes
        }
    except Exception as e:
        logger.error(f"Error fetching severity trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/metrics")
async def get_current_metrics(
    project_id: Optional[str] = Query(None)
):
    """
    Get current security metrics snapshot.
    Includes security score, risk score, MTTR, and finding counts.
    """
    try:
        trends_service = get_security_trends_service()
        metrics = await trends_service.get_current_metrics(project_id)
        
        return {
            "success": True,
            "timestamp": metrics.timestamp.isoformat(),
            "security_score": metrics.security_score,
            "risk_score": metrics.risk_score,
            "severity_counts": metrics.severity_counts.to_dict(),
            "open_findings": metrics.open_findings,
            "fixed_last_7d": metrics.fixed_last_7d,
            "fixed_last_30d": metrics.fixed_last_30d,
            "new_last_7d": metrics.new_last_7d,
            "new_last_30d": metrics.new_last_30d,
            "mttr_hours": metrics.mttr_hours,
            "compliance_rate": metrics.compliance_rate,
            "coverage_percentage": metrics.coverage_percentage
        }
    except Exception as e:
        logger.error(f"Error fetching current metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/comparison")
async def get_period_comparison(
    project_id: Optional[str] = Query(None)
):
    """
    Get period-over-period comparison.
    Compares current period with previous period to show improvement/degradation.
    """
    try:
        trends_service = get_security_trends_service()
        comparison = await trends_service.get_comparison_report(project_id)
        
        return {
            "success": True,
            "data": comparison
        }
    except Exception as e:
        logger.error(f"Error fetching period comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Scan Comparison Routes ============

@router.post("/scans/compare")
async def compare_scans(request: ScanCompareRequest):
    """
    Compare two security scans.
    Shows fixed vulnerabilities, new issues, regressions, and improvements.
    """
    try:
        comparison_service = get_scan_comparison_service()
        
        result = await comparison_service.compare_scans(
            base_scan_id=request.base_scan_id,
            compare_scan_id=request.compare_scan_id,
            include_unchanged=request.include_unchanged
        )
        
        report = await comparison_service.generate_comparison_report(result)
        
        return {
            "success": True,
            "data": report
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error comparing scans: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scans/{project_id}/compare-with-latest")
async def compare_with_latest(
    project_id: str,
    scan_id: str = Query(..., description="Scan ID to compare with latest")
):
    """
    Compare a specific scan with the latest scan for the project.
    Useful for tracking progress from a baseline scan.
    """
    try:
        comparison_service = get_scan_comparison_service()
        
        result = await comparison_service.compare_with_latest(
            project_id=project_id,
            scan_id=scan_id
        )
        
        report = await comparison_service.generate_comparison_report(result)
        
        return {
            "success": True,
            "data": report
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error comparing with latest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scans/{project_id}/branches/compare")
async def compare_branches(
    project_id: str,
    base_branch: str = Query(..., description="Base branch name"),
    compare_branch: str = Query(..., description="Branch to compare")
):
    """
    Compare latest scans from two branches.
    Useful for PR reviews and feature branch security checks.
    """
    try:
        comparison_service = get_scan_comparison_service()
        
        result = await comparison_service.compare_branches(
            project_id=project_id,
            base_branch=base_branch,
            compare_branch=compare_branch
        )
        
        report = await comparison_service.generate_comparison_report(result)
        
        return {
            "success": True,
            "base_branch": base_branch,
            "compare_branch": compare_branch,
            "data": report
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error comparing branches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scans/{project_id}/remediation-progress")
async def get_remediation_progress(
    project_id: str,
    days: int = Query(30, ge=7, le=365)
):
    """
    Get remediation progress over time.
    Shows how vulnerabilities are being fixed across scans.
    """
    try:
        comparison_service = get_scan_comparison_service()
        
        progress = await comparison_service.get_remediation_progress(
            project_id=project_id,
            days=days
        )
        
        return {
            "success": True,
            "data": progress
        }
    except Exception as e:
        logger.error(f"Error fetching remediation progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scans/{project_id}/fix-velocity")
async def get_fix_velocity(
    project_id: str,
    severity: Optional[str] = Query(None, description="Filter by severity")
):
    """
    Get fix velocity metrics.
    Shows average time to remediate vulnerabilities by severity.
    """
    try:
        comparison_service = get_scan_comparison_service()
        
        velocity = await comparison_service.get_fix_velocity(
            project_id=project_id,
            severity=severity
        )
        
        return {
            "success": True,
            "data": velocity
        }
    except Exception as e:
        logger.error(f"Error fetching fix velocity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Utility Functions ============

def dict_to_xml(data: dict, root_name: str = "root") -> str:
    """Simple dict to XML converter"""
    def _to_xml(d, parent):
        xml = ""
        if isinstance(d, dict):
            for key, val in d.items():
                xml += f"<{key}>{_to_xml(val, key)}</{key}>"
        elif isinstance(d, list):
            for item in d:
                xml += f"<item>{_to_xml(item, 'item')}</item>"
        else:
            xml = str(d) if d is not None else ""
        return xml
    
    return f'<?xml version="1.0" encoding="UTF-8"?><{root_name}>{_to_xml(data, root_name)}</{root_name}>'
