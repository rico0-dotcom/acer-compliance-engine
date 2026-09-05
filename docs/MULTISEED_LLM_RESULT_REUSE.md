# Multi-Seed GPT-oss Reuse and Live Progress

This version:
- reuses the completed 20260904 LLM result;
- runs GPT-oss only for the other requested seeds;
- leaves the LLM subprocess attached to the terminal so its per-system progress is visible;
- preserves a machine-readable final summary on disk.

Run:
`python scripts/run_multiseed_adaptation_evaluation.py --seeds 20260904 20260905 20260906 --count 100 --run-llm --reuse-llm-seed 20260904 --reuse-llm-results data/results/llm_randomized --provider digitalocean --model openai-gpt-oss-120b`
