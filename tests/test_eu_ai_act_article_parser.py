from pathlib import Path
import importlib.util
import yaml
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts'/'ingest_eu_ai_act.py'
spec=importlib.util.spec_from_file_location('ingest_eu_ai_act',SCRIPT); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
def test_parser_uses_standalone_article_headings():
    source='''<html><body><h2>Article 9</h2><p>Risk management system.</p><p>The process refers to Article 72 and Article 60.</p><h2>Article 10</h2><p>Data and data governance.</p><h2>Article 11</h2><p>Technical documentation.</p><h2>Article 12</h2><p>Record-keeping.</p></body></html>'''
    articles=module.extract_articles(module.html_to_structured_text(source.encode()))
    assert set(articles)=={'9','10','12'}
    assert 'Article 72' in articles['9']
    assert 'Article 10' not in articles['9']
def test_generated_article_file_has_expected_seven_articles():
    path=ROOT/'data'/'regulations'/'eu_ai_act_articles.yaml'; assert path.exists()
    data=yaml.safe_load(path.read_text(encoding='utf-8')); assert [x['article'] for x in data['articles']]==[9,10,12,13,14,15,50]
def test_article_9_starts_with_correct_heading_and_content():
    path=ROOT/'data'/'regulations'/'eu_ai_act_articles.yaml'; data=yaml.safe_load(path.read_text(encoding='utf-8'))
    article9=next(x['text'] for x in data['articles'] if x['article']==9)
    assert article9.splitlines()[0].strip().lower()=='article 9'
    assert 'A risk management system shall be established' in article9
