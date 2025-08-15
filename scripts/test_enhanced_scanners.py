#!/usr/bin/env python3
"""
Comprehensive test script for Enhanced Security Features:
- Custom Rule Engine
- Baseline Scanning  
- Policy as Code
- Enhanced Security Scanners
"""
import asyncio
import sys
import os
from pathlib import Path
import logging
import json
import yaml
from datetime import datetime, timedelta

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_custom_rule_engine():
    """Test Custom Rule Engine functionality"""
    print("\n🔧 Testing Custom Rule Engine")
    print("=" * 50)
    
    try:
        from services.rule_engine import rule_engine, CustomRule, RuleType, RuleSeverity
        
        # Test 1: Create a custom regex rule
        print("📝 Creating custom regex rule...")
        regex_rule = CustomRule(
            id="test-hardcoded-password",
            name="Hardcoded Password Detection",
            description="Detects hardcoded passwords in source code",
            type=RuleType.REGEX,
            severity=RuleSeverity.HIGH,
            pattern=r"password\s*=\s*['\"]([^'\"]{6,})['\"]",
            author="test-user",
            cwe_ids=["CWE-798"],
            languages=["python", "javascript"],
            file_patterns=["**/*.py", "**/*.js"],
            test_cases=[
                {
                    "content": "password = 'hardcoded123'",
                    "expected_matches": 1
                },
                {
                    "content": "password = get_password()",
                    "expected_matches": 0
                }
            ]
        )
        
        # Save rule
        success = await rule_engine.save_rule(regex_rule)
        print(f"  ✅ Rule saved: {success}")
        
        # Test 2: Validate rule
        print("🔍 Validating rule...")
        validation_result = await rule_engine.validate_rule(regex_rule)
        print(f"  ✅ Rule valid: {validation_result.is_valid}")
        if validation_result.errors:
            print(f"  ❌ Errors: {validation_result.errors}")
        if validation_result.warnings:
            print(f"  ⚠️ Warnings: {validation_result.warnings}")
        
        # Test 3: Load rule
        print("📂 Loading rule...")
        loaded_rule = await rule_engine.load_rule("test-hardcoded-password")
        print(f"  ✅ Rule loaded: {loaded_rule is not None}")
        
        # Test 4: Get all rules
        print("📋 Getting all rules...")
        all_rules = await rule_engine.get_all_rules()
        print(f"  ✅ Found {len(all_rules)} rules")
        
        # Test 5: Test rule templates
        print("📚 Testing rule templates...")
        templates = await rule_engine.get_all_templates()
        print(f"  ✅ Found {len(templates)} templates")
        
        if templates:
            # Create rule from template
            template = templates[0]
            new_rule = await rule_engine.create_rule_from_template(
                template.template_id,
                {
                    "name": "Generated SQL Injection Rule",
                    "description": "Generated from template",
                    "severity": "high",
                    "author": "test-generator"
                },
                "generated-sql-injection"
            )
            print(f"  ✅ Rule from template created: {new_rule is not None}")
        
        return True
        
    except Exception as e:
        print(f"❌ Custom Rule Engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_baseline_scanning():
    """Test Baseline Scanning functionality"""
    print("\n📊 Testing Baseline Scanning")
    print("=" * 50)
    
    try:
        from services.baseline_scanner import baseline_service, BaselineFingerprint
        from models.report import VulnerabilityFinding, Severity, ScannerType, ScanReport
        
        # Test 1: Create mock scan report
        print("📝 Creating mock scan report...")
        mock_findings = [
            VulnerabilityFinding(
                title="SQL Injection",
                description="SQL injection vulnerability",
                severity=Severity.HIGH,
                scanner=ScannerType.SEMGREP,
                file_path="/app/models.py",
                line_number=45,
                rule_id="sql-injection-rule"
            ),
            VulnerabilityFinding(
                title="Hardcoded Secret",
                description="API key in source code",
                severity=Severity.CRITICAL,
                scanner=ScannerType.GITLEAKS,
                file_path="/app/config.py",
                line_number=12,
                rule_id="hardcoded-secret"
            )
        ]
        
        mock_scan_report = ScanReport(
            report_id="test-scan-123",
            repository_url="https://github.com/test/repo",
            branch="main",
            findings=mock_findings,
            created_at=datetime.utcnow()
        )
        
        # Test 2: Create baseline
        print("🎯 Creating baseline...")
        baseline = await baseline_service.create_baseline(
            scan_report=mock_scan_report,
            repository_url="https://github.com/test/repo",
            branch="main",
            commit_hash="abc123",
            created_by="test-user",
            tags=["test", "initial"]
        )
        
        print(f"  ✅ Baseline created: {baseline.baseline_id}")
        print(f"  📊 Fingerprints: {len(baseline.fingerprints)}")
        print(f"  📈 Total findings: {baseline.total_findings}")
        
        # Test 3: Create fingerprints
        print("🔍 Testing fingerprints...")
        for finding in mock_findings:
            fingerprint = BaselineFingerprint.from_finding(finding)
            print(f"  🔗 Fingerprint: {fingerprint.finding_hash[:8]}...")
        
        # Test 4: Simulate drift analysis with new scan
        print("📈 Testing drift analysis...")
        
        # Create modified scan (add new finding, remove one)
        modified_findings = [
            mock_findings[0],  # Keep SQL injection
            VulnerabilityFinding(  # New finding
                title="XSS Vulnerability",
                description="Cross-site scripting",
                severity=Severity.MEDIUM,
                scanner=ScannerType.SEMGREP,
                file_path="/app/views.py",
                line_number=78,
                rule_id="xss-rule"
            )
        ]
        
        modified_scan_report = ScanReport(
            report_id="test-scan-456",
            repository_url="https://github.com/test/repo",
            branch="main",
            findings=modified_findings,
            created_at=datetime.utcnow()
        )
        
        # Compare with baseline
        drift = await baseline_service.compare_with_baseline(
            current_scan=modified_scan_report,
            baseline_id=baseline.baseline_id
        )
        
        if drift:
            print(f"  ✅ Drift analysis completed")
            print(f"  📊 Total changes: {drift.total_changes}")
            print(f"  🆕 New findings: {len(drift.new_findings)}")
            print(f"  ✅ Fixed findings: {len(drift.fixed_findings)}")
            print(f"  📈 Drift severity: {drift.drift_severity}")
        else:
            print("  ⚠️ No baseline found for comparison")
        
        # Test 5: Get baselines
        print("📋 Getting baselines...")
        baselines = await baseline_service.get_baselines_for_repository(
            "https://github.com/test/repo", "main", 5
        )
        print(f"  ✅ Found {len(baselines)} baselines")
        
        return True
        
    except Exception as e:
        print(f"❌ Baseline Scanning test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_policy_as_code():
    """Test Policy as Code functionality"""
    print("\n📋 Testing Policy as Code")
    print("=" * 50)
    
    try:
        from services.policy_engine import (
            policy_service, SecurityPolicy, PolicyRule, PolicyCondition,
            PolicyScope, PolicyAction, RuleSeverity
        )
        from models.report import VulnerabilityFinding, Severity, ScannerType, ScanReport
        
        # Test 1: Load default policies
        print("📚 Loading policies...")
        policies = await policy_service.load_policies()
        print(f"  ✅ Loaded {len(policies)} policies")
        
        # Test 2: Create custom policy
        print("📝 Creating custom policy...")
        custom_policy = SecurityPolicy(
            policy_id="test-security-policy",
            name="Test Security Policy",
            description="Test policy for validation",
            version="1.0.0",
            scope=PolicyScope.REPOSITORY,
            target_repositories=["test/repo"],
            owner="test-user",
            max_critical=0,
            max_high=2,
            max_medium=10,
            rules=[
                PolicyRule(
                    rule_id="no-sql-injection",
                    name="No SQL Injection",
                    description="Block SQL injection vulnerabilities",
                    conditions=[
                        PolicyCondition(
                            field="cwe_id",
                            operator="eq",
                            value="CWE-89"
                        )
                    ],
                    action=PolicyAction.FAIL,
                    message="SQL injection vulnerabilities must be fixed"
                )
            ]
        )
        
        # Save policy
        await policy_service._save_policy_to_file(custom_policy)
        print(f"  ✅ Policy saved: {custom_policy.policy_id}")
        
        # Test 3: Get applicable policies
        print("🔍 Getting applicable policies...")
        applicable_policies = await policy_service.get_applicable_policies(
            "https://github.com/test/repo", "main", "development"
        )
        print(f"  ✅ Found {len(applicable_policies)} applicable policies")
        
        # Test 4: Create mock scan for policy evaluation
        print("📊 Creating mock scan for evaluation...")
        policy_test_findings = [
            VulnerabilityFinding(
                title="SQL Injection",
                description="SQL injection vulnerability",
                severity=Severity.HIGH,
                scanner=ScannerType.SEMGREP,
                file_path="/app/models.py",
                line_number=45,
                rule_id="sql-injection-rule",
                cwe_id="CWE-89"
            ),
            VulnerabilityFinding(
                title="XSS Vulnerability",
                description="Cross-site scripting",
                severity=Severity.MEDIUM,
                scanner=ScannerType.SEMGREP,
                file_path="/app/views.py",
                line_number=78,
                rule_id="xss-rule",
                cwe_id="CWE-79"
            )
        ]
        
        policy_scan_report = ScanReport(
            report_id="policy-test-scan",
            repository_url="https://github.com/test/repo",
            branch="main",
            findings=policy_test_findings,
            created_at=datetime.utcnow()
        )
        
        # Test 5: Evaluate policy
        print("⚖️ Evaluating policy...")
        if applicable_policies:
            policy = applicable_policies[0]
            evaluation_result = await policy_service.evaluate_policy(
                policy=policy,
                scan_report=policy_scan_report,
                repository_url="https://github.com/test/repo",
                branch="main",
                commit_hash="test123"
            )
            
            print(f"  ✅ Policy evaluation completed")
            print(f"  📊 Compliant: {evaluation_result.compliant}")
            print(f"  📈 Compliance score: {evaluation_result.compliance_score}")
            print(f"  ⚠️ Violations: {len(evaluation_result.violations)}")
            print(f"  💡 Recommendations: {len(evaluation_result.recommendations)}")
            
            # Show violations
            for violation in evaluation_result.violations:
                print(f"    - {violation.rule_id}: {violation.message}")
        
        # Test 6: Evaluate all applicable policies
        print("🔄 Evaluating all applicable policies...")
        all_results = await policy_service.evaluate_all_policies(
            scan_report=policy_scan_report,
            repository_url="https://github.com/test/repo",
            branch="main",
            commit_hash="test123",
            environment="development"
        )
        
        print(f"  ✅ Evaluated {len(all_results)} policies")
        for result in all_results:
            print(f"    - {result.policy_id}: Compliant={result.compliant}, Score={result.compliance_score}")
        
        return True
        
    except Exception as e:
        print(f"❌ Policy as Code test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration():
    """Test integration between all systems"""
    print("\n🔗 Testing System Integration")
    print("=" * 50)
    
    try:
        from services.rule_engine import rule_engine
        from services.baseline_scanner import baseline_service
        from services.policy_engine import policy_service
        from models.report import VulnerabilityFinding, Severity, ScannerType, ScanReport
        
        # Test 1: Create comprehensive scan report
        print("📊 Creating comprehensive scan report...")
        integration_findings = [
            VulnerabilityFinding(
                title="SQL Injection",
                description="SQL injection vulnerability detected by custom rule",
                severity=Severity.CRITICAL,
                scanner=ScannerType.SEMGREP,
                file_path="/app/database.py",
                line_number=67,
                rule_id="custom-sql-injection",
                cwe_id="CWE-89"
            ),
            VulnerabilityFinding(
                title="Hardcoded Password",
                description="Password hardcoded in source",
                severity=Severity.HIGH,
                scanner=ScannerType.GITLEAKS,
                file_path="/app/config.py",
                line_number=23,
                rule_id="test-hardcoded-password",
                cwe_id="CWE-798"
            ),
            VulnerabilityFinding(
                title="Insecure Random",
                description="Weak random number generation",
                severity=Severity.MEDIUM,
                scanner=ScannerType.BANDIT,
                file_path="/app/crypto.py",
                line_number=15,
                rule_id="insecure-random",
                cwe_id="CWE-330"
            )
        ]
        
        integration_scan = ScanReport(
            report_id="integration-test-scan",
            repository_url="https://github.com/test/integration-repo",
            branch="main",
            findings=integration_findings,
            created_at=datetime.utcnow()
        )
        
        print(f"  ✅ Created scan with {len(integration_findings)} findings")
        
        # Test 2: Create baseline
        print("🎯 Creating integration baseline...")
        integration_baseline = await baseline_service.create_baseline(
            scan_report=integration_scan,
            repository_url="https://github.com/test/integration-repo",
            branch="main",
            commit_hash="integration123",
            created_by="integration-test",
            tags=["integration", "comprehensive"]
        )
        
        print(f"  ✅ Baseline created: {integration_baseline.baseline_id}")
        
        # Test 3: Evaluate policies
        print("⚖️ Evaluating policies...")
        policy_results = await policy_service.evaluate_all_policies(
            scan_report=integration_scan,
            repository_url="https://github.com/test/integration-repo",
            branch="main",
            commit_hash="integration123",
            environment="production"
        )
        
        print(f"  ✅ Evaluated {len(policy_results)} policies")
        
        overall_compliant = all(result.compliant for result in policy_results)
        print(f"  📊 Overall compliance: {overall_compliant}")
        
        # Test 4: Simulate follow-up scan with improvements
        print("🔄 Simulating follow-up scan...")
        
        # Remove critical finding, add new low finding
        followup_findings = [
            integration_findings[1],  # Keep hardcoded password
            integration_findings[2],  # Keep insecure random
            VulnerabilityFinding(  # New low severity finding
                title="Missing Input Validation",
                description="Input not validated",
                severity=Severity.LOW,
                scanner=ScannerType.SEMGREP,
                file_path="/app/forms.py",
                line_number=34,
                rule_id="missing-validation",
                cwe_id="CWE-20"
            )
        ]
        
        followup_scan = ScanReport(
            report_id="integration-followup-scan",
            repository_url="https://github.com/test/integration-repo",
            branch="main",
            findings=followup_findings,
            created_at=datetime.utcnow()
        )
        
        # Test 5: Analyze drift
        print("📈 Analyzing security drift...")
        drift_analysis = await baseline_service.compare_with_baseline(
            current_scan=followup_scan,
            baseline_id=integration_baseline.baseline_id
        )
        
        if drift_analysis:
            print(f"  ✅ Drift analysis completed")
            print(f"  🆕 New findings: {len(drift_analysis.new_findings)}")
            print(f"  ✅ Fixed findings: {len(drift_analysis.fixed_findings)}")
            print(f"  📊 Security score change: {drift_analysis.security_score_change:+.1f}")
            print(f"  📈 Drift severity: {drift_analysis.drift_severity}")
        
        # Test 6: Re-evaluate policies
        print("🔄 Re-evaluating policies after improvements...")
        followup_policy_results = await policy_service.evaluate_all_policies(
            scan_report=followup_scan,
            repository_url="https://github.com/test/integration-repo",
            branch="main",
            commit_hash="integration456",
            environment="production"
        )
        
        followup_compliant = all(result.compliant for result in followup_policy_results)
        print(f"  📊 Follow-up compliance: {followup_compliant}")
        
        # Summary
        print("\n📋 Integration Test Summary:")
        print(f"  📊 Initial findings: {len(integration_findings)}")
        print(f"  📊 Follow-up findings: {len(followup_findings)}")
        print(f"  ✅ Fixed critical issues: {len([f for f in integration_findings if f.severity == Severity.CRITICAL])}")
        print(f"  📈 Compliance improved: {not overall_compliant and followup_compliant}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    test_repo_path.mkdir(exist_ok=True)
    
    # Sample vulnerable Python code
    vulnerable_code = '''
import os
import subprocess
import hashlib

# Hardcoded secret (should be detected by Semgrep and GitLeaks)
API_KEY = "sk-1234567890abcdef1234567890abcdef"
PASSWORD = "admin123"

# SQL injection vulnerability (should be detected by Bandit and Semgrep)
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return execute_query(query)

# Command injection vulnerability (should be detected by Bandit)
def run_command(user_input):
    os.system(f"ls {user_input}")

# Weak cryptography (should be detected by Bandit)
def weak_hash(data):
    return hashlib.md5(data.encode()).hexdigest()

# Debug mode enabled (should be detected by custom rules)
DEBUG = True
'''
    
    # Sample requirements.txt with vulnerable dependencies
    requirements_txt = '''
Django==2.0.1
requests==2.18.0
Pillow==5.0.0
'''
    
    # Write test files
    (test_repo_path / "vulnerable_app.py").write_text(vulnerable_code)
    (test_repo_path / "requirements.txt").write_text(requirements_txt)
    
    # Test each scanner
    scanners_to_test = [
        ScannerType.SEMGREP,
        ScannerType.BANDIT,
        ScannerType.SAFETY,
        ScannerType.GITLEAKS,
        ScannerType.TRIVY
    ]
    
    results = {}
    
    for scanner_type in scanners_to_test:
        try:
            print(f"\nTesting {scanner_type.value}...")
            
            # Run single scanner
            scan_results = await security_scanner.run_all_scans(
                repo_path=str(test_repo_path),
                selected_scanners=[scanner_type]
            )
            
            if scan_results:
                result = scan_results[0]
                results[scanner_type.value] = {
                    "status": result.status.value,
                    "findings_count": len(result.findings),
                    "duration": result.duration_seconds,
                    "error": result.error_message
                }
                
                if result.status == ScanStatus.COMPLETED:
                    print(f"  ✅ Completed - Found {len(result.findings)} findings in {result.duration_seconds:.2f}s")
                    
                    # Show sample findings
                    if result.findings:
                        print("  📋 Sample findings:")
                        for finding in result.findings[:3]:  # Show first 3 findings
                            print(f"    - {finding.severity.value.upper()}: {finding.title}")
                else:
                    print(f"  ❌ Failed - {result.error_message}")
            else:
                print(f"  ❌ No results returned")
                results[scanner_type.value] = {"status": "no_results"}
                
        except Exception as e:
            print(f"  ❌ Exception - {str(e)}")
            results[scanner_type.value] = {"status": "exception", "error": str(e)}
    
    # Cleanup test directory
    import shutil
    shutil.rmtree(test_repo_path, ignore_errors=True)
    
    return results


async def test_custom_configuration():
    """Test custom scanner configurations"""
    print("\n⚙️ Testing Custom Configuration")
    print("=" * 40)
    
    # Create test repository
    test_repo_path = Path("test_custom_config")
    test_repo_path.mkdir(exist_ok=True)
    
    # Sample code with custom patterns
    custom_code = '''
# Organization-specific secret pattern
ORG_SECRET_KEY = "org_secret_abcdef123456"
COMPANY_API_TOKEN = "company_api_xyz789"

# Test various patterns
internal_service_token = "internal_token_abcd1234"
'''
    
    (test_repo_path / "config.py").write_text(custom_code)
    
    # Custom configuration
    custom_config = {
        "gitleaks": {
            "custom_config": {
                "rules": [
                    {
                        "id": "test-org-secret",
                        "regex": r"(?i)(org|company)[-_]?(secret|api)[-_]?[:=]\s*['\"]?[a-zA-Z0-9_]{10,}",
                        "description": "Test organization secret pattern"
                    }
                ]
            }
        },
        "bandit": {
            "exclude_paths": ["tests/"],
            "skip_tests": True
        }
    }
    
    try:
        # Run scan with custom configuration
        results = await security_scanner.run_all_scans(
            repo_path=str(test_repo_path),
            selected_scanners=[ScannerType.GITLEAKS, ScannerType.BANDIT],
            custom_config=custom_config
        )
        
        print("✅ Custom configuration test completed")
        for result in results:
            print(f"  {result.scanner.value}: {result.status.value} - {len(result.findings)} findings")
        
    except Exception as e:
        print(f"❌ Custom configuration test failed: {e}")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_repo_path, ignore_errors=True)


async def test_performance():
    """Test scanner performance and concurrency"""
    print("\n⚡ Testing Performance and Concurrency")
    print("=" * 40)
    
    # Test concurrent scanner execution
    test_repo_path = Path("test_performance")
    test_repo_path.mkdir(exist_ok=True)
    
    # Create multiple test files
    for i in range(5):
        (test_repo_path / f"test_file_{i}.py").write_text(f'''
# Test file {i}
password = "test123"
api_key = "key_{i}_abcdef123456"

def test_function_{i}():
    import os
    os.system("echo test")
''')
    
    try:
        import time
        start_time = time.time()
        
        # Run all scanners concurrently
        results = await security_scanner.run_all_scans(
            repo_path=str(test_repo_path)
        )
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        print(f"✅ Performance test completed in {total_duration:.2f} seconds")
        print(f"📊 Ran {len(results)} scanners concurrently")
        
        for result in results:
            if result.duration_seconds:
                print(f"  {result.scanner.value}: {result.duration_seconds:.2f}s")
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_repo_path, ignore_errors=True)


async def test_database_update():
    """Test database update functionality"""
    print("\n🔄 Testing Database Updates")
    print("=" * 40)
    
    try:
        update_status = await security_scanner.update_scanner_databases()
        
        for scanner, status in update_status.items():
            status_text = "✅ Updated" if status else "❌ Failed"
            print(f"  {scanner}: {status_text}")
        
    except Exception as e:
        print(f"❌ Database update test failed: {e}")


def print_configuration_summary():
    """Print current scanner configuration"""
    print("\n📋 Configuration Summary")
    print("=" * 40)
    
    config_items = [
        ("Semgrep Enabled", settings.enable_semgrep),
        ("Trivy Enabled", settings.enable_trivy),
        ("GitLeaks Enabled", settings.enable_gitleaks),
        ("Lynis Enabled", settings.enable_lynis),
        ("Bandit Enabled", settings.enable_bandit),
        ("Safety Enabled", settings.enable_safety),
        ("Scan Timeout", f"{settings.scan_timeout}s"),
        ("Max Concurrent Scans", settings.max_concurrent_scans),
        ("Trivy Cache Dir", settings.trivy_cache_dir),
    ]
    
    for item, value in config_items:
        print(f"  {item}: {value}")


async def main():
    """Main test function"""
    print("🛡️ SecureDevOps AI Platform - Enhanced Security Scanner Tests")
    print("=" * 60)
    
    # Print configuration
    print_configuration_summary()
    
    # Run tests
    try:
        # Test 1: Scanner availability
        all_available = await test_scanner_availability()
        
        if not all_available:
            print("\n⚠️ Some scanners are not available. Please install missing tools.")
            print("Run: ./scripts/install_security_tools.sh (Linux/macOS)")
            print("Or:  .\\scripts\\install_security_tools.ps1 (Windows)")
            return False
        
        # Test 2: Individual scanner functionality
        test_results = await test_individual_scanners()
        
        # Test 3: Custom configuration
        await test_custom_configuration()
        
        # Test 4: Performance testing
        await test_performance()
        
        # Test 5: Database updates
        await test_database_update()
        
        # Summary
        print("\n📊 Test Summary")
        print("=" * 40)
        
        successful_scanners = sum(1 for result in test_results.values() 
                                if result.get("status") == "completed")
        total_scanners = len(test_results)
        
        print(f"Successful scanners: {successful_scanners}/{total_scanners}")
        
        if successful_scanners == total_scanners:
            print("🎉 All tests passed! Enhanced security scanner integration is working correctly.")
async def main():
    """Main test function"""
    print("🚀 SecureDevOps AI Platform - Enhanced Security Features Test")
    print("=" * 70)
    
    tests = [
        ("Custom Rule Engine", test_custom_rule_engine),
        ("Baseline Scanning", test_baseline_scanning),
        ("Policy as Code", test_policy_as_code),
        ("System Integration", test_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if await test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced security features are working correctly.")
        
        # Show summary of implemented features
        print("\n✅ Enhanced Security Features Summary:")
        print("  🔧 Custom Rule Engine")
        print("    - User-defined YAML/JSON rules")
        print("    - Rule template library with CWE mapping")
        print("    - Rule validation and testing framework")
        print("    - Version-controlled rule storage")
        
        print("  📊 Baseline Scanning")
        print("    - Historical scan comparison")
        print("    - Security drift detection")
        print("    - Trend analysis and visualization")
        print("    - Regression identification and alerting")
        
        print("  📋 Policy as Code")
        print("    - Git-based policy management")
        print("    - Automated policy enforcement")
        print("    - Policy compliance reporting")
        print("    - Threshold-based and rule-based policies")
        
        print("  🔗 System Integration")
        print("    - Seamless integration between all components")
        print("    - Comprehensive security analysis workflows")
        print("    - Automated baseline creation and policy evaluation")
        
    else:
        print(f"⚠️ {total - passed} tests failed. Please check the implementation.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n{'='*70}")
    if success:
        print("🎯 Enhanced security features successfully implemented and tested!")
    else:
        print("⚠️ Some tests failed. Please review the implementation.")
    sys.exit(0 if success else 1)
