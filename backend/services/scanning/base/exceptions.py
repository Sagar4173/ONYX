"""
Custom Exceptions for Security Scanning
========================================

Defines exception hierarchy for scanner operations.
"""


class ScannerError(Exception):
    """Base exception for all scanner-related errors."""
    
    def __init__(self, message: str, scanner_name: str = None, details: dict = None):
        self.message = message
        self.scanner_name = scanner_name
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.scanner_name:
            return f"[{self.scanner_name}] {self.message}"
        return self.message


class ScanTimeoutError(ScannerError):
    """Raised when a scan operation times out."""
    
    def __init__(self, scanner_name: str, timeout_seconds: int, message: str = None):
        self.timeout_seconds = timeout_seconds
        msg = message or f"Scan timed out after {timeout_seconds} seconds"
        super().__init__(msg, scanner_name, {"timeout_seconds": timeout_seconds})


class ScanConfigurationError(ScannerError):
    """Raised when scanner configuration is invalid."""
    
    def __init__(self, scanner_name: str, config_issue: str):
        self.config_issue = config_issue
        super().__init__(
            f"Configuration error: {config_issue}",
            scanner_name,
            {"config_issue": config_issue}
        )


class TargetNotAllowedError(ScannerError):
    """Raised when a scan target is not in the allowlist."""
    
    def __init__(self, target: str, scanner_name: str = None):
        self.target = target
        super().__init__(
            f"Target '{target}' is not in the allowed list",
            scanner_name,
            {"target": target}
        )


class ScannerNotAvailableError(ScannerError):
    """Raised when a scanner binary is not available."""
    
    def __init__(self, scanner_name: str, binary_path: str):
        self.binary_path = binary_path
        super().__init__(
            f"Scanner binary not found at '{binary_path}'",
            scanner_name,
            {"binary_path": binary_path}
        )


class ScanParseError(ScannerError):
    """Raised when scanner output cannot be parsed."""
    
    def __init__(self, scanner_name: str, output_format: str, error_details: str):
        self.output_format = output_format
        self.error_details = error_details
        super().__init__(
            f"Failed to parse {output_format} output: {error_details}",
            scanner_name,
            {"output_format": output_format, "error_details": error_details}
        )


class RepositoryCloneError(ScannerError):
    """Raised when repository cloning fails."""
    
    def __init__(self, repo_url: str, error_details: str):
        self.repo_url = repo_url
        self.error_details = error_details
        super().__init__(
            f"Failed to clone repository: {error_details}",
            details={"repo_url": repo_url, "error_details": error_details}
        )
