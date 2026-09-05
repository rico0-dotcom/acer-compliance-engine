
from pathlib import Path
import json
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE / "scripts" / "run_llm_assisted_adaptation.py"

def test_llm_assisted_runner_accepts_randomized_dataset(tmp_path):
    systems = tmp_path / "systems"
    systems.mkdir()
    (systems / "ai-act-random-stress-001.yaml").write_text(
        """id: ai-act-random-stress-001
name: Random test
domain: demo
version: '1.0'
components:
  - id: final_decision
    type: final_decision
    properties:
      logging_enabled: false
attributes:
  system_is_high_risk: true
  direct_ai_interaction: true
  transparency_notice: false
data: []
flows: []
objectives: {}
""",
        encoding="utf-8",
    )
    req = tmp_path / "requirements.yaml"
    req.write_text(
        """requirements:
  - id: EUAI-R12-01
    title: Logging
    regulation: Test
    provision: T12
    category: logging
    obligation: log
    actor: provider
    condition: {system_is_high_risk: true}
    system_property: automatic_event_logging
    rule: property_equals
    parameters: {component_type: final_decision, property: logging_enabled, expected: true}
    evidence_expected: []
    adaptation_tactics: []
    provenance: {source_type: test, validation_status: UNVALIDATED}
""",
        encoding="utf-8",
    )
    out = tmp_path / "results"
    # Do not call the live LLM. The command only verifies that the randomized
    # filename is discovered; the run may terminate at the LLM credential gate.
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--systems", str(systems), "--requirements", str(req), "--results", str(out),
         "--provider", "digitalocean", "--model", "test-model"],
        capture_output=True, text=True
    )
    assert "No ACER system YAML files found" not in result.stderr
