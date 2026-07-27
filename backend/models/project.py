"""
Project Management Models for ONYX Platform
Handles project creation, management, and organization
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from beanie import Document
from pydantic import BaseModel, Field
from pymongo import IndexModel

# Import shared enums from the single source of truth
from .base import ProjectCategory, ProjectPriority, ProjectStatus


class RepositoryConfig(BaseModel):
    """Repository configuration for project"""
    url: str = Field(..., description="Repository URL")
    branch: str = Field(default="main", description="Default branch to scan")
    access_token: Optional[str] = Field(default=None, description="Access token for private repos")
    scan_paths: List[str] = Field(default_factory=lambda: ["/"], description="Paths to scan")
    exclude_paths: List[str] = Field(default_factory=list, description="Paths to exclude")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://github.com/user/repo",
                "branch": "main",
                "access_token": "ghp_xxxxxxxxxxxx",
                "scan_paths": ["/src", "/api"],
                "exclude_paths": ["/tests", "/docs"]
            }
        }


class ScanConfiguration(BaseModel):
    """Scan configuration for project"""
    enabled_scanners: List[str] = Field(
        default_factory=lambda: ["sast", "secrets", "container"],
        description="List of enabled security scanners"
    )
    scan_schedule: Optional[str] = Field(default=None, description="Cron schedule for automated scans")
    auto_scan_on_push: bool = Field(default=False, description="Auto-scan on repository push")
    scan_timeout_minutes: int = Field(default=60, description="Scan timeout in minutes")
    fail_on_critical: bool = Field(default=False, description="Fail build on critical vulnerabilities")
    
    class Config:
        json_schema_extra = {
            "example": {
                "enabled_scanners": ["sast", "secrets", "container", "infrastructure"],
                "scan_schedule": "0 2 * * *",  # Daily at 2 AM
                "auto_scan_on_push": True,
                "scan_timeout_minutes": 120,
                "fail_on_critical": True
            }
        }


class ProjectMember(BaseModel):
    """Project team member"""
    user_id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="Project role")
    permissions: List[str] = Field(default_factory=list, description="Specific permissions")
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    added_by: str = Field(..., description="User ID who added this member")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "email": "developer@company.com",
                "role": "developer",
                "permissions": ["scan", "view_reports"],
                "added_by": "admin123"
            }
        }


class ProjectStats(BaseModel):
    """Project statistics"""
    total_scans: int = Field(default=0, description="Total number of scans")
    last_scan_date: Optional[datetime] = Field(default=None, description="Last scan date")
    critical_vulnerabilities: int = Field(default=0, description="Current critical vulnerabilities")
    high_vulnerabilities: int = Field(default=0, description="Current high vulnerabilities")
    medium_vulnerabilities: int = Field(default=0, description="Current medium vulnerabilities")
    low_vulnerabilities: int = Field(default=0, description="Current low vulnerabilities")
    security_score: float = Field(default=0.0, description="Current security score")
    compliance_score: float = Field(default=0.0, description="Compliance score")
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Project(Document):
    """Project document model"""
    # Basic Information
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(default=None, description="Project description")
    category: ProjectCategory = Field(default=ProjectCategory.OTHER, description="Project category")
    priority: ProjectPriority = Field(default=ProjectPriority.MEDIUM, description="Project priority")
    status: ProjectStatus = Field(default=ProjectStatus.ACTIVE, description="Project status")
    
    # Repository and Scanning Configuration
    repository: RepositoryConfig = Field(..., description="Repository configuration")
    scan_config: ScanConfiguration = Field(default_factory=ScanConfiguration, description="Scan configuration")
    
    # Team and Permissions
    owner_id: str = Field(..., description="Project owner user ID")
    team_members: List[ProjectMember] = Field(default_factory=list, description="Team members")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Project tags")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom fields")
    
    # Statistics and Analytics
    stats: ProjectStats = Field(default_factory=ProjectStats, description="Project statistics")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = Field(..., description="User ID who created the project")
    updated_by: Optional[str] = Field(default=None, description="User ID who last updated the project")
    
    class Settings:
        name = "projects"
        indexes = [
            IndexModel([("name", 1), ("owner_id", 1)], unique=True),  # Unique project name per owner
            IndexModel([("owner_id", 1), ("status", 1)]),
            IndexModel([("category", 1), ("priority", 1)]),
            IndexModel([("created_at", -1)]),
            IndexModel([("repository.url", 1)]),
            "tags"  # Text index for tag search
        ]

    def update_stats(self, scan_results: Dict[str, Any]) -> None:
        """Update project statistics from scan results"""
        self.stats.total_scans += 1
        self.stats.last_scan_date = datetime.now(timezone.utc)
        
        # Update vulnerability counts
        severity_counts = scan_results.get("severity_distribution", {})
        self.stats.critical_vulnerabilities = severity_counts.get("critical", 0)
        self.stats.high_vulnerabilities = severity_counts.get("high", 0)
        self.stats.medium_vulnerabilities = severity_counts.get("medium", 0)
        self.stats.low_vulnerabilities = severity_counts.get("low", 0)
        
        # Update security score
        self.stats.security_score = scan_results.get("security_score", 0.0)
        self.stats.compliance_score = scan_results.get("compliance_score", 0.0)
        self.stats.last_updated = datetime.now(timezone.utc)

    def add_team_member(self, user_id: str, email: str, role: str, permissions: List[str], added_by: str) -> bool:
        """Add a team member to the project"""
        # Check if user is already a member
        if any(member.user_id == user_id for member in self.team_members):
            return False
        
        member = ProjectMember(
            user_id=user_id,
            email=email,
            role=role,
            permissions=permissions,
            added_by=added_by
        )
        self.team_members.append(member)
        return True

    def remove_team_member(self, user_id: str) -> bool:
        """Remove a team member from the project"""
        initial_count = len(self.team_members)
        self.team_members = [member for member in self.team_members if member.user_id != user_id]
        return len(self.team_members) < initial_count

    def has_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has specific permission in this project"""
        # Owner has all permissions
        if self.owner_id == user_id:
            return True
        
        # Check team member permissions
        for member in self.team_members:
            if member.user_id == user_id:
                return permission in member.permissions
        
        return False

    def get_member_role(self, user_id: str) -> Optional[str]:
        """Get user's role in this project"""
        if self.owner_id == user_id:
            return "owner"
        
        for member in self.team_members:
            if member.user_id == user_id:
                return member.role
        
        return None

    def to_dict_summary(self) -> Dict[str, Any]:
        """Convert to dictionary with summary information"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "repository_url": self.repository.url,
            "total_scans": self.stats.total_scans,
            "last_scan": self.stats.last_scan_date,
            "security_score": self.stats.security_score,
            "vulnerability_count": {
                "critical": self.stats.critical_vulnerabilities,
                "high": self.stats.high_vulnerabilities,
                "medium": self.stats.medium_vulnerabilities,
                "low": self.stats.low_vulnerabilities
            },
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


# Project Management DTOs
class ProjectCreateRequest(BaseModel):
    """Request model for creating a project"""
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: Optional[str] = Field(default=None, max_length=500, description="Project description")
    category: ProjectCategory = Field(default=ProjectCategory.OTHER, description="Project category")
    priority: ProjectPriority = Field(default=ProjectPriority.MEDIUM, description="Project priority")
    repository: RepositoryConfig = Field(..., description="Repository configuration")
    scan_config: Optional[ScanConfiguration] = Field(default=None, description="Scan configuration")
    tags: List[str] = Field(default_factory=list, description="Project tags")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "E-commerce API",
                "description": "Main e-commerce platform API service",
                "category": "api_service",
                "priority": "high",
                "repository": {
                    "url": "https://github.com/company/ecommerce-api",
                    "branch": "main",
                    "scan_paths": ["/src", "/api"]
                },
                "tags": ["api", "production", "critical"]
            }
        }


class ProjectUpdateRequest(BaseModel):
    """Request model for updating a project"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    category: Optional[ProjectCategory] = Field(default=None)
    priority: Optional[ProjectPriority] = Field(default=None)
    status: Optional[ProjectStatus] = Field(default=None)
    repository: Optional[RepositoryConfig] = Field(default=None)
    scan_config: Optional[ScanConfiguration] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)


class TeamMemberRequest(BaseModel):
    """Request model for adding/updating team members"""
    email: str = Field(..., description="User email")
    role: str = Field(..., description="Project role")
    permissions: List[str] = Field(..., description="Specific permissions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "developer@company.com",
                "role": "developer",
                "permissions": ["scan", "view_reports", "manage_settings"]
            }
        }


class RepositoryConfigResponse(BaseModel):
    """Repository configuration for API responses (excludes sensitive fields)"""
    url: str
    branch: str
    scan_paths: List[str]
    exclude_paths: List[str]

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://github.com/user/repo",
                "branch": "main",
                "scan_paths": ["/src", "/api"],
                "exclude_paths": ["/tests", "/docs"]
            }
        }


class ProjectResponse(BaseModel):
    """Response model for project data"""
    id: str
    name: str
    description: Optional[str]
    category: ProjectCategory
    priority: ProjectPriority
    status: ProjectStatus
    repository: RepositoryConfigResponse
    scan_config: ScanConfiguration
    owner_id: str
    team_members: List[ProjectMember]
    tags: List[str]
    stats: ProjectStats
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
