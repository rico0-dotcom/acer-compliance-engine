from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE / "scripts" / "evaluate_three_way_statistics.py"


def test_three_way_evaluation_runs_on_saved_results():
    p = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    path = BASE / "data/results/adaptation_multiseed/statistical_evaluation_three_way.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["total_systems"] == 300
    assert "AGENTIC_vs_FIXED_ORDER" in data["comparisons"]
    assert "AGENTIC_NO_LLM_vs_AGENTIC_LLM" in data["comparisons"]
    assert data["comparisons"]["AGENTIC_NO_LLM_vs_AGENTIC_LLM"]["llm_failures"] == [0, 0, 0]
    assert data["comparisons"]["AGENTIC_NO_LLM_vs_AGENTIC_LLM"]["steps"]["n"] == 3
