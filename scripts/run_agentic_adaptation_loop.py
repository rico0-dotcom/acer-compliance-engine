from __future__ import annotations

import argparse
import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from app.engine import assess
from app.loaders import load_requirements, load_system
from app.models import Component, Flow, SystemModel

DEFAULT_SYSTEM_DIR = BASE / "data" / "systems" / "eu_ai_act_benchmark"
DEFAULT_REQUIREMENTS = BASE / "data" / "requirements" / "eu_ai_act_core.yaml"
DEFAULT_RESULTS = BASE / "data" / "results"


def model_hash(system: SystemModel) -> str:
    payload = json.dumps(system.model_dump(), sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def has_component(system: SystemModel, component_type: str) -> bool:
    return any(c.type == component_type for c in system.components)


def has_flow(system: SystemModel, source_type: str, target_type: str) -> bool:
    sources = {c.id for c in system.components if c.type == source_type}
    targets = {c.id for c in system.components if c.type == target_type}
    return any(f.source in sources and f.target in targets for f in system.flows)


def add_component(system: SystemModel, component_type: str, component_id: str, properties: dict[str, Any] | None = None) -> SystemModel:
    updated = deepcopy(system)
    if not has_component(updated, component_type):
        updated.components.append(Component(id=component_id, type=component_type, properties=properties or {}))
    updated.version = f"{system.version}+adaptive"
    return updated


def enable_logging(system: SystemModel) -> SystemModel:
    updated = deepcopy(system)
    finals = [c for c in updated.components if c.type == "final_decision"]
    if not finals:
        updated.components.append(Component(id="final_decision_adaptive", type="final_decision", properties={"logging_enabled": True}))
    else:
        finals[0].properties["logging_enabled"] = True
    updated.version = f"{system.version}+adaptive"
    return updated


def add_human_oversight(system: SystemModel) -> SystemModel:
    updated = deepcopy(system)
    if not has_component(updated, "human_review"):
        updated.components.append(Component(id="human_review_adaptive", type="human_review", properties={"monitoring": True, "understands_output": True}))
    updated.version = f"{system.version}+adaptive"
    return updated


def add_human_intervention_bundle(system: SystemModel) -> SystemModel:
    updated = add_human_oversight(system)
    if not has_component(updated, "final_decision"):
        updated.components.append(Component(id="final_decision_adaptive", type="final_decision", properties={"logging_enabled": True}))
    human_ids = [c.id for c in updated.components if c.type == "human_review"]
    final_ids = [c.id for c in updated.components if c.type == "final_decision"]
    if human_ids and final_ids and not has_flow(updated, "human_review", "final_decision"):
        updated.flows.append(Flow(source=human_ids[0], target=final_ids[0], data="decision_intervention"))
    updated.version = f"{system.version}+adaptive"
    return updated


def enable_ai_notice(system: SystemModel) -> SystemModel:
    updated = deepcopy(system)
    updated.attributes["transparency_notice"] = True
    updated.version = f"{system.version}+adaptive"
    return updated


ActionFn = Callable[[SystemModel], SystemModel]

ACTION_CATALOG: dict[str, list[dict[str, Any]]] = {
    "EUAI-R9-01": [
        {"id": "ADD_RISK_MANAGEMENT", "title": "Add risk-management component", "cost": 2, "complexity": 1, "apply": lambda s: add_component(s, "risk_management", "risk_management_adaptive")},
    ],
    "EUAI-R10-01": [
        {"id": "ADD_DATA_GOVERNANCE", "title": "Add data-governance component", "cost": 2, "complexity": 1, "apply": lambda s: add_component(s, "data_governance", "data_governance_adaptive")},
    ],
    "EUAI-R12-01": [
        {"id": "ENABLE_DECISION_LOGGING", "title": "Enable final-decision logging", "cost": 1, "complexity": 1, "apply": enable_logging},
    ],
    "EUAI-R13-01": [
        {"id": "ADD_TRANSPARENCY_MECHANISM", "title": "Add transparency mechanism", "cost": 2, "complexity": 1, "apply": lambda s: add_component(s, "transparency_mechanism", "transparency_adaptive")},
    ],
    "EUAI-R14-01": [
        {"id": "ADD_HUMAN_OVERSIGHT", "title": "Add human-oversight component", "cost": 2, "complexity": 1, "apply": add_human_oversight},
        {"id": "ADD_HUMAN_INTERVENTION_BUNDLE", "title": "Add human oversight with intervention path", "cost": 3, "complexity": 2, "apply": add_human_intervention_bundle},
    ],
    "EUAI-R14-02": [
        {"id": "ADD_HUMAN_INTERVENTION_BUNDLE", "title": "Add human oversight with intervention path", "cost": 3, "complexity": 2, "apply": add_human_intervention_bundle},
    ],
    "EUAI-R15-01": [
        {"id": "ADD_PERFORMANCE_MONITORING", "title": "Add performance-monitoring component", "cost": 2, "complexity": 1, "apply": lambda s: add_component(s, "performance_monitoring", "performance_monitoring_adaptive")},
    ],
    "EUAI-R50-01": [
        {"id": "ENABLE_AI_INTERACTION_NOTICE", "title": "Enable direct AI interaction notice", "cost": 1, "complexity": 1, "apply": enable_ai_notice},
    ],
}


class ViolationDiagnoser:
    def diagnose(self, report) -> list[str]:
        return [r.requirement_id for r in report.results if r.status == "FAIL"]


class AdaptationGenerator:
    def generate(self, failed_requirements: list[str]) -> list[dict[str, Any]]:
        candidates = []
        seen: set[str] = set()
        for req_id in failed_requirements:
            for candidate in ACTION_CATALOG.get(req_id, []):
                if candidate["id"] not in seen:
                    candidates.append({**candidate, "targets": [req_id]})
                    seen.add(candidate["id"])
        return candidates


class AdaptationEvaluator:
    def evaluate(self, before: SystemModel, candidate: dict[str, Any], requirements) -> dict[str, Any]:
        before_report = assess(before, requirements)
        before_failed = sum(r.status == "FAIL" for r in before_report.results)
        trial = candidate["apply"](before)
        after_report = assess(trial, requirements)
        after_failed = sum(r.status == "FAIL" for r in after_report.results)
        new_failures = max(0, after_failed - before_failed)
        direct_targets_passed = [
            req for req in candidate["targets"]
            if next((r.status for r in after_report.results if r.requirement_id == req), None) == "PASS"
        ]
        gain = before_failed - after_failed
        score = (10.0 * gain) + (2.0 * len(direct_targets_passed)) - (5.0 * new_failures) - candidate["cost"] - candidate["complexity"]
        return {
            "candidate_id": candidate["id"],
            "title": candidate["title"],
            "targets": candidate["targets"],
            "violations_before": before_failed,
            "violations_after": after_failed,
            "compliance_gain": gain,
            "new_failures": new_failures,
            "direct_targets_passed": direct_targets_passed,
            "cost": candidate["cost"],
            "complexity": candidate["complexity"],
            "score": round(score, 3),
            "trial_model_hash": model_hash(trial),
            "trial_model": trial,
        }


class AdaptationSelector:
    def select(self, evaluations: list[dict[str, Any]]) -> dict[str, Any] | None:
        improving = [e for e in evaluations if e["compliance_gain"] > 0 and e["new_failures"] == 0]
        if not improving:
            return None
        return max(improving, key=lambda e: (e["score"], len(e["direct_targets_passed"]), -e["cost"], -e["complexity"], e["candidate_id"]))


class AgenticOrchestrator:
    def __init__(self, requirements, max_steps: int = 12):
        self.requirements = requirements
        self.max_steps = max_steps
        self.diagnoser = ViolationDiagnoser()
        self.generator = AdaptationGenerator()
        self.evaluator = AdaptationEvaluator()
        self.selector = AdaptationSelector()

    def run(self, system: SystemModel) -> tuple[SystemModel, list[dict[str, Any]]]:
        current = deepcopy(system)
        history: list[dict[str, Any]] = []
        seen_states: set[tuple[tuple[str, str], ...]] = set()

        for step in range(1, self.max_steps + 1):
            before_report = assess(current, self.requirements)
            failed = self.diagnoser.diagnose(before_report)
            state = tuple((r.requirement_id, r.status) for r in before_report.results)
            if not failed:
                history.append({"step": step, "accepted": False, "termination": "COMPLIANT", "violations_after": 0})
                break
            if state in seen_states:
                history.append({"step": step, "accepted": False, "termination": "CYCLE_DETECTED", "failed_requirements": failed})
                break
            seen_states.add(state)

            candidates = self.generator.generate(failed)
            evaluations = [self.evaluator.evaluate(current, c, self.requirements) for c in candidates]
            selected = self.selector.select(evaluations)
            if selected is None:
                history.append({
                    "step": step,
                    "accepted": False,
                    "termination": "NO_STRICT_IMPROVEMENT",
                    "failed_requirements": failed,
                    "candidate_evaluations": [self._public_eval(e) for e in evaluations],
                })
                break

            current = selected["trial_model"]
            history.append({
                "step": step,
                "accepted": True,
                "selected_candidate": self._public_eval(selected),
                "failed_requirements_before": failed,
                "violations_before": selected["violations_before"],
                "violations_after": selected["violations_after"],
            })

        return current, history

    @staticmethod
    def _public_eval(e: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in e.items() if k not in {"trial_model"}}


def run_all(system_dir: Path, requirements_path: Path, results_dir: Path, max_steps: int) -> dict[str, Any]:
    requirements = load_requirements(requirements_path)
    system_paths = sorted(system_dir.glob("ai-act-benchmark-*.yaml"))
    if not system_paths:
        raise SystemExit(f"No systems matched ai-act-benchmark-*.yaml in {system_dir}")

    orchestrator = AgenticOrchestrator(requirements, max_steps=max_steps)
    records = []
    initial_hashes: dict[str, str] = {}

    for system_path in system_paths:
        system = load_system(system_path)
        original_hash = model_hash(system)
        initial_hashes[system.id] = original_hash
        before = assess(system, requirements)
        before_failures = sum(r.status == "FAIL" for r in before.results)
        adapted, history = orchestrator.run(system)
        after = assess(adapted, requirements)
        after_failures = sum(r.status == "FAIL" for r in after.results)
        records.append({
            "system_id": system.id,
            "source_file": str(system_path),
            "original_model_hash": original_hash,
            "adapted_model_hash": model_hash(adapted),
            "source_model_unchanged_in_memory": original_hash == model_hash(system),
            "violations_before": before_failures,
            "violations_after": after_failures,
            "status_before": before.overall_status,
            "status_after": after.overall_status,
            "steps": len(history),
            "accepted_steps": sum(1 for h in history if h.get("accepted")),
            "history": history,
            "adapted_system": adapted.model_dump(),
        })

    total_before = sum(r["violations_before"] for r in records)
    total_after = sum(r["violations_after"] for r in records)
    total_accepted = sum(r["accepted_steps"] for r in records)
    compliant_after = sum(r["status_after"] == "COMPLIANT" for r in records)
    records_path = results_dir / "agentic_adaptation_runs.json"
    summary_path = results_dir / "agentic_adaptation_summary.json"
    results_dir.mkdir(parents=True, exist_ok=True)
    records_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = {
        "method": "multi-agent model-level adaptation loop",
        "agents": ["ViolationDiagnoser", "AdaptationGenerator", "AdaptationEvaluator", "AdaptationSelector", "AgenticOrchestrator"],
        "systems": len(records),
        "total_violations_before": total_before,
        "total_violations_after": total_after,
        "violations_reduced": total_before - total_after,
        "accepted_adaptation_steps": total_accepted,
        "systems_compliant_after": compliant_after,
        "system_compliance_rate_after": round(compliant_after / len(records), 6) if records else 0.0,
        "source_models_persistently_modified": False,
        "execution_scope": "isolated in-memory deep copies of system models",
        "selection_objective": "maximize verified compliance improvement while avoiding new failures and minimizing cost/complexity",
        "verification": "existing deterministic ACER assessor rerun after every accepted adaptation",
        "method_note": "Research prototype. Model mutations occur only on isolated copies; successful re-assessment demonstrates benchmark/model-level remediation, not real-world legal compliance or production-safe autonomous deployment.",
        "records_file": str(records_path),
        "initial_model_hash_count": len(initial_hashes),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ACER multi-agent model-level adaptation and verification loop.")
    parser.add_argument("--systems", default=str(DEFAULT_SYSTEM_DIR))
    parser.add_argument("--requirements", default=str(DEFAULT_REQUIREMENTS))
    parser.add_argument("--results", default=str(DEFAULT_RESULTS))
    parser.add_argument("--max-steps", type=int, default=12)
    args = parser.parse_args()
    summary = run_all(Path(args.systems), Path(args.requirements), Path(args.results), args.max_steps)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
