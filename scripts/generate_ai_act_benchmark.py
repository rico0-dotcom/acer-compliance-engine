from pathlib import Path
import argparse
import csv
import yaml

BASE = Path(__file__).resolve().parents[1]

REQUIREMENTS = [
    "EUAI-R9-01", "EUAI-R10-01", "EUAI-R12-01", "EUAI-R13-01",
    "EUAI-R14-01", "EUAI-R14-02", "EUAI-R15-01", "EUAI-R50-01",
]

BASE_COMPONENTS = [
    {"id": "candidate_portal", "type": "user_interface", "properties": {}},
    {"id": "resume_llm", "type": "generative_ai",
     "properties": {"purpose": "resume_information_extraction"}},
    {"id": "scoring_model", "type": "decision_engine", "properties": {}},
    {"id": "final_decision", "type": "final_decision",
     "properties": {"logging_enabled": True}},
    {"id": "hr_dashboard", "type": "human_interface", "properties": {}},
    {"id": "risk_management", "type": "risk_management", "properties": {}},
    {"id": "data_governance", "type": "data_governance", "properties": {}},
    {"id": "transparency_mechanism", "type": "transparency_mechanism", "properties": {}},
    {"id": "human_review", "type": "human_review",
     "properties": {"can_override": True, "can_stop": True}},
    {"id": "performance_monitoring", "type": "performance_monitoring", "properties": {}},
]

BASE_FLOWS = [
    {"source": "candidate_portal", "target": "resume_llm", "data": "candidate_data"},
    {"source": "resume_llm", "target": "scoring_model", "data": "candidate_data"},
    {"source": "scoring_model", "target": "human_review", "data": "candidate_data"},
    {"source": "human_review", "target": "final_decision", "data": "candidate_data"},
    {"source": "final_decision", "target": "hr_dashboard", "data": "candidate_data"},
]


def build_scenario(case):
    components = [
        {"id": x["id"], "type": x["type"], "properties": dict(x.get("properties", {}))}
        for x in BASE_COMPONENTS
    ]
    flows = [dict(x) for x in BASE_FLOWS]

    attributes = {
        "system_is_high_risk": bool(case["high_risk"]),
        "uses_training_data": bool(case["uses_training_data"]),
        "direct_ai_interaction": bool(case["direct_ai_interaction"]),
        "transparency_notice": True,
    }

    missing = set(case.get("missing", []))

    # Remove only the component associated with a component-level defect.
    component_types = {
        "risk_management": "risk_management",
        "data_governance": "data_governance",
        "transparency_mechanism": "transparency_mechanism",
        "human_review": "human_review",
        "performance_monitoring": "performance_monitoring",
    }

    remove_types = {
        component_types[m]
        for m in missing
        if m in component_types
    }
    components = [c for c in components if c["type"] not in remove_types]

    # Logging is a property defect: do NOT remove final_decision because
    # Article 12 evaluates its logging configuration.
    if "logging" in missing:
        for component in components:
            if component["type"] == "final_decision":
                component["properties"]["logging_enabled"] = False

    # If human review is absent, its associated flows cannot exist.
    if "human_review" in missing:
        flows = [
            f for f in flows
            if f["source"] != "human_review" and f["target"] != "human_review"
        ]

    # Explicit flow defect: retain the human_review component but remove its
    # connection to final_decision.
    if "human_intervention_flow" in missing:
        flows = [
            f for f in flows
            if not (f["source"] == "human_review" and f["target"] == "final_decision")
        ]

    if "article50_notice" in missing:
        attributes["transparency_notice"] = False

    # Applicability cases.
    if not case["high_risk"]:
        high_risk_types = {
            "risk_management", "data_governance", "transparency_mechanism",
            "human_review", "performance_monitoring",
        }
        components = [c for c in components if c["type"] not in high_risk_types]
        flows = [
            f for f in flows
            if f["source"] != "human_review" and f["target"] != "human_review"
        ]

    if not case["uses_training_data"]:
        components = [c for c in components if c["type"] != "data_governance"]

    return {
        "id": f"ai-act-benchmark-{case['id']}",
        "name": f"EU AI Act Benchmark {case['id']}",
        "domain": "recruitment",
        "version": "1.0",
        "components": components,
        "data": [{"id": "candidate_data", "classification": "personal_data"}],
        "flows": flows,
        "attributes": attributes,
        "objectives": {"compliance": 1.0, "performance": 0.8, "cost": 0.7},
    }


def independent_labels(case):
    labels = {rid: "PASS" for rid in REQUIREMENTS}
    missing = set(case.get("missing", []))

    if not case["high_risk"]:
        for rid in REQUIREMENTS:
            if rid != "EUAI-R50-01":
                labels[rid] = "NOT_APPLICABLE"

    if case["high_risk"] and not case["uses_training_data"]:
        labels["EUAI-R10-01"] = "NOT_APPLICABLE"

    if not case["direct_ai_interaction"]:
        labels["EUAI-R50-01"] = "NOT_APPLICABLE"

    mapping = {
        "risk_management": "EUAI-R9-01",
        "data_governance": "EUAI-R10-01",
        "logging": "EUAI-R12-01",
        "transparency_mechanism": "EUAI-R13-01",
        "human_review": "EUAI-R14-01",
        "human_intervention_flow": "EUAI-R14-02",
        "performance_monitoring": "EUAI-R15-01",
        "article50_notice": "EUAI-R50-01",
    }

    for defect in missing:
        rid = mapping[defect]
        if labels[rid] != "NOT_APPLICABLE":
            labels[rid] = "FAIL"

    # R14-02 requires a human_review -> final_decision flow.
    # If human_review itself is absent, that flow necessarily cannot exist.
    if "human_review" in missing and labels["EUAI-R14-02"] != "NOT_APPLICABLE":
        labels["EUAI-R14-02"] = "FAIL"

    return labels


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--spec",
        default=str(BASE / "data" / "ground_truth" / "eu_ai_act_benchmark_spec.yaml"),
    )
    parser.add_argument(
        "--out",
        default=str(BASE / "data" / "systems" / "eu_ai_act_benchmark"),
    )
    parser.add_argument(
        "--ground-truth",
        default=str(BASE / "data" / "ground_truth" / "eu_ai_act_ground_truth.csv"),
    )
    args = parser.parse_args()

    spec = yaml.safe_load(Path(args.spec).read_text(encoding="utf-8"))
    cases = spec.get("cases", [])
    if not cases:
        raise SystemExit("Benchmark specification contains no cases.")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    gt_path = Path(args.ground_truth)
    gt_path.parent.mkdir(parents=True, exist_ok=True)

    labels = []
    manifest = []

    for case in cases:
        scenario = build_scenario(case)
        (out / f"{scenario['id']}.yaml").write_text(
            yaml.safe_dump(scenario, sort_keys=False),
            encoding="utf-8",
        )

        manifest.append({
            "system_id": scenario["id"],
            "type": case["type"],
        })

        expected = independent_labels(case)
        for rid in REQUIREMENTS:
            labels.append({
                "scenario_id": scenario["id"],
                "requirement_id": rid,
                "expected_status": expected[rid],
                "rationale": (
                    f"Spec-defined benchmark case: type={case['type']}; "
                    f"high_risk={case['high_risk']}; "
                    f"uses_training_data={case['uses_training_data']}; "
                    f"direct_ai_interaction={case['direct_ai_interaction']}; "
                    f"missing={','.join(case.get('missing', [])) or 'none'}"
                ),
                "annotator": "benchmark_author",
                "reviewed": "YES",
            })

    with gt_path.open("w", encoding="utf-8", newline="") as f:
        fields = ["scenario_id", "requirement_id", "expected_status",
                  "rationale", "annotator", "reviewed"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(labels)

    (out / "manifest.yaml").write_text(
        yaml.safe_dump({
            "source": "data/ground_truth/eu_ai_act_benchmark_spec.yaml",
            "count": len(cases),
            "requirements": len(REQUIREMENTS),
            "ground_truth_rows": len(labels),
            "cases": manifest,
        }, sort_keys=False),
        encoding="utf-8",
    )

    print(f"Generated {len(cases)} benchmark scenarios in {out}")
    print(f"Created {len(labels)} independent benchmark labels in {gt_path}")


if __name__ == "__main__":
    main()
