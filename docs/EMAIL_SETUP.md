# Email Configuration Guide

The ONYX Platform now supports real email sending for user verification and password resets. This guide explains how to configure different email providers.

## Quick Setup

1. Copy the email configuration example:

   ```bash
   cp .env.email.example .env.local
   ```

2. Edit `.env.local` with your email provider settings

3. Restart the backend server

## Supported Email Providers

### Gmail (Recommended for Development)

```env
EMAIL_ENABLED=true
EMAIL_PROVIDER=gmail
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com
EMAIL_FROM_NAME="ONYX Platform"
```

**Setup Steps:**

1. Enable 2-Factor Authentication on your Google account
2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Generate an app password for "Mail"
4. Use your Gmail address as `SMTP_USERNAME` and `EMAIL_FROM`
5. Use the generated app password as `SMTP_PASSWORD`

### SendGrid (Recommended for Production)

```env
EMAIL_ENABLED=true
EMAIL_PROVIDER=sendgrid
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME="SecureDevOps Platform"
```

**Setup Steps:**

1. Create a [SendGrid account](https://sendgrid.com/)
2. Verify your sender identity (domain or single sender)
3. Generate an API key in Settings > API Keys
4. Use `apikey` as username and your API key as password

### Outlook/Hotmail

```env
EMAIL_ENABLED=true
EMAIL_PROVIDER=outlook
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-password
EMAIL_FROM=your-email@outlook.com
EMAIL_FROM_NAME="SecureDevOps Platform"
```

### Custom SMTP Server

```env
EMAIL_ENABLED=true
EMAIL_PROVIDER=custom
SMTP_SERVER=smtp.yourdomain.com
SMTP_PORT=587
SMTP_USERNAME=your-username
SMTP_PASSWORD=your-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME="SecureDevOps Platform"
```

## Environment Variables

| Variable          | Description                                               | Default                 | Required    |
| ----------------- | --------------------------------------------------------- | ----------------------- | ----------- |
| `EMAIL_ENABLED`   | Enable/disable email sending                              | `false`                 | Yes         |
| `EMAIL_PROVIDER`  | Provider preset (gmail, sendgrid, outlook, yahoo, custom) | -                       | Yes         |
| `SMTP_SERVER`     | SMTP server hostname                                      | Auto-set by provider    | Custom only |
| `SMTP_PORT`       | SMTP server port                                          | `587`                   | Custom only |
| `SMTP_USERNAME`   | SMTP username                                             | -                       | Yes         |
| `SMTP_PASSWORD`   | SMTP password/API key                                     | -                       | Yes         |
| `SMTP_USE_TLS`    | Use STARTTLS                                              | `true`                  | No          |
| `SMTP_USE_SSL`    | Use SSL/TLS connection                                    | `false`                 | No          |
| `EMAIL_FROM`      | Sender email address                                      | `SMTP_USERNAME`         | No          |
| `EMAIL_FROM_NAME` | Sender display name                                       | "SecureDevOps Platform" | No          |
| `FRONTEND_URL`    | Frontend URL for email links                              | `http://localhost:5173` | Yes         |

## Testing Email Configuration

1. Start the backend server with email configuration
2. Log in as an admin user
3. Go to User Profile → Account tab
4. Click "Send Test Email"
5. Check your inbox for the test email

## Email Templates

The system includes professional HTML email templates for:

- **Email Verification**: Welcome email with verification link
- **Password Reset**: Security-focused reset email
- **Test Email**: Simple test email for configuration verification

Templates are responsive and include:

- Modern design with gradients
- Platform branding
- Security notices
- Mobile-friendly layout
- Clear call-to-action buttons

## Troubleshooting

### Common Issues

1. **Authentication Failed**

   - Check username/password
   - For Gmail, ensure you're using an app password, not your regular password
   - Verify 2FA is enabled for Gmail

2. **Connection Timeout**

   - Check SMTP server and port
   - Verify firewall/network settings
   - Try different ports (587, 465, 25)

3. **TLS/SSL Errors**

   - Try toggling `SMTP_USE_TLS` and `SMTP_USE_SSL`
   - For Gmail, use TLS on port 587
   - For some providers, use SSL on port 465

4. **Emails Not Delivered**
   - Check spam/junk folders
   - Verify sender reputation
   - Use authenticated email services like SendGrid

### Debug Mode

Set log level to DEBUG to see detailed SMTP communication:

```python
import logging
logging.getLogger('aiosmtplib').setLevel(logging.DEBUG)
```

## Production Recommendations

1. **Use Professional Email Service**

   - SendGrid, Amazon SES, Mailgun, etc.
   - Better deliverability and reputation
   - Advanced analytics and monitoring

2. **Domain Authentication**

   - Set up SPF, DKIM, and DMARC records
   - Use a dedicated sending domain
   - Verify domain ownership

3. **Security**

   - Store credentials securely (environment variables, secrets manager)
   - Use API keys instead of passwords when possible
   - Enable rate limiting and monitoring

4. **Monitoring**
   - Track email delivery rates
   - Monitor bounce and complaint rates
   - Set up alerts for failures

## Example Production Configuration

```env
# Production SendGrid Configuration
EMAIL_ENABLED=true
EMAIL_PROVIDER=sendgrid
SMTP_USERNAME=apikey
SMTP_PASSWORD=${SENDGRID_API_KEY}
EMAIL_FROM=noreply@securedevops.com
EMAIL_FROM_NAME="SecureDevOps Platform"
FRONTEND_URL=https://app.securedevops.com
```

## API Integration

The email service is integrated with:

- User registration (verification emails)
- Password reset requests
- Account notifications
- Admin test emails

All emails are sent asynchronously and include proper error handling.
