# LLM provider setup

The same extraction experiment can run with OpenAI, DigitalOcean Serverless Inference, or a local Ollama model.

## Prepare

    python scripts\run_llm_requirement_extraction.py --prepare-only

## DigitalOcean

Set a DigitalOcean model access credential and choose an account-available model:

    $env:DIGITALOCEAN_TOKEN="YOUR_TOKEN"
    $env:ACER_LLM_MODEL="MODEL_ID"

List available models:

    python scripts\run_llm_requirement_extraction.py --provider digitalocean --list-models

Run:

    python scripts\run_llm_requirement_extraction.py --provider digitalocean --run

DigitalOcean Serverless Inference uses `https://inference.do-ai.run/v1` and OpenAI-compatible text endpoints.

## Ollama

Install Ollama, pull a local model, then set its name:

    ollama pull <model>
    $env:ACER_LLM_MODEL="<model>"
    python scripts\run_llm_requirement_extraction.py --provider ollama --run

Ollama's OpenAI-compatible local endpoint is `http://localhost:11434/v1`; no cloud API key is required for local access.

## OpenAI

    $env:OPENAI_API_KEY="YOUR_KEY"
    $env:ACER_LLM_MODEL="<model>"
    python scripts\run_llm_requirement_extraction.py --provider openai --run

## Evaluation

After a run:

    python scripts\run_llm_requirement_extraction.py --evaluate

The deterministic ACER baseline, benchmark and ground truth are not modified.
