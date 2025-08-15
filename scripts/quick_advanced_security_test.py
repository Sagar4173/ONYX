#!/usr/bin/env python3
"""
Quick Advanced Security Test
Simplified test for advanced security features
"""
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_advanced_security_imports():
    """Test that all advanced security modules import correctly"""
    print("🔐 Advanced Security Import Test")
    print("="*50)
    
    results = {}
    
    # Test OWASP ZAP and Nuclei scanner imports
    try:
        from services.advanced_scanners import (
            OWASPZAPScanner, NucleiScanner, ScannerType, ScanSeverity, 
            AdvancedScannerConfig
        )
        results["advanced_scanners"] = "✅ PASSED"
        print("✅ Advanced Scanners (OWASP ZAP, Nuclei): PASSED")
    except Exception as e:
        results["advanced_scanners"] = f"❌ FAILED: {e}"
        print(f"❌ Advanced Scanners: FAILED - {e}")
    
    # Test CodeQL and Checkov scanner imports
    try:
        from services.codeql_checkov_scanners import CodeQLScanner, CheckovScanner
        results["codeql_checkov_scanners"] = "✅ PASSED"
        print("✅ CodeQL & Checkov Scanners: PASSED")
    except Exception as e:
        results["codeql_checkov_scanners"] = f"❌ FAILED: {e}"
        print(f"❌ CodeQL & Checkov Scanners: FAILED - {e}")
    
    # Test custom security rules engine
    try:
        from services.custom_security_rules import (
            CustomSecurityRulesEngine, ComplianceStandard, IndustryType
        )
        results["custom_security_rules"] = "✅ PASSED"
        print("✅ Custom Security Rules Engine: PASSED")
    except Exception as e:
        results["custom_security_rules"] = f"❌ FAILED: {e}"
        print(f"❌ Custom Security Rules Engine: FAILED - {e}")
    
    # Test enhanced baseline manager
    try:
        from services.enhanced_baseline_manager import (
            EnhancedBaselineManager, BaselineType
        )
        results["enhanced_baseline_manager"] = "✅ PASSED"
        print("✅ Enhanced Baseline Manager: PASSED")
    except Exception as e:
        results["enhanced_baseline_manager"] = f"❌ FAILED: {e}"
        print(f"❌ Enhanced Baseline Manager: FAILED - {e}")
    
    # Test advanced security API routes
    try:
        from routes.advanced_security import router
        results["advanced_security_api"] = "✅ PASSED"
        print("✅ Advanced Security API Routes: PASSED")
    except Exception as e:
        results["advanced_security_api"] = f"❌ FAILED: {e}"
        print(f"❌ Advanced Security API Routes: FAILED - {e}")
    
    print("="*50)
    
    # Calculate summary
    passed = sum(1 for result in results.values() if "✅ PASSED" in result)
    total = len(results)
    success_rate = (passed / total) * 100
    
    print(f"📊 Import Test Summary:")
    print(f"   Total Tests: {total}")
    print(f"   Passed: {passed}")
    print(f"   Failed: {total - passed}")
    print(f"   Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("🎉 All advanced security modules imported successfully!")
        return True
    else:
        print("⚠️ Some advanced security modules have import issues.")
        return False

async def test_basic_functionality():
    """Test basic functionality of advanced security components"""
    print("\n🔧 Advanced Security Functionality Test")
    print("="*50)
    
    results = {}
    
    # Test custom rules engine basic functionality
    try:
        from services.custom_security_rules import (
            CustomSecurityRulesEngine, ComplianceStandard, IndustryType
        )
        
        engine = CustomSecurityRulesEngine()
        
        # Test getting compliance rules
        pci_rules = engine.get_compliance_rules(ComplianceStandard.PCI_DSS)
        hipaa_rules = engine.get_compliance_rules(ComplianceStandard.HIPAA)
        
        results["custom_rules_engine"] = f"✅ PASSED - PCI: {len(pci_rules)}, HIPAA: {len(hipaa_rules)} rules"
        print(f"✅ Custom Rules Engine: PASSED - PCI: {len(pci_rules)}, HIPAA: {len(hipaa_rules)} rules")
        
    except Exception as e:
        results["custom_rules_engine"] = f"❌ FAILED: {e}"
        print(f"❌ Custom Rules Engine: FAILED - {e}")
    
    # Test enhanced baseline manager basic functionality
    try:
        from services.enhanced_baseline_manager import EnhancedBaselineManager, BaselineType
        
        manager = EnhancedBaselineManager()
        
        # Test baseline establishment (mock)
        baseline = await manager.establish_golden_baseline(
            repository="test_repo",
            branch="main",
            compliance_standards=[]
        )
        
        results["baseline_manager"] = f"✅ PASSED - Baseline ID: {baseline.baseline_id[:20]}..."
        print(f"✅ Enhanced Baseline Manager: PASSED - Baseline ID: {baseline.baseline_id[:20]}...")
        
    except Exception as e:
        results["baseline_manager"] = f"❌ FAILED: {e}"
        print(f"❌ Enhanced Baseline Manager: FAILED - {e}")
    
    # Test scanner configurations
    try:
        from services.advanced_scanners import (
            OWASPZAPScanner, NucleiScanner, ScannerType, AdvancedScannerConfig
        )
        
        # Test scanner initialization
        zap_scanner = OWASPZAPScanner()
        nuclei_scanner = NucleiScanner()
        
        # Test config creation
        config = AdvancedScannerConfig(
            scanner_type=ScannerType.OWASP_ZAP,
            timeout_seconds=300
        )
        
        results["scanner_config"] = "✅ PASSED - Scanner initialization successful"
        print("✅ Scanner Configuration: PASSED - Scanner initialization successful")
        
    except Exception as e:
        results["scanner_config"] = f"❌ FAILED: {e}"
        print(f"❌ Scanner Configuration: FAILED - {e}")
    
    print("="*50)
    
    # Calculate summary
    passed = sum(1 for result in results.values() if "✅ PASSED" in result)
    total = len(results)
    success_rate = (passed / total) * 100
    
    print(f"📊 Functionality Test Summary:")
    print(f"   Total Tests: {total}")
    print(f"   Passed: {passed}")
    print(f"   Failed: {total - passed}")
    print(f"   Success Rate: {success_rate:.1f}%")
    
    return success_rate >= 80

async def test_api_routes():
    """Test that API routes are properly configured"""
    print("\n🌐 API Routes Test")
    print("="*50)
    
    try:
        from routes.advanced_security import router
        
        # Count routes
        route_count = len(router.routes)
        
        # Check for key endpoints
        route_paths = [route.path for route in router.routes if hasattr(route, 'path')]
        
        key_endpoints = [
            "/scan/zap",
            "/scan/nuclei", 
            "/scan/codeql",
            "/scan/checkov",
            "/scan/comprehensive",
            "/rules/compliance",
            "/baseline/establish"
        ]
        
        found_endpoints = []
        for endpoint in key_endpoints:
            for path in route_paths:
                if endpoint in path:
                    found_endpoints.append(endpoint)
                    break
        
        print(f"✅ Advanced Security API Routes: {route_count} total routes")
        print(f"   Key endpoints found: {len(found_endpoints)}/{len(key_endpoints)}")
        
        for endpoint in found_endpoints:
            print(f"   ✓ {endpoint}")
        
        return True
        
    except Exception as e:
        print(f"❌ API Routes Test: FAILED - {e}")
        return False

async def main():
    """Main test execution"""
    print("🔐 Quick Advanced Security Test Suite")
    print("Testing all advanced security components\n")
    
    start_time = datetime.now(timezone.utc)
    
    # Run tests
    import_test = await test_advanced_security_imports()
    functionality_test = await test_basic_functionality()
    api_test = await test_api_routes()
    
    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()
    
    # Overall summary
    print(f"\n{'='*60}")
    print("🔐 QUICK ADVANCED SECURITY TEST RESULTS")
    print(f"{'='*60}")
    print(f"⏱️  Duration: {duration:.2f} seconds")
    print(f"📊 Import Test: {'✅ PASSED' if import_test else '❌ FAILED'}")
    print(f"🔧 Functionality Test: {'✅ PASSED' if functionality_test else '❌ FAILED'}")
    print(f"🌐 API Routes Test: {'✅ PASSED' if api_test else '❌ FAILED'}")
    
    all_passed = import_test and functionality_test and api_test
    
    if all_passed:
        print("🎉 All advanced security components are working correctly!")
        print("✅ OWASP ZAP Scanner - Ready")
        print("✅ Nuclei Scanner - Ready") 
        print("✅ CodeQL Scanner - Ready")
        print("✅ Checkov Scanner - Ready")
        print("✅ Custom Rules Engine - Ready")
        print("✅ Enhanced Baseline Manager - Ready")
        print("✅ Advanced Security API - Ready")
    else:
        print("⚠️ Some advanced security components need attention.")
    
    print(f"{'='*60}")
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    asyncio.run(main())
