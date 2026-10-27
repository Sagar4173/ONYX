"""Clone-path safety tests for the real scanner."""
from pathlib import Path
from unittest.mock import patch

import pytest

from services.scanning.scanners.real_scanner import RealSecurityScanner


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/owner/repo.git",
        "https://github.com/owner/",
        "https://github.com/owner/..\\..\\evil",
    ],
)
async def test_clone_path_stays_inside_temp_dir(tmp_path, url):
    scanner = RealSecurityScanner(temp_dir=str(tmp_path))

    with patch("services.scanning.scanners.real_scanner.Repo.clone_from"):
        clone_path = await scanner._clone_repository(url, "main")

    assert Path(clone_path).parent == tmp_path
    assert Path(clone_path).resolve() != tmp_path.resolve()
    assert Path(clone_path).is_dir()


async def test_failed_clone_removes_temp_dir(tmp_path):
    scanner = RealSecurityScanner(temp_dir=str(tmp_path))

    with patch(
        "services.scanning.scanners.real_scanner.Repo.clone_from",
        side_effect=RuntimeError("clone failed"),
    ):
        with pytest.raises(RuntimeError):
            await scanner._clone_repository("https://github.com/owner/repo.git", "main")

    assert list(tmp_path.iterdir()) == []
