from pathlib import Path
import json
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE / "scripts" / "run_compliance_assessment.py"
SUMMARY = BASE / "data" / "results" / "compliance_assessment_summary.json"
TRACE = BASE / "data" / "results" / "compliance_assessment_trace.csv"


def test_assessment_script_exists():
    assert SCRIPT.exists()


def test_assessment_outputs_are_traceable_after_run():
    if not SUMMARY.exists() or not TRACE.exists():
        subprocess.run([sys.executable, str(SCRIPT)], cwd=BASE, check=True)
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    assert summary["checks"] > 0
    assert summary["traceable_checks"] == summary["checks"]


def test_assessment_has_evidence_for_every_check():
    if not SUMMARY.exists() or not TRACE.exists():
        subprocess.run([sys.executable, str(SCRIPT)], cwd=BASE, check=True)
    lines = TRACE.read_text(encoding="utf-8").splitlines()
    assert len(lines) > 1
    header = lines[0].split(",")
    assert "evidence_count" in header
    assert "source_provision" in header


def test_summary_keeps_method_boundary_explicit():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    assert "does not by itself establish legal compliance" in summary["method_note"]
