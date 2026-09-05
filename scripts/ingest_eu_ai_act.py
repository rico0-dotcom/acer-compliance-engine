from __future__ import annotations
import hashlib, html, re, sys
from datetime import date
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
REG_DIR = ROOT / 'data' / 'regulations'
REQ_DIR = ROOT / 'data' / 'requirements'
SOURCE = REG_DIR / 'eu_ai_act_source.html'
EXPECTED = [9, 10, 12, 13, 14, 15, 50]

def html_to_structured_text(raw: bytes) -> str:
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:
        print('ERROR: beautifulsoup4 is required. Install with: python -m pip install beautifulsoup4')
        raise SystemExit(1) from exc
    soup = BeautifulSoup(raw, 'html.parser')
    for tag in soup(['script','style','noscript']):
        tag.decompose()
    text = html.unescape(soup.get_text('\n')).replace('\xa0',' ')
    lines=[]
    for line in text.splitlines():
        line=re.sub(r'[ \t]+',' ',line).strip()
        if line:
            lines.append(line)
    return '\n'.join(lines)

def extract_articles(structured_text: str) -> dict[str,str]:
    lines=structured_text.splitlines()
    heading_re=re.compile(r'^Article\s+(\d+)\s*$', re.I)
    headings=[]
    for i,line in enumerate(lines):
        m=heading_re.fullmatch(line)
        if m:
            headings.append((i,int(m.group(1))))
    found={}
    for pos,(start,num) in enumerate(headings):
        if num not in EXPECTED: continue
        end=len(lines)
        if pos+1 < len(headings): end=headings[pos+1][0]
        found[str(num)]='\n'.join(lines[start:end]).strip()
    return found

def main()->int:
    REG_DIR.mkdir(parents=True,exist_ok=True); REQ_DIR.mkdir(parents=True,exist_ok=True)
    if not SOURCE.exists():
        print(f'ERROR: Missing local official source: {SOURCE}'); return 1
    raw=SOURCE.read_bytes()
    if not raw: print('ERROR: Local source is empty.'); return 1
    structured=html_to_structured_text(raw)
    articles=extract_articles(structured)
    missing=[str(n) for n in EXPECTED if str(n) not in articles]
    if missing:
        print(f'ERROR: Missing actual article headings: {", ".join(missing)}')
        print('Detected required headings:', sorted(articles.keys(), key=int)); return 1
    digest=hashlib.sha256(raw).hexdigest()
    selected_url='https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727'
    manifest={'document':'Regulation (EU) 2024/1689 (Artificial Intelligence Act)','celex':'02024R1689-20260727','consolidated_version':'27 July 2026','source_url':selected_url,'local_source':str(SOURCE.relative_to(ROOT)).replace('\\','/'),'retrieval_date':date.today().isoformat(),'sha256':digest,'source_status':'LOCAL_OFFICIAL_SOURCE_SNAPSHOT','parser':'standalone_article_heading_parser_v2','articles_extracted':EXPECTED}
    (REG_DIR/'eur_ai_act_source_manifest.yaml').write_text(yaml.safe_dump(manifest,sort_keys=False,allow_unicode=True),encoding='utf-8')
    payload={'document':manifest['document'],'celex':manifest['celex'],'consolidated_version':manifest['consolidated_version'],'source_sha256':digest,'source_url':selected_url,'articles':[{'article':n,'text':articles[str(n)],'source':selected_url} for n in EXPECTED]}
    (REG_DIR/'eu_ai_act_articles.yaml').write_text(yaml.safe_dump(payload,sort_keys=False,allow_unicode=True),encoding='utf-8')
    core=REQ_DIR/'eu_ai_act_core.yaml'; trace={'source':{'celex':manifest['celex'],'consolidated_version':manifest['consolidated_version'],'source_url':selected_url,'local_snapshot':manifest['local_source'],'sha256':digest},'requirements':[]}
    if core.exists():
        data=yaml.safe_load(core.read_text(encoding='utf-8')) or {}
        for req in data.get('requirements',[]):
            prov=req.get('provenance',{}); trace['requirements'].append({'requirement_id':req.get('id'),'title':req.get('title'),'provision':req.get('provision'),'source_article':prov.get('provision'),'source_url':prov.get('source_url',selected_url),'source_snapshot_sha256':digest,'formalization_status':'CURATED_ACER_REQUIREMENT'})
    (REQ_DIR/'eu_ai_act_traceability.yaml').write_text(yaml.safe_dump(trace,sort_keys=False,allow_unicode=True),encoding='utf-8')
    print(f'Accepted local source: {SOURCE}')
    print(f'SHA-256: {digest}')
    print('Extracted actual Article headings: ' + ', '.join(map(str,EXPECTED)))
    print(f'Wrote: {REG_DIR / "eu_ai_act_articles.yaml"}')
    print(f'Wrote: {REQ_DIR / "eu_ai_act_traceability.yaml"}')
    return 0
if __name__=='__main__': raise SystemExit(main())
