# SecureDevOps AI Platform

A production-ready, AI-powered security scanning platform that automatically analyzes code repositories for vulnerabilities and provides intelligent remediation recommendations.

## 🚀 Features

- **Multi-Scanner Integration**: Semgrep, Trivy, GitLeaks, and Lynis
- **AI-Powered Analysis**: OpenAI GPT-4 integration for vulnerability analysis and secure code recommendations
- **Real-time WebSocket Updates**: Live scan progress and results
- **Webhook Support**: GitHub, GitLab, and Bitbucket integration
- **Smart Notifications**: Slack and Teams alerts
- **Comprehensive API**: RESTful API with detailed reporting
- **Production Ready**: Docker containerization with security best practices
- **Scalable Architecture**: Async processing with MongoDB storage

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Git Provider  │───▶│   Webhook API    │───▶│  Scanner Queue  │
│ (GitHub/GitLab) │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   WebSocket     │◀───│   FastAPI App    │    │  Security       │
│   Real-time     │    │                  │    │  Scanners       │
│   Updates       │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Notifications  │◀───│    MongoDB       │◀───│  AI Processor   │
│ (Slack/Teams)   │    │   Database       │    │  (OpenAI GPT-4) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

- **Backend**: FastAPI + Uvicorn + Gunicorn
- **Database**: MongoDB with Beanie ODM
- **Security Scanners**: Semgrep, Trivy, GitLeaks, Lynis
- **AI**: OpenAI GPT-4 API
- **Async Processing**: asyncio
- **WebSocket**: Real-time updates
- **Containerization**: Docker multi-stage builds
- **Monitoring**: Structured logging with rotation

## 📋 Prerequisites

- Docker and Docker Compose
- MongoDB (or use Docker container)
- OpenAI API key
- Python 3.11+ (for development)

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd SecureDevOps-Platform/backend
```

### 2. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your configuration
```

**Required Environment Variables:**

```bash
# Database
MONGODB_URI=mongodb://localhost:27017

# Security
SECRET_KEY=your-secret-key-here

# AI
OPENAI_API_KEY=your-openai-api-key

# Notifications (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...
```

### 3. Production Deployment

```bash
chmod +x deploy.sh
./deploy.sh
```

### 4. Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start MongoDB (if not using Docker)
# mongod --dbpath ./data

# Run development server
python app.py
```

## 📊 API Endpoints

### Webhook Endpoints

- `POST /webhook` - Receive Git webhooks
- `GET /webhook/events` - List webhook events
- `GET /webhook/events/{id}` - Get webhook event details

### Reports Endpoints

- `GET /reports` - List all scan reports
- `GET /reports/{id}` - Get detailed report
- `GET /reports/{id}/summary` - Get report summary
- `GET /reports/analytics/overview` - Analytics dashboard
- `GET /reports/project/{name}` - Project-specific reports

### System Endpoints

- `GET /health` - Health check
- `GET /metrics` - Basic metrics
- `WebSocket /ws` - Real-time updates

## 🔧 Configuration

### Scanner Configuration

The platform supports multiple security scanners:

```yaml
scanners:
  semgrep:
    enabled: true
    rules: auto # or custom rule sets
  trivy:
    enabled: true
    formats: [json]
  gitleaks:
    enabled: true
    config: default
  lynis:
    enabled: true
    quick_scan: true
```

### Notification Templates

Customize notification messages:

```python
# Slack notification example
{
  "text": "🔒 Security Scan Completed",
  "attachments": [
    {
      "color": "danger",  # or "warning", "good"
      "fields": [
        {"title": "Critical", "value": "5", "short": true},
        {"title": "High", "value": "12", "short": true}
      ]
    }
  ]
}
```

## 🐳 Docker Deployment

### Production Deployment

```bash
# Build and deploy
./deploy.sh

# Or manually:
docker build -t securedevops-platform .
docker run -d \
  --name securedevops-backend \
  -p 8000:8000 \
  --env-file .env \
  securedevops-platform
```

### Docker Compose (Alternative)

```yaml
version: "3.8"
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=mongodb://mongodb:27017/securedevops
    depends_on:
      - mongodb

  mongodb:
    image: mongo:7.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

## 🔒 Security Features

### Built-in Security

- **CORS Protection**: Configurable origins
- **Rate Limiting**: Requests per minute/hour
- **Security Headers**: XSS, CSRF, etc.
- **Input Validation**: Pydantic models
- **Non-root Container**: Principle of least privilege

### Scanner Integration

```python
# Example scan workflow
async def scan_repository(repo_url: str):
    # 1. Clone repository securely
    clone_info = await clone_repository(repo_url)

    # 2. Run security scanners
    scan_results = await run_security_scans(clone_info.path)

    # 3. AI analysis
    ai_analysis = await analyze_with_ai(scan_results)

    # 4. Generate report
    report = create_scan_report(scan_results, ai_analysis)

    # 5. Send notifications
    await send_notifications(report)

    return report
```

## 📈 Monitoring & Logging

### Structured Logging

```python
import structlog

logger = structlog.get_logger()
logger.info("Scan started", repo_url=repo_url, scan_id=scan_id)
logger.error("Scan failed", error=str(e), scan_id=scan_id)
```

### Health Checks

- **Database**: MongoDB connection
- **Scanners**: Tool availability
- **Disk Space**: Temporary storage
- **API**: Response times

### Metrics

```bash
# Health endpoint
curl http://localhost:8000/health

# Metrics endpoint
curl http://localhost:8000/metrics
```

## 🔗 Webhook Integration

### GitHub Webhook

```json
{
  "url": "https://your-domain.com/webhook",
  "content_type": "application/json",
  "events": ["push", "pull_request"],
  "active": true
}
```

### GitLab Webhook

```json
{
  "url": "https://your-domain.com/webhook",
  "push_events": true,
  "merge_requests_events": true
}
```

## 🤖 AI Integration

### OpenAI Configuration

```python
# AI analysis features
- Executive summaries
- Risk assessments
- Priority findings
- Secure code examples
- Compliance impact
- Fix time estimates
```

### Custom Prompts

```python
async def analyze_vulnerabilities(findings):
    prompt = f"""
    Analyze these security findings and provide:
    1. Risk assessment
    2. Remediation priority
    3. Secure code examples

    Findings: {findings}
    """
    return await openai_client.complete(prompt)
```

## 📋 Development

### Project Structure

```
backend/
├── app.py                 # Main FastAPI application
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container definition
├── deploy.sh           # Deployment script
├── models/
│   └── report.py       # MongoDB models
├── routes/
│   ├── webhook.py      # Webhook endpoints
│   └── reports.py      # Report endpoints
├── services/
│   ├── scanner.py      # Security scanners
│   ├── ai_processor.py # AI analysis
│   └── notifier.py     # Notifications
└── utils/
    ├── repo_clone.py   # Git operations
    └── result_parser.py # Result parsing
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/ -v

# Run with coverage
pytest --cov=. tests/
```

### Development Commands

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .

# Security scan
bandit -r .
```

## 🚀 Production Checklist

- [ ] Environment variables configured
- [ ] MongoDB secured and backed up
- [ ] SSL/TLS certificates configured
- [ ] Rate limiting configured
- [ ] Log rotation configured
- [ ] Monitoring set up
- [ ] Backup strategy implemented
- [ ] Security scanners updated
- [ ] AI API keys secured

## 📚 API Documentation

When running in development mode, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Troubleshooting

### Common Issues

1. **MongoDB Connection**

   ```bash
   # Check MongoDB status
   docker logs securedevops-mongodb
   ```

2. **Scanner Not Found**

   ```bash
   # Verify scanner installation
   docker exec securedevops-backend semgrep --version
   ```

3. **OpenAI API Errors**
   ```bash
   # Check API key
   echo $OPENAI_API_KEY
   ```

### Logs

```bash
# Application logs
docker logs -f securedevops-backend

# MongoDB logs
docker logs -f securedevops-mongodb
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Semgrep](https://semgrep.dev/) - Static analysis
- [Trivy](https://trivy.dev/) - Vulnerability scanning
- [GitLeaks](https://github.com/zricethezav/gitleaks) - Secret detection
- [Lynis](https://cisofy.com/lynis/) - Security auditing
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [OpenAI](https://openai.com/) - AI analysis
