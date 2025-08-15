#!/usr/bin/env python3
"""
Quick test for security boundaries - should complete in under 30 seconds
"""
import asyncio
import sys
import os
import time

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.rule_engine import CustomRuleEngine, CustomRule, AllowedRuleType, SeverityLevel, AllowedLanguage


async def quick_test():
    """Quick test of key security boundaries"""
    print("🚀 Quick Security Boundaries Test")
    print("=" * 40)
    
    start_time = time.time()
    
    # Initialize components
    rule_engine = CustomRuleEngine()
    
    # Test 1: Valid rule should pass
    print("\n✅ Testing valid rule...")
    valid_rule = CustomRule(
        id="test-valid",
        name="Valid Test Rule",
        description="A valid rule for testing",
        type=AllowedRuleType.REGEX,
        severity=SeverityLevel.MEDIUM,
        languages=[AllowedLanguage.PYTHON],
        author="test-user",
        category="testing",
        pattern=r"password\s*=\s*['\"][^'\"]{3,}['\"]",  # Simple, safe pattern
        file_patterns=["**/*.py"],
        test_cases=[
            {
                "name": "test_case",
                "content": "password = 'test123'",
                "expected_matches": 1
            }
        ]
    )
    
    try:
        result = await rule_engine.validate_rule_security(valid_rule)
        if result.is_valid:
            print("✅ Valid rule passed validation")
        else:
            print(f"❌ Valid rule failed: {result.errors}")
    except Exception as e:
        print(f"❌ Exception during valid rule test: {e}")
    
    # Test 2: ReDoS pattern should fail
    print("\n❌ Testing ReDoS vulnerable pattern...")
    redos_rule = CustomRule(
        id="test-redos",
        name="ReDoS Test Rule",
        description="A rule with ReDoS vulnerability",
        type=AllowedRuleType.REGEX,
        severity=SeverityLevel.LOW,
        languages=[AllowedLanguage.PYTHON],
        author="test-user",
        category="testing",
        pattern=r"(a+)+b",  # Classic ReDoS pattern
        file_patterns=["**/*.py"],
        test_cases=[
            {
                "name": "test_case",
                "content": "aaaaaaaaab",
                "expected_matches": 1
            }
        ]
    )
    
    try:
        result = await rule_engine.validate_rule_security(redos_rule)
        if not result.is_valid:
            print("✅ ReDoS pattern correctly rejected")
        else:
            print("❌ ReDoS pattern was incorrectly accepted")
    except Exception as e:
        print(f"❌ Exception during ReDoS test: {e}")
    
    # Test 3: Path traversal should fail
    print("\n❌ Testing path traversal...")
    path_traversal_rule = CustomRule(
        id="test-traversal",
        name="Path Traversal Test",
        description="A rule with path traversal",
        type=AllowedRuleType.REGEX,
        severity=SeverityLevel.LOW,
        languages=[AllowedLanguage.PYTHON],
        author="test-user",
        category="testing",
        pattern=r"test",
        file_patterns=["../../../etc/passwd"],  # Path traversal
        test_cases=[
            {
                "name": "test_case",
                "content": "test",
                "expected_matches": 1
            }
        ]
    )
    
    try:
        result = await rule_engine.validate_rule_security(path_traversal_rule)
        if not result.is_valid:
            print("✅ Path traversal correctly rejected")
        else:
            print("❌ Path traversal was incorrectly accepted")
    except Exception as e:
        print(f"❌ Exception during path traversal test: {e}")
    
    elapsed = time.time() - start_time
    print(f"\n⏱️  Test completed in {elapsed:.2f} seconds")
    
    if elapsed < 30:
        print("✅ Test ran efficiently (under 30 seconds)")
    else:
        print("⚠️  Test took longer than expected")


if __name__ == "__main__":
    asyncio.run(quick_test())
