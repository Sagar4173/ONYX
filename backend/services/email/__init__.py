"""
Email Service Package
Provides email functionality for the ONYX Security Intelligence Platform

This module has been refactored for better maintainability:
- templates/ - Modular email template components
  - base_template.py - Base HTML template and styling
  - auth_templates.py - Authentication-related emails
  - security_templates.py - Security alerts and scan results
  - template_registry.py - Centralized template management
- service.py - Main email service implementation
"""

from .service import EmailService, email_service

__all__ = ['EmailService', 'email_service']
