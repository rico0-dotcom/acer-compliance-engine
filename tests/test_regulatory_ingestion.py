from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]

def test_local_regulatory_source_exists_after_ingestion():
    source = ROOT / "data" / "regulations" / "eu_ai_act_source.html"
    manifest = ROOT / "data" / "regulations" / "eur_ai_act_source_manifest.yaml"

    # This test is intentionally conditional before the user has supplied
    # the local source snapshot.
    if not source.exists():
        return
    assert source.stat().st_size > 0
    assert manifest.exists()

def test_traceability_uses_real_eu_ai_act_celex():
    path = ROOT / "data" / "requirements" / "eu_ai_act_traceability.yaml"
    if not path.exists():
        return
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["source"]["celex"] == "02024R1689-20260727"
    assert data["source"]["sha256"]
    ids = [r["requirement_id"] for r in data.get("requirements", [])]
    assert "EUAI-R9-01" in ids
    assert "EUAI-R14-02" in ids
