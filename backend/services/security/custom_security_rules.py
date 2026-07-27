"""
Custom Security Rules Engine for Organization and Industry-Specific Compliance
Supports PCI-DSS, HIPAA, and custom organizational coding standards
"""
import logging
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


# Helper function for timezone-aware UTC datetime
def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

from services.rules.rule_engine import AllowedLanguage, AllowedRuleType, CustomRule, SeverityLevel
from services.rules.rule_security import SecureRuleValidator

logger = logging.getLogger(__name__)


class ComplianceStandard(str, Enum):
    """Supported compliance standards"""
    PCI_DSS = "pci_dss"
    HIPAA = "hipaa"
    SOX = "sox"
    GDPR = "gdpr"
    OWASP_TOP10 = "owasp_top10"
    CWE_TOP25 = "cwe_top25"
    NIST = "nist"
    ISO27001 = "iso27001"


class IndustryType(str, Enum):
    """Industry types for specific compliance rules"""
    FINANCIAL = "financial"
    HEALTHCARE = "healthcare"
    GOVERNMENT = "government"
    RETAIL = "retail"
    TECHNOLOGY = "technology"
    EDUCATION = "education"


class CustomRuleCategory(str, Enum):
    """Categories for custom organizational rules"""
    DATA_PROTECTION = "data_protection"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CRYPTOGRAPHY = "cryptography"
    INPUT_VALIDATION = "input_validation"
    OUTPUT_ENCODING = "output_encoding"
    ERROR_HANDLING = "error_handling"
    LOGGING_MONITORING = "logging_monitoring"
    CONFIGURATION = "configuration"
    BUSINESS_LOGIC = "business_logic"


class ComplianceRule(BaseModel):
    """Compliance-specific security rule"""
    rule_id: str
    compliance_standard: ComplianceStandard
    control_id: str  # e.g., "PCI-DSS 3.4", "HIPAA 164.312(a)(1)"
    title: str
    description: str
    requirement: str
    category: CustomRuleCategory
    industry_type: Optional[IndustryType] = None
    semgrep_rules: List[Dict[str, Any]] = Field(default_factory=list)
    codeql_queries: List[str] = Field(default_factory=list)
    custom_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    severity: SeverityLevel = SeverityLevel.MEDIUM
    languages: List[AllowedLanguage] = Field(default_factory=list)
    file_patterns: List[str] = Field(default_factory=list)
    test_cases: List[Dict[str, Any]] = Field(default_factory=list)
    remediation_guidance: str = ""
    references: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)


class OrganizationalRule(BaseModel):
    """Organization-specific coding standard rule"""
    rule_id: str
    organization: str
    title: str
    description: str
    category: CustomRuleCategory
    coding_standard: str  # Internal coding standard reference
    ast_patterns: List[Dict[str, Any]] = Field(default_factory=list)  # AST matching patterns
    framework_patterns: Dict[str, Any] = Field(default_factory=dict)  # Framework-specific patterns
    severity: SeverityLevel = SeverityLevel.MEDIUM
    languages: List[AllowedLanguage] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)  # e.g., ["spring", "django", "express"]
    file_patterns: List[str] = Field(default_factory=list)
    test_cases: List[Dict[str, Any]] = Field(default_factory=list)
    enforcement_level: str = "warning"  # "error", "warning", "info"
    remediation_guidance: str = ""
    owner_team: str = ""
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)


class CustomSecurityRulesEngine:
    """Advanced engine for custom organizational and compliance-specific rules"""
    
    def __init__(self, rules_directory: str = "configs/custom_rules"):
        self.rules_directory = Path(rules_directory)
        self.compliance_rules_dir = self.rules_directory / "compliance"
        self.organizational_rules_dir = self.rules_directory / "organizational"
        self.industry_rules_dir = self.rules_directory / "industry"
        
        # Create directories
        for directory in [self.compliance_rules_dir, self.organizational_rules_dir, self.industry_rules_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize rule validators
        self.security_validator = SecureRuleValidator()
        
        # Load built-in compliance rules
        self._initialize_compliance_rules()
        self._initialize_industry_rules()
    
    def _initialize_compliance_rules(self):
        """Initialize built-in compliance rules for major standards"""
        
        # PCI-DSS Rules
        pci_rules = [
            {
                "rule_id": "pci_dss_3_4_encrypted_transmission",
                "compliance_standard": ComplianceStandard.PCI_DSS,
                "control_id": "PCI-DSS 3.4",
                "title": "Unencrypted Transmission of Credit Card Data",
                "description": "Detects potential transmission of credit card data without encryption",
                "requirement": "Render PAN unreadable anywhere it is transmitted over open, public networks",
                "category": CustomRuleCategory.CRYPTOGRAPHY,
                "semgrep_rules": [
                    {
                        "id": "unencrypted-cc-transmission",
                        "message": "Credit card data transmitted without encryption",
                        "severity": "ERROR",
                        "languages": ["python", "java", "javascript"],
                        "patterns": [
                            {
                                "pattern-either": [
                                    {"pattern": "requests.post($URL, data={..., \"card_number\": $VAL, ...})"},
                                    {"pattern": "requests.get($URL, params={..., \"ccnum\": $VAL, ...})"},
                                    {"pattern": "http.request($METHOD, $URL, {\"credit_card\": $VAL})"}
                                ]
                            }
                        ],
                        "metadata": {
                            "cwe": "CWE-319",
                            "compliance": "PCI-DSS 3.4"
                        }
                    }
                ],
                "severity": SeverityLevel.CRITICAL,
                "languages": [AllowedLanguage.PYTHON, AllowedLanguage.JAVA, AllowedLanguage.JAVASCRIPT],
                "file_patterns": ["**/*.py", "**/*.java", "**/*.js"],
                "test_cases": [
                    {
                        "name": "unencrypted_cc_post",
                        "content": "requests.post('http://api.example.com', data={'card_number': '4111111111111111'})",
                        "expected_matches": 1
                    }
                ],
                "remediation_guidance": "Use HTTPS for all credit card data transmission and consider tokenization",
                "references": ["https://www.pcisecuritystandards.org/document_library"]
            },
            {
                "rule_id": "pci_dss_3_2_stored_cc_data",
                "compliance_standard": ComplianceStandard.PCI_DSS,
                "control_id": "PCI-DSS 3.2",
                "title": "Stored Credit Card Data",
                "description": "Detects storage of prohibited credit card data elements",
                "requirement": "Do not store sensitive authentication data after authorization",
                "category": CustomRuleCategory.DATA_PROTECTION,
                "semgrep_rules": [
                    {
                        "id": "stored-cc-data",
                        "message": "Prohibited credit card data storage detected",
                        "severity": "ERROR",
                        "languages": ["python", "java", "javascript"],
                        "patterns": [
                            {
                                "pattern-either": [
                                    {"pattern": "$DB.save({..., \"cvv\": $VAL, ...})"},
                                    {"pattern": "$DB.insert({..., \"cvc\": $VAL, ...})"},
                                    {"pattern": "store($DICT) where $DICT contains \"track_data\""}
                                ]
                            }
                        ],
                        "metadata": {
                            "cwe": "CWE-200",
                            "compliance": "PCI-DSS 3.2"
                        }
                    }
                ],
                "severity": SeverityLevel.CRITICAL,
                "languages": [AllowedLanguage.PYTHON, AllowedLanguage.JAVA, AllowedLanguage.JAVASCRIPT],
                "file_patterns": ["**/*.py", "**/*.java", "**/*.js"],
                "test_cases": [
                    {
                        "name": "stored_cvv",
                        "content": "database.save({'user_id': 123, 'cvv': '123'})",
                        "expected_matches": 1
                    }
                ]
            }
        ]
        
        # HIPAA Rules
        hipaa_rules = [
            {
                "rule_id": "hipaa_164_312_a_1_access_control",
                "compliance_standard": ComplianceStandard.HIPAA,
                "control_id": "HIPAA 164.312(a)(1)",
                "title": "Insufficient Access Control for PHI",
                "description": "Detects potential unauthorized access to Protected Health Information",
                "requirement": "Implement technical safeguards to allow access to ePHI only to authorized persons",
                "category": CustomRuleCategory.AUTHORIZATION,
                "industry_type": IndustryType.HEALTHCARE,
                "semgrep_rules": [
                    {
                        "id": "hipaa-phi-access",
                        "message": "Potential unauthorized PHI access detected",
                        "severity": "ERROR",
                        "languages": ["python", "java"],
                        "patterns": [
                            {
                                "pattern-either": [
                                    {"pattern": "get_patient_data($ID) without authentication"},
                                    {"pattern": "$DB.query(\"SELECT * FROM patients\") without authorization"},
                                    {"pattern": "phi_data = $FUNC() if not check_access()"}
                                ]
                            }
                        ],
                        "metadata": {
                            "cwe": "CWE-862",
                            "compliance": "HIPAA 164.312(a)(1)"
                        }
                    }
                ],
                "severity": SeverityLevel.HIGH,
                "languages": [AllowedLanguage.PYTHON, AllowedLanguage.JAVA],
                "file_patterns": ["**/*.py", "**/*.java"],
                "test_cases": [
                    {
                        "name": "unauthorized_phi_access",
                        "content": "patient_data = database.query('SELECT * FROM patients WHERE id = ?', patient_id)",
                        "expected_matches": 1
                    }
                ]
            }
        ]
        
        # Save rules to files
        self._save_compliance_rules(ComplianceStandard.PCI_DSS, pci_rules)
        self._save_compliance_rules(ComplianceStandard.HIPAA, hipaa_rules)
    
    def _initialize_industry_rules(self):
        """Initialize industry-specific rule templates"""
        
        # Financial industry rules
        financial_rules = [
            {
                "rule_id": "financial_api_rate_limiting",
                "title": "Missing Rate Limiting on Financial APIs",
                "description": "Financial APIs should implement strict rate limiting",
                "category": CustomRuleCategory.CONFIGURATION,
                "industry_type": IndustryType.FINANCIAL,
                "semgrep_rules": [
                    {
                        "id": "missing-financial-rate-limit",
                        "message": "Financial API endpoint missing rate limiting",
                        "severity": "WARNING",
                        "languages": ["python", "javascript"],
                        "patterns": [
                            {
                                "pattern": "@app.route(\"/api/transfer\", methods=[\"POST\"]) def $FUNC($ARGS): ..."
                            }
                        ]
                    }
                ],
                "severity": SeverityLevel.MEDIUM,
                "frameworks": ["flask", "express", "spring"],
                "remediation_guidance": "Implement rate limiting using middleware or decorators"
            }
        ]
        
        # Healthcare industry rules  
        healthcare_rules = [
            {
                "rule_id": "healthcare_audit_logging",
                "title": "Missing Audit Logging for PHI Access",
                "description": "All PHI access must be logged for compliance",
                "category": CustomRuleCategory.LOGGING_MONITORING,
                "industry_type": IndustryType.HEALTHCARE,
                "semgrep_rules": [
                    {
                        "id": "missing-phi-audit-log",
                        "message": "PHI access without audit logging",
                        "severity": "ERROR",
                        "languages": ["python", "java"],
                        "patterns": [
                            {
                                "pattern": "get_patient_record($ID) without logging"
                            }
                        ]
                    }
                ],
                "severity": SeverityLevel.HIGH,
                "remediation_guidance": "Add audit logging for all PHI access operations"
            }
        ]
        
        # Save industry rules
        self._save_industry_rules(IndustryType.FINANCIAL, financial_rules)
        self._save_industry_rules(IndustryType.HEALTHCARE, healthcare_rules)
    
    async def create_organizational_rule(self, org_rule: OrganizationalRule) -> bool:
        """Create a new organizational coding standard rule"""
        try:
            # Validate rule security
            custom_rule = self._convert_to_custom_rule(org_rule)
            validation_result = await self.security_validator.validate_rule_metadata(custom_rule.dict())
            
            if not validation_result[0]:  # is_valid
                logger.error(f"Organizational rule validation failed: {validation_result[1]}")
                return False
            
            # Save rule
            rule_file = self.organizational_rules_dir / f"{org_rule.rule_id}.yaml"
            with open(rule_file, 'w') as f:
                yaml.safe_dump(org_rule.dict(), f)
            
            logger.info(f"Created organizational rule: {org_rule.rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create organizational rule: {e}")
            return False
    
    def get_compliance_rules(self, standard: ComplianceStandard, industry: Optional[IndustryType] = None) -> List[ComplianceRule]:
        """Get compliance rules for a specific standard"""
        rules = []
        
        try:
            rules_file = self.compliance_rules_dir / f"{standard.value}.yaml"
            if rules_file.exists():
                with open(rules_file, 'r') as f:
                    rules_data = yaml.safe_load(f)
                    for rule_data in rules_data:
                        rule = ComplianceRule(**rule_data)
                        if not industry or rule.industry_type == industry:
                            rules.append(rule)
        except Exception as e:
            logger.error(f"Failed to load compliance rules for {standard}: {e}")
        
        return rules
    
    def get_industry_rules(self, industry: IndustryType) -> List[OrganizationalRule]:
        """Get industry-specific rules"""
        rules = []
        
        try:
            rules_file = self.industry_rules_dir / f"{industry.value}.yaml"
            if rules_file.exists():
                with open(rules_file, 'r') as f:
                    rules_data = yaml.safe_load(f)
                    for rule_data in rules_data:
                        rules.append(OrganizationalRule(**rule_data))
        except Exception as e:
            logger.error(f"Failed to load industry rules for {industry}: {e}")
        
        return rules
    
    def get_organizational_rules(self, organization: str) -> List[OrganizationalRule]:
        """Get all organizational rules for a specific organization"""
        rules = []
        
        try:
            for rule_file in self.organizational_rules_dir.glob("*.yaml"):
                with open(rule_file, 'r') as f:
                    rule_data = yaml.safe_load(f)
                    rule = OrganizationalRule(**rule_data)
                    if rule.organization == organization:
                        rules.append(rule)
        except Exception as e:
            logger.error(f"Failed to load organizational rules: {e}")
        
        return rules
    
    async def generate_ast_pattern(self, language: AllowedLanguage, pattern_description: str) -> Dict[str, Any]:
        """Generate AST matching pattern for custom framework detection"""
        # This would integrate with tree-sitter or similar AST parsing
        # For now, return a template pattern
        
        ast_patterns = {
            AllowedLanguage.PYTHON: {
                "unsafe_deserialization": {
                    "pattern": "ast.Call",
                    "func": {"id": "pickle.loads"},
                    "args": ["$USER_INPUT"]
                },
                "sql_injection": {
                    "pattern": "ast.Call", 
                    "func": {"attr": "execute"},
                    "args": [{"binop": "+", "left": "$QUERY", "right": "$USER_INPUT"}]
                }
            },
            AllowedLanguage.JAVA: {
                "unsafe_reflection": {
                    "pattern": "MethodInvocation",
                    "name": "forName",
                    "arguments": ["$USER_INPUT"]
                }
            }
        }
        
        return ast_patterns.get(language, {}).get(pattern_description, {})
    
    def _convert_to_custom_rule(self, org_rule: OrganizationalRule) -> CustomRule:
        """Convert organizational rule to CustomRule for validation"""
        return CustomRule(
            id=org_rule.rule_id,
            name=org_rule.title,
            description=org_rule.description,
            message=org_rule.title,  # Required field
            type=AllowedRuleType.SEMGREP,  # Default type
            severity=org_rule.severity,
            languages=org_rule.languages or [AllowedLanguage.PYTHON],
            author=org_rule.owner_team,
            category=org_rule.category.value,
            file_patterns=org_rule.file_patterns or ["**/*"],
            test_cases=org_rule.test_cases or [{"name": "default", "content": "test", "expected_matches": 0}]
        )
    
    def _save_compliance_rules(self, standard: ComplianceStandard, rules: List[Dict]):
        """Save compliance rules to file"""
        try:
            rules_file = self.compliance_rules_dir / f"{standard.value}.yaml"
            
            # Convert enum values to strings for YAML serialization
            serializable_rules = []
            for rule in rules:
                serializable_rule = rule.copy()
                # Convert any enum values to strings
                if 'category' in serializable_rule and hasattr(serializable_rule['category'], 'value'):
                    serializable_rule['category'] = serializable_rule['category'].value
                if 'severity' in serializable_rule and hasattr(serializable_rule['severity'], 'value'):
                    serializable_rule['severity'] = serializable_rule['severity'].value
                serializable_rules.append(serializable_rule)
            
            with open(rules_file, 'w') as f:
                yaml.safe_dump(serializable_rules, f, default_flow_style=False)
                
            logger.info(f"Saved {len(rules)} {standard.value} rules")
            
        except Exception as e:
            logger.error(f"Failed to save compliance rules: {e}")
            # Continue without saving - rules are still in memory
    
    def _save_industry_rules(self, industry: IndustryType, rules: List[Dict]):
        """Save industry rules to file"""
        try:
            rules_file = self.industry_rules_dir / f"{industry.value}.yaml"
            
            # Convert enum values to strings for YAML serialization
            serializable_rules = []
            for rule in rules:
                serializable_rule = rule.copy()
                # Convert any enum values to strings
                if 'category' in serializable_rule and hasattr(serializable_rule['category'], 'value'):
                    serializable_rule['category'] = serializable_rule['category'].value
                if 'severity' in serializable_rule and hasattr(serializable_rule['severity'], 'value'):
                    serializable_rule['severity'] = serializable_rule['severity'].value
                serializable_rules.append(serializable_rule)
            
            with open(rules_file, 'w') as f:
                yaml.safe_dump(serializable_rules, f, default_flow_style=False)
                
            logger.info(f"Saved {len(rules)} {industry.value} industry rules")
            
        except Exception as e:
            logger.error(f"Failed to save industry rules: {e}")
            # Continue without saving - rules are still in memory


# Export main classes
__all__ = [
    'ComplianceStandard', 'IndustryType', 'CustomRuleCategory',
    'ComplianceRule', 'OrganizationalRule', 'CustomSecurityRulesEngine'
]
