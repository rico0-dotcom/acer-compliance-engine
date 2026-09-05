"""
Provider-agnostic LLM-assisted regulatory requirement extraction.

Providers:
  openai       OpenAI API
  digitalocean DigitalOcean Serverless Inference
  ollama       Local Ollama server

All providers use an OpenAI-compatible chat-completions interface.
This experiment never modifies the deterministic benchmark or ground truth.
"""
from __future__ import annotations
import argparse, json, os
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
ARTICLES=ROOT/'data/regulations/eu_ai_act_articles.yaml'
CORE=ROOT/'data/requirements/eu_ai_act_core.yaml'
OUTDIR=ROOT/'data/llm'
SYSTEM_PROMPT="""You are a regulatory-requirement engineering assistant.
Extract candidate machine-processable compliance requirements from only the
supplied EU AI Act article text. Do not add obligations from outside the text.
Preserve legal meaning and provenance. Identify applicability conditions only
when supported by the supplied article. Express machine constraints at an
abstract engineering level; do not invent implementation details.

Return ONLY valid JSON matching this structure:
{"requirements":[{"candidate_id":"LLM-Rxx-01","title":"...","provision":"...","obligation":"...","actor":"...","applicability":"...","machine_constraint":"...","evidence_expected":["..."],"source_quote":"..."}]}

source_quote MUST be copied verbatim from the supplied article text.
"""
def load_inputs():
    if not ARTICLES.exists(): raise FileNotFoundError(f'Missing {ARTICLES}')
    if not CORE.exists(): raise FileNotFoundError(f'Missing {CORE}')
    return yaml.safe_load(ARTICLES.read_text(encoding='utf-8')) or {}, yaml.safe_load(CORE.read_text(encoding='utf-8')) or {}
def prepare():
    articles,_=load_inputs(); OUTDIR.mkdir(parents=True,exist_ok=True)
    path=OUTDIR/'requirement_extraction_prompts.jsonl'
    with path.open('w',encoding='utf-8') as f:
        for item in articles.get('articles',[]):
            f.write(json.dumps({'article':item['article'],'source':item['text'],'task':'Extract all distinct explicit, independently testable candidate compliance requirements.'},ensure_ascii=False)+'\n')
    print(f'Prepared {len(articles.get("articles",[]))} article prompts: {path}'); return 0
def provider_config(provider):
    if provider=='openai': return os.getenv('OPENAI_API_KEY'),os.getenv('ACER_OPENAI_BASE_URL','https://api.openai.com/v1'),os.getenv('ACER_LLM_MODEL','gpt-5-mini')
    if provider=='digitalocean': return os.getenv('DIGITALOCEAN_TOKEN') or os.getenv('DIGITALOCEAN_INFERENCE_KEY'),os.getenv('ACER_DO_BASE_URL','https://inference.do-ai.run/v1'),os.getenv('ACER_LLM_MODEL','')
    if provider=='ollama': return os.getenv('OLLAMA_API_KEY','ollama'),os.getenv('ACER_OLLAMA_BASE_URL','http://localhost:11434/v1'),os.getenv('ACER_LLM_MODEL','')
    raise ValueError(f'Unknown provider: {provider}')
def list_models(provider):
    try: from openai import OpenAI
    except ImportError: print('ERROR: openai package is not installed. Run: python -m pip install openai'); return 1
    api_key,base_url,_=provider_config(provider)
    if not api_key: print(f'ERROR: No credential configured for {provider}.'); return 1
    for model in OpenAI(api_key=api_key,base_url=base_url).models.list().data: print(model.id)
    return 0
def run(provider,model):
    try: from openai import OpenAI
    except ImportError: print('ERROR: openai package is not installed. Run: python -m pip install openai'); return 1
    articles,_=load_inputs(); api_key,base_url,env_model=provider_config(provider); model=model or env_model
    if not api_key: print(f'ERROR: No credential configured for {provider}.'); return 1
    if not model: print(f'ERROR: No model specified for {provider}. Use --model MODEL or set ACER_LLM_MODEL.'); return 1
    client=OpenAI(api_key=api_key,base_url=base_url); OUTDIR.mkdir(parents=True,exist_ok=True); out=OUTDIR/'llm_requirement_candidates.jsonl'
    with out.open('w',encoding='utf-8') as f:
        for item in articles.get('articles',[]):
            response=client.chat.completions.create(model=model,messages=[{'role':'system','content':SYSTEM_PROMPT},{'role':'user','content':f"Article {item['article']} from the pinned EU AI Act source:\n\n{item['text']}\n\nExtract the candidate requirements from this article."}],temperature=0)
            content=response.choices[0].message.content
            try: parsed=json.loads(content)
            except json.JSONDecodeError as exc: raise RuntimeError(f'Provider returned invalid JSON for Article {item["article"]}: {exc}') from exc
            if not isinstance(parsed,dict) or not isinstance(parsed.get('requirements'),list): raise RuntimeError(f'Provider output for Article {item["article"]} does not match expected schema.')
            f.write(json.dumps({'article':item['article'],'provider':provider,'model':model,'response':parsed},ensure_ascii=False)+'\n')
    print(f'Saved LLM candidates: {out}'); print(f'Provider: {provider}'); print(f'Model: {model}'); return 0
def norm(v): return ' '.join(str(v).lower().replace('–','-').split())
def evaluate():
    pred=OUTDIR/'llm_requirement_candidates.jsonl'
    if not pred.exists(): print(f'ERROR: Missing {pred}; run --run first.'); return 1
    _,core=load_inputs(); gold=core.get('requirements',[]); candidates=[]; providers=set(); models=set()
    for line in pred.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        row=json.loads(line); providers.add(row.get('provider')); models.add(row.get('model')); candidates.extend(row.get('response',{}).get('requirements',[]))
    provision_hits=sum(any(norm(c.get('provision',''))==norm(g['provision']) for g in gold) for c in candidates)
    title_hits=sum(any(c.get('title','').strip().lower()==g['title'].strip().lower() for g in gold) for c in candidates)
    summary={'providers':sorted(providers),'models':sorted(models),'gold_requirements':len(gold),'llm_candidates':len(candidates),'exact_provision_matches':provision_hits,'title_exact_matches':title_hits,'note':'Initial automated comparison only; legal meaning, completeness, applicability and provenance require human validation.'}
    (OUTDIR/'llm_extraction_evaluation.json').write_text(json.dumps(summary,indent=2),encoding='utf-8'); print(json.dumps(summary,indent=2)); return 0
def main():
    p=argparse.ArgumentParser(); p.add_argument('--prepare-only',action='store_true'); p.add_argument('--run',action='store_true'); p.add_argument('--evaluate',action='store_true'); p.add_argument('--list-models',action='store_true'); p.add_argument('--provider',choices=['openai','digitalocean','ollama'],default='ollama'); p.add_argument('--model'); a=p.parse_args()
    if a.prepare_only:return prepare()
    if a.list_models:return list_models(a.provider)
    if a.run:return run(a.provider,a.model)
    if a.evaluate:return evaluate()
    p.error('Choose --prepare-only, --list-models, --run, or --evaluate.')
if __name__=='__main__': raise SystemExit(main())
