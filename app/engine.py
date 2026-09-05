from __future__ import annotations
import hashlib
import json
from .models import CheckResult, ComplianceReport, Evidence, Requirement, SystemModel

def has_component(system, component_type):
    return [c.id for c in system.components if c.type == component_type]

def has_flow(system, source, target):
    return any(f.source == source and f.target == target for f in system.flows)

def condition_satisfied(system: SystemModel, req: Requirement) -> bool:
    for key, expected in req.condition.items():
        if key == "system_is_high_risk":
            actual = system.attributes.get("system_is_high_risk")
        elif key == "uses_training_data":
            actual = system.attributes.get("uses_training_data")
        elif key == "direct_ai_interaction":
            actual = system.attributes.get("direct_ai_interaction")
        else:
            actual = system.attributes.get(key)
        if actual != expected:
            return False
    return True

def deterministic_check(system: SystemModel, req: Requirement):
    evidence = []

    if not condition_satisfied(system, req):
        return CheckResult(
            system_id=system.id,
            requirement_id=req.id,
            status="PASS",
            explanation="Requirement is not applicable under the system's modeled applicability conditions.",
            evidence=[Evidence(
                type="applicability",
                description=f"Applicability conditions not satisfied: {req.condition}"
            )]
        )

    if req.rule == "required_component":
        ctype = req.parameters["component_type"]
        matches = has_component(system, ctype)
        if matches:
            evidence.append(Evidence(type="architecture", description=f"Found {ctype}: {matches}"))
            return CheckResult(
                system_id=system.id, requirement_id=req.id, status="PASS",
                explanation=f"Required component '{ctype}' is present.",
                evidence=evidence
            )
        return CheckResult(
            system_id=system.id, requirement_id=req.id, status="FAIL",
            explanation=f"Required component '{ctype}' is absent.",
            evidence=[Evidence(type="architecture", description=f"No {ctype} component found.")],
            remediation_options=req.adaptation_tactics
        )

    if req.rule == "required_flow":
        sources = has_component(system, req.parameters["source_type"])
        targets = has_component(system, req.parameters["target_type"])
        pairs = [(s,t) for s in sources for t in targets if has_flow(system,s,t)]
        if pairs:
            return CheckResult(
                system_id=system.id, requirement_id=req.id, status="PASS",
                explanation="Required architectural flow is present.",
                evidence=[Evidence(type="dataflow", description=f"Flow(s): {pairs}")]
            )
        return CheckResult(
            system_id=system.id, requirement_id=req.id, status="FAIL",
            explanation="Required architectural flow is absent.",
            evidence=[Evidence(type="dataflow", description="No required flow found.")],
            remediation_options=req.adaptation_tactics
        )

    if req.rule == "property_equals":
        ctype = req.parameters["component_type"]
        prop = req.parameters["property"]
        expected = req.parameters["expected"]
        matches = [
            c for c in system.components
            if c.type == ctype and c.properties.get(prop) == expected
        ]
        if matches:
            return CheckResult(
                system_id=system.id, requirement_id=req.id, status="PASS",
                explanation="Required configuration property is satisfied.",
                evidence=[Evidence(type="configuration", description=f"{matches[0].id} satisfies {prop}.")]
            )
        return CheckResult(
            system_id=system.id, requirement_id=req.id, status="FAIL",
            explanation="Required configuration property is missing or incorrect.",
            evidence=[Evidence(type="configuration", description=f"No {ctype} has {prop}={expected!r}.")],
            remediation_options=req.adaptation_tactics
        )

    if req.rule == "attribute_equals":
        prop = req.parameters["attribute"]
        expected = req.parameters["expected"]
        if system.attributes.get(prop) == expected:
            return CheckResult(
                system_id=system.id, requirement_id=req.id, status="PASS",
                explanation=f"System attribute {prop}={expected!r} is satisfied.",
                evidence=[Evidence(type="system_attribute", description=f"{prop}={expected!r}.")]
            )
        return CheckResult(
            system_id=system.id, requirement_id=req.id, status="FAIL",
            explanation=f"System attribute {prop} is not {expected!r}.",
            evidence=[Evidence(type="system_attribute",
                               description=f"Observed {prop}={system.attributes.get(prop)!r}.")],
            remediation_options=req.adaptation_tactics
        )

    raise ValueError(f"Unsupported rule: {req.rule}")

def trace_id(system, requirements):
    payload={"system":system.model_dump(),"requirements":[r.model_dump() for r in requirements]}
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()[:16]
    return f"{system.id}-{digest}"

def assess(system, requirements):
    results=[deterministic_check(system,r) for r in requirements]
    overall="NON_COMPLIANT" if any(r.status=="FAIL" for r in results) else             "UNCERTAIN" if any(r.status=="UNCERTAIN" for r in results) else "COMPLIANT"
    return ComplianceReport(
        system_id=system.id,
        system_version=system.version,
        overall_status=overall,
        results=results,
        trace_id=trace_id(system,requirements)
    )
