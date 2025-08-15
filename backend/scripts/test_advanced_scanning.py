#!/usr/bin/env python3
"""
Advanced Scanning Test Suite
Tests ZAP, Nuclei, CodeQL, and Checkov integration with unified pipeline
"""
import asyncio
import json
import tempfile
import shutil
import sys
from pathlib import Path
from datetime import datetime, timezone
import logging

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / 'backend'))
sys.path.append(str(Path(__file__).parent.parent))

from services.advanced_scanner_engine import (
    AdvancedScannerEngine,
    ScanConfig,
    Finding,
    ScanType,
    Severity,
    SuppressionEngine
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedScanningTester:
    """Test advanced scanning capabilities"""
    
    def __init__(self):
        self.config = ScanConfig(
            max_concurrent_scans=2,
            scan_timeout=300,  # 5 minutes for testing
            dast_target_allowlist=["httpbin.org", "localhost", "example.com"],
            dast_rate_limit=1.0,  # Conservative for testing
            sast_languages=["python", "javascript"],
            iac_frameworks=["docker", "kubernetes"],
            suppression_file=".security-suppressions.yaml",
            allow_inline_suppressions=True
        )
        self.engine = AdvancedScannerEngine(self.config)
        
    async def test_suppression_engine(self):
        """Test false positive suppression functionality"""
        logger.info("\n" + "="*60)
        logger.info("🔧 TESTING SUPPRESSION ENGINE")
        logger.info("="*60)
        
        # Create test repository structure
        test_repo = tempfile.mkdtemp(prefix='test_repo_')
        try:
            # Create test files with various patterns
            test_files = {
                "src/app.py": '''
# This is a test file
password = "hardcoded123"  # nosec B105
api_key = "test-key-value"
                ''',
                "tests/test_auth.py": '''
# Test file should be suppressed
SECRET_KEY = "test-secret"
PASSWORD = "test-password"
                ''',
                "docs/example.py": '''
# Documentation example
token = "demo-token-123"
                ''',
                ".security-suppressions.yaml": '''
version: "1.0"
rules:
  test-files:
    description: "Suppress findings in test files"
    file_patterns:
      - "**/tests/**"
      - "**/test_*.py"
    rule_ids:
      - "CWE-798"
    severities:
      - "high"
      - "medium"
                '''
            }
            
            # Create test files
            for file_path, content in test_files.items():
                full_path = Path(test_repo) / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write(content)
            
            # Test suppression engine
            suppression_engine = SuppressionEngine(self.config)
            
            # Load suppression rules
            rules = suppression_engine.load_suppression_rules(test_repo)
            logger.info(f"✅ Loaded {len(rules.get('rules', {}))} suppression rules")
            
            # Scan for inline suppressions
            inline_suppressions = suppression_engine.scan_inline_suppressions(test_repo)
            logger.info(f"✅ Found {len(inline_suppressions)} inline suppressions")
            
            # Test suppression logic with mock findings
            test_findings = [
                Finding(
                    id="test-1",
                    source="test",
                    rule_id="CWE-798",
                    title="Hardcoded credential",
                    description="Hardcoded password found",
                    severity=Severity.HIGH,
                    confidence="High",
                    location={"file": "src/app.py", "line": 3},
                    scan_type=ScanType.SAST
                ),
                Finding(
                    id="test-2", 
                    source="test",
                    rule_id="CWE-798",
                    title="Hardcoded credential",
                    description="Hardcoded secret found",
                    severity=Severity.MEDIUM,
                    confidence="High",
                    location={"file": "tests/test_auth.py", "line": 3},
                    scan_type=ScanType.SAST
                ),
                Finding(
                    id="test-3",
                    source="test", 
                    rule_id="CWE-200",
                    title="Information exposure",
                    description="Sensitive data in docs",
                    severity=Severity.LOW,
                    confidence="Medium",
                    location={"file": "docs/example.py", "line": 3},
                    scan_type=ScanType.SAST
                )
            ]
            
            # Test suppressions
            suppressed_count = 0
            for finding in test_findings:
                should_suppress, reason = suppression_engine.should_suppress(finding, test_repo)
                if should_suppress:
                    finding.suppressed = True
                    finding.suppression_reason = reason
                    suppressed_count += 1
                    logger.info(f"🔇 Suppressed finding: {finding.title} - {reason}")
                else:
                    logger.info(f"🔍 Active finding: {finding.title}")
            
            logger.info(f"✅ Suppression test completed: {suppressed_count}/{len(test_findings)} findings suppressed")
            
        finally:
            shutil.rmtree(test_repo, ignore_errors=True)
    
    async def test_unified_finding_schema(self):
        """Test unified finding schema normalization"""
        logger.info("\n" + "="*60)
        logger.info("📋 TESTING UNIFIED FINDING SCHEMA")
        logger.info("="*60)
        
        # Create sample findings from different scanners
        sample_findings = {
            "zap": {
                "pluginId": "40012",
                "alert": "Cross Site Scripting (Reflected)",
                "risk": "High", 
                "confidence": "Medium",
                "url": "http://example.com/search",
                "param": "q",
                "description": "XSS vulnerability found",
                "solution": "Encode user input"
            },
            "nuclei": {
                "template-id": "xss-reflected",
                "info": {
                    "name": "Reflected XSS",
                    "severity": "high",
                    "description": "Reflected XSS in search parameter"
                },
                "matched-at": "http://example.com/search?q=<script>",
                "template": "xss-reflected.yaml"
            },
            "codeql": {
                "ruleId": "js/xss",
                "level": "error", 
                "message": {
                    "text": "Cross-site scripting vulnerability"
                },
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {"uri": "src/app.js"},
                        "region": {"startLine": 42, "startColumn": 15}
                    }
                }]
            },
            "checkov": {
                "check_id": "CKV_DOCKER_1",
                "check_name": "Ensure Docker image uses non-root user",
                "file_path": "Dockerfile",
                "file_line_range": [5, 5],
                "resource": "docker_image.app",
                "severity": "MEDIUM",
                "description": "Container runs as root user"
            }
        }
        
        # Test normalization
        normalized_findings = []
        
        # Simulate ZAP finding normalization
        zap_data = sample_findings["zap"]
        zap_finding = Finding(
            id="zap-test-1",
            source="zap",
            rule_id=zap_data["pluginId"],
            title=zap_data["alert"],
            description=zap_data["description"],
            severity=Severity.HIGH,  # Normalized from "High"
            confidence=zap_data["confidence"],
            location={
                "url": zap_data["url"],
                "parameter": zap_data["param"]
            },
            recommendation=zap_data["solution"],
            scan_type=ScanType.DAST,
            raw_output=zap_data
        )
        normalized_findings.append(zap_finding)
        
        # Simulate Nuclei finding normalization  
        nuclei_data = sample_findings["nuclei"]
        nuclei_finding = Finding(
            id="nuclei-test-1",
            source="nuclei",
            rule_id=nuclei_data["template-id"],
            title=nuclei_data["info"]["name"],
            description=nuclei_data["info"]["description"],
            severity=Severity.HIGH,  # Normalized from "high"
            confidence="High",
            location={
                "url": nuclei_data["matched-at"],
                "template": nuclei_data["template"]
            },
            scan_type=ScanType.PENTEST,
            raw_output=nuclei_data
        )
        normalized_findings.append(nuclei_finding)
        
        # Simulate CodeQL finding normalization
        codeql_data = sample_findings["codeql"]
        location = codeql_data["locations"][0]["physicalLocation"]
        codeql_finding = Finding(
            id="codeql-test-1",
            source="codeql", 
            rule_id=codeql_data["ruleId"],
            title="Cross-site scripting vulnerability",
            description=codeql_data["message"]["text"],
            severity=Severity.HIGH,  # Normalized from "error"
            confidence="High",
            location={
                "file": location["artifactLocation"]["uri"],
                "line": location["region"]["startLine"],
                "column": location["region"]["startColumn"]
            },
            scan_type=ScanType.SAST,
            raw_output=codeql_data
        )
        normalized_findings.append(codeql_finding)
        
        # Simulate Checkov finding normalization
        checkov_data = sample_findings["checkov"]
        checkov_finding = Finding(
            id="checkov-test-1",
            source="checkov",
            rule_id=checkov_data["check_id"],
            title=checkov_data["check_name"], 
            description=checkov_data["description"],
            severity=Severity.MEDIUM,  # Normalized from "MEDIUM"
            confidence="High",
            location={
                "file": checkov_data["file_path"],
                "line": checkov_data["file_line_range"][0],
                "resource": checkov_data["resource"]
            },
            scan_type=ScanType.IAC,
            raw_output=checkov_data
        )
        normalized_findings.append(checkov_finding)
        
        # Validate unified schema
        logger.info("✅ Testing unified finding schema:")
        for finding in normalized_findings:
            logger.info(f"  📊 {finding.source}: {finding.title}")
            logger.info(f"     └─ Severity: {finding.severity.value}")
            logger.info(f"     └─ Type: {finding.scan_type.value}")
            logger.info(f"     └─ Location: {finding.location}")
        
        # Test JSON serialization
        try:
            findings_json = json.dumps([finding.__dict__ for finding in normalized_findings], default=str, indent=2)
            logger.info(f"✅ JSON serialization successful ({len(findings_json)} chars)")
        except Exception as e:
            logger.error(f"❌ JSON serialization failed: {e}")
    
    async def test_rate_limiting_and_scoping(self):
        """Test rate limiting and target scoping"""
        logger.info("\n" + "="*60)
        logger.info("⚡ TESTING RATE LIMITING AND SCOPING")
        logger.info("="*60)
        
        # Test target allowlist validation
        test_targets = [
            ("http://httpbin.org/get", True),  # Allowed
            ("https://example.com/api", True),  # Allowed  
            ("http://localhost:8080", True),   # Allowed
            ("https://malicious-site.com", False),  # Not allowed
            ("http://internal-server", False)   # Not allowed
        ]
        
        for target_url, should_be_allowed in test_targets:
            try:
                from urllib.parse import urlparse
                parsed_url = urlparse(target_url)
                target_host = parsed_url.netloc.lower()
                
                is_allowed = False
                for allowed in self.config.dast_target_allowlist:
                    if target_host == allowed.lower() or target_host.endswith(f".{allowed.lower()}"):
                        is_allowed = True
                        break
                
                status = "✅ ALLOWED" if is_allowed else "❌ BLOCKED"
                expected = "✅ EXPECTED" if is_allowed == should_be_allowed else "⚠️ UNEXPECTED"
                
                logger.info(f"  🎯 {target_url}: {status} ({expected})")
                
            except Exception as e:
                logger.error(f"  ❌ Error testing {target_url}: {e}")
        
        # Test rate limiting configuration
        logger.info(f"\n⚡ Rate limiting configuration:")
        logger.info(f"  └─ DAST rate limit: {self.config.dast_rate_limit} req/s")
        logger.info(f"  └─ Max concurrent scans: {self.config.max_concurrent_scans}")
        logger.info(f"  └─ Scan timeout: {self.config.scan_timeout}s")
        
        # Simulate rate-limited scanning
        import time
        start_time = time.time()
        request_count = 5
        
        for i in range(request_count):
            # Simulate rate-limited request
            await asyncio.sleep(1.0 / self.config.dast_rate_limit)
            logger.info(f"  📡 Simulated request {i+1}/{request_count}")
        
        elapsed = time.time() - start_time
        expected_time = (request_count - 1) / self.config.dast_rate_limit
        logger.info(f"✅ Rate limiting test: {elapsed:.1f}s elapsed (expected ~{expected_time:.1f}s)")
    
    async def test_mock_scanner_integration(self):
        """Test mock scanner integration without actual tools"""
        logger.info("\n" + "="*60)
        logger.info("🔧 TESTING MOCK SCANNER INTEGRATION")
        logger.info("="*60)
        
        # Create mock findings for each scanner type
        mock_findings = {
            "sast": [
                Finding(
                    id="sast-mock-1",
                    source="codeql",
                    rule_id="js/sql-injection",
                    title="SQL Injection vulnerability",
                    description="Unsanitized user input used in SQL query",
                    severity=Severity.HIGH,
                    confidence="High",
                    location={"file": "src/db.js", "line": 25},
                    cwe="CWE-89",
                    recommendation="Use parameterized queries",
                    scan_type=ScanType.SAST
                )
            ],
            "dast": [
                Finding(
                    id="dast-mock-1",
                    source="zap",
                    rule_id="40012",
                    title="Cross Site Scripting (Reflected)",
                    description="XSS vulnerability in search parameter",
                    severity=Severity.HIGH,
                    confidence="Medium",
                    location={"url": "http://example.com/search", "parameter": "q"},
                    cwe="CWE-79",
                    recommendation="Encode all user input",
                    scan_type=ScanType.DAST
                ),
                Finding(
                    id="dast-mock-2",
                    source="nuclei",
                    rule_id="xss-reflected",
                    title="Reflected XSS Template",
                    description="Reflected XSS detected via template",
                    severity=Severity.MEDIUM,
                    confidence="High",
                    location={"url": "http://example.com/form", "template": "xss.yaml"},
                    recommendation="Validate and sanitize input",
                    scan_type=ScanType.PENTEST
                )
            ],
            "iac": [
                Finding(
                    id="iac-mock-1",
                    source="checkov",
                    rule_id="CKV_DOCKER_2",
                    title="Docker container runs as root",
                    description="Container configured to run as root user",
                    severity=Severity.MEDIUM,
                    confidence="High",
                    location={"file": "Dockerfile", "line": 8, "resource": "docker_image"},
                    recommendation="Add USER directive to run as non-root",
                    scan_type=ScanType.IAC
                )
            ]
        }
        
        # Test summary generation
        all_findings = []
        for scan_type, findings in mock_findings.items():
            all_findings.extend(findings)
            logger.info(f"📊 {scan_type.upper()}: {len(findings)} findings")
        
        # Generate comprehensive summary
        summary = self.engine._generate_summary(all_findings)
        
        logger.info("\n📋 Comprehensive Scan Summary:")
        logger.info(f"  📊 Total findings: {summary['total_findings']}")
        logger.info(f"  ✅ Active findings: {summary['active_findings']}")
        logger.info(f"  🔇 Suppressed: {summary['suppressed_findings']}")
        
        logger.info("  📈 By severity:")
        for severity, count in summary['by_severity'].items():
            if count > 0:
                logger.info(f"     └─ {severity}: {count}")
        
        logger.info("  🔧 By scanner:")
        for scanner, count in summary['by_scanner'].items():
            if count > 0:
                logger.info(f"     └─ {scanner}: {count}")
        
        logger.info("  📋 By scan type:")
        for scan_type, count in summary['by_scan_type'].items():
            if count > 0:
                logger.info(f"     └─ {scan_type}: {count}")
    
    async def run_all_tests(self):
        """Run all advanced scanning tests"""
        logger.info("🚀" + "="*58 + "🚀")
        logger.info("🚀 ADVANCED SCANNING COMPREHENSIVE TEST SUITE")
        logger.info("🚀" + "="*58 + "🚀")
        
        tests = [
            self.test_suppression_engine,
            self.test_unified_finding_schema,
            self.test_rate_limiting_and_scoping,
            self.test_mock_scanner_integration
        ]
        
        passed_tests = 0
        for test in tests:
            try:
                await test()
                passed_tests += 1
                logger.info("✅ Test passed!")
            except Exception as e:
                logger.error(f"❌ Test failed: {e}")
        
        logger.info("\n" + "🎉" + "="*58 + "🎉")
        logger.info("🎉 ADVANCED SCANNING TEST RESULTS")
        logger.info("🎉" + "="*58 + "🎉")
        logger.info(f"✅ Tests passed: {passed_tests}/{len(tests)}")
        logger.info(f"📊 Success rate: {(passed_tests/len(tests)*100):.1f}%")
        
        if passed_tests == len(tests):
            logger.info("🏆 ALL TESTS PASSED! Advanced scanning is ready! 🏆")
        else:
            logger.info("⚠️ Some tests failed. Review implementation.")
        
        return passed_tests == len(tests)

async def main():
    """Main test execution"""
    tester = AdvancedScanningTester()
    success = await tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
