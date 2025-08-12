# 🏗️ Architecture & Design

## Overview

SecureDevOps AI Platform is designed as a modern, scalable, and enterprise-ready security scanning platform that rivals GitHub Advanced Security (GHAS) and Snyk. The architecture follows microservices principles with clear separation of concerns.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SecureDevOps AI Platform                   │
├─────────────────────────────────────────────────────────────────┤
│  🌐 Frontend Layer (React 18 + Vite)                          │
│  ├── Modern Dark UI with Glassmorphism                         │
│  ├── Real-time WebSocket Updates                               │
│  ├── Interactive Charts & Analytics                            │
│  ├── Mobile-Responsive Design                                  │
│  └── Progressive Web App (PWA) Support                         │
├─────────────────────────────────────────────────────────────────┤
│  🔌 API Gateway Layer                                          │
│  ├── FastAPI with OpenAPI Documentation                        │
│  ├── JWT Authentication & Authorization                        │
│  ├── Rate Limiting & CORS                                      │
│  ├── Request/Response Validation                               │
│  └── API Versioning Support                                    │
├─────────────────────────────────────────────────────────────────┤
│  ⚙️ Business Logic Layer                                        │
│  ├── 🔍 Scan Orchestrator                                      │
│  ├── 🤖 AI Analysis Engine                                     │
│  ├── 📊 Report Generator                                       │
│  ├── 🔔 Notification Service                                   │
│  └── 📁 Repository Manager                                     │
├─────────────────────────────────────────────────────────────────┤
│  🛡️ Security Engine Layer                                      │
│  ├── 🔬 Semgrep (SAST)           ├── 📦 Trivy (Container)     │
│  ├── 🔐 GitLeaks (Secrets)       ├── 🏗️ Lynis (Infrastructure)│
│  ├── 🔍 Safety (Dependencies)    ├── 🎯 Bandit (Python SAST)  │
│  └── 🤖 AI Processor (GPT-4 Analysis & Recommendations)        │
├─────────────────────────────────────────────────────────────────┤
│  💾 Data Layer                                                 │
│  ├── MongoDB Atlas (Primary Database)                          │
│  ├── Redis (Caching & Sessions)                                │
│  ├── File Storage (Local/S3/Azure Blob)                        │
│  └── Search Engine (Elasticsearch - Optional)                  │
├─────────────────────────────────────────────────────────────────┤
│  🔗 Integration Layer                                           │
│  ├── Git Providers (GitHub, GitLab, Bitbucket)                 │
│  ├── Notification Systems (Slack, Teams, Email)                │
│  ├── CI/CD Systems (Jenkins, GitHub Actions, Azure DevOps)     │
│  └── External APIs (OpenAI, Security Feeds)                    │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### Frontend Architecture

**Technology Stack:**
- **React 18** with Concurrent Features
- **Vite** for fast development and building
- **Tailwind CSS** for utility-first styling
- **React Query** for state management and caching
- **WebSocket** for real-time updates
- **Chart.js/Recharts** for data visualization

**Key Components:**
```
frontend/src/
├── components/
│   ├── Dashboard/           # Main dashboard components
│   ├── Reports/             # Report viewing and analysis
│   ├── Settings/            # Configuration management
│   ├── Charts/              # Data visualization
│   └── Common/              # Reusable UI components
├── services/
│   ├── api.js              # API client configuration
│   ├── websocket.js        # Real-time communication
│   └── auth.js             # Authentication service
├── hooks/
│   ├── useAuth.js          # Authentication hooks
│   ├── useScanData.js      # Scan data management
│   └── useWebSocket.js     # WebSocket hooks
└── utils/
    ├── formatters.js       # Data formatting utilities
    ├── validators.js       # Input validation
    └── constants.js        # Application constants
```

### Backend Architecture

**Technology Stack:**
- **FastAPI** with async/await support
- **Python 3.11+** with type hints
- **Pydantic** for data validation
- **Motor** for async MongoDB operations
- **Beanie** ODM for document modeling
- **Structlog** for structured logging

**Service Architecture:**
```
backend/
├── app.py                  # FastAPI application entry point
├── config.py               # Configuration management
├── database.py             # Database connection and setup
├── models/
│   ├── report.py           # Scan report data models
│   ├── user.py             # User and authentication models
│   └── webhook.py          # Webhook event models
├── routes/
│   ├── auth.py             # Authentication endpoints
│   ├── reports.py          # Report management APIs
│   ├── webhook.py          # Webhook handlers
│   └── admin.py            # Administrative functions
├── services/
│   ├── scanner.py          # Security scanner orchestrator
│   ├── ai_processor.py     # AI analysis engine
│   ├── notifier.py         # Notification service
│   ├── real_scanner.py     # Real security tool integration
│   └── auth_service.py     # Authentication logic
├── utils/
│   ├── repo_clone.py       # Repository management
│   ├── result_parser.py    # Scan result processing
│   └── validators.py       # Data validation utilities
└── middleware/
    ├── auth.py             # Authentication middleware
    ├── rate_limit.py       # Rate limiting
    └── cors.py             # CORS configuration
```

### Security Engine

**Scanner Integration:**
```python
class SecurityScanner:
    """Main security scanner orchestrator"""
    
    def __init__(self):
        self.scanners = {
            ScannerType.SEMGREP: SemgrepScanner(),      # SAST
            ScannerType.TRIVY: TrivyScanner(),          # Container
            ScannerType.GITLEAKS: GitLeaksScanner(),    # Secrets
            ScannerType.LYNIS: LynisScanner(),          # Infrastructure
            ScannerType.SAFETY: SafetyScanner(),        # Dependencies
            ScannerType.BANDIT: BanditScanner()         # Python SAST
        }
    
    async def run_all_scans(self, repo_path: str) -> List[ScanResult]:
        """Execute all security scanners in parallel"""
        tasks = [
            scanner.scan(repo_path) 
            for scanner in self.scanners.values()
        ]
        return await asyncio.gather(*tasks)
```

**AI Analysis Engine:**
```python
class VulnerabilityAIProcessor:
    """AI processor for vulnerability analysis"""
    
    async def analyze_scan_results(
        self, 
        scan_results: List[ScanResult]
    ) -> AIAnalysis:
        """Generate comprehensive AI analysis"""
        
        # Parallel AI analysis tasks
        analysis_tasks = [
            self._generate_executive_summary(findings_data),
            self._generate_risk_assessment(findings_data),
            self._generate_priority_findings(findings_data),
            self._generate_recommendations(findings_data),
            self._generate_secure_code_examples(findings_data),
            self._generate_compliance_impact(findings_data)
        ]
        
        results = await asyncio.gather(*analysis_tasks)
        
        return AIAnalysis(
            model_used="gpt-4",
            executive_summary=results[0],
            risk_assessment=results[1],
            priority_findings=results[2],
            recommendations=results[3],
            secure_code_examples=results[4],
            compliance_impact=results[5]
        )
```

### Data Models

**Scan Report Model:**
```python
class ScanReport(Document):
    """Comprehensive scan report document"""
    
    # Basic Information
    scan_id: str = Field(..., unique=True)
    project_name: str
    status: ScanStatus
    
    # Timestamps
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    
    # Git Information
    git_metadata: GitMetadata
    
    # Scan Results
    scan_results: List[ScanResult] = []
    total_findings: int = 0
    findings_by_severity: Dict[str, int] = {}
    
    # AI Analysis
    ai_analysis: Optional[AIAnalysis]
    
    # Metadata
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    
    class Settings:
        name = "scan_reports"
        indexes = [
            "scan_id",
            "project_name",
            "status",
            "created_at",
            [("project_name", 1), ("created_at", -1)]
        ]
```

**AI Analysis Model:**
```python
class AIAnalysis(BaseModel):
    """AI-generated analysis and recommendations"""
    
    model_used: str
    generated_at: datetime
    
    # Analysis Results
    executive_summary: str
    risk_assessment: str
    priority_findings: List[str]
    recommendations: List[str]
    secure_code_examples: Dict[str, str]
    compliance_impact: Dict[str, str]
    estimated_fix_time: str
    
    # Quality Metrics
    confidence_score: Optional[float]
    analysis_duration: Optional[float]
```

## Security Architecture

### Authentication & Authorization

```python
class AuthenticationService:
    """JWT-based authentication service"""
    
    async def authenticate_user(
        self, 
        token: str
    ) -> Optional[User]:
        """Validate JWT token and return user"""
        try:
            payload = jwt.decode(
                token, 
                settings.secret_key, 
                algorithms=[settings.algorithm]
            )
            user_id = payload.get("sub")
            if user_id:
                return await User.get(user_id)
        except JWTError:
            return None
```

### Rate Limiting

```python
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    
    client_ip = request.client.host
    
    # Check rate limit
    if await rate_limiter.is_rate_limited(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )
    
    response = await call_next(request)
    return response
```

### Data Encryption

```python
class EncryptionService:
    """Data encryption and decryption service"""
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data before storage"""
        cipher = Fernet(settings.encryption_key)
        return cipher.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data after retrieval"""
        cipher = Fernet(settings.encryption_key)
        return cipher.decrypt(encrypted_data.encode()).decode()
```

## Scalability & Performance

### Async Processing

```python
@app.post("/webhook/scan")
async def submit_scan(scan_request: ScanRequest):
    """Async scan submission"""
    
    # Create scan record immediately
    scan_report = await ScanReport.create(scan_request)
    
    # Process scan in background
    asyncio.create_task(
        process_scan_background(scan_report.scan_id)
    )
    
    return {"scan_id": scan_report.scan_id, "status": "submitted"}

async def process_scan_background(scan_id: str):
    """Background scan processing"""
    try:
        # Run security scanners
        scan_results = await security_scanner.run_all_scans(repo_path)
        
        # Generate AI analysis
        ai_analysis = await ai_processor.analyze_scan_results(scan_results)
        
        # Update scan report
        await ScanReport.find_one(
            ScanReport.scan_id == scan_id
        ).update({"$set": {
            "scan_results": scan_results,
            "ai_analysis": ai_analysis,
            "status": ScanStatus.COMPLETED
        }})
        
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        await mark_scan_failed(scan_id, str(e))
```

### Database Optimization

```python
# MongoDB Indexes for Performance
class ScanReport(Document):
    class Settings:
        indexes = [
            # Single field indexes
            "scan_id",
            "project_name", 
            "status",
            "created_at",
            
            # Compound indexes
            [("project_name", 1), ("created_at", -1)],
            [("status", 1), ("created_at", -1)],
            [("total_findings", -1), ("created_at", -1)],
            
            # Text search index
            [("project_name", "text"), ("git_metadata.commit_message", "text")]
        ]
```

### Caching Strategy

```python
from redis import asyncio as aioredis

class CacheService:
    """Redis-based caching service"""
    
    async def get_scan_cache(self, cache_key: str) -> Optional[dict]:
        """Get cached scan results"""
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        return None
    
    async def set_scan_cache(
        self, 
        cache_key: str, 
        data: dict, 
        expire: int = 3600
    ):
        """Cache scan results"""
        await self.redis.setex(
            cache_key, 
            expire, 
            json.dumps(data, default=str)
        )
```

## Deployment Architecture

### Container Architecture

```dockerfile
# Multi-stage Docker build
FROM python:3.11-slim as backend-builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM node:18-alpine as frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM python:3.11-slim as production
# Copy backend and frontend builds
COPY --from=backend-builder /app /app
COPY --from=frontend-builder /app/dist /app/static
EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app:app"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: securedevops-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: securedevops
  template:
    metadata:
      labels:
        app: securedevops
    spec:
      containers:
      - name: backend
        image: securedevops/platform:latest
        env:
        - name: MONGODB_URI
          valueFrom:
            secretKeyRef:
              name: securedevops-secrets
              key: mongodb-uri
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: securedevops-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## Monitoring & Observability

### Health Checks

```python
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Database connectivity
    try:
        await db_manager.ping()
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {e}"
        health_status["status"] = "unhealthy"
    
    # Security scanners
    for scanner_type, scanner in security_scanner.scanners.items():
        try:
            is_available = await scanner.is_available()
            health_status["services"][scanner_type.value] = (
                "healthy" if is_available else "unavailable"
            )
        except Exception as e:
            health_status["services"][scanner_type.value] = f"error: {e}"
    
    # AI service
    try:
        await ai_processor.health_check()
        health_status["services"]["ai_processor"] = "healthy"
    except Exception as e:
        health_status["services"]["ai_processor"] = f"unhealthy: {e}"
    
    return health_status
```

### Logging & Metrics

```python
import structlog

# Structured logging configuration
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Usage in application
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Request logging middleware"""
    
    start_time = time.time()
    
    logger.info(
        "request_started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host
    )
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    logger.info(
        "request_completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time
    )
    
    return response
```

## Future Architecture Enhancements

### Microservices Migration

```
┌─────────────────────────────────────────────────────────────────┐
│                    Future Microservices Architecture            │
├─────────────────────────────────────────────────────────────────┤
│  🌐 API Gateway (Kong/AWS API Gateway)                         │
├─────────────────────────────────────────────────────────────────┤
│  🔍 Scan Service    │  🤖 AI Service     │  📊 Report Service   │
│  ├── Scanner Mgmt   │  ├── Analysis      │  ├── Generation      │
│  ├── Queue Mgmt     │  ├── ML Models     │  ├── Export          │
│  └── Result Proc    │  └── Recommendations│  └── Templates       │
├─────────────────────────────────────────────────────────────────┤
│  👤 Auth Service    │  🔔 Notification   │  📁 File Service     │
│  ├── JWT Mgmt       │  ├── Slack/Teams   │  ├── Storage         │
│  ├── RBAC           │  ├── Email         │  ├── Backup          │
│  └── SSO            │  └── Webhooks      │  └── Archive         │
├─────────────────────────────────────────────────────────────────┤
│  📨 Message Queue (RabbitMQ/Kafka)                             │
│  📊 Monitoring (Prometheus + Grafana)                          │
│  📋 Service Mesh (Istio)                                       │
└─────────────────────────────────────────────────────────────────┘
```

### Event-Driven Architecture

```python
# Event-driven scan processing
class ScanEventHandler:
    """Event-driven scan processing"""
    
    async def handle_scan_submitted(self, event: ScanSubmittedEvent):
        """Handle scan submission event"""
        await self.queue_scan_job(event.scan_id)
        await self.notify_scan_started(event.scan_id)
    
    async def handle_scan_completed(self, event: ScanCompletedEvent):
        """Handle scan completion event"""
        await self.generate_ai_analysis(event.scan_results)
        await self.send_notifications(event.scan_id)
        await self.update_security_metrics(event.scan_results)
```

This architecture provides a solid foundation for a production-ready security scanning platform that can compete with enterprise solutions while maintaining the flexibility and cost-effectiveness of open-source software.
