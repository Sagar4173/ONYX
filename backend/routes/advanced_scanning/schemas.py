from typing import Annotated, Any, Dict, List, Optional

from pydantic import AfterValidator, BaseModel, HttpUrl

from utils.url_redaction import has_embedded_credentials


def _reject_embedded_credentials(value: HttpUrl) -> HttpUrl:
    if has_embedded_credentials(str(value)):
        raise ValueError(
            "Repository URL must not embed credentials; use access_token instead"
        )
    return value


RepositoryUrl = Annotated[HttpUrl, AfterValidator(_reject_embedded_credentials)]


class ComprehensiveScanRequest(BaseModel):
    repository_url: RepositoryUrl
    target_url: Optional[HttpUrl] = None
    config: Optional[Dict[str, Any]] = {}


class SASTScanRequest(BaseModel):
    repository_url: RepositoryUrl
    languages: Optional[List[str]] = []


class DASTScanRequest(BaseModel):
    target_url: HttpUrl


class IaCScanRequest(BaseModel):
    repository_url: RepositoryUrl
    frameworks: Optional[List[str]] = []


class SuppressionRuleRequest(BaseModel):
    name: str
    description: str
    repository_url: RepositoryUrl
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
