from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

def test_llm_schema_is_valid_json():
    path = ROOT / "data" / "llm" / "requirement_extraction_schema.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["type"] == "object"
    assert "requirements" in data["properties"]

def test_llm_runner_preserves_baseline():
    assert (ROOT / "data" / "requirements" / "eu_ai_act_core.yaml").exists()
    assert (ROOT / "data" / "regulations" / "eu_ai_act_articles.yaml").exists()
