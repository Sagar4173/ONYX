import logging
from datetime import datetime
from typing import List

from bson import ObjectId

from database import scan_reports_collection
from models.report import ScanReport

logger = logging.getLogger(__name__)


async def _get_scan_reports_by_ids(report_ids: List[str]) -> List[ScanReport]:
    try:
        reports = []
        for report_id in report_ids:
            if not ObjectId.is_valid(report_id):
                continue
            report = await scan_reports_collection.find_one({"_id": ObjectId(report_id)})
            if report:
                report["_id"] = str(report["_id"])
                reports.append(ScanReport(**report))
        return reports
    except Exception as e:
        logger.error(f"Error fetching scan reports by IDs: {e}")
        return []


async def _get_recent_scan_reports(cutoff_date: datetime) -> List[ScanReport]:
    try:
        cursor = scan_reports_collection.find({
            "created_at": {"$gte": cutoff_date}
        }).sort("created_at", -1)

        reports = []
        async for report_doc in cursor:
            reports.append(ScanReport(**report_doc))

        return reports
    except Exception as e:
        logger.error(f"Error fetching recent scan reports: {e}")
        return []


async def _get_scan_reports_since(cutoff_date: datetime) -> List[ScanReport]:
    try:
        cursor = scan_reports_collection.find({
            "created_at": {"$gte": cutoff_date}
        }).sort("created_at", 1)

        reports = []
        async for report_doc in cursor:
            reports.append(ScanReport(**report_doc))

        return reports
    except Exception as e:
        logger.error(f"Error fetching scan reports for trends: {e}")
        return []
