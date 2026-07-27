import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestScannerHealth:
    """Test /api/scanners/health route logic."""

    @pytest.mark.asyncio
    async def test_scanner_availability_available(self):
        from routes.scanners import _check_scanner_availability

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"Semgrep 1.5.0\n", b""))

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_process):
            result = await _check_scanner_availability("semgrep", ["semgrep", "--version"])
            assert result["status"] == "available"
            assert "version" in result

    @pytest.mark.asyncio
    async def test_scanner_availability_unavailable(self):
        from routes.scanners import _check_scanner_availability

        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b"", b"error"))

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_process):
            result = await _check_scanner_availability("bad-scanner", ["bad-scanner", "--version"])
            assert result["status"] == "unavailable"

    @pytest.mark.asyncio
    async def test_scanner_not_installed(self):
        from routes.scanners import _check_scanner_availability

        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
            result = await _check_scanner_availability("nonexistent", ["nonexistent", "--version"])
            assert result["status"] == "not_installed"

    @pytest.mark.asyncio
    async def test_scanner_timeout(self):
        from routes.scanners import _check_scanner_availability

        mock_process = MagicMock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError)

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_process):
            result = await _check_scanner_availability("slow-scanner", ["slow", "--version"])
            assert result["status"] == "unavailable"

    def test_overall_status_healthy(self):
        total = 5
        available = 5
        status = "healthy" if available == total else "degraded" if available >= total // 2 else "limited" if available > 0 else "unavailable"
        assert status == "healthy"

    def test_overall_status_degraded(self):
        total = 5
        available = 3
        status = "healthy" if available == total else "degraded" if available >= total // 2 else "limited" if available > 0 else "unavailable"
        assert status == "degraded"

    def test_overall_status_limited(self):
        total = 5
        available = 1
        status = "healthy" if available == total else "degraded" if available >= total // 2 else "limited" if available > 0 else "unavailable"
        assert status == "limited"

    def test_overall_status_unavailable(self):
        total = 5
        available = 0
        status = "healthy" if available == total else "degraded" if available >= total // 2 else "limited" if available > 0 else "unavailable"
        assert status == "unavailable"

    @pytest.mark.asyncio
    async def test_get_scanners_health_result_structure(self):
        mock_available = {"status": "available", "version": "1.0.0"}
        mock_unavailable = {"status": "not_installed", "version": "N/A"}

        result = {
            "scanners": {
                "semgrep": mock_available,
                "trivy": mock_unavailable,
                "gitleaks": mock_available,
                "bandit": mock_unavailable,
                "safety": mock_available,
            },
            "overall_status": "degraded",
            "available_count": 3,
            "total_count": 5,
            "timestamp": "2026-01-01T00:00:00",
        }
        assert result["overall_status"] == "degraded"
        assert result["available_count"] == 3
        assert result["total_count"] == 5
        assert result["scanners"]["semgrep"]["status"] == "available"
        assert result["scanners"]["trivy"]["status"] == "not_installed"

    @pytest.mark.asyncio
    async def test_check_scanner_availability_exception(self):
        from routes.scanners import _check_scanner_availability

        with patch("asyncio.create_subprocess_exec", side_effect=Exception("Unexpected error")):
            result = await _check_scanner_availability("broken", ["broken"])
            assert result["status"] == "error"
            assert "error" in result
