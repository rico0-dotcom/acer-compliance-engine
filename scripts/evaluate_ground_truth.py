from pathlib import Path
import argparse
import csv
import json
from collections import Counter

BASE = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = BASE / "data" / "results" / "benchmark_predictions.csv"
DEFAULT_GOLD = BASE / "data" / "ground_truth" / "eu_ai_act_ground_truth.csv"
DEFAULT_OUT = BASE / "data" / "results" / "independent_ground_truth_metrics.json"

VALID = {"PASS", "FAIL", "NOT_APPLICABLE", "UNCERTAIN"}


def norm(value):
    if value is None:
        return ""
    return str(value).strip().upper().replace("-", "_")


def load_csv(path):
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default=str(DEFAULT_RESULTS))
    parser.add_argument("--gold", default=str(DEFAULT_GOLD))
    parser.add_argument("--output", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    results_path = Path(args.results)
    gold_path = Path(args.gold)
    out_path = Path(args.output)

    if not results_path.exists():
        raise SystemExit(f"Results not found: {results_path}")
    if not gold_path.exists():
        raise SystemExit(f"Ground truth not found: {gold_path}")

    results = load_csv(results_path)
    gold = load_csv(gold_path)

    # Current benchmark evaluator output schema:
    # scenario_id, requirement_id, predicted_status
    pred = {}
    for row in results:
        scenario_id = row.get("scenario_id", "").strip()
        requirement_id = row.get("requirement_id", "").strip()
        predicted = row.get("predicted_status", "")
        if scenario_id and requirement_id and predicted:
            pred[(scenario_id, requirement_id)] = norm(predicted)

    gold_map = {}
    incomplete = []

    for row in gold:
        scenario_id = row.get("scenario_id", "").strip()
        requirement_id = row.get("requirement_id", "").strip()
        expected = norm(row.get("expected_status"))
        reviewed = norm(row.get("reviewed"))

        if not scenario_id or not requirement_id:
            continue

        if expected not in VALID:
            incomplete.append(
                (scenario_id, requirement_id, "invalid/missing expected_status")
            )
            continue

        if reviewed not in {"YES", "TRUE", "1"}:
            incomplete.append(
                (scenario_id, requirement_id, "not reviewed")
            )
            continue

        gold_map[(scenario_id, requirement_id)] = expected

    comparable = []
    missing_prediction = []

    for key, expected in gold_map.items():
        if key not in pred:
            missing_prediction.append(key)
        elif expected != "UNCERTAIN":
            comparable.append((expected, pred[key]))

    cm = Counter((expected, predicted) for expected, predicted in comparable)
    correct = sum(expected == predicted for expected, predicted in comparable)
    total = len(comparable)
    accuracy = correct / total if total else None

    per_class = {}
    for cls in ["PASS", "FAIL", "NOT_APPLICABLE"]:
        tp = sum(1 for expected, predicted in comparable
                 if expected == cls and predicted == cls)
        fp = sum(1 for expected, predicted in comparable
                 if expected != cls and predicted == cls)
        fn = sum(1 for expected, predicted in comparable
                 if expected == cls and predicted != cls)

        precision = tp / (tp + fp) if tp + fp else None
        recall = tp / (tp + fn) if tp + fn else None
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision is not None
            and recall is not None
            and precision + recall
            else None
        )

        per_class[cls] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": sum(1 for expected, _ in comparable if expected == cls),
        }

    summary = {
        "gold_rows": len(gold),
        "reviewed_valid_gold_rows": len(gold_map),
        "comparable_rows": total,
        "accuracy": accuracy,
        "confusion_matrix": {
            f"{expected}->{predicted}": count
            for (expected, predicted), count in sorted(cm.items())
        },
        "per_class": per_class,
        "incomplete_gold_rows": len(incomplete),
        "missing_predictions": len(missing_prediction),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
