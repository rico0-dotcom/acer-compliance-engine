from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from statistics import mean
from typing import Any, Callable

BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from app.engine import assess
from app.loaders import load_requirements, load_system
from app.models import Component, Flow, SystemModel

DEFAULT_SYSTEM_DIR = BASE / "data" / "systems" / "eu_ai_act_adaptation_stress"
DEFAULT_REQUIREMENTS = BASE / "data" / "requirements" / "eu_ai_act_core.yaml"
DEFAULT_RESULTS = BASE / "data" / "results"


def add_component(system: SystemModel, ctype: str, cid: str, properties: dict[str, Any] | None = None) -> SystemModel:
    out = deepcopy(system)
    if not any(c.type == ctype for c in out.components):
        out.components.append(Component(id=cid, type=ctype, properties=properties or {}))
    out.version = f"{system.version}+stress-adaptive"
    return out


def set_attr(system: SystemModel, key: str, value: Any) -> SystemModel:
    out = deepcopy(system)
    out.attributes[key] = value
    out.version = f"{system.version}+stress-adaptive"
    return out


def has_flow(system: SystemModel, source_type: str, target_type: str) -> bool:
    src = {c.id for c in system.components if c.type == source_type}
    dst = {c.id for c in system.components if c.type == target_type}
    return any(f.source in src and f.target in dst for f in system.flows)


def add_human_intervention(system: SystemModel) -> SystemModel:
    out = add_component(system, "human_review", "human_review_stress", {"monitoring": True, "understands_output": True})
    finals = [c.id for c in out.components if c.type == "final_decision"]
    humans = [c.id for c in out.components if c.type == "human_review"]
    if finals and humans and not has_flow(out, "human_review", "final_decision"):
        out.flows.append(Flow(source=humans[0], target=finals[0], data="decision_intervention"))
    out.version = f"{system.version}+stress-adaptive"
    return out


def enable_logging(system: SystemModel) -> SystemModel:
    out = deepcopy(system)
    finals = [c for c in out.components if c.type == "final_decision"]
    if not finals:
        out.components.append(Component(id="final_decision_stress", type="final_decision", properties={"logging_enabled": True}))
    else:
        finals[0].properties["logging_enabled"] = True
    out.version = f"{system.version}+stress-adaptive"
    return out


def bundle_transparency(system: SystemModel) -> SystemModel:
    out = add_component(system, "transparency_mechanism", "transparency_stress")
    return set_attr(out, "transparency_notice", True)


def bundle_risk_data(system: SystemModel) -> SystemModel:
    out = add_component(system, "risk_management", "risk_management_stress")
    return add_component(out, "data_governance", "data_governance_stress")


def bundle_operational(system: SystemModel) -> SystemModel:
    out = enable_logging(system)
    return add_component(out, "performance_monitoring", "performance_monitoring_stress")


def bundle_human(system: SystemModel) -> SystemModel:
    return add_human_intervention(system)


def add_transparency(system: SystemModel) -> SystemModel:
    return add_component(system, "transparency_mechanism", "transparency_single_stress")


def add_risk(system: SystemModel) -> SystemModel:
    return add_component(system, "risk_management", "risk_single_stress")


def add_data(system: SystemModel) -> SystemModel:
    return add_component(system, "data_governance", "data_single_stress")


def add_perf(system: SystemModel) -> SystemModel:
    return add_component(system, "performance_monitoring", "performance_single_stress")


def enable_notice(system: SystemModel) -> SystemModel:
    return set_attr(system, "transparency_notice", True)

Action = Callable[[SystemModel], SystemModel]

CATALOG: dict[str, list[dict[str, Any]]] = {
    "EUAI-R9-01": [
        {"id": "ADD_RISK", "title": "Add risk-management control", "cost": 2, "complexity": 1, "apply": add_risk},
        {"id": "BUNDLE_RISK_DATA", "title": "Add joint risk-management and data-governance controls", "cost": 3, "complexity": 2, "apply": bundle_risk_data, "targets": ["EUAI-R9-01", "EUAI-R10-01"]},
    ],
    "EUAI-R10-01": [
        {"id": "ADD_DATA", "title": "Add data-governance control", "cost": 2, "complexity": 1, "apply": add_data},
        {"id": "BUNDLE_RISK_DATA", "title": "Add joint risk-management and data-governance controls", "cost": 3, "complexity": 2, "apply": bundle_risk_data, "targets": ["EUAI-R9-01", "EUAI-R10-01"]},
    ],
    "EUAI-R12-01": [
        {"id": "ENABLE_LOGGING", "title": "Enable automatic decision logging", "cost": 1, "complexity": 1, "apply": enable_logging},
        {"id": "BUNDLE_OPERATIONAL", "title": "Add logging and performance-monitoring controls", "cost": 2, "complexity": 2, "apply": bundle_operational, "targets": ["EUAI-R12-01", "EUAI-R15-01"]},
    ],
    "EUAI-R13-01": [
        {"id": "ADD_TRANSPARENCY", "title": "Add transparency mechanism", "cost": 2, "complexity": 1, "apply": add_transparency},
        {"id": "BUNDLE_TRANSPARENCY", "title": "Add transparency mechanism and interaction notice", "cost": 2, "complexity": 2, "apply": bundle_transparency, "targets": ["EUAI-R13-01", "EUAI-R50-01"]},
    ],
    "EUAI-R14-01": [
        {"id": "ADD_HUMAN", "title": "Add human oversight", "cost": 2, "complexity": 1, "apply": lambda s: add_component(s, "human_review", "human_review_single_stress", {"monitoring": True, "understands_output": True})},
        {"id": "BUNDLE_HUMAN", "title": "Add human oversight with intervention path", "cost": 3, "complexity": 2, "apply": bundle_human, "targets": ["EUAI-R14-01", "EUAI-R14-02"]},
    ],
    "EUAI-R14-02": [
        {"id": "BUNDLE_HUMAN", "title": "Add human oversight with intervention path", "cost": 3, "complexity": 2, "apply": bundle_human, "targets": ["EUAI-R14-01", "EUAI-R14-02"]},
    ],
    "EUAI-R15-01": [
        {"id": "ADD_PERF", "title": "Add performance-monitoring control", "cost": 2, "complexity": 1, "apply": add_perf},
        {"id": "BUNDLE_OPERATIONAL", "title": "Add logging and performance-monitoring controls", "cost": 2, "complexity": 2, "apply": bundle_operational, "targets": ["EUAI-R12-01", "EUAI-R15-01"]},
    ],
    "EUAI-R50-01": [
        {"id": "ENABLE_NOTICE", "title": "Enable direct-AI interaction notice", "cost": 1, "complexity": 1, "apply": enable_notice},
        {"id": "BUNDLE_TRANSPARENCY", "title": "Add transparency mechanism and interaction notice", "cost": 2, "complexity": 2, "apply": bundle_transparency, "targets": ["EUAI-R13-01", "EUAI-R50-01"]},
    ],
}


def failed(report) -> list[str]:
    return [r.requirement_id for r in report.results if r.status == "FAIL"]


def eval_candidate(system, candidate, requirements):
    before = assess(system, requirements)
    trial = candidate["apply"](system)
    after = assess(trial, requirements)
    b = len(failed(before)); a = len(failed(after))
    targets = candidate.get("targets", candidate.get("primary_targets", []))
    direct_pass = [r for r in targets if next((x.status for x in after.results if x.requirement_id == r), None) == "PASS"]
    gain = b - a
    new_failures = max(0, a - b)
    score = 10 * gain + 2 * len(direct_pass) - 5 * new_failures - candidate["cost"] - candidate["complexity"]
    return {"candidate_id": candidate["id"], "title": candidate["title"], "targets": targets,
            "violations_before": b, "violations_after": a, "gain": gain, "new_failures": new_failures,
            "direct_targets_passed": direct_pass, "cost": candidate["cost"], "complexity": candidate["complexity"],
            "score": score, "trial_model": trial}


def candidates_for(fails: list[str]) -> list[dict[str, Any]]:
    out, seen = [], set()
    for req in fails:
        for c in CATALOG.get(req, []):
            if c["id"] in seen:
                continue
            seen.add(c["id"])
            out.append(dict(c))
    return out


def run_fixed(system, requirements, max_steps=20):
    current = deepcopy(system); hist=[]
    for step in range(1, max_steps+1):
        fails = failed(assess(current, requirements))
        if not fails: break
        applied=False
        for req in fails:
            for c in CATALOG.get(req, []):
                e=eval_candidate(current, {**c, "primary_targets":[req]}, requirements)
                if e["gain"]>0 and e["new_failures"]==0:
                    current=e["trial_model"]; hist.append(e); applied=True; break
            if applied: break
        if not applied: break
    return current, hist


def run_greedy(system, requirements, max_steps=20):
    current=deepcopy(system); hist=[]
    for _ in range(max_steps):
        fails=failed(assess(current, requirements))
        if not fails: break
        ev=[eval_candidate(current,c,requirements) for c in candidates_for(fails)]
        good=[e for e in ev if e["gain"]>0 and e["new_failures"]==0]
        if not good: break
        s=min(good,key=lambda e:(e["cost"],e["complexity"],e["candidate_id"]))
        current=s["trial_model"]; hist.append(s)
    return current,hist


def run_agentic(system, requirements, max_steps=20):
    current=deepcopy(system); hist=[]
    for _ in range(max_steps):
        fails=failed(assess(current, requirements))
        if not fails: break
        ev=[eval_candidate(current,c,requirements) for c in candidates_for(fails)]
        good=[e for e in ev if e["gain"]>0 and e["new_failures"]==0]
        if not good: break
        s=max(good,key=lambda e:(e["score"],len(e["direct_targets_passed"]),-e["cost"],-e["complexity"],e["candidate_id"]))
        current=s["trial_model"]; hist.append(s)
    return current,hist


def summary(name: str, records: list[dict[str,Any]]) -> dict[str,Any]:
    b=sum(r["before"] for r in records); a=sum(r["after"] for r in records); steps=sum(r["steps"] for r in records)
    cost=sum(r["cost"] for r in records); comp=sum(r["complexity"] for r in records)
    compliant=sum(r["after"]==0 for r in records)
    return {"strategy":name,"systems":len(records),"violations_before":b,"violations_after":a,
            "violation_reduction_rate":round((b-a)/b,6) if b else 1.0,"systems_compliant_after":compliant,
            "system_compliance_rate_after":round(compliant/len(records),6),"accepted_adaptation_steps":steps,
            "mean_steps_per_system":round(mean(r["steps"] for r in records),6),"total_cost":cost,
            "mean_cost_per_system":round(mean(r["cost"] for r in records),6),"total_complexity":comp,
            "mean_complexity_per_system":round(mean(r["complexity"] for r in records),6),
            "new_failures_total":sum(r["new_failures"] for r in records)}


def main():
    ap=argparse.ArgumentParser(description="ACER multi-objective adaptation stress comparison")
    ap.add_argument("--systems",default=str(DEFAULT_SYSTEM_DIR)); ap.add_argument("--requirements",default=str(DEFAULT_REQUIREMENTS)); ap.add_argument("--results",default=str(DEFAULT_RESULTS))
    args=ap.parse_args(); reqs=load_requirements(args.requirements)
    paths=sorted(Path(args.systems).glob("ai-act-stress-*.yaml"))
    if not paths: raise SystemExit("No stress benchmark systems found. Run generate_adaptation_stress_benchmark.py first.")
    strategies={"FIXED_ORDER":run_fixed,"CHEAPEST_GREEDY":run_greedy,"AGENTIC":run_agentic}; all_runs={}
    for name,fn in strategies.items():
        rows=[]
        for p in paths:
            system=load_system(p); before=len(failed(assess(system,reqs))); adapted,h=fn(system,reqs); after=len(failed(assess(adapted,reqs)))
            rows.append({"system_id":system.id,"before":before,"after":after,"steps":len(h),"cost":sum(x["cost"] for x in h),"complexity":sum(x["complexity"] for x in h),"new_failures":sum(x["new_failures"] for x in h),"history":[{k:v for k,v in x.items() if k!="trial_model"} for x in h]})
        all_runs[name]=rows
    comparison={"method":"multi-objective interaction stress benchmark using identical 8 requirements and deterministic assessor","benchmark_systems":len(paths),"strategies":{k:summary(k,v) for k,v in all_runs.items()},"intended_interactions":["multi-violation systems","multi-target bundled repairs","shared human-oversight intervention path"],"interpretation_guardrail":"This is a synthetic stress test of adaptation search/selection policies over encoded tactics; it does not establish legal compliance or superiority on unseen systems."}
    out=Path(args.results); out.mkdir(parents=True,exist_ok=True); (out/"adaptation_stress_comparison.json").write_text(json.dumps(comparison,indent=2,ensure_ascii=False),encoding="utf-8"); (out/"adaptation_stress_comparison_runs.json").write_text(json.dumps(all_runs,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(comparison,indent=2,ensure_ascii=False))

if __name__=="__main__": main()
