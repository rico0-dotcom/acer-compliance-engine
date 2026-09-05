import json
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]


def test_script_exists():
    assert (BASE / "scripts" / "plan_compliance_adaptations.py").exists()


def test_action_catalog_covers_all_requirements():
    text = (BASE / "scripts" / "plan_compliance_adaptations.py").read_text(encoding="utf-8")
    for req in ["EUAI-R9-01", "EUAI-R10-01", "EUAI-R12-01", "EUAI-R13-01", "EUAI-R14-01", "EUAI-R14-02", "EUAI-R15-01", "EUAI-R50-01"]:
        assert req in text


def test_planner_is_proposal_only(tmp_path):
    trace = tmp_path / "trace.jsonl"
    trace.write_text(json.dumps({
        "system_id": "s1", "system_version": "1", "requirement_id": "EUAI-R14-02",
        "requirement_title": "Override", "regulation": "EU AI Act", "provision": "Article 14(4)(d)-(e)",
        "status": "FAIL", "explanation": "override and stop controls missing", "evidence": "[]", "trace_id": "t1"
    }) + "\n", encoding="utf-8")
    out = tmp_path / "out"
    result = subprocess.run([sys.executable, str(BASE / "scripts" / "plan_compliance_adaptations.py"), "--trace", str(trace), "--results", str(out)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    plans = json.loads((out / "compliance_adaptation_plans.json").read_text(encoding="utf-8"))
    assert plans[0]["execution_status"] == "PROPOSED_NOT_APPLIED"
    assert plans[0]["human_intervention_required"] is True
    assert plans[0]["verification_required_after_adaptation"] is True
