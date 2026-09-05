# ACER Agentic Adaptation Loop

This layer implements a research prototype for model-level self-adaptation.

Flow:

`FAIL -> diagnosis -> candidate generation -> isolated model mutation -> deterministic re-assessment -> multi-objective selection -> repeat`

The implementation separates five roles:

- ViolationDiagnoser: identifies current failing requirements.
- AdaptationGenerator: proposes engineering actions applicable to those failures.
- AdaptationEvaluator: applies each candidate to an isolated deep copy and reruns the ACER deterministic assessor.
- AdaptationSelector: selects an action only when it strictly reduces violations without introducing new failures, then scores compliance gain against cost and complexity.
- AgenticOrchestrator: repeats the loop, stopping on compliance, cycle detection, or lack of strict improvement.

The source YAML models are never overwritten. Adaptations are applied to in-memory copies and retained in `data/results/agentic_adaptation_runs.json` for inspection.

The post-adaptation `PASS` results are benchmark/model-level verification results. They are not evidence of real-world legal compliance. Production execution would require validated model-to-system mutation, safety constraints, human authorization policies, rollback, and verification over the deployed system.
