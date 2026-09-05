
from __future__ import annotations
import argparse, json
from pathlib import Path
from statistics import mean, median, pstdev

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def paired_stats(a, b):
    diffs = [x - y for x, y in zip(a, b)]
    return {
        "n": len(diffs),
        "mean_difference": mean(diffs) if diffs else 0.0,
        "median_difference": median(diffs) if diffs else 0.0,
        "population_sd_difference": pstdev(diffs) if len(diffs) > 1 else 0.0,
        "mean_absolute_difference": mean([abs(x) for x in diffs]) if diffs else 0.0,
        "direction_counts": {
            "a_greater": sum(x > 0 for x in diffs),
            "equal": sum(x == 0 for x in diffs),
            "b_greater": sum(x < 0 for x in diffs),
        },
    }

def change_rate(old, new):
    return None if old == 0 else (new - old) / old

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/results/adaptation_multiseed/multiseed_summary.json")
    ap.add_argument("--output", default="data/results/adaptation_multiseed/statistical_evaluation.json")
    args = ap.parse_args()

    base = Path(__file__).resolve().parents[1]
    data = load_json((base / args.input).resolve())
    rows = data["per_seed"]
    seeds = data["seeds"]

    def det(cond, metric):
        return [r["deterministic_conditions"][cond][metric] for r in rows]

    fs = det("FIXED_ORDER","accepted_adaptation_steps")
    fc = det("FIXED_ORDER","total_cost")
    fx = det("FIXED_ORDER","total_complexity")
    as_ = det("AGENTIC","accepted_adaptation_steps")
    ac = det("AGENTIC","total_cost")
    ax = det("AGENTIC","total_complexity")

    result = {
        "method": "paired descriptive statistical evaluation over saved multi-seed ACER results",
        "seeds": seeds,
        "systems_per_seed": data["systems_per_seed"],
        "total_systems": len(seeds) * data["systems_per_seed"],
        "AGENTIC_vs_FIXED_ORDER": {
            "steps": paired_stats(as_, fs),
            "cost": paired_stats(ac, fc),
            "complexity": paired_stats(ax, fx),
            "mean_step_change_rate": change_rate(mean(fs), mean(as_)),
            "mean_cost_change_rate": change_rate(mean(fc), mean(ac)),
            "mean_complexity_change_rate": change_rate(mean(fx), mean(ax)),
        },
        "seed_values": {
            "FIXED_ORDER": {"steps": fs, "cost": fc, "complexity": fx},
            "AGENTIC": {"steps": as_, "cost": ac, "complexity": ax},
        },
        "guardrails": [
            "Descriptive paired analysis over three seeds; no statistical significance claim is made.",
            "Modeled cost and complexity are benchmark quantities, not measured real-world engineering cost or complexity.",
            "All compliance outcomes remain determined by the deterministic ACER assessor.",
            "Synthetic benchmark evidence does not establish legal compliance or superiority on unseen systems."
        ]
    }

    llm = [r.get("llm_metrics") for r in rows]
    if all(llm):
        ls = [x["accepted_adaptation_steps"] for x in llm]
        lc = [x["total_cost"] for x in llm]
        lx = [x["total_complexity"] for x in llm]
        result["AGENTIC_NO_LLM_vs_AGENTIC_LLM"] = {
            "steps": paired_stats(as_, ls),
            "cost": paired_stats(ac, lc),
            "complexity": paired_stats(ax, lx),
            "mean_step_change_rate": change_rate(mean(as_), mean(ls)),
            "mean_cost_change_rate": change_rate(mean(ac), mean(lc)),
            "mean_complexity_change_rate": change_rate(mean(ax), mean(lx)),
            "llm_calls": [x["llm_calls"] for x in llm],
            "llm_failures": [x["llm_failures"] for x in llm],
        }

    out = (base / args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    raise SystemExit(main())
