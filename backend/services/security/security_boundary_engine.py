"""
Security Boundaries for Custom Rules
Provides sandboxed execution, resource limits, and adversarial testing protection
"""
import asyncio
import logging
import subprocess
import psutil
import signal
import time
# docker - Lazy-loaded on-demand for container scanning
import tempfile
import os
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
import json
import uuid
import contextlib
import sys

# Conditional import for Unix-specific resource module
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    # resource module is not available on Windows
    HAS_RESOURCE = False
    resource = None

logger = logging.getLogger(__name__)

@dataclass
class ResourceLimits:
    """Resource limits for rule execution"""
    cpu_limit: float = 1.0  # CPU cores
    memory_limit_mb: int = 256  # Memory in MB
    timeout_per_file: int = 5  # Seconds per file
    timeout_total: int = 30  # Total seconds per rule
    max_matches: int = 10000  # Maximum matches per rule
    max_file_size_mb: int = 10  # Maximum file size to scan

@dataclass
class ResourceUsage:
    """Tracking resource usage during rule execution"""
    cpu_time: float = 0.0
    memory_peak_mb: float = 0.0
    wall_time: float = 0.0
    matches_count: int = 0
    files_processed: int = 0
    killed_by_limit: bool = False
    kill_reason: Optional[str] = None

@dataclass
class AdversarialTestCase:
    """Adversarial test case to validate security boundaries"""
    name: str
    rule_type: str
    content: str
    expected_behavior: str  # timeout, memory_limit, cpu_limit, etc.
    description: str

class SecurityBoundaryEngine:
    """Security boundary enforcement for custom rule execution"""
    
    def __init__(self, data_dir: str = "security_boundaries"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Default limits
        self.default_limits = ResourceLimits()
        
        # Docker client for containerized execution (lazy-loaded)
        self.docker_client = None
        self.docker_available = False
        
        # Adversarial test corpus
        self.adversarial_tests = self._create_adversarial_corpus()
        
        # Resource monitoring
        self.active_executions = {}
    
    async def _ensure_docker(self):
        """Lazy-load docker client when needed"""
        if self.docker_client is not None:
            return self.docker_available
        
        try:
            from utils.lazy_imports import get_docker
            docker = await get_docker()
            if docker:
                self.docker_client = docker.from_env()
                self.docker_available = True
                logger.info("✅ Docker client initialized for sandboxed execution")
            else:
                logger.warning("Docker SDK installation failed, using process isolation")
                self.docker_available = False
        except Exception as e:
            logger.warning(f"Docker not available, falling back to process isolation: {e}")
            self.docker_available = False
        
        return self.docker_available
        
    def _create_adversarial_corpus(self) -> List[AdversarialTestCase]:
        """Create corpus of adversarial test cases"""
        return [
            AdversarialTestCase(
                name="Catastrophic Backtracking Regex",
                rule_type="regex",
                content=r"(a+)+b",
                expected_behavior="timeout",
                description="Classic catastrophic backtracking pattern"
            ),
            AdversarialTestCase(
                name="Nested Quantifiers Regex",
                rule_type="regex", 
                content=r"(a*)*b",
                expected_behavior="timeout",
                description="Nested quantifiers causing exponential backtracking"
            ),
            AdversarialTestCase(
                name="Memory Bomb Regex",
                rule_type="regex",
                content=r"(?:(?:(?:(?:a)?a)?a)?a)*",
                expected_behavior="memory_limit",
                description="Regex designed to consume excessive memory"
            ),
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
            AdversarialTestCase(
                name="Recursive Wildcard Glob",
                rule_type="glob",
                content="**/*/**/*/**/*/**/*",
                expected_behavior="timeout",
                description="Deeply recursive glob pattern"
            ),
            AdversarialTestCase(
                name="CPU Intensive Regex",
                rule_type="regex",
                content=r"a{1000000}",
                expected_behavior="cpu_limit",
                description="Regex requiring intensive CPU computation"
            )
        ]
    
    async def execute_rule_safely(self, rule_content: str, rule_type: str, 
                                 target_files: List[str], 
                                 limits: Optional[ResourceLimits] = None) -> Tuple[Dict[str, Any], ResourceUsage]:
        """Execute a rule with security boundaries"""
        if limits is None:
            limits = self.default_limits
        
        execution_id = str(uuid.uuid4())
        logger.info(f"Starting secure rule execution: {execution_id}")
        
        # Ensure docker is available if needed
        await self._ensure_docker()
        
        # Choose execution method
        if self.docker_available:
            return await self._execute_in_container(execution_id, rule_content, rule_type, target_files, limits)
        else:
            return await self._execute_in_process(execution_id, rule_content, rule_type, target_files, limits)
    
    async def _execute_in_container(self, execution_id: str, rule_content: str, 
                                   rule_type: str, target_files: List[str],
                                   limits: ResourceLimits) -> Tuple[Dict[str, Any], ResourceUsage]:
        """Execute rule in Docker container with strict resource limits"""
        try:
            # Create temporary directory for execution
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Write rule content
                rule_file = temp_path / f"rule.{rule_type}"
                rule_file.write_text(rule_content)
                
                # Copy target files
                target_dir = temp_path / "targets"
                target_dir.mkdir()
                for file_path in target_files:
                    if Path(file_path).exists():
                        target_file = target_dir / Path(file_path).name
                        target_file.write_text(Path(file_path).read_text())
                
                # Create execution script
                script_content = self._create_execution_script(rule_type, str(rule_file), str(target_dir))
                script_file = temp_path / "execute.py"
                script_file.write_text(script_content)
                
                # Get docker.types dynamically
                from utils.lazy_imports import try_import_docker
                docker_module = try_import_docker()
                if not docker_module:
                    raise Exception("Docker SDK not available")
                
                # Resource limits for container
                container_limits = {
                    'mem_limit': f"{limits.memory_limit_mb}m",
                    'cpus': str(limits.cpu_limit),
                    'ulimits': [
                        docker_module.types.Ulimit(name='nproc', soft=100, hard=100),  # Process limit
                        docker_module.types.Ulimit(name='fsize', soft=limits.max_file_size_mb * 1024 * 1024),  # File size
                    ],
                    'security_opt': ['no-new-privileges:true'],  # Security options
                    'cap_drop': ['ALL'],  # Drop all capabilities
                    'read_only': True,  # Read-only filesystem
                    'tmpfs': {'/tmp': 'size=100m,noexec'},  # Temporary filesystem
                }
                
                start_time = time.time()
                usage = ResourceUsage()
                
                try:
                    # Run container with timeout
                    container = self.docker_client.containers.run(
                        'python:3.11-alpine',
                        f'timeout {limits.timeout_total} python /workspace/execute.py',
                        volumes={str(temp_path): {'bind': '/workspace', 'mode': 'ro'}},
                        working_dir='/workspace',
                        detach=True,
                        **container_limits
                    )
                    
                    # Monitor container execution
                    result = container.wait(timeout=limits.timeout_total + 5)
                    logs = container.logs().decode('utf-8')
                    
                    # Get resource stats
                    stats = container.stats(stream=False)
                    if stats:
                        usage.memory_peak_mb = stats.get('memory', {}).get('max_usage', 0) / (1024 * 1024)
                    
                    container.remove()
                    
                    usage.wall_time = time.time() - start_time
                    
                    # Parse execution results
                    execution_results = self._parse_execution_results(logs, result['StatusCode'])
                    
                    return execution_results, usage
                    
                except Exception as e:
                    # Handle docker errors
                    if docker_module and hasattr(docker_module, 'errors') and isinstance(e, docker_module.errors.ContainerError):
                        usage.killed_by_limit = True
                        usage.kill_reason = f"Container error: {e}"
                        logger.warning(f"Container execution failed: {e}")
                    else:
                        raise
                    return {"error": "Container execution failed", "killed": True}, usage
                    
                except Exception as e:
                    usage.killed_by_limit = True
                    usage.kill_reason = f"Timeout or resource limit: {e}"
                    logger.warning(f"Container execution timeout/limit: {e}")
                    return {"error": "Execution timeout or resource limit", "killed": True}, usage
                    
        except Exception as e:
            logger.error(f"Container execution setup failed: {e}")
            usage = ResourceUsage()
            usage.killed_by_limit = True
            usage.kill_reason = f"Setup failed: {e}"
            return {"error": "Container setup failed"}, usage
    
    async def _execute_in_process(self, execution_id: str, rule_content: str,
                                 rule_type: str, target_files: List[str],
                                 limits: ResourceLimits) -> Tuple[Dict[str, Any], ResourceUsage]:
        """Execute rule in isolated process with resource limits"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Write rule and target files
                rule_file = temp_path / f"rule.{rule_type}"
                rule_file.write_text(rule_content)
                
                target_dir = temp_path / "targets"
                target_dir.mkdir()
                for file_path in target_files:
                    if Path(file_path).exists():
                        target_file = target_dir / Path(file_path).name
                        target_file.write_text(Path(file_path).read_text())
                
                # Create execution script
                script_content = self._create_execution_script(rule_type, str(rule_file), str(target_dir))
                script_file = temp_path / "execute.py"
                script_file.write_text(script_content)
                
                # Start resource monitoring
                usage = ResourceUsage()
                start_time = time.time()
                
                # Execute with resource limits
                result = await self._run_with_limits(
                    [sys.executable, str(script_file)],
                    limits,
                    execution_id
                )
                
                usage.wall_time = time.time() - start_time
                
                # Parse results
                if result['timeout']:
                    usage.killed_by_limit = True
                    usage.kill_reason = "Timeout"
                    return {"error": "Execution timeout", "killed": True}, usage
                
                execution_results = self._parse_execution_results(
                    result['stdout'], 
                    result['returncode']
                )
                
                usage.memory_peak_mb = result.get('peak_memory_mb', 0)
                usage.cpu_time = result.get('cpu_time', 0)
                
                return execution_results, usage
                
        except Exception as e:
            logger.error(f"Process execution failed: {e}")
            usage = ResourceUsage()
            usage.killed_by_limit = True
            usage.kill_reason = f"Process execution failed: {e}"
            return {"error": "Process execution failed"}, usage
    
    def _create_execution_script(self, rule_type: str, rule_file: str, target_dir: str) -> str:
        """Create Python script for rule execution"""
        if rule_type == "regex":
            return f"""
import re
import json
import sys
import os
import time
from pathlib import Path

def execute_regex_rule():
    try:
        with open('{rule_file}', 'r') as f:
            pattern = f.read().strip()
        
        regex = re.compile(pattern)
        matches = []
        files_processed = 0
        
        for file_path in Path('{target_dir}').rglob('*'):
            if file_path.is_file():
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    file_matches = []
                    
                    for match in regex.finditer(content):
                        file_matches.append({{
                            'start': match.start(),
                            'end': match.end(),
                            'text': match.group()
                        }})
                        
                        # Limit matches to prevent DoS
                        if len(file_matches) > 1000:
                            break
                    
                    if file_matches:
                        matches.append({{
                            'file': str(file_path),
                            'matches': file_matches
                        }})
                    
                    files_processed += 1
                    
                except Exception as e:
                    pass  # Skip problematic files
        
        result = {{
            'success': True,
            'matches': matches,
            'files_processed': files_processed,
            'total_matches': sum(len(m['matches']) for m in matches)
        }}
        
        print(json.dumps(result))
        
    except Exception as e:
        result = {{
            'success': False,
            'error': str(e)
        }}
        print(json.dumps(result))
        sys.exit(1)

if __name__ == '__main__':
    execute_regex_rule()
"""
        elif rule_type == "semgrep":
            return f"""
import json
import subprocess
import sys
from pathlib import Path

def execute_semgrep_rule():
    try:
        cmd = [
            'semgrep',
            '--config={rule_file}',
            '--json',
            '--no-git-ignore',
            '{target_dir}'
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=25  # Leave buffer for cleanup
        )
        
        if result.returncode == 0:
            output = {{
                'success': True,
                'semgrep_output': json.loads(result.stdout)
            }}
        else:
            output = {{
                'success': False,
                'error': result.stderr
            }}
        
        print(json.dumps(output))
        
    except subprocess.TimeoutExpired:
        output = {{
            'success': False,
            'error': 'Semgrep execution timeout'
        }}
        print(json.dumps(output))
        sys.exit(1)
        
    except Exception as e:
        output = {{
            'success': False,
            'error': str(e)
        }}
        print(json.dumps(output))
        sys.exit(1)

if __name__ == '__main__':
    execute_semgrep_rule()
"""
        else:
            return """
import json
import sys

result = {
    'success': False,
    'error': 'Unsupported rule type'
}
print(json.dumps(result))
sys.exit(1)
"""
    
    async def _run_with_limits(self, cmd: List[str], limits: ResourceLimits, 
                              execution_id: str) -> Dict[str, Any]:
        """Run command with resource limits"""
        try:
            # Set resource limits for the process (Unix only)
            def set_limits():
                if HAS_RESOURCE:
                    # Memory limit (soft and hard)
                    memory_bytes = limits.memory_limit_mb * 1024 * 1024
                    resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
                    
                    # CPU time limit
                    resource.setrlimit(resource.RLIMIT_CPU, (limits.timeout_total, limits.timeout_total))
                    
                    # File size limit
                    file_size_bytes = limits.max_file_size_mb * 1024 * 1024
                    resource.setrlimit(resource.RLIMIT_FSIZE, (file_size_bytes, file_size_bytes))
            
            # Start process with limits (preexec_fn only works on Unix)
            if HAS_RESOURCE:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    preexec_fn=set_limits
                )
            else:
                # Windows fallback - no resource limits
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
            )
            
            self.active_executions[execution_id] = process
            
            try:
                # Wait with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=limits.timeout_total
                )
                
                return {
                    'stdout': stdout.decode('utf-8'),
                    'stderr': stderr.decode('utf-8'),
                    'returncode': process.returncode,
                    'timeout': False
                }
                
            except asyncio.TimeoutError:
                # Kill the process
                process.kill()
                await process.wait()
                
                return {
                    'stdout': '',
                    'stderr': 'Process killed due to timeout',
                    'returncode': -1,
                    'timeout': True
                }
            
            finally:
                if execution_id in self.active_executions:
                    del self.active_executions[execution_id]
                    
        except Exception as e:
            logger.error(f"Failed to run command with limits: {e}")
            return {
                'stdout': '',
                'stderr': f'Execution failed: {e}',
                'returncode': -1,
                'timeout': False
            }
    
    def _parse_execution_results(self, output: str, return_code: int) -> Dict[str, Any]:
        """Parse execution results from script output"""
        try:
            if return_code == 0 and output.strip():
                return json.loads(output.strip())
            else:
                return {
                    'success': False,
                    'error': 'Execution failed or no output',
                    'return_code': return_code
                }
        except json.JSONDecodeError:
            return {
                'success': False,
                'error': 'Invalid JSON output',
                'raw_output': output
            }
    
    async def test_adversarial_cases(self) -> Dict[str, Any]:
        """Test security boundaries against adversarial test cases"""
        logger.info("Starting adversarial test suite...")
        
        results = {
            'test_start': datetime.now(timezone.utc).isoformat(),
            'total_tests': len(self.adversarial_tests),
            'passed': 0,
            'failed': 0,
            'test_results': []
        }
        
        # Create test target files
        test_files = self._create_test_target_files()
        
        for test_case in self.adversarial_tests:
            logger.info(f"Running adversarial test: {test_case.name}")
            
            try:
                # Execute with tight limits for adversarial tests
                tight_limits = ResourceLimits(
                    cpu_limit=0.5,
                    memory_limit_mb=128,
                    timeout_per_file=2,
                    timeout_total=10,
                    max_matches=1000
                )
                
                execution_result, usage = await self.execute_rule_safely(
                    test_case.content,
                    test_case.rule_type,
                    test_files,
                    tight_limits
                )
                
                # Evaluate if boundary worked as expected
                boundary_effective = self._evaluate_boundary_effectiveness(
                    test_case, execution_result, usage
                )
                
                test_result = {
                    'test_name': test_case.name,
                    'expected_behavior': test_case.expected_behavior,
                    'boundary_effective': boundary_effective,
                    'killed_by_limit': usage.killed_by_limit,
                    'kill_reason': usage.kill_reason,
                    'resource_usage': {
                        'cpu_time': usage.cpu_time,
                        'memory_peak_mb': usage.memory_peak_mb,
                        'wall_time': usage.wall_time,
                        'matches_count': usage.matches_count
                    },
                    'execution_result': execution_result
                }
                
                if boundary_effective:
                    results['passed'] += 1
                    logger.info(f"✅ Adversarial test passed: {test_case.name}")
                else:
                    results['failed'] += 1
                    logger.warning(f"❌ Adversarial test failed: {test_case.name}")
                
                results['test_results'].append(test_result)
                
            except Exception as e:
                logger.error(f"❌ Adversarial test error: {test_case.name} - {e}")
                results['failed'] += 1
                results['test_results'].append({
                    'test_name': test_case.name,
                    'boundary_effective': False,
                    'error': str(e)
                })
        
        results['test_end'] = datetime.now(timezone.utc).isoformat()
        results['success_rate'] = results['passed'] / results['total_tests'] if results['total_tests'] > 0 else 0
        
        logger.info(f"Adversarial testing complete: {results['passed']}/{results['total_tests']} passed")
        
        return results
    
    def _create_test_target_files(self) -> List[str]:
        """Create test target files for adversarial testing"""
        test_dir = self.data_dir / "adversarial_targets"
        test_dir.mkdir(exist_ok=True)
        
        test_files = []
        
        # Large file to test memory/CPU limits
        large_file = test_dir / "large_file.py"
        large_content = "a" * 1000000 + "\n" + "def function():\n    pass\n" * 10000
        large_file.write_text(large_content)
        test_files.append(str(large_file))
        
        # File with many lines for match testing
        many_lines_file = test_dir / "many_lines.js"
        many_lines_content = "\n".join([f"var x{i} = 'value{i}';" for i in range(10000)])
        many_lines_file.write_text(many_lines_content)
        test_files.append(str(many_lines_file))
        
        # Complex nested structure
        complex_file = test_dir / "complex.java"
        complex_content = """
public class ComplexClass {
    """ + "\n".join([f"    private String field{i};" for i in range(1000)]) + """
    
    public void complexMethod() {
        """ + "\n".join([f"        System.out.println(\"Line {i}\");" for i in range(1000)]) + """
    }
}
        """
        complex_file.write_text(complex_content)
        test_files.append(str(complex_file))
        
        return test_files
    
    def _evaluate_boundary_effectiveness(self, test_case: AdversarialTestCase,
                                       execution_result: Dict[str, Any],
                                       usage: ResourceUsage) -> bool:
        """Evaluate if security boundary was effective for test case"""
        expected = test_case.expected_behavior.lower()
        
        if expected == "timeout":
            return usage.killed_by_limit and "timeout" in (usage.kill_reason or "").lower()
        elif expected == "memory_limit":
            return usage.killed_by_limit and ("memory" in (usage.kill_reason or "").lower() or usage.memory_peak_mb > 100)
        elif expected == "cpu_limit":
            return usage.killed_by_limit and ("cpu" in (usage.kill_reason or "").lower() or usage.cpu_time > 8)
        elif expected == "max_matches":
            matches = execution_result.get('total_matches', 0)
            return matches <= 1000  # Within acceptable limit
        else:
            # General expectation that rule should be contained
            return usage.wall_time < 15 and usage.memory_peak_mb < 200
    
    async def get_security_metrics(self) -> Dict[str, Any]:
        """Get security boundary metrics"""
        return {
            'docker_available': self.docker_available,
            'default_limits': {
                'cpu_limit': self.default_limits.cpu_limit,
                'memory_limit_mb': self.default_limits.memory_limit_mb,
                'timeout_total': self.default_limits.timeout_total,
                'max_matches': self.default_limits.max_matches
            },
            'adversarial_tests_count': len(self.adversarial_tests),
            'active_executions': len(self.active_executions)
        }

# Export main classes
__all__ = ['SecurityBoundaryEngine', 'ResourceLimits', 'ResourceUsage', 'AdversarialTestCase']
