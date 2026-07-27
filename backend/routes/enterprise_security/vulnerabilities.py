import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.infrastructure.osv_nvd_integration import (
    get_osv_nvd_service,
)
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vulnerabilities", tags=["Enterprise Security - Vulnerabilities"])


class VulnerabilityEnrichRequest(BaseModel):
    cve_id: Optional[str] = None
    package_name: Optional[str] = None
    package_version: Optional[str] = None
    ecosystem: str = "pypi"


class PackageVulnerabilityRequest(BaseModel):
    packages: List[dict] = Field(
        ...,
        example=[
            {"name": "django", "version": "3.2.0", "ecosystem": "pypi"},
            {"name": "lodash", "version": "4.17.20", "ecosystem": "npm"}
        ]
    )


@router.get("/cve/{cve_id}")
async def get_cve_details(cve_id: str) -> Dict[str, Any]:
    try:
        vuln_db = await get_osv_nvd_service()
        cve_data = await vuln_db.query_by_cve(cve_id)

        if not cve_data:
            raise HTTPException(status_code=404, detail=f"CVE {cve_id} not found")

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
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.post("/packages")
async def check_package_vulnerabilities(request: PackageVulnerabilityRequest) -> Dict[str, Any]:
    from services.infrastructure.osv_nvd_integration import Ecosystem, PackageQuery

    try:
        vuln_db = await get_osv_nvd_service()
        results = []

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
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.post("/enrich")
async def enrich_vulnerability(request: VulnerabilityEnrichRequest) -> Dict[str, Any]:
    from services.infrastructure.osv_nvd_integration import Ecosystem, PackageQuery

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
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))
