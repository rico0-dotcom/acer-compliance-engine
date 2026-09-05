from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE / "scripts" / "run_ablation_study.py"

def test_ablation_study_runs_from_completed_results():
    p = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    out = BASE / "data/results/ablation_study/ablation_summary.json"
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["total_systems"] == 300
    assert set(data["conditions"]) == {"FIXED_ORDER", "AGENTIC_NO_LLM", "AGENTIC_LLM"}
    assert data["conditions"]["AGENTIC_LLM"]["llm_failures"] == [0, 0, 0]
    assert data["ablations"]["agentic_selection_contribution"]["comparison"] == "AGENTIC_NO_LLM_vs_FIXED_ORDER"
    assert data["ablations"]["llm_assistance_contribution"]["comparison"] == "AGENTIC_LLM_vs_AGENTIC_NO_LLM"
