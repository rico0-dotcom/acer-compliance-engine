from __future__ import annotations

import argparse, csv, json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data/llm/llm_requirement_candidates.jsonl"
CORE = ROOT / "data/requirements/eu_ai_act_core.yaml"
ANNOTATION = ROOT / "data/llm/llm_requirement_human_annotations.csv"
SUMMARY = ROOT / "data/llm/llm_human_evaluation_summary.json"

RELEVANCE = {"EXACT_MATCH", "PARTIAL_MATCH", "UNSUPPORTED", "DUPLICATE", "OTHER"}
YN = {"YES", "PARTIAL", "NO"}
APP = {"YES", "PARTIAL", "NO", "NOT_APPLICABLE"}

def load_candidates():
    if not CANDIDATES.exists():
        raise FileNotFoundError(f"Missing {CANDIDATES}")
    out = []
    for line_no, line in enumerate(CANDIDATES.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        for c in row.get("response", {}).get("requirements", []):
            x = dict(c)
            x["_article"] = row["article"]
            x["_line"] = line_no
            out.append(x)
    return out

def load_gold():
    if not CORE.exists():
        raise FileNotFoundError(f"Missing {CORE}")
    data = yaml.safe_load(CORE.read_text(encoding="utf-8")) or {}
    return data.get("requirements", [])

def prepare():
    candidates = load_candidates()
    fields = [
        "candidate_index","article","candidate_id","title","provision","obligation",
        "actor","applicability","machine_constraint","evidence_expected","source_quote",
        "matched_requirement_id","relevance","obligation_correct","applicability_correct",
        "machine_constraint_correct","provenance_correct","notes","reviewer"
    ]
    with ANNOTATION.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i, c in enumerate(candidates, 1):
            w.writerow({
                "candidate_index": i,
                "article": c.get("_article",""),
                "candidate_id": c.get("candidate_id",""),
                "title": c.get("title",""),
                "provision": c.get("provision",""),
                "obligation": c.get("obligation",""),
                "actor": c.get("actor",""),
                "applicability": c.get("applicability",""),
                "machine_constraint": c.get("machine_constraint",""),
                "evidence_expected": json.dumps(c.get("evidence_expected",[]), ensure_ascii=False),
                "source_quote": c.get("source_quote",""),
                "matched_requirement_id":"","relevance":"","obligation_correct":"",
                "applicability_correct":"","machine_constraint_correct":"",
                "provenance_correct":"","notes":"","reviewer":""
            })
    print(f"Created annotation template with {len(candidates)} candidates: {ANNOTATION}")
    return 0

def rate(rows, field, accepted):
    vals = [r[field] for r in rows if r.get(field)]
    return None if not vals else sum(v in accepted for v in vals) / len(vals)

def evaluate():
    candidates = load_candidates()
    gold = load_gold()
    if not ANNOTATION.exists():
        print(f"ERROR: Missing {ANNOTATION}; run --prepare first.")
        return 1
    with ANNOTATION.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != len(candidates):
        print(f"ERROR: annotation rows={len(rows)} but candidates={len(candidates)}")
        return 1
    reviewed = [r for r in rows if r.get("relevance","").strip()]
    if not reviewed:
        print("ERROR: No reviewed candidates. Fill the CSV, then rerun --evaluate.")
        return 1

    errors = []
    for r in reviewed:
        if r["relevance"] not in RELEVANCE:
            errors.append((r["candidate_index"], "relevance", r["relevance"]))
        for field in ("obligation_correct","machine_constraint_correct","provenance_correct"):
            if r[field] and r[field] not in YN:
                errors.append((r["candidate_index"], field, r[field]))
        if r["applicability_correct"] and r["applicability_correct"] not in APP:
            errors.append((r["candidate_index"], "applicability_correct", r["applicability_correct"]))
    if errors:
        print("ERROR: invalid annotations:")
        for e in errors: print(e)
        return 1

    gold_ids = {g["id"] for g in gold}
    matched = {
        r["matched_requirement_id"].strip()
        for r in reviewed
        if r["relevance"] in {"EXACT_MATCH","PARTIAL_MATCH"} and r["matched_requirement_id"].strip()
    }

    rel_counts = {k: sum(r["relevance"] == k for r in reviewed) for k in RELEVANCE}
    summary = {
        "candidate_count": len(candidates),
        "reviewed_candidates": len(reviewed),
        "review_completion": len(reviewed)/len(candidates),
        "relevance_distribution": rel_counts,
        "supported_candidate_rate": (
            rel_counts["EXACT_MATCH"] + rel_counts["PARTIAL_MATCH"]
        ) / len(reviewed),
        "exact_match_rate": rel_counts["EXACT_MATCH"]/len(reviewed),
        "gold_requirements": len(gold),
        "gold_requirements_covered": len(matched & gold_ids),
        "gold_requirements_missing": sorted(gold_ids - matched),
        "unknown_matched_requirement_ids": sorted(matched - gold_ids),
        "dimension_scores": {
            "obligation_exact_rate": rate(reviewed,"obligation_correct",{"YES"}),
            "obligation_at_least_partial": rate(reviewed,"obligation_correct",{"YES","PARTIAL"}),
            "applicability_correct_rate": rate(reviewed,"applicability_correct",{"YES","NOT_APPLICABLE"}),
            "applicability_at_least_partial": rate(reviewed,"applicability_correct",{"YES","PARTIAL","NOT_APPLICABLE"}),
            "machine_constraint_exact_rate": rate(reviewed,"machine_constraint_correct",{"YES"}),
            "machine_constraint_at_least_partial": rate(reviewed,"machine_constraint_correct",{"YES","PARTIAL"}),
            "provenance_exact_rate": rate(reviewed,"provenance_correct",{"YES"})
        },
        "note": "Human-reviewed extraction metrics, not a legal compliance opinion."
    }
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--prepare", action="store_true")
    p.add_argument("--evaluate", action="store_true")
    a = p.parse_args()
    if a.prepare: return prepare()
    if a.evaluate: return evaluate()
    p.error("Choose --prepare or --evaluate.")

if __name__ == "__main__":
    raise SystemExit(main())
