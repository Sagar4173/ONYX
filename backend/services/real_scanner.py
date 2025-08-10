"""
Real Security Scanner Implementation
Integrates actual security tools to perform genuine vulnerability scanning
"""
import os
import json
import tempfile
import shutil
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import git
from git import Repo
import requests

logger = logging.getLogger(__name__)

class RealSecurityScanner:
    """
    Real security scanner that uses actual security tools to scan repositories
    """
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the security scanner
        
        Args:
            temp_dir: Directory for temporary repository clones
        """
        self.temp_dir = temp_dir or tempfile.mkdtemp(prefix="secdev_scan_")
        self.findings = []
        self.scan_metadata = {}
    
    async def scan_repository(self, repository_url: str, branch: str = "main") -> Dict[str, Any]:
        """
        Perform comprehensive security scan of a repository
        
        Args:
            repository_url: GitHub repository URL
            branch: Branch to scan
            
        Returns:
            Dictionary containing scan results and findings
        """
        logger.info(f"🔍 Starting real security scan of {repository_url}")
        
        try:
            # Clone repository
            repo_path = await self._clone_repository(repository_url, branch)
            
            # Perform different types of scans
            findings = []
            
            # 1. Static Application Security Testing (SAST)
            logger.info("🔍 Running SAST scan...")
            sast_findings = await self._run_sast_scan(repo_path)
            findings.extend(sast_findings)
            
            # 2. Secrets Detection
            logger.info("🔍 Running secrets detection...")
            secrets_findings = await self._run_secrets_scan(repo_path)
            findings.extend(secrets_findings)
            
            # 3. Dependency Vulnerability Scan (SCA)
            logger.info("🔍 Running dependency scan...")
            dependency_findings = await self._run_dependency_scan(repo_path)
            findings.extend(dependency_findings)
            
            # 4. Code Quality and Security Issues
            logger.info("🔍 Running code quality scan...")
            quality_findings = await self._run_code_quality_scan(repo_path)
            findings.extend(quality_findings)
            
            # Categorize findings by severity
            findings_by_severity = self._categorize_findings(findings)
            
            # Get repository metadata
            repo_metadata = await self._get_repo_metadata(repo_path)
            
            result = {
                'total_findings': len(findings),
                'findings_by_severity': findings_by_severity,
                'detailed_findings': findings,
                'repository_metadata': repo_metadata,
                'scan_metadata': {
                    'scan_types': ['sast', 'secrets', 'sca', 'code_quality'],
                    'tools_used': ['bandit', 'detect-secrets', 'safety', 'custom'],
                    'scanned_files': self._count_files(repo_path),
                    'scan_completed': True
                }
            }
            
            logger.info(f"✅ Scan completed: {len(findings)} findings found")
            return result
            
        except Exception as e:
            logger.error(f"❌ Scan failed: {e}")
            raise
        finally:
            # Cleanup
            await self._cleanup(repo_path if 'repo_path' in locals() else None)
    
    async def _clone_repository(self, repository_url: str, branch: str) -> str:
        """Clone repository to temporary directory"""
        repo_name = repository_url.split('/')[-1].replace('.git', '')
        clone_path = os.path.join(self.temp_dir, repo_name)
        
        try:
            logger.info(f"📥 Cloning repository to {clone_path}")
            repo = Repo.clone_from(repository_url, clone_path, branch=branch, depth=1)
            logger.info(f"✅ Repository cloned successfully")
            return clone_path
        except Exception as e:
            logger.error(f"❌ Failed to clone repository: {e}")
            raise
    
    async def _run_sast_scan(self, repo_path: str) -> List[Dict[str, Any]]:
        """Run Static Application Security Testing using Bandit (Python)"""
        findings = []
        
        try:
            # Check if there are Python files to scan
            python_files = list(Path(repo_path).rglob("*.py"))
            if not python_files:
                logger.info("No Python files found for SAST scan")
                return findings
            
            logger.info(f"Found {len(python_files)} Python files to scan")
            
            # Run Bandit scan
            bandit_cmd = [
                'bandit', '-r', repo_path, '-f', 'json', '--quiet'
            ]
            
            result = subprocess.run(
                bandit_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            
            if result.stdout:
                bandit_data = json.loads(result.stdout)
                
                for issue in bandit_data.get('results', []):
                    finding = {
                        'title': issue.get('test_name', 'Unknown Security Issue'),
                        'severity': self._map_bandit_severity(issue.get('issue_severity', 'LOW')),
                        'scanner': 'Bandit-SAST',
                        'description': issue.get('issue_text', 'Security issue detected'),
                        'file_path': self._get_relative_path(issue.get('filename', ''), repo_path),
                        'line_number': issue.get('line_number', 0),
                        'rule_id': issue.get('test_id', 'UNKNOWN'),
                        'cwe_id': issue.get('more_info', '').split('/')[-1] if issue.get('more_info') else None,
                        'confidence': issue.get('issue_confidence', 'UNDEFINED'),
                        'code_snippet': issue.get('code', '').strip()[:200],
                        'owasp_category': self._get_owasp_category(issue.get('test_id', ''))
                    }
                    findings.append(finding)
                    
            logger.info(f"🔍 Bandit found {len(findings)} security issues")
            
        except subprocess.CalledProcessError as e:
            logger.warning(f"Bandit scan failed: {e}")
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Bandit output: {e}")
        except Exception as e:
            logger.error(f"SAST scan error: {e}")
        
        return findings
    
    async def _run_secrets_scan(self, repo_path: str) -> List[Dict[str, Any]]:
        """Run secrets detection using detect-secrets"""
        findings = []
        
        try:
            # Run detect-secrets scan
            secrets_cmd = [
                'detect-secrets', 'scan', '--all-files', '--force-use-all-plugins', repo_path
            ]
            
            result = subprocess.run(
                secrets_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            
            if result.stdout:
                secrets_data = json.loads(result.stdout)
                
                for file_path, secrets in secrets_data.get('results', {}).items():
                    for secret in secrets:
                        finding = {
                            'title': f"Secret Detected: {secret.get('type', 'Unknown')}",
                            'severity': 'high',  # Secrets are generally high severity
                            'scanner': 'detect-secrets',
                            'description': f"Potential {secret.get('type', 'secret')} detected in source code",
                            'file_path': self._get_relative_path(file_path, repo_path),
                            'line_number': secret.get('line_number', 0),
                            'rule_id': f"SECRET_{secret.get('type', 'UNKNOWN').upper()}",
                            'confidence': 'HIGH',
                            'owasp_category': 'A02:2021 - Cryptographic Failures'
                        }
                        findings.append(finding)
                        
            logger.info(f"🔍 Secrets scan found {len(findings)} potential secrets")
            
        except subprocess.CalledProcessError as e:
            logger.warning(f"Secrets scan failed: {e}")
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse secrets scan output: {e}")
        except Exception as e:
            logger.error(f"Secrets scan error: {e}")
        
        return findings
    
    async def _run_dependency_scan(self, repo_path: str) -> List[Dict[str, Any]]:
        """Run dependency vulnerability scan using Safety (Python)"""
        findings = []
        
        try:
            # Check for requirements files
            req_files = [
                'requirements.txt', 'requirements-dev.txt', 'dev-requirements.txt',
                'Pipfile', 'pyproject.toml', 'setup.py'
            ]
            
            found_req_files = []
            for req_file in req_files:
                req_path = os.path.join(repo_path, req_file)
                if os.path.exists(req_path):
                    found_req_files.append(req_file)
            
            if not found_req_files:
                logger.info("No Python dependency files found for vulnerability scan")
                return findings
            
            logger.info(f"Found dependency files: {found_req_files}")
            
            # Run Safety check
            for req_file in found_req_files:
                if req_file == 'requirements.txt':
                    safety_cmd = ['safety', 'check', '--json', '-r', req_file]
                    
                    result = subprocess.run(
                        safety_cmd,
                        capture_output=True,
                        text=True,
                        cwd=repo_path
                    )
                    
                    if result.stdout:
                        try:
                            safety_data = json.loads(result.stdout)
                            
                            for vuln in safety_data:
                                finding = {
                                    'title': f"Vulnerable Dependency: {vuln.get('package_name', 'Unknown')}",
                                    'severity': self._map_vulnerability_severity(vuln.get('advisory', '')),
                                    'scanner': 'Safety-SCA',
                                    'description': vuln.get('advisory', 'Vulnerable dependency detected'),
                                    'file_path': req_file,
                                    'line_number': 1,
                                    'rule_id': f"VULN_DEP_{vuln.get('vulnerability_id', 'UNKNOWN')}",
                                    'cve_id': vuln.get('cve', None),
                                    'package_name': vuln.get('package_name', 'Unknown'),
                                    'vulnerable_spec': vuln.get('vulnerable_spec', ''),
                                    'owasp_category': 'A06:2021 - Vulnerable and Outdated Components'
                                }
                                findings.append(finding)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse Safety output for {req_file}")
                            
            logger.info(f"🔍 Dependency scan found {len(findings)} vulnerable packages")
            
        except subprocess.CalledProcessError as e:
            logger.warning(f"Dependency scan failed: {e}")
        except Exception as e:
            logger.error(f"Dependency scan error: {e}")
        
        return findings
    
    async def _run_code_quality_scan(self, repo_path: str) -> List[Dict[str, Any]]:
        """Run custom code quality and security checks"""
        findings = []
        
        try:
            # Check for common security anti-patterns
            security_patterns = [
                {
                    'pattern': r'(?i)(password|pwd|pass)\s*=\s*["\'][^"\']+["\']',
                    'title': 'Hardcoded Password',
                    'severity': 'high',
                    'description': 'Password appears to be hardcoded in source code'
                },
                {
                    'pattern': r'(?i)(api[_-]?key|apikey|access[_-]?token)\s*=\s*["\'][^"\']+["\']',
                    'title': 'Hardcoded API Key',
                    'severity': 'high',
                    'description': 'API key appears to be hardcoded in source code'
                },
                {
                    'pattern': r'eval\s*\(',
                    'title': 'Use of eval()',
                    'severity': 'medium',
                    'description': 'Use of eval() function can lead to code injection vulnerabilities'
                },
                {
                    'pattern': r'exec\s*\(',
                    'title': 'Use of exec()',
                    'severity': 'medium',
                    'description': 'Use of exec() function can lead to code injection vulnerabilities'
                }
            ]
            
            import re
            
            # Scan source files
            source_extensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cs', '.php']
            
            for ext in source_extensions:
                files = list(Path(repo_path).rglob(f"*{ext}"))
                
                for file_path in files:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            lines = content.split('\n')
                            
                            for pattern_info in security_patterns:
                                pattern = re.compile(pattern_info['pattern'])
                                
                                for line_num, line in enumerate(lines, 1):
                                    if pattern.search(line):
                                        finding = {
                                            'title': pattern_info['title'],
                                            'severity': pattern_info['severity'],
                                            'scanner': 'Custom-CodeQuality',
                                            'description': pattern_info['description'],
                                            'file_path': self._get_relative_path(str(file_path), repo_path),
                                            'line_number': line_num,
                                            'rule_id': f"CUSTOM_{pattern_info['title'].upper().replace(' ', '_')}",
                                            'code_snippet': line.strip()[:100],
                                            'owasp_category': 'A02:2021 - Cryptographic Failures'
                                        }
                                        findings.append(finding)
                    except Exception as e:
                        logger.warning(f"Error scanning file {file_path}: {e}")
                        continue
            
            logger.info(f"🔍 Code quality scan found {len(findings)} issues")
            
        except Exception as e:
            logger.error(f"Code quality scan error: {e}")
        
        return findings
    
    def _categorize_findings(self, findings: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize findings by severity"""
        severity_counts = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0
        }
        
        for finding in findings:
            severity = finding.get('severity', 'info').lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        return severity_counts
    
    async def _get_repo_metadata(self, repo_path: str) -> Dict[str, Any]:
        """Extract repository metadata"""
        try:
            repo = Repo(repo_path)
            
            # Get latest commit info
            latest_commit = repo.head.commit
            
            return {
                'commit_hash': latest_commit.hexsha,
                'commit_message': latest_commit.message.strip(),
                'commit_author': str(latest_commit.author),
                'commit_date': latest_commit.committed_datetime.isoformat(),
                'branch': repo.active_branch.name if repo.active_branch else 'unknown'
            }
        except Exception as e:
            logger.warning(f"Failed to get repo metadata: {e}")
            return {}
    
    def _count_files(self, repo_path: str) -> Dict[str, int]:
        """Count files by type"""
        counts = {}
        
        try:
            for file_path in Path(repo_path).rglob("*"):
                if file_path.is_file():
                    ext = file_path.suffix.lower()
                    counts[ext] = counts.get(ext, 0) + 1
        except Exception as e:
            logger.warning(f"Error counting files: {e}")
        
        return counts
    
    def _get_relative_path(self, full_path: str, repo_path: str) -> str:
        """Get relative path from repository root"""
        try:
            return os.path.relpath(full_path, repo_path)
        except:
            return full_path
    
    def _map_bandit_severity(self, bandit_severity: str) -> str:
        """Map Bandit severity to our severity levels"""
        mapping = {
            'HIGH': 'high',
            'MEDIUM': 'medium',
            'LOW': 'low'
        }
        return mapping.get(bandit_severity.upper(), 'low')
    
    def _map_vulnerability_severity(self, advisory: str) -> str:
        """Map vulnerability advisory to severity"""
        advisory_lower = advisory.lower()
        
        if any(word in advisory_lower for word in ['critical', 'severe', 'remote code execution', 'rce']):
            return 'critical'
        elif any(word in advisory_lower for word in ['high', 'dangerous', 'exploit']):
            return 'high'
        elif any(word in advisory_lower for word in ['medium', 'moderate']):
            return 'medium'
        else:
            return 'low'
    
    def _get_owasp_category(self, test_id: str) -> str:
        """Map Bandit test ID to OWASP category"""
        owasp_mapping = {
            'B101': 'A02:2021 - Cryptographic Failures',
            'B102': 'A03:2021 - Injection',
            'B103': 'A05:2021 - Security Misconfiguration',
            'B104': 'A02:2021 - Cryptographic Failures',
            'B105': 'A02:2021 - Cryptographic Failures',
            'B106': 'A02:2021 - Cryptographic Failures',
            'B107': 'A02:2021 - Cryptographic Failures',
            'B108': 'A05:2021 - Security Misconfiguration',
            'B110': 'A06:2021 - Vulnerable and Outdated Components',
            'B201': 'A03:2021 - Injection',
            'B301': 'A05:2021 - Security Misconfiguration',
            'B302': 'A05:2021 - Security Misconfiguration',
            'B303': 'A02:2021 - Cryptographic Failures',
            'B304': 'A02:2021 - Cryptographic Failures',
            'B305': 'A02:2021 - Cryptographic Failures',
            'B306': 'A05:2021 - Security Misconfiguration',
            'B307': 'A03:2021 - Injection',
            'B308': 'A05:2021 - Security Misconfiguration',
            'B309': 'A02:2021 - Cryptographic Failures',
            'B310': 'A06:2021 - Vulnerable and Outdated Components',
            'B311': 'A02:2021 - Cryptographic Failures',
            'B312': 'A05:2021 - Security Misconfiguration',
            'B313': 'A03:2021 - Injection',
            'B314': 'A03:2021 - Injection',
            'B315': 'A03:2021 - Injection',
            'B316': 'A03:2021 - Injection',
            'B317': 'A03:2021 - Injection',
            'B318': 'A03:2021 - Injection',
            'B319': 'A03:2021 - Injection',
            'B320': 'A03:2021 - Injection',
            'B321': 'A05:2021 - Security Misconfiguration',
            'B322': 'A03:2021 - Injection',
            'B323': 'A06:2021 - Vulnerable and Outdated Components',
            'B324': 'A02:2021 - Cryptographic Failures',
            'B325': 'A05:2021 - Security Misconfiguration',
            'B401': 'A03:2021 - Injection',
            'B402': 'A05:2021 - Security Misconfiguration',
            'B403': 'A05:2021 - Security Misconfiguration',
            'B404': 'A06:2021 - Vulnerable and Outdated Components',
            'B405': 'A03:2021 - Injection',
            'B406': 'A03:2021 - Injection',
            'B407': 'A03:2021 - Injection',
            'B408': 'A03:2021 - Injection',
            'B409': 'A03:2021 - Injection',
            'B410': 'A03:2021 - Injection',
            'B411': 'A03:2021 - Injection',
            'B412': 'A03:2021 - Injection',
            'B501': 'A05:2021 - Security Misconfiguration',
            'B502': 'A05:2021 - Security Misconfiguration',
            'B503': 'A05:2021 - Security Misconfiguration',
            'B504': 'A05:2021 - Security Misconfiguration',
            'B505': 'A02:2021 - Cryptographic Failures',
            'B506': 'A05:2021 - Security Misconfiguration',
            'B507': 'A03:2021 - Injection',
            'B601': 'A03:2021 - Injection',
            'B602': 'A03:2021 - Injection',
            'B603': 'A03:2021 - Injection',
            'B604': 'A03:2021 - Injection',
            'B605': 'A05:2021 - Security Misconfiguration',
            'B606': 'A05:2021 - Security Misconfiguration',
            'B607': 'A05:2021 - Security Misconfiguration',
            'B608': 'A03:2021 - Injection',
            'B609': 'A03:2021 - Injection',
            'B610': 'A03:2021 - Injection',
            'B611': 'A03:2021 - Injection',
            'B701': 'A07:2021 - Identification and Authentication Failures',
            'B702': 'A05:2021 - Security Misconfiguration'
        }
        
        return owasp_mapping.get(test_id, 'A05:2021 - Security Misconfiguration')
    
    async def _cleanup(self, repo_path: Optional[str]):
        """Clean up temporary files"""
        try:
            if repo_path and os.path.exists(repo_path):
                shutil.rmtree(repo_path)
                logger.info(f"🧹 Cleaned up temporary directory: {repo_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {repo_path}: {e}")
