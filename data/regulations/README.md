# ACER regulatory source layer

This directory stores provenance and local snapshots for regulations used by ACER.

The current source is the official EUR-Lex consolidated English text of Regulation (EU) 2024/1689 (Artificial Intelligence Act), current version identified by EUR-Lex as 27 July 2026.

ACER does not treat the downloaded regulation as a legal interpretation. The ingestion layer only acquires source material, records its hash and extracts article-level text for traceability. Formal machine-processable requirements remain a curated research artifact and require human validation.

Run from the project root:

```powershell
python scripts\ingest_eu_ai_act.py
```

This creates/updates:

- `data/regulations/eu_ai_act_source.html` — local source snapshot
- `data/regulations/eu_ai_act_source_manifest.yaml` — source URL, CELEX/version, retrieval date, SHA-256
- `data/regulations/eu_ai_act_articles.yaml` — extracted article text for the selected provisions
- `data/requirements/eu_ai_act_traceability.yaml` — links the existing ACER requirements to source articles and extracted source text

The live EUR-Lex page is the authoritative source. The local snapshot is only a reproducibility artifact.
