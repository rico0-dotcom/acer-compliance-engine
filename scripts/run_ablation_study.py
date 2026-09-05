from __future__ import annotations
import json
from pathlib import Path
from statistics import mean, pstdev

BASE = Path(__file__).resolve().parents[1]
THREE = BASE / "data/results/adaptation_multiseed/statistical_evaluation_three_way.json"
OUT = BASE / "data/results/ablation_study/ablation_summary.json"
MD = BASE / "data/results/ablation_study/ablation_summary.md"


def paired(a, b):
    d = [x - y for x, y in zip(a, b)]
    return {
        "n": len(d),
        "mean_difference": mean(d),
        "population_sd_difference": pstdev(d) if len(d) > 1 else 0.0,
        "mean_absolute_difference": mean(abs(x) for x in d),
        "direction_counts": {
            "a_greater": sum(x > 0 for x in d),
            "equal": sum(x == 0 for x in d),
            "b_greater": sum(x < 0 for x in d),
        },
    }


def pct(new, old):
    return (new - old) / old if old else None


def main():
    if not THREE.exists():
        raise FileNotFoundError(f"Missing completed three-way results: {THREE}")

    data = json.loads(THREE.read_text(encoding="utf-8"))
    seeds = data["seeds"]
    sv = data["seed_values"]

    fixed_steps = sv["FIXED_ORDER"]["steps"]
    fixed_cost = sv["FIXED_ORDER"]["cost"]
    fixed_complexity = sv["FIXED_ORDER"]["complexity"]

    agentic_steps = sv["AGENTIC"]["steps"]
    agentic_cost = sv["AGENTIC"]["cost"]
    agentic_complexity = sv["AGENTIC"]["complexity"]

    llm_steps = sv["AGENTIC_LLM"]["steps"]
    llm_cost = sv["AGENTIC_LLM"]["cost"]
    llm_complexity = sv["AGENTIC_LLM"]["complexity"]
    llm_calls = sv["AGENTIC_LLM"]["llm_calls"]
    llm_failures = sv["AGENTIC_LLM"]["llm_failures"]

    ablation = {
        "method": "component attribution ablation over completed three-seed ACER experiments",
        "seeds": seeds,
        "systems_per_seed": data["systems_per_seed"],
        "total_systems": data["total_systems"],
        "conditions": {
            "FIXED_ORDER": {
                "description": "Baseline fixed-order remediation policy.",
                "steps": fixed_steps,
                "cost": fixed_cost,
                "complexity": fixed_complexity,
            },
            "AGENTIC_NO_LLM": {
                "description": "Deterministic multi-objective agentic adaptation without external LLM assistance.",
                "steps": agentic_steps,
                "cost": agentic_cost,
                "complexity": agentic_complexity,
            },
            "AGENTIC_LLM": {
                "description": "Agentic adaptation with GPT-oss proposal assistance and deterministic post-verification.",
                "steps": llm_steps,
                "cost": llm_cost,
                "complexity": llm_complexity,
                "llm_calls": llm_calls,
                "llm_failures": llm_failures,
            },
        },
        "ablations": {
            "agentic_selection_contribution": {
                "comparison": "AGENTIC_NO_LLM_vs_FIXED_ORDER",
                "steps": paired(agentic_steps, fixed_steps),
                "cost": paired(agentic_cost, fixed_cost),
                "complexity": paired(agentic_complexity, fixed_complexity),
                "mean_relative_change": {
                    "steps": pct(mean(agentic_steps), mean(fixed_steps)),
                    "cost": pct(mean(agentic_cost), mean(fixed_cost)),
                    "complexity": pct(mean(agentic_complexity), mean(fixed_complexity)),
                },
            },
            "llm_assistance_contribution": {
                "comparison": "AGENTIC_LLM_vs_AGENTIC_NO_LLM",
                "steps": paired(llm_steps, agentic_steps),
                "cost": paired(llm_cost, agentic_cost),
                "complexity": paired(llm_complexity, agentic_complexity),
                "mean_relative_change": {
                    "steps": pct(mean(llm_steps), mean(agentic_steps)),
                    "cost": pct(mean(llm_cost), mean(agentic_cost)),
                    "complexity": pct(mean(llm_complexity), mean(agentic_complexity)),
                },
            },
        },
        "compliance_control": {
            "all_conditions_share_deterministic_assessment": True,
            "llm_failures_by_seed": llm_failures,
        },
        "limitations": [
            "This ablation uses the completed three-seed randomized experiments; no new LLM calls are made.",
            "Only the implemented components are ablated: adaptation selection policy and LLM assistance.",
            "A pure LLM-only compliance oracle was not evaluated and therefore is not claimed to be a valid ablation.",
            "Modeled cost and complexity are benchmark quantities rather than measured real-world engineering cost or complexity.",
            "Three seeds support descriptive attribution but not statistical significance claims.",
            "The benchmark is synthetic and does not establish legal compliance or superiority on unseen systems.",
        ],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(ablation, indent=2), encoding="utf-8")

    md = [
        "# ACER Component Ablation Study",
        "",
        f"Seeds: {', '.join(map(str, seeds))}",
        f"Systems: {data['total_systems']} ({data['systems_per_seed']} per seed)",
        "",
        "## Conditions",
        "",
        "| Condition | Mean steps | Mean cost | Mean complexity |",
        "|---|---:|---:|---:|",
        f"| FIXED_ORDER | {mean(fixed_steps):.2f} | {mean(fixed_cost):.2f} | {mean(fixed_complexity):.2f} |",
        f"| AGENTIC_NO_LLM | {mean(agentic_steps):.2f} | {mean(agentic_cost):.2f} | {mean(agentic_complexity):.2f} |",
        f"| AGENTIC_LLM | {mean(llm_steps):.2f} | {mean(llm_cost):.2f} | {mean(llm_complexity):.2f} |",
        "",
        "## Attribution",
        "",
        f"- Agentic selection vs fixed-order: steps {pct(mean(agentic_steps), mean(fixed_steps))*100:.2f}%, cost {pct(mean(agentic_cost), mean(fixed_cost))*100:.2f}%, complexity {pct(mean(agentic_complexity), mean(fixed_complexity))*100:.2f}%.",
        f"- Adding LLM assistance to agentic adaptation: steps {pct(mean(llm_steps), mean(agentic_steps))*100:.2f}%, cost {pct(mean(llm_cost), mean(agentic_cost))*100:.2f}%, complexity {pct(mean(llm_complexity), mean(agentic_complexity))*100:.2f}%.",
        f"- LLM calls: {llm_calls}; failures: {llm_failures}.",
        "",
        "## Interpretation guardrails",
        "",
        "- Descriptive attribution only; no statistical significance claim.",
        "- All final compliance decisions remain deterministic.",
        "- Modeled cost/complexity are benchmark quantities.",
        "- Synthetic benchmark evidence does not establish legal compliance or superiority on unseen systems.",
        "- A pure LLM-only condition was not run and is not claimed.",
    ]
    MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(ablation, indent=2))


if __name__ == "__main__":
    main()
