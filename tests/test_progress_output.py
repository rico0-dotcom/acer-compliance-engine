
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

def test_progress_hooks_present():
    llm = (BASE/"scripts/run_llm_assisted_adaptation.py").read_text(encoding="utf-8")
    ms = (BASE/"scripts/run_multiseed_adaptation_evaluation.py").read_text(encoding="utf-8")
    assert "LLM progress:" in llm
    assert "run_live" in ms
    assert "Reusing completed LLM result" in ms
