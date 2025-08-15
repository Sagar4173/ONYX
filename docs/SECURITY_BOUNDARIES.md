# 🔒 Security Boundaries Implementation

## Overview

Security boundaries are critical when allowing users to upload custom security rules (regex, Semgrep patterns, etc.). Without proper boundaries, malicious or poorly designed rules can crash the scanner, consume excessive resources, or cause security vulnerabilities.

## 🚨 Why Security Boundaries Are Critical

### The Risk
- **Resource Exhaustion**: Catastrophic backtracking in regex can consume 100% CPU
- **Memory Bombs**: Complex patterns can allocate gigabytes of memory
- **Denial of Service**: One bad rule can crash the entire scanning system
- **Path Traversal**: Malicious rules could attempt to access unauthorized files
- **Code Injection**: Improperly sandboxed execution could lead to RCE

### Without Boundaries
```python
# Dangerous regex that can cause DoS
pattern = r"(a+)+b"
text = "a" * 1000 + "c"  # No 'b' at end
re.match(pattern, text)  # Hangs indefinitely, 100% CPU
```

## 🛡️ Our Security Boundary Implementation

### Location
- **Main Engine**: `backend/services/security_boundary_engine.py`
- **Integration**: `backend/services/rule_parsing_engine.py`
- **API Endpoints**: `backend/routes/god_level_security.py`

### 1. Sandboxed Execution

#### Container-Based Isolation (Preferred)
```python
container_limits = {
    'mem_limit': '256m',           # Memory limit
    'cpus': '1.0',                 # CPU cores
    'ulimits': [
        Ulimit(name='nproc', soft=100, hard=100),     # Process limit
        Ulimit(name='fsize', soft=10*1024*1024)       # File size limit
    ],
    'security_opt': ['no-new-privileges:true'],       # Security options
    'cap_drop': ['ALL'],                              # Drop all capabilities
    'read_only': True,                                # Read-only filesystem
    'tmpfs': {'/tmp': 'size=100m,noexec'}            # Temporary filesystem
}
```

#### Process-Based Isolation (Fallback)
```python
def set_limits():
    # Memory limit
    memory_bytes = limits.memory_limit_mb * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
    
    # CPU time limit
    resource.setrlimit(resource.RLIMIT_CPU, (limits.timeout_total, limits.timeout_total))
    
    # File size limit
    file_size_bytes = limits.max_file_size_mb * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_FSIZE, (file_size_bytes, file_size_bytes))
```

### 2. Resource Accounting

#### Default Limits
```python
@dataclass
class ResourceLimits:
    cpu_limit: float = 1.0          # CPU cores
    memory_limit_mb: int = 256      # Memory in MB
    timeout_per_file: int = 5       # Seconds per file
    timeout_total: int = 30         # Total seconds per rule
    max_matches: int = 10000        # Maximum matches per rule
    max_file_size_mb: int = 10      # Maximum file size to scan
```

#### Real-Time Monitoring
```python
@dataclass
class ResourceUsage:
    cpu_time: float = 0.0           # CPU time consumed
    memory_peak_mb: float = 0.0     # Peak memory usage
    wall_time: float = 0.0          # Total execution time
    matches_count: int = 0          # Number of matches found
    files_processed: int = 0        # Files processed
    killed_by_limit: bool = False   # Was execution terminated?
    kill_reason: Optional[str] = None  # Reason for termination
```

### 3. Adversarial Testing

#### Evil Rule Corpus
Our platform maintains a corpus of malicious rules to validate boundaries:

```python
adversarial_tests = [
    # Catastrophic backtracking
    AdversarialTestCase(
        name="Catastrophic Backtracking Regex",
        rule_type="regex",
        content=r"(a+)+b",
        expected_behavior="timeout",
        description="Classic catastrophic backtracking pattern"
    ),
    
    # Memory bomb
    AdversarialTestCase(
        name="Memory Bomb Regex",
        rule_type="regex", 
        content=r"(?:(?:(?:(?:a)?a)?a)?a)*",
        expected_behavior="memory_limit",
        description="Regex designed to consume excessive memory"
    ),
    
    # Match everything
    AdversarialTestCase(
        name="Match Everything Semgrep",
        rule_type="semgrep",
        content="""
rules:
  - id: match-everything
    pattern: $X
    message: Matches everything
    languages: [python, javascript, java, go, c, cpp]
    severity: INFO
        """,
        expected_behavior="max_matches",
        description="Semgrep rule that matches every token"
    ),
    
    # Recursive wildcards
    AdversarialTestCase(
        name="Recursive Wildcard Glob",
        rule_type="glob",
        content="**/*/**/*/**/*/**/*",
        expected_behavior="timeout",
        description="Deeply recursive glob pattern"
    )
]
```

#### Validation Process
```python
async def validate_boundaries():
    """Run adversarial tests in CI/CD"""
    for test_case in adversarial_tests:
        execution_result, usage = await execute_rule_safely(
            rule_content=test_case.content,
            rule_type=test_case.rule_type,
            target_files=vulnerable_files,
            limits=strict_limits
        )
        
        # Verify boundary held
        assert usage.killed_by_limit or execution_time < threshold
        assert usage.memory_peak_mb < memory_threshold
```

## 🔧 Implementation Details

### Security Boundary Engine

#### Class Structure
```python
class SecurityBoundaryEngine:
    def __init__(self, data_dir: str = "security_boundaries"):
        self.default_limits = ResourceLimits()
        self.docker_client = docker.from_env()  # Container support
        self.adversarial_tests = self._create_adversarial_corpus()
        
    async def execute_rule_safely(self, rule_content: str, rule_type: str, 
                                 target_files: List[str], 
                                 limits: ResourceLimits) -> Tuple[Dict, ResourceUsage]:
        """Execute rule with strict security boundaries"""
        
    async def test_adversarial_cases(self) -> Dict[str, Any]:
        """Test boundaries against evil rule corpus"""
```

#### Container Execution
```python
async def _execute_in_container(self, execution_id: str, rule_content: str, 
                               rule_type: str, target_files: List[str],
                               limits: ResourceLimits) -> Tuple[Dict, ResourceUsage]:
    """Execute rule in Docker container with strict resource limits"""
    
    # Create isolated execution environment
    with tempfile.TemporaryDirectory() as temp_dir:
        # Write rule and target files
        # Set up container with limits
        # Execute with monitoring
        # Return results and usage metrics
```

#### Process Execution
```python
async def _execute_in_process(self, execution_id: str, rule_content: str,
                             rule_type: str, target_files: List[str],
                             limits: ResourceLimits) -> Tuple[Dict, ResourceUsage]:
    """Execute rule in isolated process with resource limits"""
    
    # Set resource limits
    # Monitor execution
    # Kill if limits exceeded
    # Return results
```

### Integration with Rule Parser

#### Enhanced Validation
```python
async def test_rule_with_security_boundaries(self, rule_id: str, 
                                           test_files: Optional[List[str]] = None) -> Dict[str, Any]:
    """Test rule execution with security boundaries"""
    
    # Get rule content
    rule = await self.get_rule_by_id(rule_id)
    
    # Set conservative limits for testing
    test_limits = ResourceLimits(
        cpu_limit=0.5,
        memory_limit_mb=128,
        timeout_per_file=3,
        timeout_total=15,
        max_matches=1000,
        max_file_size_mb=5
    )
    
    # Execute with security boundaries
    execution_result, resource_usage = await self.security_engine.execute_rule_safely(
        rule_content=rule["content"],
        rule_type=rule["format"],
        target_files=test_files,
        limits=test_limits
    )
    
    # Analyze safety
    safety_assessment = self._analyze_execution_safety(execution_result, resource_usage)
    return safety_assessment
```

### API Endpoints

#### Security Boundary Testing
```bash
# Test adversarial cases
POST /api/v1/god-level/security/boundaries/test

# Test specific rule with boundaries
POST /api/v1/god-level/rule/test-boundary/{rule_id}
{
    "test_files": ["optional", "list", "of", "files"]
}
```

## 📊 Monitoring and Metrics

### Resource Usage Tracking
```python
# Per-rule execution metrics
{
    "rule_id": "custom-rule-123",
    "resource_usage": {
        "cpu_time": 2.1,
        "memory_peak_mb": 45.2,
        "wall_time": 3.4,
        "matches_count": 156,
        "files_processed": 23,
        "killed_by_limit": false,
        "kill_reason": null
    },
    "safety_assessment": {
        "overall_safety": "safe",
        "concerns": [],
        "recommendations": []
    }
}
```

### Safety Assessment
```python
def _analyze_execution_safety(self, execution_result: Dict[str, Any], 
                             resource_usage: ResourceUsage) -> Dict[str, Any]:
    """Analyze execution safety based on results and resource usage"""
    
    safety_assessment = {
        "overall_safety": "safe",
        "concerns": [],
        "recommendations": []
    }
    
    # Check if killed by limits
    if resource_usage.killed_by_limit:
        safety_assessment["overall_safety"] = "dangerous"
        safety_assessment["concerns"].append(f"Rule killed by security boundary: {resource_usage.kill_reason}")
        safety_assessment["recommendations"].append("Review rule complexity and resource requirements")
    
    # Check resource usage thresholds
    if resource_usage.memory_peak_mb > 100:
        safety_assessment["concerns"].append("High memory usage detected")
    
    if resource_usage.wall_time > 10:
        safety_assessment["concerns"].append("Slow execution time")
    
    return safety_assessment
```

## 🧪 Testing

### Running Security Boundary Tests
```bash
# Run comprehensive security boundary tests
cd scripts
python test_security_boundaries.py
```

### Expected Output
```
🔒============================================================🔒
🔒 SECURITY BOUNDARIES TEST SUITE
🔒============================================================🔒
🔥 Testing Catastrophic Backtracking Protection...
✅ Catastrophic backtracking protection EFFECTIVE
🧨 Testing Adversarial Test Suite...
✅ Adversarial protection EFFECTIVE (5/6 passed)

🔒======================================================================🔒
🔒 SECURITY BOUNDARIES TEST RESULTS
🔒======================================================================🔒
📊 Test Categories: 2/2 passed
🛡️ Overall Security Status: EXCELLENT
⚡ Security Features Operational: 2

🔒 Validated Security Features:
   ✅ boundary_enforcement
   ✅ adversarial_protection

🎉 SECURITY BOUNDARIES ARE OPERATIONAL! 🎉
🔒 Your platform is protected against malicious rules!
```

### CI/CD Integration
```yaml
# .github/workflows/security-boundaries.yml
name: Security Boundaries Tests
on: [push, pull_request]

jobs:
  security-boundaries:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
      - name: Run security boundary tests
        run: |
          cd scripts
          python test_security_boundaries.py
      - name: Fail if boundaries ineffective
        run: |
          # Check test results and fail build if boundaries don't hold
          python check_boundary_results.py
```

## 🛠️ Configuration

### Environment Variables
```bash
# Security boundary configuration
SECURITY_BOUNDARIES_ENABLED=true
DEFAULT_CPU_LIMIT=1.0
DEFAULT_MEMORY_LIMIT_MB=256
DEFAULT_TIMEOUT_TOTAL=30
DOCKER_AVAILABLE=true
ADVERSARIAL_TEST_ON_STARTUP=true
```

### Custom Limits per Environment
```python
# Development - loose limits
DEV_LIMITS = ResourceLimits(
    cpu_limit=2.0,
    memory_limit_mb=512,
    timeout_total=60
)

# Production - strict limits
PROD_LIMITS = ResourceLimits(
    cpu_limit=0.5,
    memory_limit_mb=128,
    timeout_total=15
)

# Testing - very strict limits
TEST_LIMITS = ResourceLimits(
    cpu_limit=0.1,
    memory_limit_mb=64,
    timeout_total=5
)
```

## 🚀 Benefits

### Security
- **Zero Trust**: Every rule executed in isolation
- **Resource Protection**: System resources protected from abuse
- **Proactive Defense**: Adversarial testing catches issues before production

### Reliability
- **Predictable Performance**: Resource limits ensure consistent performance
- **Graceful Degradation**: Bad rules don't crash the system
- **Monitoring**: Complete visibility into rule resource usage

### Compliance
- **Audit Trail**: Complete logging of rule execution and resource usage
- **Risk Assessment**: Automated safety assessment for every rule
- **Policy Enforcement**: Configurable limits based on organizational needs

## 🔮 Future Enhancements

### Planned Features
- **Machine Learning**: Predict resource usage based on rule patterns
- **Dynamic Limits**: Adjust limits based on system load
- **Advanced Sandboxing**: Additional security layers (SELinux, gVisor)
- **Performance Optimization**: Cache compiled rules with safety validation

### Research Areas
- **Static Analysis**: Detect problematic patterns without execution
- **Fuzzing**: Automated generation of adversarial test cases
- **Behavioral Analysis**: Monitor rule behavior over time

---

## 🎯 Summary

Our security boundaries implementation provides enterprise-grade protection against malicious custom rules through:

1. **Multi-Layer Sandboxing**: Container and process isolation
2. **Resource Limits**: CPU, memory, time, and match count restrictions
3. **Adversarial Testing**: Continuous validation against evil rule corpus
4. **Real-Time Monitoring**: Complete resource usage tracking
5. **Safety Assessment**: Automated analysis of rule behavior

This ensures that your security platform remains robust and reliable even when processing untrusted custom security rules.

**🔒 Your platform is now protected against malicious rules! 🔒**
