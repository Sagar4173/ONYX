# 🚀 Installation & Deployment Guide

## 🌐 Live Demo

**Try SecureDevOps AI Platform without installation:**

- 🌐 **Frontend Demo**: [https://secure-dev-ops-ai-platform.vercel.app](https://secure-dev-ops-ai-platform.vercel.app)
- 🔌 **Backend API**: [https://securedevopsai-platform-production.up.railway.app](https://securedevopsai-platform-production.up.railway.app)
- 📚 **API Documentation**: [https://securedevopsai-platform-production.up.railway.app/docs](https://securedevopsai-platform-production.up.railway.app/docs)
- 🏥 **System Health**: [https://securedevopsai-platform-production.up.railway.app/health](https://securedevopsai-platform-production.up.railway.app/health)

> **Note**: Demo environment has limited resources. For full functionality, deploy your own instance using the guides below.

## Overview

SecureDevOps AI Platform can be deployed in multiple configurations to meet different organizational needs, from development environments to enterprise-scale production deployments.

---

## 📋 **Prerequisites**

### **System Requirements**

#### **Minimum Requirements (Development)**
- **CPU**: 2 cores
- **Memory**: 4GB RAM
- **Storage**: 20GB free space
- **Network**: Internet connection for AI services

#### **Recommended Requirements (Production)**
- **CPU**: 4+ cores
- **Memory**: 8GB+ RAM
- **Storage**: 100GB+ SSD
- **Network**: High-speed internet, dedicated bandwidth

#### **Enterprise Requirements (High Scale)**
- **CPU**: 8+ cores per node
- **Memory**: 16GB+ RAM per node
- **Storage**: 500GB+ NVMe SSD
- **Network**: Load balancer, CDN, dedicated circuits

### **Software Dependencies**

#### **Required Software**
- **Python 3.11+** with pip
- **Node.js 18+** with npm/yarn
- **MongoDB 7.0+** (local or cloud)
- **Git** for repository cloning
- **Docker** (optional, for containerized deployment)

#### **Security Tools (Auto-installed)**
```bash
# These are automatically installed via requirements.txt
- Semgrep (Static Analysis)
- Trivy (Container Security)
- GitLeaks (Secret Detection)
- Lynis (Infrastructure Security)
- Safety (Python Dependencies)
- Bandit (Python SAST)
```

#### **External Services**
- **OpenAI API** (required for AI analysis)
- **Slack/Teams** (optional, for notifications)
- **SMTP Server** (optional, for email notifications)

---

## 🛠️ **Installation Methods**

### **Method 1: Local Development Setup**

#### **1. Clone Repository**
```bash
# Clone the repository
git clone https://github.com/Sagar4173/SecureDevOpsAI-Platform.git
cd SecureDevOpsAI-Platform

# Verify directory structure
ls -la
# Should show: backend/ frontend/ docs/ README.md
```

#### **2. Backend Setup**
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell
venv\Scripts\Activate.ps1
# Windows Command Prompt
venv\Scripts\activate.bat
# Linux/macOS
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import fastapi, motor, openai; print('All dependencies installed successfully')"
```

#### **3. Frontend Setup**
```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install Node.js dependencies
npm install

# Verify installation
npm list --depth=0
```

#### **4. Database Setup**

##### **Option A: Local MongoDB**
```bash
# Install MongoDB (Ubuntu/Debian)
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB service
sudo systemctl start mongod
sudo systemctl enable mongod

# Verify MongoDB is running
mongosh --eval "db.adminCommand('ping')"
```

##### **Option B: MongoDB Atlas (Cloud)**
```bash
# Sign up at https://cloud.mongodb.com/
# Create a cluster
# Get connection string
# Use in environment configuration
```

#### **5. Environment Configuration**
```bash
# Create environment file (from project root)
cp .env.example .env

# Edit configuration
nano .env  # or your preferred editor
```

**Environment Variables:**
```bash
# Required Settings
OPENAI_API_KEY=sk-your-openai-api-key-here
SECRET_KEY=your-super-secure-secret-key-256-bits
MONGODB_URI=mongodb://localhost:27017/securedevops

# Optional Settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100

# Notification Settings (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/YOUR/TEAMS/WEBHOOK

# Scanner Configuration
SEMGREP_PATH=semgrep
TRIVY_PATH=trivy
GITLEAKS_PATH=gitleaks
LYNIS_PATH=lynis

# Git Scanning Settings
GIT_SCAN_TIMEOUT=300
CLEANUP_AFTER_SCAN=true

# OpenAI Configuration
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=2000
```

#### **6. Generate Secret Key**
```bash
# Generate a secure secret key
python -c "
import secrets
print('SECRET_KEY=' + secrets.token_urlsafe(32))
"
```

#### **7. Start Services**
```bash
# Terminal 1: Start Backend
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python app.py

# Terminal 2: Start Frontend
cd frontend
npm run dev

# Terminal 3: Monitor Logs (Optional)
tail -f backend/logs/app.log
```

#### **8. Verify Installation**
```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
open http://localhost:5173  # or visit in browser

# Test API documentation
open http://localhost:8000/docs
```

### **Method 2: Docker Deployment**

#### **1. Docker Compose Setup**
```yaml
# docker-compose.yml
version: '3.8'

services:
  mongodb:
    image: mongo:7.0
    container_name: securedevops-mongo
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
      MONGO_INITDB_DATABASE: securedevops
    volumes:
      - mongodb_data:/data/db
      - ./backend/scripts/init-mongo.js:/docker-entrypoint-initdb.d/init-mongo.js:ro
    ports:
      - "27017:27017"
    networks:
      - securedevops-network

  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    container_name: securedevops-backend
    restart: unless-stopped
    environment:
      MONGODB_URI: mongodb://admin:${MONGO_PASSWORD}@mongodb:27017/securedevops?authSource=admin
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      SECRET_KEY: ${SECRET_KEY}
      ENVIRONMENT: production
      DEBUG: false
    volumes:
      - ./backend/logs:/app/logs
      - scanner_cache:/app/cache
    ports:
      - "8000:8000"
    depends_on:
      - mongodb
    networks:
      - securedevops-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: 
      context: ./frontend
      dockerfile: Dockerfile
    container_name: securedevops-frontend
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
    networks:
      - securedevops-network
    volumes:
      - ./ssl:/etc/nginx/ssl:ro

  redis:
    image: redis:7-alpine
    container_name: securedevops-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - securedevops-network

volumes:
  mongodb_data:
  redis_data:
  scanner_cache:

networks:
  securedevops-network:
    driver: bridge
```

#### **2. Environment Configuration**
```bash
# Create .env file for Docker
cat > .env << EOF
MONGO_PASSWORD=your-secure-mongo-password
OPENAI_API_KEY=sk-your-openai-api-key
SECRET_KEY=$(openssl rand -hex 32)
EOF
```

#### **3. Build and Deploy**
```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Scale backend if needed
docker-compose up -d --scale backend=3
```

#### **4. Docker Health Checks**
```bash
# Check all service health
docker-compose exec backend curl -f http://localhost:8000/health
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
docker-compose exec redis redis-cli ping
```

### **Method 3: Kubernetes Deployment**

#### **1. Kubernetes Manifests**

**Namespace:**
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: securedevops
  labels:
    name: securedevops
```

**ConfigMap:**
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: securedevops-config
  namespace: securedevops
data:
  ENVIRONMENT: "production"
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  RATE_LIMIT_PER_MINUTE: "100"
  OPENAI_MODEL: "gpt-4"
  OPENAI_MAX_TOKENS: "2000"
```

**Secrets:**
```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: securedevops-secrets
  namespace: securedevops
type: Opaque
stringData:
  MONGODB_URI: "mongodb://admin:password@mongodb:27017/securedevops?authSource=admin"
  OPENAI_API_KEY: "sk-your-openai-api-key"
  SECRET_KEY: "your-super-secure-secret-key"
  SLACK_WEBHOOK_URL: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
```

**MongoDB Deployment:**
```yaml
# k8s/mongodb.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mongodb
  namespace: securedevops
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mongodb
  template:
    metadata:
      labels:
        app: mongodb
    spec:
      containers:
      - name: mongodb
        image: mongo:7.0
        env:
        - name: MONGO_INITDB_ROOT_USERNAME
          value: "admin"
        - name: MONGO_INITDB_ROOT_PASSWORD
          value: "password"
        - name: MONGO_INITDB_DATABASE
          value: "securedevops"
        ports:
        - containerPort: 27017
        volumeMounts:
        - name: mongodb-storage
          mountPath: /data/db
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
      volumes:
      - name: mongodb-storage
        persistentVolumeClaim:
          claimName: mongodb-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: mongodb
  namespace: securedevops
spec:
  selector:
    app: mongodb
  ports:
  - port: 27017
    targetPort: 27017
```

**Backend Deployment:**
```yaml
# k8s/backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: securedevops-backend
  namespace: securedevops
spec:
  replicas: 3
  selector:
    matchLabels:
      app: securedevops-backend
  template:
    metadata:
      labels:
        app: securedevops-backend
    spec:
      containers:
      - name: backend
        image: securedevops/backend:latest
        envFrom:
        - configMapRef:
            name: securedevops-config
        - secretRef:
            name: securedevops-secrets
        ports:
        - containerPort: 8000
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
        volumeMounts:
        - name: logs
          mountPath: /app/logs
        - name: cache
          mountPath: /app/cache
      volumes:
      - name: logs
        emptyDir: {}
      - name: cache
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: securedevops-backend
  namespace: securedevops
spec:
  selector:
    app: securedevops-backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

**Ingress:**
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: securedevops-ingress
  namespace: securedevops
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  tls:
  - hosts:
    - securedevops.yourdomain.com
    secretName: securedevops-tls
  rules:
  - host: securedevops.yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: securedevops-backend
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: securedevops-frontend
            port:
              number: 80
```

#### **2. Deploy to Kubernetes**
```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n securedevops
kubectl get services -n securedevops
kubectl get ingress -n securedevops

# Check logs
kubectl logs -f deployment/securedevops-backend -n securedevops

# Scale deployment
kubectl scale deployment securedevops-backend --replicas=5 -n securedevops
```

---

## 🔧 **Production Configuration**

### **Security Hardening**

#### **1. SSL/TLS Configuration**
```nginx
# nginx.conf for frontend
server {
    listen 443 ssl http2;
    server_name securedevops.yourdomain.com;

    ssl_certificate /etc/ssl/certs/securedevops.crt;
    ssl_certificate_key /etc/ssl/private/securedevops.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
}
```

#### **2. Database Security**
```bash
# MongoDB security configuration
# Enable authentication
security:
  authorization: enabled

# Enable SSL
net:
  ssl:
    mode: requireSSL
    PEMKeyFile: /etc/ssl/mongodb.pem

# Bind to specific interface
net:
  bindIp: 127.0.0.1,mongodb.yourdomain.com
```

#### **3. Environment Security**
```bash
# Production environment variables
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=$(openssl rand -hex 32)
MONGODB_URI=mongodb://user:password@mongodb:27017/securedevops?ssl=true&authSource=admin

# Security headers
FORCE_HTTPS=true
SECURE_COOKIES=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SECURE=true

# Rate limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10
```

### **Performance Optimization**

#### **1. Application Tuning**
```python
# backend/config.py - Production settings
class ProductionConfig(BaseConfig):
    WORKERS = 4  # Number of Gunicorn workers
    WORKER_CLASS = "uvicorn.workers.UvicornWorker"
    WORKER_CONNECTIONS = 1000
    MAX_REQUESTS = 1000
    MAX_REQUESTS_JITTER = 100
    PRELOAD_APP = True
    
    # Database connection pooling
    MONGODB_MAX_POOL_SIZE = 100
    MONGODB_MIN_POOL_SIZE = 10
    
    # Caching
    CACHE_TYPE = "redis"
    CACHE_REDIS_URL = "redis://redis:6379/0"
    CACHE_DEFAULT_TIMEOUT = 300
```

#### **2. Database Optimization**
```javascript
// MongoDB indexes for performance
db.scan_reports.createIndex({ "scan_id": 1 }, { unique: true });
db.scan_reports.createIndex({ "project_name": 1, "created_at": -1 });
db.scan_reports.createIndex({ "status": 1, "created_at": -1 });
db.scan_reports.createIndex({ "total_findings": -1 });
db.scan_reports.createIndex({ 
  "project_name": "text", 
  "git_metadata.commit_message": "text" 
});

// Compound indexes for common queries
db.scan_reports.createIndex({ 
  "project_name": 1, 
  "status": 1, 
  "created_at": -1 
});
```

#### **3. Caching Strategy**
```python
# Redis caching implementation
from redis import asyncio as aioredis
import json

class CacheService:
    def __init__(self):
        self.redis = aioredis.from_url("redis://redis:6379")
    
    async def get_scan_results(self, scan_id: str):
        cached = await self.redis.get(f"scan:{scan_id}")
        if cached:
            return json.loads(cached)
        return None
    
    async def cache_scan_results(self, scan_id: str, results: dict):
        await self.redis.setex(
            f"scan:{scan_id}", 
            3600,  # 1 hour TTL
            json.dumps(results, default=str)
        )
```

### **Monitoring & Observability**

#### **1. Health Checks**
```python
# Comprehensive health check endpoint
@app.get("/health")
async def health_check():
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {}
    }
    
    # Database check
    try:
        await db_manager.ping()
        health["services"]["database"] = "healthy"
    except Exception as e:
        health["services"]["database"] = f"unhealthy: {e}"
        health["status"] = "unhealthy"
    
    # Security scanners check
    for scanner_name, scanner in security_scanner.scanners.items():
        try:
            available = await scanner.is_available()
            health["services"][scanner_name.value] = "healthy" if available else "unavailable"
        except Exception as e:
            health["services"][scanner_name.value] = f"error: {e}"
    
    # AI service check
    try:
        await ai_processor.health_check()
        health["services"]["ai_processor"] = "healthy"
    except Exception as e:
        health["services"]["ai_processor"] = f"unhealthy: {e}"
        health["status"] = "unhealthy"
    
    return health
```

#### **2. Prometheus Metrics**
```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Define metrics
SCAN_REQUESTS = Counter('securedevops_scan_requests_total', 'Total scan requests')
SCAN_DURATION = Histogram('securedevops_scan_duration_seconds', 'Scan duration')
ACTIVE_SCANS = Gauge('securedevops_active_scans', 'Number of active scans')
VULNERABILITIES_FOUND = Counter('securedevops_vulnerabilities_total', 'Total vulnerabilities found', ['severity'])

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

#### **3. Logging Configuration**
```python
# logging_config.py
import structlog

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
```

---

## 🔄 **Backup & Recovery**

### **Database Backup**
```bash
#!/bin/bash
# backup.sh - MongoDB backup script

BACKUP_DIR="/backup/mongodb"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/securedevops_$DATE"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
mongodump --uri="mongodb://admin:password@mongodb:27017/securedevops?authSource=admin" --out="$BACKUP_PATH"

# Compress backup
tar -czf "$BACKUP_PATH.tar.gz" -C "$BACKUP_DIR" "securedevops_$DATE"

# Remove uncompressed backup
rm -rf "$BACKUP_PATH"

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_PATH.tar.gz"
```

### **Automated Backup with Cron**
```bash
# Add to crontab (daily backup at 2 AM)
0 2 * * * /path/to/backup.sh >> /var/log/mongodb-backup.log 2>&1
```

### **Recovery Process**
```bash
#!/bin/bash
# restore.sh - MongoDB restore script

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

# Extract backup
tar -xzf "$BACKUP_FILE" -C /tmp/

# Get backup directory name
BACKUP_DIR=$(tar -tzf "$BACKUP_FILE" | head -1 | cut -f1 -d"/")

# Restore database
mongorestore --uri="mongodb://admin:password@mongodb:27017/?authSource=admin" --drop /tmp/$BACKUP_DIR

# Clean up
rm -rf /tmp/$BACKUP_DIR

echo "Restore completed from: $BACKUP_FILE"
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **1. Backend Won't Start**
```bash
# Check Python version
python --version  # Should be 3.11+

# Check dependencies
pip list | grep fastapi
pip list | grep motor

# Check environment variables
echo $OPENAI_API_KEY
echo $MONGODB_URI

# Check logs
tail -f backend/logs/app.log
```

#### **2. Database Connection Issues**
```bash
# Test MongoDB connectivity
mongosh "mongodb://localhost:27017/securedevops" --eval "db.adminCommand('ping')"

# Check MongoDB service
sudo systemctl status mongod

# Check network connectivity
telnet mongodb-host 27017
```

#### **3. Frontend Build Issues**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 18+
npm --version
```

#### **4. Security Scanner Issues**
```bash
# Verify scanner installations
semgrep --version
trivy --version
gitleaks version
lynis --version

# Check scanner availability
curl http://localhost:8000/health
```

### **Performance Issues**

#### **1. Slow Scans**
```bash
# Check system resources
top
htop
iostat

# Monitor scan processes
ps aux | grep -E "(semgrep|trivy|gitleaks|lynis)"

# Check disk space
df -h
```

#### **2. High Memory Usage**
```bash
# Check memory usage
free -h
cat /proc/meminfo

# Monitor Python processes
ps aux | grep python | awk '{print $6}' | awk '{sum+=$1} END {print sum/1024 " MB"}'

# Adjust worker processes
# In production config, reduce WORKERS count
```

#### **3. Database Performance**
```bash
# Check MongoDB performance
db.serverStatus().metrics
db.stats()

# Monitor slow queries
db.setProfilingLevel(1, { slowms: 100 })
db.system.profile.find().sort({ ts: -1 }).limit(5)
```

---

## 📞 **Support & Maintenance**

### **Regular Maintenance Tasks**
```bash
# Weekly tasks
- Database backup verification
- Log rotation and cleanup
- Security scanner updates
- Dependency updates

# Monthly tasks
- Performance monitoring review
- Security audit
- Capacity planning
- Documentation updates
```

### **Update Procedures**
```bash
# Update application
git pull origin main
pip install -r requirements.txt
npm install --prefix frontend
npm run build --prefix frontend

# Update security scanners
pip install --upgrade semgrep
# Trivy auto-updates its database
# GitLeaks updates via Go modules
```

This comprehensive installation guide covers all deployment scenarios from development to enterprise production environments, ensuring successful deployment and operation of the SecureDevOps AI Platform.
