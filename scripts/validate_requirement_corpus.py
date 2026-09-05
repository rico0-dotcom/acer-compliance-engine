from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.loaders import load_requirements

path = Path(__file__).resolve().parents[1] / "data/requirements/eu_ai_act_core.yaml"
requirements = load_requirements(path)

required = ["id","title","regulation","provision","category","obligation","actor",
            "condition","system_property","rule","parameters","provenance"]

for req in requirements:
    missing = [x for x in required if getattr(req, x, None) is None]
    if missing:
        raise SystemExit(f"{req.id}: missing {missing}")
    if req.provenance.validation_status not in {"HUMAN_VALIDATED", "EXPERT_VALIDATED"}:
        raise SystemExit(f"{req.id}: requirement is not validated")
    if not req.provenance.source_url:
        raise SystemExit(f"{req.id}: missing source URL")

print(f"Validated {len(requirements)} source-traceable requirements.")
