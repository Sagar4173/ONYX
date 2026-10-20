from typing import Any, Dict

SENSITIVE_METADATA_KEYS = ("pending_fixes",)


def redacted_report_metadata(metadata: Any) -> Dict[str, Any]:
    if not isinstance(metadata, dict):
        return {}
    return {k: v for k, v in metadata.items() if k not in SENSITIVE_METADATA_KEYS}
