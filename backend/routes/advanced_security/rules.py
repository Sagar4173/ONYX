import logging

from fastapi import APIRouter, Depends, HTTPException

from models.user import User
from routes.dependencies import get_current_user
from services.service_registry import ServiceRegistry
from utils.error_handling import get_safe_error_detail

from .schemas import RuleParseRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Advanced Security - Rules"])


@router.post("/rules/parse")
async def parse_security_rules(
    request: RuleParseRequest,
    current_user: User = Depends(get_current_user)
):
    rule_parser = ServiceRegistry.get_rule_parser()
    if not rule_parser:
        raise HTTPException(status_code=503, detail="Rule parser not initialized")

    try:
        parsed_rules = await rule_parser.parse_rules(request.rules)
        return {
            "parsed_rules": parsed_rules,
            "total_rules": len(parsed_rules),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Rule parsing error: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Rule parsing"))


@router.get("/rules/test-status/{rule_id}")
async def get_rule_test_status(
    rule_id: str,
    current_user: User = Depends(get_current_user)
):
    rule_tester = ServiceRegistry.get_rule_tester()
    if not rule_tester:
        raise HTTPException(status_code=503, detail="Rule tester not initialized")

    try:
        response = await rule_tester.get_test_status(rule_id)
        return response
    except Exception as e:
        logger.error(f"Error getting rule test status: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Rule test status retrieval"))
