import argparse
import csv
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = DATA / "results"

TRACE = RESULTS / "compliance_assessment_trace.csv"
PLANS = RESULTS / "compliance_adaptation_plans.json"
OUT = RESULTS / "compliance_adaptation_execution.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def flatten_dicts(obj: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from flatten_dicts(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from flatten_dicts(v)


def find_value(d: Dict[str, Any], names: Iterable[str]) -> Optional[Any]:
    wanted = {n.lower() for n in names}
    for k, v in d.items():
        if str(k).lower() in wanted:
            return v
    return None


def load_failed_checks() -> List[Dict[str, str]]:
    with TRACE.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    failed = [r for r in rows if str(r.get("status", "")).upper() == "FAIL"]
    return failed


def load_plans() -> List[Dict[str, Any]]:
    raw = load_json(PLANS)
    candidates: List[Dict[str, Any]] = []
    for d in flatten_dicts(raw):
        system_id = find_value(d, ["system_id", "system"])
        requirement_id = find_value(d, ["requirement_id", "requirement", "matched_requirement_id"])
        if system_id and requirement_id:
            candidates.append(d)
    return candidates


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False).lower()
    return str(value).lower()


def choose_candidate(plan_dicts: List[Dict[str, Any]], system_id: str, requirement_id: str) -> Optional[Dict[str, Any]]:
    matching = []
    for d in plan_dicts:
        sid = find_value(d, ["system_id", "system"])
        rid = find_value(d, ["requirement_id", "requirement", "matched_requirement_id"])
        if sid == system_id and rid == requirement_id:
            matching.append(d)
    if not matching:
        return None

    def score(d: Dict[str, Any]) -> float:
        s = 0.0
        rank = find_value(d, ["rank", "priority_rank", "candidate_rank"])
        if isinstance(rank, int):
            s += max(0, 100 - rank)
        elif isinstance(rank, str) and rank.isdigit():
            s += max(0, 100 - int(rank))
        status = normalize_text(find_value(d, ["status", "execution_status", "approval_status"]))
        if "proposed" in status:
            s += 1
        return s

    return max(matching, key=score)


def infer_action(d: Optional[Dict[str, Any]], requirement_id: str) -> Dict[str, Any]:
    if d:
        action = find_value(d, ["action", "adaptation_action", "candidate_action", "description", "remediation"])
        target = find_value(d, ["target", "target_component", "target_field"])
        postcondition = find_value(d, ["postcondition", "expected_effect", "expected_outcome"])
    else:
        action = target = postcondition = None

    defaults = {
        "EUAI-R9-01": "Add or strengthen a documented, continuously maintained risk-management control and evidence trail.",
        "EUAI-R10-01": "Add or strengthen data-governance controls, including provenance, quality, suitability, and documented management evidence.",
        "EUAI-R12-01": "Enable automatic event logging for relevant events and retain logs as auditable evidence.",
        "EUAI-R13-01": "Add system transparency information and user-facing instructions appropriate to the AI system.",
        "EUAI-R14-01": "Add effective human-oversight controls, including monitoring, understanding, and intervention capability.",
        "EUAI-R14-02": "Add explicit human override/rejection and safe-stop/interruption capability.",
        "EUAI-R15-01": "Add or strengthen accuracy, robustness, and cybersecurity controls with verification evidence.",
        "EUAI-R50-01": "Add a direct-AI-interaction disclosure control at the point of interaction.",
    }
    return {
        "action": action or defaults.get(requirement_id, f"Apply an engineered remediation for {requirement_id}."),
        "target": target,
        "postcondition": postcondition or f"Verification must show PASS for {requirement_id} after adaptation.",
    }


def simulate_and_verify(failed: List[Dict[str, str]], plan_dicts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Controlled prototype execution: builds isolated adaptation overlays instead of mutating source models.
    Verification is state-based: an approved overlay satisfies only the requirement instance it explicitly targets.
    A production implementation should replace this state transition with actual model/component mutation plus
    the existing deterministic assessor.
    """
    overlays: List[Dict[str, Any]] = []
    verification: List[Dict[str, Any]] = []

    for row in failed:
        sid = row.get("system_id", "")
        rid = row.get("requirement_id", "")
        plan = choose_candidate(plan_dicts, sid, rid)
        action = infer_action(plan, rid)
        overlay = {
            "system_id": sid,
            "requirement_id": rid,
            "change_type": "CONTROL_OVERLAY",
            "action": action["action"],
            "target": action["target"],
            "postcondition": action["postcondition"],
            "approval_required": True,
            "verification_required": True,
        }
        overlays.append(overlay)
        verification.append({
            "system_id": sid,
            "requirement_id": rid,
            "baseline_status": "FAIL",
            "selected_adaptation": action["action"],
            "simulated_post_status": "PASS",
            "verification_method": "controlled_state_transition",
            "verification_note": "PASS is a prototype postcondition check on an isolated overlay; it is not evidence that the real system has been remediated.",
        })

    return {"overlays": overlays, "verification": verification}


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute approved compliance adaptations on isolated overlays and verify postconditions.")
    parser.add_argument("--approve-all", action="store_true", help="Approve the top-ranked proposal for each failed check. Default is proposal-only.")
    args = parser.parse_args()

    if not TRACE.exists() or not PLANS.exists():
        raise SystemExit("Required inputs are missing. Run the compliance assessment and adaptation planning layers first.")

    failed = load_failed_checks()
    plan_dicts = load_plans()
    unique_pairs = {(r.get("system_id", ""), r.get("requirement_id", "")) for r in failed}

    if not args.approve_all:
        result = {
            "execution_status": "AWAITING_HUMAN_APPROVAL",
            "failed_checks": len(failed),
            "adaptation_targets": len(unique_pairs),
            "approved": False,
            "applied_changes": 0,
            "post_verification": 0,
            "rollback_required": False,
            "note": "No source system model was modified. Re-run with --approve-all only for the isolated prototype execution/verification path.",
        }
        OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    result = simulate_and_verify(failed, plan_dicts)
    final = {
        "execution_status": "SIMULATED_APPROVED_AND_VERIFIED",
        "failed_checks": len(failed),
        "applied_changes": len(result["overlays"]),
        "post_verification": len(result["verification"]),
        "post_status_counts": {
            "PASS": sum(1 for x in result["verification"] if x["simulated_post_status"] == "PASS"),
            "FAIL": sum(1 for x in result["verification"] if x["simulated_post_status"] == "FAIL"),
        },
        "human_approval": "APPROVED_ALL_FOR_PROTOTYPE",
        "source_models_modified": False,
        "rollback_required": any(x["simulated_post_status"] != "PASS" for x in result["verification"]),
        "overlays": result["overlays"],
        "verification": result["verification"],
        "method_note": "This is a controlled execution prototype using isolated control overlays. A simulated PASS is not evidence of real-world remediation or legal compliance; production execution must mutate a system model, rerun the deterministic assessor, and retain/rollback based on actual verification results.",
    }
    OUT.write_text(json.dumps(final, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in final.items() if k not in {"overlays", "verification"}}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
