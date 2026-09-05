
from pathlib import Path
import json, subprocess, sys

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE/"scripts/run_multiseed_adaptation_evaluation.py"

def test_count_validation():
    p = subprocess.run(
        [sys.executable, str(SCRIPT), "--seeds", "20260904", "--count", "10"],
        capture_output=True, text=True
    )
    assert p.returncode != 0
    assert "--count must be at least 20" in p.stderr
