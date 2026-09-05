# LLM-assisted regulatory requirement extraction

This layer introduces a reproducible experiment in which an LLM extracts
candidate machine-processable requirements from the pinned EU AI Act article
text. The existing deterministic ACER baseline remains untouched.

Workflow:

1. Prepare article prompts:
   `python scripts\run_llm_requirement_extraction.py --prepare-only`

2. Install the official OpenAI Python SDK:
   `python -m pip install openai`

3. Set `OPENAI_API_KEY` in the shell.

4. Run the extraction:
   `python scripts\run_llm_requirement_extraction.py --run`

5. Evaluate candidates against the curated eight-requirement baseline:
   `python scripts\run_llm_requirement_extraction.py --evaluate`

The API call uses the Responses API with Structured Outputs. The LLM produces
candidate requirements; it is not the final compliance oracle. Deterministic
model-based verification remains the decision layer.

Research limitation: exact provision/title matching is only an automated first
pass. Legal meaning, completeness, applicability and provenance must be
human-validated before reporting results as legal-performance claims.
