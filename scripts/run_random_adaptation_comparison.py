from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from scripts.run_adaptation_stress_comparison import main as run_stress_main
import shutil
import tempfile


def main() -> None:
    # Bridge randomized filenames to the validated stress runner without modifying source data.
    import sys as _sys
    ap = argparse.ArgumentParser(description="Run the ACER randomized adaptation benchmark comparison.")
    ap.add_argument("--systems", default=str(BASE / "data" / "systems" / "eu_ai_act_adaptation_randomized"))
    ap.add_argument("--requirements", default=str(BASE / "data" / "requirements" / "eu_ai_act_core.yaml"))
    ap.add_argument("--results", default=str(BASE / "data" / "results"))
    args = ap.parse_args()
    source_dir = Path(args.systems)
    files = sorted(source_dir.glob("ai-act-random-stress-*.yaml"))
    if not files:
        raise SystemExit(f"No randomized benchmark systems found in {source_dir}. Run generate_random_adaptation_benchmark.py first.")
    with tempfile.TemporaryDirectory(prefix="acer_randomized_stress_") as td:
        bridge = Path(td) / "systems"
        bridge.mkdir()
        for f in files:
            shutil.copy2(f, bridge / f.name.replace("ai-act-random-stress-", "ai-act-stress-", 1))
        _sys.argv = ["run_adaptation_stress_comparison.py", "--systems", str(bridge), "--requirements", args.requirements, "--results", args.results]
        run_stress_main()

if __name__ == "__main__":
    main()
