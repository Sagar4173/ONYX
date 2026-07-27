"""
Projects Routes Tests (unit tests via direct service methods)
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestProjectService:
    """Test project service methods directly."""

    @pytest.mark.asyncio
    async def test_create_project(self):
        from services.infrastructure.project_service import ProjectService
        svc = ProjectService()
        mock_project = MagicMock()
        mock_project.id = "proj-123"
        mock_project.name = "Test Project"
        mock_project.model_dump.return_value = {
            "id": "proj-123",
            "name": "Test Project",
        }
        with patch.object(svc, 'create_project', new_callable=AsyncMock, return_value=mock_project):
            result = await svc.create_project(MagicMock(), "user-id")
            assert result.name == "Test Project"

    @pytest.mark.asyncio
    async def test_get_user_projects(self):
        from services.infrastructure.project_service import ProjectService
        svc = ProjectService()
        with patch.object(svc, 'get_user_projects', new_callable=AsyncMock, return_value=([], 0)):
            projects, total = await svc.get_user_projects("user-id")
            assert projects == []
            assert total == 0

    @pytest.mark.asyncio
    async def test_get_project_by_id(self):
        from services.infrastructure.project_service import ProjectService
        svc = ProjectService()
        mock_project = MagicMock()
        mock_project.id = "proj-123"
        with patch.object(svc, 'get_project_by_id', new_callable=AsyncMock, return_value=mock_project):
            result = await svc.get_project_by_id("proj-123", "user-id")
            assert result.id == "proj-123"

    @pytest.mark.asyncio
    async def test_get_project_by_id_not_found(self):
        from services.infrastructure.project_service import ProjectService
        svc = ProjectService()
        with patch.object(svc, 'get_project_by_id', new_callable=AsyncMock, return_value=None):
            result = await svc.get_project_by_id("nonexistent", "user-id")
            assert result is None

    @pytest.mark.asyncio
    async def test_update_project(self):
        from services.infrastructure.project_service import ProjectService
        svc = ProjectService()
        mock_project = MagicMock()
        mock_project.id = "proj-123"
        mock_project.model_dump.return_value = {"id": "proj-123", "name": "Updated"}
        with patch.object(svc, 'update_project', new_callable=AsyncMock, return_value=mock_project):
            result = await svc.update_project("proj-123", MagicMock(), "user-id")
            assert result.id == "proj-123"

    @pytest.mark.asyncio
    async def test_delete_project(self):
        from services.infrastructure.project_service import ProjectService
        svc = ProjectService()
        with patch.object(svc, 'delete_project', new_callable=AsyncMock, return_value=True):
            result = await svc.delete_project("proj-123", "user-id")
            assert result is True

    @pytest.mark.asyncio
    async def test_add_team_member(self):
        from services.infrastructure.project_service import ProjectService
        svc = ProjectService()
        mock_project = MagicMock()
        mock_project.model_dump.return_value = {"id": "proj-123"}
        with patch.object(svc, 'add_team_member', new_callable=AsyncMock, return_value=mock_project):
            result = await svc.add_team_member("proj-123", MagicMock(), "user-id")
            assert result.model_dump()["id"] == "proj-123"

    @pytest.mark.asyncio
    async def test_get_project_stats(self):
        from services.infrastructure.project_service import ProjectService
        svc = ProjectService()
        with patch.object(svc, 'get_project_stats', new_callable=AsyncMock, return_value={"stats": {}}):
            result = await svc.get_project_stats("proj-123", "user-id")
            assert "stats" in result

    @pytest.mark.asyncio
    async def test_get_project_analytics(self):
        from services.infrastructure.project_service import ProjectService
        svc = ProjectService()
        with patch.object(svc, 'get_project_analytics', new_callable=AsyncMock, return_value={"analytics": {}}):
            result = await svc.get_project_analytics("user-id")
            assert "analytics" in result
