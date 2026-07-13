from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

VERSION = "3.7.0"
DOMAIN_PROFILE_SCHEMA = "sc-workbench-lab-domain-profile/1.0"
CALCULATION_SCHEMA = "sc-workbench-lab-calculation-contract/1.0"
EXPERIMENT_SCHEMA = "sc-workbench-lab-experiment-contract/1.0"
VALIDATION_SCHEMA = "sc-workbench-lab-validation-contract/1.0"
NOTEBOOK_SCHEMA = "sc-workbench-lab-notebook-entry/1.0"
REPORT_SCHEMA = "sc-workbench-lab-report-template/1.0"
SYNC_SCHEMA = "sc-workbench-lab-sync-plan/1.0"
BUNDLE_SCHEMA = "sc-workbench-lab-integration-bundle/1.0"
EQUIVALENCE_SCHEMA = "sc-workbench-lab-language-equivalence/1.0"

router = APIRouter(prefix="/v370", tags=["workbench-v370"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _hash(value: Any) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def _slug(value: Any, fallback: str = "record") -> str:
    text = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return text[:120] or fallback


DOMAIN_REGISTRY: dict[str, dict[str, Any]] = {
    "physics": {
        "label": "Physics Laboratory", "labVersion": "0.4+", "status": "active",
        "capabilities": ["mechanics", "electromagnetism", "waves", "thermodynamics", "uncertainty"],
        "defaultUnits": "SI", "validation": ["dimensional-consistency", "boundary-conditions", "uncertainty", "independent-check"],
    },
    "chemistry": {
        "label": "Chemistry and Spectrometry", "labVersion": "0.3+", "status": "active",
        "capabilities": ["stoichiometry", "solutions", "spectrometry", "kinetics", "calibration"],
        "defaultUnits": "SI-compatible", "validation": ["mass-balance", "unit-consistency", "calibration", "method-blank", "uncertainty"],
    },
    "biology": {
        "label": "Biology and Computational Biology", "labVersion": "0.5+", "status": "active",
        "capabilities": ["population-models", "sequence-analysis", "ecology", "biostatistics", "microscopy"],
        "defaultUnits": "domain-specific", "validation": ["controls", "replicates", "sample-provenance", "statistical-review", "biosafety-boundary"],
    },
    "astronomy": {
        "label": "Astronomy and Astrophysics", "labVersion": "0.6+", "status": "active",
        "capabilities": ["orbital-mechanics", "photometry", "spectra", "cosmology", "telescope-data"],
        "defaultUnits": "SI/astronomical", "validation": ["coordinate-frame", "epoch", "instrument-calibration", "uncertainty", "source-provenance"],
    },
    "energy-engineering": {
        "label": "Energy and Engineering Systems", "labVersion": "0.9+", "status": "active",
        "capabilities": ["energy-balance", "power-systems", "efficiency", "storage", "systems-modeling"],
        "defaultUnits": "SI", "validation": ["energy-conservation", "rated-limits", "scenario-assumptions", "sensitivity", "safety-review"],
    },
    "electrical-embedded": {
        "label": "Electrical, Electronics, and Embedded Systems", "labVersion": "0.10+", "status": "active",
        "capabilities": ["circuits", "embedded-control", "signal-processing", "power-electronics", "instrumentation"],
        "defaultUnits": "SI", "validation": ["electrical-ratings", "timing", "signal-integrity", "thermal-margin", "hardware-review"],
    },
    "mechanical-thermal": {
        "label": "Mechanical and Thermal Engineering", "labVersion": "0.11+", "status": "active",
        "capabilities": ["statics", "dynamics", "fluids", "heat-transfer", "machine-design"],
        "defaultUnits": "SI", "validation": ["free-body-check", "material-properties", "factor-of-safety", "thermal-boundary", "independent-check"],
    },
    "civil-infrastructure": {
        "label": "Civil Engineering and Infrastructure Systems", "labVersion": "0.12+", "status": "active",
        "capabilities": ["structures", "hydrology", "transport", "geotechnical", "infrastructure-resilience"],
        "defaultUnits": "SI", "validation": ["load-cases", "site-assumptions", "code-reference", "factor-of-safety", "licensed-review-boundary"],
    },
    "architecture-building": {
        "label": "Architecture and Building Performance", "labVersion": "0.13+", "status": "active",
        "capabilities": ["building-energy", "daylighting", "envelope", "comfort", "materials"],
        "defaultUnits": "SI", "validation": ["climate-file", "geometry", "occupancy-assumptions", "energy-balance", "code-reference"],
    },
    "urban-spatial": {
        "label": "Urban Planning and Spatial Systems", "labVersion": "0.14+", "status": "active",
        "capabilities": ["gis", "accessibility", "land-use", "mobility", "scenario-comparison"],
        "defaultUnits": "spatial/domain-specific", "validation": ["coordinate-reference", "data-freshness", "coverage", "equity-review", "scenario-assumptions"],
    },
    "sustainable-cities": {
        "label": "Sustainable Cities and Urban Resilience", "labVersion": "0.15+", "status": "active",
        "capabilities": ["resilience", "emissions", "resource-flows", "adaptation", "equity"],
        "defaultUnits": "domain-specific", "validation": ["baseline", "system-boundary", "scenario-assumptions", "distributional-effects", "uncertainty"],
    },
    "circular-economy": {
        "label": "Circular Economy and Industrial Ecology", "labVersion": "0.16+", "status": "active",
        "capabilities": ["material-flow", "life-cycle", "waste", "industrial-symbiosis", "circularity"],
        "defaultUnits": "mass/energy", "validation": ["functional-unit", "system-boundary", "allocation-method", "mass-balance", "data-quality"],
    },
    "economics-development": {
        "label": "Comparative Economics and Development Systems", "labVersion": "0.17+", "status": "active",
        "capabilities": ["econometrics", "development-indicators", "distribution", "policy-scenarios", "cost-benefit"],
        "defaultUnits": "currency/index/domain-specific", "validation": ["price-year", "currency", "identification-strategy", "sensitivity", "distributional-review"],
    },
    "aerospace": {
        "label": "Aerospace Engineering and Flight Systems", "labVersion": "0.18+", "status": "active",
        "capabilities": ["aerodynamics", "flight-dynamics", "structures", "propulsion", "guidance"],
        "defaultUnits": "SI", "validation": ["reference-frame", "flight-envelope", "mass-properties", "stability-margin", "safety-review"],
    },
    "rocket-propulsion": {
        "label": "Rocket Propulsion and Spaceflight", "labVersion": "0.19+", "status": "active",
        "capabilities": ["rocket-equation", "propulsion-analysis", "trajectory", "thermal", "mission-budget"],
        "defaultUnits": "SI", "validation": ["mass-budget", "propellant-properties", "trajectory-assumptions", "thermal-margin", "safety-boundary"],
    },
    "microbiology": {
        "label": "Microbiology Laboratory", "labVersion": "0.20+", "status": "planned",
        "capabilities": ["growth-curves", "culture-records", "microscopy", "sequence-analysis", "bioprocess-observation"],
        "defaultUnits": "domain-specific", "validation": ["controls", "replicates", "sample-provenance", "biosafety-boundary", "qualified-review"],
    },
    "biochemistry": {
        "label": "Biochemistry and Molecular Analysis", "labVersion": "0.21+", "status": "planned",
        "capabilities": ["enzyme-kinetics", "molecular-assays", "spectroscopy", "binding", "pathway-models"],
        "defaultUnits": "SI-compatible", "validation": ["controls", "calibration", "assay-range", "replicates", "qualified-review"],
    },
    "biotechnology": {
        "label": "Biotechnology and Bioprocess Engineering", "labVersion": "0.22+", "status": "planned",
        "capabilities": ["bioreactors", "mass-transfer", "yield", "process-control", "scale-up"],
        "defaultUnits": "SI", "validation": ["mass-balance", "sterility-boundary", "scale-assumptions", "process-controls", "qualified-review"],
    },
    "biomedical": {
        "label": "Biomedical Engineering and Biosignals", "labVersion": "0.23+", "status": "planned",
        "capabilities": ["biosignals", "biomechanics", "medical-device-analysis", "imaging", "human-factors"],
        "defaultUnits": "SI/domain-specific", "validation": ["signal-quality", "calibration", "human-subject-boundary", "clinical-non-diagnostic-boundary", "qualified-review"],
    },
    "health-human-services": {
        "label": "Health and Human Services", "labVersion": "future", "status": "planned",
        "capabilities": ["public-health-analysis", "service-systems", "program-evaluation", "equity", "evidence-synthesis"],
        "defaultUnits": "domain-specific", "validation": ["non-diagnostic-boundary", "privacy", "population-context", "equity-review", "qualified-review"],
    },
}


class DomainProfileRequest(BaseModel):
    domain: str
    project_id: str = "default"
    lab_version: str = ""
    requested_capabilities: list[str] = Field(default_factory=list)


class CalculationContractRequest(BaseModel):
    domain: str
    project_id: str = "default"
    title: str = "Domain calculation"
    equation: str = ""
    inputs: dict[str, Any] = Field(default_factory=dict)
    units: dict[str, str] = Field(default_factory=dict)
    expected_outputs: list[str] = Field(default_factory=list)
    language: str = "python"
    evidence_ids: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class ExperimentContractRequest(BaseModel):
    domain: str
    project_id: str = "default"
    title: str = "Laboratory experiment"
    hypothesis: str = ""
    independent_variables: list[str] = Field(default_factory=list)
    dependent_variables: list[str] = Field(default_factory=list)
    controls: list[str] = Field(default_factory=list)
    instruments: list[str] = Field(default_factory=list)
    protocol_steps: list[str] = Field(default_factory=list)
    replicates: int = Field(default=1, ge=1, le=10000)
    safety_review_required: bool = False


class ValidationContractRequest(BaseModel):
    domain: str
    artifact_type: Literal["calculation", "experiment", "dataset", "model", "report", "device-run"] = "calculation"
    supplied_checks: list[str] = Field(default_factory=list)
    reviewer: str = ""
    evidence_ids: list[str] = Field(default_factory=list)


class NotebookEntryRequest(BaseModel):
    domain: str
    project_id: str = "default"
    title: str = "Laboratory notebook entry"
    observations: list[str] = Field(default_factory=list)
    calculation_ids: list[str] = Field(default_factory=list)
    experiment_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    attachments: list[str] = Field(default_factory=list)
    author: str = ""


class ReportTemplateRequest(BaseModel):
    domain: str
    project_id: str = "default"
    title: str = "Domain laboratory report"
    include_methods: bool = True
    include_validation: bool = True
    include_reproducibility: bool = True
    record_ids: list[str] = Field(default_factory=list)


class SyncPlanRequest(BaseModel):
    domain: str
    project_id: str = "default"
    workbench_hash: str = ""
    lab_hash: str = ""
    conflict_strategy: Literal["manual", "newest", "workbench", "lab"] = "manual"
    direction: Literal["bidirectional", "workbench-to-lab", "lab-to-workbench"] = "bidirectional"
    record_types: list[str] = Field(default_factory=lambda: ["calculations", "experiments", "notebook", "validation", "reports"])


class IntegrationBundleRequest(BaseModel):
    domain: str
    project_id: str = "default"
    records: list[dict[str, Any]] = Field(default_factory=list)
    source_application: str = "workbench"
    target_application: str = "lab"


class LanguageEquivalenceRequest(BaseModel):
    domain: str
    calculation_id: str = "calculation"
    equation: str = ""
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=lambda: ["python", "r", "javascript", "rust"])
    tolerance: float = Field(default=1e-9, gt=0)


def _domain(key: str) -> tuple[str, dict[str, Any]]:
    slug = _slug(key, "")
    if slug not in DOMAIN_REGISTRY:
        raise ValueError(f"unsupported laboratory domain: {key}")
    return slug, DOMAIN_REGISTRY[slug]


def list_domain_registry() -> dict[str, Any]:
    domains = []
    for key, item in DOMAIN_REGISTRY.items():
        domains.append({"domain": key, **item})
    record = {"schema": "sc-workbench-lab-domain-registry/1.0", "version": VERSION, "domains": domains, "domainCount": len(domains), "generatedAt": _now()}
    record["registryHash"] = _hash(record)
    return {"ok": True, "registry": record, "registryHash": record["registryHash"]}


def build_domain_profile(request: DomainProfileRequest) -> dict[str, Any]:
    key, domain = _domain(request.domain)
    requested = sorted({_slug(item, "") for item in request.requested_capabilities if _slug(item, "")})
    available = list(domain["capabilities"])
    missing = [item for item in requested if item not in available]
    record = {
        "schema": DOMAIN_PROFILE_SCHEMA, "version": VERSION, "domain": key, "label": domain["label"],
        "projectId": _slug(request.project_id, "default"), "labVersion": request.lab_version or domain["labVersion"],
        "domainStatus": domain["status"], "availableCapabilities": available, "requestedCapabilities": requested,
        "missingCapabilities": missing, "defaultUnits": domain["defaultUnits"],
        "validationRequirements": list(domain["validation"]), "humanReviewRequired": True,
        "generatedAt": _now(),
    }
    record["profileHash"] = _hash(record)
    return {"ok": not missing, "profile": record, "profileHash": record["profileHash"]}


def build_calculation_contract(request: CalculationContractRequest) -> dict[str, Any]:
    key, domain = _domain(request.domain)
    if not request.inputs:
        raise ValueError("at least one calculation input is required")
    missing_units = sorted([name for name in request.inputs if not request.units.get(name)])
    calculation_id = f"calc-{_slug(request.title, 'calculation')}-{_hash(request.inputs)[:10]}"
    record = {
        "schema": CALCULATION_SCHEMA, "version": VERSION, "calculationId": calculation_id,
        "domain": key, "domainLabel": domain["label"], "projectId": _slug(request.project_id, "default"),
        "title": request.title.strip() or "Domain calculation", "equation": request.equation.strip(),
        "inputs": request.inputs, "units": request.units, "missingUnits": missing_units,
        "expectedOutputs": request.expected_outputs, "language": _slug(request.language, "python"),
        "evidenceIds": sorted(set(request.evidence_ids)), "assumptions": request.assumptions,
        "validationRequirements": list(domain["validation"]), "dimensionalReviewRequired": bool(missing_units or not request.equation),
        "humanReviewRequired": True, "createdAt": _now(),
    }
    record["calculationHash"] = _hash(record)
    return {"ok": not missing_units, "contract": record, "calculationHash": record["calculationHash"]}


def build_experiment_contract(request: ExperimentContractRequest) -> dict[str, Any]:
    key, domain = _domain(request.domain)
    if not request.protocol_steps:
        raise ValueError("at least one protocol step is required")
    if not request.dependent_variables:
        raise ValueError("at least one dependent variable is required")
    biological = key in {"biology", "microbiology", "biochemistry", "biotechnology", "biomedical", "health-human-services"}
    safety_required = bool(request.safety_review_required or biological or key in {"rocket-propulsion", "aerospace"})
    experiment_id = f"exp-{_slug(request.title, 'experiment')}-{_hash(request.protocol_steps)[:10]}"
    record = {
        "schema": EXPERIMENT_SCHEMA, "version": VERSION, "experimentId": experiment_id,
        "domain": key, "domainLabel": domain["label"], "projectId": _slug(request.project_id, "default"),
        "title": request.title.strip() or "Laboratory experiment", "hypothesis": request.hypothesis.strip(),
        "independentVariables": request.independent_variables, "dependentVariables": request.dependent_variables,
        "controls": request.controls, "instruments": request.instruments, "protocolSteps": request.protocol_steps,
        "replicates": request.replicates, "reproducibilityControls": ["fixed protocol version", "timestamped observations", "instrument identity", "raw data preservation"],
        "validationRequirements": list(domain["validation"]), "safetyReviewRequired": safety_required,
        "executionAuthorized": False, "humanReviewRequired": True, "createdAt": _now(),
    }
    record["experimentHash"] = _hash(record)
    return {"ok": True, "contract": record, "experimentHash": record["experimentHash"]}


def build_validation_contract(request: ValidationContractRequest) -> dict[str, Any]:
    key, domain = _domain(request.domain)
    required = list(domain["validation"])
    supplied = sorted(set(_slug(item, "") for item in request.supplied_checks if _slug(item, "")))
    missing = [item for item in required if item not in supplied]
    status = "blocked" if missing else ("review-ready" if request.reviewer else "review-required")
    record = {
        "schema": VALIDATION_SCHEMA, "version": VERSION, "domain": key, "domainLabel": domain["label"],
        "artifactType": request.artifact_type, "requiredChecks": required, "suppliedChecks": supplied,
        "missingChecks": missing, "reviewer": request.reviewer.strip(), "evidenceIds": sorted(set(request.evidence_ids)),
        "status": status, "autoValidated": False, "humanReviewRequired": True, "generatedAt": _now(),
    }
    record["validationHash"] = _hash(record)
    return {"ok": not missing and bool(request.reviewer), "validation": record, "validationHash": record["validationHash"]}


def build_notebook_entry(request: NotebookEntryRequest) -> dict[str, Any]:
    key, domain = _domain(request.domain)
    if not request.observations:
        raise ValueError("at least one observation is required")
    body = {
        "schema": NOTEBOOK_SCHEMA, "version": VERSION, "domain": key, "domainLabel": domain["label"],
        "projectId": _slug(request.project_id, "default"), "title": request.title.strip() or "Laboratory notebook entry",
        "observations": request.observations, "calculationIds": sorted(set(request.calculation_ids)),
        "experimentIds": sorted(set(request.experiment_ids)), "evidenceIds": sorted(set(request.evidence_ids)),
        "attachments": sorted(set(request.attachments)), "author": request.author.strip(), "recordedAt": _now(),
        "immutableSnapshotRecommended": True,
    }
    body["entryId"] = f"note-{key}-{_hash(body)[:12]}"
    body["entryHash"] = _hash(body)
    return {"ok": True, "entry": body, "entryHash": body["entryHash"]}


def build_report_template(request: ReportTemplateRequest) -> dict[str, Any]:
    key, domain = _domain(request.domain)
    sections = ["Executive summary", "Domain context", "Question and scope"]
    if request.include_methods:
        sections += ["Methods", "Inputs, units, and assumptions", "Instruments and software"]
    sections += ["Results", "Uncertainty and limitations"]
    if request.include_validation:
        sections += ["Validation evidence", "Requirement coverage", "Reviewer findings"]
    if request.include_reproducibility:
        sections += ["Reproducibility package", "Equivalent implementations", "Data and environment manifest"]
    sections += ["Safety and responsible-use boundary", "Citations", "Appendices"]
    record = {
        "schema": REPORT_SCHEMA, "version": VERSION, "domain": key, "domainLabel": domain["label"],
        "projectId": _slug(request.project_id, "default"), "title": request.title.strip() or "Domain laboratory report",
        "sections": sections, "recordIds": sorted(set(request.record_ids)), "publicationState": "draft",
        "humanReviewRequired": True, "generatedAt": _now(),
    }
    record["reportTemplateHash"] = _hash(record)
    return {"ok": True, "reportTemplate": record, "reportTemplateHash": record["reportTemplateHash"]}


def build_sync_plan(request: SyncPlanRequest) -> dict[str, Any]:
    key, domain = _domain(request.domain)
    conflict = bool(request.workbench_hash and request.lab_hash and request.workbench_hash != request.lab_hash)
    if not request.workbench_hash and not request.lab_hash:
        action = "initialize-both"
    elif conflict and request.conflict_strategy == "manual":
        action = "hold-for-review"
    elif request.direction == "workbench-to-lab" or request.conflict_strategy == "workbench":
        action = "send-workbench-to-lab"
    elif request.direction == "lab-to-workbench" or request.conflict_strategy == "lab":
        action = "send-lab-to-workbench"
    else:
        action = "compare-and-merge"
    record = {
        "schema": SYNC_SCHEMA, "version": VERSION, "domain": key, "domainLabel": domain["label"],
        "projectId": _slug(request.project_id, "default"), "direction": request.direction,
        "conflictStrategy": request.conflict_strategy, "workbenchHash": request.workbench_hash,
        "labHash": request.lab_hash, "conflictDetected": conflict, "action": action,
        "recordTypes": sorted(set(request.record_types)), "destructiveOverwrite": False,
        "backupRequired": conflict, "humanReviewRequired": conflict or request.conflict_strategy == "manual",
        "generatedAt": _now(),
    }
    record["syncPlanHash"] = _hash(record)
    return {"ok": action != "hold-for-review", "syncPlan": record, "syncPlanHash": record["syncPlanHash"]}


def build_integration_bundle(request: IntegrationBundleRequest) -> dict[str, Any]:
    key, domain = _domain(request.domain)
    record_manifest = []
    for index, record in enumerate(request.records):
        record_manifest.append({"index": index, "schema": str(record.get("schema", "unknown")), "recordHash": _hash(record)})
    manifest = {
        "schema": BUNDLE_SCHEMA, "version": VERSION, "domain": key, "domainLabel": domain["label"],
        "projectId": _slug(request.project_id, "default"), "sourceApplication": _slug(request.source_application, "workbench"),
        "targetApplication": _slug(request.target_application, "lab"), "recordCount": len(request.records),
        "records": record_manifest, "portable": True, "generatedAt": _now(),
    }
    manifest["manifestHash"] = _hash(manifest)
    bundle = {"manifest": manifest, "records": request.records}
    bundle["bundleHash"] = _hash(bundle)
    return {"ok": True, "bundle": bundle, "bundleHash": bundle["bundleHash"]}


def build_language_equivalence(request: LanguageEquivalenceRequest) -> dict[str, Any]:
    key, domain = _domain(request.domain)
    supported = {"python", "r", "javascript", "rust", "go", "c", "cpp", "haskell", "sql"}
    languages = []
    unsupported = []
    for language in request.languages:
        slug = _slug(language, "")
        if slug in supported and slug not in languages:
            languages.append(slug)
        elif slug and slug not in supported:
            unsupported.append(slug)
    if not languages:
        raise ValueError("at least one supported language is required")
    record = {
        "schema": EQUIVALENCE_SCHEMA, "version": VERSION, "domain": key, "domainLabel": domain["label"],
        "calculationId": _slug(request.calculation_id, "calculation"), "equation": request.equation,
        "inputs": request.inputs, "outputs": request.outputs, "languages": languages, "unsupportedLanguages": unsupported,
        "tolerance": request.tolerance, "fixtureRequirements": ["identical inputs", "identical units", "fixed constants", "recorded runtime versions"],
        "comparisonRequirements": ["absolute error", "relative error", "unit equivalence", "edge cases"],
        "humanReviewRequired": True, "generatedAt": _now(),
    }
    record["equivalenceHash"] = _hash(record)
    return {"ok": not unsupported, "plan": record, "equivalenceHash": record["equivalenceHash"]}


def _route(function, request):
    try:
        return function(request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/status")
def status():
    return {"ok": True, "version": VERSION, "schema": "sc-workbench-domain-laboratory-status/1.0", "domainCount": len(DOMAIN_REGISTRY), "physicalExecution": False, "clinicalDiagnosis": False, "licensedCertification": False}


@router.get("/domains")
def domains(): return list_domain_registry()


@router.post("/domain/profile")
def route_domain_profile(request: DomainProfileRequest): return _route(build_domain_profile, request)


@router.post("/calculation/contract")
def route_calculation(request: CalculationContractRequest): return _route(build_calculation_contract, request)


@router.post("/experiment/contract")
def route_experiment(request: ExperimentContractRequest): return _route(build_experiment_contract, request)


@router.post("/validation/contract")
def route_validation(request: ValidationContractRequest): return _route(build_validation_contract, request)


@router.post("/notebook/entry")
def route_notebook(request: NotebookEntryRequest): return _route(build_notebook_entry, request)


@router.post("/report/template")
def route_report(request: ReportTemplateRequest): return _route(build_report_template, request)


@router.post("/sync/plan")
def route_sync(request: SyncPlanRequest): return _route(build_sync_plan, request)


@router.post("/bundle/build")
def route_bundle(request: IntegrationBundleRequest): return _route(build_integration_bundle, request)


@router.post("/language/equivalence")
def route_equivalence(request: LanguageEquivalenceRequest): return _route(build_language_equivalence, request)
