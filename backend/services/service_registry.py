"""
ONYX Service Registry
=====================

Centralized service initialization and management.
All services are initialized once and shared across the application.

Usage:
    from services.service_registry import ServiceRegistry
    
    # Initialize all services (call once at startup)
    await ServiceRegistry.initialize()
    
    # Get a service
    threat_intel = ServiceRegistry.get_threat_intelligence()
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """
    Centralized service registry for ONYX platform.
    Implements singleton pattern for all security services.
    """
    
    _initialized: bool = False
    _services: Dict[str, Any] = {}
    
    # Service instances
    _threat_intel_engine = None
    _vuln_manager = None
    _metrics_engine = None
    _pentest_engine = None
    _rule_parser = None
    _rule_tester = None
    _baseline_manager = None
    _policy_engine = None
    _security_scanner = None
    _scan_orchestrator = None
    
    @classmethod
    def initialize(cls) -> Dict[str, bool]:
        """
        Initialize all services. Safe to call multiple times.
        Returns dict of service initialization status.
        """
        if cls._initialized:
            logger.info("🔄 Services already initialized, skipping...")
            return cls.get_status()
        
        logger.info("🚀 Initializing ONYX Service Registry...")
        status = {}
        
        # Initialize Threat Intelligence Engine
        try:
            from services.security.threat_intelligence import ThreatIntelligenceEngine
            cls._threat_intel_engine = ThreatIntelligenceEngine()
            status["threat_intelligence"] = True
            logger.info("✅ Threat Intelligence Engine initialized")
        except Exception as e:
            logger.warning(f"⚠️ Threat Intelligence Engine failed: {e}")
            status["threat_intelligence"] = False
        
        # Initialize Vulnerability Manager
        try:
            from services.scanning.vulnerability import VulnerabilityManager
            cls._vuln_manager = VulnerabilityManager()
            status["vulnerability_manager"] = True
            logger.info("✅ Vulnerability Manager initialized")
        except Exception as e:
            logger.warning(f"⚠️ Vulnerability Manager failed: {e}")
            status["vulnerability_manager"] = False
        
        # Initialize Security Metrics Engine
        try:
            from services.security.security_metrics import SecurityMetricsEngine
            cls._metrics_engine = SecurityMetricsEngine()
            status["security_metrics"] = True
            logger.info("✅ Security Metrics Engine initialized")
        except Exception as e:
            logger.warning(f"⚠️ Security Metrics Engine failed: {e}")
            status["security_metrics"] = False
        
        # Initialize Penetration Testing Engine
        try:
            from services.scanning.pentest import PenetrationTestingEngine
            cls._pentest_engine = PenetrationTestingEngine()
            status["penetration_testing"] = True
            logger.info("✅ Penetration Testing Engine initialized")
        except Exception as e:
            logger.warning(f"⚠️ Penetration Testing Engine failed: {e}")
            status["penetration_testing"] = False
        
        # Initialize Rule Parsing Engine
        try:
            from services.rules.rule_parsing_engine import RuleParsingEngine
            cls._rule_parser = RuleParsingEngine()
            status["rule_parser"] = True
            logger.info("✅ Rule Parsing Engine initialized")
        except Exception as e:
            logger.warning(f"⚠️ Rule Parsing Engine failed: {e}")
            status["rule_parser"] = False
        
        # Initialize Rule Testing Framework
        try:
            from services.rules.rule_testing_framework import RuleTestingFramework
            cls._rule_tester = RuleTestingFramework()
            status["rule_tester"] = True
            logger.info("✅ Rule Testing Framework initialized")
        except Exception as e:
            logger.warning(f"⚠️ Rule Testing Framework failed: {e}")
            status["rule_tester"] = False
        
        # Initialize Baseline Manager
        try:
            from services.scanning.baseline import BaselineManager
            cls._baseline_manager = BaselineManager()
            status["baseline_manager"] = True
            logger.info("✅ Baseline Manager initialized")
        except Exception as e:
            logger.warning(f"⚠️ Baseline Manager failed: {e}")
            status["baseline_manager"] = False
        
        # Initialize Policy Engine
        try:
            from services.rules.policy_as_code_engine import PolicyAsCodeEngine
            cls._policy_engine = PolicyAsCodeEngine()
            status["policy_engine"] = True
            logger.info("✅ Policy Engine initialized")
        except Exception as e:
            logger.warning(f"⚠️ Policy Engine failed: {e}")
            status["policy_engine"] = False
        
        # Initialize Security Scanner
        try:
            from services.scanning.scanners import RealSecurityScanner
            cls._security_scanner = RealSecurityScanner()
            status["security_scanner"] = True
            logger.info("✅ Security Scanner initialized")
        except Exception as e:
            logger.warning(f"⚠️ Security Scanner failed: {e}")
            status["security_scanner"] = False
        
        # Initialize Scan Orchestrator
        try:
            from services.scanning.base import ScanConfig
            from services.scanning.engine import ScanOrchestrator
            config = ScanConfig(
                max_concurrent_scans=3,
                scan_timeout=1800,
                dast_target_allowlist=["localhost", "127.0.0.1"],
                dast_rate_limit=2.0,
                sast_languages=["python", "javascript", "java", "go", "csharp", "cpp"],
                iac_frameworks=["terraform", "cloudformation", "kubernetes", "docker"],
                suppression_file=".security-suppressions.yaml",
                allow_inline_suppressions=True
            )
            cls._scan_orchestrator = ScanOrchestrator(config)
            status["scan_orchestrator"] = True
            logger.info("✅ Scan Orchestrator initialized")
        except Exception as e:
            logger.warning(f"⚠️ Scan Orchestrator failed: {e}")
            status["scan_orchestrator"] = False
        
        cls._initialized = True
        cls._services = status
        
        successful = sum(1 for v in status.values() if v)
        total = len(status)
        logger.info(f"🎯 Service Registry initialized: {successful}/{total} services active")
        
        return status
    
    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Get status of all services"""
        return {
            "initialized": cls._initialized,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "threat_intelligence": cls._threat_intel_engine is not None,
                "vulnerability_manager": cls._vuln_manager is not None,
                "security_metrics": cls._metrics_engine is not None,
                "penetration_testing": cls._pentest_engine is not None,
                "rule_parser": cls._rule_parser is not None,
                "rule_tester": cls._rule_tester is not None,
                "baseline_manager": cls._baseline_manager is not None,
                "policy_engine": cls._policy_engine is not None,
                "security_scanner": cls._security_scanner is not None,
                "scan_orchestrator": cls._scan_orchestrator is not None,
            },
            "active_count": sum([
                cls._threat_intel_engine is not None,
                cls._vuln_manager is not None,
                cls._metrics_engine is not None,
                cls._pentest_engine is not None,
                cls._rule_parser is not None,
                cls._rule_tester is not None,
                cls._baseline_manager is not None,
                cls._policy_engine is not None,
                cls._security_scanner is not None,
                cls._scan_orchestrator is not None,
            ]),
            "total_services": 10
        }
    
    # Service getters
    @classmethod
    def get_threat_intelligence(cls):
        """Get Threat Intelligence Engine instance"""
        return cls._threat_intel_engine
    
    @classmethod
    def get_vulnerability_manager(cls):
        """Get Vulnerability Manager instance"""
        return cls._vuln_manager
    
    @classmethod
    def get_security_metrics(cls):
        """Get Security Metrics Engine instance"""
        return cls._metrics_engine
    
    @classmethod
    def get_penetration_testing(cls):
        """Get Penetration Testing Engine instance"""
        return cls._pentest_engine
    
    @classmethod
    def get_rule_parser(cls):
        """Get Rule Parsing Engine instance"""
        return cls._rule_parser
    
    @classmethod
    def get_rule_tester(cls):
        """Get Rule Testing Framework instance"""
        return cls._rule_tester
    
    @classmethod
    def get_baseline_manager(cls):
        """Get Baseline Manager instance"""
        return cls._baseline_manager
    
    @classmethod
    def get_policy_engine(cls):
        """Get Policy Engine instance"""
        return cls._policy_engine
    
    @classmethod
    def get_security_scanner(cls):
        """Get Security Scanner instance"""
        return cls._security_scanner
    
    @classmethod
    def get_scan_orchestrator(cls):
        """Get Scan Orchestrator instance"""
        return cls._scan_orchestrator
    
    @classmethod
    async def shutdown(cls):
        """Gracefully shutdown all services"""
        logger.info("🛑 Shutting down Service Registry...")
        
        # Stop threat intelligence engine if it has a stop method
        if cls._threat_intel_engine and hasattr(cls._threat_intel_engine, 'stop'):
            try:
                await cls._threat_intel_engine.stop()
                logger.info("✅ Threat Intelligence Engine stopped")
            except Exception as e:
                logger.warning(f"⚠️ Error stopping Threat Intelligence Engine: {e}")
        
        cls._initialized = False
        logger.info("🛑 Service Registry shutdown complete")


# Convenience functions for backward compatibility
def get_service_status() -> Dict[str, Any]:
    """Get status of all services"""
    return ServiceRegistry.get_status()


def init_all_services() -> Dict[str, bool]:
    """Initialize all services"""
    return ServiceRegistry.initialize()
