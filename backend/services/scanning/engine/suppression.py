"""
Suppression Engine
==================

Engine for suppressing and filtering security findings.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from utils.datetime_utils import utc_now

from ..base.models import Finding, Severity

logger = logging.getLogger(__name__)


@dataclass
class SuppressionRule:
    """A rule for suppressing findings."""
    id: str
    description: str
    enabled: bool = True
    
    # Match criteria (all specified must match)
    rule_ids: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    file_patterns: List[str] = field(default_factory=list)
    title_patterns: List[str] = field(default_factory=list)
    severities: List[Severity] = field(default_factory=list)
    
    # Expiration
    expires: Optional[datetime] = None
    
    # Reason for suppression
    reason: str = ""
    author: str = ""
    created: datetime = field(default_factory=utc_now)
    
    def matches(self, finding: Finding) -> bool:
        """Check if this rule matches a finding."""
        if not self.enabled:
            return False
        
        if self.expires and utc_now() > self.expires:
            return False
        
        # Rule ID match
        if self.rule_ids and finding.rule_id not in self.rule_ids:
            return False
        
        # Source match
        if self.sources and finding.source not in self.sources:
            return False
        
        # Severity match
        if self.severities and finding.severity not in self.severities:
            return False
        
        # File pattern match
        if self.file_patterns:
            file_path = finding.location.get("file", "")
            if not any(self._match_pattern(p, file_path) for p in self.file_patterns):
                return False
        
        # Title pattern match
        if self.title_patterns:
            if not any(self._match_pattern(p, finding.title) for p in self.title_patterns):
                return False
        
        return True
    
    def _match_pattern(self, pattern: str, text: str) -> bool:
        """Match a pattern against text."""
        try:
            # Try regex first
            if pattern.startswith("^") or pattern.endswith("$"):
                return bool(re.match(pattern, text, re.IGNORECASE))
            
            # Glob-style matching
            pattern = pattern.replace("**", ".*").replace("*", "[^/]*").replace("?", ".")
            return bool(re.match(f".*{pattern}.*", text, re.IGNORECASE))
        except re.error:
            # Fall back to substring match
            return pattern.lower() in text.lower()


class SuppressionEngine:
    """
    Engine for managing and applying finding suppressions.
    
    Supports:
    - Rule-based suppressions
    - File-based suppressions (YAML/JSON config)
    - Inline comment suppressions
    - Temporary suppressions with expiration
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.rules: List[SuppressionRule] = []
        self.suppressed_findings: List[Dict[str, Any]] = []
        
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: str) -> None:
        """Load suppression rules from config file."""
        path = Path(config_path)
        
        if not path.exists():
            logger.warning(f"Suppression config not found: {config_path}")
            return
        
        try:
            content = path.read_text()
            
            if path.suffix in [".yaml", ".yml"]:
                data = yaml.safe_load(content)
            elif path.suffix == ".json":
                data = json.loads(content)
            else:
                logger.warning(f"Unsupported config format: {path.suffix}")
                return
            
            self._parse_config(data)
            logger.info(f"Loaded {len(self.rules)} suppression rules from {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load suppression config: {e}")
    
    def _parse_config(self, data: Dict[str, Any]) -> None:
        """Parse configuration data into suppression rules."""
        rules_data = data.get("suppressions", data.get("rules", []))
        
        for rule_data in rules_data:
            try:
                rule = SuppressionRule(
                    id=rule_data.get("id", f"rule-{len(self.rules)}"),
                    description=rule_data.get("description", ""),
                    enabled=rule_data.get("enabled", True),
                    rule_ids=rule_data.get("rule_ids", []),
                    sources=rule_data.get("sources", []),
                    file_patterns=rule_data.get("file_patterns", []),
                    title_patterns=rule_data.get("title_patterns", []),
                    severities=[
                        Severity(s) for s in rule_data.get("severities", [])
                    ],
                    expires=self._parse_expiration(rule_data.get("expires")),
                    reason=rule_data.get("reason", ""),
                    author=rule_data.get("author", "")
                )
                self.rules.append(rule)
            except Exception as e:
                logger.error(f"Failed to parse suppression rule: {e}")
    
    def _parse_expiration(self, expires: Any) -> Optional[datetime]:
        """Parse expiration date/duration."""
        if not expires:
            return None
        
        if isinstance(expires, datetime):
            return expires
        
        if isinstance(expires, str):
            # Try parsing as ISO date
            try:
                return datetime.fromisoformat(expires)
            except ValueError:
                pass
            
            # Try parsing as duration (e.g., "30d", "1w")
            duration_match = re.match(r"(\d+)([dwmh])", expires)
            if duration_match:
                value = int(duration_match.group(1))
                unit = duration_match.group(2)
                
                if unit == "h":
                    return utc_now() + timedelta(hours=value)
                elif unit == "d":
                    return utc_now() + timedelta(days=value)
                elif unit == "w":
                    return utc_now() + timedelta(weeks=value)
                elif unit == "m":
                    return utc_now() + timedelta(days=value * 30)
        
        return None
    
    def add_rule(self, rule: SuppressionRule) -> None:
        """Add a suppression rule."""
        self.rules.append(rule)
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a suppression rule by ID."""
        for i, rule in enumerate(self.rules):
            if rule.id == rule_id:
                self.rules.pop(i)
                return True
        return False
    
    def apply(self, findings: List[Finding]) -> List[Finding]:
        """
        Apply suppression rules to findings.
        
        Returns only the non-suppressed findings.
        """
        if not self.rules:
            return findings
        
        active_findings = []
        self.suppressed_findings = []
        
        for finding in findings:
            suppressed = False
            matched_rule = None
            
            for rule in self.rules:
                if rule.matches(finding):
                    suppressed = True
                    matched_rule = rule
                    break
            
            if suppressed:
                self.suppressed_findings.append({
                    "finding": finding,
                    "rule_id": matched_rule.id,
                    "reason": matched_rule.reason
                })
                logger.debug(
                    f"Suppressed finding {finding.id} by rule {matched_rule.id}"
                )
            else:
                active_findings.append(finding)
        
        if self.suppressed_findings:
            logger.info(
                f"Suppressed {len(self.suppressed_findings)} of "
                f"{len(findings)} findings"
            )
        
        return active_findings
    
    def get_suppressed(self) -> List[Dict[str, Any]]:
        """Get list of suppressed findings with reasons."""
        return self.suppressed_findings
    
    def check_inline_suppression(
        self, 
        file_content: str, 
        finding: Finding
    ) -> bool:
        """
        Check for inline suppression comments.
        
        Supports formats:
        - # noqa: RULE_ID
        - # security-ignore: RULE_ID
        - // ONYX-SUPPRESS: RULE_ID
        """
        line_num = finding.location.get("line", finding.location.get("line_start", 0))
        
        if not line_num:
            return False
        
        lines = file_content.split("\n")
        if line_num > len(lines):
            return False
        
        line = lines[line_num - 1]
        rule_id = finding.rule_id
        
        # Check various suppression comment formats
        patterns = [
            rf"#\s*noqa:\s*{rule_id}",
            rf"#\s*security-ignore:\s*{rule_id}",
            rf"//\s*ONYX-SUPPRESS:\s*{rule_id}",
            rf"#\s*type:\s*ignore\[{rule_id}\]",
            rf"/\*\s*ONYX-SUPPRESS:\s*{rule_id}\s*\*/",
        ]
        
        for pattern in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        
        # Check previous line for suppression comment
        if line_num > 1:
            prev_line = lines[line_num - 2]
            for pattern in patterns:
                if re.search(pattern, prev_line, re.IGNORECASE):
                    return True
        
        return False
    
    def export_config(self, output_path: str) -> None:
        """Export current suppression rules to a config file."""
        rules_data = []
        
        for rule in self.rules:
            rule_dict = {
                "id": rule.id,
                "description": rule.description,
                "enabled": rule.enabled
            }
            
            if rule.rule_ids:
                rule_dict["rule_ids"] = rule.rule_ids
            if rule.sources:
                rule_dict["sources"] = rule.sources
            if rule.file_patterns:
                rule_dict["file_patterns"] = rule.file_patterns
            if rule.title_patterns:
                rule_dict["title_patterns"] = rule.title_patterns
            if rule.severities:
                rule_dict["severities"] = [s.value for s in rule.severities]
            if rule.expires:
                rule_dict["expires"] = rule.expires.isoformat()
            if rule.reason:
                rule_dict["reason"] = rule.reason
            if rule.author:
                rule_dict["author"] = rule.author
            
            rules_data.append(rule_dict)
        
        output = {"suppressions": rules_data}
        
        path = Path(output_path)
        if path.suffix in [".yaml", ".yml"]:
            content = yaml.dump(output, default_flow_style=False)
        else:
            content = json.dumps(output, indent=2)
        
        path.write_text(content)
        logger.info(f"Exported {len(self.rules)} suppression rules to {output_path}")
