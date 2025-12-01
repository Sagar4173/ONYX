"""
Rule Testing Framework with Mandatory Dry-Run Validation
Tests security rules against known vulnerable repo corpus before production
"""
import asyncio
import logging
import json
import sqlite3
import git
import tempfile
import shutil
import subprocess
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import uuid
import statistics
import time

logger = logging.getLogger(__name__)

class TestSeverity(Enum):
    """Test result severity"""
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"

class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"

@dataclass
class VulnerableTestCase:
    """Known vulnerable test case"""
    case_id: str
    name: str
    description: str
    repository_url: str
    commit_hash: str
    file_path: str
    line_number: int
    vulnerability_type: str
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None
    expected_finding: bool = True  # Should this case trigger a finding?
    severity: TestSeverity = TestSeverity.MEDIUM

@dataclass
class TestResult:
    """Rule test execution result"""
    test_id: str
    rule_id: str
    test_case_id: str
    repository: str
    commit_hash: str
    execution_time: float
    memory_usage: float
    findings_found: List[Dict[str, Any]] = field(default_factory=list)
    expected_findings: List[Dict[str, Any]] = field(default_factory=list)
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    status: TestStatus = TestStatus.PENDING
    error_message: Optional[str] = None
    executed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class TestSuite:
    """Collection of test cases for comprehensive validation"""
    suite_id: str
    name: str
    description: str
    test_cases: List[VulnerableTestCase] = field(default_factory=list)
    minimum_precision: float = 0.95  # 95% precision required
    minimum_recall: float = 0.90     # 90% recall required
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class RuleTestingFramework:
    """Comprehensive rule testing framework with vulnerable repo corpus"""
    
    def __init__(self, data_dir: str = "data/testing"):
        """Initialize rule testing framework"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Database for test results
        self.db_path = self.data_dir / "rule_tests.db"
        
        # Test repositories directory
        self.test_repos_dir = self.data_dir / "test_repositories"
        self.test_repos_dir.mkdir(exist_ok=True)
        
        # Performance thresholds
        self.performance_thresholds = {
            "max_execution_time": 30.0,  # seconds per test case
            "max_memory_usage": 512,     # MB
            "timeout_seconds": 300       # 5 minutes total timeout
        }
        
        # Load default test suites
        self.default_test_suites = self._create_default_test_suites()
        
        # Initialize database
        self._init_database()
        
        # Setup test corpus (lazy initialization)
        self._corpus_initialized = False
    
    def _init_database(self):
        """Initialize test results database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS test_suites (
                    suite_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    test_cases TEXT,             -- JSON array
                    minimum_precision REAL,
                    minimum_recall REAL,
                    created_at TEXT
                )
                """)
                
                conn.execute("""
                CREATE TABLE IF NOT EXISTS test_cases (
                    case_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    repository_url TEXT NOT NULL,
                    commit_hash TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    line_number INTEGER,
                    vulnerability_type TEXT,
                    cwe_id TEXT,
                    cvss_score REAL,
                    expected_finding BOOLEAN,
                    severity TEXT,
                    created_at TEXT
                )
                """)
                
                conn.execute("""
                CREATE TABLE IF NOT EXISTS test_executions (
                    test_id TEXT PRIMARY KEY,
                    rule_id TEXT NOT NULL,
                    suite_id TEXT,
                    test_case_id TEXT NOT NULL,
                    repository TEXT,
                    commit_hash TEXT,
                    execution_time REAL,
                    memory_usage REAL,
                    findings_found TEXT,         -- JSON array
                    expected_findings TEXT,      -- JSON array
                    true_positives INTEGER,
                    false_positives INTEGER,
                    false_negatives INTEGER,
                    precision_score REAL,
                    recall_score REAL,
                    f1_score REAL,
                    status TEXT,
                    error_message TEXT,
                    executed_at TEXT,
                    FOREIGN KEY (test_case_id) REFERENCES test_cases (case_id)
                )
                """)
                
                conn.execute("""
                CREATE TABLE IF NOT EXISTS rule_certifications (
                    certification_id TEXT PRIMARY KEY,
                    rule_id TEXT NOT NULL,
                    suite_id TEXT NOT NULL,
                    overall_precision REAL,
                    overall_recall REAL,
                    overall_f1 REAL,
                    test_count INTEGER,
                    passed_tests INTEGER,
                    failed_tests INTEGER,
                    certification_passed BOOLEAN,
                    certified_at TEXT,
                    expires_at TEXT,
                    FOREIGN KEY (suite_id) REFERENCES test_suites (suite_id)
                )
                """)
                
                conn.execute("CREATE INDEX IF NOT EXISTS idx_executions_rule ON test_executions(rule_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_executions_status ON test_executions(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_certifications_rule ON rule_certifications(rule_id)")
                
        except Exception as e:
            logger.error(f"Failed to initialize test database: {e}")
            raise
    
    def _create_default_test_suites(self) -> List[TestSuite]:
        """Create default test suites with known vulnerable cases"""
        suites = []
        
        # SQL Injection Test Suite
        sql_injection_suite = TestSuite(
            suite_id="sql-injection-tests",
            name="SQL Injection Vulnerability Tests",
            description="Test cases for SQL injection detection rules",
            test_cases=[
                VulnerableTestCase(
                    case_id="sql-inject-1",
                    name="Basic SQL Injection",
                    description="Simple SQL injection in user input",
                    repository_url="https://github.com/OWASP/WebGoat.git",
                    commit_hash="main",
                    file_path="src/main/java/org/owasp/webgoat/lessons/SqlInjection.java",
                    line_number=45,
                    vulnerability_type="sql_injection",
                    cwe_id="CWE-89",
                    cvss_score=8.1,
                    severity=TestSeverity.HIGH
                ),
                VulnerableTestCase(
                    case_id="sql-inject-2",
                    name="Blind SQL Injection",
                    description="Time-based blind SQL injection",
                    repository_url="https://github.com/digininja/DVWA.git",
                    commit_hash="master",
                    file_path="vulnerabilities/sqli_blind/source/low.php",
                    line_number=12,
                    vulnerability_type="sql_injection",
                    cwe_id="CWE-89",
                    severity=TestSeverity.HIGH
                )
            ]
        )
        suites.append(sql_injection_suite)
        
        # XSS Test Suite
        xss_suite = TestSuite(
            suite_id="xss-tests",
            name="Cross-Site Scripting Tests",
            description="Test cases for XSS vulnerability detection",
            test_cases=[
                VulnerableTestCase(
                    case_id="xss-reflected-1",
                    name="Reflected XSS",
                    description="Basic reflected XSS vulnerability",
                    repository_url="https://github.com/OWASP/WebGoat.git",
                    commit_hash="main",
                    file_path="src/main/java/org/owasp/webgoat/lessons/CrossSiteScripting.java",
                    line_number=67,
                    vulnerability_type="xss",
                    cwe_id="CWE-79",
                    cvss_score=6.1,
                    severity=TestSeverity.MEDIUM
                ),
                VulnerableTestCase(
                    case_id="xss-stored-1",
                    name="Stored XSS",
                    description="Persistent XSS vulnerability",
                    repository_url="https://github.com/digininja/DVWA.git",
                    commit_hash="master",
                    file_path="vulnerabilities/xss_s/source/low.php",
                    line_number=8,
                    vulnerability_type="xss",
                    cwe_id="CWE-79",
                    severity=TestSeverity.HIGH
                )
            ]
        )
        suites.append(xss_suite)
        
        # Secret Exposure Test Suite
        secrets_suite = TestSuite(
            suite_id="secrets-exposure-tests",
            name="Secret Exposure Tests",
            description="Test cases for hardcoded secrets detection",
            test_cases=[
                VulnerableTestCase(
                    case_id="secret-api-key-1",
                    name="Hardcoded API Key",
                    description="API key hardcoded in source code",
                    repository_url="https://github.com/trufflesecurity/test_keys.git",
                    commit_hash="main",
                    file_path="keys/aws.py",
                    line_number=3,
                    vulnerability_type="secret_exposure",
                    cwe_id="CWE-798",
                    severity=TestSeverity.CRITICAL
                ),
                VulnerableTestCase(
                    case_id="secret-password-1",
                    name="Hardcoded Password",
                    description="Database password in configuration",
                    repository_url="https://github.com/trufflesecurity/test_keys.git",
                    commit_hash="main",
                    file_path="keys/database.js",
                    line_number=15,
                    vulnerability_type="secret_exposure",
                    cwe_id="CWE-798",
                    severity=TestSeverity.HIGH
                )
            ]
        )
        suites.append(secrets_suite)
        
        return suites
    
    async def _ensure_corpus_initialized(self):
        """Ensure test corpus is initialized"""
        if not self._corpus_initialized:
            await self._setup_test_corpus()
            self._corpus_initialized = True
    
    async def _setup_test_corpus(self):
        """Setup test repository corpus"""
        try:
            # Store default test suites
            for suite in self.default_test_suites:
                await self._store_test_suite(suite)
                
                # Store individual test cases
                for test_case in suite.test_cases:
                    await self._store_test_case(test_case)
            
            # Clone test repositories
            await self._clone_test_repositories()
            
        except Exception as e:
            logger.error(f"Failed to setup test corpus: {e}")
    
    async def _clone_test_repositories(self):
        """Clone test repositories for local testing"""
        try:
            unique_repos = set()
            for suite in self.default_test_suites:
                for test_case in suite.test_cases:
                    unique_repos.add((test_case.repository_url, test_case.commit_hash))
            
            for repo_url, commit_hash in unique_repos:
                repo_name = repo_url.split('/')[-1].replace('.git', '')
                repo_path = self.test_repos_dir / repo_name
                
                if not repo_path.exists():
                    try:
                        logger.info(f"Cloning test repository: {repo_url}")
                        repo = git.Repo.clone_from(repo_url, repo_path)
                        
                        if commit_hash != "main" and commit_hash != "master":
                            repo.git.checkout(commit_hash)
                            
                    except Exception as e:
                        logger.warning(f"Failed to clone {repo_url}: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to clone test repositories: {e}")
    
    async def run_rule_certification(self, rule_id: str, rule_content: str,
                                   rule_format: str, suite_id: Optional[str] = None) -> Dict[str, Any]:
        """Run mandatory certification tests for a rule"""
        try:
            # Ensure test corpus is initialized
            await self._ensure_corpus_initialized()
            
            # Get test suite(s)
            if suite_id:
                test_suites = [await self._get_test_suite(suite_id)]
            else:
                test_suites = await self._get_all_test_suites()
            
            certification_results = []
            
            for suite in test_suites:
                if not suite:
                    continue
                    
                logger.info(f"Running certification tests for rule {rule_id} against suite {suite.name}")
                
                suite_results = await self._run_suite_tests(rule_id, rule_content, rule_format, suite)
                certification_results.append(suite_results)
            
            # Calculate overall certification status
            overall_result = self._calculate_overall_certification(certification_results)
            
            # Store certification record
            await self._store_certification_result(rule_id, overall_result)
            
            return overall_result
            
        except Exception as e:
            logger.error(f"Failed to run rule certification: {e}")
            return {"error": str(e), "certified": False}
    
    async def _run_suite_tests(self, rule_id: str, rule_content: str,
                             rule_format: str, suite: TestSuite) -> Dict[str, Any]:
        """Run all tests in a suite against a rule"""
        try:
            test_results = []
            
            for test_case in suite.test_cases:
                logger.info(f"Running test case: {test_case.name}")
                
                result = await self._run_single_test(
                    rule_id, rule_content, rule_format, test_case, suite.suite_id
                )
                test_results.append(result)
                
                # Store individual test result
                await self._store_test_result(result)
            
            # Calculate suite metrics
            suite_metrics = self._calculate_suite_metrics(test_results, suite)
            
            return {
                "suite_id": suite.suite_id,
                "suite_name": suite.name,
                "test_results": test_results,
                "metrics": suite_metrics,
                "certification_passed": (
                    suite_metrics["precision"] >= suite.minimum_precision and
                    suite_metrics["recall"] >= suite.minimum_recall
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to run suite tests: {e}")
            return {"error": str(e), "certification_passed": False}
    
    async def _run_single_test(self, rule_id: str, rule_content: str,
                             rule_format: str, test_case: VulnerableTestCase,
                             suite_id: str) -> TestResult:
        """Run a single test case against a rule"""
        test_result = TestResult(
            test_id=str(uuid.uuid4()),
            rule_id=rule_id,
            test_case_id=test_case.case_id,
            repository=test_case.repository_url.split('/')[-1].replace('.git', ''),
            commit_hash=test_case.commit_hash
        )
        
        try:
            test_result.status = TestStatus.RUNNING
            start_time = time.time()
            
            # Execute rule against test case
            findings = await self._execute_rule_on_test_case(
                rule_content, rule_format, test_case
            )
            
            test_result.execution_time = time.time() - start_time
            test_result.memory_usage = 50.0  # Mock memory usage
            test_result.findings_found = findings
            
            # Calculate metrics
            test_result = self._calculate_test_metrics(test_result, test_case)
            
            test_result.status = TestStatus.PASSED if test_result.f1_score > 0.5 else TestStatus.FAILED
            
        except Exception as e:
            test_result.status = TestStatus.ERROR
            test_result.error_message = str(e)
            test_result.execution_time = time.time() - start_time
            logger.error(f"Test execution failed: {e}")
        
        return test_result
    
    async def _execute_rule_on_test_case(self, rule_content: str, rule_format: str,
                                       test_case: VulnerableTestCase) -> List[Dict[str, Any]]:
        """Execute a security rule against a specific test case"""
        findings = []
        
        try:
            repo_path = self.test_repos_dir / test_case.repository_url.split('/')[-1].replace('.git', '')
            target_file = repo_path / test_case.file_path
            
            if not target_file.exists():
                logger.warning(f"Test file not found: {target_file}")
                return findings
            
            # Mock rule execution based on format
            if rule_format.lower() == "semgrep":
                findings = await self._run_semgrep_test(rule_content, target_file, test_case)
            elif rule_format.lower() == "regex":
                findings = await self._run_regex_test(rule_content, target_file, test_case)
            elif rule_format.lower() == "custom":
                findings = await self._run_custom_test(rule_content, target_file, test_case)
            
            return findings
            
        except Exception as e:
            logger.error(f"Failed to execute rule on test case: {e}")
            return []
    
    async def _run_semgrep_test(self, rule_content: str, target_file: Path,
                              test_case: VulnerableTestCase) -> List[Dict[str, Any]]:
        """Run Semgrep rule against test case"""
        try:
            # Create temporary rule file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as rule_file:
                rule_file.write(rule_content)
                rule_file_path = rule_file.name
            
            try:
                # Run Semgrep
                cmd = [
                    "semgrep",
                    "--config", rule_file_path,
                    "--json",
                    str(target_file)
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.performance_thresholds["timeout_seconds"]
                )
                
                if result.returncode == 0:
                    output = json.loads(result.stdout)
                    findings = []
                    
                    for finding in output.get("results", []):
                        findings.append({
                            "file": finding.get("path"),
                            "line": finding.get("start", {}).get("line"),
                            "column": finding.get("start", {}).get("col"),
                            "message": finding.get("extra", {}).get("message"),
                            "severity": finding.get("extra", {}).get("severity"),
                            "rule_id": finding.get("check_id")
                        })
                    
                    return findings
                else:
                    logger.warning(f"Semgrep execution failed: {result.stderr}")
                    return []
                    
            finally:
                # Clean up temp file
                Path(rule_file_path).unlink(missing_ok=True)
                
        except subprocess.TimeoutExpired:
            logger.warning(f"Semgrep test timed out for {test_case.name}")
            return []
        except Exception as e:
            logger.error(f"Semgrep test failed: {e}")
            return []
    
    async def _run_regex_test(self, rule_content: str, target_file: Path,
                            test_case: VulnerableTestCase) -> List[Dict[str, Any]]:
        """Run regex rule against test case"""
        try:
            import re
            
            rule_data = json.loads(rule_content)
            pattern = rule_data.get("pattern", "")
            flags = rule_data.get("flags", [])
            
            # Convert flags
            regex_flags = 0
            if "i" in flags:
                regex_flags |= re.IGNORECASE
            if "m" in flags:
                regex_flags |= re.MULTILINE
            if "s" in flags:
                regex_flags |= re.DOTALL
            
            compiled_regex = re.compile(pattern, regex_flags)
            
            # Read target file
            content = target_file.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            
            findings = []
            for i, line in enumerate(lines, 1):
                matches = compiled_regex.finditer(line)
                for match in matches:
                    findings.append({
                        "file": str(target_file),
                        "line": i,
                        "column": match.start(),
                        "message": f"Pattern match: {match.group()}",
                        "severity": rule_data.get("severity", "medium"),
                        "match": match.group()
                    })
            
            return findings
            
        except Exception as e:
            logger.error(f"Regex test failed: {e}")
            return []
    
    async def _run_custom_test(self, rule_content: str, target_file: Path,
                             test_case: VulnerableTestCase) -> List[Dict[str, Any]]:
        """Run custom rule against test case"""
        try:
            # Mock custom rule execution
            # In practice, this would execute the custom logic safely
            
            rule_data = json.loads(rule_content)
            logic = rule_data.get("logic", "")
            
            # Simple mock: if the logic mentions the vulnerability type, consider it a match
            if test_case.vulnerability_type.lower() in logic.lower():
                return [{
                    "file": str(target_file),
                    "line": test_case.line_number,
                    "column": 1,
                    "message": f"Custom rule detected {test_case.vulnerability_type}",
                    "severity": rule_data.get("severity", "medium"),
                    "rule_type": "custom"
                }]
            
            return []
            
        except Exception as e:
            logger.error(f"Custom test failed: {e}")
            return []
    
    def _calculate_test_metrics(self, test_result: TestResult,
                              test_case: VulnerableTestCase) -> TestResult:
        """Calculate precision, recall, and F1 score for test result"""
        try:
            # Expected findings based on test case
            if test_case.expected_finding:
                test_result.expected_findings = [{
                    "file": test_case.file_path,
                    "line": test_case.line_number,
                    "vulnerability_type": test_case.vulnerability_type
                }]
            
            # Calculate metrics
            expected_count = len(test_result.expected_findings)
            found_count = len(test_result.findings_found)
            
            # Simple matching: check if we found something at the expected location
            true_positives = 0
            if expected_count > 0 and found_count > 0:
                for expected in test_result.expected_findings:
                    for found in test_result.findings_found:
                        if (str(expected["line"]) == str(found.get("line", "")) and
                            expected["file"] in str(found.get("file", ""))):
                            true_positives += 1
                            break
            
            test_result.true_positives = true_positives
            test_result.false_positives = found_count - true_positives
            test_result.false_negatives = expected_count - true_positives
            
            # Calculate precision, recall, F1
            if found_count > 0:
                test_result.precision = true_positives / found_count
            else:
                test_result.precision = 1.0 if expected_count == 0 else 0.0
            
            if expected_count > 0:
                test_result.recall = true_positives / expected_count
            else:
                test_result.recall = 1.0 if found_count == 0 else 0.0
            
            if test_result.precision + test_result.recall > 0:
                test_result.f1_score = 2 * (test_result.precision * test_result.recall) / (test_result.precision + test_result.recall)
            else:
                test_result.f1_score = 0.0
            
            return test_result
            
        except Exception as e:
            logger.error(f"Failed to calculate test metrics: {e}")
            test_result.precision = 0.0
            test_result.recall = 0.0
            test_result.f1_score = 0.0
            return test_result
    
    def _calculate_suite_metrics(self, test_results: List[TestResult],
                               suite: TestSuite) -> Dict[str, Any]:
        """Calculate overall metrics for a test suite"""
        try:
            if not test_results:
                return {"precision": 0.0, "recall": 0.0, "f1_score": 0.0, "passed_tests": 0, "total_tests": 0}
            
            # Filter successful tests
            successful_tests = [r for r in test_results if r.status == TestStatus.PASSED or r.status == TestStatus.FAILED]
            
            if not successful_tests:
                return {"precision": 0.0, "recall": 0.0, "f1_score": 0.0, "passed_tests": 0, "total_tests": len(test_results)}
            
            # Calculate averages
            avg_precision = statistics.mean([r.precision for r in successful_tests])
            avg_recall = statistics.mean([r.recall for r in successful_tests])
            avg_f1 = statistics.mean([r.f1_score for r in successful_tests])
            
            passed_tests = len([r for r in test_results if r.status == TestStatus.PASSED])
            
            return {
                "precision": avg_precision,
                "recall": avg_recall,
                "f1_score": avg_f1,
                "passed_tests": passed_tests,
                "total_tests": len(test_results),
                "pass_rate": passed_tests / len(test_results) if test_results else 0.0,
                "avg_execution_time": statistics.mean([r.execution_time for r in successful_tests]),
                "max_execution_time": max([r.execution_time for r in successful_tests]),
                "certification_passed": (
                    avg_precision >= suite.minimum_precision and
                    avg_recall >= suite.minimum_recall
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate suite metrics: {e}")
            return {"precision": 0.0, "recall": 0.0, "f1_score": 0.0, "passed_tests": 0, "total_tests": len(test_results)}
    
    def _calculate_overall_certification(self, certification_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall certification result across all suites"""
        try:
            if not certification_results:
                return {"certified": False, "reason": "No test results"}
            
            successful_suites = [r for r in certification_results if "metrics" in r]
            
            if not successful_suites:
                return {"certified": False, "reason": "All test suites failed"}
            
            # All suites must pass for overall certification
            all_passed = all(r.get("certification_passed", False) for r in successful_suites)
            
            # Calculate overall metrics
            overall_precision = statistics.mean([r["metrics"]["precision"] for r in successful_suites])
            overall_recall = statistics.mean([r["metrics"]["recall"] for r in successful_suites])
            overall_f1 = statistics.mean([r["metrics"]["f1_score"] for r in successful_suites])
            
            total_tests = sum([r["metrics"]["total_tests"] for r in successful_suites])
            passed_tests = sum([r["metrics"]["passed_tests"] for r in successful_suites])
            
            return {
                "certified": all_passed,
                "overall_precision": overall_precision,
                "overall_recall": overall_recall,
                "overall_f1": overall_f1,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "pass_rate": passed_tests / total_tests if total_tests > 0 else 0.0,
                "suite_results": certification_results,
                "certification_timestamp": datetime.now(timezone.utc).isoformat(),
                "reason": "All requirements met" if all_passed else "Failed to meet precision/recall requirements"
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate overall certification: {e}")
            return {"certified": False, "reason": f"Calculation error: {e}"}
    
    async def _store_test_suite(self, suite: TestSuite):
        """Store test suite in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                INSERT OR REPLACE INTO test_suites (
                    suite_id, name, description, test_cases,
                    minimum_precision, minimum_recall, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    suite.suite_id,
                    suite.name,
                    suite.description,
                    json.dumps([{
                        "case_id": tc.case_id,
                        "name": tc.name,
                        "description": tc.description,
                        "repository_url": tc.repository_url,
                        "commit_hash": tc.commit_hash,
                        "file_path": tc.file_path,
                        "line_number": tc.line_number,
                        "vulnerability_type": tc.vulnerability_type,
                        "cwe_id": tc.cwe_id,
                        "cvss_score": tc.cvss_score,
                        "expected_finding": tc.expected_finding,
                        "severity": tc.severity.value
                    } for tc in suite.test_cases]),
                    suite.minimum_precision,
                    suite.minimum_recall,
                    suite.created_at.isoformat()
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store test suite: {e}")
            raise
    
    async def _store_test_case(self, test_case: VulnerableTestCase):
        """Store individual test case in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                INSERT OR REPLACE INTO test_cases (
                    case_id, name, description, repository_url, commit_hash,
                    file_path, line_number, vulnerability_type, cwe_id,
                    cvss_score, expected_finding, severity, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    test_case.case_id,
                    test_case.name,
                    test_case.description,
                    test_case.repository_url,
                    test_case.commit_hash,
                    test_case.file_path,
                    test_case.line_number,
                    test_case.vulnerability_type,
                    test_case.cwe_id,
                    test_case.cvss_score,
                    test_case.expected_finding,
                    test_case.severity.value,
                    datetime.now(timezone.utc).isoformat()
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store test case: {e}")
            raise
    
    async def _store_test_result(self, test_result: TestResult):
        """Store test execution result in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                INSERT OR REPLACE INTO test_executions (
                    test_id, rule_id, test_case_id, repository, commit,
                    execution_time, memory_usage, findings_found, expected_findings,
                    true_positives, false_positives, false_negatives,
                    precision_score, recall_score, f1_score, status,
                    error_message, executed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    test_result.test_id,
                    test_result.rule_id,
                    test_result.test_case_id,
                    test_result.repository,
                    test_result.commit,
                    test_result.execution_time,
                    test_result.memory_usage,
                    json.dumps(test_result.findings_found),
                    json.dumps(test_result.expected_findings),
                    test_result.true_positives,
                    test_result.false_positives,
                    test_result.false_negatives,
                    test_result.precision,
                    test_result.recall,
                    test_result.f1_score,
                    test_result.status.value,
                    test_result.error_message,
                    test_result.executed_at.isoformat()
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store test result: {e}")
            raise
    
    async def _store_certification_result(self, rule_id: str, certification_result: Dict[str, Any]):
        """Store certification result in database"""
        try:
            certification_id = str(uuid.uuid4())
            expires_at = datetime.now(timezone.utc) + timedelta(days=90)  # 90-day certification
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                INSERT INTO rule_certifications (
                    certification_id, rule_id, suite_id, overall_precision,
                    overall_recall, overall_f1, test_count, passed_tests,
                    failed_tests, certification_passed, certified_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    certification_id,
                    rule_id,
                    "overall",  # Could be specific suite ID
                    certification_result.get("overall_precision", 0.0),
                    certification_result.get("overall_recall", 0.0),
                    certification_result.get("overall_f1", 0.0),
                    certification_result.get("total_tests", 0),
                    certification_result.get("passed_tests", 0),
                    certification_result.get("total_tests", 0) - certification_result.get("passed_tests", 0),
                    certification_result.get("certified", False),
                    certification_result.get("certification_timestamp"),
                    expires_at.isoformat()
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store certification result: {e}")
            raise
    
    async def _get_test_suite(self, suite_id: str) -> Optional[TestSuite]:
        """Get test suite by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM test_suites WHERE suite_id = ?",
                    (suite_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    test_cases_data = json.loads(row[3]) if row[3] else []
                    test_cases = []
                    
                    for tc_data in test_cases_data:
                        test_case = VulnerableTestCase(
                            case_id=tc_data["case_id"],
                            name=tc_data["name"],
                            description=tc_data["description"],
                            repository_url=tc_data["repository_url"],
                            commit_hash=tc_data["commit_hash"],
                            file_path=tc_data["file_path"],
                            line_number=tc_data["line_number"],
                            vulnerability_type=tc_data["vulnerability_type"],
                            cwe_id=tc_data.get("cwe_id"),
                            cvss_score=tc_data.get("cvss_score"),
                            expected_finding=tc_data.get("expected_finding", True),
                            severity=TestSeverity(tc_data.get("severity", "medium"))
                        )
                        test_cases.append(test_case)
                    
                    return TestSuite(
                        suite_id=row[0],
                        name=row[1],
                        description=row[2],
                        test_cases=test_cases,
                        minimum_precision=row[4],
                        minimum_recall=row[5],
                        created_at=datetime.fromisoformat(row[6])
                    )
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to get test suite: {e}")
            return None
    
    async def _get_all_test_suites(self) -> List[TestSuite]:
        """Get all test suites"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT suite_id FROM test_suites")
                suite_ids = [row[0] for row in cursor.fetchall()]
            
            suites = []
            for suite_id in suite_ids:
                suite = await self._get_test_suite(suite_id)
                if suite:
                    suites.append(suite)
            
            return suites
            
        except Exception as e:
            logger.error(f"Failed to get all test suites: {e}")
            return []
    
    async def get_rule_certification_status(self, rule_id: str) -> Dict[str, Any]:
        """Get certification status for a rule"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                SELECT * FROM rule_certifications 
                WHERE rule_id = ? 
                ORDER BY certified_at DESC 
                LIMIT 1
                """, (rule_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        "rule_id": rule_id,
                        "certified": bool(row[9]),
                        "overall_precision": row[3],
                        "overall_recall": row[4],
                        "overall_f1": row[5],
                        "test_count": row[6],
                        "passed_tests": row[7],
                        "failed_tests": row[8],
                        "certified_at": row[10],
                        "expires_at": row[11],
                        "is_valid": datetime.fromisoformat(row[11]) > datetime.now(timezone.utc) if row[11] else False
                    }
                else:
                    return {
                        "rule_id": rule_id,
                        "certified": False,
                        "reason": "No certification tests run"
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get certification status: {e}")
            return {"rule_id": rule_id, "certified": False, "error": str(e)}

# Export main classes
__all__ = [
    'RuleTestingFramework', 'TestResult', 'TestSuite', 'VulnerableTestCase',
    'TestStatus', 'TestSeverity'
]
