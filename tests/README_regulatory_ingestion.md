# Regulatory ingestion tests

These tests validate the local ingestion layer and provenance metadata without requiring a live EUR-Lex request.

The live acquisition command is:

```powershell
python scripts\ingest_eu_ai_act.py
```

The resulting source snapshot is not committed to the patch because it is downloaded from EUR-Lex at runtime. The manifest records the exact retrieval URL, consolidated version and SHA-256 hash for reproducibility.
