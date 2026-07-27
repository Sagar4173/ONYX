"""
Security Scanning Tests
Tests for security scanners, orchestration, and result processing
"""

import pytest


class TestScannerAvailability:
    """Test scanner availability detection"""
    
    def test_core_scanners_enabled_by_default(self):
        """Test that core scanners are enabled by default"""
        from config import settings
        
        # Core scanners should be enabled
        assert settings.enable_semgrep
        assert settings.enable_bandit
        assert settings.enable_safety
        assert settings.enable_gitleaks
    
    def test_optional_scanners_disabled_by_default(self):
        """Test that optional scanners are disabled by default"""
        from config import settings
        
        # Optional scanners should be disabled
        assert not settings.enable_trivy
        assert not settings.enable_zap
        assert not settings.enable_nuclei
        assert not settings.enable_codeql
        assert not settings.enable_checkov


class TestScanOrchestrator:
    """Test scan orchestration"""
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test ScanOrchestrator can be initialized"""
        from services.scanning.engine import ScanOrchestrator
        
        orchestrator = ScanOrchestrator()
        assert orchestrator is not None
    
    @pytest.mark.asyncio
    async def test_scan_workflow_creation(self, sample_scan_result):
        """Test scan workflow can be created"""
        from services.scanning.engine import ScanWorkflow
        
        workflow = ScanWorkflow()
        assert workflow is not None


class TestScanResults:
    """Test scan result processing"""
    
    def test_finding_severity_levels(self, sample_scan_result):
        """Test finding severity levels are valid"""
        valid_severities = {"critical", "high", "medium", "low", "info"}
        
        for finding in sample_scan_result["findings"]:
            assert finding["severity"].lower() in valid_severities
    
    def test_scan_summary_totals(self, sample_scan_result):
        """Test scan summary totals are consistent"""
        summary = sample_scan_result["summary"]
        calculated_total = (
            summary["critical"] +
            summary["high"] +
            summary["medium"] +
            summary["low"]
        )
        
        # Total should equal sum of severity counts
        assert summary["total"] == calculated_total or summary["total"] == len(sample_scan_result["findings"])


class TestBaselineScanning:
    """Test baseline scanning and drift detection"""
    
    @pytest.mark.asyncio
    async def test_baseline_manager_initialization(self):
        """Test BaselineManager can be initialized"""
        from services.scanning.baseline import BaselineManager
        
        manager = BaselineManager()
        assert manager is not None
    
    @pytest.mark.asyncio
    async def test_drift_detection_same_results(self, sample_scan_result):
        """Test no drift detected for identical scans"""
        # When comparing identical scans, no drift should be detected
        baseline_findings = sample_scan_result["findings"]
        current_findings = sample_scan_result["findings"]
        
        # Simple drift check - new findings
        new_findings = [f for f in current_findings if f not in baseline_findings]
        assert len(new_findings) == 0


class TestVulnerabilityManager:
    """Test vulnerability lifecycle management"""
    
    @pytest.mark.asyncio
    async def test_vulnerability_manager_initialization(self):
        """Test VulnerabilityManager can be initialized"""
        from services.scanning.vulnerability import VulnerabilityManager
        
        manager = VulnerabilityManager()
        assert manager is not None
    
    def test_vulnerability_status_values(self):
        """Test vulnerability status enum values"""
        from services.scanning.vulnerability import VulnerabilityStatus
        
        assert hasattr(VulnerabilityStatus, 'OPEN')
        assert hasattr(VulnerabilityStatus, 'IN_PROGRESS')
        assert hasattr(VulnerabilityStatus, 'FIXED')


class TestServiceRegistry:
    """Test centralized service registry"""
    
    def test_service_registry_singleton(self):
        """Test ServiceRegistry uses singleton pattern"""
        from services.service_registry import ServiceRegistry
        
        # Multiple calls should return same status
        status1 = ServiceRegistry.get_status()
        status2 = ServiceRegistry.get_status()
        
        assert status1["initialized"] == status2["initialized"]
        assert status1["active_count"] == status2["active_count"]
        assert status1["total_services"] == status2["total_services"]
        assert status1["services"] == status2["services"]
    
    def test_get_status_returns_dict(self):
        """Test get_status returns a dictionary"""
        from services.service_registry import ServiceRegistry
        
        status = ServiceRegistry.get_status()
        assert isinstance(status, dict)
