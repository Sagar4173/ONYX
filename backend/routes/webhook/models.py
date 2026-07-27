from typing import Optional

from pydantic import BaseModel, HttpUrl


class ScanRequest(BaseModel):
    repository_url: HttpUrl
    branch: str = "main"
    scan_types: list[str] = ["sast", "secrets", "container"]
    access_token: Optional[str] = None
    project_id: Optional[str] = None
