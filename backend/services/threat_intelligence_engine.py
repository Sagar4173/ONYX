"""
Threat Intelligence Engine
==========================

Enterprise-grade threat intelligence integration with NVD, OSV, and KEV feeds.
Provides vulnerability enrichment, EPSS scoring, and exploit intelligence.

Author: SecureDevOpsAI Platform
Date: August 2025
"""

import asyncio
import aiohttp
import json
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import zipfile
import gzip
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CVEMetadata:
    """CVE metadata from threat intelligence sources"""
    cve_id: str
    description: str
    cvss_v3_score: float
    cvss_v3_vector: str
    severity: str
    published_date: str
    last_modified: str
    cpes: List[str]  # Affected products/packages
    references: List[str]
    exploitability_score: float  # EPSS score
    exploit_available: bool
    in_kev: bool  # CISA Known Exploited Vulnerabilities
    threat_level: str  # critical, high, medium, low
    mitigation_priority: int  # 1-5 scale

@dataclass
class VulnerabilityFinding:
    """Enhanced vulnerability finding with threat intelligence"""
    finding_id: str
    cve_id: Optional[str]
    component: str
    version: str
    severity: str
    epss_score: float
    kev_status: bool
    exploit_available: bool
    business_criticality: str
    asset_context: Dict[str, Any]
    risk_score: float
    lifecycle_state: str
    assignee: Optional[str]
    due_date: Optional[str]
    sla_breach: bool

class ThreatIntelligenceEngine:
    """Core threat intelligence engine for vulnerability enrichment"""
    
    def __init__(self, db_path: str = "threat_intelligence.db"):
        self.db_path = db_path
        self.session = None
        self.feeds = {
            'nvd': 'https://nvd.nist.gov/feeds/json/cve/1.1/',
            'osv': 'https://osv.dev/list',
            'kev': 'https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json',
            'epss': 'https://epss.cyentia.com/epss_scores-current.csv.gz'
        }
        self.init_database()
    
    def init_database(self):
        """Initialize threat intelligence database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # CVE metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cve_metadata (
                cve_id TEXT PRIMARY KEY,
                description TEXT,
                cvss_v3_score REAL,
                cvss_v3_vector TEXT,
                severity TEXT,
                published_date TEXT,
                last_modified TEXT,
                exploitability_score REAL,
                exploit_available BOOLEAN,
                in_kev BOOLEAN,
                threat_level TEXT,
                mitigation_priority INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # CPE (Common Platform Enumeration) mappings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cpe_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cve_id TEXT,
                cpe_string TEXT,
                vendor TEXT,
                product TEXT,
                version TEXT,
                FOREIGN KEY (cve_id) REFERENCES cve_metadata (cve_id)
            )
        ''')
        
        # EPSS scores table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS epss_scores (
                cve_id TEXT PRIMARY KEY,
                epss_score REAL,
                percentile REAL,
                last_updated DATE
            )
        ''')
        
        # KEV (Known Exploited Vulnerabilities) table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kev_catalog (
                cve_id TEXT PRIMARY KEY,
                vendor_project TEXT,
                product TEXT,
                vulnerability_name TEXT,
                date_added TEXT,
                short_description TEXT,
                required_action TEXT,
                due_date TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("🗄️ Threat intelligence database initialized")
    
    async def start_session(self):
        """Start HTTP session for API calls"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def ingest_nvd_feed(self, year: int = None) -> int:
        """Ingest NVD CVE feed for specified year"""
        await self.start_session()
        
        if year is None:
            year = datetime.now().year
        
        feed_url = f"{self.feeds['nvd']}nvdcve-1.1-{year}.json.zip"
        logger.info(f"📡 Ingesting NVD feed for {year}...")
        
        try:
            async with self.session.get(feed_url) as response:
                if response.status == 200:
                    content = await response.read()
                    return await self._process_nvd_data(content)
                else:
                    logger.error(f"❌ Failed to fetch NVD feed: {response.status}")
                    return 0
        except Exception as e:
            logger.error(f"❌ Error ingesting NVD feed: {str(e)}")
            return 0
    
    async def _process_nvd_data(self, zip_content: bytes) -> int:
        """Process NVD JSON data from zip file"""
        import tempfile
        import os
        
        processed_count = 0
        
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "nvd_feed.zip")
            
            # Write zip content to file
            with open(zip_path, 'wb') as f:
                f.write(zip_content)
            
            # Extract and process JSON
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                for filename in zip_file.namelist():
                    if filename.endswith('.json'):
                        with zip_file.open(filename) as json_file:
                            data = json.load(json_file)
                            processed_count += await self._store_nvd_cves(data)
        
        logger.info(f"✅ Processed {processed_count} CVEs from NVD feed")
        return processed_count
    
    async def _store_nvd_cves(self, nvd_data: Dict) -> int:
        """Store NVD CVEs in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        processed = 0
        
        for cve_item in nvd_data.get('CVE_Items', []):
            cve = cve_item.get('cve', {})
            impact = cve_item.get('impact', {})
            
            cve_id = cve.get('CVE_data_meta', {}).get('ID', '')
            
            if not cve_id:
                continue
            
            # Extract description
            descriptions = cve.get('description', {}).get('description_data', [])
            description = descriptions[0].get('value', '') if descriptions else ''
            
            # Extract CVSS v3 data
            cvss_v3 = impact.get('baseMetricV3', {}).get('cvssV3', {})
            cvss_score = cvss_v3.get('baseScore', 0.0)
            cvss_vector = cvss_v3.get('vectorString', '')
            severity = cvss_v3.get('baseSeverity', 'UNKNOWN').lower()
            
            # Extract dates
            published = cve_item.get('publishedDate', '')
            modified = cve_item.get('lastModifiedDate', '')
            
            # Store CVE metadata
            cursor.execute('''
                INSERT OR REPLACE INTO cve_metadata 
                (cve_id, description, cvss_v3_score, cvss_v3_vector, severity, 
                 published_date, last_modified, exploitability_score, exploit_available, 
                 in_kev, threat_level, mitigation_priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0.0, FALSE, FALSE, ?, 3)
            ''', (cve_id, description, cvss_score, cvss_vector, severity, 
                  published, modified, severity))
            
            # Extract and store CPE data
            configurations = cve_item.get('configurations', {}).get('nodes', [])
            for node in configurations:
                for cpe_match in node.get('cpe_match', []):
                    cpe_string = cpe_match.get('cpe23Uri', '')
                    if cpe_string:
                        # Parse CPE string (cpe:2.3:a:vendor:product:version:...)
                        parts = cpe_string.split(':')
                        if len(parts) >= 6:
                            vendor = parts[3]
                            product = parts[4]
                            version = parts[5]
                            
                            cursor.execute('''
                                INSERT OR IGNORE INTO cpe_mappings 
                                (cve_id, cpe_string, vendor, product, version)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (cve_id, cpe_string, vendor, product, version))
            
            processed += 1
        
        conn.commit()
        conn.close()
        return processed
    
    async def ingest_kev_catalog(self) -> int:
        """Ingest CISA Known Exploited Vulnerabilities catalog"""
        await self.start_session()
        
        logger.info("📡 Ingesting CISA KEV catalog...")
        
        try:
            async with self.session.get(self.feeds['kev']) as response:
                if response.status == 200:
                    data = await response.json()
                    return await self._store_kev_data(data)
                else:
                    logger.error(f"❌ Failed to fetch KEV catalog: {response.status}")
                    return 0
        except Exception as e:
            logger.error(f"❌ Error ingesting KEV catalog: {str(e)}")
            return 0
    
    async def _store_kev_data(self, kev_data: Dict) -> int:
        """Store KEV catalog data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        processed = 0
        
        for vuln in kev_data.get('vulnerabilities', []):
            cve_id = vuln.get('cveID', '')
            
            cursor.execute('''
                INSERT OR REPLACE INTO kev_catalog 
                (cve_id, vendor_project, product, vulnerability_name, 
                 date_added, short_description, required_action, due_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                cve_id,
                vuln.get('vendorProject', ''),
                vuln.get('product', ''),
                vuln.get('vulnerabilityName', ''),
                vuln.get('dateAdded', ''),
                vuln.get('shortDescription', ''),
                vuln.get('requiredAction', ''),
                vuln.get('dueDate', '')
            ))
            
            # Update CVE metadata to mark as KEV
            cursor.execute('''
                UPDATE cve_metadata 
                SET in_kev = TRUE, threat_level = 'critical', mitigation_priority = 1
                WHERE cve_id = ?
            ''', (cve_id,))
            
            processed += 1
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Processed {processed} KEV entries")
        return processed
    
    async def ingest_epss_scores(self) -> int:
        """Ingest EPSS (Exploit Prediction Scoring System) scores"""
        await self.start_session()
        
        logger.info("📡 Ingesting EPSS scores...")
        
        try:
            async with self.session.get(self.feeds['epss']) as response:
                if response.status == 200:
                    content = await response.read()
                    return await self._process_epss_data(content)
                else:
                    logger.error(f"❌ Failed to fetch EPSS scores: {response.status}")
                    return 0
        except Exception as e:
            logger.error(f"❌ Error ingesting EPSS scores: {str(e)}")
            return 0
    
    async def _process_epss_data(self, gzip_content: bytes) -> int:
        """Process EPSS CSV data"""
        import csv
        import io
        
        # Decompress gzip content
        decompressed = gzip.decompress(gzip_content)
        csv_content = decompressed.decode('utf-8')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        processed = 0
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        for row in csv_reader:
            cve_id = row.get('cve', '')
            epss_score = float(row.get('epss', 0.0))
            percentile = float(row.get('percentile', 0.0))
            
            if cve_id:
                cursor.execute('''
                    INSERT OR REPLACE INTO epss_scores 
                    (cve_id, epss_score, percentile, last_updated)
                    VALUES (?, ?, ?, date('now'))
                ''', (cve_id, epss_score, percentile))
                
                # Update CVE metadata with EPSS score
                cursor.execute('''
                    UPDATE cve_metadata 
                    SET exploitability_score = ?
                    WHERE cve_id = ?
                ''', (epss_score, cve_id))
                
                processed += 1
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Processed {processed} EPSS scores")
        return processed
    
    async def enrich_finding(self, component: str, version: str, 
                           finding_data: Dict) -> VulnerabilityFinding:
        """Enrich a vulnerability finding with threat intelligence"""
        
        # Look up CVE information
        cve_data = await self._lookup_cve_by_component(component, version)
        
        if not cve_data:
            # Create basic finding without CVE
            return VulnerabilityFinding(
                finding_id=finding_data.get('id', ''),
                cve_id=None,
                component=component,
                version=version,
                severity=finding_data.get('severity', 'unknown'),
                epss_score=0.0,
                kev_status=False,
                exploit_available=False,
                business_criticality='medium',
                asset_context=finding_data.get('asset_context', {}),
                risk_score=self._calculate_base_risk_score(finding_data.get('severity', 'unknown')),
                lifecycle_state='open',
                assignee=None,
                due_date=None,
                sla_breach=False
            )
        
        # Calculate enriched risk score
        risk_score = await self._calculate_risk_score(cve_data, finding_data)
        
        # Determine SLA based on risk score
        due_date, sla_breach = self._calculate_sla(risk_score, cve_data.get('in_kev', False))
        
        return VulnerabilityFinding(
            finding_id=finding_data.get('id', ''),
            cve_id=cve_data.get('cve_id'),
            component=component,
            version=version,
            severity=cve_data.get('severity', 'unknown'),
            epss_score=cve_data.get('exploitability_score', 0.0),
            kev_status=cve_data.get('in_kev', False),
            exploit_available=cve_data.get('exploit_available', False),
            business_criticality=finding_data.get('business_criticality', 'medium'),
            asset_context=finding_data.get('asset_context', {}),
            risk_score=risk_score,
            lifecycle_state='open',
            assignee=None,
            due_date=due_date,
            sla_breach=sla_breach
        )
    
    async def _lookup_cve_by_component(self, component: str, version: str) -> Optional[Dict]:
        """Look up CVE data by component and version"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Search for matching CPE entries
        cursor.execute('''
            SELECT c.*, e.epss_score, e.percentile, k.cve_id as kev_id
            FROM cve_metadata c
            LEFT JOIN cpe_mappings cpe ON c.cve_id = cpe.cve_id
            LEFT JOIN epss_scores e ON c.cve_id = e.cve_id
            LEFT JOIN kev_catalog k ON c.cve_id = k.cve_id
            WHERE (cpe.product LIKE ? OR cpe.vendor LIKE ?)
            AND (cpe.version = ? OR cpe.version = '*')
            ORDER BY c.cvss_v3_score DESC
            LIMIT 1
        ''', (f'%{component}%', f'%{component}%', version))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
        
        return None
    
    async def _calculate_risk_score(self, cve_data: Dict, finding_data: Dict) -> float:
        """Calculate comprehensive risk score"""
        base_score = cve_data.get('cvss_v3_score', 0.0)
        epss_score = cve_data.get('exploitability_score', 0.0)
        
        # Base risk from CVSS
        risk_score = base_score
        
        # EPSS multiplier (higher exploitability = higher risk)
        if epss_score > 0.7:
            risk_score *= 1.5
        elif epss_score > 0.3:
            risk_score *= 1.2
        
        # KEV multiplier (known exploited = critical priority)
        if cve_data.get('in_kev', False):
            risk_score *= 2.0
        
        # Business criticality multiplier
        criticality = finding_data.get('business_criticality', 'medium')
        criticality_multipliers = {
            'critical': 2.0,
            'high': 1.5,
            'medium': 1.0,
            'low': 0.7
        }
        risk_score *= criticality_multipliers.get(criticality, 1.0)
        
        # Cap at 10.0
        return min(risk_score, 10.0)
    
    def _calculate_base_risk_score(self, severity: str) -> float:
        """Calculate base risk score from severity"""
        severity_scores = {
            'critical': 9.0,
            'high': 7.0,
            'medium': 5.0,
            'low': 3.0,
            'info': 1.0
        }
        return severity_scores.get(severity.lower(), 5.0)
    
    def _calculate_sla(self, risk_score: float, is_kev: bool) -> Tuple[str, bool]:
        """Calculate SLA due date and breach status"""
        now = datetime.now()
        
        # SLA days based on risk score
        if is_kev or risk_score >= 9.0:
            sla_days = 1  # Critical - 24 hours
        elif risk_score >= 7.0:
            sla_days = 7  # High - 1 week
        elif risk_score >= 5.0:
            sla_days = 30  # Medium - 1 month
        else:
            sla_days = 90  # Low - 3 months
        
        due_date = (now + timedelta(days=sla_days)).isoformat()
        sla_breach = False  # New finding, not breached yet
        
        return due_date, sla_breach
    
    async def update_threat_intelligence(self) -> Dict[str, int]:
        """Update all threat intelligence feeds"""
        logger.info("🔄 Updating threat intelligence feeds...")
        
        results = {
            'nvd_cves': 0,
            'kev_entries': 0,
            'epss_scores': 0
        }
        
        try:
            # Update current year NVD feed
            results['nvd_cves'] = await self.ingest_nvd_feed()
            
            # Update KEV catalog
            results['kev_entries'] = await self.ingest_kev_catalog()
            
            # Update EPSS scores
            results['epss_scores'] = await self.ingest_epss_scores()
            
            logger.info(f"✅ Threat intelligence update complete: {results}")
            
        except Exception as e:
            logger.error(f"❌ Error updating threat intelligence: {str(e)}")
        
        finally:
            await self.close_session()
        
        return results
    
    async def get_threat_stats(self) -> Dict[str, Any]:
        """Get threat intelligence statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # CVE counts by severity
        cursor.execute('''
            SELECT severity, COUNT(*) 
            FROM cve_metadata 
            GROUP BY severity
        ''')
        stats['cve_by_severity'] = dict(cursor.fetchall())
        
        # KEV count
        cursor.execute('SELECT COUNT(*) FROM kev_catalog')
        stats['kev_count'] = cursor.fetchone()[0]
        
        # High EPSS scores (>0.7)
        cursor.execute('SELECT COUNT(*) FROM epss_scores WHERE epss_score > 0.7')
        stats['high_epss_count'] = cursor.fetchone()[0]
        
        # Recent CVEs (last 30 days)
        cursor.execute('''
            SELECT COUNT(*) FROM cve_metadata 
            WHERE date(published_date) > date('now', '-30 days')
        ''')
        stats['recent_cves'] = cursor.fetchone()[0]
        
        conn.close()
        return stats

# Export main class
__all__ = ['ThreatIntelligenceEngine', 'CVEMetadata', 'VulnerabilityFinding']
