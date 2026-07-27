from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.report import AIAnalysis


@pytest.fixture(autouse=True)
def _patch_settings():
    with patch("services.ai.ollama_ai_processor.settings") as mock:
        mock.ai_local_base_url = "http://localhost:11434/v1"
        mock.ai_local_model = "qwen2.5-coder:1.5b"
        mock.ai_local_timeout = 120
        mock.openai_max_tokens = 2000
        yield mock


@pytest.fixture
def processor():
    from services.ai.ollama_ai_processor import OllamaVulnerabilityAIProcessor

    with patch("services.ai.ollama_ai_processor.AsyncOpenAI") as mock_client:
        inst = OllamaVulnerabilityAIProcessor()
        inst.client = mock_client
        yield inst


class TestOllamaProcessorHealth:
    @pytest.mark.asyncio
    async def test_check_health_success(self, processor):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"models": [{"name": "qwen2.5-coder:1.5b"}]}

        with patch("httpx.AsyncClient") as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)
            result = await processor._check_health()
            assert result is True

    @pytest.mark.asyncio
    async def test_check_health_no_models(self, processor):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"models": []}

        with patch("httpx.AsyncClient") as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)
            result = await processor._check_health()
            assert result is False

    @pytest.mark.asyncio
    async def test_check_health_connection_error(self, processor):
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value.get = AsyncMock(side_effect=Exception("Connection refused"))
            result = await processor._check_health()
            assert result is False


class TestOllamaProcessorCall:
    @pytest.mark.asyncio
    async def test_call_ollama_success(self, processor):
        mock_choice = MagicMock()
        mock_choice.message.content = "Test analysis response"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        processor.client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await processor._call_ollama("test prompt")
        assert result == "Test analysis response"
        processor.client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_ollama_with_json_format(self, processor):
        mock_choice = MagicMock()
        mock_choice.message.content = '{"key": "value"}'
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        processor.client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await processor._call_ollama("test prompt", response_format={"type": "json_object"})
        assert result == '{"key": "value"}'

        call_kwargs = processor.client.chat.completions.create.call_args[1]
        assert call_kwargs["response_format"] == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_call_ollama_failure(self, processor):
        processor.client.chat.completions.create = AsyncMock(side_effect=Exception("API error"))

        with pytest.raises(Exception):
            await processor._call_ollama("test prompt")


class TestOllamaProcessorAnalysis:
    @pytest.mark.asyncio
    async def test_analyze_scan_results_clean(self, processor):
        with patch.object(processor, "_prepare_findings_data", return_value={"total_findings": 0}):
            result = await processor.analyze_scan_results([])
            assert isinstance(result, AIAnalysis)
            assert result.risk_score == 5
            assert result.risk_level == "LOW"
            assert result.security_score == 98

    @pytest.mark.asyncio
    async def test_analyze_scan_results_with_findings(self, processor):
        mock_finding = MagicMock()
        mock_finding.title = "SQL Injection"
        mock_finding.description = "SQL injection in login"
        mock_finding.severity = "critical"
        mock_finding.scanner = "semgrep"
        mock_finding.file_path = "app/login.py"
        mock_finding.rule_id = "sql-injection-1"
        mock_finding.cwe_id = "CWE-89"
        mock_finding.cve_id = ""
        mock_finding.owasp_category = "A1"

        mock_result = MagicMock()
        mock_result.scanner = MagicMock()
        mock_result.scanner.value = "semgrep"
        mock_result.status = MagicMock()
        mock_result.status.value = "completed"
        mock_result.duration_seconds = 10
        mock_result.findings = [mock_finding]

        processor._call_ollama = AsyncMock(return_value="AI generated summary")

        with patch.object(processor, "_prepare_findings_data") as mock_prep:
            mock_prep.return_value = {
                "total_findings": 1,
                "findings": [mock_finding],
                "severity_counts": {"critical": 1, "high": 0, "medium": 0, "low": 0, "info": 0},
                "scanner_summary": {"semgrep": 1},
                "high_severity_count": 1,
            }

            result = await processor.analyze_scan_results([mock_result])
            assert isinstance(result, AIAnalysis)
            assert result.risk_score >= 40
            assert result.model_used == "ollama/qwen2.5-coder:1.5b"
            assert "ollama" in result.model_used

    @pytest.mark.asyncio
    async def test_analyze_scan_results_partial_failure(self, processor):
        mock_finding = MagicMock()
        mock_finding.title = "Test finding"
        mock_finding.description = "test"
        mock_finding.severity = "medium"
        mock_finding.scanner = "semgrep"
        mock_finding.file_path = "test.py"
        mock_finding.rule_id = "test-1"
        mock_finding.cwe_id = ""
        mock_finding.cve_id = ""
        mock_finding.owasp_category = ""
        # Override get() to return actual values instead of MagicMock
        mock_finding.get = lambda key, default="": getattr(mock_finding, key, default)

        mock_result = MagicMock()
        mock_result.scanner = MagicMock()
        mock_result.scanner.value = "semgrep"
        mock_result.status = MagicMock()
        mock_result.status.value = "completed"
        mock_result.duration_seconds = 5
        mock_result.findings = [mock_finding]

        processor._call_ollama = AsyncMock(side_effect=[Exception("Summary failed"), "Risk assessment"])

        with patch.object(processor, "_prepare_findings_data") as mock_prep:
            mock_prep.return_value = {
                "total_findings": 1,
                "findings": [mock_finding],
                "severity_counts": {"critical": 0, "high": 0, "medium": 1, "low": 0, "info": 0},
                "scanner_summary": {"semgrep": 1},
                "high_severity_count": 0,
            }

            result = await processor.analyze_scan_results([mock_result])
            assert isinstance(result, AIAnalysis)
            # Fallback message from _generate_executive_summary exception handler
            assert "findings requiring attention" in result.executive_summary


class TestOllamaProcessorEnrichment:
    @pytest.mark.asyncio
    async def test_enrich_findings_with_remediation(self, processor):
        finding = MagicMock()
        finding.title = "SQL Injection"
        finding.description = "SQL injection in login"
        finding.severity = "critical"
        finding.file_path = "app/login.py"
        finding.code_snippet = "cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')"
        finding.cwe_id = "CWE-89"
        finding.remediation = None
        finding.fix_effort = None
        finding.remediation_code = None

        processor._call_ollama = AsyncMock(
            return_value='{"remediation": "Use parameterized queries", "fix_effort": "medium", "secure_code": "cursor.execute(\\"SELECT * FROM users WHERE id = ?\\", (user_id,))"}'
        )

        result = await processor.enrich_findings_with_remediation([finding])
        assert len(result) == 1
        assert result[0].remediation == "Use parameterized queries"
        assert result[0].fix_effort == "medium"
        assert result[0].remediation_code is not None

    @pytest.mark.asyncio
    async def test_enrich_findings_empty_skip(self, processor):
        finding = MagicMock()
        finding.title = ""
        finding.description = ""
        finding.severity = ""
        finding.file_path = ""
        finding.code_snippet = ""
        finding.cwe_id = ""
        # Override get() to return empty strings so the skip logic works
        finding.get = lambda key, default="": ""

        processor._call_ollama = AsyncMock()

        result = await processor.enrich_findings_with_remediation([finding])
        assert len(result) == 1
        processor._call_ollama.assert_not_called()


class TestOllamaProcessorHelpers:
    def test_prepare_findings_data_empty(self, processor):
        data = processor._prepare_findings_data([])
        assert data["total_findings"] == 0
        assert data["severity_counts"]["critical"] == 0

    def test_prepare_findings_data_with_results(self, processor):
        finding = MagicMock()
        finding.severity = "high"
        finding.title = "Test"
        finding.description = ""
        finding.file_path = ""
        finding.rule_id = ""
        finding.cwe_id = ""
        finding.cve_id = ""
        finding.owasp_category = ""
        finding.scanner = "semgrep"

        result = MagicMock()
        result.scanner = MagicMock()
        result.scanner.value = "semgrep"
        result.findings = [finding]

        data = processor._prepare_findings_data([result])
        assert data["total_findings"] == 1
        assert data["severity_counts"]["high"] == 1
        assert data["high_severity_count"] == 1

    def test_calculate_risk_score(self, processor):
        data = {
            "severity_counts": {"critical": 1, "high": 2, "medium": 0, "low": 0, "info": 0},
        }
        score, level = processor._calculate_risk_score(data)
        assert score == 90
        assert level == "CRITICAL"

    def test_calculate_security_score(self, processor):
        data = {
            "severity_counts": {"critical": 1, "high": 1, "medium": 1, "low": 1, "info": 1},
        }
        score = processor._calculate_security_score(data)
        assert score == 60

    def test_categorize_threats(self, processor):
        data = {"findings": [{"title": "SQL Injection vulnerability", "description": "SQL injection in login"}]}
        cats = processor._categorize_threats(data)
        assert cats.get("Injection") == 1

    def test_estimate_fix_time(self, processor):
        data = {
            "severity_counts": {"critical": 1, "high": 1, "medium": 1, "low": 1, "info": 1},
        }
        result = processor._estimate_fix_time(data)
        assert "hours" in result

    def test_remediation_roadmap(self, processor):
        data = {
            "severity_counts": {"critical": 1, "high": 2, "medium": 3, "low": 0, "info": 0},
        }
        roadmap = processor._generate_remediation_roadmap(data)
        assert len(roadmap) == 3
        assert roadmap[0]["priority"] == "CRITICAL"
        assert roadmap[1]["priority"] == "HIGH"
        assert roadmap[2]["priority"] == "MEDIUM"

    def test_create_clean_analysis(self, processor):
        analysis = processor._create_clean_analysis()
        assert isinstance(analysis, AIAnalysis)
        assert analysis.risk_score == 5
        assert analysis.security_score == 98
