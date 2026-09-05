# ACER Automated Compliance Assessment

This layer runs the deterministic ACER compliance engine over the system models and curated requirement corpus. It adds a traceable assessment artifact without replacing the existing benchmark evaluator.

## Evidence chain

Each check records:

`regulation → provision → ACER requirement → verification rule/parameters → system → evidence → verification status → remediation options`

The output keeps requirement provenance (`source_id`, URL, provision, retrieval date, validation status) alongside the engine's evidence and explanation.

## Run

```powershell
python scripts\run_compliance_assessment.py
```

Outputs are written to:

- `data/results/compliance_assessment_summary.json`
- `data/results/compliance_assessment_trace.csv`
- `data/results/compliance_assessment_trace.jsonl`
- `data/results/compliance_assessment_reports.json`

## Interpretation boundary

This is an engineering verification layer over the current ACER formalization. A PASS means that the encoded requirement rule is satisfied by the encoded system model. A FAIL means the encoded rule is not satisfied. An N/A/NOT_APPLICABLE status, where supported by the current engine, means the requirement condition is not active for that system.

The layer does not establish legal compliance independently of the correctness, completeness, applicability assumptions, and validation status of the requirement corpus and system model.
