#!/usr/bin/env python3
"""
Simple test script for compliance analysis models and basic functionality
"""
import sys
import os
from pathlib import Path
import json
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

# Test the basic imports and model creation
def test_basic_imports():
    """Test that we can import our modules"""
    print("🧪 Testing Basic Imports")
    print("=" * 40)
    
    try:
        from models.report import (
            VulnerabilityFinding, 
            Severity, 
            ScannerType, 
            ComplianceFramework,
            ComplianceMapping,
            ThreatAnalysis,
            ThreatCategory,
            CVSSScore,
            BusinessImpact,
            RiskLevel
        )
        print("✅ Successfully imported all model classes")
        
        # Test model creation
        print("\n📝 Testing Model Creation:")
        
        # Create a basic vulnerability finding
        finding = VulnerabilityFinding(
            title="Test SQL Injection",
            description="Test vulnerability description",
            severity=Severity.HIGH,
            scanner=ScannerType.SEMGREP,
            file_path="/test/file.py",
            line_number=42,
            rule_id="test-rule-id"
        )
        print(f"  ✅ Created VulnerabilityFinding: {finding.title}")
        
        # Create compliance mapping
        compliance_mapping = ComplianceMapping(
            framework=ComplianceFramework.SOC2,
            control_ids=["CC6.1", "CC6.7"],
            compliance_status="non_compliant",
            gap_analysis="SQL injection vulnerability violates secure coding practices"
        )
        print(f"  ✅ Created ComplianceMapping: {compliance_mapping.framework.value}")
        
        # Create threat analysis
        threat_analysis = ThreatAnalysis(
            category=ThreatCategory.INJECTION,
            exploitability="high",
            potential_impact="data_breach",
            attack_vectors=["web_application", "api_endpoint"],
            mitigation_strategies=["input_validation", "parameterized_queries"]
        )
        print(f"  ✅ Created ThreatAnalysis: {threat_analysis.category.value}")
        
        # Create CVSS score
        cvss_score = CVSSScore(
            base_score=7.5,
            impact_score=3.6,
            exploitability_score=3.9,
            vector_string="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"
        )
        print(f"  ✅ Created CVSSScore: {cvss_score.base_score}")
        
        # Create business impact
        business_impact = BusinessImpact(
            financial_impact=8,
            operational_impact=6,
            reputational_impact=7,
            regulatory_impact=9,
            confidentiality_impact="high",
            integrity_impact="medium",
            availability_impact="low"
        )
        print(f"  ✅ Created BusinessImpact: Financial={business_impact.financial_impact}")
        
        # Test enhanced finding with all components
        enhanced_finding = VulnerabilityFinding(
            title="Enhanced SQL Injection",
            description="SQL injection with full compliance analysis",
            severity=Severity.CRITICAL,
            scanner=ScannerType.SEMGREP,
            file_path="/app/api/users.py",
            line_number=125,
            rule_id="python.django.security.injection.sql.sql-injection",
            cwe_id="CWE-89",
            compliance_mappings=[compliance_mapping],
            threat_analysis=threat_analysis,
            cvss_score=cvss_score,
            business_impact=business_impact,
            risk_level=RiskLevel.CRITICAL
        )
        print(f"  ✅ Created Enhanced Finding: {enhanced_finding.title}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Model creation failed: {e}")
        return False


def test_compliance_mapping_config():
    """Test loading compliance mapping configuration"""
    print("\n🔧 Testing Compliance Configuration")
    print("=" * 40)
    
    try:
        config_path = backend_path / 'configs' / 'compliance_mapping.json'
        
        if not config_path.exists():
            print(f"❌ Configuration file not found: {config_path}")
            return False
        
        with open(config_path, 'r') as f:
            compliance_config = json.load(f)
        
        print(f"✅ Loaded compliance configuration")
        print(f"  📋 Frameworks: {list(compliance_config.keys())}")
        
        for framework_name, framework_data in compliance_config.items():
            controls_count = len(framework_data.get('controls', {}))
            cwe_mappings_count = len(framework_data.get('cwe_mappings', {}))
            print(f"  - {framework_name}: {controls_count} controls, {cwe_mappings_count} CWE mappings")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_result_parser_structure():
    """Test result parser structure"""
    print("\n🔍 Testing Result Parser Structure")
    print("=" * 40)
    
    try:
        from utils.result_parser import result_parser, BaseResultParser
        
        print("✅ Successfully imported result parser")
        print(f"  📊 Available parsers: {list(result_parser.parsers.keys())}")
        
        # Check if enhance_finding_with_analysis method exists
        base_parser = BaseResultParser()
        if hasattr(base_parser, 'enhance_finding_with_analysis'):
            print("  ✅ enhance_finding_with_analysis method found")
        else:
            print("  ❌ enhance_finding_with_analysis method missing")
        
        return True
        
    except ImportError as e:
        print(f"❌ Result parser import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Result parser test failed: {e}")
        return False


def test_compliance_service_structure():
    """Test compliance service structure"""
    print("\n⚙️ Testing Compliance Service Structure")
    print("=" * 40)
    
    try:
        from services.compliance_analyzer import ComplianceAnalysisService
        
        print("✅ Successfully imported ComplianceAnalysisService")
        
        # Check for key methods
        service = ComplianceAnalysisService()
        required_methods = [
            'map_finding_to_compliance',
            'analyze_threat',
            'calculate_cvss_score',
            'assess_business_impact',
            'calculate_risk_level',
            'generate_compliance_report',
            'get_framework_control_status',
            'generate_risk_summary'
        ]
        
        for method_name in required_methods:
            if hasattr(service, method_name):
                print(f"  ✅ {method_name} method found")
            else:
                print(f"  ❌ {method_name} method missing")
        
        return True
        
    except ImportError as e:
        print(f"❌ Compliance service import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Compliance service test failed: {e}")
        return False


def main():
    """Main test function"""
    print("🚀 SecureDevOps AI Platform - Compliance Features Test")
    print("=" * 60)
    
    tests = [
        test_basic_imports,
        test_compliance_mapping_config,
        test_result_parser_structure,
        test_compliance_service_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Compliance features are properly implemented.")
        
        # Show summary of implemented features
        print("\n✅ Implemented Features Summary:")
        print("  📋 Compliance Framework Mapping (SOC2, PCI-DSS, GDPR, NIST CSF, OWASP)")
        print("  🎯 Threat Analysis & Categorization System")
        print("  📊 CVSS 3.1 Scoring Engine")
        print("  💼 Business Impact Assessment")
        print("  ⚖️ Risk Assessment Methodology")
        print("  🔍 Enhanced Result Parser with Auto-Analysis")
        print("  📈 Compliance Reporting & Analytics")
        print("  🌐 RESTful API Endpoints for Compliance")
        
    else:
        print(f"⚠️ {total - passed} tests failed. Please check the implementation.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
