"""
Lazy Semgrep Loader
===================
Installs and runs semgrep on-demand to save memory on free-tier hosting (512MB).
Semgrep is only loaded when a user requests a scan that requires it.
"""

import subprocess
import shutil
import logging
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Global state
_semgrep_installed = False
_semgrep_installing = False


def is_semgrep_available() -> bool:
    """Check if semgrep CLI is available"""
    return shutil.which("semgrep") is not None


async def ensure_semgrep_installed() -> bool:
    """
    Ensure semgrep is installed. Installs on first use.
    Returns True if semgrep is available, False otherwise.
    """
    global _semgrep_installed, _semgrep_installing
    
    # Already installed
    if _semgrep_installed or is_semgrep_available():
        _semgrep_installed = True
        return True
    
    # Already being installed by another request
    if _semgrep_installing:
        # Wait for installation to complete
        for _ in range(60):  # Wait up to 60 seconds
            await asyncio.sleep(1)
            if _semgrep_installed:
                return True
        return False
    
    # Install semgrep
    _semgrep_installing = True
    logger.info("📦 Installing semgrep on-demand (first-time setup)...")
    
    try:
        # Install semgrep via pip
        process = await asyncio.create_subprocess_exec(
            "pip", "install", "--no-cache-dir", "semgrep>=1.45.0",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            _semgrep_installed = True
            logger.info("✅ Semgrep installed successfully")
            return True
        else:
            logger.error(f"❌ Failed to install semgrep: {stderr.decode()}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error installing semgrep: {e}")
        return False
    finally:
        _semgrep_installing = False


async def run_semgrep_scan(
    target_path: str,
    config: str = "auto",
    output_format: str = "json"
) -> Dict[str, Any]:
    """
    Run semgrep scan on target path.
    Automatically installs semgrep if not available.
    
    Args:
        target_path: Path to scan
        config: Semgrep config (default: "auto" for auto-detection)
        output_format: Output format (json, sarif, text)
    
    Returns:
        Dict with scan results or error info
    """
    # Ensure semgrep is installed
    if not await ensure_semgrep_installed():
        return {
            "success": False,
            "error": "Semgrep installation failed. Please try again later.",
            "findings": []
        }
    
    try:
        # Build semgrep command
        cmd = [
            "semgrep",
            "--config", config,
            "--json" if output_format == "json" else f"--{output_format}",
            "--quiet",
            target_path
        ]
        
        logger.info(f"🔍 Running semgrep scan on {target_path}")
        
        # Run semgrep
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode in [0, 1]:  # 0 = no findings, 1 = findings found
            import json
            try:
                results = json.loads(stdout.decode())
                return {
                    "success": True,
                    "findings": results.get("results", []),
                    "errors": results.get("errors", [])
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "findings": [],
                    "raw_output": stdout.decode()
                }
        else:
            return {
                "success": False,
                "error": stderr.decode() or "Semgrep scan failed",
                "findings": []
            }
            
    except Exception as e:
        logger.error(f"❌ Semgrep scan error: {e}")
        return {
            "success": False,
            "error": str(e),
            "findings": []
        }


def get_semgrep_status() -> Dict[str, Any]:
    """Get semgrep availability status"""
    return {
        "installed": _semgrep_installed or is_semgrep_available(),
        "installing": _semgrep_installing,
        "available": is_semgrep_available()
    }
