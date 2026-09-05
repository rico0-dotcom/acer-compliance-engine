# Live LLM Progress

The LLM-assisted runner prints per-system progress, completed LLM calls, elapsed-derived ETA, and percentage.
The multi-seed runner streams that output instead of hiding it inside captured subprocess output.
ETA is approximate because different systems require different numbers of LLM calls.
