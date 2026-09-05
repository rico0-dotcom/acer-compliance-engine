# Human-reviewed LLM extraction evaluation

The existing exact-string evaluator is only a sanity check. This layer creates
a reviewable annotation CSV for all LLM candidates and computes multidimensional
extraction metrics.

Run:

    python scripts\prepare_llm_human_evaluation.py --prepare

Review:

    data\llm\llm_requirement_human_annotations.csv

For each candidate, assign:
- relevance: EXACT_MATCH / PARTIAL_MATCH / UNSUPPORTED / DUPLICATE / OTHER
- matched_requirement_id when an ACER baseline requirement is supported
- obligation_correct: YES / PARTIAL / NO
- applicability_correct: YES / PARTIAL / NO / NOT_APPLICABLE
- machine_constraint_correct: YES / PARTIAL / NO
- provenance_correct: YES / NO

Then run:

    python scripts\prepare_llm_human_evaluation.py --evaluate

Output:

    data\llm\llm_human_evaluation_summary.json

The eight-item ACER requirement set is a task-specific reference, not a claim
of complete coverage of the EU AI Act. Extra candidates may be valid. Human
review is required before interpreting extraction quality.
