# Enhanced Security Scanner Integration Documentation

## Overview

This document describes the implementation of enhanced security scanning features in the ONYX Platform, including the integration of six security scanners with advanced customization and performance optimizations.

## Implemented Features

### ✅ Security Scanner Integration

#### 1. Semgrep (SAST) - Enhanced Implementation

- **Configuration**: Custom rule sets with organization-specific patterns
- **Features**:
  - Multi-language static analysis (Python, JavaScript, Java, Go, etc.)
  - Security-focused rulesets (OWASP Top 10, CWE Top 25)
  - Custom organizational rules support
  - Memory and timeout optimization
- **Custom Rules**: `/backend/configs/custom-semgrep-rules.yaml`
- **Usage**: `--config=p/security-audit --config=p/owasp-top-ten`

#### 2. Trivy (Container/Filesystem Scanning) - Enhanced Implementation

- **Configuration**: Database caching with automatic updates
- **Features**:
  - Vulnerability scanning for containers and filesystems
  - Secret detection capabilities
  - Configuration misdetection
  - Daily database updates with caching
- **Cache Directory**: Configurable via `TRIVY_CACHE_DIR`
- **Usage**: `trivy fs --security-checks vuln,secret,config`

#### 3. GitLeaks (Secret Detection) - Enhanced Implementation

- **Configuration**: Custom regex patterns for org-specific secrets
- **Features**:
  - Git repository secret scanning
  - Custom configuration support
  - Secret redaction in outputs (security feature)
  - Organization-specific pattern detection
- **Custom Config**: `/backend/configs/gitleaks-custom.toml`
- **Security**: Automatically redacts detected secrets in logs

#### 4. Lynis (Infrastructure Scanning) - Enhanced Implementation

- **Configuration**: Baseline security assessment
- **Features**:
  - System hardening recommendations
  - Security configuration analysis
  - Baseline security establishment
  - Custom audit categories
- **Output**: Combined log and report data in JSON format
- **Usage**: `lynis audit system --quick`

#### 5. Bandit (Python SAST) - New Implementation

- **Configuration**: Python-specific security anti-patterns
- **Features**:
  - Python code security analysis
  - Confidence and severity levels
  - Custom exclusion patterns
  - Integration with Semgrep for comprehensive Python analysis
- **Usage**: `bandit -r . -f json --confidence-level=low`

#### 6. Safety (Python Dependencies) - New Implementation

- **Configuration**: Python dependency vulnerability scanning
- **Features**:
  - CVE database integration
  - Multiple dependency file support (requirements.txt, pyproject.toml, etc.)
  - Transitive dependency scanning
  - Custom ignore patterns
- **Supported Files**: requirements\*.txt, pyproject.toml, poetry.lock, Pipfile.lock

## Technical Implementation

### Enhanced Scanner Architecture

```python
class SecurityScanner:
    """Enhanced security scanner orchestrator with advanced features"""

    def __init__(self):
        self.scanners = {
            ScannerType.SEMGREP: EnhancedSemgrepScanner(),
            ScannerType.TRIVY: EnhancedTrivyScanner(),
            ScannerType.GITLEAKS: EnhancedGitLeaksScanner(),
            ScannerType.LYNIS: EnhancedLynisScanner(),
            ScannerType.BANDIT: BanditScanner(),
            ScannerType.SAFETY: SafetyScanner()
        }
```

### Key Enhancements

#### 1. Concurrency Control

- **Semaphore-based limiting**: `max_concurrent_scans` setting
- **Resource management**: Memory and timeout controls
- **Graceful error handling**: Failed scans don't block others

#### 2. Caching and Performance

- **Trivy database caching**: Daily updates with local storage
- **Custom cache directories**: `/opt/onyx/cache/trivy`
- **Scanner output caching**: Reduces redundant scans

#### 3. Custom Configuration Support

- **Organization-specific rules**: Custom Semgrep rules
- **Secret pattern customization**: GitLeaks custom patterns
- **Configurable exclusions**: Skip files and patterns

#### 4. Security Features

- **Secret redaction**: Prevents secret leakage in logs
- **Secure temporary files**: Automatic cleanup
- **Environment isolation**: Separate process execution

### Configuration Files

#### Custom Semgrep Rules (`custom-semgrep-rules.yaml`)

```yaml
rules:
  - id: hardcoded-secrets-custom
    pattern-either:
      - pattern: $VAR = "org_secret_$VALUE"
      - pattern: password = "$VALUE"
    message: Hardcoded secret detected
    severity: ERROR
```

#### Custom GitLeaks Config (`gitleaks-custom.toml`)

```toml
[[rules]]
id = "org-api-key"
description = "Organization API Key"
regex = '''(?i)(org|company)[-_]?(api[-_]?key|token)[-_]?[:=]\s*['"]?[a-zA-Z0-9]{20,}'''
```

## Installation and Setup

### Automated Installation

#### Linux/macOS

```bash
# Make script executable
chmod +x scripts/install_security_tools.sh

# Run installation
./scripts/install_security_tools.sh
```

#### Windows (PowerShell as Administrator)

```powershell
# Set execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run installation
.\scripts\install_security_tools.ps1
```

### Manual Installation

#### Python Tools

```bash
pip install bandit==1.7.5 safety==2.3.5 semgrep==1.45.0
```

#### System Tools

```bash
# Trivy
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh

# GitLeaks
curl -sfL https://github.com/gitleaks/gitleaks/releases/download/v8.18.0/gitleaks_8.18.0_linux_x64.tar.gz | tar -xz

# Lynis
apt-get install lynis  # Ubuntu/Debian
yum install lynis      # RHEL/CentOS
```

## Configuration

### Environment Variables

```bash
# Scanner paths
export SEMGREP_PATH="semgrep"
export TRIVY_PATH="trivy"
export GITLEAKS_PATH="gitleaks"
export LYNIS_PATH="lynis"
export BANDIT_PATH="bandit"
export SAFETY_PATH="safety"

# Custom configurations
export CUSTOM_SEMGREP_RULES_REPO="/path/to/custom/rules"
export CUSTOM_GITLEAKS_CONFIG="/path/to/gitleaks-custom.toml"

# Caching
export TRIVY_CACHE_DIR="/opt/onyx/cache/trivy"
export TRIVY_DB_UPDATE_INTERVAL="24"  # hours
```

### Scanner Settings

```python
# In config.py
enable_semgrep: bool = True
enable_trivy: bool = True
enable_gitleaks: bool = True
enable_lynis: bool = True
enable_bandit: bool = True
enable_safety: bool = True

scan_timeout: int = 600  # 10 minutes
max_concurrent_scans: int = 3
```

## Usage Examples

### Running All Scanners

```python
from services.scanner import security_scanner

# Run all enabled scanners
results = await security_scanner.run_all_scans("/path/to/repo")

# Run specific scanners
selected = [ScannerType.SEMGREP, ScannerType.BANDIT, ScannerType.SAFETY]
results = await security_scanner.run_all_scans("/path/to/repo", selected)
```

### Custom Configuration

```python
custom_config = {
    "semgrep": {
        "additional_rules": ["p/django", "p/flask"]
    },
    "gitleaks": {
        "custom_config": {
            "rules": [
                {
                    "id": "custom-pattern",
                    "regex": "custom-secret-pattern",
                    "description": "Custom secret pattern"
                }
            ]
        }
    },
    "bandit": {
        "exclude_paths": ["tests/", "examples/"],
        "skip_tests": True
    },
    "safety": {
        "ignore_ids": ["12345", "67890"]
    }
}

results = await security_scanner.run_all_scans(
    repo_path="/path/to/repo",
    custom_config=custom_config
)
```

### Health Check

```python
# Check scanner availability
health = await security_scanner.health_check()
print(health)
# Output: {'semgrep': True, 'trivy': True, 'gitleaks': True, ...}

# Update scanner databases
update_status = await security_scanner.update_scanner_databases()
```

## API Integration

### Scan Endpoint Enhancement

```python
@app.post("/api/v1/scan")
async def enhanced_scan_repository(request: ScanRequest):
    """Enhanced repository scanning with custom configuration"""

    # Custom scanner configuration
    custom_config = {
        "semgrep": {"additional_rules": request.semgrep_rules},
        "gitleaks": {"custom_config": request.gitleaks_config},
        "bandit": {"exclude_paths": request.exclude_paths},
        "safety": {"ignore_ids": request.ignore_vulnerabilities}
    }

    # Run enhanced scan
    results = await security_scanner.run_all_scans(
        repo_path=request.repo_path,
        selected_scanners=request.scanners,
        custom_config=custom_config
    )

    return {"scan_results": results}
```

## Performance Optimization

### Caching Strategy

1. **Trivy Database**: Daily updates with local caching
2. **Scanner Results**: Cache results for identical repository states
3. **Custom Rules**: Cache compiled rule sets

### Resource Management

1. **Memory Limits**: 2GB per scanner process
2. **Timeout Controls**: 10-minute default timeout
3. **Concurrency**: Maximum 3 concurrent scanners

### Optimization Tips

1. **Exclude Large Files**: Use `.gitignore` patterns
2. **Skip Binary Files**: Automatic binary file detection
3. **Incremental Scanning**: Compare with previous scan results

## Monitoring and Logging

### Health Monitoring

```bash
# Run health check
/opt/onyx/health_check.sh

# Windows
PowerShell -File "C:\ProgramData\ONYX\health_check.ps1"
```

### Logging Configuration

```python
# Structured logging for scanner operations
logger = structlog.get_logger("scanner")

logger.info("scan_started",
    scanner=scanner_type.value,
    repo_path=repo_path,
    duration=scan_duration)
```

## Security Considerations

### Secret Redaction

- **Automatic redaction**: GitLeaks output automatically redacted
- **Log sanitization**: No secrets in application logs
- **Secure cleanup**: Temporary files securely deleted

### Access Control

- **Process isolation**: Each scanner runs in isolated process
- **File permissions**: Restricted access to cache directories
- **Network security**: Outbound connections for database updates only

## Troubleshooting

### Common Issues

#### Scanner Not Found

```bash
# Check PATH
echo $PATH

# Verify installation
which semgrep trivy gitleaks bandit safety

# Health check
/opt/onyx/health_check.sh
```

#### Permission Errors

```bash
# Fix cache directory permissions
sudo chown -R $(whoami):$(whoami) /opt/onyx
chmod -R 755 /opt/onyx
```

#### Database Update Failures

```bash
# Manual Trivy database update
trivy image --download-db-only --cache-dir /opt/onyx/cache/trivy
```

### Log Analysis

```bash
# Scanner logs location
tail -f /opt/onyx/logs/scanner.log

# Error patterns
grep "ERROR" /opt/onyx/logs/scanner.log
```

## Future Enhancements

### Planned Features

1. **Machine Learning Integration**: AI-powered false positive reduction
2. **Custom Rule Engine**: Web-based rule management interface
3. **Baseline Scanning**: Historical comparison and drift detection
4. **Integration APIs**: Plugin system for additional scanners

### Performance Improvements

1. **Parallel Processing**: Multi-core scanner execution
2. **Smart Caching**: Content-based cache invalidation
3. **Incremental Scanning**: Delta-based vulnerability detection

## Compliance Mapping

### Security Frameworks

- **OWASP Top 10**: Covered by Semgrep and custom rules
- **CWE Top 25**: Mapped vulnerability categories
- **NIST Cybersecurity Framework**: Control mapping
- **SOC 2**: Security scanning evidence
- **PCI DSS**: Code security requirements

### Audit Support

- **Scan Reports**: Detailed vulnerability reports
- **Compliance Evidence**: Automated compliance reporting
- **Audit Trails**: Complete scan history and results

This enhanced security scanner integration provides a comprehensive, enterprise-ready security scanning solution with advanced customization, performance optimization, and security features.
