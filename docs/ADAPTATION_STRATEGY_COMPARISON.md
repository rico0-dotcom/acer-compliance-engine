# ACER Adaptation Strategy Comparison

This experiment compares three selection policies over the same ACER adaptation catalog and the same deterministic compliance assessor:

1. `FIXED_ORDER`: deterministic requirement-order remediation using the first improving tactic.
2. `CHEAPEST_GREEDY`: repeatedly choose the lowest-cost improving tactic that introduces no new failures.
3. `AGENTIC`: use the existing `ViolationDiagnoser`, `AdaptationGenerator`, `AdaptationEvaluator`, `AdaptationSelector`, and `AgenticOrchestrator`.

All three operate on isolated deep copies. None modifies the source benchmark YAML files.

The experiment measures violation reduction, final system compliance, accepted adaptation steps, cost, complexity, and new failures.

Interpretation: because all strategies share the same encoded adaptation catalog and deterministic assessor, this is an ablation of **selection/orchestration policy**, not a comparison of fundamentally different remediation knowledge. A result where all strategies reach zero violations is still useful: efficiency metrics such as adaptation steps, cost, and complexity become the differentiators. Generalization to unseen systems requires a separate benchmark.


## Interpretation note
The experiment is an ablation study, not a presumption that the agentic strategy must outperform simpler policies on every metric. The comparator reads agentic cost/complexity from its nested selected-candidate records, and the tests only require internally valid reported metrics and zero new failures. Strategy superiority must be established empirically on broader benchmarks.
