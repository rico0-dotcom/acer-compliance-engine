# ACER Research Data Protocol

## Goal

Keep regulatory interpretation, architecture modeling, ground truth, and
generated model outputs as separate evidence layers.

## Requirement record

Each regulatory requirement must retain:
- regulation and provision
- concise obligation representation
- applicability condition
- machine-checkable rule
- expected evidence
- possible adaptation tactics
- source URL/identifier
- retrieval date
- validation status

## Validation

A requirement is not considered research-grounded until it has been checked
against the authoritative source and marked HUMAN_VALIDATED or EXPERT_VALIDATED.

## Ground truth

Ground truth must be authored independently from the LLM and from the
prediction produced by ACER.

## Copyright / reproducibility

Store source identifiers and URLs plus concise paraphrases in the repository.
Keep downloaded source documents separately and follow their reuse terms.
