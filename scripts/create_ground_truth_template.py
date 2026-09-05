import csv
from pathlib import Path
import argparse

BASE = Path(__file__).resolve().parents[1]

RESULTS = BASE / "data" / "results" / "eu_ai_act_requirement_results.csv"
OUT = BASE / "data" / "ground_truth" / "eu_ai_act_ground_truth.csv"


def main():
    parser = argparse.ArgumentParser(
        description="Create a blank independent-ground-truth worksheet from ACER experiment outputs."
    )
    parser.add_argument("--input", default=str(RESULTS))
    parser.add_argument("--output", default=str(OUT))
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise SystemExit(f"Input results file not found: {input_path}")

    with input_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise SystemExit("Input results file is empty.")

    required = {"system_id", "requirement_id"}
    missing = required - set(rows[0].keys())
    if missing:
        raise SystemExit(
            f"Input CSV is missing required columns: {sorted(missing)}. "
            f"Found: {list(rows[0].keys())}"
        )

    fieldnames = [
        "scenario_id",
        "requirement_id",
        "expected_status",
        "rationale",
        "annotator",
        "reviewed",
    ]

    seen = set()
    out_rows = []

    for row in rows:
        scenario_id = row["system_id"].strip()
        requirement_id = row["requirement_id"].strip()

        if not scenario_id or not requirement_id:
            continue

        key = (scenario_id, requirement_id)
        if key in seen:
            continue

        seen.add(key)
        out_rows.append(
            {
                "scenario_id": scenario_id,
                "requirement_id": requirement_id,
                "expected_status": "",
                "rationale": "",
                "annotator": "",
                "reviewed": "NO",
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Created {len(out_rows)} independent-label rows: {output_path}")
    print("Fill expected_status and rationale independently of ACER before evaluation.")


if __name__ == "__main__":
    main()
