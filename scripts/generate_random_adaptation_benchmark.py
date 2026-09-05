from __future__ import annotations

import argparse
import random
from pathlib import Path
import yaml

BASE = Path(__file__).resolve().parents[1]
DEFAULT_OUT = BASE / "data" / "systems" / "eu_ai_act_adaptation_randomized"
REQS = [
    "EUAI-R9-01", "EUAI-R10-01", "EUAI-R12-01", "EUAI-R13-01",
    "EUAI-R14-01", "EUAI-R14-02", "EUAI-R15-01", "EUAI-R50-01",
]
STRUCTURED = [
    ["EUAI-R13-01", "EUAI-R50-01"],
    ["EUAI-R14-01", "EUAI-R14-02"],
    ["EUAI-R9-01", "EUAI-R10-01"],
    ["EUAI-R12-01", "EUAI-R15-01"],
    ["EUAI-R9-01", "EUAI-R10-01", "EUAI-R13-01", "EUAI-R50-01"],
    ["EUAI-R14-01", "EUAI-R14-02", "EUAI-R13-01", "EUAI-R50-01"],
    ["EUAI-R9-01", "EUAI-R10-01", "EUAI-R12-01", "EUAI-R15-01"],
    REQS[:],
    ["EUAI-R9-01", "EUAI-R13-01", "EUAI-R50-01"],
    ["EUAI-R12-01", "EUAI-R14-01", "EUAI-R14-02"],
    ["EUAI-R9-01", "EUAI-R15-01", "EUAI-R50-01"],
    ["EUAI-R10-01", "EUAI-R12-01", "EUAI-R14-01", "EUAI-R14-02"],
]


def normalize_failure_set(items: list[str]) -> list[str]:
    s = set(items)
    # Under the current curated ACER rules, EUAI-R14-01 is a required-component
    # check for human_review, while EUAI-R14-02 is a required human_review ->
    # final_decision flow. Therefore a model with no human_review component
    # necessarily fails both checks. Preserve independent R14-02 failures when
    # R14-01 is otherwise satisfied, but make the declared failure set match the
    # executable semantics of the current assessor.
    if "EUAI-R14-01" in s:
        s.add("EUAI-R14-02")
    return [r for r in REQS if r in s]


def system_yaml(system_id: str, failing: list[str]) -> dict:
    f = set(failing)
    comps = [
        {"id": "ai_model", "type": "ai_model", "properties": {}},
        {"id": "candidate_ui", "type": "user_interface", "properties": {}},
        {"id": "final_decision", "type": "final_decision", "properties": {"logging_enabled": "EUAI-R12-01" not in f}},
    ]
    if "EUAI-R9-01" not in f:
        comps.append({"id": "risk_management", "type": "risk_management", "properties": {}})
    if "EUAI-R10-01" not in f:
        comps.append({"id": "data_governance", "type": "data_governance", "properties": {}})
    if "EUAI-R13-01" not in f:
        comps.append({"id": "transparency_mechanism", "type": "transparency_mechanism", "properties": {}})
    if "EUAI-R14-01" not in f:
        comps.append({"id": "human_review", "type": "human_review", "properties": {"monitoring": True, "understands_output": True}})
    if "EUAI-R15-01" not in f:
        comps.append({"id": "performance_monitoring", "type": "performance_monitoring", "properties": {}})

    flows = []
    # R14-02 is controlled directly by this flow; R14-01 can be independently PASS/FAIL.
    if "EUAI-R14-02" not in f:
        if any(c["type"] == "human_review" for c in comps):
            flows.append({"source": "human_review", "target": "final_decision", "data": "decision_intervention"})

    return {
        "id": system_id,
        "name": f"ACER randomized adaptation stress - {system_id}",
        "domain": "synthetic randomized adaptation stress benchmark",
        "version": "1.0",
        "components": comps,
        "data": [{"id": "training_data", "type": "dataset"}],
        "flows": flows,
        "attributes": {
            "system_is_high_risk": True,
            "uses_training_data": True,
            "direct_ai_interaction": True,
            "transparency_notice": "EUAI-R50-01" not in f,
        },
        "objectives": {},
    }


def build_sets(seed: int, count: int) -> list[list[str]]:
    rng = random.Random(seed)
    sets: list[list[str]] = []
    # 20 structured cases preserve interpretable interaction patterns.
    for i in range(20):
        base = STRUCTURED[i % len(STRUCTURED)]
        if i >= len(STRUCTURED):
            # Add one or two random requirements while retaining the structured core.
            extras = [r for r in REQS if r not in base]
            base = base + rng.sample(extras, k=min(len(extras), 1 + (i % 2)))
        sets.append(normalize_failure_set(base))

    # 60 mixed-size random interaction cases.
    for _ in range(60):
        k = rng.choices([2, 3, 4, 5, 6], weights=[15, 20, 20, 15, 10])[0]
        chosen = rng.sample(REQS, k=k)
        # Encourage coupled human-oversight cases, but preserve independent R14-02 cases too.
        if "EUAI-R14-01" in chosen and "EUAI-R14-02" not in chosen and rng.random() < 0.7:
            chosen.append("EUAI-R14-02")
        sets.append(normalize_failure_set(chosen))

    # 20 dense cases, including several all-eight cases.
    for i in range(20):
        if i < 5:
            chosen = REQS[:]
        else:
            k = rng.choice([6, 7, 8])
            chosen = rng.sample(REQS, k=k)
            if rng.random() < 0.75 and "EUAI-R14-01" in chosen and "EUAI-R14-02" not in chosen:
                chosen.append("EUAI-R14-02")
        sets.append(normalize_failure_set(chosen))

    # Make deterministic and unique; fill to requested count if duplicates occur.
    unique = []
    seen = set()
    for s in sets:
        key = tuple(s)
        if key not in seen:
            seen.add(key); unique.append(s)
    while len(unique) < count:
        k = rng.randint(2, 8)
        s = normalize_failure_set(rng.sample(REQS, k=k))
        key = tuple(s)
        if key not in seen:
            seen.add(key); unique.append(s)
    return unique[:count]


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate a deterministic randomized ACER adaptation stress benchmark.")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--count", type=int, default=100)
    ap.add_argument("--seed", type=int, default=20260904)
    args = ap.parse_args()
    if args.count < 20:
        raise SystemExit("--count must be at least 20")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for p in out.glob("ai-act-random-stress-*.yaml"):
        p.unlink()

    failure_sets = build_sets(args.seed, args.count)
    total = 0
    scenarios = []
    for idx, failing in enumerate(failure_sets, start=1):
        sid = f"ai-act-random-stress-{idx:03d}"
        (out / f"{sid}.yaml").write_text(
            yaml.safe_dump(system_yaml(sid, failing), sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        total += len(failing)
        scenarios.append({"scenario_id": sid, "failing_requirements": failing, "initial_failure_count": len(failing)})

    manifest = {
        "benchmark": "ACER randomized adaptation interaction stress benchmark",
        "systems": args.count,
        "seed": args.seed,
        "requirements": REQS,
        "expected_total_initial_failures": total,
        "scenarios": scenarios,
        "design": {
            "structured_interaction_cases": 20,
            "mixed_random_cases": 60,
            "dense_random_cases": 20,
            "multi_violation": True,
            "bundled_repair_opportunities": True,
            "paired_human_oversight_cases": True,
        },
        "grounding": "Same 8 curated ACER requirements and deterministic assessor as the primary benchmark.",
    }
    (out / "MANIFEST.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(yaml.safe_dump({k: v for k, v in manifest.items() if k != "scenarios"}, sort_keys=False, allow_unicode=True))


if __name__ == "__main__":
    main()
