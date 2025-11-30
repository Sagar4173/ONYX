# 🔧 Deployment Guide

## Current Live Deployments

**ONYX Platform is currently live and running:**

- 🌐 **Frontend (Vercel)**: [https://secure-dev-ops-ai-platform.vercel.app](https://secure-dev-ops-ai-platform.vercel.app)
- 🔌 **Backend (Railway)**: [https://securedevopsai-platform-production.up.railway.app](https://securedevopsai-platform-production.up.railway.app)
- 📚 **API Docs**: [https://securedevopsai-platform-production.up.railway.app/docs](https://securedevopsai-platform-production.up.railway.app/docs)
- 🏥 **Health Check**: [https://securedevopsai-platform-production.up.railway.app/health](https://securedevopsai-platform-production.up.railway.app/health)

## Overview

ONYX - Security Intelligence Platform supports multiple deployment options to fit different infrastructure requirements. This guide covers deployment strategies from local development to enterprise production environments.

---

## 🐳 Docker Deployment (Recommended)

### Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- 4GB+ RAM available
- 10GB+ disk space

### Quick Start with Docker Compose

1. **Clone the repository:**

```bash
git clone https://github.com/Sagar4173/SecureDevOpsAI-Platform.git
cd SecureDevOpsAI-Platform
```

2. **Configure environment:**

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

3. **Required environment variables:**

```env
# Database
MONGODB_URL=mongodb://mongodb:27017/securedevops
MONGODB_DB_NAME=securedevops

# OpenAI API (Primary AI Provider)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Google Gemini API (Alternative AI Provider)
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-pro
AI_PROVIDER=openai  # Options: "openai" or "gemini"

# JWT Authentication
SECRET_KEY=your-super-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/slack/webhook
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/your/teams/webhook

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info
CORS_ORIGINS=["https://your-frontend-domain.com"]
```

4. **Start the platform:**

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Development deployment
docker-compose up -d
```

5. **Verify deployment:**

```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs -f

# Health check
curl http://localhost:8000/health
```

### Docker Compose Configuration

**Production (`docker-compose.prod.yml`):**

```yaml
version: "3.8"

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URL=mongodb://mongodb:27017/securedevops
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - mongodb
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - securedevops-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
    restart: unless-stopped
    volumes:
      - ./ssl:/etc/nginx/ssl
    networks:
      - securedevops-network

  mongodb:
    image: mongo:7.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
      - ./backend/scripts/init-mongo.js:/docker-entrypoint-initdb.d/init-mongo.js:ro
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=${MONGODB_ROOT_PASSWORD}
      - MONGO_INITDB_DATABASE=securedevops
    restart: unless-stopped
    networks:
      - securedevops-network

  redis:
    image: redis:7.0-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - securedevops-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
    networks:
      - securedevops-network

volumes:
  mongodb_data:
  redis_data:

networks:
  securedevops-network:
    driver: bridge
```

---

## ☁️ Cloud Deployment Options

### AWS Deployment

#### Option 1: ECS with Fargate

**Prerequisites:**

- AWS CLI configured
- ECS CLI installed
- ECR repositories created

**Deploy with CloudFormation:**

```yaml
# cloudformation/ecs-deployment.yml
AWSTemplateFormatVersion: "2010-09-09"
Description: "SecureDevOps AI Platform ECS Deployment"

Parameters:
  VpcId:
    Type: AWS::EC2::VPC::Id
    Description: VPC for the ECS cluster

  SubnetIds:
    Type: List<AWS::EC2::Subnet::Id>
    Description: Subnets for the ECS service

  OpenAIApiKey:
    Type: String
    NoEcho: true
    Description: OpenAI API Key

Resources:
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: securedevops-cluster
      CapacityProviders:
        - FARGATE
        - FARGATE_SPOT

  TaskDefinition:
    Type: AWS::ECS::TaskDefinition
    Properties:
      Family: securedevops-task
      NetworkMode: awsvpc
      RequiresCompatibilities:
        - FARGATE
      Cpu: 1024
      Memory: 2048
      ExecutionRoleArn: !Ref ExecutionRole
      TaskRoleArn: !Ref TaskRole
      ContainerDefinitions:
        - Name: backend
          Image: !Sub ${AWS::AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/securedevops-backend:latest
          PortMappings:
            - ContainerPort: 8000
          Environment:
            - Name: MONGODB_URL
              Value: !Sub mongodb://${DocumentDBCluster.Endpoint}:27017/securedevops
            - Name: OPENAI_API_KEY
              Value: !Ref OpenAIApiKey
          LogConfiguration:
            LogDriver: awslogs
            Options:
              awslogs-group: /ecs/securedevops
              awslogs-region: !Ref AWS::Region
              awslogs-stream-prefix: backend

  ECSService:
    Type: AWS::ECS::Service
    Properties:
      Cluster: !Ref ECSCluster
      TaskDefinition: !Ref TaskDefinition
      DesiredCount: 2
      LaunchType: FARGATE
      NetworkConfiguration:
        AwsvpcConfiguration:
          SecurityGroups:
            - !Ref SecurityGroup
          Subnets: !Ref SubnetIds
          AssignPublicIp: ENABLED
      LoadBalancers:
        - ContainerName: backend
          ContainerPort: 8000
          TargetGroupArn: !Ref TargetGroup

  DocumentDBCluster:
    Type: AWS::DocDB::DBCluster
    Properties:
      DBClusterIdentifier: securedevops-docdb
      EngineVersion: 4.0.0
      MasterUsername: admin
      MasterUserPassword: !Ref DocumentDBPassword
      VpcSecurityGroupIds:
        - !Ref DocumentDBSecurityGroup
      DBSubnetGroupName: !Ref DocumentDBSubnetGroup

Outputs:
  LoadBalancerDNS:
    Description: DNS name of the load balancer
    Value: !GetAtt LoadBalancer.DNSName
```

**Deploy command:**

```bash
aws cloudformation deploy \
  --template-file cloudformation/ecs-deployment.yml \
  --stack-name securedevops-platform \
  --parameter-overrides \
    VpcId=vpc-12345678 \
    SubnetIds=subnet-12345678,subnet-87654321 \
    OpenAIApiKey=sk-your-key-here \
  --capabilities CAPABILITY_IAM
```

#### Option 2: EC2 with Auto Scaling

**User Data script for EC2 instances:**

```bash
#!/bin/bash
yum update -y
yum install -y docker

# Start Docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Clone repository
cd /opt
git clone https://github.com/Sagar4173/SecureDevOpsAI-Platform.git
cd SecureDevOpsAI-Platform

# Configure environment
cat > .env << EOF
MONGODB_URL=mongodb://mongodb.cluster.amazonaws.com:27017/securedevops
OPENAI_API_KEY=${OpenAIApiKey}
SECRET_KEY=${SecretKey}
ENVIRONMENT=production
EOF

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Configure log rotation
cat > /etc/logrotate.d/docker-compose << EOF
/opt/SecureDevOpsAI-Platform/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    copytruncate
}
EOF
```

### Google Cloud Platform (GCP)

#### Deploy to Google Kubernetes Engine (GKE)

**1. Create GKE cluster:**

```bash
# Create cluster
gcloud container clusters create securedevops-cluster \
  --num-nodes=3 \
  --machine-type=e2-standard-4 \
  --zone=us-central1-a \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=10

# Get credentials
gcloud container clusters get-credentials securedevops-cluster --zone=us-central1-a
```

**2. Deploy with Kubernetes manifests:**

```yaml
# k8s/namespace.yml
apiVersion: v1
kind: Namespace
metadata:
  name: securedevops

---
# k8s/configmap.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: securedevops
data:
  MONGODB_URL: "mongodb://mongodb-service:27017/securedevops"
  ENVIRONMENT: "production"
  LOG_LEVEL: "info"

---
# k8s/secret.yml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: securedevops
type: Opaque
data:
  OPENAI_API_KEY: <base64-encoded-key>
  SECRET_KEY: <base64-encoded-secret>

---
# k8s/backend-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: securedevops
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
        - name: backend
          image: gcr.io/your-project/securedevops-backend:latest
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: app-config
            - secretRef:
                name: app-secrets
          resources:
            requests:
              cpu: 500m
              memory: 1Gi
            limits:
              cpu: 1000m
              memory: 2Gi
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10

---
# k8s/backend-service.yml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: securedevops
spec:
  selector:
    app: backend
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: ClusterIP

---
# k8s/ingress.yml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: securedevops-ingress
  namespace: securedevops
  annotations:
    kubernetes.io/ingress.class: "gce"
    kubernetes.io/ingress.global-static-ip-name: "securedevops-ip"
    networking.gke.io/managed-certificates: "securedevops-ssl-cert"
spec:
  rules:
    - host: api.securedevops.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: backend-service
                port:
                  number: 80
```

**3. Deploy to cluster:**

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n securedevops
kubectl get services -n securedevops
kubectl get ingress -n securedevops

# View logs
kubectl logs -f deployment/backend -n securedevops
```

### Microsoft Azure

#### Deploy to Azure Container Instances (ACI)

**Azure Resource Manager template:**

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "openAIApiKey": {
      "type": "securestring",
      "metadata": {
        "description": "OpenAI API Key"
      }
    }
  },
  "resources": [
    {
      "type": "Microsoft.ContainerInstance/containerGroups",
      "apiVersion": "2021-03-01",
      "name": "securedevops-platform",
      "location": "[resourceGroup().location]",
      "properties": {
        "containers": [
          {
            "name": "backend",
            "properties": {
              "image": "your-registry.azurecr.io/securedevops-backend:latest",
              "ports": [
                {
                  "port": 8000,
                  "protocol": "TCP"
                }
              ],
              "environmentVariables": [
                {
                  "name": "OPENAI_API_KEY",
                  "secureValue": "[parameters('openAIApiKey')]"
                },
                {
                  "name": "MONGODB_URL",
                  "value": "mongodb://cosmosdb-account.mongo.cosmos.azure.com:10255/securedevops"
                }
              ],
              "resources": {
                "requests": {
                  "cpu": 1,
                  "memoryInGB": 2
                }
              }
            }
          }
        ],
        "osType": "Linux",
        "ipAddress": {
          "type": "Public",
          "ports": [
            {
              "port": 8000,
              "protocol": "TCP"
            }
          ]
        }
      }
    }
  ]
}
```

**Deploy with Azure CLI:**

```bash
# Create resource group
az group create --name securedevops-rg --location eastus

# Deploy template
az deployment group create \
  --resource-group securedevops-rg \
  --template-file azure-deployment.json \
  --parameters openAIApiKey=sk-your-key-here

# Get container IP
az container show --resource-group securedevops-rg --name securedevops-platform --query ipAddress.ip
```

---

## 🔧 Manual Deployment

### Ubuntu/Debian Server

**1. System preparation:**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm git curl

# Install MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update
sudo apt install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Install security tools
sudo apt install -y docker.io
curl -sSfL https://raw.githubusercontent.com/securecodewarrior/semgrep/develop/install.sh | sh
wget https://github.com/aquasecurity/trivy/releases/latest/download/trivy_0.48.0_Linux-64bit.deb
sudo dpkg -i trivy_0.48.0_Linux-64bit.deb
```

**2. Application setup:**

```bash
# Clone repository
cd /opt
sudo git clone https://github.com/Sagar4173/SecureDevOpsAI-Platform.git
sudo chown -R $USER:$USER SecureDevOpsAI-Platform
cd SecureDevOpsAI-Platform

# Backend setup
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
npm run build

# Configure environment
cd ..
cp .env.example .env
nano .env  # Edit configuration
```

**3. Service configuration:**

**Backend systemd service (`/etc/systemd/system/securedevops-backend.service`):**

```ini
[Unit]
Description=SecureDevOps AI Backend
After=network.target mongod.service
Requires=mongod.service

[Service]
Type=simple
User=securedevops
WorkingDirectory=/opt/SecureDevOpsAI-Platform/backend
Environment=PATH=/opt/SecureDevOpsAI-Platform/backend/venv/bin
ExecStart=/opt/SecureDevOpsAI-Platform/backend/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Nginx configuration (`/etc/nginx/sites-available/securedevops`):**

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/securedevops.crt;
    ssl_certificate_key /etc/ssl/private/securedevops.key;

    # Frontend
    location / {
        root /opt/SecureDevOpsAI-Platform/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

**4. Start services:**

```bash
# Create user
sudo useradd -r -s /bin/false securedevops

# Set permissions
sudo chown -R securedevops:securedevops /opt/SecureDevOpsAI-Platform

# Enable and start services
sudo systemctl enable securedevops-backend
sudo systemctl start securedevops-backend

# Configure nginx
sudo ln -s /etc/nginx/sites-available/securedevops /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Check status
sudo systemctl status securedevops-backend
sudo systemctl status nginx
```

---

## 🔒 Production Security

### SSL/TLS Configuration

**Let's Encrypt with Certbot:**

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Firewall Configuration

```bash
# UFW (Ubuntu/Debian)
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp  # Block direct backend access
sudo ufw deny 27017/tcp # Block direct MongoDB access

# Check status
sudo ufw status
```

### Security Hardening

**1. MongoDB security:**

```javascript
// MongoDB admin user creation
use admin
db.createUser({
  user: "admin",
  pwd: "secure-password-here",
  roles: [ { role: "userAdminAnyDatabase", db: "admin" } ]
})

// Application user
use securedevops
db.createUser({
  user: "app",
  pwd: "app-password-here",
  roles: [ { role: "readWrite", db: "securedevops" } ]
})
```

**2. Application security:**

```env
# Strong JWT secret
SECRET_KEY=your-super-long-random-secret-key-here

# Secure headers
SECURE_HEADERS=true
CSRF_PROTECTION=true

# Rate limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# IP filtering
ALLOWED_IPS=10.0.0.0/8,192.168.0.0/16
```

---

## 📊 Monitoring & Logging

### Prometheus & Grafana

**docker-compose-monitoring.yml:**

```yaml
version: "3.8"

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
      - "--web.console.libraries=/etc/prometheus/console_libraries"
      - "--web.console.templates=/etc/prometheus/consoles"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - "--path.procfs=/host/proc"
      - "--path.sysfs=/host/sys"
      - "--collector.filesystem.ignored-mount-points=^/(sys|proc|dev|host|etc)($$|/)"

volumes:
  prometheus_data:
  grafana_data:
```

### Log Management

**Centralized logging with ELK Stack:**

```yaml
# docker-compose-logging.yml
version: "3.8"

services:
  elasticsearch:
    image: elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: logstash:8.5.0
    ports:
      - "5000:5000"
    volumes:
      - ./logging/logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  kibana:
    image: kibana:8.5.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

---

## 🔄 Backup & Recovery

### Database Backup

**Automated backup script:**

```bash
#!/bin/bash
# backup-mongodb.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/mongodb"
DB_NAME="securedevops"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
mongodump --db $DB_NAME --out $BACKUP_DIR/$DATE

# Compress backup
tar -czf $BACKUP_DIR/mongodb_backup_$DATE.tar.gz -C $BACKUP_DIR $DATE

# Remove uncompressed backup
rm -rf $BACKUP_DIR/$DATE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "mongodb_backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: mongodb_backup_$DATE.tar.gz"
```

**Cron job for daily backups:**

```bash
# Add to crontab
0 2 * * * /opt/scripts/backup-mongodb.sh >> /var/log/mongodb-backup.log 2>&1
```

### Disaster Recovery

**Recovery procedure:**

```bash
# Stop services
sudo systemctl stop securedevops-backend

# Restore from backup
tar -xzf mongodb_backup_20240115_020000.tar.gz
mongorestore --db securedevops --drop securedevops/

# Start services
sudo systemctl start securedevops-backend

# Verify functionality
curl http://localhost:8000/health
```

---

## 📈 Scaling Considerations

### Horizontal Scaling

**Load balancer configuration (HAProxy):**

```
global
    daemon

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend securedevops_frontend
    bind *:80
    default_backend securedevops_backend

backend securedevops_backend
    balance roundrobin
    server backend1 10.0.1.10:8000 check
    server backend2 10.0.1.11:8000 check
    server backend3 10.0.1.12:8000 check
```

### Database Scaling

**MongoDB replica set:**

```javascript
// Initialize replica set
rs.initiate({
  _id: "securedevops-rs",
  members: [
    { _id: 0, host: "mongo1:27017", priority: 1 },
    { _id: 1, host: "mongo2:27017", priority: 0.5 },
    { _id: 2, host: "mongo3:27017", priority: 0.5 },
  ],
});
```

---

## 🆘 Troubleshooting

### Common Issues

**1. Backend fails to start:**

```bash
# Check logs
sudo journalctl -u securedevops-backend -f

# Common fixes
sudo systemctl restart securedevops-backend
sudo systemctl status securedevops-backend
```

**2. Database connection issues:**

```bash
# Test MongoDB connection
mongosh --eval "db.adminCommand('ismaster')"

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log
```

**3. Scanner tool errors:**

```bash
# Test individual scanners
semgrep --version
trivy version
gitleaks version

# Update scanner databases
trivy image --download-db-only
```

**4. Memory/CPU issues:**

```bash
# Monitor resources
htop
docker stats

# Adjust container limits in docker-compose.yml
```

### Performance Optimization

**1. Database optimization:**

```javascript
// Create indexes
db.reports.createIndex({ created_at: -1 });
db.reports.createIndex({ project_name: 1, status: 1 });
db.reports.createIndex({ "git_metadata.repository_url": 1 });
```

**2. Application optimization:**

```env
# Async workers
WORKER_PROCESSES=4
MAX_CONCURRENT_SCANS=10

# Caching
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600
```

---

For deployment support and troubleshooting, visit our [GitHub Issues](https://github.com/Sagar4173/SecureDevOpsAI-Platform/issues) or [Discussion Forum](https://github.com/Sagar4173/SecureDevOpsAI-Platform/discussions).
