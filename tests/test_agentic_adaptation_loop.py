import json
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE / "scripts" / "run_agentic_adaptation_loop.py"


def test_script_exists():
    assert SCRIPT.exists()


def test_agent_classes_are_present():
    text = SCRIPT.read_text(encoding="utf-8")
    for name in [
        "ViolationDiagnoser",
        "AdaptationGenerator",
        "AdaptationEvaluator",
        "AdaptationSelector",
        "AgenticOrchestrator",
    ]:
        assert f"class {name}" in text


def test_isolated_model_execution_reduces_failures(tmp_path):
    systems = tmp_path / "systems"
    systems.mkdir()
    source = systems / "ai-act-benchmark-test.yaml"
    source.write_text(
        """id: test-system\nname: Test\ndomain: demo\nversion: '1.0'\ncomponents:\n  - id: final_decision\n    type: final_decision\n    properties:\n      logging_enabled: false\n  - id: candidate_ui\n    type: user_interface\n    properties: {}\ndata: []\nflows: []\nattributes:\n  transparency_notice: false\n  system_is_high_risk: true\n  direct_ai_interaction: true\nobjectives: {}\n""",
        encoding="utf-8",
    )
    req = tmp_path / "requirements.yaml"
    req.write_text(
        """requirements:\n  - id: EUAI-R12-01\n    title: Logging\n    regulation: Test\n    provision: T12\n    category: logging\n    obligation: log\n    actor: provider\n    condition: {system_is_high_risk: true}\n    system_property: automatic_event_logging\n    rule: property_equals\n    parameters: {component_type: final_decision, property: logging_enabled, expected: true}\n    evidence_expected: []\n    adaptation_tactics: []\n    provenance: {source_type: test, validation_status: UNVALIDATED}\n  - id: EUAI-R50-01\n    title: Notice\n    regulation: Test\n    provision: T50\n    category: transparency\n    obligation: notice\n    actor: provider\n    condition: {direct_ai_interaction: true}\n    system_property: ai_interaction_notice\n    rule: attribute_equals\n    parameters: {attribute: transparency_notice, expected: true}\n    evidence_expected: []\n    adaptation_tactics: []\n    provenance: {source_type: test, validation_status: UNVALIDATED}\n""",
        encoding="utf-8",
    )
    out = tmp_path / "results"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--systems", str(systems), "--requirements", str(req), "--results", str(out)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    summary = json.loads((out / "agentic_adaptation_summary.json").read_text(encoding="utf-8"))
    assert summary["total_violations_before"] == 2
    assert summary["total_violations_after"] == 0
    assert summary["systems_compliant_after"] == 1
    assert summary["source_models_persistently_modified"] is False
