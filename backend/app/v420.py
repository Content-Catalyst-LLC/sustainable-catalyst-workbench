"""Workbench v4.2.0 — Workflow Templates and Guided Scientific/Engineering Project Creation."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import re
from typing import Any, Dict, List, Literal, Optional, Set

from fastapi import APIRouter
from pydantic import BaseModel, Field

VERSION = "4.2.0"
EXPECTED_STUDIOS = 24
router = APIRouter(prefix="/v420", tags=["workbench-v420"])

DOMAIN_ALIASES = {
    "energy": "energy-engineering",
    "electrical": "electrical-embedded",
    "mechanical": "mechanical-thermal",
    "civil": "civil-infrastructure",
    "architecture": "architecture-building",
    "urban": "urban-spatial",
    "cities": "sustainable-cities",
    "circular": "circular-economy",
    "economics": "comparative-economics",
    "aerospace": "aerospace-flight",
    "rocket": "rocket-spaceflight",
    "biology": "biology-computational",
    "astronomy": "astronomy-astrophysics",
    "health": "health-human-services",
}

BUILTIN_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "scientific-investigation": {
        "templateId": "scientific-investigation",
        "title": "Scientific Investigation",
        "projectType": "research",
        "domains": ["physics", "chemistry", "biology-computational", "microbiology", "biochemistry", "astronomy-astrophysics"],
        "summary": "Question-driven investigation with hypotheses, controls, measurements, uncertainty, evidence, and reproducible reporting.",
        "stages": ["frame", "evidence", "protocol", "measure", "analyze", "validate", "report"],
        "requiredCapabilities": ["research", "experiments", "instrumentation", "visualization", "documentation", "reviews"],
        "defaultRequirements": [
            {"id": "question", "title": "Document a testable research question", "priority": "must"},
            {"id": "hypothesis", "title": "Record hypotheses or explicit exploratory intent", "priority": "must"},
            {"id": "controls", "title": "Define controls, comparators, and confounders", "priority": "must"},
            {"id": "uncertainty", "title": "Quantify measurement and analytical uncertainty", "priority": "must"},
            {"id": "reproducibility", "title": "Preserve data, code, versions, and methods", "priority": "must"},
        ],
        "defaultGates": [
            {"id": "protocol-review", "title": "Protocol reviewed before execution", "requiredEvidenceTypes": ["protocol", "safety-boundary"]},
            {"id": "analysis-validation", "title": "Analysis validated before conclusions", "requiredEvidenceTypes": ["dataset", "calculation", "uncertainty"]},
            {"id": "report-review", "title": "Report reviewed before release", "requiredEvidenceTypes": ["report", "review-snapshot"]},
        ],
        "recommendedRoles": ["project-owner", "researcher", "reviewer"],
        "deliverables": ["protocol", "dataset", "analysis-record", "validation-report", "technical-report"],
    },
    "engineering-design": {
        "templateId": "engineering-design",
        "title": "Engineering Design and Verification",
        "projectType": "engineering",
        "domains": ["energy-engineering", "electrical-embedded", "mechanical-thermal", "civil-infrastructure", "architecture-building", "aerospace-flight", "rocket-spaceflight"],
        "summary": "Requirements-led design with alternatives, calculations, interfaces, hazards, verification, and technical sign-off.",
        "stages": ["need", "requirements", "concepts", "model", "prototype", "verify", "release"],
        "requiredCapabilities": ["simulation", "runtime", "documentation", "reviews", "handoffs", "devices"],
        "defaultRequirements": [
            {"id": "design-basis", "title": "Establish the design basis and operating envelope", "priority": "must"},
            {"id": "requirements", "title": "Create measurable functional and nonfunctional requirements", "priority": "must"},
            {"id": "interfaces", "title": "Document physical, electrical, data, and organizational interfaces", "priority": "must"},
            {"id": "hazards", "title": "Identify hazards, failure modes, and protective controls", "priority": "must"},
            {"id": "verification", "title": "Map every requirement to a verification method", "priority": "must"},
        ],
        "defaultGates": [
            {"id": "requirements-baseline", "title": "Requirements baseline approved", "requiredEvidenceTypes": ["requirements", "review-snapshot"]},
            {"id": "design-review", "title": "Design review completed", "requiredEvidenceTypes": ["calculation", "model", "risk-record"]},
            {"id": "verification-complete", "title": "Verification evidence complete", "requiredEvidenceTypes": ["verification-report", "traceability-matrix"]},
        ],
        "recommendedRoles": ["project-owner", "engineer", "reviewer", "approver"],
        "deliverables": ["requirements-baseline", "design-record", "model-package", "verification-report", "technical-dossier"],
    },
    "instrument-validation": {
        "templateId": "instrument-validation",
        "title": "Instrument, Sensor, and Measurement Validation",
        "projectType": "validation",
        "domains": ["chemistry", "physics", "electrical-embedded", "mechanical-thermal", "biomedical-biosignals", "microbiology"],
        "summary": "Calibration, acquisition, uncertainty, acceptance limits, traceability, and instrument-session validation.",
        "stages": ["specify", "calibrate", "acquire", "analyze", "challenge", "accept", "monitor"],
        "requiredCapabilities": ["instrumentation", "devices", "experiments", "visualization", "reviews"],
        "defaultRequirements": [
            {"id": "measurement-range", "title": "Define range, resolution, accuracy, and bandwidth", "priority": "must"},
            {"id": "calibration", "title": "Document calibration standards and traceability", "priority": "must"},
            {"id": "uncertainty-budget", "title": "Build an uncertainty budget", "priority": "must"},
            {"id": "acceptance", "title": "Define measurable acceptance criteria", "priority": "must"},
        ],
        "defaultGates": [
            {"id": "calibration-valid", "title": "Calibration evidence is current", "requiredEvidenceTypes": ["calibration-record", "reference-standard"]},
            {"id": "measurement-valid", "title": "Measurement system meets acceptance criteria", "requiredEvidenceTypes": ["dataset", "uncertainty", "acceptance-report"]},
        ],
        "recommendedRoles": ["project-owner", "instrument-operator", "reviewer"],
        "deliverables": ["calibration-record", "measurement-plan", "dataset", "uncertainty-budget", "validation-report"],
    },
    "predictive-analysis": {
        "templateId": "predictive-analysis",
        "title": "Predictive Analytics and Model Evaluation",
        "projectType": "analytics",
        "domains": ["comparative-economics", "sustainable-cities", "health-human-services", "biology-computational", "energy-engineering", "general"],
        "summary": "Dataset profiling, leakage-safe experiment design, validation, uncertainty, subgroup checks, drift monitoring, and model cards.",
        "stages": ["question", "data", "split", "baseline", "model", "validate", "monitor", "document"],
        "requiredCapabilities": ["intelligence", "visualization", "runtime", "reviews", "documentation"],
        "defaultRequirements": [
            {"id": "intended-use", "title": "Document intended and prohibited uses", "priority": "must"},
            {"id": "data-provenance", "title": "Preserve dataset provenance and permissions", "priority": "must"},
            {"id": "leakage-control", "title": "Prevent target, time, and post-outcome leakage", "priority": "must"},
            {"id": "baseline", "title": "Compare against transparent baselines", "priority": "must"},
            {"id": "subgroups", "title": "Evaluate meaningful subgroup performance", "priority": "should"},
        ],
        "defaultGates": [
            {"id": "data-review", "title": "Data and split plan reviewed", "requiredEvidenceTypes": ["dataset-profile", "split-plan", "leakage-audit"]},
            {"id": "model-validation", "title": "Model validation completed", "requiredEvidenceTypes": ["validation-report", "uncertainty", "model-card"]},
            {"id": "deployment-review", "title": "Human deployment review completed", "requiredEvidenceTypes": ["risk-record", "review-snapshot"]},
        ],
        "recommendedRoles": ["project-owner", "analyst", "domain-reviewer", "approver"],
        "deliverables": ["dataset-profile", "experiment-plan", "validation-report", "model-card", "monitoring-plan"],
    },
    "sustainability-systems-assessment": {
        "templateId": "sustainability-systems-assessment",
        "title": "Sustainability Systems Assessment",
        "projectType": "systems-assessment",
        "domains": ["energy-engineering", "urban-spatial", "sustainable-cities", "circular-economy", "comparative-economics", "architecture-building"],
        "summary": "Boundary-aware systems assessment with indicators, scenarios, tradeoffs, uncertainty, sources, and decision handoffs.",
        "stages": ["scope", "system-map", "evidence", "indicators", "scenarios", "tradeoffs", "brief"],
        "requiredCapabilities": ["connected", "handoffs", "simulation", "visualization", "library", "documentation"],
        "defaultRequirements": [
            {"id": "system-boundary", "title": "Define spatial, temporal, organizational, and lifecycle boundaries", "priority": "must"},
            {"id": "stakeholders", "title": "Document affected stakeholders and distributional effects", "priority": "must"},
            {"id": "indicators", "title": "Use sourced indicators with methods and freshness", "priority": "must"},
            {"id": "scenarios", "title": "Compare multiple scenarios and a baseline", "priority": "must"},
            {"id": "tradeoffs", "title": "Make uncertainty and tradeoffs explicit", "priority": "must"},
        ],
        "defaultGates": [
            {"id": "scope-review", "title": "Assessment scope reviewed", "requiredEvidenceTypes": ["system-boundary", "stakeholder-record"]},
            {"id": "evidence-review", "title": "Evidence and indicators reviewed", "requiredEvidenceTypes": ["source-record", "methodology", "freshness-record"]},
            {"id": "decision-brief-review", "title": "Decision brief reviewed", "requiredEvidenceTypes": ["scenario-record", "tradeoff-record", "review-snapshot"]},
        ],
        "recommendedRoles": ["project-owner", "systems-analyst", "domain-reviewer", "stakeholder-reviewer"],
        "deliverables": ["system-map", "indicator-register", "scenario-package", "tradeoff-analysis", "decision-brief"],
    },
    "lab-to-decision-brief": {
        "templateId": "lab-to-decision-brief",
        "title": "Laboratory Evidence to Decision Brief",
        "projectType": "connected-workflow",
        "domains": ["general"],
        "summary": "Connect Lab experiments and Workbench analysis to shared evidence, review, and a Decision Studio briefing packet.",
        "stages": ["question", "lab-contract", "experiment", "analysis", "shared-evidence", "review", "handoff"],
        "requiredCapabilities": ["laboratories", "experiments", "intelligence", "handoffs", "reviews", "connected"],
        "defaultRequirements": [
            {"id": "lab-contract", "title": "Create a domain laboratory experiment contract", "priority": "must"},
            {"id": "evidence-provenance", "title": "Preserve experiment and analysis provenance", "priority": "must"},
            {"id": "claim-boundary", "title": "Bound claims to the available evidence", "priority": "must"},
            {"id": "decision-handoff", "title": "Build a validated Decision Studio handoff packet", "priority": "must"},
        ],
        "defaultGates": [
            {"id": "experiment-reviewed", "title": "Experiment and safety boundaries reviewed", "requiredEvidenceTypes": ["experiment-contract", "safety-boundary"]},
            {"id": "evidence-reviewed", "title": "Shared evidence reviewed", "requiredEvidenceTypes": ["shared-evidence", "uncertainty", "review-snapshot"]},
            {"id": "handoff-validated", "title": "Decision handoff validated", "requiredEvidenceTypes": ["handoff-packet", "compatibility-report"]},
        ],
        "recommendedRoles": ["project-owner", "laboratory-researcher", "analyst", "decision-reviewer"],
        "deliverables": ["experiment-contract", "analysis-record", "shared-evidence-bundle", "review-snapshot", "decision-handoff"],
    },
}


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def slug(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return cleaned or fallback


def normalize_domain(value: str) -> str:
    domain = slug(value, "general")
    return DOMAIN_ALIASES.get(domain, domain)


def clean_secret_fields(value: Any) -> Any:
    if isinstance(value, list):
        return [clean_secret_fields(item) for item in value]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(token in lowered for token in ("password", "secret", "token", "api_key", "apikey", "privatekey")):
                continue
            result[key] = clean_secret_fields(item)
        return result
    return value


class TemplateCatalogRequest(BaseModel):
    domain: str = ""
    project_type: str = ""


class TemplateValidationRequest(BaseModel):
    template: Dict[str, Any] = Field(default_factory=dict)


class GuidedIntakeRequest(BaseModel):
    title: str
    domain: str = "general"
    project_type: str = "research"
    objective: str
    research_question: str = ""
    constraints: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    stakeholders: List[str] = Field(default_factory=list)
    data_classification: Literal["public", "internal", "restricted", "sensitive"] = "internal"
    team_mode: bool = False
    high_stakes: bool = False
    professional_review_required: bool = False


class RequirementPlanRequest(BaseModel):
    template_id: str
    domain: str = "general"
    objective: str = ""
    additional_requirements: List[Dict[str, Any]] = Field(default_factory=list)


class MilestonePlanRequest(BaseModel):
    template_id: str
    start_date: str = ""
    target_date: str = ""
    stage_duration_days: Dict[str, int] = Field(default_factory=dict)
    dependencies: List[Dict[str, str]] = Field(default_factory=list)


class ValidationGateRequest(BaseModel):
    template_id: str
    gates: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    approvals: List[Dict[str, Any]] = Field(default_factory=list)


class StarterEvidenceRequest(BaseModel):
    domain: str = "general"
    objective: str = ""
    source_hints: List[Dict[str, Any]] = Field(default_factory=list)
    include_methodology_placeholders: bool = True


class ScaffoldRequest(BaseModel):
    template_id: str
    intake: Dict[str, Any] = Field(default_factory=dict)
    requirements: List[Dict[str, Any]] = Field(default_factory=list)
    milestones: List[Dict[str, Any]] = Field(default_factory=list)
    validation_gates: List[Dict[str, Any]] = Field(default_factory=list)
    starter_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    team_bindings: List[Dict[str, Any]] = Field(default_factory=list)
    storage_mode: Literal["browser", "wordpress", "hybrid", "offline"] = "browser"


class AdaptTemplateRequest(BaseModel):
    template_id: str
    domain: str = "general"
    constraints: List[str] = Field(default_factory=list)
    high_stakes: bool = False
    team_mode: bool = False


class TemplatePackageRequest(BaseModel):
    template: Dict[str, Any] = Field(default_factory=dict)
    scaffold: Dict[str, Any] = Field(default_factory=dict)
    include_examples: bool = True


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "expectedStudioCount": EXPECTED_STUDIOS,
        "workspace": "guided-project-creation",
        "templateCount": len(BUILTIN_TEMPLATES),
        "privateByDefault": True,
        "browserFallback": True,
        "offlineFallback": True,
        "teamReady": True,
        "paidExternalDatabaseRequired": False,
        "automaticExperimentExecutionAuthorized": False,
        "automaticDeviceControlAuthorized": False,
        "automaticPublicationAuthorized": False,
        "automaticCertificationAuthorized": False,
        "humanReviewRequired": True,
    }


def catalog_templates(request: TemplateCatalogRequest) -> Dict[str, Any]:
    domain = normalize_domain(request.domain) if request.domain else ""
    project_type = slug(request.project_type, "") if request.project_type else ""
    templates = []
    for source in BUILTIN_TEMPLATES.values():
        if domain and domain not in source["domains"] and "general" not in source["domains"]:
            continue
        if project_type and source["projectType"] != project_type:
            continue
        item = json.loads(canonical(source))
        item["schema"] = "sc-workbench-workflow-template/1.0"
        item["version"] = VERSION
        item["templateHash"] = stable_hash(item)
        templates.append(item)
    templates.sort(key=lambda item: item["title"])
    report = {
        "schema": "sc-workbench-template-catalog/1.0",
        "version": VERSION,
        "filters": {"domain": domain, "projectType": project_type},
        "templates": templates,
        "templateCount": len(templates),
    }
    report["catalogHash"] = stable_hash(report)
    return {"ok": True, "catalog": report}


def validate_template(request: TemplateValidationRequest) -> Dict[str, Any]:
    template = dict(request.template)
    findings: List[Dict[str, Any]] = []
    required = ["templateId", "title", "projectType", "stages", "requiredCapabilities", "defaultRequirements", "defaultGates", "deliverables"]
    for field in required:
        if not template.get(field):
            findings.append({"severity": "high", "code": f"missing-{field}"})
    stages = [str(item).strip() for item in template.get("stages", []) if str(item).strip()]
    if len(stages) != len(set(stages)):
        findings.append({"severity": "medium", "code": "duplicate-stage"})
    requirements = template.get("defaultRequirements", [])
    requirement_ids = [str(item.get("id", "")).strip() for item in requirements]
    if len([item for item in requirement_ids if item]) != len(set(item for item in requirement_ids if item)):
        findings.append({"severity": "high", "code": "duplicate-requirement-id"})
    gates = template.get("defaultGates", [])
    if not gates:
        findings.append({"severity": "high", "code": "validation-gate-required"})
    for gate in gates:
        if not gate.get("requiredEvidenceTypes"):
            findings.append({"severity": "medium", "code": "gate-without-evidence", "gateId": gate.get("id", "")})
    normalized = clean_secret_fields(template)
    normalized["schema"] = "sc-workbench-workflow-template/1.0"
    normalized["version"] = VERSION
    normalized["privateByDefault"] = True
    normalized["automaticExecutionAuthorized"] = False
    normalized["automaticPublicationAuthorized"] = False
    normalized["templateHash"] = stable_hash(normalized)
    blocking = [item for item in findings if item["severity"] in {"high", "critical"}]
    return {"ok": not blocking, "template": normalized, "findings": findings, "blockingFindingCount": len(blocking)}


def build_guided_intake(request: GuidedIntakeRequest) -> Dict[str, Any]:
    findings = []
    if not request.title.strip():
        findings.append("project-title-required")
    if not request.objective.strip():
        findings.append("project-objective-required")
    if request.project_type == "research" and not request.research_question.strip():
        findings.append("research-question-recommended")
    professional_review = bool(request.professional_review_required or request.high_stakes)
    intake = {
        "schema": "sc-workbench-guided-project-intake/1.0",
        "version": VERSION,
        "projectId": slug(request.title, "guided-project"),
        "title": request.title.strip(),
        "domain": normalize_domain(request.domain),
        "projectType": slug(request.project_type, "research"),
        "objective": request.objective.strip(),
        "researchQuestion": request.research_question.strip(),
        "constraints": sorted({str(item).strip() for item in request.constraints if str(item).strip()}),
        "assumptions": sorted({str(item).strip() for item in request.assumptions if str(item).strip()}),
        "stakeholders": sorted({str(item).strip() for item in request.stakeholders if str(item).strip()}),
        "dataClassification": request.data_classification,
        "teamMode": bool(request.team_mode),
        "highStakes": bool(request.high_stakes),
        "professionalReviewRequired": professional_review,
        "privateByDefault": request.data_classification != "public",
        "humanReviewRequired": True,
        "automaticExecutionAuthorized": False,
        "automaticPublicationAuthorized": False,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    intake["intakeHash"] = stable_hash(intake)
    return {"ok": not any(item.endswith("required") for item in findings), "intake": intake, "findings": findings}


def build_requirement_plan(request: RequirementPlanRequest) -> Dict[str, Any]:
    template = BUILTIN_TEMPLATES.get(request.template_id)
    findings = []
    if not template:
        findings.append("unknown-template")
        template = {"defaultRequirements": []}
    merged: Dict[str, Dict[str, Any]] = {}
    for raw in list(template.get("defaultRequirements", [])) + list(request.additional_requirements):
        title = str(raw.get("title", "")).strip()
        item_id = slug(str(raw.get("id") or title), "requirement")
        if not title:
            findings.append(f"requirement-title-required:{item_id}")
            continue
        priority = str(raw.get("priority", "should")).lower()
        if priority not in {"must", "should", "could"}:
            priority = "should"
        item = {
            "requirementId": item_id,
            "title": title,
            "priority": priority,
            "verificationMethod": str(raw.get("verificationMethod", "review")),
            "source": str(raw.get("source", "template")),
            "status": "planned",
            "linkedRecordIds": [],
        }
        if item_id in merged and merged[item_id] != item:
            findings.append(f"duplicate-requirement-merged:{item_id}")
        merged[item_id] = item
    requirements = sorted(merged.values(), key=lambda item: ({"must": 0, "should": 1, "could": 2}[item["priority"]], item["requirementId"]))
    plan = {
        "schema": "sc-workbench-guided-requirement-plan/1.0",
        "version": VERSION,
        "templateId": request.template_id,
        "domain": normalize_domain(request.domain),
        "objective": request.objective.strip(),
        "requirements": requirements,
        "requirementCount": len(requirements),
        "mustCount": sum(1 for item in requirements if item["priority"] == "must"),
        "traceabilityComplete": False,
        "automaticApprovalAuthorized": False,
    }
    plan["planHash"] = stable_hash(plan)
    return {"ok": bool(requirements) and "unknown-template" not in findings, "plan": plan, "findings": findings}


def _parse_date(value: str, fallback: datetime) -> datetime:
    if not value:
        return fallback
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return fallback


def build_milestone_plan(request: MilestonePlanRequest) -> Dict[str, Any]:
    template = BUILTIN_TEMPLATES.get(request.template_id)
    if not template:
        return {"ok": False, "plan": {}, "findings": ["unknown-template"]}
    start = _parse_date(request.start_date, datetime.now(timezone.utc))
    current = start
    milestones = []
    for index, stage in enumerate(template["stages"], 1):
        duration = max(1, int(request.stage_duration_days.get(stage, 7)))
        due = current + timedelta(days=duration)
        milestones.append({
            "milestoneId": f"m{index:02d}-{stage}",
            "stage": stage,
            "sequence": index,
            "startAt": current.date().isoformat(),
            "dueAt": due.date().isoformat(),
            "durationDays": duration,
            "status": "planned",
            "dependsOn": [milestones[-1]["milestoneId"]] if milestones else [],
        })
        current = due
    findings = []
    target = _parse_date(request.target_date, current) if request.target_date else current
    if request.target_date and target < current:
        findings.append("target-date-before-planned-completion")
    plan = {
        "schema": "sc-workbench-guided-milestone-plan/1.0",
        "version": VERSION,
        "templateId": request.template_id,
        "startAt": start.date().isoformat(),
        "plannedCompletionAt": current.date().isoformat(),
        "requestedTargetAt": target.date().isoformat(),
        "milestones": milestones,
        "milestoneCount": len(milestones),
        "automaticScheduleCommitAuthorized": False,
    }
    plan["planHash"] = stable_hash(plan)
    return {"ok": not findings, "plan": plan, "findings": findings}


def evaluate_validation_gates(request: ValidationGateRequest) -> Dict[str, Any]:
    template = BUILTIN_TEMPLATES.get(request.template_id, {})
    gates = request.gates or list(template.get("defaultGates", []))
    evidence_types = {str(item.get("type", "")).strip() for item in request.evidence if str(item.get("type", "")).strip()}
    approved_gates = {str(item.get("gateId", "")).strip() for item in request.approvals if str(item.get("status", "")).lower() == "approved"}
    results = []
    for raw in gates:
        gate_id = slug(str(raw.get("id") or raw.get("gateId") or raw.get("title", "")), "gate")
        required = sorted({str(item).strip() for item in raw.get("requiredEvidenceTypes", []) if str(item).strip()})
        missing = [item for item in required if item not in evidence_types]
        human_approved = gate_id in approved_gates
        results.append({
            "gateId": gate_id,
            "title": str(raw.get("title", gate_id)),
            "requiredEvidenceTypes": required,
            "missingEvidenceTypes": missing,
            "evidenceComplete": not missing,
            "humanApproved": human_approved,
            "state": "passed" if not missing and human_approved else ("approval-required" if not missing else "blocked"),
        })
    all_passed = bool(results) and all(item["state"] == "passed" for item in results)
    report = {
        "schema": "sc-workbench-guided-validation-gate-report/1.0",
        "version": VERSION,
        "templateId": request.template_id,
        "gates": results,
        "gateCount": len(results),
        "passedGateCount": sum(1 for item in results if item["state"] == "passed"),
        "allGatesPassed": all_passed,
        "humanApprovalRequired": True,
        "automaticCertificationAuthorized": False,
        "automaticPublicationAuthorized": False,
    }
    report["reportHash"] = stable_hash(report)
    return {"ok": all_passed, "report": report}


def build_starter_evidence(request: StarterEvidenceRequest) -> Dict[str, Any]:
    domain = normalize_domain(request.domain)
    categories = ["source-record", "methodology", "assumption", "uncertainty", "review-note"]
    if domain in {"electrical-embedded", "mechanical-thermal", "civil-infrastructure", "aerospace-flight", "rocket-spaceflight"}:
        categories += ["design-basis", "calculation", "risk-record", "verification-record"]
    elif domain in {"physics", "chemistry", "biology-computational", "microbiology", "biochemistry"}:
        categories += ["protocol", "dataset", "measurement", "calibration-record"]
    elif domain in {"comparative-economics", "sustainable-cities", "urban-spatial", "health-human-services"}:
        categories += ["indicator", "population-boundary", "scenario-record", "stakeholder-record"]
    records = []
    for index, category in enumerate(dict.fromkeys(categories), 1):
        record = {
            "evidenceId": f"starter-{index:02d}-{category}",
            "type": category,
            "title": category.replace("-", " ").title(),
            "status": "placeholder",
            "verified": False,
            "sourceRequired": True,
            "claimUseAuthorized": False,
        }
        record["recordHash"] = stable_hash(record)
        records.append(record)
    for raw in request.source_hints:
        hint = clean_secret_fields(raw)
        hint.update({"type": hint.get("type", "source-hint"), "status": "unverified", "verified": False, "claimUseAuthorized": False})
        hint["recordHash"] = stable_hash(hint)
        records.append(hint)
    package = {
        "schema": "sc-workbench-starter-evidence-package/1.0",
        "version": VERSION,
        "domain": domain,
        "objective": request.objective.strip(),
        "records": records,
        "recordCount": len(records),
        "allRecordsRequireVerification": True,
        "automaticSourceRetrievalAuthorized": False,
        "automaticClaimApprovalAuthorized": False,
    }
    package["packageHash"] = stable_hash(package)
    return {"ok": True, "package": package}


def build_project_scaffold(request: ScaffoldRequest) -> Dict[str, Any]:
    template = BUILTIN_TEMPLATES.get(request.template_id)
    findings = []
    if not template:
        findings.append("unknown-template")
        template = {"requiredCapabilities": [], "deliverables": [], "recommendedRoles": []}
    intake = clean_secret_fields(request.intake)
    project_id = slug(str(intake.get("projectId") or intake.get("title") or request.template_id), "guided-project")
    bindings = []
    for raw in request.team_bindings:
        user_id = str(raw.get("userId", "")).strip()
        role = str(raw.get("role", "viewer")).strip().lower()
        if user_id:
            bindings.append({"userId": user_id, "role": role, "status": "planned"})
    records = {
        "intake": intake,
        "requirements": clean_secret_fields(request.requirements),
        "milestones": clean_secret_fields(request.milestones),
        "validationGates": clean_secret_fields(request.validation_gates),
        "starterEvidence": clean_secret_fields(request.starter_evidence),
    }
    scaffold = {
        "schema": "sc-workbench-guided-project-scaffold/1.0",
        "version": VERSION,
        "projectId": project_id,
        "title": str(intake.get("title") or template.get("title") or "Guided Workbench Project"),
        "templateId": request.template_id,
        "domain": normalize_domain(str(intake.get("domain", "general"))),
        "projectType": str(intake.get("projectType", template.get("projectType", "research"))),
        "storageMode": request.storage_mode,
        "privateByDefault": bool(intake.get("privateByDefault", True)),
        "requiredCapabilities": list(template.get("requiredCapabilities", [])),
        "recommendedStudioRoutes": list(template.get("requiredCapabilities", [])),
        "deliverables": list(template.get("deliverables", [])),
        "recommendedRoles": list(template.get("recommendedRoles", [])),
        "teamBindings": bindings,
        "records": records,
        "recordSchemas": {
            "project": "sc-workbench-connected-project/1.0",
            "requirement": "sc-workbench-guided-requirement/1.0",
            "milestone": "sc-workbench-guided-milestone/1.0",
            "validationGate": "sc-workbench-guided-validation-gate/1.0",
            "evidence": "sc-workbench-shared-evidence/1.0",
        },
        "humanReviewRequired": True,
        "automaticExecutionAuthorized": False,
        "automaticDeviceControlAuthorized": False,
        "automaticPublicationAuthorized": False,
        "automaticCertificationAuthorized": False,
    }
    scaffold["scaffoldHash"] = stable_hash(scaffold)
    return {"ok": not findings, "scaffold": scaffold, "findings": findings}


def adapt_template(request: AdaptTemplateRequest) -> Dict[str, Any]:
    source = BUILTIN_TEMPLATES.get(request.template_id)
    if not source:
        return {"ok": False, "plan": {}, "findings": ["unknown-template"]}
    additions = []
    if request.high_stakes:
        additions += [
            {"type": "requirement", "id": "qualified-review", "title": "Require qualified domain review"},
            {"type": "gate", "id": "high-stakes-release-review", "title": "Complete high-stakes release review"},
        ]
    if request.team_mode:
        additions.append({"type": "role", "id": "independent-reviewer", "title": "Assign an independent reviewer"})
    if request.constraints:
        additions.append({"type": "constraint-register", "items": sorted(set(request.constraints))})
    plan = {
        "schema": "sc-workbench-template-adaptation-plan/1.0",
        "version": VERSION,
        "sourceTemplateId": request.template_id,
        "sourceTemplateHash": stable_hash(source),
        "domain": normalize_domain(request.domain),
        "additions": additions,
        "sourceTemplateMutated": False,
        "requiresHumanAcceptance": True,
        "automaticTemplateReplacementAuthorized": False,
    }
    plan["planHash"] = stable_hash(plan)
    return {"ok": True, "plan": plan, "findings": []}


def build_template_package(request: TemplatePackageRequest) -> Dict[str, Any]:
    template = clean_secret_fields(request.template)
    scaffold = clean_secret_fields(request.scaffold)
    package = {
        "schema": "sc-workbench-guided-project-template-package/1.0",
        "version": VERSION,
        "exportedAt": datetime.now(timezone.utc).isoformat(),
        "template": template,
        "scaffold": scaffold,
        "examplesIncluded": bool(request.include_examples),
        "secretsIncluded": False,
        "requiresExplicitImport": True,
        "automaticCloudUpload": False,
        "automaticProjectCreationAuthorized": False,
    }
    package["packageHash"] = stable_hash(package)
    return {"ok": bool(template or scaffold), "package": package}


@router.get("/status")
def status_route() -> Dict[str, Any]:
    return status()


@router.post("/templates/catalog")
def catalog_route(request: TemplateCatalogRequest) -> Dict[str, Any]:
    return catalog_templates(request)


@router.post("/template/validate")
def validate_route(request: TemplateValidationRequest) -> Dict[str, Any]:
    return validate_template(request)


@router.post("/intake/build")
def intake_route(request: GuidedIntakeRequest) -> Dict[str, Any]:
    return build_guided_intake(request)


@router.post("/requirements/plan")
def requirements_route(request: RequirementPlanRequest) -> Dict[str, Any]:
    return build_requirement_plan(request)


@router.post("/milestones/plan")
def milestones_route(request: MilestonePlanRequest) -> Dict[str, Any]:
    return build_milestone_plan(request)


@router.post("/validation/gates")
def gates_route(request: ValidationGateRequest) -> Dict[str, Any]:
    return evaluate_validation_gates(request)


@router.post("/evidence/starter")
def evidence_route(request: StarterEvidenceRequest) -> Dict[str, Any]:
    return build_starter_evidence(request)


@router.post("/scaffold/build")
def scaffold_route(request: ScaffoldRequest) -> Dict[str, Any]:
    return build_project_scaffold(request)


@router.post("/template/adapt")
def adapt_route(request: AdaptTemplateRequest) -> Dict[str, Any]:
    return adapt_template(request)


@router.post("/package/build")
def package_route(request: TemplatePackageRequest) -> Dict[str, Any]:
    return build_template_package(request)
