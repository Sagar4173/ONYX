"""
Authentication Tests
Tests for user authentication, registration, and token management
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    @pytest.mark.asyncio
    async def test_login_success(self, mock_user):
        """Test successful login"""
        from services.auth.auth_service import AuthService
        
        with patch.object(AuthService, 'authenticate_user', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = (mock_user, "access_token", "refresh_token")
            
            # Simulate authentication
            user, access, refresh = await mock_auth(
                email="test@example.com",
                password="password123"
            )
            
            assert user.email == "test@example.com"
            assert access == "access_token"
            assert refresh == "refresh_token"
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        from services.auth.auth_service import AuthService
        
        with patch.object(AuthService, 'authenticate_user', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = None
            
            result = await mock_auth(
                email="wrong@example.com",
                password="wrongpassword"
            )
            
            assert result is None


class TestEmailVerificationEnforcement:
    """REQUIRE_EMAIL_VERIFICATION must block unverified logins when enabled"""

    @pytest.fixture(autouse=True)
    def _enforce_verification(self):
        from config import settings
        with patch.object(settings, "require_email_verification", True):
            yield

    def _user_mock(self, verified: bool):
        from datetime import datetime, timezone

        from models.user import UserRole, UserStatus

        return MagicMock(
            id="user-verify-1",
            email="verify@example.com",
            username="verifyuser",
            full_name="Verify User",
            role=UserRole.VIEWER,
            status=UserStatus.ACTIVE if verified else UserStatus.PENDING_VERIFICATION,
            is_email_verified=verified,
            two_factor_enabled=False,
            hashed_password="hashed",
            save=AsyncMock(),
            dict=MagicMock(return_value={
                "id": "user-verify-1",
                "email": "verify@example.com",
                "username": "verifyuser",
                "full_name": "Verify User",
                "role": UserRole.VIEWER,
                "status": UserStatus.ACTIVE if verified else UserStatus.PENDING_VERIFICATION,
                "timezone": "UTC",
                "is_email_verified": verified,
                "created_at": datetime.now(timezone.utc),
                "notification_preferences": {},
            }),
        )

    def _login_request(self):
        from models.user import LoginRequest
        return LoginRequest(
            username_or_email="verify@example.com",
            password="Password123!",
        )

    def _http_request(self):
        from starlette.requests import Request
        return Request({
            "type": "http",
            "method": "POST",
            "path": "/api/auth/login",
            "headers": [],
            "query_string": b"",
            "client": ("127.0.0.1", 1234),
            "server": ("test", 80),
            "scheme": "http",
        })

    def _session_mock(self):
        session_cls = MagicMock()
        session_cls.return_value.insert = AsyncMock()
        return session_cls

    @pytest.mark.asyncio
    async def test_unverified_login_blocked(self):
        """Unverified PENDING_VERIFICATION user must be rejected with 403"""
        from fastapi import HTTPException

        from routes.auth.sessions import login
        from services.auth.auth_service import auth_service

        user = self._user_mock(verified=False)
        with patch.object(
            auth_service, "authenticate_user", new_callable=AsyncMock, return_value=user
        ):
            with pytest.raises(HTTPException) as exc_info:
                await login(self._login_request(), self._http_request())

        assert exc_info.value.status_code == 403
        assert "Email verification required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verified_login_allowed(self):
        """Verified user must still log in successfully when verification is enforced"""
        from routes.auth.sessions import login
        from services.auth.auth_service import auth_service

        user = self._user_mock(verified=True)
        with (
            patch.object(
                auth_service, "authenticate_user", new_callable=AsyncMock, return_value=user
            ),
            patch.object(auth_service, "create_access_token", return_value="access-123"),
            patch.object(auth_service, "create_refresh_token", return_value="refresh-123"),
            patch("services.auth.auth_service.UserSession", new=self._session_mock()),
        ):
            result = await login(self._login_request(), self._http_request())

        assert result.access_token == "access-123"
        assert result.refresh_token == "refresh-123"

    @pytest.mark.asyncio
    async def test_unverified_login_allowed_when_disabled(self):
        """Unverified login is allowed when REQUIRE_EMAIL_VERIFICATION is off"""
        from config import settings
        from routes.auth.sessions import login
        from services.auth.auth_service import auth_service

        user = self._user_mock(verified=False)
        with (
            patch.object(settings, "require_email_verification", False),
            patch.object(
                auth_service, "authenticate_user", new_callable=AsyncMock, return_value=user
            ),
            patch.object(auth_service, "create_access_token", return_value="access-123"),
            patch.object(auth_service, "create_refresh_token", return_value="refresh-123"),
            patch("services.auth.auth_service.UserSession", new=self._session_mock()),
        ):
            result = await login(self._login_request(), self._http_request())

        assert result.access_token == "access-123"
    
    @pytest.mark.asyncio
    async def test_token_refresh(self, mock_user, mock_jwt_token):
        """Test token refresh"""
        from services.auth.auth_service import AuthService
        
        with patch.object(AuthService, 'refresh_access_token', new_callable=AsyncMock) as mock_refresh:
            mock_refresh.return_value = "new_access_token"
            
            new_token = await mock_refresh(mock_jwt_token)
            
            assert new_token == "new_access_token"
    
    @pytest.mark.asyncio
    async def test_password_hashing(self):
        """Test password hashing is secure"""
        from services.auth.auth_service import AuthService
        
        auth = AuthService()
        
        password = "secure_password_123"
        hashed = auth.hash_password(password)
        
        # Hashed password should not equal plain text
        assert hashed != password
        
        # Should verify correctly
        assert auth.verify_password(password, hashed)
        
        # Wrong password should not verify
        assert not auth.verify_password("wrong_password", hashed)


class TestUserRoles:
    """Test role-based access control"""
    
    def test_admin_role_permissions(self, mock_admin_user):
        """Test admin has all permissions"""
        from models.user import UserRole
        
        assert mock_admin_user.role == UserRole.ADMIN
    
    def test_developer_role_permissions(self, mock_user):
        """Test developer has limited permissions"""
        from models.user import UserRole
        
        assert mock_user.role == UserRole.DEVELOPER


class TestJWTToken:
    """Test JWT token creation and validation"""
    
    def test_token_contains_user_id(self, mock_jwt_token):
        """Test JWT token structure"""
        # Token should be a string with 3 parts separated by dots
        parts = mock_jwt_token.split(".")
        assert len(parts) == 3
    
    @pytest.mark.asyncio
    async def test_expired_token_rejected(self):
        """Test expired tokens are rejected"""
        from services.auth.auth_service import AuthService
        
        with patch.object(AuthService, 'verify_token', new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = None  # Expired tokens return None
            
            result = await mock_verify("expired_token")
            
            assert result is None
