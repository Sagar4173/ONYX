"""
Project Management Service for SecureDevOps Platform
Handles project CRUD operations, team management, and business logic
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from bson import ObjectId
from beanie import PydanticObjectId
from beanie.operators import In, And, Or
from fastapi import HTTPException, status

from models.project import (
    Project, ProjectCreateRequest, ProjectUpdateRequest, 
    TeamMemberRequest, ProjectStatus, ProjectCategory, ProjectPriority,
    ProjectMember, ScanConfiguration
)
from models.user import User, UserRole
from models.report import ScanReport, WebhookEvent

logger = logging.getLogger(__name__)
class ProjectService:
    """Service for managing projects"""
    
    def __init__(self):
        self.default_permissions = {
            "owner": ["all"],
            "admin": ["scan", "view_reports", "manage_settings", "manage_team", "delete"],
            "developer": ["scan", "view_reports", "manage_settings"],
            "viewer": ["view_reports"],
            "scanner": ["scan", "view_reports"]
        }
    
    async def create_project(self, project_data: ProjectCreateRequest, owner_id: str) -> Project:
        """Create a new project"""
        # Check if project name already exists for this owner
        existing = await Project.find_one(
            And(Project.name == project_data.name, Project.owner_id == owner_id)
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Project '{project_data.name}' already exists"
            )
        
        # Create scan configuration if not provided
        scan_config = project_data.scan_config or ScanConfiguration()
        
        # Create project
        project = Project(
            name=project_data.name,
            description=project_data.description,
            category=project_data.category,
            priority=project_data.priority,
            repository=project_data.repository,
            scan_config=scan_config,
            owner_id=owner_id,
            tags=project_data.tags,
            created_by=owner_id
        )
        
        await project.save()
        return project
    
    async def get_project_by_id(self, project_id: str, user_id: str) -> Optional[Project]:
        """Get project by ID with permission check"""
        try:
            project = await Project.get(project_id)
            if not project:
                return None
            
            # Check if user has access to this project
            if not await self.user_has_access(project, user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this project"
                )
            
            return project
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            return None
    
    async def get_user_projects(
        self, 
        user_id: str, 
        status_filter: Optional[ProjectStatus] = None,
        category_filter: Optional[ProjectCategory] = None,
        priority_filter: Optional[ProjectPriority] = None,
        search_query: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Project], int]:
        """Get projects accessible to user with filters"""
        
        # Base query - projects owned by user or where user is team member
        base_conditions = [
            Or(
                Project.owner_id == user_id,
                Project.team_members.user_id == user_id
            ),
            # Always exclude deleted projects unless explicitly filtering for them
            Project.status != ProjectStatus.DELETED
        ]
        
        # Add filters (if user explicitly wants deleted projects, they can filter)
        if status_filter:
            # If filtering for deleted, remove the exclusion and add the filter
            if status_filter == ProjectStatus.DELETED:
                base_conditions = [
                    Or(
                        Project.owner_id == user_id,
                        Project.team_members.user_id == user_id
                    ),
                    Project.status == status_filter
                ]
            else:
                base_conditions.append(Project.status == status_filter)
        
        if category_filter:
            base_conditions.append(Project.category == category_filter)
        
        if priority_filter:
            base_conditions.append(Project.priority == priority_filter)
        
        # Search functionality
        if search_query:
            search_conditions = [
                Project.name.regex(search_query, "i"),
                Project.description.regex(search_query, "i"),
                In(Project.tags, [search_query])
            ]
            base_conditions.append(Or(*search_conditions))
        
        # Combine all conditions
        query = And(*base_conditions) if len(base_conditions) > 1 else base_conditions[0]
        
        # Get total count
        total = await Project.find(query).count()
        
        # Get projects with pagination
        projects = await Project.find(query).sort(-Project.created_at).skip(skip).limit(limit).to_list()
        
        return projects, total
    
    async def update_project(
        self, 
        project_id: str, 
        update_data: ProjectUpdateRequest, 
        user_id: str
    ) -> Project:
        """Update project with permission check"""
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check if user has permission to edit
        if not await self.user_has_permission(project, user_id, "manage_settings"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to edit this project"
            )
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(project, field, value)
        
        project.updated_at = datetime.now(timezone.utc)
        project.updated_by = user_id
        
        await project.save()
        return project
    
    async def delete_project(self, project_id: str, user_id: str, hard_delete: bool = True) -> bool:
        """Delete project permanently or soft delete, including all related data"""
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Only owner can delete project
        if project.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owner can delete the project"
            )
        
        if hard_delete:
            # Delete all related scan reports first
            # Match by project name and repository URL
            deleted_reports_count = 0
            deleted_events_count = 0
            
            try:
                # Delete reports by project name
                result = await ScanReport.find(
                    ScanReport.project_name == project.name
                ).delete()
                if result:
                    deleted_reports_count += result.deleted_count if hasattr(result, 'deleted_count') else 0
                
                # Also delete by repository URL if available
                if project.repository and project.repository.url:
                    result2 = await ScanReport.find(
                        ScanReport.git_metadata.repository_url == project.repository.url
                    ).delete()
                    if result2:
                        deleted_reports_count += result2.deleted_count if hasattr(result2, 'deleted_count') else 0
                    
                    # Delete webhook events by repository URL
                    result3 = await WebhookEvent.find(
                        WebhookEvent.repository_url == project.repository.url
                    ).delete()
                    if result3:
                        deleted_events_count += result3.deleted_count if hasattr(result3, 'deleted_count') else 0
                
                logger.info(f"Deleted {deleted_reports_count} scan reports and {deleted_events_count} webhook events for project {project_id}")
            except Exception as e:
                logger.warning(f"Error deleting related data for project {project_id}: {e}")
            
            # Permanently delete the project from database
            await project.delete()
            logger.info(f"Project {project_id} and all related data permanently deleted by user {user_id}")
        else:
            # Soft delete - just change status
            project.status = ProjectStatus.DELETED
            project.updated_at = datetime.now(timezone.utc)
            project.updated_by = user_id
            await project.save()
            logger.info(f"Project {project_id} soft deleted by user {user_id}")
        
        return True
    
    async def add_team_member(
        self, 
        project_id: str, 
        member_data: TeamMemberRequest, 
        user_id: str
    ) -> Project:
        """Add team member to project"""
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check if user has permission to manage team
        if not await self.user_has_permission(project, user_id, "manage_team"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to manage team members"
            )
        
        # Find user by email
        user = await User.find_one(User.email == member_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {member_data.email} not found"
            )
        
        # Add team member
        success = project.add_team_member(
            user_id=str(user.id),
            email=member_data.email,
            role=member_data.role,
            permissions=member_data.permissions,
            added_by=user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a team member"
            )
        
        project.updated_at = datetime.now(timezone.utc)
        project.updated_by = user_id
        
        await project.save()
        return project
    
    async def remove_team_member(self, project_id: str, member_user_id: str, user_id: str) -> Project:
        """Remove team member from project"""
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check if user has permission to manage team
        if not await self.user_has_permission(project, user_id, "manage_team"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to manage team members"
            )
        
        # Cannot remove owner
        if project.owner_id == member_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove project owner"
            )
        
        success = project.remove_team_member(member_user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team member not found"
            )
        
        project.updated_at = datetime.now(timezone.utc)
        project.updated_by = user_id
        
        await project.save()
        return project
    
    async def get_project_stats(self, project_id: str, user_id: str) -> Dict[str, Any]:
        """Get detailed project statistics"""
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Get recent scan reports
        recent_reports = await ScanReport.find(
            ScanReport.project_name == project.name
        ).sort(-ScanReport.scan_start_time).limit(10).to_list()
        
        # Calculate trends
        vulnerability_trend = []
        score_trend = []
        
        for report in reversed(recent_reports):
            severity_dist = report.severity_distribution or {}
            total_vulns = sum(severity_dist.values())
            vulnerability_trend.append({
                "date": report.scan_start_time,
                "count": total_vulns
            })
            score_trend.append({
                "date": report.scan_start_time,
                "score": report.security_score or 0
            })
        
        return {
            "basic_stats": project.stats.model_dump(),
            "recent_scans": len(recent_reports),
            "vulnerability_trend": vulnerability_trend,
            "security_score_trend": score_trend,
            "team_size": len(project.team_members) + 1,  # +1 for owner
            "last_activity": project.updated_at
        }
    
    async def user_has_access(self, project: Project, user_id: str) -> bool:
        """Check if user has access to project"""
        # Owner always has access
        if project.owner_id == user_id:
            return True
        
        # Check if user is team member
        return any(member.user_id == user_id for member in project.team_members)
    
    async def user_has_permission(self, project: Project, user_id: str, permission: str) -> bool:
        """Check if user has specific permission"""
        # Owner has all permissions
        if project.owner_id == user_id:
            return True
        
        # Check team member permissions
        for member in project.team_members:
            if member.user_id == user_id:
                return permission in member.permissions or "all" in member.permissions
        
        return False
    
    async def get_project_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get user's project analytics overview"""
        # Get user's projects
        projects, total = await self.get_user_projects(user_id)
        
        # Calculate analytics
        stats = {
            "total_projects": total,
            "active_projects": 0,
            "total_scans": 0,
            "total_vulnerabilities": 0,
            "average_security_score": 0,
            "category_distribution": {},
            "priority_distribution": {},
            "recent_activity": []
        }
        
        total_scores = 0
        project_with_scores = 0
        
        for project in projects:
            if project.status == ProjectStatus.ACTIVE:
                stats["active_projects"] += 1
            
            stats["total_scans"] += project.stats.total_scans
            
            # Vulnerability counts
            stats["total_vulnerabilities"] += (
                project.stats.critical_vulnerabilities +
                project.stats.high_vulnerabilities +
                project.stats.medium_vulnerabilities +
                project.stats.low_vulnerabilities
            )
            
            # Security scores
            if project.stats.security_score > 0:
                total_scores += project.stats.security_score
                project_with_scores += 1
            
            # Category distribution
            category = project.category.value
            stats["category_distribution"][category] = stats["category_distribution"].get(category, 0) + 1
            
            # Priority distribution
            priority = project.priority.value
            stats["priority_distribution"][priority] = stats["priority_distribution"].get(priority, 0) + 1
            
            # Recent activity
            stats["recent_activity"].append({
                "project_name": project.name,
                "last_scan": project.stats.last_scan_date,
                "updated_at": project.updated_at
            })
        
        # Calculate average security score
        if project_with_scores > 0:
            stats["average_security_score"] = total_scores / project_with_scores
        
        # Sort recent activity
        stats["recent_activity"].sort(key=lambda x: x["updated_at"] or datetime.min, reverse=True)
        stats["recent_activity"] = stats["recent_activity"][:10]  # Limit to 10 items
        
        return stats
    
    async def update_project_from_scan(self, project_name: str, scan_results: Dict[str, Any], repository_url: str = None) -> Optional[Project]:
        """Update project statistics from scan results
        
        Tries to find the project by:
        1. Project ID (if project_name is a valid ObjectId)
        2. Project name
        3. Repository URL
        """
        from bson import ObjectId
        
        project = None
        
        # First, try to find by project ID if it looks like an ObjectId
        if project_name and len(project_name) == 24:
            try:
                project = await Project.get(ObjectId(project_name))
            except:
                pass
        
        # If not found, try by project name
        if not project and project_name:
            project = await Project.find_one(Project.name == project_name)
        
        # If still not found, try by repository URL
        if not project and repository_url:
            project = await Project.find_one(Project.repository.url == repository_url)
        
        if not project:
            return None
        
        # Update stats
        project.update_stats(scan_results)
        project.updated_at = datetime.now(timezone.utc)
        
        await project.save()
        return project
