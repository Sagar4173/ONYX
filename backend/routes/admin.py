"""
Admin Routes for ONYX Security Intelligence Platform
Provides complete system administration capabilities for admin users
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from beanie.operators import Or, In

from models.user import User, UserRole, UserStatus
from models.project import Project
from models.report import ScanReport, ScanStatus
from services.auth.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Administration"])
security = HTTPBearer()
auth_service = AuthService()


async def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Require admin role for access"""
    user = await auth_service.get_current_user(credentials)
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


@router.get("/dashboard/stats")
async def get_admin_dashboard_stats(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get comprehensive system statistics for admin dashboard
    
    Returns:
    - User statistics (total, by role, by status, new registrations)
    - Project statistics (total, by category, active scans)
    - Scan statistics (total, completed, failed, findings)
    - System health metrics
    """
    try:
        # Calculate time ranges
        now = datetime.now(timezone.utc)
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        # User Statistics
        all_users = await User.find_all().to_list()
        total_users = len(all_users)
        
        users_by_role = {}
        users_by_status = {}
        new_users_24h = 0
        new_users_7d = 0
        new_users_30d = 0
        active_users_24h = 0
        
        for u in all_users:
            # By role
            role = u.role.value if hasattr(u.role, 'value') else str(u.role)
            users_by_role[role] = users_by_role.get(role, 0) + 1
            
            # By status
            user_status = u.status.value if hasattr(u.status, 'value') else str(u.status)
            users_by_status[user_status] = users_by_status.get(user_status, 0) + 1
            
            # New registrations
            if u.created_at:
                if u.created_at >= last_24h:
                    new_users_24h += 1
                if u.created_at >= last_7d:
                    new_users_7d += 1
                if u.created_at >= last_30d:
                    new_users_30d += 1
            
            # Active users (logged in recently)
            if u.last_login and u.last_login >= last_24h:
                active_users_24h += 1
        
        # Project Statistics
        all_projects = await Project.find_all().to_list()
        total_projects = len(all_projects)
        
        projects_by_category = {}
        projects_by_status = {}
        projects_by_priority = {}
        
        for p in all_projects:
            # By category
            cat = p.category.value if hasattr(p.category, 'value') else str(p.category) if p.category else 'unknown'
            projects_by_category[cat] = projects_by_category.get(cat, 0) + 1
            
            # By status
            proj_status = p.status.value if hasattr(p.status, 'value') else str(p.status) if p.status else 'unknown'
            projects_by_status[proj_status] = projects_by_status.get(proj_status, 0) + 1
            
            # By priority
            priority = p.priority.value if hasattr(p.priority, 'value') else str(p.priority) if p.priority else 'unknown'
            projects_by_priority[priority] = projects_by_priority.get(priority, 0) + 1
        
        # Scan Statistics
        all_scans = await ScanReport.find_all().to_list()
        total_scans = len(all_scans)
        
        scans_by_status = {}
        scans_24h = 0
        scans_7d = 0
        total_findings = 0
        findings_by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        
        for scan in all_scans:
            # By status
            scan_status = scan.status.value if hasattr(scan.status, 'value') else str(scan.status)
            scans_by_status[scan_status] = scans_by_status.get(scan_status, 0) + 1
            
            # Recent scans
            if scan.created_at:
                if scan.created_at >= last_24h:
                    scans_24h += 1
                if scan.created_at >= last_7d:
                    scans_7d += 1
            
            # Findings
            total_findings += scan.total_findings or 0
            if scan.findings_by_severity:
                for sev, count in scan.findings_by_severity.items():
                    if sev in findings_by_severity:
                        findings_by_severity[sev] += count or 0
        
        # Calculate system health score
        # Based on: active users ratio, scan success rate, critical findings
        active_user_ratio = active_users_24h / max(total_users, 1)
        completed_scans = scans_by_status.get('completed', 0)
        failed_scans = scans_by_status.get('failed', 0)
        scan_success_rate = completed_scans / max(completed_scans + failed_scans, 1)
        critical_ratio = findings_by_severity['critical'] / max(total_findings, 1)
        
        health_score = min(100, max(0, int(
            (scan_success_rate * 40) +  # 40% weight on scan success
            ((1 - critical_ratio) * 30) +  # 30% weight on low critical findings
            (min(active_user_ratio * 100, 30))  # 30% weight on active users (capped)
        )))
        
        return {
            "users": {
                "total": total_users,
                "by_role": users_by_role,
                "by_status": users_by_status,
                "new_24h": new_users_24h,
                "new_7d": new_users_7d,
                "new_30d": new_users_30d,
                "active_24h": active_users_24h,
                "admin_count": users_by_role.get('admin', 0),
                "pending_verification": users_by_status.get('pending_verification', 0)
            },
            "projects": {
                "total": total_projects,
                "by_category": projects_by_category,
                "by_status": projects_by_status,
                "by_priority": projects_by_priority
            },
            "scans": {
                "total": total_scans,
                "by_status": scans_by_status,
                "last_24h": scans_24h,
                "last_7d": scans_7d,
                "total_findings": total_findings,
                "findings_by_severity": findings_by_severity,
                "success_rate": round(scan_success_rate * 100, 1)
            },
            "system": {
                "health_score": health_score,
                "last_updated": now.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching admin stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch admin statistics: {str(e)}"
        )


@router.get("/users/all")
async def get_all_users_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    role: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get all users with full details for admin management
    Includes activity data, project counts, and scan counts
    """
    try:
        # Build query filters
        query_filters = {}
        
        if role and role.strip():
            query_filters["role"] = role
        
        if status and status.strip():
            query_filters["status"] = status
        
        # Build the query
        if query_filters:
            query = User.find(query_filters)
        else:
            query = User.find_all()
        
        # Apply search
        if search:
            query = User.find({
                **query_filters,
                "$or": [
                    {"username": {"$regex": search, "$options": "i"}},
                    {"email": {"$regex": search, "$options": "i"}},
                    {"full_name": {"$regex": search, "$options": "i"}}
                ]
            })
        
        # Get total count
        total = await query.count()
        
        # Apply sorting and pagination
        sort_direction = -1 if sort_order == "desc" else 1
        users = await query.sort([(sort_by, sort_direction)]).skip(skip).limit(limit).to_list()
        
        # Enrich user data with project and scan counts
        enriched_users = []
        for u in users:
            # Count projects owned by user
            project_count = await Project.find(Project.owner_id == str(u.id)).count()
            
            # Count scans initiated by user
            scan_count = await ScanReport.find(ScanReport.user_id == str(u.id)).count()
            
            user_data = {
                "id": str(u.id),
                "email": u.email,
                "username": u.username,
                "full_name": u.full_name,
                "role": u.role.value if hasattr(u.role, 'value') else str(u.role),
                "status": u.status.value if hasattr(u.status, 'value') else str(u.status),
                "organization": u.organization,
                "department": u.department,
                "avatar_url": u.avatar_url,
                "is_email_verified": u.is_email_verified,
                "two_factor_enabled": u.two_factor_enabled,
                "last_login": u.last_login.isoformat() if u.last_login else None,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "updated_at": u.updated_at.isoformat() if u.updated_at else None,
                "failed_login_attempts": u.failed_login_attempts,
                "locked_until": u.locked_until.isoformat() if u.locked_until else None,
                # Enriched data
                "project_count": project_count,
                "scan_count": scan_count,
                "created_by": u.created_by
            }
            enriched_users.append(user_data)
        
        return {
            "users": enriched_users,
            "pagination": {
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": skip + len(enriched_users) < total
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching users for admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}"
        )


@router.get("/projects/all")
async def get_all_projects_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get all projects across all users for admin oversight
    Includes owner info, scan counts, and vulnerability stats
    """
    try:
        # Build query
        query_filters = {}
        
        if status:
            query_filters["status"] = status
        
        if category:
            query_filters["category"] = category
        
        if query_filters:
            query = Project.find(query_filters)
        else:
            query = Project.find_all()
        
        # Apply search
        if search:
            query = Project.find({
                **query_filters,
                "$or": [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"description": {"$regex": search, "$options": "i"}}
                ]
            })
        
        total = await query.count()
        
        # Apply sorting and pagination
        sort_direction = -1 if sort_order == "desc" else 1
        projects = await query.sort([(sort_by, sort_direction)]).skip(skip).limit(limit).to_list()
        
        # Enrich project data
        enriched_projects = []
        for p in projects:
            # Get owner info
            owner = await User.find_one(User.id == p.owner_id) if p.owner_id else None
            
            # Get scan stats for this project
            project_scans = await ScanReport.find(
                ScanReport.project_id == str(p.id)
            ).to_list()
            
            total_scans = len(project_scans)
            total_findings = sum(s.total_findings or 0 for s in project_scans)
            critical_findings = sum(
                (s.findings_by_severity or {}).get('critical', 0) 
                for s in project_scans
            )
            
            last_scan = None
            if project_scans:
                sorted_scans = sorted(project_scans, key=lambda x: x.created_at or datetime.min, reverse=True)
                if sorted_scans:
                    last_scan = {
                        "id": str(sorted_scans[0].id),
                        "status": sorted_scans[0].status.value if hasattr(sorted_scans[0].status, 'value') else str(sorted_scans[0].status),
                        "created_at": sorted_scans[0].created_at.isoformat() if sorted_scans[0].created_at else None,
                        "total_findings": sorted_scans[0].total_findings
                    }
            
            project_data = {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "category": p.category.value if hasattr(p.category, 'value') else str(p.category) if p.category else None,
                "status": p.status.value if hasattr(p.status, 'value') else str(p.status) if p.status else None,
                "priority": p.priority.value if hasattr(p.priority, 'value') else str(p.priority) if p.priority else None,
                "repository_url": p.repository.url if p.repository else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
                # Owner info
                "owner": {
                    "id": str(owner.id) if owner else None,
                    "username": owner.username if owner else "Unknown",
                    "email": owner.email if owner else None
                } if owner else None,
                "owner_id": p.owner_id,
                # Scan stats
                "total_scans": total_scans,
                "total_findings": total_findings,
                "critical_findings": critical_findings,
                "last_scan": last_scan,
                "team_member_count": len(p.team_members) if p.team_members else 0
            }
            enriched_projects.append(project_data)
        
        return {
            "projects": enriched_projects,
            "pagination": {
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": skip + len(enriched_projects) < total
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching projects for admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch projects: {str(e)}"
        )


@router.get("/reports/all")
async def get_all_reports_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get all scan reports across all users for admin oversight
    """
    try:
        query_filters = {}
        
        if status:
            query_filters["status"] = status
        
        if query_filters:
            query = ScanReport.find(query_filters)
        else:
            query = ScanReport.find_all()
        
        if search:
            query = ScanReport.find({
                **query_filters,
                "project_name": {"$regex": search, "$options": "i"}
            })
        
        # Filter by minimum severity if specified
        if severity:
            severity_key = f"findings_by_severity.{severity}"
            query = query.find({severity_key: {"$gt": 0}})
        
        total = await query.count()
        
        sort_direction = -1 if sort_order == "desc" else 1
        reports = await query.sort([(sort_by, sort_direction)]).skip(skip).limit(limit).to_list()
        
        # Enrich with user info
        enriched_reports = []
        for r in reports:
            user = None
            if r.user_id:
                user = await User.find_one(User.id == r.user_id)
            
            report_data = {
                "id": str(r.id),
                "scan_id": r.scan_id,
                "project_name": r.project_name,
                "project_id": r.project_id,
                "status": r.status.value if hasattr(r.status, 'value') else str(r.status),
                "total_findings": r.total_findings,
                "findings_by_severity": r.findings_by_severity,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "duration_seconds": r.duration_seconds,
                "repository_url": r.git_metadata.repository_url if r.git_metadata else None,
                "branch": r.git_metadata.branch if r.git_metadata else None,
                # User info
                "user": {
                    "id": str(user.id) if user else None,
                    "username": user.username if user else "Unknown",
                    "email": user.email if user else None
                } if user else None,
                "user_id": r.user_id
            }
            enriched_reports.append(report_data)
        
        return {
            "reports": enriched_reports,
            "pagination": {
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": skip + len(enriched_reports) < total
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching reports for admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch reports: {str(e)}"
        )


@router.get("/activity/recent")
async def get_recent_activity(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get recent system activity for admin monitoring
    Combines user registrations, scans, and project creations
    """
    try:
        activities = []
        
        # Recent user registrations
        recent_users = await User.find_all().sort([("created_at", -1)]).limit(20).to_list()
        for u in recent_users:
            if u.created_at:
                activities.append({
                    "type": "user_registration",
                    "icon": "user",
                    "title": f"New user registered: {u.username}",
                    "description": f"{u.email} ({u.role.value if hasattr(u.role, 'value') else u.role})",
                    "timestamp": u.created_at.isoformat(),
                    "entity_id": str(u.id),
                    "entity_type": "user"
                })
        
        # Recent logins
        for u in recent_users:
            if u.last_login and u.last_login > (datetime.now(timezone.utc) - timedelta(days=7)):
                activities.append({
                    "type": "user_login",
                    "icon": "login",
                    "title": f"User login: {u.username}",
                    "description": f"Last login from {u.organization or 'Unknown organization'}",
                    "timestamp": u.last_login.isoformat(),
                    "entity_id": str(u.id),
                    "entity_type": "user"
                })
        
        # Recent projects
        recent_projects = await Project.find_all().sort([("created_at", -1)]).limit(20).to_list()
        for p in recent_projects:
            if p.created_at:
                owner = await User.find_one(User.id == p.owner_id) if p.owner_id else None
                activities.append({
                    "type": "project_created",
                    "icon": "folder",
                    "title": f"Project created: {p.name}",
                    "description": f"By {owner.username if owner else 'Unknown'}",
                    "timestamp": p.created_at.isoformat(),
                    "entity_id": str(p.id),
                    "entity_type": "project"
                })
        
        # Recent scans
        recent_scans = await ScanReport.find_all().sort([("created_at", -1)]).limit(30).to_list()
        for s in recent_scans:
            if s.created_at:
                scan_status = s.status.value if hasattr(s.status, 'value') else str(s.status)
                icon = "check" if scan_status == "completed" else "x" if scan_status == "failed" else "clock"
                
                activities.append({
                    "type": f"scan_{scan_status}",
                    "icon": icon,
                    "title": f"Scan {scan_status}: {s.project_name}",
                    "description": f"{s.total_findings or 0} findings" if scan_status == "completed" else "",
                    "timestamp": s.created_at.isoformat(),
                    "entity_id": str(s.id),
                    "entity_type": "scan"
                })
        
        # Sort all activities by timestamp
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "activities": activities[:limit],
            "total": len(activities)
        }
        
    except Exception as e:
        logger.error(f"Error fetching recent activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch activity: {str(e)}"
        )


@router.get("/users/{user_id}/activity")
async def get_user_activity_admin(
    user_id: str,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """Get activity history for a specific user"""
    try:
        user = await User.find_one(User.id == user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        activities = []
        
        # User's projects
        user_projects = await Project.find(Project.owner_id == user_id).to_list()
        for p in user_projects:
            if p.created_at:
                activities.append({
                    "type": "project_created",
                    "icon": "folder",
                    "title": f"Created project: {p.name}",
                    "description": p.description[:100] if p.description else "",
                    "timestamp": p.created_at.isoformat(),
                    "entity_id": str(p.id),
                    "entity_type": "project"
                })
        
        # User's scan reports
        user_scans = await ScanReport.find(ScanReport.user_id == user_id).to_list()
        for s in user_scans:
            if s.created_at:
                scan_status = s.status.value if hasattr(s.status, 'value') else str(s.status)
                activities.append({
                    "type": f"scan_{scan_status}",
                    "icon": "shield",
                    "title": f"Ran scan: {s.project_name}",
                    "description": f"{s.total_findings or 0} findings found",
                    "timestamp": s.created_at.isoformat(),
                    "entity_id": str(s.id),
                    "entity_type": "scan"
                })
        
        # User login activity
        if user.last_login:
            activities.append({
                "type": "login",
                "icon": "login",
                "title": "Last login",
                "description": f"From {user.organization or 'Unknown organization'}",
                "timestamp": user.last_login.isoformat(),
                "entity_id": str(user.id),
                "entity_type": "user"
            })
        
        # Sort by timestamp
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                "created_at": user.created_at.isoformat() if user.created_at else None
            },
            "activities": activities[:limit],
            "total": len(activities)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user activity: {str(e)}"
        )


@router.delete("/users/{user_id}")
async def delete_user_admin(
    user_id: str,
    current_user: User = Depends(require_admin)
) -> Dict[str, str]:
    """Delete a user (admin only)"""
    try:
        # Prevent self-deletion
        if user_id == str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        user = await User.find_one(User.id == user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Don't allow deleting other admins
        if user.role == UserRole.ADMIN and user_id != str(current_user.id):
            # Count total admins
            admin_count = await User.find(User.role == UserRole.ADMIN).count()
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete the last admin user"
                )
        
        await user.delete()
        logger.info(f"Admin {current_user.username} deleted user {user.username}")
        
        return {"message": f"User {user.username} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.put("/users/{user_id}/role")
async def update_user_role_admin(
    user_id: str,
    role_data: Dict[str, str],
    current_user: User = Depends(require_admin)
) -> Dict[str, str]:
    """Update a user's role (admin only)"""
    try:
        new_role = role_data.get("role")
        if not new_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role is required"
            )
        
        try:
            role_enum = UserRole(new_role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {new_role}"
            )
        
        user = await User.find_one(User.id == user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # If demoting an admin, ensure we have at least one admin
        if user.role == UserRole.ADMIN and role_enum != UserRole.ADMIN:
            admin_count = await User.find(User.role == UserRole.ADMIN).count()
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot demote the last admin user"
                )
        
        user.role = role_enum
        user.updated_at = datetime.now(timezone.utc)
        user.last_updated_by = str(current_user.id)
        await user.save()
        
        logger.info(f"Admin {current_user.username} updated {user.username}'s role to {new_role}")
        
        return {"message": f"User role updated to {new_role}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user role: {str(e)}"
        )


@router.put("/users/{user_id}/status")
async def update_user_status_admin(
    user_id: str,
    status_data: Dict[str, str],
    current_user: User = Depends(require_admin)
) -> Dict[str, str]:
    """Update a user's status (admin only)"""
    try:
        new_status = status_data.get("status")
        if not new_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status is required"
            )
        
        try:
            status_enum = UserStatus(new_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {new_status}"
            )
        
        user = await User.find_one(User.id == user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent self-suspension
        if user_id == str(current_user.id) and status_enum in [UserStatus.SUSPENDED, UserStatus.INACTIVE]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot suspend or deactivate your own account"
            )
        
        user.status = status_enum
        user.updated_at = datetime.now(timezone.utc)
        user.last_updated_by = str(current_user.id)
        await user.save()
        
        logger.info(f"Admin {current_user.username} updated {user.username}'s status to {new_status}")
        
        return {"message": f"User status updated to {new_status}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user status: {str(e)}"
        )


@router.delete("/projects/{project_id}")
async def delete_project_admin(
    project_id: str,
    current_user: User = Depends(require_admin)
) -> Dict[str, str]:
    """Delete any project (admin only)"""
    try:
        project = await Project.find_one(Project.id == project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        project_name = project.name
        await project.delete()
        
        # Also delete associated scan reports
        await ScanReport.find(ScanReport.project_id == project_id).delete()
        
        logger.info(f"Admin {current_user.username} deleted project {project_name}")
        
        return {"message": f"Project {project_name} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )
