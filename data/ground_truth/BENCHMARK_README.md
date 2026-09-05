# Balanced EU AI Act Benchmark

This benchmark is separate from the ACER checker.

`eu_ai_act_benchmark_spec.yaml` defines the intended scenario conditions.
`generate_ai_act_benchmark.py` turns those conditions into system models and
writes the independently authored expected status for every requirement.

The benchmark deliberately includes:
- compliant cases;
- single-violation cases;
- multi-violation cases;
- applicability / NOT_APPLICABLE cases.

Do not use ACER's `baseline_status` to populate the expected labels.
The labels in `eu_ai_act_ground_truth.csv` come from the benchmark specification.

For stronger research validity, the next stage should have a second annotator
review these labels and record disagreements before final reporting.

