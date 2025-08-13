# Environment Configuration Guide

This guide explains how to configure environment variables for the SecureDevOps AI Platform.

## 📁 Environment Files Overview

| File                    | Purpose                                     | Use Case                                  |
| ----------------------- | ------------------------------------------- | ----------------------------------------- |
| `backend/.env.example`  | Backend template with all available options | Copy this to create your `.env`           |
| `backend/.env`          | Main backend configuration                  | Your actual config (created from example) |
| `frontend/.env.example` | Frontend template                           | Copy this to create your `.env`           |
| `frontend/.env`         | Frontend configuration                      | Your actual frontend config               |

## 🚀 Quick Start

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Copy the main environment file
cp .env.example .env

# Edit the configuration
nano .env
```

**Required Variables (Must be configured):**

- `SECRET_KEY` - Generate with: `openssl rand -hex 32`
- `MONGODB_URI` - Your MongoDB connection string

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Copy the frontend environment file
cp .env.example .env

# Edit the configuration
nano .env
```

**Required Variables:**

- `VITE_API_URL` - Your backend API URL

## 🔧 Configuration Categories

### 🏗️ Application Settings

- `DEBUG` - Enable debug mode (true/false)
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8000)
- `ENVIRONMENT` - Environment type (development/staging/production)

### 🌐 URL Configuration

- `BACKEND_URL` - Backend API URL
- `FRONTEND_URL` - Frontend application URL
- `WEBSOCKET_URL` - WebSocket connection URL

### 🗄️ Database

- `MONGODB_URI` - MongoDB connection string
- `DATABASE_NAME` - Database name (default: securedevops)

### 🔐 Security

- `SECRET_KEY` - JWT signing key (required)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time
- `FORCE_HTTPS` - Force HTTPS in production

### 🤖 AI Integration

- `OPENAI_API_KEY` - OpenAI API key for AI features
- `OPENAI_MODEL` - AI model to use (gpt-4/gpt-3.5-turbo)

### 📧 Email

- `EMAIL_ENABLED` - Enable email functionality
- `SMTP_SERVER` - SMTP server address
- `SMTP_USERNAME` - SMTP username
- `SMTP_PASSWORD` - SMTP password

### 🔍 Security Scanners

- `ENABLE_SEMGREP` - Enable Semgrep scanner
- `ENABLE_TRIVY` - Enable Trivy scanner
- `ENABLE_GITLEAKS` - Enable GitLeaks scanner

## 🌍 Environment-Specific Configuration

Instead of multiple files, use a single `.env` file and change values based on your environment:

### For Development

```bash
# In your .env file
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=DEBUG
MONGODB_URI=mongodb://localhost:27017/securedevops_dev
USE_MOCK_SCANNERS=true
```

### For Production

```bash
# In your .env file
DEBUG=false
ENVIRONMENT=production
LOG_LEVEL=WARNING
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/securedevops
USE_MOCK_SCANNERS=false
FORCE_HTTPS=true
```

## 🔑 Security Best Practices

### 1. Secret Key Generation

```bash
# Generate a secure secret key
openssl rand -hex 32
```

### 2. Environment File Security

```bash
# Ensure .env files are not tracked by git
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
echo ".env.production" >> .gitignore
```

### 3. MongoDB Security

- Use strong passwords
- Enable authentication
- Use SSL/TLS connections
- Restrict network access

### 4. Production Checklist

- [ ] Generate secure `SECRET_KEY`
- [ ] Use strong MongoDB credentials
- [ ] Configure HTTPS (`FORCE_HTTPS=true`)
- [ ] Set up email provider
- [ ] Configure monitoring/notifications
- [ ] Restrict user registration
- [ ] Enable email verification
- [ ] Set appropriate rate limits

## 🔌 Service Integrations

### MongoDB Atlas

```env
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/securedevops
```

### Gmail SMTP

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Slack Notifications

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
SLACK_CHANNEL=#security-alerts
```

### Redis (Optional)

```env
REDIS_URL=redis://localhost:6379
REDIS_DB=0
```

## 🐳 Docker Configuration

When using Docker, you can pass environment variables:

```bash
# Using docker-compose
docker-compose --env-file .env up

# Using docker run
docker run --env-file .env your-app
```

## 🔄 Frontend Environment Variables

All frontend variables must be prefixed with `VITE_`:

```env
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# Feature Flags
VITE_DEMO_MODE=false
VITE_DEBUG=true
```

## 🆘 Troubleshooting

### Common Issues

1. **"SECRET_KEY not set" error**

   - Ensure you've generated and set a `SECRET_KEY`

2. **MongoDB connection failed**

   - Check `MONGODB_URI` format
   - Verify database credentials
   - Ensure MongoDB is running

3. **CORS errors in frontend**

   - Add frontend URL to `CORS_ORIGINS`
   - Check `VITE_API_URL` configuration

4. **Email not working**
   - Set `EMAIL_ENABLED=true`
   - Configure SMTP settings
   - Use app passwords for Gmail

### Environment Variable Validation

The application validates required environment variables on startup. Check logs for missing or invalid configurations.

## 📚 Additional Resources

- [MongoDB Connection Strings](https://docs.mongodb.com/manual/reference/connection-string/)
- [OpenAI API Keys](https://platform.openai.com/api-keys)
- [Slack Webhooks](https://api.slack.com/messaging/webhooks)
- [Gmail App Passwords](https://support.google.com/accounts/answer/185833)

## 🤝 Support

If you need help with environment configuration:

1. Check the example files
2. Review the troubleshooting section
3. Open an issue on GitHub
4. Contact the development team
