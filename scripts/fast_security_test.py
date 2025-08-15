#!/usr/bin/env python3
"""
Fast security boundaries test - should complete in under 30 seconds
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.rule_engine import CustomRuleEngine, CustomRule, AllowedRuleType, SeverityLevel, AllowedLanguage


async def quick_test():
    """Quick test of security boundaries - should complete in 10-15 seconds"""
    print("🚀 Fast Security Boundaries Test")
    print("Expected runtime: 10-15 seconds")
    print("=" * 50)
    
    rule_engine = CustomRuleEngine()
    
    # Test 1: Valid rule (should pass)
    print("\n✅ Testing valid rule...")
    try:
        valid_rule = CustomRule(
            id="test-valid",
            name="Valid Test Rule",
            description="A valid rule for testing",
            message="Test security issue detected",  # Required field!
            type=AllowedRuleType.REGEX,
            severity=SeverityLevel.MEDIUM,
            languages=[AllowedLanguage.PYTHON],
            author="test-team",
            category="security",
            pattern=r"password\s*=\s*['\"][^'\"]{3,}['\"]",  # Simple, safe pattern
            file_patterns=["**/*.py"],
            test_cases=[
                {
                    "name": "positive_test",
                    "content": "password = 'secret123'",
                    "expected_matches": 1
                }
            ]
        )
        
        result = await rule_engine.validate_rule_security(valid_rule)
        if result.is_valid:
            print("✅ Valid rule passed validation")
        else:
            print(f"❌ Valid rule failed: {result.errors}")
            
    except Exception as e:
        print(f"❌ Error testing valid rule: {e}")
    
    # Test 2: ReDoS vulnerable pattern (should fail)
    print("\n❌ Testing ReDoS vulnerable pattern...")
    try:
        redos_rule = CustomRule(
            id="test-redos",
            name="ReDoS Test Rule",
            description="A rule with ReDoS vulnerability",
            message="ReDoS vulnerability detected",
            type=AllowedRuleType.REGEX,
            severity=SeverityLevel.HIGH,
            languages=[AllowedLanguage.PYTHON],
            author="test-team",
            category="testing",
            pattern=r"(a+)+b",  # Classic ReDoS pattern
            file_patterns=["**/*.py"],
            test_cases=[
                {
                    "name": "test_case",
                    "content": "aaaaaaaaaaaaaaaaaaaaaaaac",
                    "expected_matches": 0
                }
            ]
        )
        
        result = await rule_engine.validate_rule_security(redos_rule)
        if not result.is_valid:
            print("✅ ReDoS pattern correctly rejected")
            print(f"   Reasons: {result.errors[:2]}")  # Show first 2 errors
        else:
            print("❌ ReDoS pattern incorrectly accepted")
            
    except Exception as e:
        print(f"❌ Error testing ReDoS rule: {e}")
    
    # Test 3: Path traversal (should fail)
    print("\n❌ Testing path traversal...")
    try:
        path_rule = CustomRule(
            id="test-path",
            name="Path Traversal Test",
            description="A rule with path traversal",
            message="Path traversal detected",
            type=AllowedRuleType.REGEX,
            severity=SeverityLevel.LOW,
            languages=[AllowedLanguage.PYTHON],
            author="test-team",
            category="testing",
            pattern=r"secret",
            file_patterns=["../../../etc/passwd"],  # Path traversal
            test_cases=[
                {
                    "name": "test_case",
                    "content": "secret = 'value'",
                    "expected_matches": 1
                }
            ]
        )
        
        result = await rule_engine.validate_rule_security(path_rule)
        if not result.is_valid:
            print("✅ Path traversal correctly rejected")
            print(f"   Reasons: {result.errors[:2]}")
        else:
            print("❌ Path traversal incorrectly accepted")
            
    except Exception as e:
        print(f"❌ Error testing path traversal: {e}")
    
    # Test 4: Missing metadata (should fail)
    print("\n❌ Testing missing metadata...")
    try:
        missing_meta_rule = CustomRule(
            id="test-meta",
            name="Missing Metadata Test",
            description="A rule missing required metadata",
            message="Missing metadata test",
            type=AllowedRuleType.SEMGREP,
            severity=SeverityLevel.HIGH,
            languages=[AllowedLanguage.PYTHON],
            author="test-team",
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
        )
        
        result = await rule_engine.validate_rule_security(missing_meta_rule)
        if not result.is_valid:
            print("✅ Missing metadata correctly rejected")
            print(f"   Reasons: {result.errors[:2]}")
        else:
            print("❌ Missing metadata incorrectly accepted")
            
    except Exception as e:
        print(f"❌ Error testing missing metadata: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Fast test completed!")
    print("✅ If you see the above results, the security boundaries are working")
    print("⏱️  This test should have completed in 10-15 seconds")


if __name__ == "__main__":
    import time
    start_time = time.time()
    
    asyncio.run(quick_test())
    
    elapsed = time.time() - start_time
    print(f"\n⏱️  Actual runtime: {elapsed:.1f} seconds")
    
    if elapsed > 30:
        print("⚠️  Test took longer than expected (>30s)")
    elif elapsed < 20:
        print("🚀 Test completed quickly!")
    else:
        print("✅ Test completed in reasonable time")
