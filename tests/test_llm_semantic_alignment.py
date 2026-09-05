import csv
import json
from pathlib import Path


def test_semantic_alignment_artifacts_are_self_consistent():
    ann = Path("data/llm/llm_requirement_human_annotations_reviewed.csv")
    norm = Path("data/llm/llm_candidate_normalized.jsonl")
    assert ann.exists(), "Reviewed annotation CSV missing"
    assert norm.exists(), "Normalized candidate JSONL missing"

    with ann.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    normalized = [json.loads(x) for x in norm.read_text(encoding="utf-8").splitlines() if x.strip()]

    assert len(rows) == 70
    assert len(normalized) == 70
    assert {int(r["candidate_index"]) for r in rows} == {int(r["candidate_index"]) for r in normalized}
    assert {r["relevance"] for r in rows} <= {"EXACT_MATCH", "PARTIAL_MATCH", "OTHER"}


def test_review_covers_all_eight_baseline_requirements():
    with Path("data/llm/llm_requirement_human_annotations_reviewed.csv").open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    covered = {r["matched_requirement_id"] for r in rows if r["matched_requirement_id"]}
    expected = {
        "EUAI-R9-01", "EUAI-R10-01", "EUAI-R12-01", "EUAI-R13-01",
        "EUAI-R14-01", "EUAI-R14-02", "EUAI-R15-01", "EUAI-R50-01"
    }
    assert covered == expected
