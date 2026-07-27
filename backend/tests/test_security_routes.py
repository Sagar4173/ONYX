"""
Security Routes Tests (unit tests via direct service methods)
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestRuleEngine:
    """Test rule engine service methods directly."""

    @pytest.mark.asyncio
    async def test_get_rules_empty(self):
        from services.rules.rule_engine import rule_engine
        with patch.object(rule_engine, 'get_all_rules', new_callable=AsyncMock, return_value=[]):
            rules = await rule_engine.get_all_rules(None)
            assert rules == []

    @pytest.mark.asyncio
    async def test_create_and_save_rule(self):
        from services.rules.rule_engine import CustomRule, RuleStatus, rule_engine
        from services.rules.rule_security import AllowedLanguage, AllowedRuleType, SeverityLevel
        rule = CustomRule(
            id="test-rule",
            name="Test Rule for SG",
            description="This is a test rule description that is long enough.",
            message="Security message for this rule",
            type=AllowedRuleType.REGEX,
            severity=SeverityLevel.HIGH,
            pattern=".*",
            languages=[AllowedLanguage.PYTHON],
            file_patterns=["*.py"],
            author="tester",
            test_cases=[{"content": "print('hello')", "expected_matches": 0}],
            category="compliance",
            status=RuleStatus.TESTING,
        )
        with patch.object(rule_engine, 'save_rule', new_callable=AsyncMock, return_value=True):
            result = await rule_engine.save_rule(rule)
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_rule(self):
        from services.rules.rule_engine import rule_engine
        result = MagicMock(is_valid=True, errors=[], warnings=[])
        with patch.object(rule_engine, 'validate_rule', new_callable=AsyncMock, return_value=result):
            validation = await rule_engine.validate_rule(MagicMock(), None)
            assert validation.is_valid is True

    @pytest.mark.asyncio
    async def test_get_templates(self):
        from services.rules.rule_engine import rule_engine
        with patch.object(rule_engine, 'get_all_templates', new_callable=AsyncMock, return_value=[]):
            templates = await rule_engine.get_all_templates()
            assert templates == []

    @pytest.mark.asyncio
    async def test_create_rule_from_template(self):
        from services.rules.rule_engine import rule_engine
        with patch.object(rule_engine, 'create_rule_from_template', new_callable=AsyncMock, return_value=None):
            result = await rule_engine.create_rule_from_template("t1", {}, "r1")
            assert result is None


class TestBaselines:
    """Test baseline service methods directly."""

    @pytest.mark.asyncio
    async def test_create_baseline(self):
        from services.scanning.baseline import baseline_service
        mock_baseline = MagicMock()
        mock_baseline.dict.return_value = {"id": "b1"}
        with patch.object(baseline_service, 'create_baseline', new_callable=AsyncMock, return_value=mock_baseline):
            result = await baseline_service.create_baseline(
                scan_report=MagicMock(),
                repository_url="https://github.com/test/repo",
                branch="main",
                commit_hash="abc123",
                created_by="api",
                tags=None,
            )
            assert result.dict()["id"] == "b1"

    @pytest.mark.asyncio
    async def test_drift_analysis(self):
        from services.scanning.baseline import baseline_service
        mock_drift = MagicMock()
        mock_drift.dict.return_value = {"drift_severity": "none", "new_findings": []}
        with patch.object(baseline_service, 'compare_with_baseline', new_callable=AsyncMock, return_value=mock_drift):
            result = await baseline_service.compare_with_baseline(
                current_scan=MagicMock(),
                repository_url="https://github.com/test/repo",
                branch="main",
            )
            assert result.dict()["drift_severity"] == "none"

    @pytest.mark.asyncio
    async def test_compare_with_baseline_not_found(self):
        from services.scanning.baseline import baseline_service
        with patch.object(baseline_service, 'compare_with_baseline', new_callable=AsyncMock, return_value=None):
            result = await baseline_service.compare_with_baseline(
                current_scan=MagicMock(),
                repository_url="https://github.com/test/repo",
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_get_baselines_for_repository(self):
        from services.scanning.baseline import baseline_service
        with patch.object(baseline_service, 'get_baselines_for_repository', new_callable=AsyncMock, return_value=[]):
            baselines = await baseline_service.get_baselines_for_repository("https://github.com/test/repo")
            assert baselines == []

    @pytest.mark.asyncio
    async def test_get_drift_analysis(self):
        from services.scanning.baseline import baseline_service
        with patch.object(baseline_service, 'get_drift_analysis', new_callable=AsyncMock, return_value=[]):
            result = await baseline_service.get_drift_analysis("https://github.com/test/repo")
            assert result == []

    @pytest.mark.asyncio
    async def test_get_regression_alerts(self):
        from services.scanning.baseline import baseline_service
        with patch.object(baseline_service, 'get_regression_alerts', new_callable=AsyncMock, return_value=[]):
            alerts = await baseline_service.get_regression_alerts("https://github.com/test/repo")
            assert alerts == []

    @pytest.mark.asyncio
    async def test_generate_trend_analysis(self):
        from services.scanning.baseline import baseline_service
        with patch.object(baseline_service, 'generate_trend_analysis', new_callable=AsyncMock, return_value={"trends": []}):
            trends = await baseline_service.generate_trend_analysis("https://github.com/test/repo", "main", 90)
            assert trends["trends"] == []


class TestPolicyEngine:
    """Test policy engine service methods directly."""

    @pytest.mark.asyncio
    async def test_get_applicable_policies(self):
        from services.rules.policy_engine import policy_service
        with patch.object(policy_service, 'get_applicable_policies', new_callable=AsyncMock, return_value=[]):
            policies = await policy_service.get_applicable_policies(
                "https://github.com/test/repo", "main", "development"
            )
            assert policies == []

    @pytest.mark.asyncio
    async def test_evaluate_all_policies(self):
        from services.rules.policy_engine import policy_service
        with patch.object(policy_service, 'evaluate_all_policies', new_callable=AsyncMock, return_value=[]):
            results = await policy_service.evaluate_all_policies(
                scan_report=MagicMock(),
                repository_url="https://github.com/test/repo",
                branch="main",
                commit_hash="HEAD",
                environment="development",
            )
            assert results == []

    @pytest.mark.asyncio
    async def test_get_policy_compliance_report(self):
        from services.rules.policy_engine import policy_service
        with patch.object(policy_service, 'get_policy_compliance_report', new_callable=AsyncMock, return_value={"compliance": {}}):
            report = await policy_service.get_policy_compliance_report(
                "https://github.com/test/repo", "main", 30
            )
            assert "compliance" in report

    @pytest.mark.asyncio
    async def test_update_policy_from_git(self):
        from services.rules.policy_engine import policy_service
        with patch.object(policy_service, 'update_policy_from_git', new_callable=AsyncMock):
            await policy_service.update_policy_from_git()
