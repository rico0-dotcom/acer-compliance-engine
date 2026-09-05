# Benchmark prediction evaluation

This runner evaluates ACER's existing deterministic baseline assessor on the
balanced EU AI Act benchmark.

It does not use adaptation when producing these predictions. This isolates
whether ACER correctly identifies requirement satisfaction.

Independent benchmark labels remain in:
data/ground_truth/eu_ai_act_ground_truth.csv

Predictions are written to:
data/results/benchmark_predictions.csv

Summary is written to:
data/results/benchmark_prediction_summary.json
