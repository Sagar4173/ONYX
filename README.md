# 🛡️ SecureDevOps AI Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangion.com/)

An intelligent, comprehensive security scanning and DevOps automation platform that integrates multiple security tools with AI-powered analysis to provide actionable insights for your development workflow.

![SecureDevOps Platform Dashboard](docs/images/dashboard.png)

## 🌟 Features

### 🔍 **Multi-Layered Security Scanning**

- **Static Code Analysis** with Semgrep - Detect security vulnerabilities, bugs, and anti-patterns
- **Container Security** with Trivy - Scan Docker images for vulnerabilities and misconfigurations
- **Secret Detection** with GitLeaks - Find exposed API keys, passwords, and sensitive data
- **System Security** with Lynis - Comprehensive security auditing for infrastructure

### 🤖 **AI-Powered Analysis**

- **Intelligent Vulnerability Assessment** using OpenAI GPT-4
- **Risk Prioritization** with context-aware scoring
- **Automated Remediation Suggestions** with code examples
- **False Positive Reduction** through intelligent filtering

### 📊 **Comprehensive Reporting**

- **Real-time Dashboards** with interactive visualizations
- **Compliance Reports** (OWASP, CIS, PCI DSS, SOX)
- **Executive Summaries** with business impact analysis
- **Trend Analysis** and security posture tracking
- **Export Capabilities** (PDF, JSON, CSV)

### 🔗 **Seamless Integrations**

- **Git Webhooks** for automatic scanning on commits/PRs
- **Slack & Microsoft Teams** notifications
- **REST API** for custom integrations
- **WebSocket** real-time updates

### 🚀 **Enterprise Ready**

- **Scalable Architecture** with Docker and Kubernetes support
- **High Availability** with load balancing and clustering
- **Audit Logging** with comprehensive security trails
- **Role-Based Access Control** (planned)
- **SSO Integration** (planned)

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Web UI │    │  FastAPI Backend│    │   MongoDB DB    │
│                 │◄──►│                 │◄──►│                 │
│  • Dashboard    │    │  • REST API     │    │  • Reports      │
│  • Reports      │    │  • WebSockets   │    │  • Configs      │
│  • Settings     │    │  • AI Analysis  │    │  • Audit Logs   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ Security Tools  │
                       │                 │
                       │  • Semgrep      │
                       │  • Trivy        │
                       │  • GitLeaks     │
                       │  • Lynis        │
                       └─────────────────┘
```

## 🛠️ Tech Stack

### **Backend**

- **FastAPI** - Modern, fast Python web framework
- **Python 3.11** - Latest Python with enhanced performance
- **Motor** - Async MongoDB driver
- **Beanie** - Async ODM for MongoDB
- **Gunicorn + Uvicorn** - Production ASGI server
- **Structlog** - Structured logging
- **SlowAPI** - Rate limiting middleware

### **Frontend**

- **React 18** - Modern React with concurrent features
- **Vite** - Next-generation frontend build tool
- **Tailwind CSS** - Utility-first CSS framework
- **Headless UI** - Unstyled, accessible UI components
- **React Query** - Data fetching and caching
- **Recharts** - Composable charting library
- **React Router** - Client-side routing

### **Database & Caching**

- **MongoDB 7.0** - Document database with advanced indexing
- **Redis 7** - In-memory data structure store for caching

### **Security Tools**

- **Semgrep** - Static analysis for security vulnerabilities
- **Trivy** - Container security scanner
- **GitLeaks** - Secret detection tool
- **Lynis** - Security auditing tool

### **Infrastructure**

- **Docker** - Containerization platform
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Reverse proxy and static file serving
- **Prometheus** - Metrics collection (production)
- **Grafana** - Monitoring dashboards (production)

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (version 20.10 or later)
- **Docker Compose** (version 2.0 or later)
- **Git** (for cloning the repository)

### System Requirements

- **CPU**: 2+ cores recommended
- **Memory**: 4GB+ RAM (8GB recommended for production)
- **Disk**: 10GB+ free space
- **Network**: Internet connection for pulling images and AI services

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/securedevops-platform.git
cd securedevops-platform
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit the configuration
nano .env  # or your preferred editor
```

**Required Configuration:**

```bash
# OpenAI API Key (required for AI analysis)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Security
SECRET_KEY=your-super-secret-key-change-in-production

# Database
MONGO_PASSWORD=your-secure-mongo-password
```

### 3. Deploy with Docker Compose

#### **For Development:**

```bash
# Linux/macOS
./deploy.sh deploy

# Windows PowerShell
.\deploy.ps1
```

#### **Manual Deployment:**

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 4. Access the Platform

- **Web Interface**: http://localhost
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📖 Installation Guide

### Development Setup

1. **Clone and Navigate**

   ```bash
   git clone https://github.com/yourusername/securedevops-platform.git
   cd securedevops-platform
   ```

2. **Environment Configuration**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your settings:

   ```bash
   # Required
   OPENAI_API_KEY=sk-your-api-key
   SECRET_KEY=generate-a-secure-key
   MONGO_PASSWORD=secure-password

   # Optional
   SLACK_WEBHOOK_URL=https://hooks.slack.com/...
   TEAMS_WEBHOOK_URL=https://outlook.office.com/...
   ```

3. **Start Development Environment**

   ```bash
   # Use development overrides for hot reload
   docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
   ```

4. **Verify Installation**

   ```bash
   # Check all services are running
   docker-compose ps

   # Test the API
   curl http://localhost:8000/health
   ```

### Production Setup

1. **Prepare Production Environment**

   ```bash
   # Use production configuration
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

2. **Configure SSL (Recommended)**

   ```bash
   # Place your SSL certificates in ./ssl/
   mkdir -p ssl
   cp your-cert.pem ssl/
   cp your-key.pem ssl/
   ```

3. **Setup Monitoring** (Optional)
   ```bash
   # Enable Prometheus and Grafana
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.monitoring.yml up -d
   ```

## ⚙️ Configuration

### Environment Variables

| Variable                | Description                    | Default            | Required |
| ----------------------- | ------------------------------ | ------------------ | -------- |
| `OPENAI_API_KEY`        | OpenAI API key for AI analysis | -                  | ✅       |
| `SECRET_KEY`            | JWT signing key                | -                  | ✅       |
| `MONGO_PASSWORD`        | MongoDB admin password         | `securepass123`    | ✅       |
| `MONGODB_URI`           | MongoDB connection string      | Auto-generated     | ❌       |
| `REDIS_PASSWORD`        | Redis password                 | `redispass123`     | ❌       |
| `ALLOWED_ORIGINS`       | CORS allowed origins           | `http://localhost` | ❌       |
| `ENVIRONMENT`           | Runtime environment            | `development`      | ❌       |
| `LOG_LEVEL`             | Logging level                  | `INFO`             | ❌       |
| `RATE_LIMIT_PER_MINUTE` | API rate limit                 | `100`              | ❌       |

### Security Configuration

```bash
# Security Settings
SECRET_KEY=your-256-bit-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# HTTPS (Production)
FORCE_HTTPS=true
SSL_CERT_PATH=/ssl/cert.pem
SSL_KEY_PATH=/ssl/key.pem

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_BURST=20
```

### Notification Configuration

```bash
# Slack Integration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
SLACK_CHANNEL=#security-alerts

# Microsoft Teams Integration
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/YOUR/TEAMS/WEBHOOK

# Email Notifications (Future)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## 🔧 Usage

### Webhook Integration

1. **Configure Repository Webhook**

   ```
   URL: https://your-domain.com/webhook/github
   Content-Type: application/json
   Events: push, pull_request
   ```

2. **Manual Scan via API**

   ```bash
   curl -X POST "http://localhost:8000/scan" \
     -H "Content-Type: application/json" \
     -d '{"repository_url": "https://github.com/user/repo.git"}'
   ```

3. **View Results**
   - Web UI: http://localhost/reports
   - API: http://localhost:8000/reports

### API Usage Examples

```python
import requests

# Get all reports
response = requests.get("http://localhost:8000/api/reports")
reports = response.json()

# Get specific report
report_id = "report-uuid"
response = requests.get(f"http://localhost:8000/api/reports/{report_id}")
report = response.json()

# Trigger scan
payload = {
    "repository_url": "https://github.com/user/repo.git",
    "branch": "main",
    "scan_types": ["sast", "container", "secrets", "infrastructure"]
}
response = requests.post("http://localhost:8000/api/scan", json=payload)
```

## 🛡️ Security Best Practices

### Production Deployment Security

1. **Environment Security**

   ```bash
   # Use strong, unique passwords
   MONGO_PASSWORD=$(openssl rand -base64 32)
   REDIS_PASSWORD=$(openssl rand -base64 32)
   SECRET_KEY=$(openssl rand -hex 64)
   ```

2. **Network Security**

   ```bash
   # Firewall rules (example with ufw)
   sudo ufw allow 22    # SSH
   sudo ufw allow 80    # HTTP
   sudo ufw allow 443   # HTTPS
   sudo ufw deny 27017  # MongoDB (internal only)
   sudo ufw deny 6379   # Redis (internal only)
   sudo ufw deny 8000   # Backend API (internal only)
   ```

3. **SSL/TLS Configuration**

   ```yaml
   # docker-compose.prod.yml
   nginx:
     volumes:
       - ./ssl/cert.pem:/ssl/cert.pem:ro
       - ./ssl/key.pem:/ssl/key.pem:ro
     environment:
       - SSL_ENABLED=true
   ```

4. **Container Security**

   ```bash
   # Run containers as non-root
   # Enable Docker content trust
   export DOCKER_CONTENT_TRUST=1

   # Regular security updates
   docker-compose pull
   docker-compose up -d
   ```

### Data Protection

1. **Database Security**

   - Enable MongoDB authentication
   - Use encrypted connections
   - Regular backups with encryption
   - Implement data retention policies

2. **API Security**

   - Rate limiting enabled
   - CORS properly configured
   - Input validation and sanitization
   - Audit logging for all operations

3. **Secret Management**
   - Never commit secrets to version control
   - Use environment variables
   - Consider external secret management (HashiCorp Vault, AWS Secrets Manager)
   - Rotate secrets regularly

### Monitoring and Alerting

1. **Health Monitoring**

   ```bash
   # Check service health
   curl http://localhost:8000/health

   # Monitor container resources
   docker stats
   ```

2. **Log Monitoring**

   ```bash
   # Application logs
   docker-compose logs -f backend

   # Security events
   docker-compose logs -f | grep "SECURITY"
   ```

3. **Backup Strategy**

   ```bash
   # Automated daily backups
   ./deploy.sh backup

   # Restore from backup
   ./deploy.sh restore backup-2025-08-10.tar.gz
   ```

## 📊 Monitoring and Maintenance

### Health Checks

The platform includes comprehensive health checks:

```bash
# Overall platform health
curl http://localhost:8000/health

# Individual service health
docker-compose ps
docker-compose exec backend python -c "import asyncio; asyncio.run(check_health())"
```

### Backup and Recovery

```bash
# Create backup
./deploy.sh backup

# List backups
ls -la backups/

# Restore from backup
./deploy.sh restore backups/backup-2025-08-10.tar.gz
```

### Performance Tuning

1. **Database Optimization**

   ```javascript
   // MongoDB indexes (automatically created)
   db.scanreports.createIndex({ timestamp: -1 });
   db.scanreports.createIndex({ repository_url: 1, timestamp: -1 });
   db.scanreports.createIndex({ "findings.severity": 1 });
   ```

2. **Resource Limits**
   ```yaml
   # docker-compose.prod.yml
   services:
     backend:
       deploy:
         resources:
           limits:
             memory: 1G
             cpus: "0.5"
   ```

## 🐛 Troubleshooting

### Common Issues

1. **Services Won't Start**

   ```bash
   # Check logs
   docker-compose logs

   # Check system resources
   docker system df
   docker system prune  # Clean up if needed
   ```

2. **Database Connection Issues**

   ```bash
   # Verify MongoDB is running
   docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

   # Check environment variables
   docker-compose exec backend env | grep MONGO
   ```

3. **AI Analysis Not Working**

   ```bash
   # Verify OpenAI API key
   docker-compose exec backend python -c "
   import os
   print('API Key configured:', bool(os.getenv('OPENAI_API_KEY')))
   "
   ```

4. **Frontend Access Issues**

   ```bash
   # Check nginx configuration
   docker-compose exec frontend nginx -t

   # Verify build
   docker-compose logs frontend
   ```

### Performance Issues

1. **High Memory Usage**

   ```bash
   # Monitor resource usage
   docker stats

   # Adjust memory limits
   # Edit docker-compose.yml memory limits
   ```

2. **Slow Scans**

   ```bash
   # Check scanner health
   curl http://localhost:8000/health/scanners

   # Monitor scan queue
   curl http://localhost:8000/admin/queue-status
   ```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/securedevops-platform.git

# Create development environment
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

# Run tests
docker-compose exec backend pytest
docker-compose exec frontend npm test
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Security Tools**: Semgrep, Trivy, GitLeaks, Lynis
- **AI Provider**: OpenAI for GPT-4 analysis
- **Open Source Libraries**: FastAPI, React, MongoDB, and many others

## 📞 Support

- **Documentation**: [Full Documentation](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/securedevops-platform/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/securedevops-platform/discussions)
- **Security Issues**: security@yourdomain.com

---

**Made with ❤️ for the security community**

_Secure your code, automate your DevOps, and sleep better at night._
