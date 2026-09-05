# LLM Contribution Ablation

This experiment separates three effects on the same randomized benchmark:

1. Fixed deterministic remediation.
2. Cheapest-first greedy remediation.
3. Existing deterministic agentic multi-objective selection.

The optional `--run-llm` condition invokes the existing GPT-oss-assisted implementation, but only use it after confirming that implementation supports the same randomized-system input path. Compliance remains decided by the deterministic assessor.

The experiment must not claim that GPT-oss improves performance unless the LLM-assisted condition is run on the identical randomized dataset and its outputs are recorded separately.
