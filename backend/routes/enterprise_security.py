"""
Enterprise Security Routes
API endpoints for enterprise security features:
- OSV/NVD Vulnerability Database Integration
- SBOM Generation (SPDX/CycloneDX)
- Security Trends Dashboard
- Scan Comparison & Delta Analysis
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Response, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from dataclasses import asdict
import logging
import os

# Environment check for safe error messages
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() == "production"

def safe_error_detail(error: Exception, operation: str) -> str:
    """Return safe error message - hide details in production"""
    if IS_PRODUCTION:
        return f"{operation} failed. Please try again later."
    return f"{operation} failed: {str(error)}"
import json

# Import services
from services.infrastructure.osv_nvd_integration import (
    get_osv_nvd_service,
    OSVNVDIntegrationService
)
from services.scanning.utils.sbom import (
    get_sbom_service,
    SBOMGeneratorService,
    SBOMFormat
)
from services.security.security_trends import (
    get_security_trends_service,
    SecurityTrendsService,
    TrendPeriod
)
from services.scanning.utils.comparison import (
    get_scan_comparison_service,
    ScanComparisonService
)
from models.user import User
from services.auth.auth_service import AuthService

logger = logging.getLogger(__name__)
# Changed prefix to avoid conflict with enterprise.py which also uses /api/enterprise
router = APIRouter(prefix="/api/v1/enterprise-security", tags=["Enterprise Security"])
security = HTTPBearer()
auth_service = AuthService()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    return await auth_service.get_current_user(credentials)


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
        vuln_db = await get_osv_nvd_service()
        cve_data = await vuln_db.query_by_cve(cve_id)
        
        if not cve_data:
            raise HTTPException(status_code=404, detail=f"CVE {cve_id} not found")
        
        # Convert VulnerabilityMatch to dict
        result = {
            "id": cve_data.id,
            "source": cve_data.source.value,
            "aliases": cve_data.aliases,
            "summary": cve_data.summary,
            "details": cve_data.details,
            "severity": cve_data.severity,
            "cvss_score": cve_data.cvss_score,
            "cvss_vector": cve_data.cvss_vector,
            "cwe_ids": cve_data.cwe_ids,
            "published": cve_data.published.isoformat() if cve_data.published else None,
            "modified": cve_data.modified.isoformat() if cve_data.modified else None,
            "affected_packages": cve_data.affected_packages,
            "references": cve_data.references,
            "epss_score": cve_data.epss_score,
            "epss_percentile": cve_data.epss_percentile,
            "exploit_available": cve_data.exploit_available,
            "kev_listed": cve_data.kev_listed,
            "fix_available": cve_data.fix_available,
            "fixed_versions": cve_data.fixed_versions
        }
        
        return {
            "success": True,
            "data": result
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
    from services.infrastructure.osv_nvd_integration import PackageQuery, Ecosystem
    
    try:
        vuln_db = await get_osv_nvd_service()
        results = []
        
        # Map ecosystem string to Ecosystem enum
        ecosystem_map = {
            "pypi": Ecosystem.PYPI,
            "npm": Ecosystem.NPM,
            "maven": Ecosystem.MAVEN,
            "go": Ecosystem.GO,
            "nuget": Ecosystem.NUGET,
            "rubygems": Ecosystem.RUBYGEMS,
            "cargo": Ecosystem.CARGO,
        }
        
        for pkg in request.packages:
            eco_str = pkg.get("ecosystem", "pypi").lower()
            ecosystem = ecosystem_map.get(eco_str, Ecosystem.PYPI)
            
            pkg_query = PackageQuery(
                name=pkg["name"],
                version=pkg.get("version", ""),
                ecosystem=ecosystem
            )
            
            vulns = await vuln_db.query_osv(pkg_query)
            
            # Convert VulnerabilityMatch objects to dicts
            vuln_list = [
                {
                    "id": v.id,
                    "severity": v.severity,
                    "cvss_score": v.cvss_score,
                    "summary": v.summary,
                    "fix_available": v.fix_available,
                    "fixed_versions": v.fixed_versions
                }
                for v in vulns
            ]
            
            results.append({
                "package": pkg["name"],
                "version": pkg.get("version"),
                "ecosystem": pkg.get("ecosystem", "pypi"),
                "vulnerabilities": vuln_list,
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
    from services.infrastructure.osv_nvd_integration import PackageQuery, Ecosystem
    
    try:
        vuln_db = await get_osv_nvd_service()
        
        enriched_data = {}
        
        if request.cve_id:
            cve_data = await vuln_db.query_by_cve(request.cve_id)
            if cve_data:
                enriched_data["cve_details"] = {
                    "id": cve_data.id,
                    "source": cve_data.source.value,
                    "aliases": cve_data.aliases,
                    "summary": cve_data.summary,
                    "details": cve_data.details,
                    "severity": cve_data.severity,
                    "cvss_score": cve_data.cvss_score,
                    "cvss_vector": cve_data.cvss_vector,
                    "cwe_ids": cve_data.cwe_ids,
                    "epss_score": cve_data.epss_score,
                    "epss_percentile": cve_data.epss_percentile,
                    "exploit_available": cve_data.exploit_available,
                    "kev_listed": cve_data.kev_listed,
                    "fix_available": cve_data.fix_available,
                    "fixed_versions": cve_data.fixed_versions
                }
        
        if request.package_name:
            ecosystem_map = {
                "pypi": Ecosystem.PYPI,
                "npm": Ecosystem.NPM,
                "maven": Ecosystem.MAVEN,
                "go": Ecosystem.GO,
            }
            ecosystem = ecosystem_map.get(request.ecosystem.lower(), Ecosystem.PYPI)
            
            pkg_query = PackageQuery(
                name=request.package_name,
                version=request.package_version or "",
                ecosystem=ecosystem
            )
            
            vulns = await vuln_db.query_osv(pkg_query)
            enriched_data["package_vulnerabilities"] = [
                {
                    "id": v.id,
                    "severity": v.severity,
                    "cvss_score": v.cvss_score,
                    "summary": v.summary,
                    "fix_available": v.fix_available,
                    "fixed_versions": v.fixed_versions
                }
                for v in vulns
            ]
        
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
        sbom_gen = get_sbom_service()
        
        sbom_format = SBOMFormat.SPDX if request.format.lower() == "spdx" else SBOMFormat.CYCLONEDX
        
        sbom = await sbom_gen.generate_sbom(
            repository_path=request.repository_path,
            output_format=sbom_format,
            include_dev_dependencies=request.include_dev_deps,
            enrich_with_vulnerabilities=request.enrich_vulnerabilities
        )
        
        # Convert SBOM dataclass to dict
        sbom_dict = _sbom_to_dict(sbom)
        
        return {
            "success": True,
            "format": request.format,
            "sbom": sbom_dict
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
        sbom_gen = get_sbom_service()
        
        sbom_format = SBOMFormat.SPDX if format.lower() == "spdx" else SBOMFormat.CYCLONEDX
        
        sbom = await sbom_gen.generate_sbom(
            repository_path=repository_path,
            output_format=sbom_format
        )
        
        sbom_dict = _sbom_to_dict(sbom)
        
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

def _sbom_to_dict(sbom) -> dict:
    """Convert SBOM dataclass to dictionary, handling nested dataclasses and enums"""
    try:
        result = asdict(sbom)
        # Handle any enum values
        def convert_enums(obj):
            if isinstance(obj, dict):
                return {k: convert_enums(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_enums(item) for item in obj]
            elif isinstance(obj, Enum):
                return obj.value
            elif hasattr(obj, 'isoformat'):  # datetime
                return obj.isoformat()
            return obj
        return convert_enums(result)
    except Exception as e:
        logger.warning(f"Failed to convert SBOM to dict via asdict: {e}")
        # Fallback to manual conversion
        return vars(sbom) if hasattr(sbom, '__dict__') else str(sbom)


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

