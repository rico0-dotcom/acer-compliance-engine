import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "execute_compliance_adaptations.py"
RESULT = ROOT / "data" / "results" / "compliance_adaptation_execution.json"
TRACE = ROOT / "data" / "results" / "compliance_assessment_trace.csv"
PLANS = ROOT / "data" / "results" / "compliance_adaptation_plans.json"


def test_execution_script_exists():
    assert SCRIPT.exists()


def test_execution_waits_for_human_approval():
    if not TRACE.exists() or not PLANS.exists():
        return
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, capture_output=True, text=True)
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    assert result["execution_status"] == "AWAITING_HUMAN_APPROVAL"
    assert result["approved"] is False
    assert result["applied_changes"] == 0


def test_approved_execution_is_isolated_and_verifiable():
    if not TRACE.exists() or not PLANS.exists():
        return
    subprocess.run([sys.executable, str(SCRIPT), "--approve-all"], cwd=ROOT, check=True, capture_output=True, text=True)
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    assert result["execution_status"] == "SIMULATED_APPROVED_AND_VERIFIED"
    assert result["source_models_modified"] is False
    assert result["applied_changes"] == result["post_verification"]
    assert result["post_status_counts"]["FAIL"] == 0


def test_failed_check_count_is_preserved():
    if not TRACE.exists() or not PLANS.exists():
        return
    with TRACE.open("r", encoding="utf-8-sig", newline="") as f:
        failed = [r for r in csv.DictReader(f) if r.get("status", "").upper() == "FAIL"]
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    assert result["failed_checks"] == len(failed)
