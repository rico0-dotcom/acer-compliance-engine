from pathlib import Path
import csv
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]


def test_benchmark_has_consistent_gold_and_architecture():
    subprocess.run(
        [sys.executable, str(BASE / "scripts" / "generate_ai_act_benchmark.py")],
        cwd=BASE, check=True, capture_output=True, text=True
    )
    subprocess.run(
        [sys.executable, str(BASE / "scripts" / "evaluate_ai_act_benchmark.py")],
        cwd=BASE, check=True, capture_output=True, text=True
    )

    gt = BASE / "data" / "ground_truth" / "eu_ai_act_ground_truth.csv"
    pred = BASE / "data" / "results" / "benchmark_predictions.csv"

    with gt.open("r", encoding="utf-8", newline="") as f:
        gold = {(r["scenario_id"], r["requirement_id"]): r["expected_status"]
                for r in csv.DictReader(f)}

    with pred.open("r", encoding="utf-8", newline="") as f:
        predictions = {(r["scenario_id"], r["requirement_id"]): r["predicted_status"]
                       for r in csv.DictReader(f)}

    assert len(gold) == 168
    assert len(predictions) == 168

    # These cases were the previously observed false mismatches.
    checks = [
        ("ai-act-benchmark-fail_r12_001", "EUAI-R14-02", "PASS"),
        ("ai-act-benchmark-fail_r12_r13_001", "EUAI-R14-02", "PASS"),
        ("ai-act-benchmark-fail_r14_001", "EUAI-R14-02", "FAIL"),
        ("ai-act-benchmark-fail_four_controls_001", "EUAI-R14-02", "FAIL"),
        ("ai-act-benchmark-na_r50_001", "EUAI-R14-02", "PASS"),
    ]

    for scenario_id, requirement_id, expected in checks:
        assert gold[(scenario_id, requirement_id)] == expected
        assert predictions[(scenario_id, requirement_id)] == expected
