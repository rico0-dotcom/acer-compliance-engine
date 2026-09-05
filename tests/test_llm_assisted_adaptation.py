import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE / "scripts" / "run_llm_assisted_adaptation.py"


def test_script_exists():
    assert SCRIPT.exists()


def test_llm_cannot_invent_executable_action_ids():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "allowed_action_ids" in text
    assert "if action_id not in allowed" in text


def test_llm_cannot_directly_declare_compliance():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "deterministic ACER assessor" in text
    assert "cannot declare compliance" in text


def test_summary_schema(tmp_path, monkeypatch):
    sys.path.insert(0, str(BASE))
    import scripts.run_llm_assisted_adaptation as mod
    fake = {
        "response": {"recommendations": [{"action_id": "ENABLE_DECISION_LOGGING", "targets": ["EUAI-R12-01"], "priority": 1, "rationale": "test"}]},
        "allowed_action_ids": ["ENABLE_DECISION_LOGGING"],
        "provider": "fake",
        "model": "fake-model",
    }
    monkeypatch.setattr(mod, "call_llm", lambda *args, **kwargs: fake)
    cands = mod.build_llm_candidates(fake, ["EUAI-R12-01"])
    assert cands[0]["id"] == "ENABLE_DECISION_LOGGING"
    assert cands[0]["targets"] == ["EUAI-R12-01"]
