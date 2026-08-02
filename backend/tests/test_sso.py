"""
Google SSO tests: token verification, auto-provisioning, 2FA gate, domain allowlist.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from config import settings
from models.user import UserRole, UserStatus


def _google_claims(email="jane@example.com", verified=True, name="Jane Doe", iss="https://accounts.google.com"):
    return {
        "iss": iss,
        "email": email,
        "email_verified": verified,
        "name": name,
        "picture": "https://example.com/avatar.png",
        "aud": "test-client",
        "sub": "google-subject-123",
    }


def _http_request():
    from starlette.requests import Request
    return Request({
        "type": "http",
        "method": "POST",
        "path": "/api/auth/sso/google",
        "headers": [],
        "query_string": b"",
        "client": ("127.0.0.1", 1234),
        "server": ("test", 80),
        "scheme": "http",
    })


def _user_mock(email="jane@example.com", twofa=False):
    return MagicMock(
        id="user-sso-1",
        email=email,
        username="jane",
        full_name="Jane Doe",
        role=UserRole.VIEWER,
        status=UserStatus.ACTIVE,
        is_email_verified=True,
        two_factor_enabled=twofa,
        two_factor_secret="SECRET",
        two_factor_backup_codes=[],
        locked_until=None,
        failed_login_attempts=0,
        hashed_password="hashed",
        is_account_locked=MagicMock(return_value=False),
        save=AsyncMock(),
        dict=MagicMock(return_value={
            "id": "user-sso-1",
            "email": email,
            "username": "jane",
            "full_name": "Jane Doe",
            "role": UserRole.VIEWER,
            "status": UserStatus.ACTIVE,
            "timezone": "UTC",
            "is_email_verified": True,
            "created_at": datetime.now(timezone.utc),
            "notification_preferences": {},
        }),
    )


class TestGoogleTokenVerification:
    """Tests for verify_google_id_token (claim checks inside the service)"""

    async def test_disabled_when_no_client_id(self):
        from services.auth.auth_service import auth_service

        with patch.object(settings, "google_client_id", None):
            with pytest.raises(HTTPException) as exc_info:
                auth_service.verify_google_id_token("fake-token")
        assert exc_info.value.status_code == 404

    async def test_invalid_signature_rejected(self):
        from services.auth.auth_service import auth_service

        with patch.object(settings, "google_client_id", "test-client"):
            with patch(
                "services.auth.auth_service.google_id_token.verify_oauth2_token",
                side_effect=ValueError("Invalid token"),
            ):
                with pytest.raises(HTTPException) as exc_info:
                    auth_service.verify_google_id_token("bad-token")
        assert exc_info.value.status_code == 401

    async def test_unverified_google_email_rejected(self):
        from services.auth.auth_service import auth_service

        with patch.object(settings, "google_client_id", "test-client"):
            with patch(
                "services.auth.auth_service.google_id_token.verify_oauth2_token",
                return_value=_google_claims(verified=False),
            ):
                with pytest.raises(HTTPException) as exc_info:
                    auth_service.verify_google_id_token("token")
        assert exc_info.value.status_code == 403
        assert "not verified" in exc_info.value.detail

    async def test_bad_issuer_rejected(self):
        from services.auth.auth_service import auth_service

        with patch.object(settings, "google_client_id", "test-client"):
            with patch(
                "services.auth.auth_service.google_id_token.verify_oauth2_token",
                return_value=_google_claims(iss="https://evil.com"),
            ):
                with pytest.raises(HTTPException) as exc_info:
                    auth_service.verify_google_id_token("token")
        assert exc_info.value.status_code == 401
        assert "issuer" in exc_info.value.detail

    async def test_domain_allowlist_enforced(self):
        from services.auth.auth_service import auth_service

        claims = _google_claims(email="bob@evil.com")
        claims["nonce"] = "allowed-nonce"

        with (
            patch.object(settings, "google_client_id", "test-client"),
            patch.object(settings, "google_allowed_domains", "example.com"),
            patch(
                "services.auth.auth_service.google_id_token.verify_oauth2_token",
                return_value=claims,
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                auth_service.verify_google_id_token("token", nonce="allowed-nonce")
        assert exc_info.value.status_code == 403
        assert "domain" in exc_info.value.detail

    async def test_valid_token_returns_claims(self):
        from services.auth.auth_service import auth_service

        claims = _google_claims()
        claims["nonce"] = "expected-nonce"

        with (
            patch.object(settings, "google_client_id", "test-client"),
            patch(
                "services.auth.auth_service.google_id_token.verify_oauth2_token",
                return_value=claims,
            ) as verify_mock,
        ):
            info = auth_service.verify_google_id_token("good-token", nonce="expected-nonce")
        assert info["email"] == "jane@example.com"
        # google-auth uses the request arg to fetch its certificate cache on
        # every verification; a non-callable transport (e.g. requests.Request)
        # makes every SSO login fail with "'Request' object is not callable".
        transport = verify_mock.call_args.args[1]
        assert callable(transport)

    async def test_missing_nonce_rejected(self):
        from services.auth.auth_service import auth_service

        with (
            patch.object(settings, "google_client_id", "test-client"),
            patch(
                "services.auth.auth_service.google_id_token.verify_oauth2_token",
                return_value=_google_claims(),
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                auth_service.verify_google_id_token("good-token")
        assert exc_info.value.status_code == 401
        assert "nonce" in exc_info.value.detail

    async def test_nonce_mismatch_rejected(self):
        from services.auth.auth_service import auth_service

        with (
            patch.object(settings, "google_client_id", "test-client"),
            patch(
                "services.auth.auth_service.google_id_token.verify_oauth2_token",
                return_value=_google_claims(),
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                auth_service.verify_google_id_token("good-token", nonce="expected-nonce")
        assert exc_info.value.status_code == 401
        assert "nonce" in exc_info.value.detail

    async def test_nonce_match_accepted(self):
        from services.auth.auth_service import auth_service

        claims = _google_claims()
        claims["nonce"] = "expected-nonce"

        with (
            patch.object(settings, "google_client_id", "test-client"),
            patch(
                "services.auth.auth_service.google_id_token.verify_oauth2_token",
                return_value=claims,
            ),
        ):
            info = auth_service.verify_google_id_token("good-token", nonce="expected-nonce")
        assert info["email"] == "jane@example.com"


class TestGoogleSSOLogin:
    """Tests for google_login (session + provisioning flow)"""

    @pytest.fixture(autouse=True)
    def _beanie_ready(self):
        with (
            patch("database.beanie_initialized", True),
            patch(
                "services.auth.auth_service.auth_service.consume_sso_nonce",
                new_callable=AsyncMock,
            ),
        ):
            yield

    async def test_invalid_token_rejected(self):
        from services.auth.auth_service import auth_service

        with patch.object(
            auth_service, "verify_google_id_token", side_effect=HTTPException(401, "Invalid Google authentication token")
        ):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.google_login("bad-token", None, _http_request())
        assert exc_info.value.status_code == 401

    async def test_new_user_auto_provisioned(self):
        from services.auth.auth_service import auth_service

        session_cls = MagicMock()
        session_cls.return_value.insert = AsyncMock()

        user_cls = MagicMock()
        user_cls.find_one = AsyncMock(return_value=None)
        created = MagicMock()
        created.id = "user-sso-new"
        created.email = "jane@example.com"
        created.insert = AsyncMock()
        created.dict = MagicMock(return_value={
            "id": "user-sso-new",
            "email": "jane@example.com",
            "username": "jane",
            "full_name": "Jane Doe",
            "role": UserRole.VIEWER,
            "status": UserStatus.ACTIVE,
            "timezone": "UTC",
            "is_email_verified": True,
            "created_at": datetime.now(timezone.utc),
            "notification_preferences": {},
        })
        user_cls.return_value = created

        with (
            patch.object(settings, "google_client_id", "test-client"),
            patch.object(auth_service, "verify_google_id_token", return_value=_google_claims()),
            patch.object(auth_service, "create_access_token", return_value="access-123"),
            patch.object(auth_service, "create_refresh_token", return_value="refresh-123"),
            patch("services.auth.auth_service.User", new=user_cls),
            patch("services.auth.auth_service.UserSession", new=session_cls),
        ):
            result = await auth_service.google_login("token", None, _http_request())

        assert result.access_token == "access-123"
        assert result.refresh_token == "refresh-123"
        kwargs = user_cls.call_args.kwargs
        assert kwargs["auth_provider"] == "google"
        assert kwargs["status"] == UserStatus.ACTIVE
        assert kwargs["is_email_verified"] is True
        assert kwargs["email"] == "jane@example.com"
        created.insert.assert_awaited()

    async def test_auto_provision_blocked_when_registration_disabled(self):
        from services.auth.auth_service import auth_service

        with (
            patch.object(settings, "google_client_id", "test-client"),
            patch.object(settings, "allow_registration", False),
            patch.object(auth_service, "verify_google_id_token", return_value=_google_claims()),
            patch("services.auth.auth_service.User.find_one", new=AsyncMock(return_value=None)),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.google_login("token", None, _http_request())
        assert exc_info.value.status_code == 403
        assert "Registration is disabled" in exc_info.value.detail

    async def test_pending_unverified_existing_account_rejected(self):
        from services.auth.auth_service import auth_service

        user = _user_mock()
        user.status = UserStatus.PENDING_VERIFICATION
        user.is_email_verified = False

        with (
            patch.object(settings, "google_client_id", "test-client"),
            patch.object(settings, "require_email_verification", True),
            patch.object(auth_service, "verify_google_id_token", return_value=_google_claims()),
            patch("services.auth.auth_service.User.find_one", new=AsyncMock(return_value=user)),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.google_login("token", None, _http_request())
        assert exc_info.value.status_code == 403
        assert "Email verification required" in exc_info.value.detail

    async def test_existing_user_logs_in(self):
        from services.auth.auth_service import auth_service

        session_cls = MagicMock()
        session_cls.return_value.insert = AsyncMock()
        user = _user_mock()

        with (
            patch.object(settings, "google_client_id", "test-client"),
            patch.object(auth_service, "verify_google_id_token", return_value=_google_claims()),
            patch.object(auth_service, "create_access_token", return_value="access-123"),
            patch.object(auth_service, "create_refresh_token", return_value="refresh-123"),
            patch("services.auth.auth_service.User.find_one", new=AsyncMock(return_value=user)),
            patch("services.auth.auth_service.UserSession", new=session_cls),
        ):
            result = await auth_service.google_login("token", None, _http_request())

        assert result.access_token == "access-123"
        user.save.assert_awaited()

    async def test_existing_user_with_2fa_requires_code(self):
        from services.auth.auth_service import auth_service

        user = _user_mock(twofa=True)

        with (
            patch.object(settings, "google_client_id", "test-client"),
            patch.object(auth_service, "verify_google_id_token", return_value=_google_claims()),
            patch.object(auth_service, "_generate_2fa_temp_token", return_value="temp-123"),
            patch("services.auth.auth_service.User.find_one", new=AsyncMock(return_value=user)),
        ):
            result = await auth_service.google_login("token", None, _http_request())

        assert result["requires_2fa"] is True
        assert result["temp_token"] == "temp-123"

    async def test_existing_user_2fa_wrong_code_rejected(self):
        from services.auth.auth_service import auth_service

        user = _user_mock(twofa=True)

        with (
            patch.object(settings, "google_client_id", "test-client"),
            patch.object(auth_service, "verify_google_id_token", return_value=_google_claims()),
            patch("services.auth.auth_service.User.find_one", new=AsyncMock(return_value=user)),
            patch("pyotp.TOTP.verify", return_value=False),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.google_login("token", "000000", _http_request())
        assert exc_info.value.status_code == 401

    async def test_2fa_round_trip_uses_same_nonce_once(self):
        """The nonce survives the 2FA prompt and is consumed only on completion,
        so the (id_token, nonce) pair completes at most once."""
        import pyotp

        from services.auth.auth_service import auth_service

        session_cls = MagicMock()
        session_cls.return_value.insert = AsyncMock()
        user = _user_mock(twofa=True)
        user.two_factor_secret = pyotp.random_base32()
        consume = auth_service.consume_sso_nonce
        code = pyotp.TOTP(user.two_factor_secret).now()

        with (
            patch.object(settings, "google_client_id", "test-client"),
            patch.object(auth_service, "verify_google_id_token", return_value=_google_claims()),
            patch.object(auth_service, "create_access_token", return_value="access-123"),
            patch.object(auth_service, "create_refresh_token", return_value="refresh-123"),
            patch.object(auth_service, "_generate_2fa_temp_token", return_value="temp-123"),
            patch("services.auth.auth_service.User.find_one", new=AsyncMock(return_value=user)),
            patch("services.auth.auth_service.UserSession", new=session_cls),
        ):
            first = await auth_service.google_login("token", None, _http_request(), nonce="nonce-1")
            consume.assert_not_awaited()
            assert first["requires_2fa"] is True

            second = await auth_service.google_login("token", code, _http_request(), nonce="nonce-1")
            consume.assert_awaited_once_with("nonce-1")

        assert second.access_token == "access-123"

    async def test_suspended_account_rejected(self):
        from services.auth.auth_service import auth_service

        user = _user_mock()
        user.status = UserStatus.SUSPENDED

        with (
            patch.object(settings, "google_client_id", "test-client"),
            patch.object(auth_service, "verify_google_id_token", return_value=_google_claims()),
            patch("services.auth.auth_service.User.find_one", new=AsyncMock(return_value=user)),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.google_login("token", None, _http_request())
        assert exc_info.value.status_code == 403

    async def test_locked_account_rejected(self):
        from services.auth.auth_service import auth_service

        user = _user_mock()
        user.is_account_locked.return_value = True
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=10)
        with (
            patch.object(settings, "google_client_id", "test-client"),
            patch.object(auth_service, "verify_google_id_token", return_value=_google_claims()),
            patch("services.auth.auth_service.User.find_one", new=AsyncMock(return_value=user)),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.google_login("token", None, _http_request())
        assert exc_info.value.status_code == 423


def test_is_account_locked_naive_round_trip():
    """Mongo strips tzinfo; a naive locked_until must still lock the account, not crash."""
    from models.user import User

    user = User.model_construct(
        email="lock@example.com",
        username="lockuser",
        full_name="Lock User",
        hashed_password="x",
    )
    user.locked_until = (datetime.now(timezone.utc) + timedelta(minutes=5)).replace(tzinfo=None)
    assert user.is_account_locked() is True

    user.locked_until = (datetime.now(timezone.utc) - timedelta(minutes=5)).replace(tzinfo=None)
    assert user.is_account_locked() is False


class TestSsoNonceLifecycle:
    """Server-issued SSO nonces must be validated, single-use, and short-lived."""

    @pytest.fixture(autouse=True)
    def _beanie_ready(self):
        with patch("database.beanie_initialized", True):
            yield

    async def test_consume_rejects_missing_nonce(self):
        from services.auth.auth_service import auth_service

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.consume_sso_nonce("")
        assert exc_info.value.status_code == 401

    async def test_consume_rejects_unknown_nonce(self):
        from services.auth.auth_service import auth_service

        nonce_cls = MagicMock()
        nonce_cls.find_one = AsyncMock(return_value=None)

        with patch("services.auth.auth_service.SsoNonce", new=nonce_cls):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.consume_sso_nonce("nope")
        assert exc_info.value.status_code == 401
        assert "nonce" in exc_info.value.detail

    async def test_consume_rejects_expired_nonce(self):
        from services.auth.auth_service import auth_service

        doc = MagicMock()
        doc.used = False
        doc.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        doc.save = AsyncMock()

        nonce_cls = MagicMock()
        nonce_cls.find_one = AsyncMock(return_value=doc)

        with patch("services.auth.auth_service.SsoNonce", new=nonce_cls):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.consume_sso_nonce("old-nonce")
        assert exc_info.value.status_code == 401
        doc.save.assert_not_awaited()

    async def test_consume_marks_used_and_rejects_replay(self):
        from services.auth.auth_service import auth_service

        doc = MagicMock()
        doc.used = False
        doc.expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        doc.save = AsyncMock()

        nonce_cls = MagicMock()
        nonce_cls.find_one = AsyncMock(return_value=doc)

        with patch("services.auth.auth_service.SsoNonce", new=nonce_cls):
            await auth_service.consume_sso_nonce("valid-nonce")
        assert doc.used is True
        doc.save.assert_awaited()

        doc.used = True
        with patch("services.auth.auth_service.SsoNonce", new=nonce_cls):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.consume_sso_nonce("valid-nonce")
        assert exc_info.value.status_code == 401

    async def test_consume_accepts_naive_unexpired_nonce(self):
        """Mongo strips tzinfo on round-trip; naive datetimes must not crash comparisons."""
        from services.auth.auth_service import auth_service

        doc = MagicMock()
        doc.used = False
        doc.expires_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).replace(tzinfo=None)
        doc.save = AsyncMock()

        nonce_cls = MagicMock()
        nonce_cls.find_one = AsyncMock(return_value=doc)

        with patch("services.auth.auth_service.SsoNonce", new=nonce_cls):
            await auth_service.consume_sso_nonce("naive-nonce")
        assert doc.used is True
        doc.save.assert_awaited()

    async def test_consume_rejects_naive_expired_nonce(self):
        """Naive (DB-round-tripped) expired nonces must raise 401, not 500."""
        from services.auth.auth_service import auth_service

        doc = MagicMock()
        doc.used = False
        doc.expires_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).replace(tzinfo=None)
        doc.save = AsyncMock()

        nonce_cls = MagicMock()
        nonce_cls.find_one = AsyncMock(return_value=doc)

        with patch("services.auth.auth_service.SsoNonce", new=nonce_cls):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.consume_sso_nonce("naive-expired")
        assert exc_info.value.status_code == 401
        doc.save.assert_not_awaited()


class TestGoogleSSOEndpoints:
    async def test_endpoint_disabled(self):
        from fastapi.testclient import TestClient

        from app import app
        from database import require_beanie

        app.dependency_overrides[require_beanie] = lambda: None
        try:
            with patch.object(settings, "google_client_id", None):
                response = TestClient(app).get("/api/auth/sso/google/config")
            assert response.status_code == 200
            assert response.json() == {"enabled": False, "client_id": None, "nonce": None}

            with patch.object(settings, "google_client_id", None):
                response = TestClient(app).post(
                    "/api/auth/sso/google",
                    json={"id_token": "x", "nonce": "abc"},
                )
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    async def test_config_endpoint_when_enabled(self):
        from fastapi.testclient import TestClient

        from app import app
        from database import require_beanie
        from services.auth.auth_service import auth_service

        app.dependency_overrides[require_beanie] = lambda: None
        try:
            with (
                patch.object(settings, "google_client_id", "my-client-id"),
                patch.object(
                    auth_service,
                    "issue_sso_nonce",
                    new_callable=AsyncMock,
                    return_value="issued-nonce-1",
                ),
            ):
                response = TestClient(app).get("/api/auth/sso/google/config")
            assert response.status_code == 200
            assert response.json() == {
                "enabled": True,
                "client_id": "my-client-id",
                "nonce": "issued-nonce-1",
            }
        finally:
            app.dependency_overrides.clear()

    async def test_endpoint_rejects_bad_body(self):
        from fastapi.testclient import TestClient

        from app import app
        from database import require_beanie

        app.dependency_overrides[require_beanie] = lambda: None
        try:
            with patch.object(settings, "google_client_id", "test-client"):
                response = TestClient(app).post("/api/auth/sso/google", json={})
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    async def test_endpoint_login_success(self):
        from fastapi.testclient import TestClient

        from app import app
        from database import require_beanie
        from routes.auth.sso import google_sso_login
        from services.auth.auth_service import auth_service

        app.dependency_overrides[require_beanie] = lambda: None
        try:
            with (
                patch.object(settings, "google_client_id", "test-client"),
                patch.object(auth_service, "google_login", new_callable=AsyncMock) as mock_login,
            ):
                mock_login.return_value = {"access_token": "access-123", "user": {}}
                response = TestClient(app).post(
                    "/api/auth/sso/google",
                    json={"id_token": "valid-id-token", "nonce": "test-nonce"},
                )
            assert response.status_code == 200
            assert response.json()["access_token"] == "access-123"
            mock_login.assert_awaited_once()
        finally:
            app.dependency_overrides.clear()
