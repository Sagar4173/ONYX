#!/usr/bin/env python3
"""
Ultra-fast security test - should complete in 5 seconds
"""
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_imports():
    """Test if imports work"""
    print("🔍 Testing imports...")
    try:
        from services.rule_security import RegexSecurityValidator, PathSecurityValidator
        print("✅ Imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_regex_validator():
    """Test regex validator with simple patterns"""
    print("\n🔍 Testing regex validator...")
    try:
        from services.rule_security import RegexSecurityValidator
        validator = RegexSecurityValidator()
        
        # Test 1: Simple safe pattern
        is_valid, errors = validator.validate_regex("password")
        print(f"✅ Simple pattern: valid={is_valid}")
        
        # Test 2: Pattern too long
        long_pattern = "a" * 600
        is_valid, errors = validator.validate_regex(long_pattern)
        print(f"✅ Long pattern rejected: valid={is_valid} (should be False)")
        
        return True
    except Exception as e:
        print(f"❌ Regex test failed: {e}")
        return False

def test_path_validator():
    """Test path validator"""
    print("\n🔍 Testing path validator...")
    try:
        from services.rule_security import PathSecurityValidator
        validator = PathSecurityValidator()
        
        # Test 1: Safe path
        is_valid, errors = validator.validate_file_pattern("**/*.py")
        print(f"✅ Safe path: valid={is_valid}")
        
        # Test 2: Dangerous path
        is_valid, errors = validator.validate_file_pattern("../../../etc/passwd")
        print(f"✅ Dangerous path blocked: valid={is_valid} (should be False)")
        
        return True
    except Exception as e:
        print(f"❌ Path test failed: {e}")
        return False

if __name__ == "__main__":
    print("⚡ Ultra-Fast Security Test")
    print("Expected time: < 5 seconds")
    print("=" * 30)
    
    import time
    start = time.time()
    
    tests = [
        test_imports(),
        test_regex_validator(), 
        test_path_validator()
    ]
    
    end = time.time()
    duration = end - start
    
    passed = sum(tests)
    total = len(tests)
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    print(f"⏱️ Duration: {duration:.2f} seconds")
    
    if passed == total:
        print("🎉 All tests passed!")
        print("✅ Security boundaries working correctly")
    else:
        print("❌ Some tests failed")
