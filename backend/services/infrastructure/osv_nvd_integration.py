"""
OSV/NVD Integration Service
Enhanced vulnerability database integration with Google OSV and NIST NVD APIs
Provides comprehensive vulnerability lookup, enrichment, and real-time updates
"""
import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import aiohttp

logger = logging.getLogger(__name__)


class VulnSource(Enum):
    """Vulnerability data sources"""
    OSV = "osv"
    NVD = "nvd"
    GITHUB_ADVISORY = "github_advisory"
    COMBINED = "combined"


class Ecosystem(Enum):
    """Package ecosystems supported"""
    NPM = "npm"
    PYPI = "PyPI"
    MAVEN = "Maven"
    GO = "Go"
    NUGET = "NuGet"
    RUBYGEMS = "RubyGems"
    CARGO = "crates.io"
    PACKAGIST = "Packagist"
    PUB = "Pub"
    HEX = "Hex"
    DEBIAN = "Debian"
    ALPINE = "Alpine"
    LINUX = "Linux"


@dataclass
class VulnerabilityMatch:
    """Matched vulnerability from OSV/NVD"""
    id: str
    source: VulnSource
    aliases: List[str] = field(default_factory=list)
    summary: str = ""
    details: str = ""
    severity: str = "unknown"
    cvss_score: Optional[float] = None
    cvss_vector: Optional[str] = None
    cwe_ids: List[str] = field(default_factory=list)
    published: Optional[datetime] = None
    modified: Optional[datetime] = None
    withdrawn: Optional[datetime] = None
    affected_packages: List[Dict[str, Any]] = field(default_factory=list)
    references: List[Dict[str, str]] = field(default_factory=list)
    credits: List[str] = field(default_factory=list)
    epss_score: Optional[float] = None
    epss_percentile: Optional[float] = None
    exploit_available: bool = False
    kev_listed: bool = False  # Known Exploited Vulnerabilities
    fix_available: bool = False
    fixed_versions: List[str] = field(default_factory=list)


@dataclass
class PackageQuery:
    """Package query for vulnerability lookup"""
    name: str
    version: str
    ecosystem: Ecosystem
    purl: Optional[str] = None  # Package URL


@dataclass
class VulnDatabaseStats:
    """Vulnerability database statistics"""
    total_vulnerabilities: int = 0
    osv_count: int = 0
    nvd_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    last_sync: Optional[datetime] = None
    cache_hit_rate: float = 0.0


class OSVNVDIntegrationService:
    """
    Integrated vulnerability database service using Google OSV and NIST NVD.
    Provides comprehensive vulnerability lookup with caching and enrichment.
    """

    # API Endpoints
    OSV_API_URL = "https://api.osv.dev/v1"
    NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    EPSS_API_URL = "https://api.first.org/data/v1/epss"
    CISA_KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

    def __init__(self, nvd_api_key: Optional[str] = None, cache_ttl_hours: int = 24):
        self.nvd_api_key = nvd_api_key
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._kev_cache: Set[str] = set()
        self._epss_cache: Dict[str, Dict[str, float]] = {}
        self._stats = VulnDatabaseStats()
        self._session: Optional[aiohttp.ClientSession] = None
        self._initialized = False

    async def initialize(self):
        """Initialize the service and load KEV list"""
        if self._initialized:
            return
        
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "ONYX/1.0"}
        )
        
        # Load CISA KEV list
        await self._load_kev_list()
        self._initialized = True
        logger.info("OSV/NVD Integration Service initialized")

    async def close(self):
        """Close the service and cleanup"""
        if self._session:
            await self._session.close()
            self._session = None
        self._initialized = False

    async def _load_kev_list(self):
        """Load CISA Known Exploited Vulnerabilities list"""
        try:
            async with self._session.get(self.CISA_KEV_URL) as response:
                if response.status == 200:
                    data = await response.json()
                    self._kev_cache = {
                        vuln["cveID"] 
                        for vuln in data.get("vulnerabilities", [])
                    }
                    logger.info(f"Loaded {len(self._kev_cache)} KEV entries")
        except Exception as e:
            logger.warning(f"Failed to load KEV list: {e}")

    async def query_osv(self, package: PackageQuery) -> List[VulnerabilityMatch]:
        """
        Query Google OSV for vulnerabilities affecting a package.
        
        Args:
            package: Package query with name, version, and ecosystem
            
        Returns:
            List of matching vulnerabilities
        """
        if not self._session:
            await self.initialize()

        cache_key = f"osv:{package.ecosystem.value}:{package.name}:{package.version}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now(timezone.utc) - cached["timestamp"] < self.cache_ttl:
                self._stats.cache_hit_rate += 0.01
                return cached["data"]

        vulnerabilities = []
        
        try:
            # OSV query by package
            query_payload = {
                "package": {
                    "name": package.name,
                    "ecosystem": package.ecosystem.value
                },
                "version": package.version
            }

            async with self._session.post(
                f"{self.OSV_API_URL}/query",
                json=query_payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    for vuln in data.get("vulns", []):
                        match = await self._parse_osv_vuln(vuln)
                        vulnerabilities.append(match)
                        self._stats.osv_count += 1

            # Cache results
            self._cache[cache_key] = {
                "data": vulnerabilities,
                "timestamp": datetime.now(timezone.utc)
            }

        except Exception as e:
            logger.error(f"OSV query failed for {package.name}: {e}")

        return vulnerabilities

    async def query_nvd(self, cve_id: str) -> Optional[VulnerabilityMatch]:
        """
        Query NIST NVD for CVE details.
        
        Args:
            cve_id: CVE identifier (e.g., CVE-2023-12345)
            
        Returns:
            Vulnerability match if found
        """
        if not self._session:
            await self.initialize()

        cache_key = f"nvd:{cve_id}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now(timezone.utc) - cached["timestamp"] < self.cache_ttl:
                return cached["data"]

        try:
            headers = {}
            if self.nvd_api_key:
                headers["apiKey"] = self.nvd_api_key

            params = {"cveId": cve_id}
            
            async with self._session.get(
                self.NVD_API_URL,
                params=params,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    vulns = data.get("vulnerabilities", [])
                    if vulns:
                        match = await self._parse_nvd_vuln(vulns[0]["cve"])
                        self._stats.nvd_count += 1
                        
                        # Enrich with EPSS score
                        await self._enrich_with_epss(match)
                        
                        # Check KEV list
                        match.kev_listed = cve_id in self._kev_cache
                        
                        # Cache result
                        self._cache[cache_key] = {
                            "data": match,
                            "timestamp": datetime.now(timezone.utc)
                        }
                        return match

        except Exception as e:
            logger.error(f"NVD query failed for {cve_id}: {e}")

        return None

    async def query_by_cve(self, cve_id: str) -> Optional[VulnerabilityMatch]:
        """
        Query vulnerability by CVE ID from all sources.
        Combines data from OSV and NVD for comprehensive information.
        """
        # First try NVD for authoritative CVE data
        nvd_result = await self.query_nvd(cve_id)
        
        # Also query OSV for additional context
        try:
            async with self._session.get(
                f"{self.OSV_API_URL}/vulns/{cve_id}"
            ) as response:
                if response.status == 200:
                    osv_data = await response.json()
                    osv_result = await self._parse_osv_vuln(osv_data)
                    
                    # Merge OSV data into NVD result
                    if nvd_result:
                        nvd_result.aliases.extend(osv_result.aliases)
                        nvd_result.affected_packages.extend(osv_result.affected_packages)
                        nvd_result.references.extend(osv_result.references)
                        if osv_result.fixed_versions:
                            nvd_result.fixed_versions = osv_result.fixed_versions
                            nvd_result.fix_available = True
                        return nvd_result
                    return osv_result
        except Exception:
            pass
        
        return nvd_result

    async def bulk_query(
        self, 
        packages: List[PackageQuery]
    ) -> Dict[str, List[VulnerabilityMatch]]:
        """
        Query multiple packages for vulnerabilities in parallel.
        
        Args:
            packages: List of packages to query
            
        Returns:
            Dictionary mapping package identifiers to vulnerabilities
        """
        results = {}
        
        # Batch OSV queries for efficiency
        batch_size = 100
        for i in range(0, len(packages), batch_size):
            batch = packages[i:i + batch_size]
            tasks = [self.query_osv(pkg) for pkg in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for pkg, result in zip(batch, batch_results):
                key = f"{pkg.ecosystem.value}:{pkg.name}@{pkg.version}"
                if isinstance(result, Exception):
                    logger.warning(f"Query failed for {key}: {result}")
                    results[key] = []
                else:
                    results[key] = result

        return results

    async def search_vulnerabilities(
        self,
        query: str,
        ecosystem: Optional[Ecosystem] = None,
        severity: Optional[str] = None,
        limit: int = 50
    ) -> List[VulnerabilityMatch]:
        """
        Search vulnerabilities by keyword, ecosystem, or severity.
        """
        results = []
        
        # Check if query is a CVE ID
        if re.match(r"CVE-\d{4}-\d+", query.upper()):
            result = await self.query_by_cve(query.upper())
            if result:
                return [result]

        # Search OSV
        try:
            search_payload = {"query": query}
            
            async with self._session.post(
                f"{self.OSV_API_URL}/querybatch",
                json={"queries": [search_payload]}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    for result_set in data.get("results", []):
                        for vuln in result_set.get("vulns", [])[:limit]:
                            match = await self._parse_osv_vuln(vuln)
                            
                            # Filter by severity if specified
                            if severity and match.severity.lower() != severity.lower():
                                continue
                                
                            results.append(match)

        except Exception as e:
            logger.error(f"Vulnerability search failed: {e}")

        return results[:limit]

    async def get_vulnerability_stats(self) -> VulnDatabaseStats:
        """Get vulnerability database statistics"""
        self._stats.total_vulnerabilities = self._stats.osv_count + self._stats.nvd_count
        self._stats.last_sync = datetime.now(timezone.utc)
        return self._stats

    async def enrich_findings(
        self, 
        findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enrich scan findings with OSV/NVD data.
        
        Args:
            findings: List of scan findings with CVE references
            
        Returns:
            Enriched findings with additional vulnerability data
        """
        enriched = []
        
        for finding in findings:
            enriched_finding = finding.copy()
            
            # Extract CVE IDs from finding
            cve_ids = self._extract_cve_ids(finding)
            
            if cve_ids:
                enriched_finding["vulnerability_enrichment"] = []
                
                for cve_id in cve_ids:
                    vuln_data = await self.query_by_cve(cve_id)
                    if vuln_data:
                        enriched_finding["vulnerability_enrichment"].append({
                            "cve_id": cve_id,
                            "severity": vuln_data.severity,
                            "cvss_score": vuln_data.cvss_score,
                            "epss_score": vuln_data.epss_score,
                            "kev_listed": vuln_data.kev_listed,
                            "exploit_available": vuln_data.exploit_available,
                            "fix_available": vuln_data.fix_available,
                            "fixed_versions": vuln_data.fixed_versions,
                            "references": vuln_data.references[:5]
                        })
                        
                        # Update severity based on enriched data
                        if vuln_data.kev_listed:
                            enriched_finding["kev_listed"] = True
                            enriched_finding["priority"] = "immediate"
                        
                        if vuln_data.epss_score and vuln_data.epss_score > 0.5:
                            enriched_finding["high_exploit_probability"] = True

            enriched.append(enriched_finding)

        return enriched

    def _extract_cve_ids(self, finding: Dict[str, Any]) -> List[str]:
        """Extract CVE IDs from a finding"""
        cve_ids = []
        
        # Check common fields
        for key in ["cve_id", "cve", "vulnerability_id", "id"]:
            if key in finding:
                value = finding[key]
                if isinstance(value, str) and value.upper().startswith("CVE-"):
                    cve_ids.append(value.upper())
        
        # Check description and message for CVE references
        text_fields = ["description", "message", "title", "details"]
        for field in text_fields:
            if field in finding:
                matches = re.findall(r"CVE-\d{4}-\d+", str(finding[field]).upper())
                cve_ids.extend(matches)

        return list(set(cve_ids))

    async def _parse_osv_vuln(self, vuln: Dict[str, Any]) -> VulnerabilityMatch:
        """Parse OSV vulnerability data"""
        severity = "unknown"
        cvss_score = None
        cvss_vector = None
        
        # Extract severity from database_specific or severity array
        if "severity" in vuln:
            for sev in vuln.get("severity", []):
                if sev.get("type") == "CVSS_V3":
                    cvss_vector = sev.get("score")
                    # Parse CVSS score from vector
                    if cvss_vector:
                        cvss_score = self._parse_cvss_score(cvss_vector)
                        severity = self._cvss_to_severity(cvss_score)
                        
        # Extract severity from database_specific
        db_specific = vuln.get("database_specific", {})
        if not severity or severity == "unknown":
            severity = db_specific.get("severity", "unknown").lower()

        # Parse affected packages
        affected_packages = []
        for affected in vuln.get("affected", []):
            pkg_info = {
                "package": affected.get("package", {}),
                "ranges": affected.get("ranges", []),
                "versions": affected.get("versions", []),
                "ecosystem_specific": affected.get("ecosystem_specific", {})
            }
            affected_packages.append(pkg_info)

        # Extract fixed versions
        fixed_versions = []
        for affected in vuln.get("affected", []):
            for range_info in affected.get("ranges", []):
                for event in range_info.get("events", []):
                    if "fixed" in event:
                        fixed_versions.append(event["fixed"])

        # Parse references
        references = [
            {"type": ref.get("type", "WEB"), "url": ref.get("url", "")}
            for ref in vuln.get("references", [])
        ]

        return VulnerabilityMatch(
            id=vuln.get("id", ""),
            source=VulnSource.OSV,
            aliases=vuln.get("aliases", []),
            summary=vuln.get("summary", ""),
            details=vuln.get("details", ""),
            severity=severity,
            cvss_score=cvss_score,
            cvss_vector=cvss_vector,
            cwe_ids=db_specific.get("cwe_ids", []),
            published=self._parse_datetime(vuln.get("published")),
            modified=self._parse_datetime(vuln.get("modified")),
            withdrawn=self._parse_datetime(vuln.get("withdrawn")),
            affected_packages=affected_packages,
            references=references,
            credits=[c.get("name", "") for c in vuln.get("credits", [])],
            fix_available=len(fixed_versions) > 0,
            fixed_versions=fixed_versions
        )

    async def _parse_nvd_vuln(self, cve: Dict[str, Any]) -> VulnerabilityMatch:
        """Parse NVD CVE data"""
        cve_id = cve.get("id", "")
        
        # Get descriptions
        descriptions = cve.get("descriptions", [])
        description = next(
            (d["value"] for d in descriptions if d.get("lang") == "en"),
            descriptions[0]["value"] if descriptions else ""
        )

        # Get CVSS metrics
        metrics = cve.get("metrics", {})
        cvss_score = None
        cvss_vector = None
        severity = "unknown"

        # Try CVSS 3.1 first, then 3.0, then 2.0
        for cvss_key in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
            if cvss_key in metrics and metrics[cvss_key]:
                cvss_data = metrics[cvss_key][0]["cvssData"]
                cvss_score = cvss_data.get("baseScore")
                cvss_vector = cvss_data.get("vectorString")
                severity = cvss_data.get("baseSeverity", "").lower()
                break

        # Get CWE IDs
        cwe_ids = []
        for weakness in cve.get("weaknesses", []):
            for desc in weakness.get("description", []):
                if desc.get("value", "").startswith("CWE-"):
                    cwe_ids.append(desc["value"])

        # Get references
        references = [
            {"type": "WEB", "url": ref.get("url", "")}
            for ref in cve.get("references", [])
        ]

        return VulnerabilityMatch(
            id=cve_id,
            source=VulnSource.NVD,
            aliases=[],
            summary=description[:200] + "..." if len(description) > 200 else description,
            details=description,
            severity=severity,
            cvss_score=cvss_score,
            cvss_vector=cvss_vector,
            cwe_ids=cwe_ids,
            published=self._parse_datetime(cve.get("published")),
            modified=self._parse_datetime(cve.get("lastModified")),
            references=references,
            kev_listed=cve_id in self._kev_cache
        )

    async def _enrich_with_epss(self, vuln: VulnerabilityMatch):
        """Enrich vulnerability with EPSS score"""
        if not vuln.id.startswith("CVE-"):
            return
            
        try:
            cache_key = f"epss:{vuln.id}"
            if cache_key in self._epss_cache:
                cached = self._epss_cache[cache_key]
                vuln.epss_score = cached.get("score")
                vuln.epss_percentile = cached.get("percentile")
                return

            async with self._session.get(
                f"{self.EPSS_API_URL}",
                params={"cve": vuln.id}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("data"):
                        epss_data = data["data"][0]
                        vuln.epss_score = float(epss_data.get("epss", 0))
                        vuln.epss_percentile = float(epss_data.get("percentile", 0))
                        
                        # High EPSS indicates exploit is likely
                        if vuln.epss_score > 0.1:
                            vuln.exploit_available = True
                            
                        self._epss_cache[cache_key] = {
                            "score": vuln.epss_score,
                            "percentile": vuln.epss_percentile
                        }
        except Exception as e:
            logger.debug(f"EPSS enrichment failed for {vuln.id}: {e}")

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except Exception:
            return None

    def _parse_cvss_score(self, vector: str) -> Optional[float]:
        """Parse CVSS score from vector string"""
        # Simple extraction from CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H format
        # The actual score would need full CVSS calculation
        # For now, return None and rely on API-provided scores
        return None

    def _cvss_to_severity(self, score: Optional[float]) -> str:
        """Convert CVSS score to severity"""
        if score is None:
            return "unknown"
        if score >= 9.0:
            return "critical"
        if score >= 7.0:
            return "high"
        if score >= 4.0:
            return "medium"
        if score >= 0.1:
            return "low"
        return "info"


# Singleton instance
_osv_nvd_service: Optional[OSVNVDIntegrationService] = None


async def get_osv_nvd_service(
    nvd_api_key: Optional[str] = None
) -> OSVNVDIntegrationService:
    """Get or create OSV/NVD integration service instance"""
    global _osv_nvd_service
    if _osv_nvd_service is None:
        _osv_nvd_service = OSVNVDIntegrationService(nvd_api_key)
        await _osv_nvd_service.initialize()
    return _osv_nvd_service
