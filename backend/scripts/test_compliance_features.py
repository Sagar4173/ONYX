#!/usr/bin/env python3
"""
Test script for enhanced security scanners with compliance analysis
"""
import asyncio
import sys
import os
from pathlib import Path
import logging
import json
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from models.report import VulnerabilityFinding, Severity, ScannerType, ComplianceFramework
from services.compliance_analyzer import ComplianceAnalysisService
from utils.result_parser import result_parser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_compliance_analysis():
    """Test compliance analysis features"""
    
    print("🧪 Testing Enhanced Security Scanner Compliance Analysis")
    print("=" * 60)
    
    # Initialize compliance service
    compliance_service = ComplianceAnalysisService()
    
    # Create test findings
    test_findings = [
        VulnerabilityFinding(
            title="SQL Injection Vulnerability",
            description="User input is not properly sanitized",
            severity=Severity.HIGH,
            scanner=ScannerType.SEMGREP,
            file_path="/app/models/user.py",
            line_number=45,
            rule_id="python.django.security.injection.sql.sql-injection",
            cwe_id="CWE-89"
        ),
        VulnerabilityFinding(
            title="Hardcoded Secret",
            description="API key found in source code",
            severity=Severity.CRITICAL,
            scanner=ScannerType.GITLEAKS,
            file_path="/app/config.py",
            line_number=12,
            rule_id="generic-api-key",
            cwe_id="CWE-798"
        ),
        VulnerabilityFinding(
            title="Insecure Random Number Generation",
            description="Using weak random number generator",
            severity=Severity.MEDIUM,
            scanner=ScannerType.BANDIT,
            file_path="/app/auth/tokens.py",
            line_number=23,
            rule_id="B311",
            cwe_id="CWE-330"
        )
    ]
    
    print(f"📊 Created {len(test_findings)} test findings")
    
    # Test compliance mapping for each finding
    print("\n🔍 Testing Compliance Mapping:")
    for i, finding in enumerate(test_findings, 1):
        print(f"\n  {i}. {finding.title}")
        
        # Map to compliance frameworks
        compliance_mappings = await compliance_service.map_finding_to_compliance(finding)
        finding.compliance_mappings = compliance_mappings
        
        for mapping in compliance_mappings:
            print(f"     📋 {mapping.framework.value}: {', '.join(mapping.control_ids)}")
    
    # Test threat analysis
    print("\n🎯 Testing Threat Analysis:")
    for i, finding in enumerate(test_findings, 1):
        print(f"\n  {i}. {finding.title}")
        
        # Analyze threat
        threat_analysis = await compliance_service.analyze_threat(finding)
        finding.threat_analysis = threat_analysis
        
        print(f"     🏷️ Category: {threat_analysis.category.value}")
        print(f"     ⚡ Exploitability: {threat_analysis.exploitability}")
        print(f"     💥 Potential Impact: {threat_analysis.potential_impact}")
    
    # Test CVSS scoring
    print("\n📊 Testing CVSS Scoring:")
    for i, finding in enumerate(test_findings, 1):
        print(f"\n  {i}. {finding.title}")
        
        # Calculate CVSS score
        cvss_score = await compliance_service.calculate_cvss_score(finding)
        finding.cvss_score = cvss_score
        
        print(f"     🎯 Base Score: {cvss_score.base_score}")
        print(f"     🌍 Environmental Score: {cvss_score.environmental_score}")
        print(f"     ⏰ Temporal Score: {cvss_score.temporal_score}")
    
    # Test risk assessment
    print("\n⚖️ Testing Risk Assessment:")
    for i, finding in enumerate(test_findings, 1):
        print(f"\n  {i}. {finding.title}")
        
        # Assess business impact
        business_impact = await compliance_service.assess_business_impact(finding)
        finding.business_impact = business_impact
        
        # Calculate overall risk
        risk_level = await compliance_service.calculate_risk_level(
            finding, 
            repository_context={'environment': 'production'},
            business_context={'data_classification': 'high', 'compliance_requirements': ['SOC2', 'GDPR']}
        )
        finding.risk_level = risk_level
        
        print(f"     💼 Business Impact: Financial={business_impact.financial_impact}, Operational={business_impact.operational_impact}")
        print(f"     🚨 Risk Level: {risk_level.value}")
    
    # Test compliance report generation
    print("\n📈 Testing Compliance Report Generation:")
    
    for framework in [ComplianceFramework.SOC2, ComplianceFramework.PCI_DSS, ComplianceFramework.GDPR]:
        print(f"\n  📋 {framework.value} Report:")
        
        report = await compliance_service.generate_compliance_report(test_findings, framework)
        
        print(f"     📊 Total Findings: {report['total_findings']}")
        print(f"     🎯 Mapped Findings: {report['mapped_findings']}")
        print(f"     ✅ Compliance Score: {report['compliance_score']}%")
        print(f"     🔍 Controls Analyzed: {len(report['control_coverage'])}")
        print(f"     💡 Recommendations: {len(report['recommendations'])}")
    
    # Test risk summary
    print("\n📋 Testing Risk Summary:")
    risk_summary = await compliance_service.generate_risk_summary(test_findings)
    
    print(f"  📊 Total Findings: {risk_summary['total_findings']}")
    print(f"  🎯 By Severity: {risk_summary['by_severity']}")
    print(f"  ⚖️ By Risk Level: {risk_summary['by_risk_level']}")
    print(f"  🏷️ By Threat Category: {risk_summary['by_threat_category']}")
    print(f"  🌍 Framework Coverage: {risk_summary['framework_coverage']}")
    
    print("\n✅ Compliance Analysis Testing Complete!")
    print("=" * 60)
    
    return test_findings


async def test_enhanced_result_parser():
    """Test enhanced result parser with compliance integration"""
    
    print("\n🔧 Testing Enhanced Result Parser")
    print("=" * 60)
    
    # Mock scanner output (Semgrep format)
    mock_semgrep_output = json.dumps({
        "results": [
            {
                "check_id": "python.django.security.injection.sql.sql-injection",
                "path": "/app/models/user.py",
                "start": {"line": 45, "col": 12},
                "end": {"line": 45, "col": 45},
                "message": "User input is not properly sanitized before SQL query",
                "severity": "ERROR",
                "metadata": {
                    "cwe": ["CWE-89"],
                    "owasp": ["A03:2021 – Injection"]
                }
            }
        ]
    })
    
    # Test parsing with compliance enhancement
    repository_context = {
        'path': '/test/repo',
        'scanner_type': 'semgrep',
        'scan_timestamp': datetime.now().isoformat()
    }
    
    business_context = {
        'environment': 'production',
        'data_classification': 'high',
        'compliance_requirements': ['SOC2', 'GDPR', 'PCI_DSS']
    }
    
    print("🔍 Parsing Semgrep results with compliance enhancement...")
    
    enhanced_findings = result_parser.parse_results(
        ScannerType.SEMGREP,
        mock_semgrep_output,
        repository_context=repository_context,
        business_context=business_context
    )
    
    print(f"📊 Enhanced {len(enhanced_findings)} findings")
    
    for i, finding in enumerate(enhanced_findings, 1):
        print(f"\n  {i}. {finding.title}")
        print(f"     🎯 Severity: {finding.severity.value}")
        
        if finding.compliance_mappings:
            print(f"     📋 Compliance Mappings:")
            for mapping in finding.compliance_mappings:
                print(f"        - {mapping.framework.value}: {', '.join(mapping.control_ids)}")
        
        if finding.threat_analysis:
            print(f"     🎯 Threat Category: {finding.threat_analysis.category.value}")
            print(f"     ⚡ Exploitability: {finding.threat_analysis.exploitability}")
        
        if finding.cvss_score:
            print(f"     📊 CVSS Base Score: {finding.cvss_score.base_score}")
        
        if finding.risk_level:
            print(f"     🚨 Risk Level: {finding.risk_level.value}")
        
        if finding.business_impact:
            print(f"     💼 Business Impact: Financial={finding.business_impact.financial_impact}")
    
    print("\n✅ Enhanced Result Parser Testing Complete!")
    print("=" * 60)


async def main():
    """Main test function"""
    try:
        # Test compliance analysis
        test_findings = await test_compliance_analysis()
        
        # Test enhanced result parser
        await test_enhanced_result_parser()
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
