"""
Audit-Log Authorization Tests
Verifies authentication and authorization for all 8 audit-log endpoints

Testing strategy:
- Fixture-scoped patches isolate MongoDB during import and request handling.
- app.dependency_overrides is reset per-test via an autouse fixture.
- All 8 audit endpoints use auth_service.require_role(UserRole.SECURITY_MANAGER),
  which captures a bound method of auth_service.get_current_user at route-registration
  time.  Python creates a unique bound-method object per attribute access, so the
  one captured at route-definition time is distinct from any later
  `auth_service.get_current_user` expression.  No public FastAPI API can target
  that specific object without the route inspection below.
- If the dependency structure changes, the override silently misses and tests FAIL
  because they receive 401 instead of 403/200 -- the broken override is caught by
  assertion, not silently hidden.  Explicit assertions verify the expected number
  of captured bound methods were found.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _db_isolation():
    """Prevent real MongoDB connections during import and request handling.
    Applies before each test and is cleaned up after each test.
    """
    with patch("database.db_manager") as mock_db:
        mock_db.connected = True
        mock_db.db = MagicMock()
        with patch("app.init_database", new_callable=AsyncMock):
            with patch("app.close_database", new_callable=AsyncMock):
                yield


@pytest.fixture(autouse=True)
def reset_overrides():
    """Ensure app.dependency_overrides is clean before and after each test."""
    from app import app
    saved = app.dependency_overrides.copy()
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()
    app.dependency_overrides.update(saved)


@pytest.fixture
def mock_audit_service():
    """Mock AuditLoggingService that prevents any real database mutation."""
    svc = MagicMock()
    svc.query_audit_logs = AsyncMock(
        return_value={"success": True, "logs": [], "total": 0}
    )
    svc.get_user_activity = AsyncMock(
        return_value={"success": True, "user_id": "u1", "activity": {}}
    )
    svc.get_resource_history = AsyncMock(
        return_value={"success": True, "resource_type": "r", "resource_id": "1", "history": []}
    )
    svc.generate_compliance_report = AsyncMock(
        return_value={"success": True, "report": {}}
    )
    svc.export_audit_logs = AsyncMock(
        return_value={"success": True, "export_data": {}, "format": "json"}
    )
    svc.verify_log_integrity = AsyncMock(
        return_value={"success": True, "event_id": "e1", "integrity_valid": True}
    )
    return svc


def _build_mock_user(role: str) -> MagicMock:
    user = MagicMock(spec=[])
    user.id = f"{role}-id"
    user.role = role
    user.status = "active"
    return user


# ---------------------------------------------------------------------------
# Audit endpoint path sets
# ---------------------------------------------------------------------------

AUDIT_AUTH_PATHS = frozenset({
    "/api/enterprise/audit-logs/query",
    "/api/enterprise/audit-logs/user/{user_id}",
    "/api/enterprise/audit-logs/resource/{resource_type}/{resource_id}",
    "/api/enterprise/audit-logs/compliance-report",
    "/api/enterprise/audit-logs/export",
    "/api/enterprise/audit-logs/verify/{event_id}",
    "/api/enterprise/audit-logs",
    "/api/enterprise/audit-logs/users",
})

# Endpoints that go through audit service (need mock_service patch)
AUDIT_SERVICE_PATHS = frozenset({
    "/api/enterprise/audit-logs/query",
    "/api/enterprise/audit-logs/user/{user_id}",
    "/api/enterprise/audit-logs/resource/{resource_type}/{resource_id}",
    "/api/enterprise/audit-logs/compliance-report",
    "/api/enterprise/audit-logs/export",
    "/api/enterprise/audit-logs/verify/{event_id}",
})

# Endpoints that access MongoDB directly
AUDIT_DIRECT_DB_PATHS = frozenset({
    "/api/enterprise/audit-logs",
    "/api/enterprise/audit-logs/users",
})


def _setup_client(user_role=None):
    """Build a TestClient with DB mocked and optional auth overrides.

    All 8 audit endpoints use require_role(UserRole.SECURITY_MANAGER), which
    captures a bound-method callable at route-registration time.  Override
    each captured callable via route.dependant introspection.
    """
    from app import app
    from fastapi.testclient import TestClient
    from routes.enterprise import get_database

    app.dependency_overrides.clear()

    # -- database override (always needed) --
    mock_db = MagicMock()
    # Mock audit_logs collection for direct-DB endpoints
    mock_audit_collection = MagicMock()
    mock_audit_collection.distinct = AsyncMock(return_value=["u1", "u2"])
    mock_audit_collection.count_documents = AsyncMock(return_value=0)
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[])
    mock_audit_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_audit_collection

    async def _get_db():
        return mock_db
    app.dependency_overrides[get_database] = _get_db

    if user_role is None:
        return TestClient(app), mock_db

    mock_user = _build_mock_user(user_role)

    # Override the get_current_user bound method inside role_checker
    # for every require_role(SECURITY_MANAGER) callable captured at
    # route-registration time.
    async def _get_current_user_bound():
        return mock_user

    from services.auth.auth_service import AuthService

    found_audit_routes = 0
    found_bound_methods = 0

    for route in app.routes:
        if not hasattr(route, "dependant"):
            continue
        if route.path not in AUDIT_AUTH_PATHS:
            continue
        found_audit_routes += 1
        deps = route.dependant.dependencies
        assert deps, f"Audit route {route.path} has no dependencies"

        # Search all dependency levels for an AuthService bound method.
        # require_role(SECURITY_MANAGER) captures self.get_current_user
        # (a bound method of AuthService) inside role_checker at route-registration
        # time.  Walk the dependency tree to find it.
        overridden_for_this_route = False
        def _walk_deps(dep_list):
            nonlocal overridden_for_this_route, found_bound_methods
            for dep in dep_list:
                if not hasattr(dep, "call"):
                    if hasattr(dep, "dependencies"):
                        _walk_deps(dep.dependencies)
                    continue
                callable_obj = dep.call
                if hasattr(callable_obj, "__self__") and isinstance(callable_obj.__self__, AuthService):
                    assert not overridden_for_this_route, \
                        f"Audit route {route.path} has multiple AuthService bound methods"
                    app.dependency_overrides[callable_obj] = _get_current_user_bound
                    overridden_for_this_route = True
                    found_bound_methods += 1
                elif hasattr(dep, "dependencies"):
                    _walk_deps(dep.dependencies)

        _walk_deps(deps)
        assert overridden_for_this_route, \
            f"Audit route {route.path} has no AuthService bound method"

    assert found_audit_routes == 8, \
        f"Expected 8 audit routes with require_role, found {found_audit_routes}"
    assert found_bound_methods == 8, \
        f"Expected 8 bound-method overrides, found {found_bound_methods}"

    return TestClient(app), mock_db, mock_user


# ===================================================================
# Tests
# ===================================================================


class TestUnauthenticated:
    """All 8 audit endpoints reject requests without authentication."""

    def test_query_audit_logs(self):
        client, _ = _setup_client()
        assert client.get("/api/enterprise/audit-logs/query").status_code == 401

    def test_get_user_activity(self):
        client, _ = _setup_client()
        assert client.get("/api/enterprise/audit-logs/user/u1").status_code == 401

    def test_get_resource_history(self):
        client, _ = _setup_client()
        assert client.get(
            "/api/enterprise/audit-logs/resource/project/p1"
        ).status_code == 401

    def test_generate_compliance_report(self):
        client, _ = _setup_client()
        assert client.post(
            "/api/enterprise/audit-logs/compliance-report",
            json={"start_date": "2025-01-01T00:00:00Z",
                  "end_date": "2025-12-31T00:00:00Z"},
        ).status_code == 401

    def test_export_audit_logs(self):
        client, _ = _setup_client()
        assert client.get(
            "/api/enterprise/audit-logs/export",
            params={"start_date": "2025-01-01T00:00:00Z",
                    "end_date": "2025-12-31T00:00:00Z"},
        ).status_code == 401

    def test_verify_audit_log_integrity(self):
        client, _ = _setup_client()
        assert client.get("/api/enterprise/audit-logs/verify/e1").status_code == 401

    def test_get_audit_logs(self):
        client, _ = _setup_client()
        assert client.get("/api/enterprise/audit-logs").status_code == 401

    def test_get_audit_users(self):
        client, _ = _setup_client()
        assert client.get("/api/enterprise/audit-logs/users").status_code == 401


class TestNonSecurityManagerRejected:
    """Non-privileged roles (viewer, developer) are rejected with 403."""

    @pytest.mark.parametrize("role", ["viewer", "developer"])
    def test_query_audit_logs(self, role, mock_audit_service):
        client, _, _ = _setup_client(role)
        with patch("routes.enterprise.get_audit_service",
                   return_value=mock_audit_service):
            resp = client.get(
                "/api/enterprise/audit-logs/query",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 403

    @pytest.mark.parametrize("role", ["viewer", "developer"])
    def test_get_user_activity(self, role, mock_audit_service):
        client, _, _ = _setup_client(role)
        with patch("routes.enterprise.get_audit_service",
                   return_value=mock_audit_service):
            resp = client.get(
                "/api/enterprise/audit-logs/user/u1",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 403

    @pytest.mark.parametrize("role", ["viewer", "developer"])
    def test_get_resource_history(self, role, mock_audit_service):
        client, _, _ = _setup_client(role)
        with patch("routes.enterprise.get_audit_service",
                   return_value=mock_audit_service):
            resp = client.get(
                "/api/enterprise/audit-logs/resource/project/p1",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 403

    @pytest.mark.parametrize("role", ["viewer", "developer"])
    def test_generate_compliance_report(self, role, mock_audit_service):
        client, _, _ = _setup_client(role)
        with patch("routes.enterprise.get_audit_service",
                   return_value=mock_audit_service):
            resp = client.post(
                "/api/enterprise/audit-logs/compliance-report",
                json={"start_date": "2025-01-01T00:00:00Z",
                      "end_date": "2025-12-31T00:00:00Z"},
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 403

    @pytest.mark.parametrize("role", ["viewer", "developer"])
    def test_export_audit_logs(self, role, mock_audit_service):
        client, _, _ = _setup_client(role)
        with patch("routes.enterprise.get_audit_service",
                   return_value=mock_audit_service):
            resp = client.get(
                "/api/enterprise/audit-logs/export",
                params={"start_date": "2025-01-01T00:00:00Z",
                        "end_date": "2025-12-31T00:00:00Z"},
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 403

    @pytest.mark.parametrize("role", ["viewer", "developer"])
    def test_verify_audit_log_integrity(self, role, mock_audit_service):
        client, _, _ = _setup_client(role)
        with patch("routes.enterprise.get_audit_service",
                   return_value=mock_audit_service):
            resp = client.get(
                "/api/enterprise/audit-logs/verify/e1",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 403

    @pytest.mark.parametrize("role", ["viewer", "developer"])
    def test_get_audit_logs(self, role):
        client, _, _ = _setup_client(role)
        resp = client.get(
            "/api/enterprise/audit-logs",
            headers={"Authorization": "Bearer t"},
        )
        assert resp.status_code == 403

    @pytest.mark.parametrize("role", ["viewer", "developer"])
    def test_get_audit_users(self, role):
        client, _, _ = _setup_client(role)
        resp = client.get(
            "/api/enterprise/audit-logs/users",
            headers={"Authorization": "Bearer t"},
        )
        assert resp.status_code == 403


class TestSecurityManagerAccess:
    """SecurityManager users can reach the intended execution path on all 8 endpoints."""

    def test_query_audit_logs(self, mock_audit_service):
        client, _, _ = _setup_client("security_manager")
        with patch("routes.enterprise.get_audit_service",
                   return_value=mock_audit_service):
            resp = client.get(
                "/api/enterprise/audit-logs/query",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 200
        assert resp.json().get("success") is True

    def test_get_user_activity(self, mock_audit_service):
        client, _, _ = _setup_client("security_manager")
        with patch("routes.enterprise.get_audit_service",
                   return_value=mock_audit_service):
            resp = client.get(
                "/api/enterprise/audit-logs/user/u1",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 200
        assert resp.json().get("success") is True

    def test_get_resource_history(self, mock_audit_service):
        client, _, _ = _setup_client("security_manager")
        with patch("routes.enterprise.get_audit_service",
                   return_value=mock_audit_service):
            resp = client.get(
                "/api/enterprise/audit-logs/resource/project/p1",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 200
        assert resp.json().get("success") is True

    def test_generate_compliance_report(self, mock_audit_service):
        client, _, _ = _setup_client("security_manager")
        with patch("routes.enterprise.get_audit_service",
                   return_value=mock_audit_service):
            resp = client.post(
                "/api/enterprise/audit-logs/compliance-report",
                json={"start_date": "2025-01-01T00:00:00Z",
                      "end_date": "2025-12-31T00:00:00Z"},
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 200
        assert resp.json().get("success") is True

    def test_export_audit_logs(self, mock_audit_service):
        client, _, _ = _setup_client("security_manager")
        with patch("routes.enterprise.get_audit_service",
                   return_value=mock_audit_service):
            resp = client.get(
                "/api/enterprise/audit-logs/export",
                params={"start_date": "2025-01-01T00:00:00Z",
                        "end_date": "2025-12-31T00:00:00Z"},
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 200
        assert resp.json().get("success") is True

    def test_verify_audit_log_integrity(self, mock_audit_service):
        client, _, _ = _setup_client("security_manager")
        with patch("routes.enterprise.get_audit_service",
                   return_value=mock_audit_service):
            resp = client.get(
                "/api/enterprise/audit-logs/verify/e1",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 200
        assert resp.json().get("success") is True

    def test_get_audit_logs(self):
        client, _, _ = _setup_client("security_manager")
        resp = client.get(
            "/api/enterprise/audit-logs",
            headers={"Authorization": "Bearer t"},
        )
        assert resp.status_code == 200
        assert resp.json().get("success") is True

    def test_get_audit_users(self):
        client, _, _ = _setup_client("security_manager")
        resp = client.get(
            "/api/enterprise/audit-logs/users",
            headers={"Authorization": "Bearer t"},
        )
        assert resp.status_code == 200
        assert resp.json().get("success") is True


class TestAdminAccess:
    """Admin users can also reach the intended execution path on all 8 endpoints."""

    def test_query_audit_logs(self, mock_audit_service):
        client, _, _ = _setup_client("admin")
        with patch("routes.enterprise.get_audit_service",
                   return_value=mock_audit_service):
            resp = client.get(
                "/api/enterprise/audit-logs/query",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 200
        assert resp.json().get("success") is True

    def test_get_user_activity(self, mock_audit_service):
        client, _, _ = _setup_client("admin")
        with patch("routes.enterprise.get_audit_service",
                   return_value=mock_audit_service):
            resp = client.get(
                "/api/enterprise/audit-logs/user/u1",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 200
        assert resp.json().get("success") is True

    def test_get_resource_history(self, mock_audit_service):
        client, _, _ = _setup_client("admin")
        with patch("routes.enterprise.get_audit_service",
                   return_value=mock_audit_service):
            resp = client.get(
                "/api/enterprise/audit-logs/resource/project/p1",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 200
        assert resp.json().get("success") is True

    def test_generate_compliance_report(self, mock_audit_service):
        client, _, _ = _setup_client("admin")
        with patch("routes.enterprise.get_audit_service",
                   return_value=mock_audit_service):
            resp = client.post(
                "/api/enterprise/audit-logs/compliance-report",
                json={"start_date": "2025-01-01T00:00:00Z",
                      "end_date": "2025-12-31T00:00:00Z"},
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 200
        assert resp.json().get("success") is True

    def test_export_audit_logs(self, mock_audit_service):
        client, _, _ = _setup_client("admin")
        with patch("routes.enterprise.get_audit_service",
                   return_value=mock_audit_service):
            resp = client.get(
                "/api/enterprise/audit-logs/export",
                params={"start_date": "2025-01-01T00:00:00Z",
                        "end_date": "2025-12-31T00:00:00Z"},
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 200
        assert resp.json().get("success") is True

    def test_verify_audit_log_integrity(self, mock_audit_service):
        client, _, _ = _setup_client("admin")
        with patch("routes.enterprise.get_audit_service",
                   return_value=mock_audit_service):
            resp = client.get(
                "/api/enterprise/audit-logs/verify/e1",
                headers={"Authorization": "Bearer t"},
            )
        assert resp.status_code == 200
        assert resp.json().get("success") is True

    def test_get_audit_logs(self):
        client, _, _ = _setup_client("admin")
        resp = client.get(
            "/api/enterprise/audit-logs",
            headers={"Authorization": "Bearer t"},
        )
        assert resp.status_code == 200
        assert resp.json().get("success") is True

    def test_get_audit_users(self):
        client, _, _ = _setup_client("admin")
        resp = client.get(
            "/api/enterprise/audit-logs/users",
            headers={"Authorization": "Bearer t"},
        )
        assert resp.status_code == 200
        assert resp.json().get("success") is True
