import logging
import os
import tempfile
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from models.user import User
from routes.dependencies import get_current_user
from services.rules.rule_engine import CustomRule, RuleStatus, rule_engine
from utils.error_handling import get_safe_error_detail

from .schemas import RuleCreateRequest, RuleFromTemplateRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Security - Rules"])


@router.get("/rules", response_model=List[Dict[str, Any]])
async def get_rules(current_user: User = Depends(get_current_user), status: Optional[RuleStatus] = None) -> List[Dict[str, Any]]:
    try:
        rules = await rule_engine.get_all_rules(status)
        return [rule.dict() for rule in rules]
    except Exception as e:
        logger.error(f"Error getting rules: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Rule retrieval"))


@router.get("/rules/{rule_id}")
async def get_rule(rule_id: str, current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    try:
        rule = await rule_engine.load_rule(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        return rule.dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e, "Rule retrieval"))


@router.post("/rules")
async def create_rule(request: RuleCreateRequest, current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    try:
        rule = CustomRule(**request.rule_data)

        if request.validate_rule:
            validation_result = await rule_engine.validate_rule(rule, request.test_repo_path)
            if not validation_result.is_valid:
                return {
                    "success": False,
                    "errors": validation_result.errors,
                    "warnings": validation_result.warnings
                }

        success = await rule_engine.save_rule(rule)
        if success:
            return {"success": True, "rule_id": rule.id, "message": "Rule created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save rule")

    except Exception as e:
        logger.error(f"Error creating rule: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.post("/rules/validate")
async def validate_rule(rule_data: Dict[str, Any], current_user: User = Depends(get_current_user), test_repo_path: Optional[str] = None) -> Dict[str, Any]:
    try:
        rule = CustomRule(**rule_data)
        validation_result = await rule_engine.validate_rule(rule, test_repo_path)
        return validation_result.dict()
    except Exception as e:
        logger.error(f"Error validating rule: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.get("/rule-templates", response_model=List[Dict[str, Any]])
async def get_rule_templates(current_user: User = Depends(get_current_user)) -> List[Dict[str, Any]]:
    try:
        templates = await rule_engine.get_all_templates()
        return [template.dict() for template in templates]
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.post("/rules/from-template")
async def create_rule_from_template(request: RuleFromTemplateRequest, current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    try:
        rule = await rule_engine.create_rule_from_template(
            request.template_id,
            request.variables,
            request.rule_id
        )

        if not rule:
            raise HTTPException(status_code=404, detail="Template not found")

        success = await rule_engine.save_rule(rule)
        if success:
            return {"success": True, "rule": rule.dict()}
        else:
            raise HTTPException(status_code=500, detail="Failed to save rule")

    except Exception as e:
        logger.error(f"Error creating rule from template: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))


@router.post("/rules/upload")
async def upload_rules(file: UploadFile = File(...), current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    try:
        filename = file.filename or "unknown.yaml"
        ext = filename.rsplit('.', 1)[-1].lower()
        allowed_extensions = {"yaml", "yml", "json"}
        if ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file extension: .{ext}. Allowed: {', '.join(sorted(allowed_extensions))}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            import json

            import yaml

            with open(tmp_file_path, 'r') as f:
                if ext in ("yaml", "yml"):
                    rules_data = yaml.safe_load(f)
                else:
                    rules_data = json.load(f)

            if isinstance(rules_data, dict):
                rules_data = [rules_data]

            created_rules = []
            errors = []

            for rule_data in rules_data:
                try:
                    rule = CustomRule(**rule_data)
                    success = await rule_engine.save_rule(rule)
                    if success:
                        created_rules.append(rule.id)
                    else:
                        errors.append(f"Failed to save rule {rule.id}")
                except Exception as e:
                    errors.append(f"Invalid rule data: {e}")

            return {
                "success": len(errors) == 0,
                "created_rules": created_rules,
                "errors": errors
            }

        finally:
            os.unlink(tmp_file_path)

    except Exception as e:
        logger.error(f"Error uploading rules: {e}")
        raise HTTPException(status_code=500, detail=get_safe_error_detail(e))
