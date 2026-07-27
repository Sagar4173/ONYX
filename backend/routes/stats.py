import logging

from fastapi import APIRouter

from database import db_manager
from models.report import ScanReport
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["stats"])


@router.get("/stats/public")
async def get_public_stats():
    """Get public statistics for landing page - no auth required"""
    try:
        if db_manager.db is None:
            return {
                "total_scans": 0,
                "total_vulnerabilities": 0,
                "total_users": 0,
                "uptime_percentage": None,
            }

        total_scans = await ScanReport.count()
        total_users = await User.count()

        reports = await ScanReport.find_all().to_list()
        total_vulnerabilities = sum(
            r.total_findings for r in reports if r.total_findings
        )

        return {
            "total_scans": total_scans,
            "total_vulnerabilities": total_vulnerabilities,
            "total_users": total_users,
            "uptime_percentage": None,
        }

    except Exception as e:
        logger.error(f"Error getting public stats: {e}")
        return {
            "total_scans": 0,
            "total_vulnerabilities": 0,
            "total_users": 0,
            "uptime_percentage": None,
        }
