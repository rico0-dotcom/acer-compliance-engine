# Adaptation Execution and Post-Verification

## Purpose

This layer closes the ACER remediation loop after compliance assessment and adaptation planning.

Current prototype flow:

`FAIL -> selected remediation -> isolated control overlay -> postcondition verification`

## Safety boundary

The default command is proposal-only and requires explicit approval. Even with `--approve-all`, the prototype **does not modify the benchmark's source system models**. It creates isolated control overlays and performs a controlled postcondition check.

Therefore a simulated `PASS` is **not** evidence of real system remediation and is not a claim of legal compliance.

## Commands

Default, approval-gated mode:

```powershell
python scripts\execute_compliance_adaptations.py
```

Prototype approved execution:

```powershell
python scripts\execute_compliance_adaptations.py --approve-all
```

Output:

`data/results/compliance_adaptation_execution.json`

## Research role

This creates the experimental scaffold needed for the eventual self-adaptive loop. A production-grade ACER executor should replace the isolated overlay with a versioned system/architecture-model mutation, rerun the existing deterministic assessor against the mutated model, capture actual evidence, and retain or roll back the adaptation according to verification results.
