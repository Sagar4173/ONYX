import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from models.report import WebhookEvent
from routes.webhook.processor import webhook_processor
from utils.error_handling import get_safe_error_detail

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    try:
        headers = dict(request.headers)
        payload = await request.json()

        logger.info(f"Received webhook from {headers.get('user-agent', 'unknown')}")

        event_id = await webhook_processor.process_webhook_event(payload, headers)

        return JSONResponse(
            status_code=200,
            content={
                "status": "accepted",
                "event_id": event_id,
                "message": "Webhook received and processing started"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook endpoint error: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Internal server error"))


@router.get("/events/{event_id}")
async def get_webhook_event(event_id: str) -> Dict[str, Any]:
    try:
        webhook_event = await WebhookEvent.find_one(WebhookEvent.event_id == event_id)

        if not webhook_event:
            raise HTTPException(status_code=404, detail="Webhook event not found")

        result = {
            "event_id": webhook_event.event_id,
            "event_type": webhook_event.event_type,
            "repository_url": webhook_event.repository_url,
            "branch": webhook_event.branch,
            "commit_hash": webhook_event.commit_hash,
            "status": webhook_event.status,
            "created_at": webhook_event.created_at,
            "processed_at": webhook_event.processed_at,
            "error_message": webhook_event.error_message
        }

        if webhook_event.scan_report_id:
            result["scan_report_id"] = str(webhook_event.scan_report_id)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving webhook event: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Internal server error"))


@router.get("/events")
async def list_webhook_events(
    limit: int = Query(50, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    repository_url: Optional[str] = None
) -> Dict[str, Any]:
    try:
        query = WebhookEvent.find()

        if repository_url:
            query = query.find(WebhookEvent.repository_url == repository_url)

        total = await query.count()

        events = await query.sort(-WebhookEvent.created_at).skip(skip).limit(limit).to_list()

        return {
            "events": [
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "repository_url": event.repository_url,
                    "branch": event.branch,
                    "status": event.status,
                    "created_at": event.created_at,
                    "scan_report_id": str(event.scan_report_id) if event.scan_report_id else None
                }
                for event in events
            ],
            "total": total,
            "limit": limit,
            "skip": skip
        }

    except Exception as e:
        logger.error(f"Error listing webhook events: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Internal server error"))
