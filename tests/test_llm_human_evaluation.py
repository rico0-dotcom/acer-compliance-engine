from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/prepare_llm_human_evaluation.py"

def load():
    spec = importlib.util.spec_from_file_location("human_eval", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_candidate_run_exists():
    assert (ROOT / "data/llm/llm_requirement_candidates.jsonl").exists()

def test_curated_baseline_is_preserved():
    assert (ROOT / "data/requirements/eu_ai_act_core.yaml").exists()

def test_taxonomy():
    mod = load()
    assert "EXACT_MATCH" in mod.RELEVANCE
    assert "PARTIAL_MATCH" in mod.RELEVANCE
    assert "UNSUPPORTED" in mod.RELEVANCE
    assert "YES" in mod.YN
