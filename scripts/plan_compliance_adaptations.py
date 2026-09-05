from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parents[1]
DEFAULT_TRACE = BASE / "data" / "results" / "compliance_assessment_trace.jsonl"
DEFAULT_RESULTS = BASE / "data" / "results"

ACTION_CATALOG: dict[str, list[dict[str, Any]]] = {
    "EUAI-R9-01": [
        {"action_id": "ADD_RISK_MANAGEMENT_SYSTEM", "title": "Add documented risk-management system", "objective": "establish and maintain risk management", "impact": 3},
        {"action_id": "ADD_RISK_REVIEW_CYCLE", "title": "Add continuous risk review and update cycle", "objective": "support lifecycle risk management", "impact": 2},
    ],
    "EUAI-R10-01": [
        {"action_id": "ADD_DATA_GOVERNANCE_CONTROLS", "title": "Add data governance and quality controls", "objective": "govern training/validation/test data", "impact": 3},
        {"action_id": "ADD_DATA_DOCUMENTATION", "title": "Add data provenance and documentation controls", "objective": "make data practices demonstrable", "impact": 2},
    ],
    "EUAI-R12-01": [
        {"action_id": "ADD_AUTOMATIC_EVENT_LOGGING", "title": "Add automatic event logging", "objective": "record relevant system events", "impact": 2},
        {"action_id": "ADD_LOG_RETENTION_CONTROL", "title": "Add retention and access controls for logs", "objective": "preserve usable audit evidence", "impact": 2},
    ],
    "EUAI-R13-01": [
        {"action_id": "ADD_TRANSPARENCY_INFORMATION", "title": "Add required transparency information", "objective": "make system operation understandable to deployers/users", "impact": 2},
        {"action_id": "ADD_OUTPUT_INTERPRETATION_SUPPORT", "title": "Add output interpretation support", "objective": "support appropriate understanding of system output", "impact": 2},
    ],
    "EUAI-R14-01": [
        {"action_id": "ADD_HUMAN_OVERSIGHT_CONTROL", "title": "Add effective human oversight control", "objective": "enable human oversight during operation", "impact": 3},
        {"action_id": "ADD_OVERSIGHT_MONITORING", "title": "Add monitoring and bias-awareness support for overseers", "objective": "support effective oversight", "impact": 2},
    ],
    "EUAI-R14-02": [
        {"action_id": "ADD_OVERRIDE_CONTROL", "title": "Add human reject/override control", "objective": "allow overseer intervention on outputs", "impact": 2},
        {"action_id": "ADD_SAFE_STOP_CONTROL", "title": "Add safe-stop/interruption control", "objective": "allow system operation to be interrupted safely", "impact": 3},
    ],
    "EUAI-R15-01": [
        {"action_id": "ADD_ACCURACY_ROBUSTNESS_CONTROLS", "title": "Add accuracy and robustness controls", "objective": "improve documented technical performance", "impact": 3},
        {"action_id": "ADD_CYBERSECURITY_CONTROLS", "title": "Add cybersecurity controls", "objective": "address relevant cybersecurity risks", "impact": 3},
    ],
    "EUAI-R50-01": [
        {"action_id": "ADD_AI_INTERACTION_NOTICE", "title": "Add direct-AI-interaction notice", "objective": "inform people when they interact directly with AI", "impact": 1},
    ],
}


def _load_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _candidate_actions(requirement_id: str, explanation: str) -> list[dict[str, Any]]:
    actions = ACTION_CATALOG.get(requirement_id, [])
    ranked: list[dict[str, Any]] = []
    text = explanation.lower()
    for action in actions:
        score = 1.0 / (1 + action["impact"])
        if any(token in text for token in ("log", "logging")) and "LOG" in action["action_id"]:
            score += 0.5
        if any(token in text for token in ("override", "reject")) and "OVERRIDE" in action["action_id"]:
            score += 0.7
        if "stop" in text and "SAFE_STOP" in action["action_id"]:
            score += 0.7
        ranked.append({**action, "priority_score": round(score, 3)})
    ranked.sort(key=lambda x: (-x["priority_score"], x["impact"], x["action_id"]))
    return ranked


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate proposal-only compliance adaptation plans from failed ACER checks.")
    parser.add_argument("--trace", default=str(DEFAULT_TRACE))
    parser.add_argument("--results", default=str(DEFAULT_RESULTS))
    args = parser.parse_args()

    trace_path = Path(args.trace)
    results_dir = Path(args.results)
    if not trace_path.exists():
        raise SystemExit(f"Assessment trace not found: {trace_path}")

    rows = _load_rows(trace_path)
    failed = [r for r in rows if r.get("status") == "FAIL"]
    plans: list[dict[str, Any]] = []
    for row in failed:
        req_id = row["requirement_id"]
        actions = _candidate_actions(req_id, row.get("explanation", ""))
        plans.append({
            "plan_id": f"PLAN-{row['system_id']}-{req_id}",
            "system_id": row["system_id"],
            "system_version": row.get("system_version"),
            "requirement_id": req_id,
            "requirement_title": row.get("requirement_title"),
            "regulation": row.get("regulation"),
            "provision": row.get("provision"),
            "violation": {
                "status": row["status"],
                "explanation": row.get("explanation"),
                "evidence": json.loads(row.get("evidence", "[]")),
                "trace_id": row.get("trace_id"),
            },
            "candidate_adaptations": actions,
            "selection_policy": "rank lower-impact actions first, with explanation keyword boosts; require verification before application",
            "execution_status": "PROPOSED_NOT_APPLIED",
            "human_intervention_required": True,
            "verification_required_after_adaptation": True,
        })

    results_dir.mkdir(parents=True, exist_ok=True)
    out = results_dir / "compliance_adaptation_plans.json"
    out.write_text(json.dumps(plans, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = {
        "failed_checks": len(failed),
        "adaptation_plans": len(plans),
        "systems_with_violations": len({p["system_id"] for p in plans}),
        "requirements_with_violations": len({p["requirement_id"] for p in plans}),
        "candidate_adaptations_total": sum(len(p["candidate_adaptations"]) for p in plans),
        "execution_status": "PROPOSED_NOT_APPLIED",
        "human_intervention_required": True,
        "verification_required_after_adaptation": True,
        "method_note": "Rule-based diagnostic/adaptation planning over deterministic assessment failures. Candidate actions are engineering proposals, not legal advice or proof of remediation effectiveness.",
        "file": str(out),
    }
    summary_path = results_dir / "compliance_adaptation_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
