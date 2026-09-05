# ACER Multi-Seed Robustness Evaluation

Run the deterministic robustness evaluation first:

`python scripts/run_multiseed_adaptation_evaluation.py --seeds 20260904 20260905 20260906 --count 100`

The optional `--run-llm` mode runs GPT-oss on the same generated systems for every listed seed.
Because this is an expensive network experiment, use it only after the deterministic multi-seed
run is validated and credentials are available.

Report per-seed results and mean/dispersion. Three seeds provide robustness evidence but are not
enough to claim broad generalization or statistical significance by themselves.
