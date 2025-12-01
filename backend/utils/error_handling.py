"""
Error Handling Utilities for ONYX Platform
Provides safe error messages that don't expose internal details in production
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Check if we're in production
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() == "production"


def safe_error_message(
    error: Exception,
    operation: str,
    include_details: bool = False
) -> str:
    """
    Generate a safe error message that doesn't expose internal details in production.
    
    Args:
        error: The caught exception
        operation: Description of the operation that failed (e.g., "scan status retrieval")
        include_details: Whether to include error details (only in non-production)
    
    Returns:
        str: A safe error message suitable for API responses
    """
    # Always log the full error for debugging
    logger.error(f"{operation} failed: {str(error)}", exc_info=True)
    
    # In production, return a generic message
    if IS_PRODUCTION and not include_details:
        return f"{operation.capitalize()} failed. Please try again or contact support if the problem persists."
    
    # In development, include the error details for debugging
    return f"{operation.capitalize()} failed: {str(error)}"


def get_safe_error_detail(
    error: Exception,
    default_message: str = "An internal error occurred"
) -> str:
    """
    Get a safe error detail for HTTPException.
    
    Args:
        error: The caught exception
        default_message: Default message to use in production
    
    Returns:
        str: Safe error message
    """
    if IS_PRODUCTION:
        return default_message
    return str(error)


class SafeHTTPException:
    """
    Helper class for creating safe HTTP exceptions.
    Usage: raise SafeHTTPException.internal_error("Failed to process request", e)
    """
    
    @staticmethod
    def internal_error(operation: str, error: Exception, status_code: int = 500):
        """Create a safe 500 Internal Server Error"""
        from fastapi import HTTPException
        
        logger.error(f"{operation} failed: {str(error)}", exc_info=True)
        
        detail = (
            f"{operation} failed. Please try again later."
            if IS_PRODUCTION
            else f"{operation} failed: {str(error)}"
        )
        
        return HTTPException(status_code=status_code, detail=detail)
    
    @staticmethod
    def bad_request(message: str, error: Optional[Exception] = None):
        """Create a 400 Bad Request error"""
        from fastapi import HTTPException
        
        if error:
            logger.warning(f"Bad request: {message} - {str(error)}")
        
        return HTTPException(status_code=400, detail=message)
    
    @staticmethod
    def not_found(resource: str, resource_id: str = None):
        """Create a 404 Not Found error"""
        from fastapi import HTTPException
        
        detail = f"{resource} not found"
        if resource_id and not IS_PRODUCTION:
            detail = f"{resource} with ID '{resource_id}' not found"
        
        return HTTPException(status_code=404, detail=detail)
    
    @staticmethod
    def unauthorized(message: str = "Authentication required"):
        """Create a 401 Unauthorized error"""
        from fastapi import HTTPException
        return HTTPException(status_code=401, detail=message)
    
    @staticmethod
    def forbidden(message: str = "Access denied"):
        """Create a 403 Forbidden error"""
        from fastapi import HTTPException
        return HTTPException(status_code=403, detail=message)
