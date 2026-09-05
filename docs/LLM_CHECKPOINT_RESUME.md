# LLM checkpoint / resume and transient retry

The LLM-assisted runner now checkpoints each completed system to
`llm_assisted_adaptation_checkpoint.json` and skips only records with zero LLM failures.
Records that failed due to a provider error are recomputed on resume.

Transient provider errors such as HTTP 429/rate-limit/overload, API connection errors, and
API timeouts use exponential backoff. The deterministic ACER assessor remains the final
verification gate.

The multi-seed runner passes a per-seed checkpoint path automatically.
