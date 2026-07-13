"""
Retention Authorization Tests
Verifies authentication and authorization for all 6 retention endpoints

Testing strategy:
- Fixture-scoped patches isolate MongoDB during import and request handling.
  No module-level patchers run for the entire pytest process.
- app.dependency_overrides is reset per-test via an autouse fixture.
- For GET endpoints: overrides the local get_current_user function via the
  public app.dependency_overrides API (keyed on the imported function).
- For POST endpoints: overrides the get_current_user bound method captured
  inside role_checker by require_role.  Python creates a unique bound-method
  object per attribute access, so the one captured at route-definition time is
  distinct from any later `auth_service.get_current_user` expression.
  No public FastAPI API can target that specific object without the route
  inspection below.

  If the dependency structure changes (parameter order, different decorator),
  the override silently misses and tests FAIL because they receive 401 instead
  of 403/200 — the broken override is caught by assertion, not silently hidden.
  Additionally, explicit assertions verify the expected number of captured
  bound methods were found.
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
    No cross-test contamination.
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
def mock_service():
    """Mock DataRetentionService that prevents any real database mutation."""
    svc = MagicMock()
    svc.create_retention_policy = AsyncMock(
        return_value={"success": True, "policy_id": "mock-policy"}
    )
    svc.execute_retention_policy = AsyncMock(
        return_value={
            "success": True,
            "execution_result": {"processed_count": 0},
        }
    )
    svc.execute_all_policies = AsyncMock(
        return_value={"success": True, "policies_executed": 0}
    )
    svc.initialize_default_policies = AsyncMock(
        return_value={"success": True, "count": 0}
    )
    svc.get_retention_statistics = AsyncMock(
        return_value={"success": True, "statistics": {}}
    )
    return svc


def _build_mock_user(role: str) -> MagicMock:
    user = MagicMock(spec=[])
    user.id = f"{role}-id"
    user.role = role
    user.status = "active"
    return user


# ---------------------------------------------------------------------------
# Override helpers
# ---------------------------------------------------------------------------

RETENTION_POST_PATHS = {
    "/api/enterprise/retention/policies",
    "/api/enterprise/retention/policies/{policy_id}/execute",
    "/api/enterprise/retention/policies/execute-all",
    "/api/enterprise/retention/initialize-defaults",
}

RETENTION_GET_PATHS = {
    "/api/enterprise/retention-policies",
    "/api/enterprise/retention/statistics",
}


def _setup_client(user_role=None):
    """Build a TestClient with DB mocked and optional auth overrides.

    Overrides the bound get_current_user callables captured by require_role
    at route-registration time.  These live inside each POST route's
    role_checker closure and must be individually overridden.

    Explicit assertions verify that the expected count of bound methods
    were found, so changes to the dependency structure cause test setup
    failure rather than silent false passes.
    """
    from app import app
    from fastapi.testclient import TestClient
    from routes.enterprise import get_database, get_current_user as _local_get_current_user

    app.dependency_overrides.clear()

    # -- database override (always needed) --
    mock_db = MagicMock()
    async def _get_db():
        return mock_db
    app.dependency_overrides[get_database] = _get_db

    if user_role is None:
        return TestClient(app), mock_db

    mock_user = _build_mock_user(user_role)

    # -- override get_current_user for GET endpoints (public API) --
    async def _get_current_user():
        return mock_user
    app.dependency_overrides[_local_get_current_user] = _get_current_user

    # -- override the get_current_user bound method inside role_checker
    #    so the actual require_role logic runs against our mock user.
    #
    #    Justification for route.dependant introspection:
    #    require_role(UserRole.ADMIN) is called at module import time.
    #    It returns a closure (role_checker) whose body contains
    #    Depends(self.get_current_user).  self.get_current_user evaluates
    #    to a unique bound-method object at that instant.  Python creates a
    #    NEW bound-method object on every attribute access, so neither
    #    auth_service.get_current_user (test-time) nor
    #    patch.object(AuthService, 'get_current_user') (class-level) can
    #    target the originally-captured object.  The only reference to the
    #    exact captured callable lives in FastAPI's internal dependency
    #    graph (route.dependant.dependencies[0].dependencies[0].call).
    #    app.dependency_overrides is the documented public API for
    #    overriding dependencies, but it requires the exact callable as
    #    key because Python uses identity (not equality) for bound-method
    #    lookup.
    #    --
    async def _get_current_user_bound():
        return mock_user

    found_post_routes = 0
    found_bound_methods = 0

    for route in app.routes:
        if not hasattr(route, "dependant"):
            continue
        if "retention" not in route.path:
            continue
        if route.path not in RETENTION_POST_PATHS:
            continue
        found_post_routes += 1
        deps = route.dependant.dependencies
        assert deps, f"POST route {route.path} has no dependencies"
        assert hasattr(deps[0], "dependencies"), \
            f"POST route {route.path} first dependency has no sub-dependencies"

        sub_deps = deps[0].dependencies
        assert sub_deps, f"POST route {route.path} first dependency has empty sub-dependencies"
        assert hasattr(sub_deps[0], "call"), \
            f"POST route {route.path} sub-dependency has no callable"
        callable_obj = sub_deps[0].call
        assert hasattr(callable_obj, "__self__"), \
            f"POST route {route.path} sub-dependency is not a bound method"
        app.dependency_overrides[callable_obj] = _get_current_user_bound
        found_bound_methods += 1

    assert found_post_routes == 4, \
        f"Expected 4 POST retention routes, found {found_post_routes}"
    assert found_bound_methods == 4, \
        f"Expected 4 bound-method overrides, found {found_bound_methods}"

    return TestClient(app), mock_db, mock_user


# ===================================================================
# Tests
# ===================================================================

class TestUnauthenticated:
    """All 6 retention endpoints reject requests without authentication."""

    def test_get_policies(self):
        client, _ = _setup_client()
        assert client.get("/api/enterprise/retention-policies").status_code == 401

    def test_create_policy(self):
        client, _ = _setup_client()
        assert client.post("/api/enterprise/retention/policies", json={}).status_code == 401

    def test_execute_policy(self):
        client, _ = _setup_client()
        assert client.post("/api/enterprise/retention/policies/dummy/execute").status_code == 401

    def test_execute_all(self):
        client, _ = _setup_client()
        assert client.post("/api/enterprise/retention/policies/execute-all").status_code == 401

    def test_get_statistics(self):
        client, _ = _setup_client()
        assert client.get("/api/enterprise/retention/statistics").status_code == 401

    def test_initialize_defaults(self):
        client, _ = _setup_client()
        assert client.post("/api/enterprise/retention/initialize-defaults").status_code == 401


class TestReadOnlyAuth:
    """Read-only GET endpoints accept any authenticated user."""

    @pytest.mark.parametrize("role", ["developer", "viewer"])
    def test_get_policies(self, role):
        client, _, _ = _setup_client(role)
        resp = client.get("/api/enterprise/retention-policies",
                          headers={"Authorization": "Bearer t"})
        assert resp.status_code == 200

    @pytest.mark.parametrize("role", ["developer", "viewer"])
    def test_get_statistics(self, role, mock_service):
        client, _, _ = _setup_client(role)
        with patch("routes.enterprise.get_retention_service",
                   return_value=mock_service):
            resp = client.get("/api/enterprise/retention/statistics",
                              headers={"Authorization": "Bearer t"})
            assert resp.status_code == 200


class TestNonAdminRejected:
    """State-changing POST endpoints return 403 for non-admin users.

    The override lets the actual role_checker run against a mock non-admin
    user.  role_checker sees role='developer' (or 'viewer'), which fails the
    ``current_user.role != required_role and current_user.role != ADMIN``
    check, producing 403.
    """

    @pytest.mark.parametrize("role", ["developer", "viewer"])
    def test_create_policy(self, role):
        client, _, _ = _setup_client(role)
        resp = client.post(
            "/api/enterprise/retention/policies",
            json={"policy_type": "x", "retention_days": 1, "action": "delete"},
            headers={"Authorization": "Bearer t"},
        )
        assert resp.status_code == 403

    @pytest.mark.parametrize("role", ["developer", "viewer"])
    def test_execute_policy(self, role):
        client, _, _ = _setup_client(role)
        resp = client.post(
            "/api/enterprise/retention/policies/dummy/execute",
            headers={"Authorization": "Bearer t"},
        )
        assert resp.status_code == 403

    @pytest.mark.parametrize("role", ["developer", "viewer"])
    def test_execute_all(self, role):
        client, _, _ = _setup_client(role)
        resp = client.post(
            "/api/enterprise/retention/policies/execute-all",
            headers={"Authorization": "Bearer t"},
        )
        assert resp.status_code == 403

    @pytest.mark.parametrize("role", ["developer", "viewer"])
    def test_initialize_defaults(self, role):
        client, _, _ = _setup_client(role)
        resp = client.post(
            "/api/enterprise/retention/initialize-defaults",
            headers={"Authorization": "Bearer t"},
        )
        assert resp.status_code == 403


class TestAdminAccess:
    """Admin users can reach the intended execution path on all 6 endpoints.

    The role_checker receives the admin mock user from the overridden bound
    method, sees role='admin', passes the role check, and the endpoint runs
    to completion (with the retention service mocked).
    """

    def test_get_policies(self):
        client, _, _ = _setup_client("admin")
        resp = client.get("/api/enterprise/retention-policies",
                          headers={"Authorization": "Bearer t"})
        assert resp.status_code == 200

    def test_get_statistics(self, mock_service):
        client, _, _ = _setup_client("admin")
        with patch("routes.enterprise.get_retention_service",
                   return_value=mock_service):
            resp = client.get("/api/enterprise/retention/statistics",
                              headers={"Authorization": "Bearer t"})
            assert resp.status_code == 200

    def _check_post_success(self, url, json_data=None, mock_service=None):
        client, _, _ = _setup_client("admin")
        kw = {"headers": {"Authorization": "Bearer t"}}
        if json_data is not None:
            kw["json"] = json_data
        with patch("routes.enterprise.get_retention_service",
                   return_value=mock_service):
            resp = client.post(url, **kw)
            assert resp.status_code == 200
            assert resp.json().get("success") is True

    def test_create_policy(self, mock_service):
        self._check_post_success(
            "/api/enterprise/retention/policies",
            {"policy_type": "scan_results", "retention_days": 30, "action": "delete"},
            mock_service,
        )

    def test_execute_policy(self, mock_service):
        self._check_post_success(
            "/api/enterprise/retention/policies/dummy/execute",
            mock_service=mock_service,
        )

    def test_execute_all(self, mock_service):
        self._check_post_success(
            "/api/enterprise/retention/policies/execute-all",
            mock_service=mock_service,
        )

    def test_initialize_defaults(self, mock_service):
        self._check_post_success(
            "/api/enterprise/retention/initialize-defaults",
            mock_service=mock_service,
        )
