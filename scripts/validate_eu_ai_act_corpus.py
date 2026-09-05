from pathlib import Path
import sys
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))

from app.loaders import load_requirements

path=BASE/"data/requirements/eu_ai_act_core.yaml"
reqs=load_requirements(path)

for r in reqs:
    if not r.provenance.source_url:
        raise SystemExit(f"{r.id}: missing source URL")
    if r.provenance.source_id != "CELEX:32024R1689":
        raise SystemExit(f"{r.id}: unexpected source identifier")
    if r.provenance.validation_status not in {"HUMAN_VALIDATED","EXPERT_VALIDATED"}:
        raise SystemExit(f"{r.id}: validation status is not sufficient")
    if not r.condition:
        raise SystemExit(f"{r.id}: missing applicability condition")

print(f"Validated {len(reqs)} source-traceable EU AI Act requirements.")
