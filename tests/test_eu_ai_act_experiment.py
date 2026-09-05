import json
import subprocess
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parents[1]


def test_eu_ai_act_experiment_reaches_compliance():
    """End-to-end regression test for the current real EU AI Act pipeline."""
    result = subprocess.run(
        [
            sys.executable,
            str(BASE / "scripts" / "run_eu_ai_act_experiment.py"),
            "--scenarios",
            "10",
            "--seed",
            "42",
        ],
        cwd=BASE,
        capture_output=True,
        text=True,
        check=True,
    )

    summary_path = BASE / "data" / "results" / "eu_ai_act_summary.json"
    assert summary_path.exists(), "EU AI Act experiment did not produce its summary."

    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary["requirements"] == 8
    assert summary["scenarios"] == 10
    assert summary["requirement_checks"] == 80
    assert summary["baseline_noncompliant"] == 10
    assert summary["final_compliant"] == 10
    assert summary["adaptation_success_rate"] == 1.0
    assert summary["mean_adaptation_steps"] > 0

    # Keep the subprocess output available when this regression test fails.
    assert result.stdout
