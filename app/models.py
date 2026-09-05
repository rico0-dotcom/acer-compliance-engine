from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field

Status = Literal["PASS", "FAIL", "UNCERTAIN"]

class Provenance(BaseModel):
    source_type: str = "unknown"
    source_id: str | None = None
    source_url: str | None = None
    provision: str | None = None
    retrieval_date: str | None = None
    validator: str | None = None
    validation_status: Literal["UNVALIDATED","HUMAN_VALIDATED","EXPERT_VALIDATED"] = "UNVALIDATED"

class RegulatoryRecord(BaseModel):
    id: str
    regulation: str
    jurisdiction: str
    title: str
    effective_date: str | None = None
    applicability: str | None = None
    source: Provenance
    notes: str | None = None

class Requirement(BaseModel):
    id: str
    title: str
    regulation: str
    provision: str
    category: str
    obligation: str
    actor: str
    condition: dict[str, Any] = Field(default_factory=dict)
    system_property: str | None = None
    rule: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    evidence_expected: list[str] = Field(default_factory=list)
    adaptation_tactics: list[str] = Field(default_factory=list)
    provenance: Provenance
    ambiguity: float = 0.0

class Component(BaseModel):
    id: str
    type: str
    properties: dict[str, Any] = Field(default_factory=dict)

class DataAsset(BaseModel):
    id: str
    classification: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)

class Flow(BaseModel):
    source: str
    target: str
    data: str | None = None

class SystemModel(BaseModel):
    id: str
    name: str
    domain: str
    version: str = "1.0"
    components: list[Component]
    data: list[DataAsset] = Field(default_factory=list)
    flows: list[Flow] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    objectives: dict[str, float] = Field(default_factory=dict)

class Evidence(BaseModel):
    type: str
    description: str
    source: str | None = None
    confidence: float = 1.0

class CheckResult(BaseModel):
    system_id: str
    requirement_id: str
    status: Status
    explanation: str
    evidence: list[Evidence] = Field(default_factory=list)
    remediation_options: list[str] = Field(default_factory=list)

class ComplianceReport(BaseModel):
    system_id: str
    system_version: str
    overall_status: Literal["COMPLIANT","NON_COMPLIANT","UNCERTAIN"]
    results: list[CheckResult]
    trace_id: str

class GroundTruthCase(BaseModel):
    system_id: str
    requirement_id: str
    expected_status: Status

class ExperimentRow(BaseModel):
    experiment_id: str
    system_id: str
    requirement_id: str
    expected_status: Status
    predicted_status: Status
    correct: bool
    evidence_count: int
    adaptation_attempted: bool = False
    adaptation_success: bool = False
    adaptation_steps: int = 0
