import json
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE / "scripts" / "run_adaptation_comparison.py"


def test_script_exists():
    assert SCRIPT.exists()


def test_comparison_runs_on_real_benchmark(tmp_path):
    results = tmp_path / "results"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--results", str(results)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    summary = json.loads((results / "adaptation_strategy_comparison.json").read_text(encoding="utf-8"))
    assert set(summary["strategies"]) == {"FIXED_ORDER", "CHEAPEST_GREEDY", "AGENTIC"}
    for item in summary["strategies"].values():
        assert item["systems"] == 21
        assert item["violations_before"] == 24
        assert item["violations_after"] == 0
        assert item["new_failures_total"] == 0
        assert item["systems_compliant_after"] == 21


def test_agentic_reports_selection_metrics_without_invalid_superiority_assumption(tmp_path):
    results = tmp_path / "results"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--results", str(results)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    summary = json.loads((results / "adaptation_strategy_comparison.json").read_text(encoding="utf-8"))
    for name in ("FIXED_ORDER", "CHEAPEST_GREEDY", "AGENTIC"):
        strategy = summary["strategies"][name]
        assert strategy["accepted_adaptation_steps"] >= 0
        assert strategy["total_cost"] >= 0
        assert strategy["total_complexity"] >= 0
        assert strategy["new_failures_total"] == 0
