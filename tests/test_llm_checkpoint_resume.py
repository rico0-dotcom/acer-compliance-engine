from pathlib import Path
import json
import subprocess
import sys

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE / "scripts" / "run_llm_assisted_adaptation.py"


def test_runner_exposes_checkpoint_and_retry_flags():
    text = SCRIPT.read_text(encoding="utf-8")
    assert '"--checkpoint"' in text
    assert '"--max-retries"' in text
    assert "generate_with_retry" in text
    assert "save_checkpoint" in text
