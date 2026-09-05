
from pathlib import Path
import json, subprocess, sys

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE/"scripts/run_multiseed_adaptation_evaluation.py"

def test_multiseed_deterministic_evaluation():
    p = subprocess.run(
        [sys.executable, str(SCRIPT), "--seeds", "20260904", "20260905", "--count", "20"],
        capture_output=True, text=True
    )
    assert p.returncode == 0, p.stderr
    # The runner emits progress before its final JSON. Parse the persisted result
    # instead of assuming stdout contains JSON only.
    path = BASE/"data/results/adaptation_multiseed/multiseed_summary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["seeds"] == [20260904, 20260905]
    assert len(data["per_seed"]) == 2
    for r in data["per_seed"]:
        assert r["deterministic_conditions"]["FIXED_ORDER"]["systems"] == 20
        assert r["deterministic_conditions"]["AGENTIC"]["systems"] == 20
