from __future__ import annotations

import argparse
import json
import os
import sys
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from app.engine import assess
from app.loaders import load_requirements, load_system
from app.models import SystemModel
from scripts.run_agentic_adaptation_loop import ACTION_CATALOG, AdaptationEvaluator, AdaptationSelector, model_hash

DEFAULT_SYSTEM_DIR = BASE / "data" / "systems" / "eu_ai_act_benchmark"
DEFAULT_REQUIREMENTS = BASE / "data" / "requirements" / "eu_ai_act_core.yaml"
DEFAULT_RESULTS = BASE / "data" / "results"

LLM_SYSTEM_PROMPT = """You are the adaptation-planning agent in ACER (Autonomous Compliance Engineering and Remediation).
You do NOT determine legal compliance. A deterministic verifier does that.
Given current failed ACER requirement IDs and a SAFE ACTION CATALOG, rank/select executable action IDs.
You may only return action IDs present in the catalog. Do not invent executable actions.
Prefer actions that can repair multiple current failures, avoid unnecessary complexity, and preserve human oversight.
Return ONLY valid JSON:
{"recommendations":[{"action_id":"...","targets":["EUAI-R..-.."],"priority":1,"rationale":"..."}]}
"""


def provider_config(provider: str) -> tuple[str | None, str, str]:
    if provider == "openai":
        return os.getenv("OPENAI_API_KEY"), os.getenv("ACER_OPENAI_BASE_URL", "https://api.openai.com/v1"), os.getenv("ACER_LLM_MODEL", "gpt-5-mini")
    if provider == "digitalocean":
        return os.getenv("DIGITALOCEAN_TOKEN") or os.getenv("DIGITALOCEAN_INFERENCE_KEY"), os.getenv("ACER_DO_BASE_URL", "https://inference.do-ai.run/v1"), os.getenv("ACER_LLM_MODEL", "")
    if provider == "ollama":
        return os.getenv("OLLAMA_API_KEY", "ollama"), os.getenv("ACER_OLLAMA_BASE_URL", "http://localhost:11434/v1"), os.getenv("ACER_LLM_MODEL", "")
    raise ValueError(f"Unknown provider: {provider}")


def call_llm(provider: str, model: str, failed: list[str], catalog: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai package is not installed in the active environment") from exc
    api_key, base_url, env_model = provider_config(provider)
    model = model or env_model
    if not api_key:
        raise RuntimeError(f"No credential configured for {provider}")
    if not model:
        raise RuntimeError(f"No model configured for {provider}")

    allowed: dict[str, dict[str, Any]] = {}
    for req in failed:
        for action in catalog.get(req, []):
            allowed[action["id"]] = {
                "id": action["id"],
                "title": action["title"],
                "cost": action["cost"],
                "complexity": action["complexity"],
            }
    user_payload = {
        "failed_requirements": failed,
        "allowed_actions": list(allowed.values()),
        "instruction": "Rank the useful allowed action IDs. An action may target more than one failed requirement when its semantics support that bundle. Do not return IDs outside allowed_actions.",
    }
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": LLM_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
        temperature=0,
    )
    content = response.choices[0].message.content
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"LLM returned invalid JSON: {exc}") from exc
    if not isinstance(parsed, dict) or not isinstance(parsed.get("recommendations"), list):
        raise RuntimeError("LLM output does not match the expected schema")
    return {"provider": provider, "model": model, "response": parsed, "allowed_action_ids": sorted(allowed)}


def build_llm_candidates(llm_result: dict[str, Any], failed: list[str]) -> list[dict[str, Any]]:
    allowed = set(llm_result["allowed_action_ids"])
    recommendations = llm_result["response"].get("recommendations", [])
    action_lookup = {a["id"]: a for req in failed for a in ACTION_CATALOG.get(req, [])}
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for rec in recommendations:
        if not isinstance(rec, dict):
            continue
        action_id = rec.get("action_id")
        if action_id not in allowed or action_id in seen:
            continue
        action = action_lookup[action_id]
        # LLM cannot alter executable targets. Targets are intersection with actual failures.
        llm_targets = [r for r in rec.get("targets", []) if r in failed]
        catalog_targets = [r for r in failed if any(a["id"] == action_id for a in ACTION_CATALOG.get(r, []))]
        targets = llm_targets or catalog_targets
        candidates.append({
            **action,
            "targets": targets,
            "llm_priority": rec.get("priority"),
            "llm_rationale": str(rec.get("rationale", "")),
        })
        seen.add(action_id)
    return candidates


class LLMAssistedGenerator:
    def __init__(self, provider: str, model: str):
        self.provider = provider
        self.model = model

    def generate(self, failed: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        result = call_llm(self.provider, self.model, failed, ACTION_CATALOG)
        candidates = build_llm_candidates(result, failed)
        return candidates, result


def save_checkpoint(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def load_checkpoint(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def is_resume_complete(record: dict[str, Any]) -> bool:
    return int(record.get("llm_failures", 0)) == 0


def generate_with_retry(generator: LLMAssistedGenerator, failed: list[str], max_retries: int, base_delay: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    attempt = 0
    while True:
        try:
            return generator.generate(failed)
        except Exception as exc:
            transient = exc.__class__.__name__ in {"RateLimitError", "APIConnectionError", "APITimeoutError"} or "429" in str(exc) or "overloaded" in str(exc).lower()
            if not transient or attempt >= max_retries:
                raise
            delay = base_delay * (2 ** attempt)
            print(f"LLM transient error ({exc.__class__.__name__}); retrying in {delay:.1f}s [attempt {attempt + 1}/{max_retries}]", flush=True)
            time.sleep(delay)
            attempt += 1


def run_all(system_dir: Path, requirements_path: Path, results_dir: Path, provider: str, model: str, max_steps: int, checkpoint_path: Path | None = None, max_retries: int = 6, base_delay: float = 5.0) -> dict[str, Any]:
    requirements = load_requirements(requirements_path)
    # Accept both the original 21-system benchmark and the randomized benchmark.
    # The randomized dataset uses ai-act-random-stress-*.yaml; the original uses
    # ai-act-benchmark-*.yaml. Exclude MANIFEST.yaml and require YAML files.
    system_paths = sorted(
        p for p in system_dir.glob("*.yaml")
        if p.name != "MANIFEST.yaml"
        and (p.name.startswith("ai-act-benchmark-") or p.name.startswith("ai-act-random-stress-"))
    )
    if not system_paths:
        raise SystemExit(
            f"No ACER system YAML files found in {system_dir}; expected "
            "ai-act-benchmark-*.yaml or ai-act-random-stress-*.yaml"
        )

    generator = LLMAssistedGenerator(provider, model)
    evaluator = AdaptationEvaluator()
    selector = AdaptationSelector()
    checkpoint_path = checkpoint_path or (results_dir / "llm_assisted_adaptation_checkpoint.json")
    records = load_checkpoint(checkpoint_path)
    completed_ids = {r.get("system_id") for r in records if is_resume_complete(r)}
    if records:
        print(f"Resuming from checkpoint: {len(completed_ids)}/{len(system_paths)} completed systems", flush=True)

    for system_index, system_path in enumerate(system_paths, start=1):
        # Only fully successful/system-terminal records are skipped. Records with LLM failures
        # are recomputed so transient provider failures never become false completion.
        system_id = system_path.stem
        existing = next((r for r in records if r.get("system_id") == system_id and is_resume_complete(r)), None)
        if existing is not None:
            print(f"LLM progress: {len(completed_ids)}/{len(system_paths)} ({len(completed_ids)/len(system_paths)*100:5.1f}%) | resumed {system_id}", flush=True)
            continue
        print(f"LLM progress: {len(completed_ids)}/{len(system_paths)} ({len(completed_ids)/len(system_paths)*100:5.1f}%) | system {system_index}/{len(system_paths)}", flush=True)
        system = load_system(system_path)
        current = deepcopy(system)
        original_hash = model_hash(system)
        history: list[dict[str, Any]] = []
        seen_states: set[tuple[tuple[str, str], ...]] = set()
        llm_calls = 0
        llm_failures = 0
        for step in range(1, max_steps + 1):
            before = assess(current, requirements)
            failed = [r.requirement_id for r in before.results if r.status == "FAIL"]
            if not failed:
                history.append({"step": step, "accepted": False, "termination": "COMPLIANT"})
                break
            state = tuple((r.requirement_id, r.status) for r in before.results)
            if state in seen_states:
                history.append({"step": step, "accepted": False, "termination": "CYCLE_DETECTED", "failed_requirements": failed})
                break
            seen_states.add(state)

            try:
                candidates, llm_meta = generate_with_retry(generator, failed, max_retries, base_delay)
                llm_calls += 1
            except RuntimeError as exc:
                llm_failures += 1
                history.append({"step": step, "accepted": False, "termination": "LLM_ERROR", "failed_requirements": failed, "error": str(exc)})
                break

            evaluations = [evaluator.evaluate(current, c, requirements) for c in candidates]
            selected = selector.select(evaluations)
            if selected is None:
                history.append({
                    "step": step,
                    "accepted": False,
                    "termination": "NO_STRICT_IMPROVEMENT",
                    "failed_requirements": failed,
                    "llm": llm_meta,
                    "candidate_evaluations": [{k: v for k, v in e.items() if k != "trial_model"} for e in evaluations],
                })
                break
            current = selected["trial_model"]
            public = {k: v for k, v in selected.items() if k != "trial_model"}
            history.append({
                "step": step,
                "accepted": True,
                "failed_requirements_before": failed,
                "selected_candidate": public,
                "llm": llm_meta,
            })

        after = assess(current, requirements)
        record = {
            "system_id": system.id,
            "source_file": str(system_path),
            "original_model_hash": original_hash,
            "adapted_model_hash": model_hash(current),
            "source_model_unchanged": original_hash == model_hash(system),
            "violations_before": sum(r.status == "FAIL" for r in assess(system, requirements).results),
            "violations_after": sum(r.status == "FAIL" for r in after.results),
            "status_after": after.overall_status,
            "accepted_steps": sum(1 for h in history if h.get("accepted")),
            "llm_calls": llm_calls,
            "llm_failures": llm_failures,
            "history": history,
        }
        records = [r for r in records if r.get("system_id") != system.id]
        records.append(record)
        if checkpoint_path:
            save_checkpoint(checkpoint_path, records)
        completed_ids.add(system.id) if is_resume_complete(record) else None

    records.sort(key=lambda r: r.get("system_id", ""))
    total_before = sum(r["violations_before"] for r in records)
    total_after = sum(r["violations_after"] for r in records)
    summary = {
        "method": "LLM-assisted candidate generation with deterministic model-level evaluation and selection",
        "provider": provider,
        "model": model or provider_config(provider)[2],
        "systems": len(records),
        "total_violations_before": total_before,
        "total_violations_after": total_after,
        "violations_reduced": total_before - total_after,
        "systems_compliant_after": sum(r["status_after"] == "COMPLIANT" for r in records),
        "total_llm_calls": sum(r["llm_calls"] for r in records),
        "total_llm_failures": sum(r["llm_failures"] for r in records),
        "source_models_persistently_modified": False,
        "llm_role": "propose/rank executable candidate action IDs only",
        "verification_role": "deterministic ACER assessor decides PASS/FAIL after each isolated model mutation",
        "safety_boundary": "LLM cannot directly mutate system models and cannot declare compliance",
        "method_note": "Research prototype. LLM proposals are constrained to the safe adaptation catalog; all executable changes occur on isolated deep copies and require deterministic post-adaptation verification.",
    }
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "llm_assisted_adaptation_runs.json").write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    (results_dir / "llm_assisted_adaptation_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return summary


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--systems", default=str(DEFAULT_SYSTEM_DIR))
    p.add_argument("--requirements", default=str(DEFAULT_REQUIREMENTS))
    p.add_argument("--results", default=str(DEFAULT_RESULTS))
    p.add_argument("--provider", choices=["openai", "digitalocean", "ollama"], default="digitalocean")
    p.add_argument("--model")
    p.add_argument("--max-steps", type=int, default=12)
    p.add_argument("--checkpoint")
    p.add_argument("--max-retries", type=int, default=6)
    p.add_argument("--base-delay", type=float, default=5.0)
    a = p.parse_args()
    checkpoint = Path(a.checkpoint) if a.checkpoint else None
    run_all(Path(a.systems), Path(a.requirements), Path(a.results), a.provider, a.model or "", a.max_steps, checkpoint, a.max_retries, a.base_delay)


if __name__ == "__main__":
    main()
