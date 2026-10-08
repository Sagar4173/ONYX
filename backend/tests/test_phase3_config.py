"""Phase 3 config: approval/dry-run/gates/screening defaults + env overrides."""
from config import Settings, settings


def _settings(**overrides):
    base = dict(
        _env_file=None,
        mongodb_uri="mongodb://localhost:27017/onyx",
        secret_key="test-secret-key-" + "x" * 16,
    )
    base.update(overrides)
    return Settings(**base)


def test_phase3_defaults():
    s = _settings()
    assert s.auto_fix_requires_approval is True
    assert s.auto_fix_dry_run is False
    assert s.auto_fix_max_diff_lines == 50
    assert s.fix_agent_max_tool_retries == 2
    assert s.fix_agent_output_token_limit == 4000
    assert s.injection_screen_enabled is True
    assert s.injection_screen_fail_open is True
    assert s.injection_screen_model == "meta-llama/llama-prompt-guard-2-86m"


def test_phase3_env_overrides(monkeypatch):
    monkeypatch.setenv("AUTO_FIX_REQUIRES_APPROVAL", "false")
    monkeypatch.setenv("AUTO_FIX_DRY_RUN", "true")
    monkeypatch.setenv("AUTO_FIX_MAX_DIFF_LINES", "10")
    monkeypatch.setenv("INJECTION_SCREEN_FAIL_OPEN", "false")
    s = _settings()
    assert s.auto_fix_requires_approval is False
    assert s.auto_fix_dry_run is True
    assert s.auto_fix_max_diff_lines == 10
    assert s.injection_screen_fail_open is False


def test_settings_instance_exposes_phase3_fields():
    assert settings.auto_fix_requires_approval in (True, False)
    assert settings.injection_screen_model.startswith("meta-llama/")
