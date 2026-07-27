from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class RuleCreateRequest(BaseModel):
    rule_data: Dict[str, Any]
    validate_rule: bool = True
    test_repo_path: Optional[str] = None


class RuleFromTemplateRequest(BaseModel):
    template_id: str
    rule_id: str
    variables: Dict[str, Any]


class BaselineCreateRequest(BaseModel):
    scan_report_id: str
    repository_url: str
    branch: str
    commit_hash: str
    tags: Optional[List[str]] = None
