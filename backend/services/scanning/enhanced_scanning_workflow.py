"""
Enhanced Scanning Workflow Service
Ensures complete scanning with AI analysis and proper error handling
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path

from models.report import ScanReport, ScanStatus, ScanResult
from services.scanning.advanced_scanner_engine import AdvancedScannerEngine, ScanConfig
from services.ai.ai_processor import get_ai_processor
from services.scanning.vulnerability_management import VulnerabilityManager
from services.notifications.notification_service import NotificationService

logger = logging.getLogger(__name__)


class EnhancedScanningWorkflow:
    """Enhanced scanning workflow with AI analysis and comprehensive reporting"""
    
    def __init__(self):
        self.scanner_engine = AdvancedScannerEngine()
        self.ai_processor = get_ai_processor()
        self.vuln_manager = VulnerabilityManager()
        self.notification_service = NotificationService()
    
    async def execute_comprehensive_scan(
        self,
        scan_report: ScanReport,
        repository_path: str,
        target_url: Optional[str] = None,
        scan_config: Optional[ScanConfig] = None
    ) -> ScanReport:
        """
        Execute a comprehensive security scan with AI analysis
        
        Args:
            scan_report: The scan report to update
            repository_path: Local path to the repository
            target_url: Optional target URL for DAST scanning
            scan_config: Optional scanner configuration
            
        Returns:
            Updated scan report with results and AI analysis
        """
        try:
            logger.info(f"Starting comprehensive scan for {scan_report.project_name}")
            
            # Update scan status
            scan_report.status = ScanStatus.RUNNING
            scan_report.started_at = datetime.now(timezone.utc)
            await scan_report.save()
            
            # Phase 1: Repository Analysis
            logger.info("Phase 1: Analyzing repository structure...")
            repo_context = await self._analyze_repository_context(repository_path)
            
            # Phase 2: Security Scanning
            logger.info("Phase 2: Running security scanners...")
            scan_results = await self._execute_security_scans(
                repository_path, 
                target_url, 
                scan_config or ScanConfig(),
                scan_report.scan_id
            )
            
            # Update scan report with scan results
            scan_report.scan_results = scan_results
            scan_report.update_summary()
            await scan_report.save()
            
            # Phase 3: AI Analysis (always run, even if no findings)
            logger.info("Phase 3: Generating AI analysis...")
            ai_analysis = await self._generate_comprehensive_ai_analysis(
                scan_results,
                repo_context,
                scan_report
            )
            scan_report.ai_analysis = ai_analysis
            
            # Phase 4: Vulnerability Management
            logger.info("Phase 4: Processing vulnerabilities...")
            await self._process_vulnerabilities(scan_report, repo_context)
            
            # Phase 5: Compliance Analysis
            logger.info("Phase 5: Analyzing compliance...")
            compliance_analysis = await self._analyze_compliance(scan_report)
            if compliance_analysis:
                scan_report.metadata["compliance_analysis"] = compliance_analysis
            
            # Phase 6: Final Report Generation
            logger.info("Phase 6: Finalizing report...")
            scan_report.status = ScanStatus.COMPLETED
            scan_report.completed_at = datetime.now(timezone.utc)
            scan_report.duration_seconds = (
                scan_report.completed_at - scan_report.started_at
            ).total_seconds()
            
            # Add enhanced metadata
            scan_report.metadata.update({
                "repository_context": repo_context,
                "scan_workflow_version": "2.0",
                "ai_analysis_generated": True,
                "compliance_analyzed": bool(compliance_analysis),
                "total_scan_phases": 6
            })
            
            await scan_report.save()
            
            # Phase 7: Notifications
            logger.info("Phase 7: Sending notifications...")
            try:
                await self.notification_service.send_scan_notification(scan_report)
            except Exception as e:
                logger.warning(f"Notification failed: {e}")
            
            logger.info(f"Comprehensive scan completed for {scan_report.project_name}")
            return scan_report
            
        except Exception as e:
            logger.error(f"Comprehensive scan failed: {e}")
            
            # Update scan report with error
            scan_report.status = ScanStatus.FAILED
            scan_report.completed_at = datetime.now(timezone.utc)
            if scan_report.started_at:
                scan_report.duration_seconds = (
                    scan_report.completed_at - scan_report.started_at
                ).total_seconds()
            
            scan_report.metadata["error"] = str(e)
            scan_report.metadata["error_phase"] = "comprehensive_scan"
            await scan_report.save()
            
            raise
    
    async def _analyze_repository_context(self, repository_path: str) -> Dict[str, Any]:
        """Analyze repository context for enhanced AI analysis"""
        try:
            repo_path = Path(repository_path)
            
            context = {
                "languages": [],
                "frameworks": [],
                "package_managers": [],
                "ci_cd_files": [],
                "config_files": [],
                "size_metrics": {
                    "total_files": 0,
                    "code_files": 0,
                    "total_lines": 0
                },
                "security_files": []
            }
            
            # Detect languages and frameworks
            language_patterns = {
                "python": ["*.py", "requirements.txt", "Pipfile", "pyproject.toml"],
                "javascript": ["*.js", "*.ts", "package.json", "yarn.lock"],
                "java": ["*.java", "pom.xml", "build.gradle"],
                "go": ["*.go", "go.mod", "go.sum"],
                "rust": ["*.rs", "Cargo.toml"],
                "php": ["*.php", "composer.json"],
                "ruby": ["*.rb", "Gemfile"],
                "csharp": ["*.cs", "*.csproj", "*.sln"]
            }
            
            for language, patterns in language_patterns.items():
                for pattern in patterns:
                    if list(repo_path.rglob(pattern)):
                        context["languages"].append(language)
                        break
            
            # Detect CI/CD files
            ci_patterns = [
                ".github/workflows/*.yml",
                ".github/workflows/*.yaml",
                ".gitlab-ci.yml",
                "Jenkinsfile",
                ".travis.yml",
                "azure-pipelines.yml"
            ]
            
            for pattern in ci_patterns:
                if list(repo_path.rglob(pattern)):
                    context["ci_cd_files"].append(pattern)
            
            # Detect security-related files
            security_patterns = [
                ".security.yml",
                "security.yaml",
                ".snyk",
                "dependabot.yml",
                "SECURITY.md"
            ]
            
            for pattern in security_patterns:
                if list(repo_path.rglob(pattern)):
                    context["security_files"].append(pattern)
            
            # Count files and lines
            code_extensions = {'.py', '.js', '.ts', '.java', '.go', '.rs', '.php', '.rb', '.cs', '.cpp', '.c', '.h'}
            
            for file_path in repo_path.rglob("*"):
                if file_path.is_file() and not any(part.startswith('.') for part in file_path.parts[len(repo_path.parts):]):
                    context["size_metrics"]["total_files"] += 1
                    
                    if file_path.suffix in code_extensions:
                        context["size_metrics"]["code_files"] += 1
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                context["size_metrics"]["total_lines"] += sum(1 for _ in f)
                        except Exception:
                            pass
            
            return context
            
        except Exception as e:
            logger.warning(f"Repository context analysis failed: {e}")
            return {"error": str(e)}
    
    async def _execute_security_scans(
        self,
        repository_path: str,
        target_url: Optional[str],
        scan_config: ScanConfig,
        scan_id: str
    ) -> List[ScanResult]:
        """Execute security scans with enhanced error handling"""
        try:
            # Run comprehensive scan using advanced scanner engine
            scan_results_dict = await self.scanner_engine.scan_repository(
                repository_path,
                target_url
            )
            
            # Convert to ScanResult objects
            scan_results = []
            
            for scanner_name, scanner_data in scan_results_dict.get("scanners", {}).items():
                scan_result = ScanResult(
                    scanner=scanner_name,
                    status=ScanStatus.COMPLETED if scanner_data.get("status") == "completed" else ScanStatus.FAILED,
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                    duration_seconds=scanner_data.get("duration", 0),
                    findings=scanner_data.get("findings", []),
                    summary=f"Scanner {scanner_name} found {scanner_data.get('findings_count', 0)} findings",
                    error_message=scanner_data.get("error")
                )
                scan_results.append(scan_result)
            
            return scan_results
            
        except Exception as e:
            logger.error(f"Security scans failed: {e}")
            # Return a failed scan result
            return [ScanResult(
                scanner="comprehensive",
                status=ScanStatus.FAILED,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                duration_seconds=0,
                findings=[],
                summary="Security scanning failed",
                error_message=str(e)
            )]
    
    async def _generate_comprehensive_ai_analysis(
        self,
        scan_results: List[ScanResult],
        repo_context: Dict[str, Any],
        scan_report: ScanReport
    ):
        """Generate comprehensive AI analysis with enhanced context"""
        try:
            # Prepare enhanced project context
            project_context = {
                "project_name": scan_report.project_name,
                "repository_url": scan_report.git_metadata.repository_url if scan_report.git_metadata else None,
                "languages": repo_context.get("languages", []),
                "frameworks": repo_context.get("frameworks", []),
                "size_metrics": repo_context.get("size_metrics", {}),
                "ci_cd_present": bool(repo_context.get("ci_cd_files", [])),
                "security_files_present": bool(repo_context.get("security_files", []))
            }
            
            # Generate AI analysis with enhanced context
            ai_analysis = await self.ai_processor.analyze_scan_results(
                scan_results,
                project_context
            )
            
            # Add additional AI-powered insights
            ai_analysis.metadata = {
                "analysis_version": "2.0",
                "context_enhanced": True,
                "repository_insights": await self._generate_repository_insights(repo_context),
                "security_maturity_score": await self._calculate_security_maturity(scan_results, repo_context)
            }
            
            return ai_analysis
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            # Return minimal AI analysis on failure
            from models.report import AIAnalysis
            return AIAnalysis(
                model_used="fallback",
                executive_summary=f"AI analysis failed: {str(e)}. Basic scan completed with {sum(len(sr.findings) for sr in scan_results)} findings.",
                risk_assessment="Unable to generate AI risk assessment due to analysis failure.",
                priority_findings=[],
                recommendations=["Manual review required due to AI analysis failure."],
                secure_code_examples={},
                compliance_impact={"general": "Unable to assess compliance impact"},
                estimated_fix_time="Manual estimation required"
            )
    
    async def _process_vulnerabilities(self, scan_report: ScanReport, repo_context: Dict[str, Any]):
        """Process vulnerabilities through the vulnerability management system"""
        try:
            # Extract all findings from scan results
            all_findings = []
            for scan_result in scan_report.scan_results:
                all_findings.extend(scan_result.findings)
            
            if all_findings:
                # Process through vulnerability manager
                await self.vuln_manager.process_scan_findings(
                    scan_report.scan_id,
                    all_findings,
                    repo_context
                )
                
        except Exception as e:
            logger.warning(f"Vulnerability processing failed: {e}")
    
    async def _analyze_compliance(self, scan_report: ScanReport) -> Optional[Dict[str, Any]]:
        """Analyze compliance against security frameworks"""
        try:
            from services.compliance.compliance_analyzer import ComplianceAnalysisService
            compliance_service = ComplianceAnalysisService()
            
            # Extract findings for compliance analysis
            all_findings = []
            for scan_result in scan_report.scan_results:
                all_findings.extend(scan_result.findings)
            
            if not all_findings:
                return {"status": "clean", "frameworks_analyzed": []}
            
            # Analyze against multiple frameworks
            frameworks = ["OWASP", "NIST", "ISO27001"]
            compliance_results = {}
            
            for framework in frameworks:
                try:
                    framework_analysis = await compliance_service.analyze_framework_compliance(
                        all_findings,
                        framework
                    )
                    compliance_results[framework] = framework_analysis
                except Exception as e:
                    logger.warning(f"Compliance analysis failed for {framework}: {e}")
                    compliance_results[framework] = {"error": str(e)}
            
            return {
                "frameworks_analyzed": frameworks,
                "results": compliance_results,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.warning(f"Compliance analysis failed: {e}")
            return None
    
    async def _generate_repository_insights(self, repo_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate additional repository insights"""
        insights = {
            "complexity_score": "medium",
            "security_tooling_present": bool(repo_context.get("security_files", [])),
            "ci_cd_integration": bool(repo_context.get("ci_cd_files", [])),
            "multi_language": len(repo_context.get("languages", [])) > 1,
            "estimated_risk_level": "medium"
        }
        
        # Calculate complexity based on size metrics
        size_metrics = repo_context.get("size_metrics", {})
        total_lines = size_metrics.get("total_lines", 0)
        
        if total_lines > 100000:
            insights["complexity_score"] = "high"
        elif total_lines < 1000:
            insights["complexity_score"] = "low"
        
        return insights
    
    async def _calculate_security_maturity(self, scan_results: List[ScanResult], repo_context: Dict[str, Any]) -> float:
        """Calculate security maturity score (0-10)"""
        score = 5.0  # Base score
        
        # Adjust based on findings
        total_findings = sum(len(sr.findings) for sr in scan_results)
        critical_findings = sum(
            len([f for f in sr.findings if f.severity == "critical"]) 
            for sr in scan_results
        )
        
        # Penalize for findings
        score -= min(critical_findings * 0.5, 3.0)
        score -= min((total_findings - critical_findings) * 0.1, 2.0)
        
        # Bonus for security tooling
        if repo_context.get("security_files"):
            score += 1.0
        
        # Bonus for CI/CD
        if repo_context.get("ci_cd_files"):
            score += 0.5
        
        return max(0.0, min(10.0, score))


# Global instance
enhanced_workflow = EnhancedScanningWorkflow()
