from pathlib import Path
import argparse
import csv
import json
import sys

BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from app.engine import assess
from app.loaders import load_requirements, load_system

DEFAULT_SYSTEM_DIR = BASE / "data" / "systems" / "eu_ai_act_benchmark"
DEFAULT_REQUIREMENTS = BASE / "data" / "requirements" / "eu_ai_act_core.yaml"
DEFAULT_OUTPUT = BASE / "data" / "results" / "benchmark_predictions.csv"
DEFAULT_SUMMARY = BASE / "data" / "results" / "benchmark_prediction_summary.json"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--systems", default=str(DEFAULT_SYSTEM_DIR))
    parser.add_argument("--requirements", default=str(DEFAULT_REQUIREMENTS))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY))
    args = parser.parse_args()

    system_dir = Path(args.systems)
    requirements_path = Path(args.requirements)
    output_path = Path(args.output)
    summary_path = Path(args.summary)

    if not system_dir.exists():
        raise SystemExit(f"Benchmark system directory not found: {system_dir}")

    requirements = load_requirements(requirements_path)
    systems = sorted(system_dir.glob("ai-act-benchmark-*.yaml"))
    if not systems:
        raise SystemExit(f"No benchmark scenario YAML files found in {system_dir}")

    rows = []

    for system_path in systems:
        system = load_system(system_path)
        report = assess(system, requirements)

        for result in report.results:
            if result.status == "PASS" and result.explanation.startswith(
                "Requirement is not applicable"
            ):
                predicted = "NOT_APPLICABLE"
            else:
                predicted = result.status

            rows.append({
                "scenario_id": system.id,
                "requirement_id": result.requirement_id,
                "predicted_status": predicted,
            })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["scenario_id", "requirement_id", "predicted_status"],
        )
        writer.writeheader()
        writer.writerows(rows)

    counts = {}
    for row in rows:
        counts[row["predicted_status"]] = counts.get(row["predicted_status"], 0) + 1

    summary = {
        "scenarios": len(systems),
        "requirements": len(requirements),
        "requirement_predictions": len(rows),
        "predicted_status_counts": counts,
    }

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"Predictions: {output_path}")
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    main()
