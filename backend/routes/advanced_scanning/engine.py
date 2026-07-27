from urllib.parse import urlparse

from services.scanning.base import ScanConfig
from services.scanning.engine import ScanOrchestrator

scanner_orchestrator = None


def get_scanner_engine():
    global scanner_orchestrator
    if scanner_orchestrator is None:
        config = ScanConfig(
            max_concurrent_scans=3,
            scan_timeout=1800,
            dast_target_allowlist=get_allowed_targets(),
            dast_rate_limit=2.0,
            sast_languages=["python", "javascript", "java", "go", "csharp", "cpp"],
            iac_frameworks=["terraform", "cloudformation", "kubernetes", "docker"],
            suppression_file=".security-suppressions.yaml",
            allow_inline_suppressions=True
        )
        scanner_orchestrator = ScanOrchestrator(config)
    return scanner_orchestrator


def get_allowed_targets():
    return [
        "localhost",
        "127.0.0.1",
        "example.com",
        "staging.example.com",
        "test.example.com"
    ]


def is_target_allowed(target_url: str) -> bool:
    try:
        parsed_url = urlparse(target_url)
        target_host = parsed_url.netloc.lower()
        for allowed in get_allowed_targets():
            if target_host == allowed.lower() or target_host.endswith(f".{allowed.lower()}"):
                return True
        return False
    except Exception:
        return False


def update_scanner_config(config: ScanConfig, updates: dict):
    for key, value in updates.items():
        if hasattr(config, key):
            setattr(config, key, value)


def generate_findings_summary(findings: list) -> dict:
    active_findings = [f for f in findings if not getattr(f, 'suppressed', False)]

    summary = {
        'total_findings': len(findings),
        'active_findings': len(active_findings),
        'suppressed_findings': len(findings) - len(active_findings),
        'by_severity': {},
        'by_scanner': {},
        'by_scan_type': {},
    }

    for severity in ['critical', 'high', 'medium', 'low', 'info']:
        count = len([f for f in active_findings if getattr(f, 'severity', '') == severity])
        summary['by_severity'][severity] = count

    scanners = set(getattr(f, 'source', '') for f in active_findings)
    for scanner in scanners:
        count = len([f for f in active_findings if getattr(f, 'source', '') == scanner])
        summary['by_scanner'][scanner] = count

    scan_types = set(getattr(f, 'scan_type', '') for f in active_findings)
    for scan_type in scan_types:
        count = len([f for f in active_findings if getattr(f, 'scan_type', '') == scan_type])
        summary['by_scan_type'][scan_type] = count

    return summary
