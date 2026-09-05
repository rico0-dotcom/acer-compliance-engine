# ACER Compliance Adaptation Planning

This layer consumes deterministic ACER assessment failures and generates ranked remediation proposals.

Flow:

`FAIL -> violation diagnosis -> candidate adaptations -> ranking -> human gate -> post-adaptation verification`

The current implementation is intentionally **proposal-only**. It never edits a system model, applies a configuration change, or claims that a proposed action restores legal compliance.

Each plan preserves the assessment trace ID, requirement, provision, explanation, and evidence. Candidate actions are ranked using a simple deterministic heuristic that prefers lower estimated engineering impact and can boost actions whose control type matches the failure explanation.

Outputs:

- `data/results/compliance_adaptation_plans.json`
- `data/results/compliance_adaptation_summary.json`

This is an engineering adaptation-planning artifact. Legal equivalence, remediation effectiveness, and safe autonomous execution require separate validation.
