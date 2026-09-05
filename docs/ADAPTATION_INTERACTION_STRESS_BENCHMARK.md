# ACER Adaptation Interaction Stress Benchmark

This benchmark is a synthetic extension of the existing 21-system ACER benchmark. It uses the same eight curated requirements and the same deterministic assessor, but deliberately creates multi-violation systems so adaptation strategies must handle interacting repair choices.

The benchmark includes joint tactics that can repair multiple requirement families in one model-level mutation:

- risk management + data governance
- logging + performance monitoring
- transparency mechanism + direct-interaction notice
- human oversight + intervention path

The experiment compares three policies over the same tactic catalog and the same deterministic verifier: `FIXED_ORDER`, `CHEAPEST_GREEDY`, and `AGENTIC`.

The agentic policy scores verified compliance gain, direct target satisfaction, adaptation cost, complexity, and new-failure avoidance. All candidate changes are applied to isolated model copies and are accepted only after re-assessment.

This benchmark is intentionally synthetic. A favorable result demonstrates an advantage on the designed interaction cases, not legal compliance or generalization to unseen systems.


## Ground-truth construction

Each generated stress system is initialized so that exactly the requirement families listed for that scenario are failing; all other baseline controls are present. The 12 scenarios therefore contain 37 initial requirement-level failures in total (the sum of the declared scenario target sets). This avoids the earlier fixture error where every scenario lacked all eight controls and produced 96 failures.
