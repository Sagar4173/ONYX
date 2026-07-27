"""
Email Templates Package
Provides modular, maintainable email templates for the platform
"""

from .base_template import GRADIENTS, SEVERITY_COLORS, get_base_template
from .template_registry import EmailTemplateLoader, get_jinja_environment, get_template_loader

__all__ = [
    'EmailTemplateLoader',
    'get_template_loader',
    'get_jinja_environment',
    'get_base_template',
    'SEVERITY_COLORS',
    'GRADIENTS'
]
