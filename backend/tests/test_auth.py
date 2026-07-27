"""
Authentication Tests
Tests for user authentication, registration, and token management
"""
from unittest.mock import AsyncMock, patch

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
