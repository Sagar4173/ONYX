from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(tags=["Projects - Templates"])


@router.get("/templates", response_model=Dict[str, Any])
async def get_project_templates() -> Dict[str, Any]:
    return {
        "categories": [
            {
                "value": "web_application",
                "label": "Web Application",
                "description": "Frontend and full-stack web applications",
                "default_scanners": ["sast", "secrets", "container"]
            },
            {
                "value": "mobile_application",
                "label": "Mobile Application",
                "description": "iOS and Android mobile applications",
                "default_scanners": ["sast", "secrets"]
            },
            {
                "value": "api_service",
                "label": "API Service",
                "description": "REST APIs and microservices",
                "default_scanners": ["sast", "secrets", "container", "infrastructure"]
            },
            {
                "value": "infrastructure",
                "label": "Infrastructure",
                "description": "Infrastructure as Code (IaC) projects",
                "default_scanners": ["infrastructure", "secrets"]
            },
            {
                "value": "microservice",
                "label": "Microservice",
                "description": "Individual microservice components",
                "default_scanners": ["sast", "secrets", "container"]
            },
            {
                "value": "library",
                "label": "Library/Package",
                "description": "Reusable libraries and packages",
                "default_scanners": ["sast", "secrets"]
            },
            {
                "value": "other",
                "label": "Other",
                "description": "Other types of projects",
                "default_scanners": ["sast", "secrets"]
            }
        ],
        "priorities": [
            {"value": "low", "label": "Low", "color": "#10b981"},
            {"value": "medium", "label": "Medium", "color": "#f59e0b"},
            {"value": "high", "label": "High", "color": "#ef4444"},
            {"value": "critical", "label": "Critical", "color": "#dc2626"}
        ],
        "roles": [
            {
                "value": "admin",
                "label": "Project Admin",
                "permissions": ["scan", "view_reports", "manage_settings", "manage_team"],
                "description": "Full project management access"
            },
            {
                "value": "developer",
                "label": "Developer",
                "permissions": ["scan", "view_reports", "manage_settings"],
                "description": "Development and scanning access"
            },
            {
                "value": "viewer",
                "label": "Viewer",
                "permissions": ["view_reports"],
                "description": "Read-only access to reports"
            },
            {
                "value": "scanner",
                "label": "Scanner",
                "permissions": ["scan", "view_reports"],
                "description": "Can run scans and view results"
            }
        ],
        "scan_types": [
            {
                "value": "sast",
                "label": "Static Analysis (SAST)",
                "description": "Static code analysis for vulnerabilities"
            },
            {
                "value": "secrets",
                "label": "Secret Detection",
                "description": "Detect exposed secrets and credentials"
            },
            {
                "value": "container",
                "label": "Container Security",
                "description": "Container and image vulnerability scanning"
            },
            {
                "value": "infrastructure",
                "label": "Infrastructure as Code",
                "description": "IaC security configuration scanning"
            }
        ]
    }


@router.get("/templates/categories", response_model=Dict[str, Any])
async def get_project_template_categories() -> Dict[str, Any]:
    return await get_project_templates()
