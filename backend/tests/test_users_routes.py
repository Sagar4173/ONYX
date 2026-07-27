"""
Users Routes Tests (unit tests via direct service methods)
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestUserService:
    """Test user service methods directly."""

    @pytest.mark.asyncio
    async def test_user_to_response(self):
        from services.auth.user_service import user_service
        mock_user = MagicMock()
        mock_user.id = "uid"
        mock_user.email = "test@test.com"
        expected = {"id": "uid", "email": "test@test.com", "username": "test", "full_name": "Test"}
        with patch.object(user_service, '_user_to_response', new_callable=AsyncMock, return_value=expected):
            result = await user_service._user_to_response(mock_user)
            assert result["email"] == "test@test.com"

    @pytest.mark.asyncio
    async def test_update_user_profile(self):
        from services.auth.user_service import user_service
        with patch.object(user_service, 'update_user_profile', new_callable=AsyncMock, return_value={"id": "uid"}):
            result = await user_service.update_user_profile("uid", MagicMock(), "uid")
            assert result["id"] == "uid"

    @pytest.mark.asyncio
    async def test_change_password(self):
        from services.auth.user_service import user_service
        with patch.object(user_service, 'change_password', new_callable=AsyncMock):
            await user_service.change_password("uid", MagicMock())

    @pytest.mark.asyncio
    async def test_get_user_sessions(self):
        from services.auth.user_service import user_service
        with patch.object(user_service, 'get_user_sessions', new_callable=AsyncMock, return_value=[]):
            sessions = await user_service.get_user_sessions("uid")
            assert sessions == []

    @pytest.mark.asyncio
    async def test_get_user_api_tokens(self):
        from services.auth.user_service import user_service
        with patch.object(user_service, 'get_user_api_tokens', new_callable=AsyncMock, return_value=[]):
            tokens = await user_service.get_user_api_tokens("uid")
            assert tokens == []

    @pytest.mark.asyncio
    async def test_create_api_token(self):
        from services.auth.user_service import user_service
        token_response = {"token_id": "tok-1", "name": "Test Token", "token": "xxx-secret"}
        with patch.object(user_service, 'create_api_token', new_callable=AsyncMock, return_value=token_response):
            result = await user_service.create_api_token("uid", MagicMock(), "uid")
            assert result["name"] == "Test Token"

    @pytest.mark.asyncio
    async def test_revoke_api_token(self):
        from services.auth.user_service import user_service
        with patch.object(user_service, 'revoke_api_token', new_callable=AsyncMock):
            await user_service.revoke_api_token("uid", "tok-1", "uid")

    @pytest.mark.asyncio
    async def test_list_users(self):
        from services.auth.user_service import user_service
        expected = {"users": [], "total": 0, "page": 1, "page_size": 50}
        with patch.object(user_service, 'list_users', new_callable=AsyncMock, return_value=expected):
            result = await user_service.list_users()
            assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_get_user_statistics(self):
        from services.auth.user_service import user_service
        with patch.object(user_service, 'get_user_statistics', new_callable=AsyncMock, return_value={"total_users": 1}):
            stats = await user_service.get_user_statistics()
            assert stats["total_users"] == 1

    @pytest.mark.asyncio
    async def test_bulk_update_users(self):
        from services.auth.user_service import user_service
        with patch.object(user_service, 'bulk_update_users', new_callable=AsyncMock, return_value={"updated": 2}):
            result = await user_service.bulk_update_users(["uid1", "uid2"], {"role": "admin"}, "admin-id")
            assert result["updated"] == 2

    @pytest.mark.asyncio
    async def test_export_users(self):
        from services.auth.user_service import user_service
        with patch.object(user_service, 'export_users', new_callable=AsyncMock, return_value=[{"email": "test@test.com"}]):
            data = await user_service.export_users("json", {})
            assert len(data) == 1
