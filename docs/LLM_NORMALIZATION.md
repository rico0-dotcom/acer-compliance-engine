# LLM candidate normalization

This layer converts fine-grained LLM candidates into requirement-family
suggestions for the current eight-item ACER baseline.

Run:

    python scripts\normalize_llm_candidates.py --prepare

Outputs:

    data\llm\llm_candidate_normalized.jsonl
    data\llm\llm_normalization_summary.json

The automatic mapping is intentionally conservative. A candidate can be a
valid EU AI Act obligation while still being `OUTSIDE_BASELINE` because the
current eight ACER requirements are only a selected task-specific subset.

`data\llm\llm_mapping_overrides.yaml` can record a reviewer decision without
editing the original LLM output.

This layer does not claim semantic equivalence, legal validity, or compliance.
Those require human validation and/or a separately specified semantic
evaluation protocol.
