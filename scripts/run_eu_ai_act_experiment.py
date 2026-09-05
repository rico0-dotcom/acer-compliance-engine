from pathlib import Path
import sys, json, argparse
import pandas as pd

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))

from app.engine import assess
from app.loaders import load_requirements, load_system
from app.adaptation import load_tactics
from app.agents import ComplianceOrchestrator
from scripts.generate_ai_act_scenarios import main as generate_main

parser=argparse.ArgumentParser()
parser.add_argument("--scenarios",type=int,default=30)
parser.add_argument("--seed",type=int,default=42)
args=parser.parse_args()

req_path=BASE/"data/requirements/eu_ai_act_core.yaml"
scenario_dir=BASE/"data/systems/eu_ai_act_scenarios"
tactic_path=BASE/"data/tactics/eu_ai_act_tactics.yaml"

# Generate deterministic scenarios.
import random, yaml
from scripts.generate_ai_act_scenarios import make_scenario, DEFECTS
random.seed(args.seed)
scenario_dir.mkdir(parents=True,exist_ok=True)
for p in scenario_dir.glob("ai-act-scenario-*.yaml"):
    p.unlink()
cases=[]
rng=random.Random(args.seed)
for i in range(1,args.scenarios+1):
    defect=rng.choice(DEFECTS)
    s=make_scenario(i,defect)
    (scenario_dir/f"{s['id']}.yaml").write_text(
        yaml.safe_dump({k:v for k,v in s.items() if k!="defect_label"},sort_keys=False),
        encoding="utf-8"
    )
    cases.append({"system_id":s["id"],"defect":defect})

requirements=load_requirements(req_path)
tactics=load_tactics(tactic_path)

rows=[]
scenario_rows=[]

for case in cases:
    s=load_system(scenario_dir/f"{case['system_id']}.yaml")
    before=assess(s,requirements)
    final,history=ComplianceOrchestrator(requirements,tactics).run(s)
    after=assess(final,requirements)

    accepted=sum(bool(h.get("accepted")) for h in history)
    scenario_rows.append({
        "system_id":s.id,
        "defect":case["defect"],
        "baseline_status":before.overall_status,
        "final_status":after.overall_status,
        "baseline_violations":sum(r.status=="FAIL" for r in before.results),
        "final_violations":sum(r.status=="FAIL" for r in after.results),
        "adaptation_success":after.overall_status=="COMPLIANT",
        "adaptation_steps":accepted
    })

    for b,a in zip(before.results,after.results):
        rows.append({
            "system_id":s.id,
            "requirement_id":b.requirement_id,
            "defect":case["defect"],
            "baseline_status":b.status,
            "after_status":a.status,
            "adaptation_steps":accepted
        })

out=BASE/"data/results"
out.mkdir(parents=True,exist_ok=True)

pd.DataFrame(rows).to_csv(out/"eu_ai_act_requirement_results.csv",index=False)
pd.DataFrame(scenario_rows).to_csv(out/"eu_ai_act_scenario_results.csv",index=False)

summary={
    "requirements":len(requirements),
    "scenarios":len(scenario_rows),
    "requirement_checks":len(rows),
    "baseline_noncompliant":sum(x["baseline_status"]=="NON_COMPLIANT" for x in scenario_rows),
    "final_compliant":sum(x["final_status"]=="COMPLIANT" for x in scenario_rows),
    "adaptation_success_rate":round(sum(x["adaptation_success"] for x in scenario_rows)/len(scenario_rows),4),
    "mean_adaptation_steps":round(pd.DataFrame(scenario_rows)["adaptation_steps"].mean(),3)
}
(out/"eu_ai_act_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2))
