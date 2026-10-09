"""Phase 4 settings surface (spec 2.4, 4.4, 5.1 P4)."""
from config import settings


def test_investigate_agent_defaults():
    assert settings.investigate_agent_enabled is True
    assert settings.investigate_agent_max_tool_retries == 2
    assert settings.investigate_agent_output_token_limit == 3000


def test_ml_gate_defaults_off():
    assert settings.ml_isolation_forest_enabled is False
    assert settings.ml_min_training_scans == 30
    assert settings.ml_training_window_days == 90
