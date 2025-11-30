# Backend Environment Configuration

This directory contains the backend environment configuration files for the ONYX Platform.

## 🚀 Quick Setup

```bash
# Copy the example file
cp .env.example .env

# Generate a secret key
openssl rand -hex 32

# Edit the configuration
nano .env
```

## 📁 Environment Files

| File           | Purpose                                       |
| -------------- | --------------------------------------------- |
| `.env.example` | Template with all available options           |
| `.env`         | Main configuration (create from .env.example) |

## 🔑 Required Variables

### Must Configure

- `SECRET_KEY` - JWT signing key (generate with `openssl rand -hex 32`)
- `MONGODB_URI` - MongoDB connection string

### Recommended

- `OPENAI_API_KEY` - For AI-powered security analysis
- `EMAIL_ENABLED` & SMTP settings - For notifications
- `CORS_ORIGINS` - Frontend URLs for CORS

## 🌍 Environment Configuration

Instead of multiple files, simply edit your `.env` values based on your environment:

### For Development

```bash
# Edit .env with these values
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=DEBUG
USE_MOCK_SCANNERS=true
MONGODB_URI=mongodb://localhost:27017/onyx_dev
```

### For Production

```bash
# Edit .env with these values
DEBUG=false
ENVIRONMENT=production
LOG_LEVEL=WARNING
USE_MOCK_SCANNERS=false
FORCE_HTTPS=true
# Update all URLs and credentials!
```

## 📚 Documentation

For detailed configuration instructions, see [../docs/ENVIRONMENT_SETUP.md](../docs/ENVIRONMENT_SETUP.md)

## ⚠️ Security

- The `.env` files are git-ignored for security
- Never commit sensitive credentials
- Use strong, unique secret keys
- Review all settings before deployment
