from pathlib import Path
import json, importlib.util

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/normalize_llm_candidates.py"

def load():
    spec = importlib.util.spec_from_file_location("normalizer", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_normalizer_supports_current_acer_families():
    mod = load()
    assert mod.ARTICLE_FAMILY[9] == "EUAI-R9-01"
    assert mod.ARTICLE_FAMILY[10] == "EUAI-R10-01"
    assert mod.ARTICLE_FAMILY[12] == "EUAI-R12-01"
    assert mod.ARTICLE_FAMILY[13] == "EUAI-R13-01"
    assert mod.ARTICLE_FAMILY[14] == "EUAI-R14-01"
    assert mod.ARTICLE_FAMILY[15] == "EUAI-R15-01"
    assert mod.ARTICLE_FAMILY[50] == "EUAI-R50-01"

def test_completed_llm_candidate_file_is_preserved():
    assert (ROOT / "data/llm/llm_requirement_candidates.jsonl").exists()

def test_override_file_is_explicitly_separate():
    path = ROOT / "data/llm/llm_mapping_overrides.yaml"
    assert path.exists()
    data = __import__("yaml").safe_load(path.read_text(encoding="utf-8"))
    assert "overrides" in data
