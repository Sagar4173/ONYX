"""
Email Service for SecureDevOps AI Platform
DEPRECATED: This file is maintained for backward compatibility only.

The email service has been refactored into a modular structure.
New code should import from services.email package instead:
    from services.email import email_service

Module Structure:
- services/email/service.py - Main EmailService implementation
- services/email/templates/ - Modular template components
  - base_template.py - Base HTML template and styling
  - auth_templates.py - Authentication email templates
  - security_templates.py - Security email templates
  - template_registry.py - Centralized template management

Benefits of the new structure:
✅ Modular and maintainable
✅ Easy to add new templates
✅ Separated concerns (base styles, auth, security)
✅ Better testability
✅ Consistent styling across all emails
"""

# Import from new modular structure for backward compatibility
from .email import EmailService, email_service

# Re-export for backward compatibility
__all__ = ['EmailService', 'email_service']
