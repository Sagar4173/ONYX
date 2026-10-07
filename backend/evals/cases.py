"""Golden eval cases: hand-verified expected deterministic AI outputs.

Expected values computed with the exact formulas in
services.ai.ai_processor (risk/security scores, fix-time formatting,
roadmap phases, threat-categorization keyword rules).
Finding titles are chosen per severity so threat categories are
deterministic; descriptions are keyword-neutral on purpose.
"""
from typing import Any, Dict, List

SEVERITY_TITLES = {
    "critical": "SQL Injection in login query",          # -> Injection
    "high": "Weak password hashing algorithm used",      # -> Authentication
    "medium": "Insecure default configuration setting",  # -> Security Misconfiguration
    "low": "Unused import in helper module",             # -> Other
    "info": "Missing HTTP security header",              # -> Other
}
NEUTRAL_DESCRIPTION = "Detected by automated scanner."
SEVERITIES = ("critical", "high", "medium", "low", "info")


def _e(risk_score, risk_level, security_score, estimated_fix_time, roadmap_phases, threat_categories):
    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "security_score": security_score,
        "estimated_fix_time": estimated_fix_time,
        "roadmap_phases": roadmap_phases,
        "threat_categories": threat_categories,
    }


CASES: List[Dict[str, Any]] = [
    # name, severity counts, expected deterministic outputs
    {"name": "clean", "counts": {}, "expected": _e(5, "LOW", 98, "0 hours - No issues to fix", [], {})},
    {"name": "crit-1", "counts": {"critical": 1}, "expected": _e(40, "CRITICAL", 80, "1.0 days (8 hours)", [1], {"Injection": 1})},
    {"name": "crit-3", "counts": {"critical": 3}, "expected": _e(100, "CRITICAL", 40, "3.0 days (24 hours)", [1], {"Injection": 3})},
    {"name": "high-1", "counts": {"high": 1}, "expected": _e(25, "HIGH", 88, "4 hours", [2], {"Authentication": 1})},
    {"name": "high-4", "counts": {"high": 4}, "expected": _e(100, "CRITICAL", 52, "2.0 days (16 hours)", [2], {"Authentication": 4})},
    {"name": "medium-1", "counts": {"medium": 1}, "expected": _e(10, "MEDIUM", 95, "2 hours", [3], {"Security Misconfiguration": 1})},
    {"name": "medium-6", "counts": {"medium": 6}, "expected": _e(60, "HIGH", 70, "1.5 days (12 hours)", [3], {"Security Misconfiguration": 6})},
    {"name": "medium-7", "counts": {"medium": 7}, "expected": _e(70, "CRITICAL", 65, "1.8 days (14 hours)", [3], {"Security Misconfiguration": 7})},
    {"name": "medium-10", "counts": {"medium": 10}, "expected": _e(100, "CRITICAL", 50, "2.5 days (20 hours)", [3], {"Security Misconfiguration": 10})},
    {"name": "low-5", "counts": {"low": 5}, "expected": _e(15, "LOW", 90, "5 hours", [4], {"Other": 5})},
    {"name": "low-12", "counts": {"low": 12}, "expected": _e(36, "MEDIUM", 76, "1.5 days (12 hours)", [4], {"Other": 12})},
    {"name": "info-20", "counts": {"info": 20}, "expected": _e(20, "MEDIUM", 90, "0 hours - No issues to fix", [4], {"Other": 20})},
    {"name": "crit-high", "counts": {"critical": 1, "high": 1}, "expected": _e(65, "CRITICAL", 68, "1.5 days (12 hours)", [1, 2], {"Injection": 1, "Authentication": 1})},
    {"name": "crit-high-med-low-info", "counts": {"critical": 1, "high": 1, "medium": 1, "low": 1, "info": 1}, "expected": _e(79, "CRITICAL", 60, "1.9 days (15 hours)", [1, 2, 3, 4], {"Injection": 1, "Authentication": 1, "Security Misconfiguration": 1, "Other": 2})},
    {"name": "mixed-4", "counts": {"critical": 2, "high": 1, "medium": 1}, "expected": _e(100, "CRITICAL", 43, "2.8 days (22 hours)", [1, 2, 3], {"Injection": 2, "Authentication": 1, "Security Misconfiguration": 1})},
    {"name": "low-flood-100", "counts": {"low": 100}, "expected": _e(100, "CRITICAL", 0, "2.5 weeks (100 hours)", [4], {"Other": 100})},
    {"name": "info-flood-60", "counts": {"info": 60}, "expected": _e(60, "HIGH", 70, "0 hours - No issues to fix", [4], {"Other": 60})},
    {"name": "crit-2-high-1", "counts": {"critical": 2, "high": 1}, "expected": _e(100, "CRITICAL", 48, "2.5 days (20 hours)", [1, 2], {"Injection": 2, "Authentication": 1})},
    {"name": "high-2-medium-3", "counts": {"high": 2, "medium": 3}, "expected": _e(80, "CRITICAL", 61, "1.8 days (14 hours)", [2, 3], {"Authentication": 2, "Security Misconfiguration": 3})},
    {"name": "medium-2-low-4-info-2", "counts": {"medium": 2, "low": 4, "info": 2}, "expected": _e(34, "MEDIUM", 81, "1.0 days (8 hours)", [3, 4], {"Security Misconfiguration": 2, "Other": 6})},
    {"name": "low-8-info-5", "counts": {"low": 8, "info": 5}, "expected": _e(29, "MEDIUM", 81, "1.0 days (8 hours)", [4], {"Other": 13})},
    {"name": "crit-1-low-1", "counts": {"critical": 1, "low": 1}, "expected": _e(43, "CRITICAL", 78, "1.1 days (9 hours)", [1, 4], {"Injection": 1, "Other": 1})},
    {"name": "mixed-7", "counts": {"critical": 1, "medium": 1, "info": 1}, "expected": _e(51, "CRITICAL", 74, "1.2 days (10 hours)", [1, 3, 4], {"Injection": 1, "Security Misconfiguration": 1, "Other": 1})},
    {"name": "high-1-low-1", "counts": {"high": 1, "low": 1}, "expected": _e(28, "HIGH", 86, "5 hours", [2, 4], {"Authentication": 1, "Other": 1})},
]
