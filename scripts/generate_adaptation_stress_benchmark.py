from __future__ import annotations

import argparse
from pathlib import Path
import yaml

BASE = Path(__file__).resolve().parents[1]
DEFAULT_OUT = BASE / "data" / "systems" / "eu_ai_act_adaptation_stress"

SYSTEMS = [
    ("dual_transparency", ["EUAI-R13-01", "EUAI-R50-01"]),
    ("dual_human_oversight", ["EUAI-R14-01", "EUAI-R14-02"]),
    ("dual_risk_data", ["EUAI-R9-01", "EUAI-R10-01"]),
    ("dual_logging_performance", ["EUAI-R12-01", "EUAI-R15-01"]),
    ("four_controls", ["EUAI-R9-01", "EUAI-R10-01", "EUAI-R13-01", "EUAI-R50-01"]),
    ("human_and_transparency", ["EUAI-R14-01", "EUAI-R14-02", "EUAI-R13-01", "EUAI-R50-01"]),
    ("operational_bundle", ["EUAI-R9-01", "EUAI-R10-01", "EUAI-R12-01", "EUAI-R15-01"]),
    ("all_eight", [
        "EUAI-R9-01", "EUAI-R10-01", "EUAI-R12-01", "EUAI-R13-01",
        "EUAI-R14-01", "EUAI-R14-02", "EUAI-R15-01", "EUAI-R50-01",
    ]),
    ("three_way_transparency_risk", ["EUAI-R9-01", "EUAI-R13-01", "EUAI-R50-01"]),
    ("three_way_oversight_ops", ["EUAI-R12-01", "EUAI-R14-01", "EUAI-R14-02"]),
    ("mixed_risk_perf_notice", ["EUAI-R9-01", "EUAI-R15-01", "EUAI-R50-01"]),
    ("mixed_data_log_human", ["EUAI-R10-01", "EUAI-R12-01", "EUAI-R14-01", "EUAI-R14-02"]),
]


def system_yaml(system_id: str, failing_requirements: list[str]) -> dict:
    failing = set(failing_requirements)
    components = [
        {"id": "ai_model", "type": "ai_model", "properties": {}},
        {"id": "candidate_ui", "type": "user_interface", "properties": {}},
    ]
    if "EUAI-R12-01" in failing:
        components.append({"id": "final_decision", "type": "final_decision", "properties": {"logging_enabled": False}})
    else:
        components.append({"id": "final_decision", "type": "final_decision", "properties": {"logging_enabled": True}})
    if "EUAI-R9-01" not in failing:
        components.append({"id": "risk_management", "type": "risk_management", "properties": {}})
    if "EUAI-R10-01" not in failing:
        components.append({"id": "data_governance", "type": "data_governance", "properties": {}})
    if "EUAI-R13-01" not in failing:
        components.append({"id": "transparency_mechanism", "type": "transparency_mechanism", "properties": {}})
    if "EUAI-R14-01" not in failing:
        components.append({"id": "human_review", "type": "human_review", "properties": {"monitoring": True, "understands_output": True}})
    if "EUAI-R15-01" not in failing:
        components.append({"id": "performance_monitoring", "type": "performance_monitoring", "properties": {}})
    flows = []
    if "EUAI-R14-01" not in failing and "EUAI-R14-02" not in failing:
        flows.append({"source": "human_review", "target": "final_decision", "data": "decision_intervention"})
    return {
        "id": f"ai-act-stress-{system_id}",
        "name": f"ACER adaptation stress - {system_id}",
        "domain": "synthetic adaptation stress benchmark",
        "version": "1.0",
        "components": components,
        "data": [{"id": "training_data", "type": "dataset"}],
        "flows": flows,
        "attributes": {
            "system_is_high_risk": True,
            "uses_training_data": True,
            "direct_ai_interaction": True,
            "transparency_notice": "EUAI-R50-01" not in failing,
        },
        "objectives": {},
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate the ACER multi-objective adaptation stress benchmark.")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    # Remove only previously generated stress scenarios; leave all other datasets untouched.
    for p in out.glob("ai-act-stress-*.yaml"):
        p.unlink()
    for suffix, failing_requirements in SYSTEMS:
        path = out / f"ai-act-stress-{suffix}.yaml"
        path.write_text(
            yaml.safe_dump(system_yaml(suffix, failing_requirements), sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
    manifest = {
        "benchmark": "ACER adaptation interaction stress benchmark",
        "systems": len(SYSTEMS),
        "scenario_ids": [f"ai-act-stress-{s}" for s, _ in SYSTEMS],
        "designed_interactions": [
            "multi-violation systems",
            "bundled adaptations that repair multiple requirements simultaneously",
            "shared human-oversight intervention structures",
        ],
        "grounding": "Uses the same 8 curated ACER requirements and deterministic assessor as the primary benchmark.",
    }
    (out / "MANIFEST.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True))


if __name__ == "__main__":
    main()
