# 🔍 Advanced Scanning Implementation - Complete Guide

## 🎯 Overview

The Advanced Scanning module extends ONYX Platform beyond basic Semgrep/Trivy scanning by integrating enterprise-grade security tools:

- **🕷️ OWASP ZAP** - Dynamic Application Security Testing (DAST)
- **💥 Nuclei** - Vulnerability scanning with pentest templates
- **🔍 GitHub CodeQL** - Deep static code analysis (SAST)
- **☁️ Checkov** - Infrastructure as Code security scanning

## 🏗️ Architecture

### Unified Pipeline Design

```
┌─────────────────────────────────────────────────────────┐
│                 SCAN REQUEST                            │
├─────────────────────────────────────────────────────────┤
│  Repository URL + Target URL (optional)                │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│            ADVANCED SCANNER ENGINE                     │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   SAST      │  │    DAST     │  │    IaC      │     │
│  │             │  │             │  │             │     │
│  │ • CodeQL    │  │ • ZAP       │  │ • Checkov   │     │
│  │ • Semgrep   │  │ • Nuclei    │  │ • Terraform │     │
│  │ • Bandit    │  │ • Custom    │  │ • K8s       │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │         UNIFIED FINDING SCHEMA                  │   │
│  │  {                                              │   │
│  │    "id": "unique-finding-id",                   │   │
│  │    "source": "scanner-name",                    │   │
│  │    "rule_id": "rule-identifier",                │   │
│  │    "severity": "critical|high|medium|low|info", │   │
│  │    "location": {...},                           │   │
│  │    "cwe": "CWE-79",                             │   │
│  │    "cve": "CVE-2023-1234",                      │   │
│  │    "recommendation": "...",                     │   │
│  │    "scan_type": "sast|dast|iac|secrets",        │   │
│  │    "suppressed": false                          │   │
│  │  }                                              │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│           FALSE POSITIVE SUPPRESSION                   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              SUPPRESSION RULES                  │   │
│  │                                                 │   │
│  │ • Policy-as-code (.security-suppressions.yaml) │   │
│  │ • Inline annotations (# nosec)                 │   │
│  │ • File pattern matching                        │   │
│  │ • Severity-based filtering                     │   │
│  │ • Scanner-specific rules                       │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              NORMALIZED RESULTS                         │
│                                                         │
│  • Findings with consistent schema                     │
│  • Suppression status applied                          │
│  • Aggregated metrics and summaries                    │
│  • Integration-ready JSON output                       │
└─────────────────────────────────────────────────────────┘
```

## 🔧 Implementation Details

### 1. Scanner Integration

#### OWASP ZAP (DAST)

- **Purpose**: Dynamic security testing of running applications
- **Target**: Live web applications and APIs
- **Features**:
  - Automated spider crawling
  - Active vulnerability scanning
  - Configurable attack intensity
  - Proxy-based traffic analysis

```python
# ZAP Scanner Configuration
zap_config = {
    "proxy_port": 8080,
    "spider_max_depth": 3,
    "active_scan_policy": "default",
    "excluded_urls": [".*logout.*", ".*\\.css", ".*\\.js"]
}
```

#### Nuclei (Pentest Templates)

- **Purpose**: Fast vulnerability scanner with community templates
- **Target**: Web applications, APIs, network services
- **Features**:
  - 5000+ community templates
  - Custom template support
  - Rate limiting and throttling
  - Multiple protocol support

```python
# Nuclei Scanner Configuration
nuclei_config = {
    "rate_limit": "2",  # requests per second
    "timeout": "30s",
    "templates": ["cves/", "vulnerabilities/", "misconfiguration/"],
    "severity": ["critical", "high", "medium"]
}
```

#### GitHub CodeQL (SAST)

- **Purpose**: Deep semantic code analysis
- **Target**: Source code repositories
- **Features**:
  - Multi-language support (Python, JavaScript, Java, Go, C#, C++)
  - Advanced dataflow analysis
  - Zero-configuration setup
  - Security-focused query suites

```python
# CodeQL Scanner Configuration
codeql_config = {
    "languages": ["python", "javascript", "java"],
    "query_suite": "security-extended",
    "sarif_output": True,
    "database_cleanup": True
}
```

#### Checkov (IaC Security)

- **Purpose**: Infrastructure as Code security scanning
- **Target**: Terraform, CloudFormation, Kubernetes, Docker
- **Features**:
  - 1000+ built-in policies
  - Custom policy support
  - Multi-cloud coverage
  - Policy-as-code integration

```python
# Checkov Scanner Configuration
checkov_config = {
    "frameworks": ["terraform", "kubernetes", "docker"],
    "check_types": ["security", "compliance"],
    "custom_policies": ["./custom-policies/"],
    "skip_checks": ["CKV_DOCKER_1"]  # Configurable exclusions
}
```

### 2. Unified Finding Schema

All scanners normalize their output to a consistent schema:

```json
{
  "id": "zap-scan-001-finding-042",
  "source": "zap",
  "rule_id": "40012",
  "title": "Cross Site Scripting (Reflected)",
  "description": "User input is reflected in the response without proper encoding",
  "severity": "high",
  "confidence": "medium",
  "location": {
    "url": "https://app.example.com/search",
    "method": "GET",
    "parameter": "query"
  },
  "cwe": "CWE-79",
  "cve": null,
  "recommendation": "Encode all user input before reflecting in response",
  "scan_type": "dast",
  "raw_output": {
    /* Original scanner output */
  },
  "timestamp": "2025-08-14T12:34:56Z",
  "suppressed": false,
  "suppression_reason": null
}
```

### 3. False Positive Suppression

#### Policy-as-Code Suppressions

Managed via `.security-suppressions.yaml`:

```yaml
version: "1.0"
rules:
  test-files:
    description: "Suppress security findings in test files"
    file_patterns:
      - "**/test/**"
      - "**/tests/**"
      - "**/*_test.py"
    severities:
      - "low"
      - "medium"
    scanners:
      - "codeql"
      - "checkov"

  legacy-code:
    description: "Known issues in legacy code pending refactor"
    file_patterns:
      - "**/legacy/**"
    rule_ids:
      - "CWE-79"
      - "CWE-89"
    severities:
      - "medium"

  third-party:
    description: "Third-party dependencies"
    file_patterns:
      - "**/node_modules/**"
      - "**/vendor/**"
    scanners:
      - "codeql"
      - "checkov"
```

#### Inline Suppressions

Supported comment patterns:

```python
# Python
password = "dummy123"  # nosec B105
api_key = "test-key"   # nosec CWE-798

# JavaScript
const token = "test-token";  // nosec
var secret = "placeholder";  /* nosec CWE-798 */

# Go
password := "hardcoded"  // nosec G101

# General HTML/XML
<input type="password" value="test"> <!-- nosec -->
```

### 4. Rate Limits & Scoping

#### DAST Target Allowlist

Prevents scanning unauthorized targets:

```python
dast_target_allowlist = [
    "localhost",
    "127.0.0.1",
    "staging.example.com",
    "test.example.com"
]

def is_target_allowed(target_url: str) -> bool:
    parsed_url = urlparse(target_url)
    target_host = parsed_url.netloc.lower()

    for allowed in dast_target_allowlist:
        if target_host == allowed.lower() or target_host.endswith(f".{allowed.lower()}"):
            return True
    return False
```

#### Rate Limiting Configuration

```python
rate_limits = {
    "dast_rate_limit": 2.0,  # requests per second
    "max_concurrent_scans": 3,
    "scan_timeout": 1800,  # 30 minutes
    "dast_max_depth": 3,   # crawl depth
}
```

## 🚀 API Endpoints

### Comprehensive Scan

Start complete security scan with all scanners:

```bash
POST /api/advanced-scanning/scan/comprehensive
{
  "repository_url": "https://github.com/user/repo.git",
  "target_url": "https://staging.example.com",
  "config": {
    "sast_languages": ["python", "javascript"],
    "iac_frameworks": ["terraform", "kubernetes"],
    "dast_rate_limit": 1.0
  }
}
```

### SAST-Only Scan

Static analysis with CodeQL:

```bash
POST /api/advanced-scanning/scan/sast
{
  "repository_url": "https://github.com/user/repo.git",
  "languages": ["python", "javascript", "java"]
}
```

### DAST-Only Scan

Dynamic testing with ZAP + Nuclei:

```bash
POST /api/advanced-scanning/scan/dast
{
  "target_url": "https://staging.example.com"
}
```

### IaC-Only Scan

Infrastructure scanning with Checkov:

```bash
POST /api/advanced-scanning/scan/iac
{
  "repository_url": "https://github.com/user/repo.git",
  "frameworks": ["terraform", "kubernetes", "docker"]
}
```

### Get Scan Results

Retrieve findings with filtering:

```bash
GET /api/advanced-scanning/scan/{scan_id}/findings?severity=high&scanner=zap&suppressed=false
```

### Suppression Management

Create suppression rules:

```bash
POST /api/advanced-scanning/suppressions
{
  "name": "test-files-suppression",
  "description": "Suppress findings in test directories",
  "repository_url": "https://github.com/user/repo.git",
  "file_patterns": ["**/test/**", "**/tests/**"],
  "severities": ["low", "medium"],
  "scanners": ["codeql", "checkov"]
}
```

## 📊 Response Format

### Scan Summary Response

```json
{
  "success": true,
  "scan_id": "comp_20250814_123456",
  "report_id": "64f1234567890abcdef12345",
  "summary": {
    "total_findings": 45,
    "active_findings": 32,
    "suppressed_findings": 13,
    "by_severity": {
      "critical": 2,
      "high": 8,
      "medium": 15,
      "low": 7,
      "info": 0
    },
    "by_scanner": {
      "zap": 12,
      "nuclei": 8,
      "codeql": 18,
      "checkov": 7
    },
    "by_scan_type": {
      "sast": 18,
      "dast": 20,
      "iac": 7,
      "secrets": 0
    }
  },
  "scanners": {
    "zap": {
      "findings_count": 12,
      "duration": 245.6,
      "status": "completed"
    },
    "nuclei": {
      "findings_count": 8,
      "duration": 89.2,
      "status": "completed"
    },
    "codeql": {
      "findings_count": 18,
      "duration": 456.8,
      "status": "completed"
    },
    "checkov": {
      "findings_count": 7,
      "duration": 34.1,
      "status": "completed"
    }
  },
  "duration": 567.3
}
```

## ⚙️ Configuration

### Environment Variables

```bash
# Database
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/onyx

# DAST Configuration
DAST_TARGET_ALLOWLIST=localhost,127.0.0.1,staging.example.com
DAST_RATE_LIMIT=2.0
DAST_MAX_DEPTH=3

# Scanner Timeouts
SCAN_TIMEOUT=1800
MAX_CONCURRENT_SCANS=3

# Tool Paths (if not in PATH)
ZAP_PATH=/opt/zaproxy/zap.sh
NUCLEI_PATH=/usr/local/bin/nuclei
CODEQL_PATH=/opt/codeql/codeql
CHECKOV_PATH=/usr/local/bin/checkov
```

### Scanner Tool Installation

#### ZAP Installation

```bash
# Docker (recommended)
docker pull owasp/zap2docker-stable

# Manual installation
wget https://github.com/zaproxy/zaproxy/releases/download/v2.14.0/ZAP_2_14_0_unix.sh
chmod +x ZAP_2_14_0_unix.sh
./ZAP_2_14_0_unix.sh
```

#### Nuclei Installation

```bash
# Go installation
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# Binary download
curl -sSL https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei-linux-amd64.tar.gz | tar -xz
```

#### CodeQL Installation

```bash
# GitHub CLI
gh extension install github/gh-codeql

# Manual download
wget https://github.com/github/codeql-cli-binaries/releases/latest/download/codeql-linux64.zip
unzip codeql-linux64.zip
```

#### Checkov Installation

```bash
# Python pip
pip install checkov

# Docker
docker pull bridgecrew/checkov
```

## 🛡️ Security Considerations

### 1. DAST Target Validation

- **Allowlist enforcement**: Only scan pre-approved targets
- **Network segmentation**: Isolate scanning infrastructure
- **Rate limiting**: Prevent service disruption
- **Authentication**: Secure access to target applications

### 2. Code Repository Access

- **Git credentials**: Secure storage of repository access tokens
- **Temporary storage**: Automatic cleanup of cloned repositories
- **Access logging**: Audit trail of repository access

### 3. Scanner Tool Security

- **Container isolation**: Run scanners in secure containers
- **Resource limits**: Prevent resource exhaustion
- **Tool updates**: Regular security updates for scanner tools
- **Output sanitization**: Validate scanner output before processing

## 📈 Performance Optimization

### 1. Concurrent Scanning

```python
# Parallel scanner execution
sast_tasks = [
    engine.codeql_scanner.scan(repo_path, scan_id),
    engine.semgrep_scanner.scan(repo_path, scan_id)
]

dast_tasks = [
    engine.zap_scanner.scan(target_url, scan_id),
    engine.nuclei_scanner.scan(target_url, scan_id)
]

# Execute in parallel with resource limits
async with semaphore:
    results = await asyncio.gather(*sast_tasks, *dast_tasks)
```

### 2. Incremental Scanning

- **Baseline comparison**: Only report new findings
- **File change detection**: Focus scans on modified files
- **Caching**: Reuse results for unchanged components

### 3. Resource Management

- **Memory limits**: Container-based resource constraints
- **Timeout handling**: Graceful timeout and cleanup
- **Cleanup automation**: Automatic temporary file removal

## 🔍 Troubleshooting

### Common Issues

#### 1. Scanner Tool Not Found

```bash
# Verify tool installation
which zap.sh nuclei codeql checkov

# Check PATH configuration
echo $PATH

# Manual tool path configuration
export ZAP_PATH=/opt/zaproxy/zap.sh
export NUCLEI_PATH=/usr/local/bin/nuclei
```

#### 2. DAST Target Access Issues

```bash
# Verify target accessibility
curl -I https://staging.example.com

# Check allowlist configuration
grep -r "dast_target_allowlist" config/

# Network connectivity test
telnet staging.example.com 443
```

#### 3. Repository Access Issues

```bash
# Test git clone
git clone https://github.com/user/repo.git /tmp/test-clone

# Check authentication
git config --list | grep credential

# Verify network access
curl -I https://api.github.com
```

#### 4. Database Connection Issues

```bash
# Test MongoDB connection
mongosh "mongodb+srv://user:password@cluster.mongodb.net/onyx"

# Check environment variables
env | grep MONGODB

# Verify network connectivity
ping cluster.mongodb.net
```

### Debugging Commands

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Test individual scanner
python -m services.advanced_scanner_engine --test-scanner=zap

# Validate suppression rules
python -m scripts.test_advanced_scanning --test-suppressions

# Check API health
curl -X GET http://localhost:8000/api/advanced-scanning/config
```

## 🚀 Deployment Guide

### 1. Production Deployment

#### Docker Compose

```yaml
version: "3.8"
services:
  app:
    build: .
    environment:
      - MONGODB_URI=${MONGODB_URI}
      - DAST_TARGET_ALLOWLIST=${DAST_TARGET_ALLOWLIST}
    volumes:
      - ./security-tools:/opt/security-tools
    ports:
      - "8000:8000"

  zap:
    image: owasp/zap2docker-stable
    command: zap.sh -daemon -host 0.0.0.0 -port 8080
    ports:
      - "8080:8080"
```

#### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: advanced-scanning
spec:
  replicas: 3
  selector:
    matchLabels:
      app: advanced-scanning
  template:
    metadata:
      labels:
        app: advanced-scanning
    spec:
      containers:
        - name: app
          image: onyx/advanced-scanning:latest
          env:
            - name: MONGODB_URI
              valueFrom:
                secretKeyRef:
                  name: mongodb-secret
                  key: uri
          resources:
            limits:
              memory: "2Gi"
              cpu: "1000m"
            requests:
              memory: "1Gi"
              cpu: "500m"
```

### 2. Monitoring & Alerting

#### Metrics Collection

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

scan_counter = Counter('scans_total', 'Total scans executed', ['scanner', 'status'])
scan_duration = Histogram('scan_duration_seconds', 'Scan execution time', ['scanner'])
active_scans = Gauge('active_scans', 'Currently running scans')
```

#### Health Checks

```python
@app.get("/health/advanced-scanning")
async def health_check():
    """Health check for advanced scanning services"""
    health_status = {
        "status": "healthy",
        "scanners": {},
        "database": "connected",
        "timestamp": datetime.now().isoformat()
    }

    # Check scanner tool availability
    for scanner in ["zap", "nuclei", "codeql", "checkov"]:
        try:
            result = subprocess.run([scanner, "--version"],
                                  capture_output=True, timeout=5)
            health_status["scanners"][scanner] = "available" if result.returncode == 0 else "unavailable"
        except:
            health_status["scanners"][scanner] = "unavailable"

    return health_status
```

## 🏆 Success Metrics

- **✅ Unified Pipeline**: All 4 scanner types integrated with consistent output
- **✅ False Positive Suppression**: Policy-as-code + inline annotations
- **✅ Rate Limiting**: DAST target allowlist and request throttling
- **✅ Scalable Architecture**: Async processing with resource management
- **✅ Production Ready**: Docker deployment with monitoring and health checks

Your ONYX Security Intelligence Platform now provides enterprise-grade security scanning capabilities that go far beyond basic tools, with comprehensive coverage across SAST, DAST, IaC, and pentest methodologies! 🚀
