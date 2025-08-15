#!/usr/bin/env python3
"""
Simple test to debug the rule validation issue
"""
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_imports():
    """Test if all imports work correctly"""
    print("Testing imports...")
    
    try:
        from services.rule_security import SecureRuleValidator
        print("✅ SecureRuleValidator imported successfully")
        
        validator = SecureRuleValidator()
        print("✅ SecureRuleValidator created successfully")
        
        # Test a simple method
        test_rule = {
            'id': 'test',
            'name': 'Test Rule', 
            'type': 'semgrep',
            'metadata': {
                'cwe': 'CWE-89'
            }
        }
        
        result_metadata = validator.validate_rule_metadata(test_rule)
        print(f"✅ validate_rule_metadata returned: {result_metadata}")
        
        result_content = validator.validate_rule_content(test_rule)
        print(f"✅ validate_rule_content returned: {result_content}")
        
        result_safety = validator.validate_rule_safety(test_rule)
        print(f"✅ validate_rule_safety returned: {result_safety}")
        
    except Exception as e:
        print(f"❌ Import/initialization error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_rule_engine():
    """Test the rule engine directly"""
    print("\nTesting rule engine...")
    
    try:
        from services.rule_engine import CustomRuleEngine
        print("✅ CustomRuleEngine imported successfully")
        
        engine = CustomRuleEngine()
        print("✅ CustomRuleEngine created successfully")
        
        print(f"Security validator type: {type(engine.security_validator)}")
        print(f"Testing framework type: {type(engine.testing_framework)}")
        
    except Exception as e:
        print(f"❌ Rule engine error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("🔍 Debugging Rule Validation Issues")
    print("=" * 50)
    
    success1 = test_imports()
    success2 = test_rule_engine()
    
    if success1 and success2:
        print("\n✅ All basic tests passed!")
    else:
        print("\n❌ Some tests failed!")
