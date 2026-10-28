from typing import Optional

from pydantic import BaseModel, HttpUrl, field_validator

from utils.url_redaction import has_embedded_credentials


class ScanRequest(BaseModel):
    repository_url: HttpUrl
    branch: str = "main"
    scan_types: list[str] = ["sast", "secrets", "container"]
    access_token: Optional[str] = None
    project_id: Optional[str] = None

    @field_validator("repository_url")
    @classmethod
    def _reject_embedded_credentials(cls, value: HttpUrl) -> HttpUrl:
        if has_embedded_credentials(str(value)):
            raise ValueError(
                "Repository URL must not embed credentials; use access_token instead"
            )
        return value
