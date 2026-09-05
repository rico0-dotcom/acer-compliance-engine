
from __future__ import annotations
import argparse, json, subprocess, sys, time
from pathlib import Path
from statistics import mean, pstdev

def run_capture(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stdout, end="")
        print(p.stderr, end="", file=sys.stderr)
        raise SystemExit(p.returncode)
    return p

def run_live(cmd):
    """Run a child process with stdout/stderr attached so live progress is visible."""
    p = subprocess.run(cmd, text=True)
    if p.returncode != 0:
        raise SystemExit(p.returncode)
    return p

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def extract_llm_metrics(runs_path):
    runs = load_json(runs_path)
    accepted = []
    llm_calls = 0
    llm_failures = 0
    for system in runs:
        llm_calls += int(system.get("llm_calls", 0))
        llm_failures += int(system.get("llm_failures", 0))
        for h in system.get("history", []):
            cand = h.get("selected_candidate")
            if h.get("accepted") is True and cand:
                accepted.append({
                    "cost": float(cand.get("cost", 0)),
                    "complexity": float(cand.get("complexity", 0)),
                })
    n = len(runs)
    total_cost = sum(x["cost"] for x in accepted)
    total_complexity = sum(x["complexity"] for x in accepted)
    return {
        "systems": n,
        "accepted_adaptation_steps": len(accepted),
        "mean_steps_per_system": len(accepted) / n if n else None,
        "total_cost": total_cost,
        "mean_cost_per_system": total_cost / n if n else None,
        "total_complexity": total_complexity,
        "mean_complexity_per_system": total_complexity / n if n else None,
        "llm_calls": llm_calls,
        "llm_failures": llm_failures,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", nargs="+", type=int, default=[20260904, 20260905, 20260906])
    ap.add_argument("--count", type=int, default=100)
    ap.add_argument("--run-llm", action="store_true")
    ap.add_argument("--reuse-llm-seed", type=int, default=20260904)
    ap.add_argument("--reuse-llm-results", default="data/results/llm_randomized")
    ap.add_argument("--provider", default="digitalocean")
    ap.add_argument("--model", default="openai-gpt-oss-120b")
    ap.add_argument("--max-retries", type=int, default=6)
    ap.add_argument("--base-delay", type=float, default=5.0)
    args = ap.parse_args()

    if args.count < 20:
        print("--count must be at least 20", file=sys.stderr)
        return 1

    base = Path(__file__).resolve().parents[1]
    systems_root = base / "data" / "systems" / "eu_ai_act_adaptation_multiseed"
    results_root = base / "data" / "results" / "adaptation_multiseed"
    req = base / "data" / "requirements" / "eu_ai_act_core.yaml"
    systems_root.mkdir(parents=True, exist_ok=True)
    results_root.mkdir(parents=True, exist_ok=True)

    per_seed = []
    total = len(args.seeds)

    for idx, seed in enumerate(args.seeds, start=1):
        systems = systems_root / f"seed_{seed}"
        results = results_root / f"seed_{seed}"
        systems.mkdir(parents=True, exist_ok=True)
        results.mkdir(parents=True, exist_ok=True)

        print(f"\n===== Seed {seed} ({idx}/{total}) =====", flush=True)
        run_capture([sys.executable, str(base/"scripts/generate_random_adaptation_benchmark.py"),
                     "--out", str(systems), "--count", str(args.count), "--seed", str(seed)])
        run_capture([sys.executable, str(base/"scripts/run_random_adaptation_comparison.py"),
                     "--systems", str(systems), "--results", str(results)])
        det = load_json(results/"adaptation_stress_comparison.json")

        record = {
            "seed": seed,
            "systems": args.count,
            "deterministic_conditions": det["strategies"],
            "llm_assisted": None,
            "llm_metrics": None,
            "llm_result_source": None,
        }

        if args.run_llm:
            reuse_dir = (base / args.reuse_llm_results).resolve()
            reuse_summary = reuse_dir / "llm_assisted_adaptation_summary.json"
            reuse_runs = reuse_dir / "llm_assisted_adaptation_runs.json"

            if seed == args.reuse_llm_seed and reuse_summary.exists() and reuse_runs.exists():
                print(f"Reusing completed LLM result for seed {seed}", flush=True)
                record["llm_assisted"] = load_json(reuse_summary)
                record["llm_metrics"] = extract_llm_metrics(reuse_runs)
                record["llm_result_source"] = str(reuse_dir)
            else:
                llm_results = results / "llm_assisted"
                llm_results.mkdir(parents=True, exist_ok=True)
                llm_script = base / "scripts" / "run_llm_assisted_adaptation.py"

                print(f"Starting GPT-oss on seed {seed}: 0/{args.count} (0.0%)", flush=True)
                start = time.time()

                # IMPORTANT: do not capture this subprocess; the LLM runner prints
                # per-system progress to the terminal.
                run_live([sys.executable, str(llm_script),
                          "--systems", str(systems),
                          "--requirements", str(req),
                          "--results", str(llm_results),
                          "--provider", args.provider,
                          "--model", args.model,
                          "--checkpoint", str(llm_results / "llm_assisted_adaptation_checkpoint.json"),
                          "--max-retries", str(args.max_retries),
                          "--base-delay", str(args.base_delay)])

                elapsed = time.time() - start
                print(f"GPT-oss seed {seed} completed: {args.count}/{args.count} (100.0%) | "
                      f"elapsed {elapsed/60:.1f} min", flush=True)

                record["llm_assisted"] = load_json(
                    llm_results/"llm_assisted_adaptation_summary.json"
                )
                record["llm_metrics"] = extract_llm_metrics(
                    llm_results/"llm_assisted_adaptation_runs.json"
                )
                record["llm_result_source"] = str(llm_results)

        (results/"multiseed_record.json").write_text(
            json.dumps(record, indent=2), encoding="utf-8"
        )
        per_seed.append(record)

    out = {"method": "paired multi-seed robustness evaluation",
           "seeds": args.seeds, "systems_per_seed": args.count, "per_seed": per_seed}

    out["deterministic_aggregate"] = {}
    for condition in ("FIXED_ORDER", "CHEAPEST_GREEDY", "AGENTIC"):
        out["deterministic_aggregate"][condition] = {}
        for metric in ("violations_before","violations_after","accepted_adaptation_steps",
                       "total_cost","total_complexity","new_failures_total"):
            values = [r["deterministic_conditions"][condition][metric] for r in per_seed]
            out["deterministic_aggregate"][condition][metric+"_mean"] = mean(values)
            out["deterministic_aggregate"][condition][metric+"_population_sd"] = (
                pstdev(values) if len(values) > 1 else 0.0
            )

    llm_records = [r["llm_metrics"] for r in per_seed if r.get("llm_metrics")]
    if llm_records:
        out["llm_aggregate"] = {"seeds_with_llm_results": len(llm_records)}
        for metric in ("accepted_adaptation_steps","total_cost","total_complexity","llm_calls","llm_failures"):
            values = [r[metric] for r in llm_records]
            out["llm_aggregate"][metric+"_mean"] = mean(values)
            out["llm_aggregate"][metric+"_population_sd"] = (
                pstdev(values) if len(values) > 1 else 0.0
            )

    out["guardrail"] = (
        "Synthetic multi-seed benchmark evidence only. Reused LLM results are explicitly "
        "marked by source. Report per-seed values and dispersion; do not treat this as legal "
        "compliance or proof of superiority on unseen systems."
    )
    path = results_root / "multiseed_summary.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    # Keep stdout machine-readable at the end for scripts/tests while progress remains visible.
    print(json.dumps(out, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
