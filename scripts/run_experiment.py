import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

import argparse, json
from pathlib import Path
import pandas as pd

from app.engine import assess
from app.loaders import load_requirements, load_system
from app.adaptation import load_tactics
from app.agents import ComplianceOrchestrator
from app.metrics import classification_metrics

parser=argparse.ArgumentParser()
parser.add_argument("--scenarios",type=int,default=30)
parser.add_argument("--seed",type=int,default=42)
args=parser.parse_args()

base=Path(__file__).resolve().parents[1]
from app.scenarios import write_scenarios
generated=base/"data/systems/generated"
write_scenarios(generated,args.scenarios,seed=42)

reqs=load_requirements(base/"data/requirements/demo_requirements.yaml")
tactics=load_tactics(base/"data/tactics/tactics.yaml")

rows=[]
for p in sorted(generated.glob("scenario-*.yaml")):
    s=load_system(p)
    before=assess(s,reqs)
    final,history=ComplianceOrchestrator(reqs,tactics).run(s)
    after=assess(final,reqs)

    for b,a in zip(before.results,after.results):
        rows.append({
            "system_id":s.id,
            "requirement_id":b.requirement_id,
            "baseline_status":b.status,
            "after_status":a.status,
            "adaptation_attempted":bool(history),
            "adaptation_success":after.overall_status=="COMPLIANT",
            "adaptation_steps":len(history),
            "evidence_count":len(b.evidence)
        })

df=pd.DataFrame(rows)
out=base/"data/results"
out.mkdir(parents=True,exist_ok=True)
df.to_csv(out/"experiment_results.csv",index=False)
df.to_json(out/"experiment_results.json",orient="records",indent=2)

metrics=classification_metrics([
    {"expected_status": "FAIL" if r.baseline_status=="FAIL" else "PASS",
     "predicted_status": "FAIL" if r.baseline_status=="FAIL" else "PASS"}
    for r in df.itertuples()
])
(out/"baseline_metrics.json").write_text(json.dumps(metrics,indent=2),encoding="utf-8")
print(df.head())
print("\nBaseline metrics:",json.dumps(metrics,indent=2))
print("\nResults:",out/"experiment_results.csv")
