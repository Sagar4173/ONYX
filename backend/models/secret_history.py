from datetime import datetime, timezone
from typing import List, Optional

from beanie import Document
from pydantic import ConfigDict, Field


class SecretRecord(Document):
    secret_hash: str = Field(..., description="Hashed secret fingerprint from detect-secrets")
    file_path: str = Field(..., description="File path where the secret was found")
    secret_type: str = Field(..., description="Type of secret (SecretKeyword, Password, etc.)")
    line_number: int = Field(default=0, description="Line number in file")
    severity: str = Field(default="high", description="Severity level")
    project_name: str = Field(..., description="Project/repository name")

    first_seen_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = Field(None, description="When the secret was resolved")

    scan_ids: List[str] = Field(default_factory=list, description="Scan IDs where this secret appeared")
    appearance_count: int = Field(default=1, description="Number of scans this secret appeared in")
    status: str = Field(default="active", description="active, resolved, dismissed")

    class Settings:
        name = "secret_history"
        indexes = [
            "secret_hash",
            "project_name",
            "status",
            [("project_name", 1), ("status", 1)],
            [("project_name", 1), ("last_seen_at", -1)],
            [("secret_hash", 1), ("file_path", 1)],
        ]


class SecretTrendPoint(Document):
    project_name: str = Field(..., description="Project/repository name")
    date: datetime = Field(..., description="Date of this data point")
    new_secrets: int = Field(default=0, description="Newly detected secrets in this period")
    resolved_secrets: int = Field(default=0, description="Resolved secrets in this period")
    total_active: int = Field(default=0, description="Total active secrets at this point")

    class Settings:
        name = "secret_trends"
        indexes = [
            "project_name",
            "date",
            [("project_name", 1), ("date", -1)],
        ]


__all__ = ["SecretRecord", "SecretTrendPoint"]
