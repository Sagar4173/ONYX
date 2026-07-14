"""
Email Template Registry
Centralized template management for all email templates
"""

from jinja2 import Environment, BaseLoader, TemplateNotFound
from .auth_templates import (
    get_verification_template,
    get_password_reset_template,
    get_welcome_template,
    get_login_alert_template,
    get_2fa_enabled_template,
    get_2fa_disabled_template,
    get_2fa_recovery_used_template,
    get_password_changed_template
)
from .security_templates import (
    get_scan_completed_template,
    get_security_alert_template,
    get_new_vulnerability_template,
    get_weekly_digest_template,
    get_scan_report_attachment_template,
    get_scan_report_email_template
)


class EmailTemplateLoader(BaseLoader):
    """
    Custom Jinja2 template loader for email templates
    Provides centralized access to all email templates
    """
    
    def __init__(self):
        """Initialize template registry with all available templates"""
        self.templates = {
            # Authentication templates
            'verification': get_verification_template(),
            'password_reset': get_password_reset_template(),
            'welcome': get_welcome_template(),
            'login_alert': get_login_alert_template(),
            '2fa_enabled': get_2fa_enabled_template(),
            '2fa_disabled': get_2fa_disabled_template(),
            '2fa_recovery_used': get_2fa_recovery_used_template(),
            'password_changed': get_password_changed_template(),
            
            # Security templates
            'scan_completed': get_scan_completed_template(),
            'security_alert': get_security_alert_template(),
            'new_vulnerability': get_new_vulnerability_template(),
            'weekly_digest': get_weekly_digest_template(),
            'scan_report_attachment': get_scan_report_attachment_template(),
            'scan_report_email': get_scan_report_email_template()
        }
    
    def get_source(self, environment, template):
        """
        Retrieve template source for Jinja2
        
        Args:
            environment: Jinja2 environment
            template: Template name to retrieve
            
        Returns:
            Tuple of (source, filename, uptodate_func)
            
        Raises:
            TemplateNotFound: If template doesn't exist
        """
        if template not in self.templates:
            raise TemplateNotFound(template)
        
        source = self.templates[template]
        return source, None, lambda: True
    
    def list_templates(self):
        """
        List all available template names
        
        Returns:
            List of template names
        """
        return sorted(self.templates.keys())
    
    def add_template(self, name: str, template_content: str):
        """
        Add a custom template dynamically
        
        Args:
            name: Template name
            template_content: HTML template content
        """
        self.templates[name] = template_content
    
    def remove_template(self, name: str):
        """
        Remove a template from registry
        
        Args:
            name: Template name to remove
        """
        if name in self.templates:
            del self.templates[name]


def get_template_loader() -> EmailTemplateLoader:
    """
    Factory function to create template loader instance
    
    Returns:
        EmailTemplateLoader instance
    """
    return EmailTemplateLoader()


def get_jinja_environment() -> Environment:
    """
    Create configured Jinja2 environment with email templates
    
    Returns:
        Configured Jinja2 Environment
    """
    return Environment(loader=get_template_loader())
