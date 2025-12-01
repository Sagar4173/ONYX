"""
Email Service for ONYX Security Intelligence Platform
Backward compatibility module - imports from service.py

The main implementation is in service.py
"""

# Import from main service module for backward compatibility
from .service import EmailService, email_service

# Re-export for backward compatibility
__all__ = ['EmailService', 'email_service']
