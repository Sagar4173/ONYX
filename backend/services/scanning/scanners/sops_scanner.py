"""
SOPS Configuration Scanner
==========================

Validates SOPS (Secrets OPerationS) configuration and encrypted files.
"""

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base.config import ScanConfig
from ..base.models import Finding, ScanType, Severity
from .base_scanner import BaseScanner

logger = logging.getLogger(__name__)


class SopsScanner(BaseScanner):
    """
    SOPS configuration scanner.

    Checks repositories for proper SOPS encryption setup including:
    - SOPS tool availability
    - .sops.yaml config file existence and validity
    - Proper age/pgp key configuration
    - Properly encrypted files vs files that should be encrypted
    """

    SCANNER_NAME = "sops"
    SCANNER_TYPE = ScanType.SECRETS

    SOPS_CONFIG_FILES = [".sops.yaml", ".sops.yml"]
    ENCRYPTED_EXTENSIONS = {".enc.yaml", ".enc.yml", ".enc.json", ".enc.env"}
    SENSITIVE_CONFIG_PATTERNS = [
        "secret", "password", "credential", "token", "key", "api_key",
        "api_secret", "db_password", "db_user", "access_key", "private_key",
        "auth_token", "secret_key", "client_secret", "connection_string",
    ]

    def __init__(self, config: ScanConfig = None):
        super().__init__(config)
        self.sops_path = getattr(config, 'sops_path', 'sops')

    async def scan(self, target: str, scan_id: str, **kwargs) -> List[Finding]:
        self.log_scan_start(target, scan_id)
        start_time = asyncio.get_event_loop().time()
        findings = []
        target_path = Path(target)

        if not target_path.is_dir():
            logger.warning(f"Target {target} is not a directory, skipping SOPS scan")
            return findings

        try:
            target_path = target_path.resolve()

            sops_config = self._find_sops_config(target_path)
            if sops_config:
                config_findings = self._validate_sops_config(sops_config, scan_id, target_path)
                findings.extend(config_findings)
            else:
                findings.append(self._create_missing_config_finding(scan_id))

            encrypted_findings = self._check_encrypted_files(target_path, scan_id)
            findings.extend(encrypted_findings)

            unencrypted_findings = self._find_unencrypted_secrets(target_path, scan_id)
            findings.extend(unencrypted_findings)

        except Exception as e:
            self.log_scan_error(scan_id, e)
            raise

        duration = asyncio.get_event_loop().time() - start_time
        self.log_scan_complete(scan_id, len(findings), duration)
        return findings

    async def is_available(self) -> bool:
        try:
            stdout, stderr, code = await self.run_command(
                [self.sops_path, "--version"],
                timeout=30
            )
            return code == 0
        except Exception:
            return False

    async def get_version(self) -> str:
        try:
            stdout, stderr, code = await self.run_command(
                [self.sops_path, "--version"],
                timeout=30
            )
            if code == 0 and stdout:
                return stdout.strip()
            return "unknown"
        except Exception:
            return "unknown"

    def _find_sops_config(self, target_path: Path) -> Optional[Path]:
        for config_file in self.SOPS_CONFIG_FILES:
            config_path = target_path / config_file
            if config_path.exists():
                return config_path
        current = target_path
        for config_file in self.SOPS_CONFIG_FILES:
            config_path = current / config_file
            if config_path.exists():
                return config_path
        return None

    def _validate_sops_config(
        self, config_path: Path, scan_id: str, target_path: Path
    ) -> List[Finding]:
        findings = []
        try:
            content = config_path.read_text()
            rel_path = str(config_path.relative_to(target_path)) if target_path else str(config_path)

            if "creation_rules" not in content:
                findings.append(self._create_finding(
                    scan_id=scan_id,
                    rule_id="SOPS-CONFIG-NO-RULES",
                    title="SOPS Configuration Missing Creation Rules",
                    description="The .sops.yaml file exists but does not define any creation_rules. "
                                "Without creation_rules, SOPS will not know which files to encrypt or which keys to use.",
                    severity=Severity.HIGH,
                    file_path=rel_path,
                    recommendation="Add creation_rules to .sops.yaml. Example:\n"
                                  "creation_rules:\n"
                                  "  - path_regex: secrets/*\n"
                                  "    age: age1abc123...\n"
                                  "  - path_regex: .*enc.yaml\n"
                                  "    pgp: FINGERPRINT...",
                ))

            has_age = bool(re.search(r'age:\s*\S+', content))
            has_pgp = bool(re.search(r'pgp:\s*\S+', content))
            has_kms = bool(re.search(r'kms:\s*\S+', content))
            has_gcp_kms = bool(re.search(r'gcp_kms:\s*\S+', content))
            has_azure_kv = bool(re.search(r'azure_keyvault:\s*\S+', content))
            has_hc_vault = bool(re.search(r'hc_vault:\s*\S+', content))
            has_key_info = any([has_age, has_pgp, has_kms, has_gcp_kms, has_azure_kv, has_hc_vault])

            if not has_key_info:
                findings.append(self._create_finding(
                    scan_id=scan_id,
                    rule_id="SOPS-CONFIG-NO-KEYS",
                    title="SOPS Configuration Missing Encryption Keys",
                    description="The .sops.yaml file does not specify any encryption keys "
                                "(age, pgp, kms, gcp_kms, azure_keyvault, or hc_vault). "
                                "At least one key provider must be configured.",
                    severity=Severity.CRITICAL,
                    file_path=rel_path,
                    recommendation="Configure at least one key provider in .sops.yaml. "
                                  "Example with age:\n"
                                  "creation_rules:\n"
                                  "  - age: age1abc123def456...\n"
                                  "Example with PGP:\n"
                                  "creation_rules:\n"
                                  "  - pgp: FINGERPRINT...",
                ))

            yaml = self._try_parse_yaml(content)
            if yaml and "creation_rules" in yaml:
                for i, rule in enumerate(yaml["creation_rules"]):
                    if not isinstance(rule, dict):
                        continue
                    has_key = any(k in rule for k in ["age", "pgp", "kms", "gcp_kms", "azure_keyvault", "hc_vault"])
                    if not has_key:
                        findings.append(self._create_finding(
                            scan_id=scan_id,
                            rule_id=f"SOPS-RULE-{i}-NO-KEYS",
                            title=f"Creation Rule {i} Missing Encryption Keys",
                            description=f"Creation rule at index {i} does not specify any encryption keys.",
                            severity=Severity.HIGH,
                            file_path=rel_path,
                            recommendation=f"Add encryption keys (age, pgp, kms, etc.) to creation rule {i}.",
                        ))

        except Exception as e:
            logger.warning(f"Failed to validate SOPS config {config_path}: {e}")

        return findings

    def _check_encrypted_files(self, target_path: Path, scan_id: str) -> List[Finding]:
        findings = []
        try:
            for ext in self.ENCRYPTED_EXTENSIONS:
                for encrypted_file in target_path.rglob(f"*{ext}"):
                    try:
                        rel_path = str(encrypted_file.relative_to(target_path))
                    except ValueError:
                        rel_path = str(encrypted_file)

                    content = encrypted_file.read_text()

                    if "sops" not in content:
                        findings.append(self._create_finding(
                            scan_id=scan_id,
                            rule_id="SOPS-FILE-NOT-ENCRYPTED",
                            title=f"File with Encrypted Extension is Not Encrypted: {rel_path}",
                            description=f"The file {rel_path} has an encrypted file extension ({ext}) "
                                        f"but does not contain SOPS metadata. It may be a plaintext file "
                                        f"with a misleading extension.",
                            severity=Severity.HIGH,
                            file_path=rel_path,
                            recommendation=f"Either encrypt the file with `sops -e {rel_path}` or "
                                          f"remove the {ext} extension if the file is not meant to be encrypted.",
                        ))
                    else:
                        try:
                            sops_data = json.loads(content)
                            if isinstance(sops_data, dict):
                                mac = sops_data.get("sops", {}).get("mac", "")
                                if not mac:
                                    findings.append(self._create_finding(
                                        scan_id=scan_id,
                                        rule_id="SOPS-FILE-MISSING-MAC",
                                        title=f"SOPS-Encrypted File Missing MAC: {rel_path}",
                                        description=f"The file {rel_path} has SOPS metadata but is missing "
                                                    f"a MAC (Message Authentication Code). The file integrity "
                                                    f"cannot be verified.",
                                        severity=Severity.MEDIUM,
                                        file_path=rel_path,
                                        recommendation=f"Re-encrypt the file with `sops -e -i {rel_path}` "
                                                      f"to ensure MAC is generated.",
                                    ))
                        except json.JSONDecodeError:
                            pass

            files_with_sops_meta = list(target_path.rglob("*"))
            for f in files_with_sops_meta:
                if f.is_file() and f.suffix not in {s.lstrip(".") if s.startswith(".") else s for s in self.ENCRYPTED_EXTENSIONS}:
                    try:
                        content = f.read_text()
                        if "sops" in content:
                            try:
                                data = json.loads(content)
                                if isinstance(data, dict) and "sops" in data:
                                    encrypted = data.get("sops", {})
                                    if encrypted.get("encrypted_regex") or any(
                                        k for k in data.keys() if k != "sops"
                                    ):
                                        try:
                                            rel_path = str(f.relative_to(target_path))
                                        except ValueError:
                                            rel_path = str(f)
                                        findings.append(self._create_finding(
                                            scan_id=scan_id,
                                            rule_id="SOPS-FILE-NONSTANDARD-EXT",
                                            title=f"SOPS-Encrypted File with Non-Standard Extension: {rel_path}",
                                            description=f"The file {rel_path} contains SOPS encryption metadata "
                                                        f"but does not use a standard encrypted extension "
                                                        f"({', '.join(sorted(self.ENCRYPTED_EXTENSIONS))}). "
                                                        f"This may cause confusion about the file's encryption status.",
                                            severity=Severity.LOW,
                                            file_path=rel_path,
                                            recommendation=f"Rename the file to use a standard encrypted extension "
                                                          f"(e.g., {f.name}.enc.yaml) or ensure team conventions "
                                                          f"are documented.",
                                        ))
                            except json.JSONDecodeError:
                                pass
                    except Exception:
                        pass

        except Exception as e:
            logger.warning(f"Error checking encrypted files in {target_path}: {e}")

        return findings

    def _find_unencrypted_secrets(self, target_path: Path, scan_id: str) -> List[Finding]:
        findings = []
        try:
            sensitive_dirs = ["secrets", "config", "deploy", "deployment", "env", "environments"]
            for sensitive_dir in sensitive_dirs:
                for dir_path in target_path.rglob(sensitive_dir):
                    if not dir_path.is_dir():
                        continue
                    for f in dir_path.rglob("*"):
                        if not f.is_file():
                            continue
                        if any(f.name.endswith(ext) for ext in {".yaml", ".yml", ".json", ".env", ".properties"}):
                            if f.name.startswith(".sops"):
                                continue
                            try:
                                rel_path = str(f.relative_to(target_path))
                            except ValueError:
                                rel_path = str(f)
                            content = f.read_text().lower()
                            has_sensitive = any(
                                pattern in content for pattern in self.SENSITIVE_CONFIG_PATTERNS
                            )
                            if has_sensitive and "sops" not in f.read_text():
                                findings.append(self._create_finding(
                                    scan_id=scan_id,
                                    rule_id="SOPS-UNENCRYPTED-SECRETS",
                                    title=f"Potential Unencrypted Secrets: {rel_path}",
                                    description=f"The file {rel_path} is in a sensitive directory "
                                                f"({sensitive_dir}) and contains potential secret values "
                                                f"(passwords, tokens, keys) but is not encrypted with SOPS.",
                                    severity=Severity.MEDIUM,
                                    file_path=rel_path,
                                    recommendation=f"Encrypt this file with SOPS: `sops -e -i {rel_path}`. "
                                                  f"Add a creation rule to .sops.yaml to automate this.",
                                ))

        except Exception as e:
            logger.warning(f"Error checking unencrypted secrets in {target_path}: {e}")

        return findings

    def _create_missing_config_finding(self, scan_id: str) -> Finding:
        return Finding(
            id=f"sops-{scan_id}-missing-config",
            source="sops",
            rule_id="SOPS-CONFIG-MISSING",
            title="SOPS Configuration File Not Found",
            description="No .sops.yaml or .sops.yml configuration file was found in the repository. "
                        "SOPS (Secrets OPerationS) is a tool for encrypting secrets in Git repositories. "
                        "Without a configuration file, encrypted secret management cannot be enforced.",
            severity=Severity.MEDIUM,
            confidence="HIGH",
            location={
                "file": ".sops.yaml",
            },
            recommendation="Create a .sops.yaml file to configure SOPS encryption for your secrets. "
                          "See https://github.com/mozilla/sops for documentation.",
            scan_type=ScanType.SECRETS,
        )

    def _create_finding(
        self, scan_id: str, rule_id: str, title: str, description: str,
        severity: Severity, file_path: str, recommendation: str,
    ) -> Finding:
        return Finding(
            id=f"sops-{scan_id}-{rule_id.lower()}",
            source="sops",
            rule_id=rule_id,
            title=title,
            description=description,
            severity=severity,
            confidence="HIGH",
            location={"file": file_path},
            recommendation=recommendation,
            scan_type=ScanType.SECRETS,
        )

    def _try_parse_yaml(self, content: str) -> Optional[Dict[str, Any]]:
        try:
            import yaml
            return yaml.safe_load(content)
        except ImportError:
            pass
        except Exception:
            pass
        result = {}
        current_rule = None
        current_key = None
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            if not line.startswith(" ") and not line.startswith("\t"):
                current_key = stripped.rstrip(":")
                if current_key:
                    result[current_key] = []
                current_rule = None
            elif stripped.startswith("- ") and current_key:
                rule_text = stripped[2:].strip()
                if rule_text.rstrip(",").isdigit():
                    result[current_key].append(int(rule_text.rstrip(",")))
                else:
                    result[current_key].append({})
                    current_rule = result[current_key][-1]
            elif current_rule is not None:
                if ":" in stripped:
                    k, v = stripped.split(":", 1)
                    current_rule[k.strip()] = v.strip()
        return result if result else None
