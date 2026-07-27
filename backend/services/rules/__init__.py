"""
Rules & Policy Engine Services
"""
from .policy_as_code_engine import PolicyAsCodeEngine
from .policy_engine import (
    PolicyAsCodeService,
    PolicyCondition,
    PolicyEvaluationResult,
    PolicyRule,
    PolicyViolation,
    SecurityPolicy,
)
from .rule_engine import (
    AllowedLanguage,
    AllowedRuleType,
    CustomRule,
    CustomRuleEngine,
    RuleSeverity,
    RuleStatus,
    RuleTemplate,
    RuleType,
    RuleValidationResult,
    SeverityLevel,
)
from .rule_parsing_engine import RuleParsingEngine
from .rule_security import *
from .rule_testing_framework import RuleTestingFramework

# Aliases for backward compatibility
RuleEngine = CustomRuleEngine
SecurityRule = CustomRule
RuleMatch = RuleValidationResult
PolicyEngine = PolicyAsCodeService

__all__ = [
    "RuleEngine",
    "CustomRuleEngine",
    "SecurityRule",
    "CustomRule",
    "RuleType",
    "RuleSeverity",
    "AllowedRuleType",
    "SeverityLevel",
    "AllowedLanguage",
    "RuleMatch",
    "RuleValidationResult",
    "RuleTemplate",
    "RuleStatus",
    "RuleParsingEngine",
    "RuleTestingFramework",
    "PolicyEngine",
    "PolicyAsCodeService",
    "SecurityPolicy",
    "PolicyViolation",
    "PolicyEvaluationResult",
    "PolicyRule",
    "PolicyCondition",
    "PolicyAsCodeEngine",
]
