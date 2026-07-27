from typing import Any, Dict, List

from pydantic import BaseModel


class ThreatScanRequest(BaseModel):
    repository_path: str
    scan_types: List[str] = ["cve", "secrets", "malware"]
    severity_threshold: str = "medium"


class PolicyEvaluationRequest(BaseModel):
    repository: str
    commit_hash: str
    policies: List[str] = []


class VulnerabilityScanRequest(BaseModel):
    config: Dict[str, Any] = {}


class PentestRequest(BaseModel):
    config: Dict[str, Any] = {}


class RuleParseRequest(BaseModel):
    rules: List[Dict[str, Any]] = []


class PolicyEnforceRequest(BaseModel):
    policy: Dict[str, Any] = {}


class SecurityBoundaryTestRequest(BaseModel):
    rule_id: str
    test_input: str
    boundary_type: str = "resource"


class AdvancedScanRequest(BaseModel):
    config: Dict[str, Any] = {}
