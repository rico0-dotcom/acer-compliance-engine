from pathlib import Path
import csv
import json
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]


def test_benchmark_prediction_runner():
    result = subprocess.run(
        [sys.executable, str(BASE / "scripts" / "evaluate_ai_act_benchmark.py")],
        cwd=BASE,
        capture_output=True,
        text=True,
        check=True,
    )

    assert '"scenarios": 21' in result.stdout
    assert '"requirements": 8' in result.stdout
    assert '"requirement_predictions": 168' in result.stdout

    predictions = BASE / "data" / "results" / "benchmark_predictions.csv"
    summary = BASE / "data" / "results" / "benchmark_prediction_summary.json"

    assert predictions.exists()
    assert summary.exists()

    with predictions.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 168

    data = json.loads(summary.read_text(encoding="utf-8"))
    assert data["scenarios"] == 21
    assert data["requirements"] == 8
    assert data["requirement_predictions"] == 168
