import json
import logging
from dataclasses import asdict
from enum import Enum
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException, Response
from pydantic import BaseModel, Field

from services.scanning.utils.sbom import (
    SBOMFormat,
    get_sbom_service,
)
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sbom", tags=["Enterprise Security - SBOM"])


class SBOMGenerateRequest(BaseModel):
    repository_path: str = Field(..., description="Path to the repository")
    format: str = Field(default="spdx", description="SBOM format: spdx or cyclonedx")
    include_dev_deps: bool = Field(default=False, description="Include dev dependencies")
    enrich_vulnerabilities: bool = Field(default=True, description="Enrich with vulnerability data")


@router.post("/generate")
async def generate_sbom(request: SBOMGenerateRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    try:
        sbom_gen = get_sbom_service()

        sbom_format = SBOMFormat.SPDX if request.format.lower() == "spdx" else SBOMFormat.CYCLONEDX

        sbom = await sbom_gen.generate_sbom(
            repository_path=request.repository_path,
            output_format=sbom_format,
            include_dev_dependencies=request.include_dev_deps,
            enrich_with_vulnerabilities=request.enrich_vulnerabilities
        )

        sbom_dict = _sbom_to_dict(sbom)

        return {
            "success": True,
            "format": request.format,
            "sbom": sbom_dict
        }
    except Exception as e:
        logger.error(f"Error generating SBOM: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.post("/generate/download")
async def generate_sbom_download(
    repository_path: str,
    format: str = "spdx",
    output_type: str = "json"
):
    try:
        sbom_gen = get_sbom_service()

        sbom_format = SBOMFormat.SPDX if format.lower() == "spdx" else SBOMFormat.CYCLONEDX

        sbom = await sbom_gen.generate_sbom(
            repository_path=repository_path,
            output_format=sbom_format
        )

        sbom_dict = _sbom_to_dict(sbom)

        if output_type.lower() == "json":
            content = json.dumps(sbom_dict, indent=2)
            media_type = "application/json"
            filename = f"sbom-{format}.json"
        else:
            content = dict_to_xml(sbom_dict, root_name="sbom")
            media_type = "application/xml"
            filename = f"sbom-{format}.xml"

        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error generating SBOM download: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/formats")
async def get_supported_sbom_formats() -> Dict[str, Any]:
    return {
        "formats": [
            {
                "id": "spdx",
                "name": "SPDX 2.3",
                "description": "Software Package Data Exchange - Linux Foundation standard",
                "output_types": ["json", "xml"],
                "compliance": ["NTIA", "Executive Order 14028"]
            },
            {
                "id": "cyclonedx",
                "name": "CycloneDX 1.5",
                "description": "OWASP lightweight SBOM standard",
                "output_types": ["json", "xml"],
                "compliance": ["OWASP", "FDA", "NTIA"]
            }
        ],
        "supported_languages": [
            "Python", "JavaScript", "TypeScript", "Go", "Rust",
            "Java", "Ruby", ".NET/C#"
        ]
    }


def _sbom_to_dict(sbom) -> dict:
    try:
        result = asdict(sbom)

        def convert_enums(obj):
            if isinstance(obj, dict):
                return {k: convert_enums(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_enums(item) for item in obj]
            elif isinstance(obj, Enum):
                return obj.value
            elif hasattr(obj, 'isoformat'):
                return obj.isoformat()
            return obj
        return convert_enums(result)
    except Exception as e:
        logger.warning(f"Failed to convert SBOM to dict via asdict: {e}")
        return vars(sbom) if hasattr(sbom, '__dict__') else str(sbom)


def dict_to_xml(data: dict, root_name: str = "root") -> str:
    def _to_xml(d, parent):
        xml = ""
        if isinstance(d, dict):
            for key, val in d.items():
                xml += f"<{key}>{_to_xml(val, key)}</{key}>"
        elif isinstance(d, list):
            for item in d:
                xml += f"<item>{_to_xml(item, 'item')}</item>"
        else:
            xml = str(d) if d is not None else ""
        return xml

    return f'<?xml version="1.0" encoding="UTF-8"?><{root_name}>{_to_xml(data, root_name)}</{root_name}>'
