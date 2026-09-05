from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from app.engine import assess
from app.loaders import load_requirements, load_system

DEFAULT_SYSTEM_DIR = BASE / "data" / "systems" / "eu_ai_act_benchmark"
DEFAULT_REQUIREMENTS = BASE / "data" / "requirements" / "eu_ai_act_core.yaml"
DEFAULT_RESULTS = BASE / "data" / "results"


def _status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row["status"])
        counts[status] = counts.get(status, 0) + 1
    return counts


def _requirement_index(requirements):
    return {req.id: req for req in requirements}


def _trace_rows(system, report, req_map):
    rows: list[dict[str, Any]] = []
    for result in report.results:
        req = req_map[result.requirement_id]
        evidence = [e.model_dump() for e in result.evidence]
        rows.append({
            "system_id": system.id,
            "system_version": system.version,
            "requirement_id": req.id,
            "regulation": req.regulation,
            "provision": req.provision,
            "requirement_title": req.title,
            "actor": req.actor,
            "verification_rule": req.rule,
            "verification_parameters": json.dumps(req.parameters, sort_keys=True),
            "status": str(result.status),
            "explanation": result.explanation,
            "evidence_count": len(evidence),
            "evidence": json.dumps(evidence, ensure_ascii=False),
            "source_type": req.provenance.source_type,
            "source_id": req.provenance.source_id or "",
            "source_url": req.provenance.source_url or "",
            "source_provision": req.provenance.provision or req.provision,
            "retrieval_date": req.provenance.retrieval_date or "",
            "validation_status": req.provenance.validation_status,
            "adaptation_options": json.dumps(result.remediation_options, ensure_ascii=False),
            "trace_id": report.trace_id,
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Run traceable deterministic ACER compliance assessment.")
    parser.add_argument("--systems", default=str(DEFAULT_SYSTEM_DIR))
    parser.add_argument("--requirements", default=str(DEFAULT_REQUIREMENTS))
    parser.add_argument("--results", default=str(DEFAULT_RESULTS))
    parser.add_argument("--system-pattern", default="ai-act-benchmark-*.yaml")
    args = parser.parse_args()

    system_dir = Path(args.systems)
    requirements_path = Path(args.requirements)
    results_dir = Path(args.results)

    if not system_dir.exists():
        raise SystemExit(f"System directory not found: {system_dir}")
    if not requirements_path.exists():
        raise SystemExit(f"Requirements file not found: {requirements_path}")

    requirements = load_requirements(requirements_path)
    req_map = _requirement_index(requirements)
    system_paths = sorted(system_dir.glob(args.system_pattern))
    if not system_paths:
        raise SystemExit(f"No systems matched {args.system_pattern!r} in {system_dir}")

    all_rows: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []

    for system_path in system_paths:
        system = load_system(system_path)
        report = assess(system, requirements)
        all_rows.extend(_trace_rows(system, report, req_map))
        reports.append(report.model_dump())

    results_dir.mkdir(parents=True, exist_ok=True)

    trace_jsonl = results_dir / "compliance_assessment_trace.jsonl"
    with trace_jsonl.open("w", encoding="utf-8") as f:
        for row in all_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    trace_csv = results_dir / "compliance_assessment_trace.csv"
    fields = list(all_rows[0].keys())
    with trace_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_rows)

    reports_path = results_dir / "compliance_assessment_reports.json"
    reports_path.write_text(json.dumps(reports, indent=2, ensure_ascii=False), encoding="utf-8")

    scenario_status_counts: dict[str, int] = {}
    for report in reports:
        status = report["overall_status"]
        scenario_status_counts[status] = scenario_status_counts.get(status, 0) + 1

    summary = {
        "assessment_method": "deterministic_rule_based_engine_over_acER_system_model",
        "systems": len(system_paths),
        "requirements": len(requirements),
        "checks": len(all_rows),
        "check_status_counts": _status_counts(all_rows),
        "scenario_overall_status_counts": scenario_status_counts,
        "evidence_total": sum(row["evidence_count"] for row in all_rows),
        "traceable_checks": sum(1 for row in all_rows if row["trace_id"] and row["source_provision"]),
        "files": {
            "trace_csv": str(trace_csv),
            "trace_jsonl": str(trace_jsonl),
            "reports_json": str(reports_path),
        },
        "method_note": "This layer verifies the current ACER curated machine rules against system models. It does not by itself establish legal compliance beyond the encoded requirements and benchmark assumptions.",
    }
    summary_path = results_dir / "compliance_assessment_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
