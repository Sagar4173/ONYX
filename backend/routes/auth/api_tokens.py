import logging

from fastapi import APIRouter, Depends, HTTPException, status

from models.user import APIToken, APITokenCreate, APITokenResponse, User
from services.auth.auth_service import auth_service
from utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api-tokens", response_model=APITokenResponse)
async def create_api_token(
    token_data: APITokenCreate,
    current_user: User = Depends(auth_service.get_current_user)
):
    allowed_scopes = [
        "read:reports", "write:reports", "read:scans", "write:scans",
        "read:projects", "write:projects", "read:analytics"
    ]

    invalid_scopes = [scope for scope in token_data.scopes if scope not in allowed_scopes]
    if invalid_scopes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scopes: {invalid_scopes}"
        )

    token = await auth_service.create_api_token(
        user_id=current_user.id,
        name=token_data.name,
        scopes=token_data.scopes,
        expires_in_days=token_data.expires_in_days
    )

    api_token = await APIToken.find_one({
        "user_id": current_user.id,
        "name": token_data.name
    })

    return APITokenResponse(
        token_id=api_token.token_id,
        name=api_token.name,
        token=token,
        prefix=api_token.prefix,
        scopes=api_token.scopes,
        expires_at=api_token.expires_at,
        created_at=api_token.created_at
    )


@router.get("/api-tokens")
async def list_api_tokens(
    current_user: User = Depends(auth_service.get_current_user)
):
    tokens = await APIToken.find({
        "user_id": current_user.id,
        "is_active": True
    }).to_list()

    return [
        {
            "token_id": token.token_id,
            "name": token.name,
            "prefix": token.prefix,
            "scopes": token.scopes,
            "expires_at": token.expires_at,
            "last_used": token.last_used,
            "usage_count": token.usage_count,
            "created_at": token.created_at
        }
        for token in tokens
    ]


@router.delete("/api-tokens/{token_id}")
async def revoke_api_token(
    token_id: str,
    current_user: User = Depends(auth_service.get_current_user)
):
    token = await APIToken.find_one({
        "token_id": token_id,
        "user_id": current_user.id,
        "is_active": True
    })

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API token not found"
        )

    token.is_active = False
    token.revoked_at = utc_now()
    token.revoked_by = current_user.id
    await token.save()

    return {"message": "API token revoked successfully"}
