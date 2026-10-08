"""Deterministic validation gates for agent-proposed patches (spec 4.3.2).

Gates: single-file allowlist, non-empty, Python syntax, diff-size cap, and a
detect-secrets scan over the diff's ADDED lines. Secrets introduced by a patch
are exactly the secrets on its added lines, so original content is never
re-scanned (avoids false positives on pre-existing secrets). Scan failures
fail CLOSED. (`SecretsCollection.scan_diff` needs the optional `unidiff`
package; we deliberately avoid that dependency.)
"""
import ast
import difflib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List

from detect_secrets import SecretsCollection
from detect_secrets.settings import default_settings


@dataclass
class GateFailure:
    gate: str
    message: str


@dataclass
class GateReport:
    passed: bool
    failures: List[GateFailure]
    diff: str
    added_lines: int
    removed_lines: int


def _norm(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _secret_failures(added: List[str], target_path: str) -> List[GateFailure]:
    if not added:
        return []
    tmp = None
    try:
        suffix = Path(target_path).suffix or ".txt"
        with tempfile.NamedTemporaryFile(
            "w", suffix=suffix, encoding="utf-8", delete=False, newline="\n"
        ) as fh:
            fh.write("\n".join(added) + "\n")
            tmp = fh.name
        secrets = SecretsCollection()
        with default_settings():
            secrets.scan_file(tmp)
        flagged = sum(1 for filename in secrets.files for _ in secrets[filename])
    except Exception as e:  # fail closed: a broken secret scan blocks the patch
        return [GateFailure("secrets", f"secret scan failed: {e}")]
    finally:
        if tmp:
            try:
                os.unlink(tmp)
            except OSError:
                pass
    if flagged:
        return [GateFailure("secrets", f"detected {flagged} secret-like string(s) on added lines")]
    return []


def validate_patch(
    *,
    target_path: str,
    finding_file_path: str,
    original: str,
    patched: str,
    max_diff_lines: int,
) -> GateReport:
    failures: List[GateFailure] = []

    if _norm(target_path) != _norm(finding_file_path):
        failures.append(
            GateFailure(
                "allowlist",
                f"patch targets {target_path!r}; finding is at {finding_file_path!r}",
            )
        )
    if not patched.strip():
        failures.append(GateFailure("non_empty", "patched file is empty"))
    if Path(target_path).suffix == ".py":
        try:
            ast.parse(patched)
        except SyntaxError as e:
            failures.append(GateFailure("syntax", f"line {e.lineno}: {e.msg}"))

    diff_list = list(
        difflib.unified_diff(
            original.splitlines(),
            patched.splitlines(),
            fromfile=target_path,
            tofile=target_path,
            lineterm="",
        )
    )
    added = [ln[1:] for ln in diff_list if ln.startswith("+") and not ln.startswith("+++")]
    removed = [ln[1:] for ln in diff_list if ln.startswith("-") and not ln.startswith("---")]
    if len(added) + len(removed) > max_diff_lines:
        failures.append(
            GateFailure(
                "diff_size",
                f"{len(added) + len(removed)} changed lines exceeds cap of {max_diff_lines}",
            )
        )
    failures.extend(_secret_failures(added, target_path))

    diff_text = "\n".join(diff_list)
    if diff_text and not diff_text.endswith("\n"):
        diff_text += "\n"
    return GateReport(
        passed=not failures,
        failures=failures,
        diff=diff_text,
        added_lines=len(added),
        removed_lines=len(removed),
    )
