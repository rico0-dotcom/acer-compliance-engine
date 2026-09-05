from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
GEN = BASE / "scripts" / "generate_random_adaptation_benchmark.py"
RUN = BASE / "scripts" / "run_random_adaptation_comparison.py"


def test_random_generator_is_deterministic(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    subprocess.run([sys.executable, str(GEN), "--out", str(a), "--count", "100", "--seed", "20260904"], check=True)
    subprocess.run([sys.executable, str(GEN), "--out", str(b), "--count", "100", "--seed", "20260904"], check=True)
    ma = (a / "MANIFEST.yaml").read_text(encoding="utf-8")
    mb = (b / "MANIFEST.yaml").read_text(encoding="utf-8")
    assert ma == mb


def test_random_generator_has_expected_size(tmp_path):
    systems = tmp_path / "systems"
    subprocess.run([sys.executable, str(GEN), "--out", str(systems), "--count", "100"], check=True)
    assert len(list(systems.glob("ai-act-random-stress-*.yaml"))) == 100


def test_random_comparison_uses_one_common_initial_count(tmp_path):
    systems = tmp_path / "systems"
    results = tmp_path / "results"
    subprocess.run([sys.executable, str(GEN), "--out", str(systems), "--count", "100"], check=True)
    subprocess.run([sys.executable, str(RUN), "--systems", str(systems), "--results", str(results)], check=True)
    data = json.loads((results / "adaptation_stress_comparison.json").read_text(encoding="utf-8"))
    before = {v["violations_before"] for v in data["strategies"].values()}
    assert len(before) == 1
    observed = next(iter(before))
    assert observed > 200
    manifest = __import__("yaml").safe_load((systems / "MANIFEST.yaml").read_text(encoding="utf-8"))
    assert manifest["expected_total_initial_failures"] == observed
    assert all(v["systems"] == 100 for v in data["strategies"].values())
