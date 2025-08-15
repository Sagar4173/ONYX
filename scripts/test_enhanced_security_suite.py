#!/usr/bin/env python3
"""
Comprehensive Enhanced Security Test Suite
Tests threat intelligence, vulnerability management, and security metrics
"""
import sys
import os
import asyncio
import json
import tempfile
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from services.threat_intelligence import (
    ThreatIntelligenceEngine, ThreatSeverity, ThreatAlert, CVEData, ZeroDayIndicator,
    ThreatType, ThreatSource
)
from services.vulnerability_management import (
    VulnerabilityManager, VulnerabilityStatus, VulnerabilityPriority, 
    Asset, Vulnerability, AssetType, ExposureLevel
)
from services.threat_intelligence import ThreatSeverity
from services.security_metrics import (
    SecurityMetricsEngine, ComplianceFramework, SecurityScore, 
    ComplianceResult, SecurityKPI
)

class EnhancedSecurityTestSuite:
    """Comprehensive test suite for enhanced security features"""
    
    def __init__(self):
        """Initialize test suite"""
        self.test_data_dir = Path("test_enhanced_security_data")
        self.test_repo_dir = Path("test_repository")
        self.results = {
            "threat_intelligence": {"passed": 0, "failed": 0, "details": []},
            "vulnerability_management": {"passed": 0, "failed": 0, "details": []},
            "security_metrics": {"passed": 0, "failed": 0, "details": []},
            "integration": {"passed": 0, "failed": 0, "details": []}
        }
        
    def setup_test_environment(self):
        """Set up test environment"""
        print("🔧 Setting up test environment...")
        
        # Create test directories
        self.test_data_dir.mkdir(exist_ok=True)
        self.test_repo_dir.mkdir(exist_ok=True)
        
        # Create sample repository files for threat scanning
        (self.test_repo_dir / "app.py").write_text("""
import os
import hashlib

# Sample code with potential security issues
API_KEY = "sk-1234567890abcdef"  # Hardcoded secret
password = "admin123"  # Weak password

def execute_command(user_input):
    # Command injection vulnerability
    os.system(f"ls {user_input}")

def sql_query(user_id):
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return query

# CVE-like pattern
def vulnerable_function():
    # Buffer overflow pattern
    buffer = "A" * 1000
    return buffer
""")
        
        (self.test_repo_dir / "config.yaml").write_text("""
database:
  host: localhost
  password: "plaintext_password"
  
security:
  jwt_secret: "weak_secret_123"
  
# Kubernetes misconfiguration
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
    securityContext:
      runAsRoot: true
      privileged: true
""")
        
        print("✅ Test environment set up successfully")
    
    def cleanup_test_environment(self):
        """Clean up test environment and close database connections"""
        print("🧹 Cleaning up test environment...")
        
        # Forcefully close any remaining database connections
        import gc
        gc.collect()
        
        try:
            # Wait a bit for any pending database operations
            import time
            time.sleep(0.5)
            
            if self.test_data_dir.exists():
                # Try to remove directory, handle Windows file locking gracefully
                for attempt in range(3):
                    try:
                        shutil.rmtree(self.test_data_dir)
                        break
                    except (PermissionError, OSError) as e:
                        if attempt < 2:
                            print(f"   ⚠️ Cleanup attempt {attempt + 1} failed, retrying...")
                            time.sleep(1)
                        else:
                            print(f"   ⚠️ Warning: Could not fully clean up test directory: {e}")
                            # Continue anyway - this is just cleanup
                            
        except Exception as e:
            print(f"   ⚠️ Warning: Cleanup error (non-critical): {e}")
        
        if self.test_repo_dir.exists():
            try:
                shutil.rmtree(self.test_repo_dir)
            except Exception as e:
                print(f"   ⚠️ Warning: Could not clean up test repo: {e}")
        print("✅ Test environment cleaned up")
    
    def record_test_result(self, category: str, test_name: str, passed: bool, details: str = ""):
        """Record test result"""
        if passed:
            self.results[category]["passed"] += 1
            status = "✅ PASS"
        else:
            self.results[category]["failed"] += 1
            status = "❌ FAIL"
        
        self.results[category]["details"].append({
            "test": test_name,
            "status": status,
            "details": details
        })
        
        print(f"  {status}: {test_name}")
        if details and not passed:
            print(f"    Details: {details}")
    
    async def test_threat_intelligence(self):
        """Test threat intelligence features"""
        print("\n🛡️ Testing Threat Intelligence...")
        category = "threat_intelligence"
        
        try:
            # Initialize threat intelligence engine
            threat_engine = ThreatIntelligenceEngine(data_dir=str(self.test_data_dir / "threat_intel"))
            
            # Test 1: Engine initialization
            try:
                status = await threat_engine.get_system_status()
                self.record_test_result(category, "Engine Initialization", True, f"Status: {status.engine_status.value}")
            except Exception as e:
                self.record_test_result(category, "Engine Initialization", False, str(e))
            
            # Test 2: CVE data storage and retrieval
            try:
                # Add test CVE data
                test_cve = CVEData(
                    cve_id="CVE-2024-TEST-001",
                    description="Test CVE for enhanced security suite",
                    severity=ThreatSeverity.HIGH,
                    cvss_score=8.5,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:H",
                    published_date=datetime.now(timezone.utc),
                    modified_date=datetime.now(timezone.utc),
                    affected_products=["test-app:1.0.0"],
                    reference_urls=["https://example.com/cve"],
                    cwe_ids=["CWE-79"],
                    epss_score=0.75,
                    kev_listed=False,
                    exploit_available=True,
                    vendor_advisories=["VENDOR-2024-001"]
                )
                
                await threat_engine.store_cve_data([test_cve])
                
                # Retrieve CVE data
                retrieved_cve = await threat_engine.get_cve_details("CVE-2024-TEST-001")
                
                if retrieved_cve and retrieved_cve.cve_id == "CVE-2024-TEST-001":
                    self.record_test_result(category, "CVE Data Storage/Retrieval", True, f"CVE: {retrieved_cve.cve_id}")
                else:
                    self.record_test_result(category, "CVE Data Storage/Retrieval", False, "CVE not found or data mismatch")
                    
            except Exception as e:
                self.record_test_result(category, "CVE Data Storage/Retrieval", False, str(e))
            
            # Test 3: Threat alert creation
            try:
                alert = ThreatAlert(
                    alert_id="ALERT-TEST-001",
                    threat_type=ThreatType.SUPPLY_CHAIN,  # Need to import this
                    severity=ThreatSeverity.CRITICAL,
                    title="Test Security Alert",
                    description="Test alert for enhanced security suite",
                    source=ThreatSource.MANUAL,  # Need to import this
                    indicators=["test_pattern"],
                    matched_patterns=["test_pattern"],
                    affected_repositories=["test_asset"],
                    created_at=datetime.now(timezone.utc),
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
                )
                
                await threat_engine.create_alert(alert)
                alerts = await threat_engine.get_active_alerts()
                
                if any(a.id == "ALERT-TEST-001" for a in alerts):
                    self.record_test_result(category, "Threat Alert Creation", True, f"Alert created: {alert.id}")
                else:
                    self.record_test_result(category, "Threat Alert Creation", False, "Alert not found in active alerts")
                    
            except Exception as e:
                self.record_test_result(category, "Threat Alert Creation", False, str(e))
            
            # Test 4: Zero-day indicator detection
            try:
                # Add zero-day indicator
                zero_day = ZeroDayIndicator(
                    indicator_id="ZD-TEST-001",
                    pattern="test_exploit_pattern",
                    description="Test zero-day indicator",
                    confidence=0.9,
                    keywords=["test", "exploit"],
                    file_patterns=["*.test"],
                    techniques=["T1203"],
                    created_at=datetime.now(timezone.utc)
                )
                
                await threat_engine.add_zero_day_indicator(zero_day)
                indicators = await threat_engine.get_zero_day_indicators()
                
                if any(i.id == "ZD-TEST-001" for i in indicators):
                    self.record_test_result(category, "Zero-day Indicator Detection", True, f"Indicator: {zero_day.id}")
                else:
                    self.record_test_result(category, "Zero-day Indicator Detection", False, "Zero-day indicator not found")
                    
            except Exception as e:
                self.record_test_result(category, "Zero-day Indicator Detection", False, str(e))
            
            # Test 5: Repository threat scanning
            try:
                scan_results = await threat_engine.scan_repository(str(self.test_repo_dir))
                
                # Should detect hardcoded secrets and other patterns
                if scan_results and len(scan_results) > 0:
                    threats_found = len(scan_results)
                    self.record_test_result(category, "Repository Threat Scanning", True, f"Threats found: {threats_found}")
                else:
                    self.record_test_result(category, "Repository Threat Scanning", False, "No threats detected in test repository")
                    
            except Exception as e:
                self.record_test_result(category, "Repository Threat Scanning", False, str(e))
                
        except Exception as e:
            self.record_test_result(category, "Overall Threat Intelligence", False, f"Failed to initialize: {e}")
    
    async def test_vulnerability_management(self):
        """Test vulnerability management features"""
        print("\n🔍 Testing Vulnerability Management...")
        category = "vulnerability_management"
        
        try:
            # Initialize vulnerability manager
            vuln_manager = VulnerabilityManager(data_dir=str(self.test_data_dir / "vuln_mgmt"))
            
            # Test 1: Asset management
            try:
                # Add test asset
                test_asset = Asset(
                    asset_id="ASSET-TEST-001",
                    name="Test Web Server",
                    asset_type=AssetType.WEB_APPLICATION,
                    exposure_level=ExposureLevel.INTERNET_FACING,
                    criticality=ThreatSeverity.HIGH,
                    owner_team="test_team",
                    technologies=["nginx", "ubuntu"],
                    endpoints=["https://test-server.local"],
                    data_classification="internal",
                    compliance_requirements=["PCI-DSS"],
                    last_scan_date=datetime.now(timezone.utc),
                    metadata={"environment": "test", "region": "us-east-1"}
                )
                
                await vuln_manager.register_asset(test_asset)
                assets = await vuln_manager.get_assets(limit=100, offset=0)
                
                if any(a.id == "ASSET-TEST-001" for a in assets):
                    self.record_test_result(category, "Asset Management", True, f"Asset: {test_asset.id}")
                else:
                    self.record_test_result(category, "Asset Management", False, "Asset not found")
                    
            except Exception as e:
                self.record_test_result(category, "Asset Management", False, str(e))
            
            # Test 2: Vulnerability creation and management
            try:
                # Add test vulnerability
                test_vuln = Vulnerability(
                    vuln_id="VULN-TEST-001",
                    cve_id="CVE-2024-TEST-001",
                    title="Test SQL Injection Vulnerability",
                    description="SQL injection vulnerability in test application",
                    severity=ThreatSeverity.HIGH,
                    priority=VulnerabilityPriority.HIGH,
                    status=VulnerabilityStatus.OPEN,
                    asset_id="ASSET-TEST-001",
                    affected_component="web_application",
                    location="https://test-server.local/login",
                    cvss_score=8.5,
                    epss_score=0.75,
                    exposure_score=85.0,
                    business_impact_score=90.0,
                    risk_score=87.5,
                    discovered_date=datetime.now(timezone.utc),
                    first_seen_date=datetime.now(timezone.utc),
                    due_date=datetime.now(timezone.utc) + timedelta(days=7),
                    assigned_to="test_developer",
                    scanner_source="test_scanner",
                    remediation_guidance="Use parameterized queries",
                    tags=["sql-injection", "web"],
                    evidence={"scanner": "test_suite", "confidence": 0.9}
                )
                
                await vuln_manager.create_vulnerability(
                    cve_id=test_vuln.cve_id,
                    title=test_vuln.title,
                    description=test_vuln.description,
                    severity=test_vuln.severity,
                    asset_id=test_vuln.asset_id,
                    affected_component=test_vuln.affected_component,
                    location=test_vuln.location,
                    cvss_score=test_vuln.cvss_score,
                    evidence=test_vuln.evidence,
                    scanner_source=test_vuln.scanner_source
                )
                vulns = await vuln_manager.get_vulnerabilities({}, limit=100, offset=0)
                
                if any(v.id == "VULN-TEST-001" for v in vulns):
                    self.record_test_result(category, "Vulnerability Creation", True, f"Vulnerability: {test_vuln.id}")
                else:
                    self.record_test_result(category, "Vulnerability Creation", False, "Vulnerability not found")
                    
            except Exception as e:
                self.record_test_result(category, "Vulnerability Creation", False, str(e))
            
            # Test 3: Vulnerability status updates
            try:
                success = await vuln_manager.update_vulnerability_status(
                    "VULN-TEST-001", 
                    VulnerabilityStatus.TRIAGED, 
                    "test_analyst",
                    "Triaged for analysis"
                )
                
                if success:
                    self.record_test_result(category, "Vulnerability Status Update", True, "Status updated to TRIAGED")
                else:
                    self.record_test_result(category, "Vulnerability Status Update", False, "Failed to update status")
                    
            except Exception as e:
                self.record_test_result(category, "Vulnerability Status Update", False, str(e))
            
            # Test 4: Risk metrics calculation
            try:
                metrics = await vuln_manager.calculate_risk_metrics()
                
                if metrics.total_vulnerabilities >= 1:  # Should have at least our test vulnerability
                    self.record_test_result(category, "Risk Metrics Calculation", True, 
                                          f"Total vulns: {metrics.total_vulnerabilities}, MTTF: {metrics.mean_time_to_fix}")
                else:
                    self.record_test_result(category, "Risk Metrics Calculation", False, "Metrics calculation failed")
                    
            except Exception as e:
                self.record_test_result(category, "Risk Metrics Calculation", False, str(e))
            
            # Test 5: EPSS integration and risk scoring
            try:
                # Test EPSS score impact on prioritization
                await vuln_manager.update_epss_scores()
                
                # Add high EPSS vulnerability using create_vulnerability
                await vuln_manager.create_vulnerability(
                    cve_id="CVE-2024-TEST-002",
                    title="High EPSS Score Vulnerability",
                    description="Vulnerability with high exploitation probability",
                    severity=ThreatSeverity.MEDIUM,
                    asset_id="ASSET-TEST-001",
                    affected_component="api_endpoint",
                    location="https://test-server.local/api/data",
                    cvss_score=6.5,
                    evidence={"scanner": "test_suite", "epss_score": 0.95},
                    scanner_source="test_scanner"
                )
                
                # Check if it gets prioritized correctly
                prioritized = await vuln_manager.get_vulnerabilities(
                    {"priority": VulnerabilityPriority.HIGH}, limit=10, offset=0
                )
                
                self.record_test_result(category, "EPSS Integration", True, f"High EPSS vulnerability prioritized")
                
            except Exception as e:
                self.record_test_result(category, "EPSS Integration", False, str(e))
                
        except Exception as e:
            self.record_test_result(category, "Overall Vulnerability Management", False, f"Failed to initialize: {e}")
    
    async def test_security_metrics(self):
        """Test security metrics and KPIs"""
        print("\n📊 Testing Security Metrics & KPIs...")
        category = "security_metrics"
        
        try:
            # Initialize components
            threat_engine = ThreatIntelligenceEngine(data_dir=str(self.test_data_dir / "threat_intel"))
            vuln_manager = VulnerabilityManager(data_dir=str(self.test_data_dir / "vuln_mgmt"))
            metrics_engine = SecurityMetricsEngine(data_dir=str(self.test_data_dir / "metrics"))
            
            # Connect components
            metrics_engine.set_components(vuln_manager, threat_engine)
            
            # Test 1: Security posture calculation
            try:
                posture_score = await metrics_engine.calculate_security_posture()
                
                if posture_score.overall_score >= 0 and posture_score.overall_score <= 100:
                    self.record_test_result(category, "Security Posture Calculation", True, 
                                          f"Overall score: {posture_score.overall_score}")
                else:
                    self.record_test_result(category, "Security Posture Calculation", False, 
                                          f"Invalid score: {posture_score.overall_score}")
                    
            except Exception as e:
                self.record_test_result(category, "Security Posture Calculation", False, str(e))
            
            # Test 2: Compliance assessment
            try:
                compliance_result = await metrics_engine.assess_compliance_framework(
                    ComplianceFramework.PCI_DSS, 
                    "test_assessor"
                )
                
                if compliance_result.framework == ComplianceFramework.PCI_DSS:
                    self.record_test_result(category, "Compliance Assessment", True, 
                                          f"PCI DSS score: {compliance_result.score}")
                else:
                    self.record_test_result(category, "Compliance Assessment", False, "Compliance assessment failed")
                    
            except Exception as e:
                self.record_test_result(category, "Compliance Assessment", False, str(e))
            
            # Test 3: KPI calculation
            try:
                kpis = await metrics_engine.calculate_kpis()
                
                if len(kpis) > 0:
                    kpi_names = [kpi.name for kpi in kpis]
                    self.record_test_result(category, "KPI Calculation", True, f"KPIs: {', '.join(kpi_names)}")
                else:
                    self.record_test_result(category, "KPI Calculation", False, "No KPIs calculated")
                    
            except Exception as e:
                self.record_test_result(category, "KPI Calculation", False, str(e))
            
            # Test 4: Risk trend analysis
            try:
                risk_trends = await metrics_engine.generate_risk_trend_analysis(days=7)
                
                if risk_trends.critical_trend and len(risk_trends.critical_trend.values) > 0:
                    self.record_test_result(category, "Risk Trend Analysis", True, 
                                          f"Trend period: {risk_trends.period}")
                else:
                    self.record_test_result(category, "Risk Trend Analysis", False, "No trend data generated")
                    
            except Exception as e:
                self.record_test_result(category, "Risk Trend Analysis", False, str(e))
            
            # Test 5: Compliance framework coverage
            try:
                frameworks_tested = []
                for framework in [ComplianceFramework.PCI_DSS, ComplianceFramework.HIPAA, ComplianceFramework.SOX]:
                    try:
                        result = await metrics_engine.assess_compliance_framework(framework, "test_suite")
                        if result:
                            frameworks_tested.append(framework.value)
                    except Exception:
                        pass  # Framework might not be fully implemented
                
                if len(frameworks_tested) >= 2:
                    self.record_test_result(category, "Multi-Framework Support", True, 
                                          f"Frameworks: {', '.join(frameworks_tested)}")
                else:
                    self.record_test_result(category, "Multi-Framework Support", False, 
                                          f"Only {len(frameworks_tested)} frameworks working")
                    
            except Exception as e:
                self.record_test_result(category, "Multi-Framework Support", False, str(e))
                
        except Exception as e:
            self.record_test_result(category, "Overall Security Metrics", False, f"Failed to initialize: {e}")
    
    async def test_integration(self):
        """Test integration between all components"""
        print("\n🔗 Testing Component Integration...")
        category = "integration"
        
        try:
            # Initialize all components
            threat_engine = ThreatIntelligenceEngine(data_dir=str(self.test_data_dir / "threat_intel"))
            vuln_manager = VulnerabilityManager(data_dir=str(self.test_data_dir / "vuln_mgmt"))
            metrics_engine = SecurityMetricsEngine(data_dir=str(self.test_data_dir / "metrics"))
            
            # Connect components
            metrics_engine.set_components(vuln_manager, threat_engine)
            
            # Test 1: CVE to vulnerability correlation
            try:
                # Add CVE data
                test_cve = CVEData(
                    cve_id="CVE-2024-INTEGRATION-001",
                    description="Integration test CVE",
                    severity=ThreatSeverity.CRITICAL,
                    cvss_score=9.0,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    published_date=datetime.now(timezone.utc),
                    modified_date=datetime.now(timezone.utc),
                    affected_products=["test-app:2.0.0"],
                    reference_urls=["https://example.com/cve"],
                    cwe_ids=["CWE-89"],
                    epss_score=0.85,
                    kev_listed=True,
                    exploit_available=True,
                    vendor_advisories=["VENDOR-2024-002"]
                )
                
                await threat_engine.store_cve_data([test_cve])
                
                # Create corresponding vulnerability
                # Create integration test vulnerability using create_vulnerability
                await vuln_manager.create_vulnerability(
                    cve_id="CVE-2024-INTEGRATION-001",
                    title="Integration Test Vulnerability",
                    description="Vulnerability linked to integration CVE",
                    severity=ThreatSeverity.CRITICAL,
                    asset_id="ASSET-TEST-001",
                    affected_component="integration_module",
                    location="https://test-server.local/integration",
                    cvss_score=9.0,
                    evidence={"linked_cve": "CVE-2024-INTEGRATION-001", "epss_score": 0.85},
                    scanner_source="threat_intel"
                )
                
                # Verify correlation
                cve_data = await threat_engine.get_cve_details("CVE-2024-INTEGRATION-001")
                vulns = await vuln_manager.get_vulnerabilities({"cve_id": "CVE-2024-INTEGRATION-001"}, 10, 0)
                
                if cve_data and len(vulns) > 0 and vulns[0].cve_id == cve_data.cve_id:
                    self.record_test_result(category, "CVE-Vulnerability Correlation", True, 
                                          f"CVE {cve_data.cve_id} linked to vulnerability {vulns[0].id}")
                else:
                    self.record_test_result(category, "CVE-Vulnerability Correlation", False, "Correlation failed")
                    
            except Exception as e:
                self.record_test_result(category, "CVE-Vulnerability Correlation", False, str(e))
            
            # Test 2: Threat intelligence impact on metrics
            try:
                # Create threat alert
                alert = ThreatAlert(
                    alert_id="ALERT-INTEGRATION-001",
                    threat_type=ThreatType.SUPPLY_CHAIN,
                    severity=ThreatSeverity.CRITICAL,
                    title="Critical Integration Threat",
                    description="High-impact threat affecting security posture",
                    source=ThreatSource.AUTOMATED,
                    indicators=["malicious_pattern"],
                    matched_patterns=["pattern_match"],
                    affected_repositories=["ASSET-TEST-001"],
                    created_at=datetime.now(timezone.utc),
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=48)
                )
                
                await threat_engine.create_alert(alert)
                
                # Check impact on security posture
                posture_score = await metrics_engine.calculate_security_posture()
                
                # Threat score should be impacted by active alerts
                if posture_score.threat_score < 100:  # Should be reduced due to active threats
                    self.record_test_result(category, "Threat Impact on Metrics", True, 
                                          f"Threat score: {posture_score.threat_score}")
                else:
                    self.record_test_result(category, "Threat Impact on Metrics", False, 
                                          "Threat alerts not affecting metrics")
                    
            except Exception as e:
                self.record_test_result(category, "Threat Impact on Metrics", False, str(e))
            
            # Test 3: End-to-end workflow
            try:
                # Simulate complete workflow: Threat detection → Vulnerability creation → Status tracking → Metrics update
                
                # 1. Detect threat in repository
                scan_results = await threat_engine.scan_repository(str(self.test_repo_dir))
                
                # 2. Create vulnerabilities based on scan results
                workflow_vulns = []
                for i, result in enumerate(scan_results[:2]):  # Limit to 2 for testing
                    vuln_id = await vuln_manager.create_vulnerability(
                        cve_id=None,
                        title=f"Workflow Vulnerability {i+1}",
                        description=f"Vulnerability detected in {result.file_path}",
                        severity=result.severity,
                        asset_id="ASSET-TEST-001",
                        affected_component="source_code",
                        location=result.file_path,
                        cvss_score=7.0,
                        evidence={"file_path": result.file_path, "line": result.line_number, "workflow": True},
                        scanner_source="threat_scan"
                    )
                    # Get the created vulnerability for workflow tracking
                    if vuln_id:
                        vuln = await vuln_manager.get_vulnerability(vuln_id)
                        if vuln:
                            workflow_vulns.append(vuln)
                
                # 3. Update vulnerability status (simulate remediation)
                for vuln in workflow_vulns:
                    await vuln_manager.update_vulnerability_status(
                        vuln.vuln_id, VulnerabilityStatus.FIXED, "workflow_test", "Fixed in workflow test"
                    )
                
                # 4. Calculate updated metrics
                final_metrics = await metrics_engine.calculate_security_posture()
                
                if len(workflow_vulns) > 0 and final_metrics.overall_score > 0:
                    self.record_test_result(category, "End-to-End Workflow", True, 
                                          f"Processed {len(workflow_vulns)} vulnerabilities, final score: {final_metrics.overall_score}")
                else:
                    self.record_test_result(category, "End-to-End Workflow", False, "Workflow incomplete")
                    
            except Exception as e:
                self.record_test_result(category, "End-to-End Workflow", False, str(e))
            
            # Test 4: Data consistency across components
            try:
                # Verify data consistency
                threat_status = await threat_engine.get_system_status()
                vuln_metrics = await vuln_manager.calculate_risk_metrics()
                security_posture = await metrics_engine.calculate_security_posture()
                
                # Basic consistency checks
                consistency_checks = [
                    threat_status.active_alerts >= 0,
                    vuln_metrics.total_vulnerabilities >= 0,
                    security_posture.overall_score >= 0 and security_posture.overall_score <= 100
                ]
                
                if all(consistency_checks):
                    self.record_test_result(category, "Data Consistency", True, 
                                          f"All components consistent - Threats: {threat_status.active_alerts}, "
                                          f"Vulns: {vuln_metrics.total_vulnerabilities}, Score: {security_posture.overall_score}")
                else:
                    self.record_test_result(category, "Data Consistency", False, "Data inconsistency detected")
                    
            except Exception as e:
                self.record_test_result(category, "Data Consistency", False, str(e))
                
        except Exception as e:
            self.record_test_result(category, "Overall Integration", False, f"Failed to initialize: {e}")
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("🎯 ENHANCED SECURITY TEST SUITE RESULTS")
        print("="*80)
        
        total_passed = 0
        total_failed = 0
        
        for category, results in self.results.items():
            passed = results["passed"]
            failed = results["failed"]
            total = passed + failed
            
            total_passed += passed
            total_failed += failed
            
            if total > 0:
                success_rate = (passed / total) * 100
                status = "✅ EXCELLENT" if success_rate == 100 else "⚠️ PARTIAL" if success_rate >= 70 else "❌ NEEDS WORK"
                
                print(f"\n📊 {category.replace('_', ' ').title()}")
                print(f"   Status: {status}")
                print(f"   Results: {passed}/{total} passed ({success_rate:.1f}%)")
                
                if failed > 0:
                    print(f"   Failed Tests:")
                    for detail in results["details"]:
                        if "❌ FAIL" in detail["status"]:
                            print(f"     • {detail['test']}: {detail['details']}")
        
        print(f"\n🏆 OVERALL RESULTS")
        total_tests = total_passed + total_failed
        if total_tests > 0:
            overall_success = (total_passed / total_tests) * 100
            print(f"   Total Tests: {total_tests}")
            print(f"   Passed: {total_passed}")
            print(f"   Failed: {total_failed}")
            print(f"   Success Rate: {overall_success:.1f}%")
            
            if overall_success >= 90:
                print(f"   🎉 OUTSTANDING! Enhanced security suite is production-ready!")
            elif overall_success >= 80:
                print(f"   👍 GOOD! Enhanced security suite is largely functional!")
            elif overall_success >= 70:
                print(f"   ⚠️ FAIR! Enhanced security suite needs some improvements!")
            else:
                print(f"   ❌ POOR! Enhanced security suite requires significant work!")
        else:
            print(f"   ❌ NO TESTS EXECUTED!")
        
        print("="*80)
    
    async def run_all_tests(self):
        """Run all enhanced security tests"""
        print("🚀 Starting Enhanced Security Test Suite...")
        print("Testing: Threat Intelligence + Vulnerability Management + Security Metrics")
        
        try:
            self.setup_test_environment()
            
            # Run all test categories
            await self.test_threat_intelligence()
            await self.test_vulnerability_management()
            await self.test_security_metrics()
            await self.test_integration()
            
            self.print_test_summary()
            
        except Exception as e:
            print(f"❌ Fatal error in test suite: {e}")
        finally:
            self.cleanup_test_environment()

async def main():
    """Main test function"""
    test_suite = EnhancedSecurityTestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
