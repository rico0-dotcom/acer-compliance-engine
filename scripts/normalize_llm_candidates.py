"""
Normalize fine-grained LLM regulatory candidates into the eight ACER
requirement families.

This is a deterministic candidate-mapping layer, not a legal-validity oracle.
It uses the cited article, provision text, and curated ACER metadata to suggest
target requirement families. A manual mapping file can override suggestions.

Inputs:
  data/llm/llm_requirement_candidates.jsonl
  data/requirements/eu_ai_act_core.yaml
Optional:
  data/llm/llm_mapping_overrides.yaml

Outputs:
  data/llm/llm_candidate_normalized.jsonl
  data/llm/llm_normalization_summary.json
"""

from __future__ import annotations
import argparse, json, re
from pathlib import Path
from collections import Counter, defaultdict

import yaml

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data/llm/llm_requirement_candidates.jsonl"
CORE = ROOT / "data/requirements/eu_ai_act_core.yaml"
OVERRIDES = ROOT / "data/llm/llm_mapping_overrides.yaml"
OUT = ROOT / "data/llm/llm_candidate_normalized.jsonl"
SUMMARY = ROOT / "data/llm/llm_normalization_summary.json"

# Mapping families are intentionally conservative and tied to provisions
# represented in the current eight-item ACER baseline.
ARTICLE_FAMILY = {
    9: "EUAI-R9-01",
    10: "EUAI-R10-01",
    12: "EUAI-R12-01",
    13: "EUAI-R13-01",
    14: "EUAI-R14-01",
    15: "EUAI-R15-01",
    50: "EUAI-R50-01",
}

def load():
    if not CANDIDATES.exists():
        raise FileNotFoundError(f"Missing {CANDIDATES}")
    if not CORE.exists():
        raise FileNotFoundError(f"Missing {CORE}")
    candidates = []
    for line in CANDIDATES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        for c in row.get("response", {}).get("requirements", []):
            x = dict(c)
            x["_article"] = int(row["article"])
            candidates.append(x)
    core = yaml.safe_load(CORE.read_text(encoding="utf-8")) or {}
    return candidates, core.get("requirements", [])

def load_overrides():
    if not OVERRIDES.exists():
        return {}
    data = yaml.safe_load(OVERRIDES.read_text(encoding="utf-8")) or {}
    return data.get("overrides", {})

def normalize_text(value):
    value = str(value or "").lower()
    value = value.replace("–", "-").replace("‑", "-").replace("’", "'")
    return re.sub(r"\s+", " ", value).strip()

def article_number(provision):
    m = re.search(r"\barticle\s*([0-9]+)", str(provision), re.I)
    return int(m.group(1)) if m else None

def suggest_target(candidate):
    article = candidate["_article"]
    provision = normalize_text(candidate.get("provision", ""))
    title = normalize_text(candidate.get("title", ""))
    obligation = normalize_text(candidate.get("obligation", ""))
    combined = " ".join([title, provision, obligation])

    # Default: article-level relation to the corresponding ACER family.
    target = ARTICLE_FAMILY.get(article)
    reason = "same article family as an existing ACER requirement"

    # Refine Article 14's two ACER families.
    if article == 14:
        if re.search(r"\boverride\b|\breverse\b|\bdisregard\b|\bstop\b|\binterrupt\b|\bhalt\b", combined):
            target = "EUAI-R14-02"
            reason = "Article 14 intervention/override/interrupt limb"
        else:
            target = "EUAI-R14-01"
            reason = "Article 14 human-oversight family"

    # The current R50 baseline is specifically the direct-interaction notice.
    if article == 50:
        if re.search(r"\bdirect(ly)? interact\b|\binformed\b.*\binteract(ing)?\b|\bai system\b.*\binteraction\b", combined):
            target = "EUAI-R50-01"
            reason = "Article 50(1) direct-interaction notification"
        else:
            target = None
            reason = "Article 50 provision is outside current R50-01 baseline scope"

    # Evidence of a candidate's provision should dominate article-only mapping
    # for cross-references that clearly describe another family.
    if re.search(r"\brisk management\b", combined) and article != 9:
        if "risk management" in combined and not re.search(r"\bdata\b.*\bgovernance\b", combined):
            # Keep the local article target for Article 13/14/15, because those
            # are legitimate cross-referenced/documentation obligations.
            pass

    relation = "FAMILY_MATCH" if target else "OUTSIDE_BASELINE"
    return target, relation, reason

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--prepare", action="store_true")
    p.add_argument("--summary", action="store_true")
    args = p.parse_args()

    candidates, gold = load()
    overrides = load_overrides()

    normalized = []
    for index, c in enumerate(candidates, start=1):
        cid = c.get("candidate_id", f"CAND-{index}")
        target, relation, reason = suggest_target(c)

        override = overrides.get(str(cid)) or overrides.get(cid)
        if override:
            target = override.get("matched_requirement_id")
            relation = override.get("relation", relation)
            reason = override.get("reason", "manual override")

        normalized.append({
            "candidate_index": index,
            "candidate_id": cid,
            "article": c["_article"],
            "title": c.get("title", ""),
            "provision": c.get("provision", ""),
            "suggested_ac_requirement_id": target,
            "mapping_relation": relation,
            "mapping_reason": reason,
            "mapping_status": "AUTOMATIC_SUGGESTION" if not override else "MANUAL_OVERRIDE",
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if args.prepare:
        with OUT.open("w", encoding="utf-8") as f:
            for row in normalized:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

        counts = Counter(r["mapping_relation"] for r in normalized)
        target_counts = Counter(
            r["suggested_ac_requirement_id"]
            for r in normalized if r["suggested_ac_requirement_id"]
        )
        summary = {
            "candidate_count": len(normalized),
            "mapping_relation_counts": dict(counts),
            "target_requirement_counts": dict(target_counts),
            "coverage_of_eight_requirement_families": len(target_counts),
            "unmapped_outside_baseline": sum(
                r["mapping_relation"] == "OUTSIDE_BASELINE" for r in normalized
            ),
            "method": "deterministic article/provision heuristic with optional manual overrides",
            "warning": "Mapping suggests requirement families; it does not establish legal equivalence or compliance validity.",
        }
        SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))
        print(f"Normalized candidates: {OUT}")
        print(f"Summary: {SUMMARY}")
        return 0

    if args.summary:
        if not SUMMARY.exists():
            print("ERROR: Run --prepare first.")
            return 1
        print(SUMMARY.read_text(encoding="utf-8"))
        return 0

    p.error("Choose --prepare or --summary.")

if __name__ == "__main__":
    raise SystemExit(main())
