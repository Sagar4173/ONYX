from typing import Any, Dict, List, Optional

from pydantic import BaseModel, HttpUrl


class ComprehensiveScanRequest(BaseModel):
    repository_url: HttpUrl
    target_url: Optional[HttpUrl] = None
    config: Optional[Dict[str, Any]] = {}


class SASTScanRequest(BaseModel):
    repository_url: HttpUrl
    languages: Optional[List[str]] = []


class DASTScanRequest(BaseModel):
    target_url: HttpUrl


class IaCScanRequest(BaseModel):
    repository_url: HttpUrl
    frameworks: Optional[List[str]] = []


class SuppressionRuleRequest(BaseModel):
    name: str
    description: str
    repository_url: HttpUrl
    rule_ids: Optional[List[str]] = []
    file_patterns: Optional[List[str]] = []
    severities: Optional[List[str]] = []
    scanners: Optional[List[str]] = []


class ScanResponse(BaseModel):
    success: bool
    scan_id: str
    report_id: str
    summary: Dict[str, Any]
    duration: Optional[float] = None
