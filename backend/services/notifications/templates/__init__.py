"""
Email Templates Package
Provides modular, maintainable email templates for the platform
"""

from .base_template import get_base_template, SEVERITY_COLORS, GRADIENTS
from .template_registry import EmailTemplateLoader, get_template_loader, get_jinja_environment

__all__ = [
    'EmailTemplateLoader',
    'get_template_loader',
    'get_jinja_environment',
    'get_base_template',
    'SEVERITY_COLORS',
    'GRADIENTS'
]
