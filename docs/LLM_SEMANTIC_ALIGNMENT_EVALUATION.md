# LLM Semantic Alignment Evaluation

This layer evaluates the reviewed LLM regulatory candidates without relying on exact text matching.

## Inputs

- `data/llm/llm_requirement_human_annotations_reviewed.csv`
- `data/llm/llm_candidate_normalized.jsonl`

## Measures

- EXACT_MATCH / PARTIAL_MATCH / OTHER distribution
- supported-candidate rate
- exact-match rate
- baseline requirement-family coverage
- obligation, applicability, machine-constraint and provenance correctness
- deterministic normalization family counts
- agreement between deterministic family suggestions and reviewer-assigned requirement IDs where both exist

## Run

```powershell
python scripts\evaluate_llm_semantic_alignment.py
```

The result is written to:

`data/llm/llm_semantic_alignment_evaluation.json`

## Interpretation

`OTHER` is not a legal-error label. It means the reviewer did not map that candidate to the current eight-item ACER reference set.

The normalization layer is a controlled family-grouping mechanism. Its output must not be presented as proof that two provisions are legally equivalent or that a system is compliant.

The current metrics are based on one reviewer (`ACER_review_v1`). A later independent second review should be used to assess inter-reviewer agreement and to adjudicate disagreements before treating the labels as stronger research ground truth.
