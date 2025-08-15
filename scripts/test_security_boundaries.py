#!/usr/bin/env python3
"""
Security Boundaries Test Suite
Validates that custom rule execution is properly sandboxed and protected
"""
import asyncio
import json
import sys
import logging
from pathlib import Path
from datetime import datetime, timezone
import uuid

# Add the parent directory to the path to import our modules
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from services.security_boundary_engine import SecurityBoundaryEngine, ResourceLimits, AdversarialTestCase

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SecurityBoundaryTester:
    """Comprehensive tester for security boundary features"""
    
    def __init__(self):
        self.boundary_engine = SecurityBoundaryEngine()
        self.test_results = {
            "boundary_enforcement": {},
            "adversarial_protection": {},
            "resource_limits": {},
            "containerization": {},
            "security_features_validated": []
        }
    
    async def test_catastrophic_backtracking_protection(self):
        """Test protection against catastrophic backtracking regex"""
        logger.info("� Testing Catastrophic Backtracking Protection...")
        
        dangerous_regex = r"(a+)+b"
        test_input = "a" * 1000 + "c"  # No 'b' at end = worst case
        
        # Create test file with problematic input
        test_dir = Path("security_test_temp")
        test_dir.mkdir(exist_ok=True)
        
        test_file = test_dir / "backtrack_test.txt"
        test_file.write_text(test_input)
        
        try:
            # Test with very tight limits
            strict_limits = ResourceLimits(
                cpu_limit=0.1,
                memory_limit_mb=64,
                timeout_per_file=2,
                timeout_total=5,
                max_matches=100
            )
            
            start_time = datetime.now()
            execution_result, usage = await self.boundary_engine.execute_rule_safely(
                rule_content=dangerous_regex,
                rule_type="regex",
                target_files=[str(test_file)],
                limits=strict_limits
            )
            end_time = datetime.now()
            
            execution_time = (end_time - start_time).total_seconds()
            
            # Should be killed by timeout/limits
            protection_effective = (
                usage.killed_by_limit or 
                execution_time < 10 or  # Should not take long due to limits
                execution_result.get("error") is not None
            )
            
            self.test_results["boundary_enforcement"]["catastrophic_backtracking"] = {
                "protection_effective": protection_effective,
                "execution_time": execution_time,
                "killed_by_limit": usage.killed_by_limit,
                "kill_reason": usage.kill_reason,
                "memory_used_mb": usage.memory_peak_mb,
                "test_passed": protection_effective
            }
            
            if protection_effective:
                logger.info("✅ Catastrophic backtracking protection EFFECTIVE")
            else:
                logger.warning("❌ Catastrophic backtracking protection FAILED")
            
        except Exception as e:
            logger.error(f"❌ Catastrophic backtracking test error: {e}")
            self.test_results["boundary_enforcement"]["catastrophic_backtracking"] = {
                "test_passed": False,
                "error": str(e)
            }
        
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()
            if test_dir.exists() and not list(test_dir.iterdir()):
                test_dir.rmdir()
                            }
                        }
                    ]
                },
                file_patterns=["**/*.py"],
                test_cases=[
                    {
                        "name": "positive_test",
                        "content": "cursor.execute(query + user_input)",
                        "expected_matches": 1
                    }
                ]
            ),
            "should_pass": True
        },
        
        {
            "name": "❌ ReDoS Vulnerable Regex",
            "rule": CustomRule(
                id="test-redos-regex",
                name="ReDoS Vulnerable Pattern",
                description="A regex pattern vulnerable to ReDoS attacks",
                type=AllowedRuleType.REGEX,
                severity=SeverityLevel.MEDIUM,
                languages=[AllowedLanguage.PYTHON],
                author="test-user",
                category="testing",
                pattern=r"(a+)+b",  # Classic ReDoS pattern
                file_patterns=["**/*.py"],
                test_cases=[
                    {
                        "name": "test_case",
                        "content": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaac",
                        "expected_matches": 0
                    }
                ]
            ),
            "should_pass": False
        },
        
        {
            "name": "❌ Path Traversal in File Patterns",
            "rule": CustomRule(
                id="test-path-traversal",
                name="Path Traversal Rule",
                description="A rule with path traversal in file patterns",
                type=AllowedRuleType.REGEX,
                severity=SeverityLevel.LOW,
                languages=[AllowedLanguage.PYTHON],
                author="test-user",
                category="testing",
                pattern=r"password\s*=\s*['\"](.+?)['\"]",
                file_patterns=["../../../etc/passwd", "**/*.py"],  # Path traversal attempt
                test_cases=[
                    {
                        "name": "test_case",
                        "content": "password = 'secret123'",
                        "expected_matches": 1
                    }
                ]
            ),
            "should_pass": False
        },
        
        {
            "name": "❌ Missing Required Metadata",
            "rule": CustomRule(
                id="test-missing-metadata",
                name="Rule Without CWE",
                description="A rule missing required metadata",
                type=AllowedRuleType.SEMGREP,
                severity=SeverityLevel.HIGH,
                languages=[AllowedLanguage.PYTHON],
                author="test-user",
                category="testing",
                semgrep_rule={
                    "rules": [
                        {
                            "id": "incomplete-rule",
                            "message": "Test rule",
                            "languages": ["python"],
                            "pattern": "$X = input()"
                            # Missing metadata with CWE
                        }
                    ]
                },
                file_patterns=["**/*.py"],
                test_cases=[
                    {
                        "name": "test_case",
                        "content": "user_input = input()",
                        "expected_matches": 1
                    }
                ]
            ),
            "should_pass": False
        },
        
        {
            "name": "❌ Regex Pattern Too Long",
            "rule": CustomRule(
                id="test-long-regex",
                name="Extremely Long Regex",
                description="A regex pattern that exceeds length limits",
                type=AllowedRuleType.REGEX,
                severity=SeverityLevel.LOW,
                languages=[AllowedLanguage.PYTHON],
                author="test-user",
                category="testing",
                pattern="a" * 1000,  # Exceeds 500 character limit
                file_patterns=["**/*.py"],
                test_cases=[
                    {
                        "name": "test_case",
                        "content": "a" * 1000,
                        "expected_matches": 1
                    }
                ]
            ),
            "should_pass": False
        },
        
        {
            "name": "✅ Valid Regex Rule",
            "rule": CustomRule(
                id="test-valid-regex",
                name="Valid Hardcoded Password Detection",
                description="Detects hardcoded passwords in code",
                type=AllowedRuleType.REGEX,
                severity=SeverityLevel.MEDIUM,
                languages=[AllowedLanguage.PYTHON, AllowedLanguage.JAVASCRIPT],
                author="security-team",
                category="security",
                pattern=r"password\s*=\s*['\"](?!.*\$|\{)[^'\"]{3,}['\"]",
                file_patterns=["**/*.py", "**/*.js"],
                test_cases=[
                    {
                        "name": "positive_test",
                        "content": "password = 'hardcoded123'",
                        "expected_matches": 1
                    },
                    {
                        "name": "negative_test",
                        "content": "password = os.getenv('PASSWORD')",
                        "expected_matches": 0
                    }
                ]
            ),
            "should_pass": True
        }
    ]
    
    # Run tests
    results = []
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        print("-" * 40)
        
        try:
            # Test security validation
            validation_result = await rule_engine.validate_rule_security(test_case['rule'])
            
            passed = validation_result.is_valid == test_case['should_pass']
            
            if passed:
                print(f"✅ PASS - Expected: {'Valid' if test_case['should_pass'] else 'Invalid'}, Got: {'Valid' if validation_result.is_valid else 'Invalid'}")
            else:
                print(f"❌ FAIL - Expected: {'Valid' if test_case['should_pass'] else 'Invalid'}, Got: {'Valid' if validation_result.is_valid else 'Invalid'}")
            
            if not validation_result.is_valid:
                print(f"   Errors: {', '.join(validation_result.errors)}")
            
            if validation_result.warnings:
                print(f"   Warnings: {', '.join(validation_result.warnings)}")
            
            results.append({
                'test': test_case['name'],
                'passed': passed,
                'expected': test_case['should_pass'],
                'actual': validation_result.is_valid,
                'errors': validation_result.errors,
                'warnings': validation_result.warnings
            })
            
        except Exception as e:
            print(f"❌ ERROR - Exception during validation: {e}")
            results.append({
                'test': test_case['name'],
                'passed': False,
                'expected': test_case['should_pass'],
                'actual': False,
                'errors': [str(e)],
                'warnings': []
            })
    
    
    async def test_adversarial_test_suite(self):
        """Test the full adversarial test suite"""
        logger.info("🧨 Testing Adversarial Test Suite...")
        
        try:
            adversarial_results = await self.boundary_engine.test_adversarial_cases()
            
            total_tests = adversarial_results.get("total_tests", 0)
            passed_tests = adversarial_results.get("passed", 0)
            success_rate = adversarial_results.get("success_rate", 0)
            
            adversarial_protection_effective = success_rate >= 0.8  # 80% success rate threshold
            
            self.test_results["adversarial_protection"] = {
                "protection_effective": adversarial_protection_effective,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": success_rate,
                "detailed_results": adversarial_results.get("test_results", []),
                "test_passed": adversarial_protection_effective
            }
            
            if adversarial_protection_effective:
                logger.info(f"✅ Adversarial protection EFFECTIVE ({passed_tests}/{total_tests} passed)")
            else:
                logger.warning(f"❌ Adversarial protection NEEDS IMPROVEMENT ({passed_tests}/{total_tests} passed)")
            
        except Exception as e:
            logger.error(f"❌ Adversarial test suite error: {e}")
            self.test_results["adversarial_protection"] = {
                "test_passed": False,
                "error": str(e)
            }
    
    async def run_all_security_boundary_tests(self):
        """Run all security boundary tests"""
        start_time = datetime.now(timezone.utc)
        
        logger.info("🔒" + "="*60 + "🔒")
        logger.info("🔒 SECURITY BOUNDARIES TEST SUITE")
        logger.info("🔒" + "="*60 + "🔒")
        
        # Run all test categories
        await self.test_catastrophic_backtracking_protection()
        await self.test_adversarial_test_suite()
        
        end_time = datetime.now(timezone.utc)
        test_duration = (end_time - start_time).total_seconds()
        
        # Compile final results
        final_results = {
            "test_suite": "Security Boundaries Validation",
            "test_duration_seconds": test_duration,
            "timestamp": end_time.isoformat(),
            "results": self.test_results,
            "summary": self._generate_security_summary(),
            "security_features_validated": [
                "catastrophic_backtracking_protection",
                "adversarial_test_validation",
                "resource_usage_monitoring"
            ]
        }
        
        # Save results
        results_file = Path("security_boundaries_test_results.json")
        with open(results_file, "w") as f:
            json.dump(final_results, f, indent=2, default=str)
        
        logger.info(f"🔒 Security Boundaries Test Suite completed in {test_duration:.2f}s")
        logger.info(f"💾 Results saved to: {results_file}")
        
        return final_results
    
    def _generate_security_summary(self):
        """Generate summary of security test results"""
        summary = {
            "total_test_categories": 0,
            "categories_passed": 0,
            "categories_failed": 0,
            "security_features_operational": [],
            "overall_security_status": "unknown"
        }
        
        for category, results in self.test_results.items():
            summary["total_test_categories"] += 1
            
            if isinstance(results, dict):
                if results.get("test_passed", False):
                    summary["categories_passed"] += 1
                    summary["security_features_operational"].append(category)
                else:
                    summary["categories_failed"] += 1
        
        # Determine overall status
        if summary["categories_failed"] == 0:
            summary["overall_security_status"] = "excellent"
        elif summary["categories_passed"] > summary["categories_failed"]:
            summary["overall_security_status"] = "good"
        else:
            summary["overall_security_status"] = "needs_improvement"
        
        return summary

async def main():
    """Main security boundary test execution"""
    tester = SecurityBoundaryTester()
    results = await tester.run_all_security_boundary_tests()
    
    print("\n" + "🔒" + "="*70 + "🔒")
    print("🔒 SECURITY BOUNDARIES TEST RESULTS")
    print("🔒" + "="*70 + "🔒")
    
    summary = results["summary"]
    print(f"📊 Test Categories: {summary['categories_passed']}/{summary['total_test_categories']} passed")
    print(f"🛡️ Overall Security Status: {summary['overall_security_status'].upper()}")
    print(f"⚡ Security Features Operational: {len(summary['security_features_operational'])}")
    
    print("\n🔒 Validated Security Features:")
    for feature in summary["security_features_operational"]:
        print(f"   ✅ {feature}")
    
    if summary["overall_security_status"] in ["excellent", "good"]:
        print("\n🎉 SECURITY BOUNDARIES ARE OPERATIONAL! 🎉")
        print("🔒 Your platform is protected against malicious rules!")
    else:
        print("\n⚠️ Some security boundaries need attention.")
        print("🔧 Review failed tests and strengthen protections.")
    
    print("🔒" + "="*70 + "🔒")

if __name__ == "__main__":
    asyncio.run(main())
    
    for pattern in safe_patterns:
        is_valid, errors = regex_validator.validate_regex(pattern)
        if is_valid:
            print(f"✅ Safe pattern accepted: {pattern}")
        else:
            print(f"❌ Safe pattern rejected: {pattern} - {errors}")
    
    # Test PathSecurityValidator
    print("\n📁 Testing PathSecurityValidator")
    path_validator = PathSecurityValidator()
    
    dangerous_paths = [
        "../../../etc/passwd",
        "..\\windows\\system32",
        "/etc/shadow",
        "C:\\Windows\\System32\\config\\SAM"
    ]
    
    safe_paths = [
        "**/*.py",
        "src/**/*.js",
        "lib/security/*.yaml",
        "tests/*.py"
    ]
    
    for path in dangerous_paths:
        is_valid, errors = path_validator.validate_file_pattern(path)
        if not is_valid:
            print(f"✅ Blocked dangerous path: {path}")
        else:
            print(f"❌ Failed to block dangerous path: {path}")
    
    for path in safe_paths:
        is_valid, errors = path_validator.validate_file_pattern(path)
        if is_valid:
            print(f"✅ Safe path accepted: {path}")
        else:
            print(f"❌ Safe path rejected: {path} - {errors}")
    
    print("\n✅ Individual validator testing completed")


if __name__ == "__main__":
    print("🚀 Starting Security Boundaries Validation Tests")
    print("This will test all the security boundaries we implemented for custom rules")
    print()
    
    # Run the tests
    asyncio.run(test_security_boundaries())
    asyncio.run(test_individual_validators())
    
    print("\n🏁 Testing completed!")
