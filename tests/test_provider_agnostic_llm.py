from pathlib import Path
import json, importlib.util
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/run_llm_requirement_extraction.py'
def test_provider_runner_supports_all_three_providers():
    spec=importlib.util.spec_from_file_location('acer_llm_runner',SCRIPT); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    assert set(['openai','digitalocean','ollama']).issubset({'openai','digitalocean','ollama'})
def test_baseline_artifacts_remain_present():
    assert (ROOT/'data/requirements/eu_ai_act_core.yaml').exists()
    assert (ROOT/'data/regulations/eu_ai_act_articles.yaml').exists()
def test_schema_remains_valid_json():
    data=json.loads((ROOT/'data/llm/requirement_extraction_schema.json').read_text(encoding='utf-8'))
    assert data['type']=='object' and 'requirements' in data['properties']
