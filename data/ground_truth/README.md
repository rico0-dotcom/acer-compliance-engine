# Independent Ground-Truth Evaluation

This directory stores labels authored independently of the ACER compliance checker.

## Principle

Do NOT derive `expected_status` by running ACER and copying its result. Each label must be decided from:
1. the regulatory requirement source/provenance;
2. the scenario/system model;
3. the stated applicability conditions.

The label set is a benchmark for ACER, not an output of ACER.

## Label values

- `PASS`: the modeled system satisfies the requirement.
- `FAIL`: the modeled system violates the requirement.
- `NOT_APPLICABLE`: the requirement does not apply to the modeled scenario.
- `UNCERTAIN`: available information is insufficient for a defensible label; exclude from accuracy metrics until adjudicated.

## Minimum fields

`scenario_id, requirement_id, expected_status, rationale, annotator, reviewed`

## Recommended adjudication

Use two independent labels where feasible. Record disagreements and resolve them before computing final metrics.

The EU AI Act requirement records in this project are structured, source-traceable engineering records; they are not a substitute for legal advice or formal legal validation.
