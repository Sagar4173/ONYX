# Email Service Documentation

## Overview

The email service has been refactored into a modular, maintainable component structure. This design separates concerns, improves code organization, and makes it easier to add new email templates and features.

## Directory Structure

```
services/email/
├── __init__.py                    # Package exports
├── service.py                     # Main EmailService class
└── templates/                     # Email template components
    ├── __init__.py               # Template package exports
    ├── base_template.py          # Base HTML template & styling
    ├── auth_templates.py         # Authentication email templates
    ├── security_templates.py     # Security email templates
    └── template_registry.py      # Centralized template management
```

## Components

### 1. Base Template (`base_template.py`)

Provides the foundation for all email templates:

- **`get_base_template()`** - Creates consistent HTML structure
- **`BASE_STYLES`** - Common CSS styles
- **`SEVERITY_COLORS`** - Color constants for severity levels
- **`GRADIENTS`** - Reusable gradient patterns

### 2. Authentication Templates (`auth_templates.py`)

Handles user authentication and account security emails:

- Email Verification
- Password Reset
- Welcome Email
- Login Alerts
- 2FA Enabled/Disabled
- Recovery Code Used
- Password Changed

### 3. Security Templates (`security_templates.py`)

Manages security-related notifications:

- Scan Completed
- Security Alerts
- New Vulnerabilities
- Weekly Security Digest

### 4. Template Registry (`template_registry.py`)

Centralized template management:

- **`EmailTemplateLoader`** - Custom Jinja2 loader
- **`get_template_loader()`** - Factory function
- **`get_jinja_environment()`** - Configured Jinja2 environment

### 5. Email Service (`service.py`)

Main service implementation with SMTP support:

- Multiple provider support (Gmail, Outlook, Yahoo, SendGrid)
- Async email sending
- Template rendering
- Attachment handling
- Connection testing

## Usage

### Basic Usage

```python
from services.email import email_service

# Send verification email
await email_service.send_verification_email(
    email="user@example.com",
    verification_token="abc123"
)

# Send scan completed notification
await email_service.send_scan_completed_email(
    email="user@example.com",
    project_name="My Project",
    scan_type="SAST",
    critical_count=2,
    high_count=5,
    medium_count=10,
    low_count=3
)
```

### Adding New Templates

1. **Create template function** in appropriate file:

```python
# In auth_templates.py or security_templates.py
def get_my_new_template() -> str:
    return get_base_template(
        title="My Email",
        header_gradient=GRADIENTS["blue"],
        header_icon="🎉",
        header_subtitle="Subtitle Here",
        content='''
        <h2>Your content here...</h2>
        ''',
        footer_text="Optional footer message"
    )
```

2. **Register in template_registry.py**:

```python
# In EmailTemplateLoader.__init__
self.templates = {
    # ... existing templates
    'my_new_template': get_my_new_template()
}
```

3. **Add method to EmailService**:

```python
# In service.py
async def send_my_email(self, email: str, ...params) -> bool:
    template = self.jinja_env.get_template('my_new_template')
    html_body = template.render(**params)
    return await self.send_email(to_email=email, ...)
```

## Benefits

### ✅ Modularity

- Separate files for different template categories
- Easy to locate and modify specific templates
- Reduced file size and complexity

### ✅ Maintainability

- Clear separation of concerns
- Consistent structure across templates
- Easier to test individual components

### ✅ Extensibility

- Simple to add new templates
- Reusable components (base template, colors, gradients)
- Template inheritance through base template

### ✅ Consistency

- Unified styling across all emails
- Centralized color and gradient management
- Consistent header/footer structure

### ✅ Developer Experience

- Clear documentation
- Intuitive directory structure
- Type hints and docstrings

## Migration Guide

### Old Code (Deprecated)

```python
from services.email_service import email_service
```

### New Code (Recommended)

```python
from services.email import email_service
```

The old import path still works for backward compatibility, but new code should use the new package structure.

## Configuration

Email service configuration is managed through environment variables:

```env
# Email Provider (gmail, outlook, yahoo, sendgrid, or custom)
EMAIL_PROVIDER=gmail

# SMTP Settings (for custom provider)
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-password

# Sender Info
EMAIL_FROM=noreply@example.com
EMAIL_FROM_NAME=SecureDevOps Platform

# Frontend URL (for email links)
FRONTEND_URL=https://yourapp.com

# Enable/Disable emails
EMAIL_ENABLED=true
```

## Template Variables

### Common Variables

- `platform_name` - Platform name
- `user_name` - User's name
- Various URLs for actions

### Security Variables

- `severity` - Vulnerability severity
- `severity_color` - Color for severity badge
- `project_name` - Project name
- `file_path` - File path
- `vulnerability_type` - Type of vulnerability

### Statistics Variables

- `critical_count`, `high_count`, `medium_count`, `low_count`
- `total_scans`, `total_vulnerabilities`, `resolved_count`
- Various percentages for charts

## Testing

```python
# Test SMTP connection
await email_service.test_connection()

# Test template rendering
template = email_service.jinja_env.get_template('verification')
html = template.render(verification_url="https://example.com/verify")
```

## Best Practices

1. **Use appropriate template category**

   - Auth templates for user account operations
   - Security templates for vulnerability notifications

2. **Maintain consistent styling**

   - Use predefined colors and gradients
   - Follow existing template structure

3. **Include clear CTAs**

   - Primary action buttons should be prominent
   - Use descriptive button text

4. **Provide context**

   - Include relevant details in emails
   - Add helpful links and next steps

5. **Test thoroughly**
   - Test email rendering across clients
   - Verify all template variables
   - Check link functionality

## Support

For issues or questions about the email service, refer to:

- Main documentation: `/docs/`
- Email setup guide: `/docs/EMAIL_SETUP.md`
- Project structure: `/docs/PROJECT_STRUCTURE.md`
