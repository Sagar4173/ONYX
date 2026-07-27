import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Scanners"])


async def _check_scanner_availability(scanner_name: str, command: List[str]) -> Dict[str, Any]:
    """Check if a scanner is available and get its version."""
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5.0)

        if process.returncode == 0:
            version = stdout.decode().strip().split('\n')[0] if stdout else "unknown"
            version_match = re.search(r'[\d]+\.[\d]+\.[\d]+', version)
            version = version_match.group(0) if version_match else version[:50]
            return {"status": "available", "version": version}
        else:
            return {"status": "unavailable", "version": "N/A", "error": "Command failed"}
    except asyncio.TimeoutError:
        return {"status": "unavailable", "version": "N/A", "error": "Timeout"}
    except FileNotFoundError:
        return {"status": "not_installed", "version": "N/A", "error": "Scanner not found in PATH"}
    except Exception as e:
        return {"status": "error", "version": "N/A", "error": str(e)}


@router.get("/scanners/health")
async def get_scanners_health():
    """Get actual scanner health status by checking each scanner's availability."""
    scanner_checks = {
        "semgrep": ["semgrep", "--version"],
        "trivy": ["trivy", "--version"],
        "gitleaks": ["gitleaks", "version"],
        "bandit": ["bandit", "--version"],
        "safety": ["safety", "--version"],
    }

    results = {}
    tasks = []
    scanner_names = []

    for name, command in scanner_checks.items():
        tasks.append(_check_scanner_availability(name, command))
        scanner_names.append(name)

    check_results = await asyncio.gather(*tasks, return_exceptions=True)

    available_count = 0
    for name, result in zip(scanner_names, check_results):
        if isinstance(result, Exception):
            results[name] = {"status": "error", "version": "N/A", "error": str(result)}
        else:
            results[name] = result
            if result.get("status") == "available":
                available_count += 1

    total_scanners = len(scanner_checks)
    if available_count == total_scanners:
        overall_status = "healthy"
    elif available_count >= total_scanners // 2:
        overall_status = "degraded"
    elif available_count > 0:
        overall_status = "limited"
    else:
        overall_status = "unavailable"

    return {
        "scanners": results,
        "overall_status": overall_status,
        "available_count": available_count,
        "total_count": total_scanners,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
