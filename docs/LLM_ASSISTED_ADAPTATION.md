# LLM-Assisted Adaptation

This layer connects the DigitalOcean GPT-oss model to ACER's adaptation loop without giving the model authority to decide compliance or directly mutate system models.

Flow:

`FAIL -> LLM ranks allowed action IDs -> deterministic candidate evaluation -> selector -> isolated model mutation -> deterministic re-assessment -> repeat`

The LLM receives the current failed requirement IDs and a constrained action catalog. It may only return IDs already present in the catalog. It can provide a rationale and priority, but executable mutation semantics remain in ACER's code.

The deterministic `AdaptationEvaluator` applies each selected candidate to an isolated deep copy and reruns the existing assessor. The selector accepts only strict improvements with no new failures.

Outputs:

- `data/results/llm_assisted_adaptation_runs.json`
- `data/results/llm_assisted_adaptation_summary.json`

This is an LLM-assisted research prototype. It does not establish legal compliance. The LLM is not a compliance oracle and cannot directly change source YAML models.
