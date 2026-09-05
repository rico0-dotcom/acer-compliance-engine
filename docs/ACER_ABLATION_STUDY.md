# ACER Ablation Study

This formalizes component attribution using the completed three-seed ACER experiments.

It does not rerun the benchmark or call the LLM.

Ablated contributions:
1. Adaptation-selection contribution: AGENTIC_NO_LLM vs FIXED_ORDER.
2. LLM-assistance contribution: AGENTIC_LLM vs AGENTIC_NO_LLM.

The analysis intentionally does not invent a pure LLM-only compliance condition. Such a condition was not evaluated and is therefore not included.

Outputs:
- `data/results/ablation_study/ablation_summary.json`
- `data/results/ablation_study/ablation_summary.md`
