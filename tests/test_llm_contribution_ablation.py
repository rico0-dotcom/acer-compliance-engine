
from pathlib import Path
import json
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE / "scripts" / "run_llm_contribution_ablation.py"

def test_ablation_preserves_three_common_conditions(tmp_path):
    systems = tmp_path / "systems"
    results = tmp_path / "results"
    gen = BASE / "scripts" / "generate_random_adaptation_benchmark.py"
    subprocess.run([sys.executable, str(gen), "--out", str(systems), "--count", "20"], check=True)
    subprocess.run([sys.executable, str(SCRIPT), "--systems", str(systems), "--results", str(results)], check=True)
    data = json.loads((results / "llm_contribution_ablation.json").read_text(encoding="utf-8"))
    cond = data["conditions"]
    assert set(cond) == {"DETERMINISTIC_BASELINE", "CHEAPEST_GREEDY", "AGENTIC_NO_LLM"}
    assert len({v["violations_before"] for v in cond.values()}) == 1

def test_ablation_does_not_claim_llm_result_without_run():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        systems = Path(d) / "systems"
        results = Path(d) / "results"
        gen = BASE / "scripts" / "generate_random_adaptation_benchmark.py"
        subprocess.run([sys.executable, str(gen), "--out", str(systems), "--count", "20"], check=True)
        subprocess.run([sys.executable, str(SCRIPT), "--systems", str(systems), "--results", str(results)], check=True)
        data = json.loads((results / "llm_contribution_ablation.json").read_text(encoding="utf-8"))
        assert data["llm_assisted_condition"] is None
