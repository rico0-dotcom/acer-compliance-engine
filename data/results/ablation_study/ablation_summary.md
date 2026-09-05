# ACER Component Ablation Study

Seeds: 20260904, 20260905, 20260906
Systems: 300 (100 per seed)

## Conditions

| Condition | Mean steps | Mean cost | Mean complexity |
|---|---:|---:|---:|
| FIXED_ORDER | 421.33 | 814.33 | 493.00 |
| AGENTIC_NO_LLM | 295.33 | 736.67 | 590.67 |
| AGENTIC_LLM | 377.00 | 725.67 | 448.67 |

## Attribution

- Agentic selection vs fixed-order: steps -29.91%, cost -9.54%, complexity 19.81%.
- Adding LLM assistance to agentic adaptation: steps 27.65%, cost -1.49%, complexity -24.04%.
- LLM calls: [376, 378, 377]; failures: [0, 0, 0].

## Interpretation guardrails

- Descriptive attribution only; no statistical significance claim.
- All final compliance decisions remain deterministic.
- Modeled cost/complexity are benchmark quantities.
- Synthetic benchmark evidence does not establish legal compliance or superiority on unseen systems.
- A pure LLM-only condition was not run and is not claimed.
