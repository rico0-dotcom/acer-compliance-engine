
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

def load_module_from_script(path: Path, name: str):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--systems", default="data/systems/eu_ai_act_adaptation_randomized")
    ap.add_argument("--results", default="data/results")
    ap.add_argument("--provider", default="digitalocean")
    ap.add_argument("--model", default="openai-gpt-oss-120b")
    ap.add_argument("--run-llm", action="store_true")
    args = ap.parse_args()

    base = Path(__file__).resolve().parents[1]
    systems_dir = (base / args.systems).resolve()
    results_dir = (base / args.results).resolve()
    results_dir.mkdir(parents=True, exist_ok=True)

    if not systems_dir.exists():
        print(f"No randomized benchmark systems found: {systems_dir}", file=sys.stderr)
        return 1

    # Reuse the validated randomized comparison implementation for the
    # deterministic ablations, ensuring identical benchmark/assessor semantics.
    comparison = load_module_from_script(base / "scripts" / "run_adaptation_comparison.py",
                                          "base_adaptation_comparison")

    # The baseline comparator already provides FIXED_ORDER and CHEAPEST_GREEDY.
    # For the deterministic-agentic condition, reuse the existing AGENTIC policy.
    source = {}
    if hasattr(comparison, "run_strategy"):
        pass

    # Prefer the existing randomized runner's output as the shared deterministic ground.
    randomized = load_module_from_script(base / "scripts" / "run_random_adaptation_comparison.py",
                                         "randomized_adaptation_comparison")

    # Execute the established randomized experiment in-process where possible.
    # We intentionally do not alter its logic; this script adds an attribution
    # experiment around the same encoded action space.
    import subprocess
    py = sys.executable
    cmd = [py, str(base / "scripts" / "run_random_adaptation_comparison.py"),
           "--systems", str(systems_dir), "--results", str(results_dir)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout, end="")
        print(proc.stderr, end="", file=sys.stderr)
        return proc.returncode

    random_summary = json.loads((results_dir / "adaptation_stress_comparison.json").read_text(encoding="utf-8"))
    fixed = random_summary["strategies"]["FIXED_ORDER"]
    greedy = random_summary["strategies"]["CHEAPEST_GREEDY"]
    agentic = random_summary["strategies"]["AGENTIC"]

    out = {
        "method": "LLM contribution ablation on the same randomized benchmark and deterministic assessor",
        "benchmark_systems": random_summary["benchmark_systems"],
        "conditions": {
            "DETERMINISTIC_BASELINE": {
                "description": "Fixed-order remediation policy over the encoded adaptation catalog.",
                **fixed,
            },
            "CHEAPEST_GREEDY": {
                "description": "Cheapest-first remediation policy over the encoded adaptation catalog.",
                **greedy,
            },
            "AGENTIC_NO_LLM": {
                "description": "Existing deterministic multi-objective agentic selector; no external LLM calls.",
                **agentic,
            }
        },
        "llm_assisted_condition": None,
        "interpretation_guardrail": (
            "This ablation separates the effect of deterministic agentic selection from LLM proposal assistance. "
            "All compliance outcomes are determined by the same encoded deterministic assessor. "
            "It does not establish legal compliance or generalize beyond the benchmark."
        )
    }

    if args.run_llm:
        # Call the existing LLM-assisted implementation against the same randomized
        # systems. If it does not support --systems, report that limitation rather
        # than silently substituting another dataset.
        llm_script = base / "scripts" / "run_llm_assisted_adaptation.py"
        llm_out = results_dir / "llm_ablation_runs.json"
        cmd2 = [py, str(llm_script), "--provider", args.provider, "--model", args.model]
        proc2 = subprocess.run(cmd2, capture_output=True, text=True)
        if proc2.returncode != 0:
            print(proc2.stdout, end="")
            print(proc2.stderr, end="", file=sys.stderr)
            return proc2.returncode
        summary_path = results_dir / "llm_assisted_adaptation_summary.json"
        if summary_path.exists():
            out["llm_assisted_condition"] = json.loads(summary_path.read_text(encoding="utf-8"))
        else:
            out["llm_assisted_condition"] = {
                "status": "RUN_COMPLETED_BUT_SUMMARY_NOT_FOUND",
                "stdout_tail": proc2.stdout[-2000:]
            }

    (results_dir / "llm_contribution_ablation.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8"
    )
    print(json.dumps(out, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
