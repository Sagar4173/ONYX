"""
Dependency Governance Scanner
=============================

Scans project dependencies against governance policies including:
- Blocklist of known malicious/deprecated packages
- Disallowed license patterns
- Vulnerable version ranges
"""

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..base.config import ScanConfig
from ..base.models import Finding, ScanType, Severity
from .base_scanner import BaseScanner

logger = logging.getLogger(__name__)


KNOWN_MALICIOUS_OR_DEPRECATED = {
    "event-stream": {
        "type": "malicious",
        "description": "Compromised package that injected malicious code targeting cryptocurrency wallets",
        "advisory": "CVE-2018-16487",
    },
    "colors.js": {
        "type": "malicious",
        "description": "Package was deliberately broken by the author to cause infinite loops and corrupt output",
        "advisory": "https://github.com/Marak/colors.js/issues/285",
    },
    "faker.js": {
        "type": "malicious",
        "description": "Package was deliberately broken by the author, deleting all source code",
        "advisory": "https://github.com/Marak/Faker.js/issues/1046",
    },
    "node-ipc": {
        "type": "malicious",
        "description": "Package contained destructive malware that deleted files in protest of geopolitical events",
        "advisory": "CVE-2022-23812",
    },
    "coa": {
        "type": "malicious",
        "description": "Package was compromised with malicious code before being deprecated",
        "advisory": "CVE-2021-44906",
    },
    "rc": {
        "type": "malicious",
        "description": "Package was compromised via dependency confusion with malicious code added",
        "advisory": "CVE-2022-21225",
    },
    "ua-parser-js": {
        "type": "malicious",
        "description": "Package was compromised with malicious code that installed trojans and cryptominers",
        "advisory": "CVE-2022-25927",
    },
    "flatmap-stream": {
        "type": "malicious",
        "description": "Malicious package injected into event-stream dependency chain targeting cryptocurrency wallets",
        "advisory": "CVE-2018-16487",
    },
    "left-pad": {
        "type": "deprecated",
        "description": "Package was removed from npm registry causing widespread build failures",
        "advisory": "https://blog.npmjs.org/post/141577284765/kik-left-pad-and-npm",
    },
    "lodash": {
        "type": "vulnerable",
        "description": "Contains multiple prototype pollution vulnerabilities in older versions; use lodash@4.17.21+",
        "advisory": "CVE-2021-23337",
    },
    "minimist": {
        "type": "vulnerable",
        "description": "Contains prototype pollution vulnerability in versions below 1.2.6",
        "advisory": "CVE-2021-44906",
    },
    "node-fetch": {
        "type": "vulnerable",
        "description": "Contains URL request smuggling vulnerability in versions below 2.6.7 and 3.1.1",
        "advisory": "CVE-2022-0235",
    },
    "axios": {
        "type": "vulnerable",
        "description": "Contains server-side request forgery vulnerability in versions below 0.21.2",
        "advisory": "CVE-2021-3749",
    },
    "djongo": {
        "type": "malicious",
        "description": "Package with known SQL injection vulnerabilities; no longer maintained",
        "advisory": "CVE-2022-3730",
    },
    "moment": {
        "type": "deprecated",
        "description": "Legacy date library; no longer actively maintained with security fixes",
        "advisory": "https://momentjs.com/docs/",
    },
    "gulp": {
        "type": "deprecated",
        "description": "Legacy build system; no longer actively maintained",
        "advisory": "https://github.com/gulpjs/gulp",
    },
    "bower": {
        "type": "deprecated",
        "description": "Package manager that has been officially deprecated",
        "advisory": "https://bower.io/",
    },
    "jquery": {
        "type": "vulnerable",
        "description": "Older versions contain multiple XSS vulnerabilities; use jquery@3.5.0+",
        "advisory": "CVE-2020-11023",
    },
    "debug": {
        "type": "vulnerable",
        "description": "Contains regular expression denial of service (ReDoS) vulnerability in versions below 3.1.0",
        "advisory": "CVE-2017-16137",
    },
}

DISALLOWED_LICENSES = [
    "GPL-3.0-only",
    "GPL-3.0-or-later",
    "AGPL-3.0-only",
    "AGPL-3.0-or-later",
    "CC-BY-NC-4.0",
    "BUSL-1.1",
    "SSPL-1.0",
]

VULNERABLE_VERSION_RANGES: Dict[str, List[str]] = {
    "lodash": ["<4.17.21"],
    "minimist": ["<1.2.6"],
    "node-fetch": ["<2.6.7", "<3.1.1"],
    "axios": ["<0.21.2"],
    "jquery": ["<3.5.0"],
    "debug": ["<3.1.0"],
    "ansi-html": ["<0.0.8"],
    "nth-check": ["<2.0.1"],
    "glob-parent": ["<5.1.2"],
    "json5": ["<2.2.2"],
    "ua-parser-js": ["<0.7.30", "<1.0.1"],
    "semver-regex": ["<3.1.4"],
    "tmpl": ["<1.0.5"],
    "set-value": ["<4.1.0"],
    "browserslist": ["<4.16.5"],
    "ws": ["<7.4.6", "<6.2.2"],
    "cookiejar": ["<2.1.4"],
    "path-parse": ["<1.0.7"],
    "async": ["<2.6.4", "<3.2.2"],
    "toml": ["<3.0.0"],
    "simple-git": ["<3.15.0"],
}

PACKAGE_NAME_MATCHERS: Dict[str, List[str]] = {
    "event-stream": ["event-stream", "eventstream"],
    "colors.js": ["colors.js", "colors"],
    "faker.js": ["faker.js", "faker"],
    "lodash": ["lodash"],
    "moment": ["moment"],
    "jquery": ["jquery"],
}


class DependencyGovernanceScanner(BaseScanner):
    """
    Dependency governance scanner.

    Scans project dependencies for:
    - Known malicious or deprecated packages
    - Disallowed license patterns
    - Vulnerable version ranges
    """

    SCANNER_NAME = "dependency-governance"
    SCANNER_TYPE = ScanType.SCA
    SUPPORTED_FILES = [
        "requirements.txt", "Pipfile", "pyproject.toml",
        "package.json", "package-lock.json", "yarn.lock",
    ]

    def __init__(self, config: ScanConfig = None):
        super().__init__(config)

    async def scan(self, target: str, scan_id: str, **kwargs) -> List[Finding]:
        self.log_scan_start(target, scan_id)
        start_time = asyncio.get_event_loop().time()
        findings = []
        target_path = Path(target)

        try:
            dep_files = self._find_dependency_files(target_path)
            for dep_file in dep_files:
                file_findings = await self._scan_dependency_file(dep_file, scan_id, target_path)
                findings.extend(file_findings)

        except Exception as e:
            self.log_scan_error(scan_id, e)
            raise

        duration = asyncio.get_event_loop().time() - start_time
        self.log_scan_complete(scan_id, len(findings), duration)
        return findings

    async def is_available(self) -> bool:
        return True

    async def get_version(self) -> str:
        return "1.0.0"

    def _find_dependency_files(self, target_path: Path) -> List[Path]:
        dep_files = []
        for pattern in self.SUPPORTED_FILES:
            found = list(target_path.rglob(pattern))
            dep_files.extend(found)
        return dep_files

    async def _scan_dependency_file(
        self, dep_file: Path, scan_id: str, target_path: Path,
    ) -> List[Finding]:
        findings = []
        try:
            rel_path = str(dep_file.relative_to(target_path)) if target_path else str(dep_file)
        except ValueError:
            rel_path = str(dep_file)

        try:
            content = dep_file.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.warning(f"Cannot read {dep_file}: {e}")
            return findings

        file_name = dep_file.name

        if file_name == "package.json":
            findings.extend(self._scan_package_json(content, scan_id, rel_path))
        elif file_name in ("requirements.txt", "Pipfile"):
            findings.extend(self._scan_requirements(content, scan_id, rel_path))
        elif file_name == "pyproject.toml":
            findings.extend(self._scan_pyproject_toml(content, scan_id, rel_path))
        elif file_name in ("package-lock.json", "yarn.lock"):
            findings.extend(self._scan_lockfile(content, scan_id, rel_path, file_name))

        return findings

    def _scan_package_json(self, content: str, scan_id: str, rel_path: str) -> List[Finding]:
        findings = []
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in {rel_path}")
            return findings

        dep_sections = [
            ("dependencies", "production"),
            ("devDependencies", "dev"),
            ("peerDependencies", "peer"),
            ("optionalDependencies", "optional"),
        ]

        for section, dep_type in dep_sections:
            deps = data.get(section, {})
            if not isinstance(deps, dict):
                continue
            for pkg_name, pkg_version in deps.items():
                pkg_version = str(pkg_version) if not isinstance(pkg_version, str) else pkg_version
                findings.extend(self._check_package(pkg_name, pkg_version, scan_id, rel_path, dep_type))

        licenses = data.get("license", "")
        if isinstance(licenses, str) and licenses:
            license_findings = self._check_license(licenses, scan_id, rel_path, "package.json")
            findings.extend(license_findings)

        if isinstance(licenses, list):
            for lic in licenses:
                lic_str = lic.get("type", "") if isinstance(lic, dict) else str(lic)
                license_findings = self._check_license(lic_str, scan_id, rel_path, "package.json")
                findings.extend(license_findings)

        return findings

    def _scan_requirements(self, content: str, scan_id: str, rel_path: str) -> List[Finding]:
        findings = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            if "==" in line:
                parts = line.split("==", 1)
                pkg_name = parts[0].strip().lower()
                pkg_version = parts[1].strip()
                findings.extend(self._check_package(pkg_name, pkg_version, scan_id, rel_path, "pip"))
            elif ">" in line or "<" in line:
                parts = re.split(r"[><=!~]+", line, maxsplit=1)
                pkg_name = parts[0].strip().lower() if parts else line
                findings.extend(self._check_package(pkg_name, "", scan_id, rel_path, "pip"))
            else:
                findings.extend(self._check_package(line, "", scan_id, rel_path, "pip"))
        return findings

    def _scan_pyproject_toml(self, content: str, scan_id: str, rel_path: str) -> List[Finding]:
        findings = []
        in_dependencies = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("[tool.poetry.dependencies]") or stripped.startswith("[tool.poetry.dev-dependencies]") or stripped.startswith("[project.dependencies]"):
                in_dependencies = True
                continue
            if stripped.startswith("[") and in_dependencies:
                in_dependencies = False
                continue
            if in_dependencies and "=" in stripped:
                parts = stripped.split("=", 1)
                pkg_name = parts[0].strip().strip('"').strip("'").lower()
                pkg_version = parts[1].strip().strip('"').strip("'")
                findings.extend(self._check_package(pkg_name, pkg_version, scan_id, rel_path, "poetry"))
        return findings

    def _scan_lockfile(self, content: str, scan_id: str, rel_path: str, file_name: str) -> List[Finding]:
        findings = []
        if file_name == "package-lock.json":
            try:
                data = json.loads(content)
                packages = data.get("packages", {}) or data.get("dependencies", {})
                for pkg_path, pkg_info in packages.items():
                    if isinstance(pkg_info, dict):
                        pkg_name = pkg_path.split("/")[-1] if "/" in pkg_path else pkg_path
                        pkg_name = pkg_name.replace("@", "")
                        if not pkg_name:
                            continue
                        pkg_version = pkg_info.get("version", "")
                        findings.extend(self._check_package(
                            pkg_name, str(pkg_version), scan_id, rel_path, "npm"
                        ))
            except (json.JSONDecodeError, Exception):
                pass
        return findings

    def _check_package(
        self, pkg_name: str, pkg_version: str, scan_id: str,
        rel_path: str, dep_type: str,
    ) -> List[Finding]:
        findings = []
        pkg_lower = pkg_name.lower().strip()

        matched_pkg = self._match_blocklist_package(pkg_lower)
        if matched_pkg:
            info = KNOWN_MALICIOUS_OR_DEPRECATED[matched_pkg]
            severity = self._blocklist_severity(info["type"])
            findings.append(Finding(
                id=f"dep-gov-{scan_id}-blocklist-{matched_pkg}",
                source="dependency-governance",
                rule_id=f"BLOCKLIST-{info['type'].upper()}-{matched_pkg}",
                title=f"{info['type'].title()} Package: {pkg_name}",
                description=f"{info['description']} (Type: {info['type']}, Advisory: {info['advisory']})",
                severity=severity,
                confidence="HIGH",
                location={
                    "file": rel_path,
                    "package": pkg_name,
                    "version": pkg_version,
                    "dependency_type": dep_type,
                },
                recommendation=f"Replace {pkg_name} with a maintained and secure alternative. "
                              f"See advisory: {info['advisory']}",
                scan_type=ScanType.SCA,
            ))

        vuln_ranges = VULNERABLE_VERSION_RANGES.get(pkg_lower, [])
        for vuln_range in vuln_ranges:
            if self._is_version_in_range(pkg_version, vuln_range):
                findings.append(Finding(
                    id=f"dep-gov-{scan_id}-vuln-range-{pkg_lower}",
                    source="dependency-governance",
                    rule_id=f"VULN-RANGE-{pkg_lower}",
                    title=f"Vulnerable Version: {pkg_name}@{pkg_version}",
                    description=f"The package {pkg_name}@{pkg_version} matches a known vulnerable "
                                f"version range ({vuln_range}). Update to a patched version.",
                    severity=Severity.HIGH,
                    confidence="HIGH",
                    location={
                        "file": rel_path,
                        "package": pkg_name,
                        "version": pkg_version,
                        "dependency_type": dep_type,
                    },
                    recommendation=f"Upgrade {pkg_name} to a version outside the vulnerable range {vuln_range}.",
                    scan_type=ScanType.SCA,
                ))

        return findings

    def _check_license(self, license_str: str, scan_id: str, rel_path: str, dep_type: str) -> List[Finding]:
        findings = []
        license_lower = license_str.strip().lower()
        for disallowed in DISALLOWED_LICENSES:
            if disallowed.lower() == license_lower:
                findings.append(Finding(
                    id=f"dep-gov-{scan_id}-license-{disallowed}",
                    source="dependency-governance",
                    rule_id=f"DISALLOWED-LICENSE-{disallowed}",
                    title=f"Disallowed License: {disallowed}",
                    description=f"The package at {rel_path} uses the {disallowed} license which is "
                                f"disallowed by governance policy.",
                    severity=Severity.MEDIUM,
                    confidence="HIGH",
                    location={
                        "file": rel_path,
                        "license": disallowed,
                    },
                    recommendation=f"Replace this dependency with an alternative that uses a permissive "
                                  f"license (MIT, Apache-2.0, BSD, ISC, etc.) or seek legal approval.",
                    scan_type=ScanType.SCA,
                ))
        return findings

    def _match_blocklist_package(self, pkg_name: str) -> Optional[str]:
        for canonical, matchers in PACKAGE_NAME_MATCHERS.items():
            for matcher in matchers:
                if matcher == pkg_name:
                    return canonical
        if pkg_name in KNOWN_MALICIOUS_OR_DEPRECATED:
            return pkg_name
        return None

    def _blocklist_severity(self, block_type: str) -> Severity:
        if block_type == "malicious":
            return Severity.CRITICAL
        elif block_type == "vulnerable":
            return Severity.HIGH
        return Severity.MEDIUM

    def _is_version_in_range(self, version: str, version_range: str) -> bool:
        if not version:
            return False
        version = version.lstrip("=^~<>vV").strip()
        try:
            parts = version.split(".")
            major = int(parts[0]) if parts[0].isdigit() else None
        except (ValueError, IndexError):
            return False

        if version_range.startswith("<"):
            try:
                range_ver = version_range.lstrip("<").strip()
                range_parts = range_ver.split(".")
                range_major = int(range_parts[0]) if range_parts[0].isdigit() else None
                if major is not None and range_major is not None:
                    if major < range_major:
                        return True
                    if major > range_major:
                        return False
                    range_minor = int(range_parts[1]) if len(range_parts) > 1 and range_parts[1].isdigit() else 0
                    try:
                        minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                    except (IndexError, ValueError):
                        minor = 0
                    if minor < range_minor:
                        return True
                    if minor > range_minor:
                        return False
                    range_patch = int(range_parts[2]) if len(range_parts) > 2 and range_parts[2].isdigit() else 0
                    try:
                        patch = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
                    except (IndexError, ValueError):
                        patch = 0
                    return patch < range_patch
            except (ValueError, IndexError):
                return False

        return False
