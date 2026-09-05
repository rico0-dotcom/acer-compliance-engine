from pathlib import Path
import csv
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]


def test_balanced_benchmark_generation_and_prediction():
    gen = subprocess.run(
        [sys.executable, str(BASE / "scripts" / "generate_ai_act_benchmark.py")],
        cwd=BASE, capture_output=True, text=True, check=True
    )
    assert "Generated 21 benchmark scenarios" in gen.stdout
    assert "Created 168 independent benchmark labels" in gen.stdout

    pred = subprocess.run(
        [sys.executable, str(BASE / "scripts" / "evaluate_ai_act_benchmark.py")],
        cwd=BASE, capture_output=True, text=True, check=True
    )
    assert '"scenarios": 21' in pred.stdout
    assert '"requirements": 8' in pred.stdout
    assert '"requirement_predictions": 168' in pred.stdout

    gt = BASE / "data" / "ground_truth" / "eu_ai_act_ground_truth.csv"
    with gt.open("r", encoding="utf-8", newline="") as f:
        gt_rows = list(csv.DictReader(f))
    assert len(gt_rows) == 168

    statuses = {row["expected_status"] for row in gt_rows}
    assert {"PASS", "FAIL", "NOT_APPLICABLE"} <= statuses

    predictions = BASE / "data" / "results" / "benchmark_predictions.csv"
    with predictions.open("r", encoding="utf-8", newline="") as f:
        pred_rows = list(csv.DictReader(f))
    assert len(pred_rows) == 168
    assert {row["predicted_status"] for row in pred_rows} <= {
        "PASS", "FAIL", "NOT_APPLICABLE", "UNCERTAIN"
    }
