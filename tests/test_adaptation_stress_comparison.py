from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
GEN = BASE / "scripts" / "generate_adaptation_stress_benchmark.py"
RUN = BASE / "scripts" / "run_adaptation_stress_comparison.py"


def test_stress_benchmark_generation(tmp_path):
    out = tmp_path / "stress"
    p = subprocess.run([sys.executable, str(GEN), "--out", str(out)], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    assert len(list(out.glob("ai-act-stress-*.yaml"))) == 12


def test_agentic_prefers_joint_repairs_on_interacting_cases(tmp_path):
    systems = tmp_path / "stress"
    out = tmp_path / "results"
    subprocess.run([sys.executable, str(GEN), "--out", str(systems)], check=True, capture_output=True, text=True)
    p = subprocess.run([sys.executable, str(RUN), "--systems", str(systems), "--results", str(out)], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    data = json.loads((out / "adaptation_stress_comparison.json").read_text(encoding="utf-8"))
    fixed = data["strategies"]["FIXED_ORDER"]
    greedy = data["strategies"]["CHEAPEST_GREEDY"]
    agentic = data["strategies"]["AGENTIC"]
    assert fixed["violations_after"] == 0
    assert greedy["violations_after"] == 0
    assert agentic["violations_after"] == 0
    assert agentic["accepted_adaptation_steps"] < fixed["accepted_adaptation_steps"]
    assert agentic["accepted_adaptation_steps"] < greedy["accepted_adaptation_steps"]


def test_same_initial_failure_count(tmp_path):
    systems = tmp_path / "stress"
    out = tmp_path / "results"
    subprocess.run([sys.executable, str(GEN), "--out", str(systems)], check=True, capture_output=True, text=True)
    subprocess.run([sys.executable, str(RUN), "--systems", str(systems), "--results", str(out)], check=True, capture_output=True, text=True)
    data = json.loads((out / "adaptation_stress_comparison.json").read_text(encoding="utf-8"))
    counts = {v["violations_before"] for v in data["strategies"].values()}
    assert counts == {41}
