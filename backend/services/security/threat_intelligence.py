"""
Threat Intelligence System
CVE database integration, real-time threat feeds, and zero-day alerts

NOTE: This module uses SQLite for CVE/threat caching.
Future versions should migrate to MongoDB for consistency.
"""
import asyncio
import aiohttp
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from dataclasses import dataclass, field
import hashlib
import gzip
import sqlite3
from urllib.parse import urljoin

# Import canonical enums from models.base (SINGLE SOURCE OF TRUTH)
from models.base import ThreatSeverity, ThreatType, ThreatSource

logger = logging.getLogger(__name__)

@dataclass
class ThreatFeed:
    """Threat intelligence feed configuration"""
    feed_id: str
    name: str
    source: ThreatSource
    url: str
    enabled: bool
    update_frequency_hours: int
    last_updated: Optional[datetime] = None
    total_entries: int = 0
    api_key: Optional[str] = None
    feed_format: str = "json"  # json, xml, csv
    priority: int = 1  # 1=highest, 5=lowest

@dataclass
class CVEData:
    """CVE vulnerability data"""
    cve_id: str
    description: str
    severity: ThreatSeverity
    cvss_score: float
    cvss_vector: Optional[str]
    published_date: datetime
    modified_date: datetime
    affected_products: List[str] = field(default_factory=list)
    reference_urls: List[str] = field(default_factory=list)
    cwe_ids: List[str] = field(default_factory=list)
    epss_score: Optional[float] = None
    kev_listed: bool = False
    exploit_available: bool = False
    vendor_advisories: List[str] = field(default_factory=list)

@dataclass
class ThreatAlert:
    """Real-time threat alert"""
    alert_id: str
    threat_type: ThreatType
    severity: ThreatSeverity
    title: str
    description: str
    source: ThreatSource
    indicators: List[str] = field(default_factory=list)
    matched_patterns: List[str] = field(default_factory=list)
    affected_repositories: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    actionable: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ZeroDayIndicator:
    """Zero-day threat indicators"""
    indicator_id: str
    pattern: str
    description: str
    confidence: float  # 0.0 to 1.0
    keywords: List[str] = field(default_factory=list)
    file_patterns: List[str] = field(default_factory=list)
    techniques: List[str] = field(default_factory=list)  # MITRE ATT&CK techniques
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class ThreatIntelligenceEngine:
    """Core threat intelligence engine"""
    
    def __init__(self, data_dir: str = "data/threats"):
        """Initialize threat intelligence engine"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Database paths
        self.cve_db_path = self.data_dir / "cve_database.db"
        self.threat_db_path = self.data_dir / "threat_intelligence.db"
        
        # Initialize databases
        self._init_databases()
        
        # Threat feed configurations
        self.threat_feeds = {
            ThreatSource.NVD: {
                "url": "https://services.nvd.nist.gov/rest/json/cves/2.0",
                "api_key": None,  # Optional API key for rate limiting
                "enabled": True,
                "update_frequency": 3600  # 1 hour
            },
            ThreatSource.CISA_KEV: {
                "url": "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
                "enabled": True,
                "update_frequency": 1800  # 30 minutes
            },
            ThreatSource.OSV: {
                "url": "https://osv-vulnerabilities.storage.googleapis.com",
                "enabled": True,
                "update_frequency": 3600  # 1 hour
            },
            ThreatSource.GITHUB_ADVISORY: {
                "url": "https://api.github.com/advisories",
                "enabled": True,
                "update_frequency": 1800  # 30 minutes
            }
        }
        
        # Zero-day detection patterns
        self.zero_day_indicators = []
        self._load_zero_day_indicators()
        
        # Active threat alerts
        self.active_alerts: Dict[str, ThreatAlert] = {}
        
        # Session for HTTP requests
        self.session: Optional[aiohttp.ClientSession] = None
    
    def _init_databases(self):
        """Initialize SQLite databases"""
        try:
            # CVE database schema
            with sqlite3.connect(self.cve_db_path) as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS cves (
                    cve_id TEXT PRIMARY KEY,
                    description TEXT,
                    severity TEXT,
                    cvss_score REAL,
                    cvss_vector TEXT,
                    published_date TEXT,
                    modified_date TEXT,
                    affected_products TEXT,  -- JSON array
                    reference_urls TEXT,         -- JSON array
                    cwe_ids TEXT,           -- JSON array
                    epss_score REAL,
                    kev_listed INTEGER,
                    exploit_available INTEGER,
                    vendor_advisories TEXT,  -- JSON array
                    created_at TEXT,
                    updated_at TEXT
                )
                """)
                
                conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cve_severity ON cves(severity);
                """)
                
                conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cve_published ON cves(published_date);
                """)
                
                conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cve_score ON cves(cvss_score);
                """)
            
            # Threat intelligence database schema
            with sqlite3.connect(self.threat_db_path) as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS threat_alerts (
                    alert_id TEXT PRIMARY KEY,
                    threat_type TEXT,
                    severity TEXT,
                    title TEXT,
                    description TEXT,
                    source TEXT,
                    indicators TEXT,            -- JSON array
                    matched_patterns TEXT,      -- JSON array
                    affected_repositories TEXT, -- JSON array
                    created_at TEXT,
                    expires_at TEXT,
                    actionable INTEGER,
                    metadata TEXT,              -- JSON object
                    resolved INTEGER DEFAULT 0
                )
                """)
                
                conn.execute("""
                CREATE TABLE IF NOT EXISTS zero_day_indicators (
                    indicator_id TEXT PRIMARY KEY,
                    pattern TEXT,
                    description TEXT,
                    confidence REAL,
                    keywords TEXT,      -- JSON array
                    file_patterns TEXT, -- JSON array
                    techniques TEXT,    -- JSON array
                    created_at TEXT,
                    enabled INTEGER DEFAULT 1
                )
                """)
                
                conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_threat_severity ON threat_alerts(severity);
                """)
                
                conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_threat_created ON threat_alerts(created_at);
                """)
            
            logger.info("Threat intelligence databases initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize databases: {e}")
            raise
    
    async def start(self):
        """Start threat intelligence engine"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"User-Agent": "ONYX-ThreatIntel/1.0"}
            )
            
            # Start background tasks
            asyncio.create_task(self._threat_feed_updater())
            asyncio.create_task(self._alert_monitor())
            
            logger.info("Threat intelligence engine started")
            
        except Exception as e:
            logger.error(f"Failed to start threat intelligence engine: {e}")
            raise
    
    async def stop(self):
        """Stop threat intelligence engine"""
        if self.session:
            await self.session.close()
        logger.info("Threat intelligence engine stopped")
    
    async def _threat_feed_updater(self):
        """Background task to update threat feeds"""
        while True:
            try:
                for source, config in self.threat_feeds.items():
                    if config["enabled"]:
                        await self._update_threat_feed(source, config)
                
                # Wait before next update cycle
                await asyncio.sleep(min(config["update_frequency"] for config in self.threat_feeds.values()))
                
            except Exception as e:
                logger.error(f"Error in threat feed updater: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _update_threat_feed(self, source: ThreatSource, config: Dict[str, Any]):
        """Update specific threat feed"""
        try:
            if source == ThreatSource.NVD:
                await self._update_nvd_feed(config)
            elif source == ThreatSource.CISA_KEV:
                await self._update_cisa_kev_feed(config)
            elif source == ThreatSource.OSV:
                await self._update_osv_feed(config)
            elif source == ThreatSource.GITHUB_ADVISORY:
                await self._update_github_advisory_feed(config)
                
            logger.info(f"Updated threat feed: {source.value}")
            
        except Exception as e:
            logger.error(f"Failed to update {source.value} feed: {e}")
    
    async def _update_nvd_feed(self, config: Dict[str, Any]):
        """Update NVD CVE feed"""
        if not self.session:
            return
        
        try:
            # Get recent CVEs (last 7 days)
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=7)
            
            params = {
                "pubStartDate": start_date.strftime("%Y-%m-%dT%H:%M:%S.000"),
                "pubEndDate": end_date.strftime("%Y-%m-%dT%H:%M:%S.000"),
                "resultsPerPage": 100
            }
            
            headers = {}
            if config.get("api_key"):
                headers["apiKey"] = config["api_key"]
            
            async with self.session.get(config["url"], params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    cves = data.get("vulnerabilities", [])
                    
                    for cve_item in cves:
                        cve_data = await self._parse_nvd_cve(cve_item)
                        if cve_data:
                            await self._store_cve(cve_data)
                            
                            # Check for zero-day indicators
                            await self._check_zero_day_indicators(cve_data)
                
        except Exception as e:
            logger.error(f"Failed to update NVD feed: {e}")
    
    async def _update_cisa_kev_feed(self, config: Dict[str, Any]):
        """Update CISA Known Exploited Vulnerabilities feed"""
        if not self.session:
            return
        
        try:
            async with self.session.get(config["url"]) as response:
                if response.status == 200:
                    data = await response.json()
                    vulnerabilities = data.get("vulnerabilities", [])
                    
                    for vuln in vulnerabilities:
                        cve_id = vuln.get("cveID")
                        if cve_id:
                            # Update CVE with KEV status
                            await self._update_cve_kev_status(cve_id, True)
                            
                            # Create high-priority alert for new KEV entries
                            await self._create_kev_alert(vuln)
                
        except Exception as e:
            logger.error(f"Failed to update CISA KEV feed: {e}")
    
    async def _update_osv_feed(self, config: Dict[str, Any]):
        """Update OSV (Open Source Vulnerabilities) feed"""
        if not self.session:
            return
        
        try:
            # Query OSV API for recent vulnerabilities
            ecosystems = ["PyPI", "npm", "Maven", "Go", "RubyGems", "NuGet"]
            
            for ecosystem in ecosystems:
                query = {
                    "version": "1",
                    "package": {
                        "ecosystem": ecosystem
                    }
                }
                
                async with self.session.post(
                    f"{config['url']}/v1/query",
                    json=query
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        vulns = data.get("vulns", [])
                        
                        for vuln in vulns:
                            cve_data = await self._parse_osv_vulnerability(vuln)
                            if cve_data:
                                await self._store_cve(cve_data)
                
        except Exception as e:
            logger.error(f"Failed to update OSV feed: {e}")
    
    async def _update_github_advisory_feed(self, config: Dict[str, Any]):
        """Update GitHub Security Advisory feed"""
        if not self.session:
            return
        
        try:
            params = {
                "per_page": 100,
                "sort": "published",
                "direction": "desc"
            }
            
            async with self.session.get(config["url"], params=params) as response:
                if response.status == 200:
                    advisories = await response.json()
                    
                    for advisory in advisories:
                        cve_data = await self._parse_github_advisory(advisory)
                        if cve_data:
                            await self._store_cve(cve_data)
                
        except Exception as e:
            logger.error(f"Failed to update GitHub Advisory feed: {e}")
    
    async def _parse_nvd_cve(self, cve_item: Dict[str, Any]) -> Optional[CVEData]:
        """Parse NVD CVE data"""
        try:
            cve = cve_item.get("cve", {})
            cve_id = cve.get("id", "")
            
            if not cve_id:
                return None
            
            # Parse description
            descriptions = cve.get("descriptions", [])
            description = ""
            for desc in descriptions:
                if desc.get("lang") == "en":
                    description = desc.get("value", "")
                    break
            
            # Parse CVSS scores
            metrics = cve.get("metrics", {})
            cvss_score = 0.0
            cvss_vector = None
            severity = ThreatSeverity.LOW
            
            # Try CVSS v3.1 first, then v3.0, then v2.0
            for cvss_version in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
                if cvss_version in metrics:
                    cvss_data = metrics[cvss_version][0]["cvssData"]
                    cvss_score = cvss_data.get("baseScore", 0.0)
                    cvss_vector = cvss_data.get("vectorString", "")
                    
                    # Map CVSS score to severity
                    if cvss_score >= 9.0:
                        severity = ThreatSeverity.CRITICAL
                    elif cvss_score >= 7.0:
                        severity = ThreatSeverity.HIGH
                    elif cvss_score >= 4.0:
                        severity = ThreatSeverity.MEDIUM
                    else:
                        severity = ThreatSeverity.LOW
                    break
            
            # Parse dates
            published_date = datetime.fromisoformat(cve.get("published", "").replace("Z", "+00:00"))
            modified_date = datetime.fromisoformat(cve.get("lastModified", "").replace("Z", "+00:00"))
            
            # Parse affected products
            affected_products = []
            configurations = cve.get("configurations", [])
            for config in configurations:
                nodes = config.get("nodes", [])
                for node in nodes:
                    cpe_matches = node.get("cpeMatch", [])
                    for match in cpe_matches:
                        if match.get("vulnerable", False):
                            affected_products.append(match.get("criteria", ""))
            
            # Parse references
            references = []
            ref_list = cve.get("references", [])
            for ref in ref_list:
                references.append(ref.get("url", ""))
            
            # Parse CWE IDs
            cwe_ids = []
            weaknesses = cve.get("weaknesses", [])
            for weakness in weaknesses:
                descriptions = weakness.get("description", [])
                for desc in descriptions:
                    if desc.get("lang") == "en":
                        cwe_ids.append(desc.get("value", ""))
            
            return CVEData(
                cve_id=cve_id,
                description=description,
                severity=severity,
                cvss_score=cvss_score,
                cvss_vector=cvss_vector,
                published_date=published_date,
                modified_date=modified_date,
                affected_products=affected_products,
                reference_urls=references,
                cwe_ids=cwe_ids
            )
            
        except Exception as e:
            logger.error(f"Failed to parse NVD CVE: {e}")
            return None
    
    async def _parse_osv_vulnerability(self, vuln: Dict[str, Any]) -> Optional[CVEData]:
        """Parse OSV vulnerability data"""
        try:
            vuln_id = vuln.get("id", "")
            
            # Extract CVE ID if present
            cve_id = ""
            aliases = vuln.get("aliases", [])
            for alias in aliases:
                if alias.startswith("CVE-"):
                    cve_id = alias
                    break
            
            if not cve_id:
                cve_id = vuln_id  # Use OSV ID if no CVE
            
            summary = vuln.get("summary", "")
            details = vuln.get("details", "")
            description = f"{summary}\n{details}".strip()
            
            # Parse severity
            severity = ThreatSeverity.MEDIUM
            severity_list = vuln.get("severity", [])
            for sev in severity_list:
                if sev.get("type") == "CVSS_V3":
                    score = sev.get("score", "")
                    if score:
                        cvss_score = float(score.split("/")[0])
                        if cvss_score >= 9.0:
                            severity = ThreatSeverity.CRITICAL
                        elif cvss_score >= 7.0:
                            severity = ThreatSeverity.HIGH
                        elif cvss_score >= 4.0:
                            severity = ThreatSeverity.MEDIUM
                        else:
                            severity = ThreatSeverity.LOW
            
            # Parse dates
            published_date = datetime.fromisoformat(vuln.get("published", "").replace("Z", "+00:00"))
            modified_date = datetime.fromisoformat(vuln.get("modified", "").replace("Z", "+00:00"))
            
            # Parse affected packages
            affected_products = []
            affected = vuln.get("affected", [])
            for pkg in affected:
                package = pkg.get("package", {})
                ecosystem = package.get("ecosystem", "")
                name = package.get("name", "")
                if ecosystem and name:
                    affected_products.append(f"{ecosystem}:{name}")
            
            # Parse references
            references = []
            ref_list = vuln.get("references", [])
            for ref in ref_list:
                references.append(ref.get("url", ""))
            
            return CVEData(
                cve_id=cve_id,
                description=description,
                severity=severity,
                cvss_score=0.0,  # OSV doesn't always provide CVSS scores
                cvss_vector=None,
                published_date=published_date,
                modified_date=modified_date,
                affected_products=affected_products,
                reference_urls=references,
                cwe_ids=[]
            )
            
        except Exception as e:
            logger.error(f"Failed to parse OSV vulnerability: {e}")
            return None
    
    async def _parse_github_advisory(self, advisory: Dict[str, Any]) -> Optional[CVEData]:
        """Parse GitHub Security Advisory data"""
        try:
            # Validate that advisory is a dictionary
            if not isinstance(advisory, dict):
                logger.debug(f"Skipping non-dict advisory: {type(advisory)}")
                return None
            
            ghsa_id = advisory.get("ghsa_id", "")
            cve_id = advisory.get("cve_id", ghsa_id)
            
            summary = advisory.get("summary", "")
            description = advisory.get("description", summary)
            
            # Parse severity
            severity_str = advisory.get("severity", "medium").lower()
            severity_map = {
                "critical": ThreatSeverity.CRITICAL,
                "high": ThreatSeverity.HIGH,
                "medium": ThreatSeverity.MEDIUM,
                "low": ThreatSeverity.LOW
            }
            severity = severity_map.get(severity_str, ThreatSeverity.MEDIUM)
            
            # Parse CVSS
            cvss = advisory.get("cvss", {})
            cvss_score = cvss.get("score", 0.0)
            cvss_vector = cvss.get("vector_string", "")
            
            # Parse dates
            published_date = datetime.fromisoformat(advisory.get("published_at", "").replace("Z", "+00:00"))
            updated_date = datetime.fromisoformat(advisory.get("updated_at", "").replace("Z", "+00:00"))
            
            # Parse affected packages
            affected_products = []
            vulnerabilities = advisory.get("vulnerabilities", [])
            for vuln in vulnerabilities:
                package = vuln.get("package", {})
                ecosystem = package.get("ecosystem", "")
                name = package.get("name", "")
                if ecosystem and name:
                    affected_products.append(f"{ecosystem}:{name}")
            
            # Parse references
            references = []
            ref_list = advisory.get("references", [])
            for ref in ref_list:
                references.append(ref.get("url", ""))
            
            # Parse CWEs
            cwe_ids = []
            cwes = advisory.get("cwes", [])
            for cwe in cwes:
                cwe_ids.append(cwe.get("cwe_id", ""))
            
            return CVEData(
                cve_id=cve_id,
                description=description,
                severity=severity,
                cvss_score=cvss_score,
                cvss_vector=cvss_vector,
                published_date=published_date,
                modified_date=updated_date,
                affected_products=affected_products,
                reference_urls=references,
                cwe_ids=cwe_ids
            )
            
        except Exception as e:
            logger.error(f"Failed to parse GitHub Advisory: {e}")
            return None
    
    async def _store_cve(self, cve_data: CVEData):
        """Store CVE data in database"""
        try:
            with sqlite3.connect(self.cve_db_path) as conn:
                conn.execute("""
                INSERT OR REPLACE INTO cves (
                    cve_id, description, severity, cvss_score, cvss_vector,
                    published_date, modified_date, affected_products, reference_urls,
                    cwe_ids, epss_score, kev_listed, exploit_available,
                    vendor_advisories, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cve_data.cve_id,
                    cve_data.description,
                    cve_data.severity.value,
                    cve_data.cvss_score,
                    cve_data.cvss_vector,
                    cve_data.published_date.isoformat(),
                    cve_data.modified_date.isoformat(),
                    json.dumps(cve_data.affected_products),
                    json.dumps(cve_data.reference_urls),
                    json.dumps(cve_data.cwe_ids),
                    cve_data.epss_score,
                    int(cve_data.kev_listed),
                    int(cve_data.exploit_available),
                    json.dumps(cve_data.vendor_advisories),
                    datetime.now(timezone.utc).isoformat(),
                    datetime.now(timezone.utc).isoformat()
                ))
            
        except Exception as e:
            logger.error(f"Failed to store CVE {cve_data.cve_id}: {e}")
    
    async def _update_cve_kev_status(self, cve_id: str, kev_listed: bool):
        """Update CVE KEV status"""
        try:
            with sqlite3.connect(self.cve_db_path) as conn:
                conn.execute("""
                UPDATE cves SET kev_listed = ?, updated_at = ? WHERE cve_id = ?
                """, (int(kev_listed), datetime.now(timezone.utc).isoformat(), cve_id))
            
        except Exception as e:
            logger.error(f"Failed to update KEV status for {cve_id}: {e}")
    
    async def _create_kev_alert(self, vuln: Dict[str, Any]):
        """Create alert for new CISA KEV entry"""
        try:
            cve_id = vuln.get("cveID", "")
            vendor_project = vuln.get("vendorProject", "")
            product = vuln.get("product", "")
            vulnerability_name = vuln.get("vulnerabilityName", "")
            
            alert = ThreatAlert(
                alert_id=f"kev_{cve_id}_{hashlib.md5(cve_id.encode()).hexdigest()[:8]}",
                threat_type=ThreatType.CVE,
                severity=ThreatSeverity.HIGH,
                title=f"CISA KEV Alert: {cve_id}",
                description=f"CISA has added {cve_id} to the Known Exploited Vulnerabilities catalog. "
                           f"Vulnerability: {vulnerability_name} in {vendor_project} {product}",
                source=ThreatSource.CISA_KEV,
                indicators=[cve_id, product, vendor_project],
                metadata={
                    "cve_id": cve_id,
                    "vendor_project": vendor_project,
                    "product": product,
                    "vulnerability_name": vulnerability_name,
                    "due_date": vuln.get("dueDate", ""),
                    "required_action": vuln.get("requiredAction", "")
                }
            )
            
            await self._store_threat_alert(alert)
            self.active_alerts[alert.alert_id] = alert
            
            logger.warning(f"CISA KEV Alert created: {cve_id}")
            
        except Exception as e:
            logger.error(f"Failed to create KEV alert: {e}")
    
    def _load_zero_day_indicators(self):
        """Load zero-day detection indicators"""
        try:
            with sqlite3.connect(self.threat_db_path) as conn:
                cursor = conn.execute("""
                SELECT indicator_id, pattern, description, confidence, keywords, 
                       file_patterns, techniques FROM zero_day_indicators 
                WHERE enabled = 1
                """)
                
                for row in cursor.fetchall():
                    indicator = ZeroDayIndicator(
                        indicator_id=row[0],
                        pattern=row[1],
                        description=row[2],
                        confidence=row[3],
                        keywords=json.loads(row[4]),
                        file_patterns=json.loads(row[5]),
                        techniques=json.loads(row[6])
                    )
                    self.zero_day_indicators.append(indicator)
            
            logger.info(f"Loaded {len(self.zero_day_indicators)} zero-day indicators")
            
        except Exception as e:
            logger.error(f"Failed to load zero-day indicators: {e}")
    
    async def _ensure_default_zero_day_indicators(self):
        """Ensure default zero-day indicators exist"""
        # Add default zero-day indicators if none exist
        if not self.zero_day_indicators:
            await self._create_default_zero_day_indicators()
    
    async def _create_default_zero_day_indicators(self):
        """Create default zero-day detection indicators"""
        default_indicators = [
            ZeroDayIndicator(
                indicator_id="zd_001",
                pattern=r"(0day|zero.?day|zeroday)",
                description="Zero-day keyword detection",
                confidence=0.7,
                keywords=["0day", "zero-day", "zeroday", "undisclosed", "unknown vulnerability"],
                file_patterns=["*.py", "*.js", "*.java", "*.c", "*.cpp"],
                techniques=["T1068", "T1190"]  # Exploitation for Privilege Escalation, Exploit Public-Facing Application
            ),
            ZeroDayIndicator(
                indicator_id="zd_002",
                pattern=r"(exploit|payload|shellcode).*(unknown|undisclosed|private)",
                description="Unknown exploit code detection",
                confidence=0.8,
                keywords=["unknown exploit", "private exploit", "undisclosed payload"],
                file_patterns=["*.py", "*.sh", "*.ps1"],
                techniques=["T1203", "T1204"]  # Exploitation for Client Execution, User Execution
            ),
            ZeroDayIndicator(
                indicator_id="zd_003",
                pattern=r"(CVE-\d{4}-\d{4,7}).*(no.?patch|unpatched|unfixed)",
                description="Unpatched CVE references",
                confidence=0.9,
                keywords=["no patch", "unpatched", "unfixed", "no fix available"],
                file_patterns=["*.md", "*.txt", "*.rst"],
                techniques=["T1068"]
            )
        ]
        
        for indicator in default_indicators:
            await self._store_zero_day_indicator(indicator)
            self.zero_day_indicators.append(indicator)
    
    async def _store_zero_day_indicator(self, indicator: ZeroDayIndicator):
        """Store zero-day indicator in database"""
        try:
            with sqlite3.connect(self.threat_db_path) as conn:
                conn.execute("""
                INSERT OR REPLACE INTO zero_day_indicators (
                    indicator_id, pattern, description, confidence, keywords,
                    file_patterns, techniques, created_at, enabled
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    indicator.indicator_id,
                    indicator.pattern,
                    indicator.description,
                    indicator.confidence,
                    json.dumps(indicator.keywords),
                    json.dumps(indicator.file_patterns),
                    json.dumps(indicator.techniques),
                    indicator.created_at.isoformat(),
                    1
                ))
            
        except Exception as e:
            logger.error(f"Failed to store zero-day indicator: {e}")
    
    async def _check_zero_day_indicators(self, cve_data: CVEData):
        """Check CVE against zero-day indicators"""
        try:
            for indicator in self.zero_day_indicators:
                # Check pattern against CVE description
                if re.search(indicator.pattern, cve_data.description, re.IGNORECASE):
                    # Check keywords
                    keyword_matches = []
                    for keyword in indicator.keywords:
                        if keyword.lower() in cve_data.description.lower():
                            keyword_matches.append(keyword)
                    
                    if keyword_matches:
                        # Create zero-day alert
                        alert = ThreatAlert(
                            alert_id=f"zd_{cve_data.cve_id}_{indicator.indicator_id}",
                            threat_type=ThreatType.ZERO_DAY,
                            severity=ThreatSeverity.CRITICAL,
                            title=f"Potential Zero-Day: {cve_data.cve_id}",
                            description=f"CVE {cve_data.cve_id} matches zero-day indicator '{indicator.description}'. "
                                       f"Matched keywords: {', '.join(keyword_matches)}",
                            source=ThreatSource.CUSTOM,
                            indicators=[cve_data.cve_id] + keyword_matches,
                            matched_patterns=[indicator.pattern],
                            metadata={
                                "cve_id": cve_data.cve_id,
                                "indicator_id": indicator.indicator_id,
                                "confidence": indicator.confidence,
                                "matched_keywords": keyword_matches,
                                "mitre_techniques": indicator.techniques
                            }
                        )
                        
                        await self._store_threat_alert(alert)
                        self.active_alerts[alert.alert_id] = alert
                        
                        logger.critical(f"Zero-day alert created: {cve_data.cve_id}")
            
        except Exception as e:
            logger.error(f"Failed to check zero-day indicators: {e}")
    
    async def _store_threat_alert(self, alert: ThreatAlert):
        """Store threat alert in database"""
        try:
            with sqlite3.connect(self.threat_db_path) as conn:
                conn.execute("""
                INSERT OR REPLACE INTO threat_alerts (
                    alert_id, threat_type, severity, title, description, source,
                    indicators, matched_patterns, affected_repositories,
                    created_at, expires_at, actionable, metadata, resolved
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.alert_id,
                    alert.threat_type.value,
                    alert.severity.value,
                    alert.title,
                    alert.description,
                    alert.source.value,
                    json.dumps(alert.indicators),
                    json.dumps(alert.matched_patterns),
                    json.dumps(alert.affected_repositories),
                    alert.created_at.isoformat(),
                    alert.expires_at.isoformat() if alert.expires_at else None,
                    int(alert.actionable),
                    json.dumps(alert.metadata),
                    0
                ))
            
        except Exception as e:
            logger.error(f"Failed to store threat alert: {e}")
    
    async def _alert_monitor(self):
        """Background task to monitor and manage alerts"""
        while True:
            try:
                current_time = datetime.now(timezone.utc)
                
                # Remove expired alerts
                expired_alerts = []
                for alert_id, alert in self.active_alerts.items():
                    if alert.expires_at and current_time > alert.expires_at:
                        expired_alerts.append(alert_id)
                
                for alert_id in expired_alerts:
                    del self.active_alerts[alert_id]
                    logger.info(f"Expired alert removed: {alert_id}")
                
                # Wait before next check
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in alert monitor: {e}")
                await asyncio.sleep(60)
    
    async def get_cve_data(self, cve_id: str) -> Optional[CVEData]:
        """Get CVE data by ID"""
        try:
            with sqlite3.connect(self.cve_db_path) as conn:
                cursor = conn.execute("""
                SELECT cve_id, description, severity, cvss_score, cvss_vector,
                       published_date, modified_date, affected_products, reference_urls,
                       cwe_ids, epss_score, kev_listed, exploit_available,
                       vendor_advisories FROM cves WHERE cve_id = ?
                """, (cve_id,))
                
                row = cursor.fetchone()
                if row:
                    return CVEData(
                        cve_id=row[0],
                        description=row[1],
                        severity=ThreatSeverity(row[2]),
                        cvss_score=row[3],
                        cvss_vector=row[4],
                        published_date=datetime.fromisoformat(row[5]),
                        modified_date=datetime.fromisoformat(row[6]),
                        affected_products=json.loads(row[7]),
                        reference_urls=json.loads(row[8]),
                        cwe_ids=json.loads(row[9]),
                        epss_score=row[10],
                        kev_listed=bool(row[11]),
                        exploit_available=bool(row[12]),
                        vendor_advisories=json.loads(row[13])
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get CVE data: {e}")
            return None
    
    async def search_cves(
        self,
        query: Optional[str] = None,
        severity: Optional[ThreatSeverity] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        kev_only: bool = False,
        limit: int = 100
    ) -> List[CVEData]:
        """Search CVEs with filters"""
        try:
            conditions = []
            params = []
            
            if query:
                conditions.append("(cve_id LIKE ? OR description LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%"])
            
            if severity:
                conditions.append("severity = ?")
                params.append(severity.value)
            
            if min_score is not None:
                conditions.append("cvss_score >= ?")
                params.append(min_score)
            
            if max_score is not None:
                conditions.append("cvss_score <= ?")
                params.append(max_score)
            
            if kev_only:
                conditions.append("kev_listed = 1")
            
            where_clause = ""
            if conditions:
                where_clause = f"WHERE {' AND '.join(conditions)}"
            
            query_sql = f"""
            SELECT cve_id, description, severity, cvss_score, cvss_vector,
                   published_date, modified_date, affected_products, references,
                   cwe_ids, epss_score, kev_listed, exploit_available,
                   vendor_advisories FROM cves 
            {where_clause}
            ORDER BY cvss_score DESC, published_date DESC
            LIMIT ?
            """
            params.append(limit)
            
            cves = []
            with sqlite3.connect(self.cve_db_path) as conn:
                cursor = conn.execute(query_sql, params)
                
                for row in cursor.fetchall():
                    cve_data = CVEData(
                        cve_id=row[0],
                        description=row[1],
                        severity=ThreatSeverity(row[2]),
                        cvss_score=row[3],
                        cvss_vector=row[4],
                        published_date=datetime.fromisoformat(row[5]),
                        modified_date=datetime.fromisoformat(row[6]),
                        affected_products=json.loads(row[7]),
                        reference_urls=json.loads(row[8]),
                        cwe_ids=json.loads(row[9]),
                        epss_score=row[10],
                        kev_listed=bool(row[11]),
                        exploit_available=bool(row[12]),
                        vendor_advisories=json.loads(row[13])
                    )
                    cves.append(cve_data)
            
            return cves
            
        except Exception as e:
            logger.error(f"Failed to search CVEs: {e}")
            return []
    
    async def get_active_alerts(
        self,
        threat_type: Optional[ThreatType] = None,
        severity: Optional[ThreatSeverity] = None,
        limit: int = 100
    ) -> List[ThreatAlert]:
        """Get active threat alerts"""
        try:
            conditions = ["resolved = 0"]
            params = []
            
            if threat_type:
                conditions.append("threat_type = ?")
                params.append(threat_type.value)
            
            if severity:
                conditions.append("severity = ?")
                params.append(severity.value)
            
            where_clause = f"WHERE {' AND '.join(conditions)}"
            
            query_sql = f"""
            SELECT alert_id, threat_type, severity, title, description, source,
                   indicators, matched_patterns, affected_repositories,
                   created_at, expires_at, actionable, metadata FROM threat_alerts
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ?
            """
            params.append(limit)
            
            alerts = []
            with sqlite3.connect(self.threat_db_path) as conn:
                cursor = conn.execute(query_sql, params)
                
                for row in cursor.fetchall():
                    alert = ThreatAlert(
                        alert_id=row[0],
                        threat_type=ThreatType(row[1]),
                        severity=ThreatSeverity(row[2]),
                        title=row[3],
                        description=row[4],
                        source=ThreatSource(row[5]),
                        indicators=json.loads(row[6]),
                        matched_patterns=json.loads(row[7]),
                        affected_repositories=json.loads(row[8]),
                        created_at=datetime.fromisoformat(row[9]),
                        expires_at=datetime.fromisoformat(row[10]) if row[10] else None,
                        actionable=bool(row[11]),
                        metadata=json.loads(row[12])
                    )
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Mark alert as resolved"""
        try:
            with sqlite3.connect(self.threat_db_path) as conn:
                conn.execute("""
                UPDATE threat_alerts SET resolved = 1 WHERE alert_id = ?
                """, (alert_id,))
            
            # Remove from active alerts
            if alert_id in self.active_alerts:
                del self.active_alerts[alert_id]
            
            logger.info(f"Alert resolved: {alert_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}")
            return False
    
    async def scan_codebase_for_threats(
        self,
        repository_path: str,
        file_patterns: List[str] = None
    ) -> List[ThreatAlert]:
        """Scan codebase for threat indicators"""
        if file_patterns is None:
            file_patterns = ["*.py", "*.js", "*.java", "*.c", "*.cpp", "*.md", "*.txt"]
        
        alerts = []
        repo_path = Path(repository_path)
        
        if not repo_path.exists():
            logger.error(f"Repository path does not exist: {repository_path}")
            return alerts
        
        try:
            for indicator in self.zero_day_indicators:
                for pattern in file_patterns:
                    for file_path in repo_path.rglob(pattern):
                        if file_path.is_file():
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                
                                # Check for pattern matches
                                matches = re.finditer(indicator.pattern, content, re.IGNORECASE)
                                for match in matches:
                                    # Create alert for match
                                    alert = ThreatAlert(
                                        alert_id=f"scan_{indicator.indicator_id}_{hashlib.md5(str(file_path).encode()).hexdigest()[:8]}",
                                        threat_type=ThreatType.ZERO_DAY,
                                        severity=ThreatSeverity.HIGH,
                                        title=f"Threat Pattern Detected: {indicator.description}",
                                        description=f"Pattern '{indicator.pattern}' found in {file_path}",
                                        source=ThreatSource.CUSTOM,
                                        indicators=[str(file_path), match.group()],
                                        matched_patterns=[indicator.pattern],
                                        affected_repositories=[repository_path],
                                        metadata={
                                            "file_path": str(file_path),
                                            "line_number": content[:match.start()].count('\n') + 1,
                                            "match_text": match.group(),
                                            "indicator_id": indicator.indicator_id,
                                            "confidence": indicator.confidence
                                        }
                                    )
                                    alerts.append(alert)
                                    
                            except Exception as e:
                                logger.warning(f"Failed to scan file {file_path}: {e}")
                                continue
            
            logger.info(f"Codebase scan completed: {len(alerts)} threat indicators found")
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to scan codebase: {e}")
            return alerts
    
    async def get_zero_day_indicators(self) -> List[ZeroDayIndicator]:
        """Get all zero-day indicators"""
        try:
            # Ensure we have default indicators if none exist
            await self._ensure_default_zero_day_indicators()
            
            # Convert internal format to ZeroDayIndicator objects for API
            indicators = []
            for indicator in self.zero_day_indicators:
                zd_indicator = ZeroDayIndicator(
                    id=indicator.indicator_id,
                    pattern=indicator.pattern,
                    threat_type="zero_day",
                    description=indicator.description,
                    severity=ThreatSeverity.HIGH,  # Default severity
                    confidence=indicator.confidence,
                    first_seen=datetime.now(timezone.utc),
                    last_seen=datetime.now(timezone.utc),
                    source="internal",
                    tags=indicator.keywords
                )
                indicators.append(zd_indicator)
            
            return indicators
            
        except Exception as e:
            logger.error(f"Failed to get zero-day indicators: {e}")
            return []
    
    async def add_zero_day_indicator(self, indicator: ZeroDayIndicator):
        """Add a zero-day indicator"""
        try:
            # Convert to internal format
            internal_indicator = type('ZeroDayIndicatorInternal', (), {
                'indicator_id': indicator.id,
                'pattern': indicator.pattern,
                'description': indicator.description,
                'confidence': indicator.confidence,
                'keywords': indicator.tags,
                'file_patterns': ["*"],
                'techniques': ["manual"]
            })()
            
            await self._store_zero_day_indicator(internal_indicator)
            self.zero_day_indicators.append(internal_indicator)
            
            logger.info(f"Added zero-day indicator: {indicator.id}")
            
        except Exception as e:
            logger.error(f"Failed to add zero-day indicator: {e}")
    
    async def create_alert(self, alert: ThreatAlert):
        """Create a threat alert"""
        try:
            await self._store_threat_alert(alert)
            self.active_alerts[alert.id] = alert
            
            logger.info(f"Created threat alert: {alert.id}")
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
    
    async def get_active_alerts(self) -> List[ThreatAlert]:
        """Get all active threat alerts"""
        try:
            return list(self.active_alerts.values())
            
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []
    
    async def store_cve_data(self, cve_list: List[CVEData]):
        """Store CVE data"""
        try:
            for cve in cve_list:
                await self._store_cve_data(cve)
            
            logger.info(f"Stored {len(cve_list)} CVE records")
            
        except Exception as e:
            logger.error(f"Failed to store CVE data: {e}")
    
    async def _store_cve_data(self, cve: CVEData):
        """Store individual CVE data record"""
        try:
            with sqlite3.connect(self.cve_db_path) as conn:
                cursor = conn.execute("""
                INSERT OR REPLACE INTO cves (
                    cve_id, description, severity, cvss_score, cvss_vector,
                    published_date, modified_date, affected_products, reference_urls,
                    cwe_ids, epss_score, kev_listed, exploit_available,
                    vendor_advisories, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cve.cve_id,
                    cve.description,
                    cve.severity.value,
                    cve.cvss_score,
                    cve.cvss_vector,
                    cve.published_date.isoformat(),
                    cve.modified_date.isoformat(),
                    json.dumps(cve.affected_products),
                    json.dumps(cve.reference_urls),
                    json.dumps(cve.cwe_ids),
                    cve.epss_score,
                    cve.kev_listed,
                    cve.exploit_available,
                    json.dumps(cve.vendor_advisories),
                    datetime.now(timezone.utc).isoformat(),
                    datetime.now(timezone.utc).isoformat()
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store CVE {cve.cve_id}: {e}")
            raise
    
    async def get_cve_details(self, cve_id: str) -> Optional[CVEData]:
        """Get CVE details by ID"""
        try:
            with sqlite3.connect(self.cve_db_path) as conn:
                cursor = conn.execute("""
                SELECT cve_id, description, cvss_score, severity, published_date, 
                       modified_date, cwe_ids, affected_products, references, 
                       exploits_available, epss_score, in_kev, source
                FROM cve_data WHERE cve_id = ?
                """, (cve_id,))
                
                row = cursor.fetchone()
                if row:
                    return CVEData(
                        cve_id=row[0],
                        description=row[1],
                        cvss_score=row[2],
                        severity=ThreatSeverity(row[3]),
                        published_date=datetime.fromisoformat(row[4]) if row[4] else None,
                        modified_date=datetime.fromisoformat(row[5]) if row[5] else None,
                        cwe_ids=json.loads(row[6]) if row[6] else [],
                        affected_products=json.loads(row[7]) if row[7] else [],
                        reference_urls=json.loads(row[8]) if row[8] else [],
                        exploits_available=bool(row[9]),
                        epss_score=row[10],
                        in_kev=bool(row[11])
                    )
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get CVE details: {e}")
            return None
    
    async def scan_repository(self, repository_path: str, patterns_only: bool = False) -> List:
        """Scan repository for threat indicators"""
        try:
            # This is a simplified version that returns threat matches
            matches = []
            
            # Ensure we have indicators
            await self._ensure_default_zero_day_indicators()
            
            # Simple file patterns to scan
            file_patterns = ["*.py", "*.js", "*.yaml", "*.yml", "*.json", "*.txt"]
            
            import glob
            import re
            
            for pattern in file_patterns:
                file_paths = glob.glob(f"{repository_path}/**/{pattern}", recursive=True)
                
                for file_path in file_paths[:10]:  # Limit for testing
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            # Check for common security patterns
                            security_patterns = [
                                (r'password\s*=\s*["\']([^"\']+)["\']', 'hardcoded_password', ThreatSeverity.HIGH),
                                (r'api[_-]?key\s*=\s*["\']([^"\']+)["\']', 'hardcoded_api_key', ThreatSeverity.HIGH),
                                (r'secret\s*=\s*["\']([^"\']+)["\']', 'hardcoded_secret', ThreatSeverity.HIGH),
                                (r'os\.system\s*\(', 'command_injection', ThreatSeverity.MEDIUM),
                                (r'eval\s*\(', 'code_injection', ThreatSeverity.HIGH),
                                (r'runAsRoot:\s*true', 'privilege_escalation', ThreatSeverity.MEDIUM)
                            ]
                            
                            for regex, threat_type, severity in security_patterns:
                                for match in re.finditer(regex, content, re.IGNORECASE):
                                    line_num = content[:match.start()].count('\n') + 1
                                    
                                    threat_match = type('ThreatMatch', (), {
                                        'indicator_id': f"pattern_{threat_type}",
                                        'file_path': file_path,
                                        'line_number': line_num,
                                        'matched_content': match.group(0)[:100],
                                        'confidence': 0.8,
                                        'severity': severity,
                                        'threat_type': threat_type
                                    })()
                                    
                                    matches.append(threat_match)
                    
                    except Exception as e:
                        logger.warning(f"Failed to scan file {file_path}: {e}")
                        continue
            
            logger.info(f"Repository scan completed: {len(matches)} threats found")
            return matches
            
        except Exception as e:
            logger.error(f"Failed to scan repository: {e}")
            return []
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status including database stats and feed status"""
        try:
            status = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "databases": {},
                "feeds": {},
                "alerts": {},
                "indicators": {}
            }
            
            # CVE database stats
            with sqlite3.connect(self.cve_db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM cves")
                status["databases"]["cve_count"] = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM cve_data")
                status["databases"]["cve_data_count"] = cursor.fetchone()[0]
            
            # Threat alerts stats
            with sqlite3.connect(self.threat_db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM threat_alerts WHERE active = 1")
                status["alerts"]["active_count"] = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM zero_day_indicators")
                status["indicators"]["zero_day_count"] = cursor.fetchone()[0]
            
            # Feed status
            status["feeds"]["last_nvd_update"] = getattr(self, "_last_nvd_update", None)
            status["feeds"]["last_osv_update"] = getattr(self, "_last_osv_update", None)
            status["feeds"]["last_kev_update"] = getattr(self, "_last_kev_update", None)
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
                "databases": {},
                "feeds": {},
                "alerts": {},
                "indicators": {}
            }

__all__ = [
    'ThreatIntelligenceEngine', 'CVEData', 'ThreatAlert', 'ZeroDayIndicator',
    'ThreatSeverity', 'ThreatType', 'ThreatSource', 'ThreatFeed'
]
