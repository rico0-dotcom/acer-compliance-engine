import argparse, csv, json
from pathlib import Path

EXPECTED_RELEVANCE = {"EXACT_MATCH", "PARTIAL_MATCH", "OTHER"}
YES_NO_PARTIAL = {"YES", "NO", "PARTIAL"}


def norm(v):
    return (v or "").strip().upper()


def load_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"No rows found in {path}")
    required = {
        "candidate_index", "candidate_id", "matched_requirement_id", "relevance",
        "obligation_correct", "applicability_correct", "machine_constraint_correct",
        "provenance_correct", "reviewer"
    }
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    return rows


def load_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def rate(num, den):
    return round(num / den, 6) if den else None


def main():
    ap = argparse.ArgumentParser(description="Evaluate reviewed LLM regulatory-candidate alignment.")
    ap.add_argument("--annotations", default="data/llm/llm_requirement_human_annotations_reviewed.csv")
    ap.add_argument("--normalized", default="data/llm/llm_candidate_normalized.jsonl")
    ap.add_argument("--output", default="data/llm/llm_semantic_alignment_evaluation.json")
    args = ap.parse_args()

    ann = load_csv(args.annotations)
    normalized = load_jsonl(args.normalized)

    by_idx = {int(r["candidate_index"]): r for r in ann}
    norm_by_idx = {int(r["candidate_index"]): r for r in normalized}
    if set(by_idx) != set(norm_by_idx):
        raise ValueError("Reviewed annotations and normalized candidates do not cover the same candidate indices")

    n = len(ann)
    exact = sum(norm(r["relevance"]) == "EXACT_MATCH" for r in ann)
    partial = sum(norm(r["relevance"]) == "PARTIAL_MATCH" for r in ann)
    other = sum(norm(r["relevance"]) == "OTHER" for r in ann)
    supported = exact + partial

    baseline_ids = sorted({r["matched_requirement_id"].strip() for r in ann if r["matched_requirement_id"].strip()})
    normalized_family_ids = sorted({
        r.get("suggested_ac_requirement_id") for r in normalized
        if r.get("suggested_ac_requirement_id")
    })
    covered_from_review = sorted({
        r["matched_requirement_id"].strip() for r in ann
        if r["matched_requirement_id"].strip()
    })

    metrics = {}
    for field, label in [
        ("obligation_correct", "obligation"),
        ("applicability_correct", "applicability"),
        ("machine_constraint_correct", "machine_constraint"),
        ("provenance_correct", "provenance"),
    ]:
        yes = sum(norm(r[field]) == "YES" for r in ann)
        partial_field = sum(norm(r[field]) == "PARTIAL" for r in ann)
        metrics[f"{label}_exact_rate"] = rate(yes, n)
        metrics[f"{label}_at_least_partial_rate"] = rate(yes + partial_field, n)

    relation_counts = {}
    for r in normalized:
        rel = r.get("mapping_relation", "")
        relation_counts[rel] = relation_counts.get(rel, 0) + 1

    family_counts = {}
    for r in normalized:
        rid = r.get("suggested_ac_requirement_id")
        if rid:
            family_counts[rid] = family_counts.get(rid, 0) + 1

    # Agreement between normalization's family suggestion and the reviewer's family mapping,
    # restricted to reviewed candidates where a baseline ID is explicitly supplied.
    comparable_family = [
        (by_idx[i]["matched_requirement_id"].strip(), norm_by_idx[i].get("suggested_ac_requirement_id"))
        for i in sorted(by_idx)
        if by_idx[i]["matched_requirement_id"].strip()
    ]
    family_agree = sum(a == b for a, b in comparable_family)

    out = {
        "candidate_count": n,
        "reviewer_count": sorted({r["reviewer"] for r in ann}),
        "relevance_distribution": {
            "EXACT_MATCH": exact,
            "PARTIAL_MATCH": partial,
            "OTHER": other,
        },
        "supported_candidate_rate": rate(supported, n),
        "exact_match_rate": rate(exact, n),
        "baseline_requirements_in_review": baseline_ids,
        "baseline_requirements_covered_in_review": covered_from_review,
        "baseline_requirement_coverage_rate": rate(len(covered_from_review), 8),
        "normalization_relation_counts": relation_counts,
        "normalization_target_requirement_counts": family_counts,
        "normalization_family_coverage": len(normalized_family_ids),
        "normalization_vs_review_family_agreement": {
            "comparable_candidates": len(comparable_family),
            "agreement_count": family_agree,
            "agreement_rate": rate(family_agree, len(comparable_family)),
            "note": "This compares the deterministic family suggestion with the reviewer’s matched_requirement_id. It is not a legal-equivalence measure."
        },
        "dimension_scores": metrics,
        "method_note": (
            "Single-reviewer semantic evaluation against the current curated ACER reference set. "
            "EXACT_MATCH and PARTIAL_MATCH indicate supported alignment to the baseline; OTHER is not a claim of legal error. "
            "Normalization is family-level heuristic grouping and does not establish legal equivalence or compliance validity."
        )
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
