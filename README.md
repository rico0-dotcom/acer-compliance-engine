# ACER: AI Compliance & Regulatory Adaptation Engine

A research prototype for automated compliance assessment and self-adaptation of AI systems against regulatory requirements, using the EU AI Act as the primary case study.

## Overview

This repository contains an experimental compliance-engineering framework that explores how AI and agentic techniques can support:

1. Regulatory requirement extraction and structuring
2. Traceable compliance assessment of candidate AI systems
3. Rule-based adaptation planning
4. Agentic self-adaptation of non-compliant systems
5. LLM-assisted proposal/ranking of candidate adaptation actions
6. Deterministic post-adaptation verification

The prototype is deliberately designed so that the LLM does **not** directly modify system models or declare compliance. The LLM is restricted to proposing or ranking candidate actions, while deterministic rules perform the mutation and retain final PASS/FAIL decision authority.

> **Research prototype disclaimer:** This repository is an experimental engineering/research prototype and is not a legal-compliance tool. The encoded requirements represent a curated subset of the EU AI Act used for experimentation and do not constitute legal advice or a complete implementation of the Act.

## Research Motivation

Modern AI systems increasingly operate in environments where regulatory requirements are complex, evolving, and difficult to verify manually. This project investigates whether compliance checking and adaptation can be engineered as an automated system while preserving traceability, auditability, verifiability, and human control.

The project was developed as a practical exploration of the question:

> How can intelligent systems reason over regulatory requirements and adapt candidate AI systems while retaining deterministic, auditable control over compliance decisions?

## Current Architecture

The prototype is organized around the following stages:

```text
EU AI Act source
      |
      v
Requirement extraction / curation
      |
      v
Structured regulatory requirements
      |
      v
Deterministic compliance assessment
      |
      v
Violations
      |
      +--------------------+
      |                    |
      v                    v
Rule-based planning    Agentic adaptation
                           |
                           v
                    LLM-assisted proposal
                           |
                           v
                 Deterministic action execution
                           |
                           v
                 Deterministic re-assessment
```

## Regulatory Scope

The current baseline contains eight curated requirement families derived from selected EU AI Act provisions:

- **EUAI-R9-01** — Risk management system
- **EUAI-R10-01** — Data governance and management practices
- **EUAI-R12-01** — Automatic event logging
- **EUAI-R13-01** — Transparency and interpretability for deployers
- **EUAI-R14-01** — Human oversight
- **EUAI-R14-02** — Human intervention / control
- **EUAI-R15-01** — Accuracy, robustness and cybersecurity
- **EUAI-R50-01** — Transparency notice

The curated baseline is explicitly marked as human-validated and linked to official EUR-Lex provenance in the project data files.

## Experimental Results

### Deterministic / Agentic Adaptation Benchmark

A three-seed benchmark was conducted over **300 synthetic systems**.

Compared with the fixed-order baseline:

- Agentic adaptation reduced the number of adaptation steps by **29.9%**
- Agentic adaptation reduced adaptation cost by **9.5%**
- All benchmark violations were resolved under the encoded requirements

### LLM-Assisted Adaptation

The LLM-assisted variant was evaluated under the same three-seed setup.

Compared with the non-LLM agentic condition:

- Adaptation complexity was reduced by **24.0%**
- The LLM-assisted system completed the benchmark with **0 LLM failures**
- The LLM was restricted to candidate-action proposal/ranking
- Deterministic assessment remained the final authority for compliance decisions

The detailed multi-seed outputs are stored under the `data/results/` directory.

### LLM-Assisted Multi-Seed Runs

The three completed seeds produced:

| Seed | LLM steps | Adaptation cost | Complexity | LLM calls | LLM failures |
|---|---:|---:|---:|---:|---:|
| 20260904 | 376 | 726 | 451 | 376 | 0 |
| 20260905 | 378 | 731 | 449 | 378 | 0 |
| 20260906 | 377 | 720 | 446 | 377 | 0 |
| **Mean** | **377.0** | **725.7** | **448.7** | **377.0** | **0** |

### Deterministic Three-Seed Comparison

Across the same three seeds:

| Condition | Mean steps | Mean cost | Mean complexity |
|---|---:|---:|---:|
| Fixed-order baseline | 421.3 | 814.3 | 493.0 |
| Agentic, no LLM | 295.3 | 736.7 | 590.7 |
| Agentic + LLM | 377.0 | 725.7 | 448.7 |

Observed relative changes:

- **Agentic vs fixed-order:** steps **-29.9%**, cost **-9.5%**
- **LLM-assisted vs agentic without LLM:** steps **+27.7%**, cost **-1.5%**, complexity **-24.0%**

These are descriptive benchmark results on synthetic systems. They should not be interpreted as statistically validated claims about general real-world performance.

## Human Review Status

The regulatory extraction component has undergone an **initial human review** using a structured annotation process.

An **independent second human review is currently ongoing**.

The current project should therefore be understood as an evolving research prototype rather than a finalized benchmark of regulatory-requirement extraction quality.

## Important Methodological Boundary

The project intentionally separates:

**LLM / agentic reasoning**
- proposing candidate adaptation actions
- ranking candidate actions

from:

**deterministic control**
- applying approved candidate actions in an isolated copy
- re-running compliance assessment
- determining PASS/FAIL
- verifying that source system models are not persistently modified

This boundary is central to the prototype's focus on auditability, verifiability, and controllability.

## Repository Structure

A typical repository layout is:

```text
acer-compliance-engine/
├── data/
│   ├── regulations/
│   ├── requirements/
│   ├── systems/
│   ├── llm/
│   └── results/
├── scripts/
├── src/                  # if/when core modules are organized here
├── tests/
├── notebooks/
├── README.md
└── requirements.txt
```

Keep generated experiment outputs under `data/results/` so that benchmark artifacts remain separate from source code.

## Reproducibility

The repository is intended to make the experiments reproducible from the stored:

- requirement definitions
- synthetic system definitions
- experiment scripts
- benchmark outputs
- statistical evaluation files
- ablation-study outputs

Randomized experiments should be run with explicit seeds.

## External Model Provider

The LLM-assisted experiments were run using `openai-gpt-oss-120b` through a DigitalOcean-hosted API.

**Do not commit API keys, `.env` files, virtual environments, or other credentials to GitHub.**

Environment variables should be used for secrets, for example:

```powershell
$env:DIGITALOCEAN_TOKEN="YOUR_TOKEN"
```

Never replace `YOUR_TOKEN` with a real credential in the repository.

## What Should Not Be Committed

Do **not** push the following:

```text
.venv/
venv/
__pycache__/
*.pyc
.env
.env.*
*.pem
*.key
secrets/
```

Also exclude large temporary/cache files that are not required for reproduction.

## Research Limitations

This work has several deliberate limitations:

- The regulatory baseline covers only a curated subset of EU AI Act requirements.
- Regulatory extraction is an experimental component and is still under independent second review.
- The benchmark systems are synthetic rather than production AI systems.
- The results demonstrate behavior within the encoded benchmark and do not establish legal compliance.
- LLM-assisted insight/proposal components remain experimental.
- Real-world deployment would require stronger validation, governance, security controls, and legal review.

## Project Status

**Status: Active research prototype**

Implemented components include:

- traceable compliance assessment
- rule-based adaptation planning
- agentic self-adaptation
- LLM-assisted action proposal/ranking
- deterministic post-adaptation verification
- three-seed adaptation benchmark
- component ablation study
- statistical/descriptive evaluation
- initial human review of regulatory extraction
- independent second human review **ongoing**

## Suggested Citation / Attribution

If this repository is used as part of an application, research discussion, or demonstration, describe it as an experimental prototype for automated compliance engineering and self-adaptive AI systems rather than as a production compliance product.

## Author

**Anuj Pal**

This repository was developed as an independent research prototype to explore automated regulatory compliance engineering, agentic self-adaptation, and controlled LLM-assisted decision support.
