"""Workbench v6.14.0 — Platform Integration Certification.

Final v6.x platform-integration hardening layer before v7.0.0.  The module
assembles deterministic Workbench-side conformance evidence for every Platform
Core bridge introduced in v6.4–v6.13 and prepares caller-reviewed requests for
Platform Core's v2.97 integration-certification registry.

Certification here means declared runtime-contract conformance evidence only.
It does not certify scientific validity or product quality, authorize or rank
products, infer missing evidence or reproducibility, resolve failed cases,
invoke products automatically, or determine truth.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v640 import CORE_RUNTIME_CONTRACT, _authorize_core_route, capabilities_record
from .v650 import PRODUCT_REF, adapter_manifest
from .v660 import CORE_UNIFIED_RUNTIME_CONTRACT, bridge_manifest
from .v670 import CORE_COMPUTATION_LINEAGE_CONTRACT, lineage_manifest
from .v680 import scenario_uncertainty_manifest
from .v690 import visual_reasoning_manifest
from .v6100 import predictive_manifest
from .v6110 import forensic_manifest
from .v6120 import integration_manifest
from .v6130 import experience_manifest

VERSION = APP_VERSION
SCHEMA = "sc-workbench-platform-integration-certification/1.0"
LOCAL_REPORT_SCHEMA = "sc-workbench-platform-integration-certification-report/1.0"
CORE_REQUEST_SCHEMA = "sc-workbench-core-platform-integration-certification-request/1.0"
CORE_CERTIFICATION_CONTRACT = "sc.research.platform-integration-certification.v1"
BRIDGE_REF = "workbench:/integration/core/certification"

router = APIRouter(tags=["workbench-v6140-platform-integration-certification"])

CORE_PATHS: Dict[str, str] = {
    "readiness": "/v1/research/integration-certification/readiness",
    "suites": "/v1/research/integration-certification/suites",
    "products": "/v1/research/integration-certification/products",
    "cases": "/v1/research/integration-certification/cases",
    "runs": "/v1/research/integration-certification/runs",
    "caseResults": "/v1/research/integration-certification/case-results",
    "exchangeChecks": "/v1/research/integration-certification/exchange-checks",
    "traceChecks": "/v1/research/integration-certification/trace-checks",
    "reproductionChecks": "/v1/research/integration-certification/reproduction-checks",
    "evidence": "/v1/research/integration-certification/evidence",
    "findings": "/v1/research/integration-certification/findings",
    "revisions": "/v1/research/integration-certification/revisions",
    "snapshots": "/v1/research/integration-certification/snapshots",
    "runReport": "/v1/research/integration-certification/runs/{run_id}/report",
    "suiteBundle": "/v1/research/integration-certification/suites/{suite_id}/bundle",
}

RESULT_STATUSES = {"pass", "fail", "blocked", "not_run", "not_applicable"}

REQUIRED_CORE_INTEGRATION_FLAGS = [
    "connectivityFoundation",
    "unifiedRuntimeContractAdapter",
    "unifiedResearchSessionBinding",
    "executionLineageBridge",
    "scenarioUncertaintyRuntime",
    "visualReasoningRuntimeAdapter",
    "predictiveIntelligenceRuntime",
    "forensicQuantitativeReconstructionRuntime",
    "researchStateReproductionSnapshotIntegration",
    "coreAwareWorkbenchExperience",
    "platformIntegrationCertification",
]

CASE_CATALOG: List[Dict[str, Any]] = [
    {
        "case_key": "workbench-connectivity-foundation",
        "operation": "connectivity",
        "object_type": "workbench.runtime",
        "requirement": "Workbench exposes Core-compatible health, capabilities, request-context and service-token boundaries.",
        "expected_evidence": ["/health", "/capabilities", "/integration/core/status"],
    },
    {
        "case_key": "workbench-unified-runtime-contract",
        "operation": "runtime-contract",
        "object_type": "workbench.runtime-contract-adapter",
        "requirement": "Workbench declares the unified runtime contract and builds reference-first requests without automatic Core dispatch.",
        "expected_evidence": ["/integration/core/runtime-contract/manifest"],
    },
    {
        "case_key": "workbench-unified-research-session",
        "operation": "research-session",
        "object_type": "workbench.research-session-bridge",
        "requirement": "Workbench requires Core-issued session IDs and prepares project/product/object bindings without fabricating Core identity.",
        "expected_evidence": ["/integration/core/unified-runtime/manifest"],
    },
    {
        "case_key": "workbench-execution-lineage",
        "operation": "execution-lineage",
        "object_type": "workbench.execution-lineage",
        "requirement": "Workbench emits computation lineage and session execution-binding plans with Core-issued execution IDs.",
        "expected_evidence": ["/integration/core/computation-lineage/manifest"],
    },
    {
        "case_key": "workbench-scenario-uncertainty",
        "operation": "scenario-uncertainty",
        "object_type": "workbench.uncertainty-runtime",
        "requirement": "Workbench executes bounded scenario and uncertainty numerics while Core retains scenario and uncertainty semantics.",
        "expected_evidence": ["/integration/core/scenario-uncertainty/manifest"],
    },
    {
        "case_key": "workbench-visual-reasoning",
        "operation": "visual-reasoning",
        "object_type": "workbench.visual-runtime-adapter",
        "requirement": "Workbench produces renderer-neutral visual research manifests and requires Core-issued visual identities.",
        "expected_evidence": ["/integration/core/visual-reasoning/manifest"],
    },
    {
        "case_key": "workbench-predictive-intelligence",
        "operation": "predictive",
        "object_type": "workbench.predictive-runtime",
        "requirement": "Workbench executes predictive numerics and prepares Core predictive provenance/visual plans without certifying forecast truth.",
        "expected_evidence": ["/integration/core/predictive-intelligence/manifest"],
    },
    {
        "case_key": "workbench-forensic-quantitative",
        "operation": "forensic",
        "object_type": "workbench.forensic-runtime",
        "requirement": "Workbench performs quantitative reconstruction without ranking hypotheses, assigning guilt, or determining truth.",
        "expected_evidence": ["/integration/core/forensic-quantitative/manifest"],
    },
    {
        "case_key": "workbench-research-state-reproduction",
        "operation": "reproduction",
        "object_type": "workbench.research-state",
        "requirement": "Workbench captures deterministic state and prepares reproduction/resume plans without automatic restore or replay.",
        "expected_evidence": ["/integration/core/research-state/manifest"],
    },
    {
        "case_key": "workbench-core-aware-experience",
        "operation": "experience",
        "object_type": "workbench.core-aware-context",
        "requirement": "Workbench assembles one Core-aware context, gap/readiness view and explicit next-action plans without automatic mutation.",
        "expected_evidence": ["/integration/core/experience/manifest"],
    },
    {
        "case_key": "workbench-safety-boundaries",
        "operation": "safety-boundaries",
        "object_type": "workbench.integration-boundary",
        "requirement": "Every Core integration preserves explicit no-auto-dispatch/no-auto-persistence boundaries and separates runtime conformance from scientific validity or truth.",
        "expected_evidence": ["bridge manifests", "v6.14 local certification report"],
    },
]


class SuitePrepareInput(BaseModel):
    suiteKey: str = Field(default="workbench-platform-integration-v6-14-0", min_length=1, max_length=180)
    title: str = Field(default="Sustainable Catalyst Workbench v6.14 Platform Integration Certification", min_length=1, max_length=400)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench-v6.14.0", min_length=1, max_length=255)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProductPrepareInput(BaseModel):
    coreSuiteId: str = Field(min_length=1, max_length=1000)
    visibility: Literal["private", "internal", "public"] = "internal"
    runtimeBindingRef: Optional[str] = Field(default="workbench:/integration/core/runtime-contract", max_length=1000)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CasesPrepareInput(BaseModel):
    coreSuiteId: str = Field(min_length=1, max_length=1000)
    visibility: Literal["private", "internal", "public"] = "internal"


class RunPrepareInput(BaseModel):
    coreSuiteId: str = Field(min_length=1, max_length=1000)
    coreProductId: str = Field(min_length=1, max_length=1000)
    runKey: str = Field(default="workbench-v6-14-0-platform-integration", min_length=1, max_length=180)
    executedBy: str = Field(default="workbench-v6.14.0", min_length=1, max_length=500)
    environmentRef: Optional[str] = Field(default="sc://workbench/runtime/6.14.0", max_length=1000)
    startedAt: Optional[str] = Field(default=None, max_length=80)
    completedAt: Optional[str] = Field(default=None, max_length=80)
    visibility: Literal["private", "internal", "public"] = "internal"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResultsPrepareInput(BaseModel):
    coreRunId: str = Field(min_length=1, max_length=1000)
    coreCaseIds: Dict[str, str] = Field(default_factory=dict)
    executedBy: str = Field(default="workbench-v6.14.0", min_length=1, max_length=500)
    visibility: Literal["private", "internal", "public"] = "internal"


class AncillaryPrepareInput(BaseModel):
    coreRunId: str = Field(min_length=1, max_length=1000)
    projectRef: str = Field(min_length=1, max_length=1000)
    sourceProductRef: str = Field(default=PRODUCT_REF, min_length=1, max_length=500)
    targetProductRef: str = Field(default="product:platform-core", min_length=1, max_length=500)
    exchangeRef: str = Field(default="workbench:/integration/core/runtime-contract", min_length=1, max_length=1000)
    objectRef: str = Field(default="workbench:/integration/core/certification", min_length=1, max_length=1000)
    objectRefs: List[str] = Field(default_factory=list, max_length=500)
    expectedTraceRefs: List[str] = Field(default_factory=list, max_length=500)
    observedTraceRefs: List[str] = Field(default_factory=list, max_length=500)
    stateVersionRef: Optional[str] = Field(default=None, max_length=1000)
    reconstructionPlanRef: Optional[str] = Field(default=None, max_length=1000)
    evidenceRefs: List[str] = Field(default_factory=list, max_length=500)
    visibility: Literal["private", "internal", "public"] = "internal"


class EvidencePrepareInput(BaseModel):
    coreRunId: str = Field(min_length=1, max_length=1000)
    evidenceKey: str = Field(default="workbench-v6-14-local-certification-report", min_length=1, max_length=180)
    evidenceRef: Optional[str] = Field(default=None, max_length=1000)
    capturedBy: str = Field(default="workbench-v6.14.0", min_length=1, max_length=500)
    visibility: Literal["private", "internal", "public"] = "internal"


class FinalizePrepareInput(BaseModel):
    coreSuiteId: str = Field(min_length=1, max_length=1000)
    createdBy: str = Field(default="workbench-v6.14.0", min_length=1, max_length=255)
    reason: Optional[str] = Field(default="Record Workbench v6.14 platform-integration certification state", max_length=4000)


class CoreReportConsumeInput(BaseModel):
    report: Dict[str, Any]


class CoreBundleConsumeInput(BaseModel):
    bundle: Dict[str, Any]


def _core_request(path: str, data: Dict[str, Any], phase: str, method: str = "POST") -> Dict[str, Any]:
    record = {
        "ok": True,
        "schema": CORE_REQUEST_SCHEMA,
        "version": VERSION,
        "contract": CORE_CERTIFICATION_CONTRACT,
        "phase": phase,
        "request": {"method": method, "path": path, "data": data},
        "automaticCoreDispatchAuthorized": False,
        "automaticCorePersistenceAuthorized": False,
        "callerMustReviewAndInvoke": True,
    }
    record["requestHash"] = content_hash(record)
    return record


def _bridge_records() -> Dict[str, Dict[str, Any]]:
    return {
        "runtimeContract": adapter_manifest(),
        "researchSession": bridge_manifest(),
        "executionLineage": lineage_manifest(),
        "scenarioUncertainty": scenario_uncertainty_manifest(),
        "visualReasoning": visual_reasoning_manifest(),
        "predictiveIntelligence": predictive_manifest(),
        "forensicQuantitative": forensic_manifest(),
        "researchState": integration_manifest(),
        "coreAwareExperience": experience_manifest(),
    }


def _automatic_boundary_failures(record: Dict[str, Any]) -> List[str]:
    boundaries = record.get("boundaries", {}) if isinstance(record, dict) else {}
    bad: List[str] = []
    for key, value in boundaries.items():
        lk = str(key).lower()
        if ("automatic" in lk or "truth" in lk or "certif" in lk or "ranking" in lk or "winner" in lk) and value is True:
            if key not in {"certification_means_runtime_contract_conformance_not_scientific_validity"}:
                bad.append(key)
    return sorted(bad)


def local_certification_report() -> Dict[str, Any]:
    caps = capabilities_record()
    bridges = _bridge_records()
    results: List[Dict[str, Any]] = []

    def add(case_key: str, passed: bool, observed: str, evidence: List[str]) -> None:
        results.append({
            "caseKey": case_key,
            "status": "pass" if passed else "fail",
            "observedBehavior": observed,
            "evidenceRefs": evidence,
        })

    add(
        "workbench-connectivity-foundation",
        caps.get("ok") is True and caps.get("version") == VERSION,
        f"capability registry reports Workbench {caps.get('version')}",
        ["/health", "/capabilities", "/integration/core/status"],
    )

    case_map = {
        "workbench-unified-runtime-contract": "runtimeContract",
        "workbench-unified-research-session": "researchSession",
        "workbench-execution-lineage": "executionLineage",
        "workbench-scenario-uncertainty": "scenarioUncertainty",
        "workbench-visual-reasoning": "visualReasoning",
        "workbench-predictive-intelligence": "predictiveIntelligence",
        "workbench-forensic-quantitative": "forensicQuantitative",
        "workbench-research-state-reproduction": "researchState",
        "workbench-core-aware-experience": "coreAwareExperience",
    }
    for case_key, bridge_key in case_map.items():
        manifest = bridges[bridge_key]
        failures = _automatic_boundary_failures(manifest)
        passed = manifest.get("ok") is True and manifest.get("version") == VERSION and not failures
        observed = f"{bridge_key} manifest version={manifest.get('version')}; unsafe-boundaries={failures or 'none'}"
        add(case_key, passed, observed, [manifest.get("bridgeRef") or manifest.get("adapterRef") or f"workbench:{bridge_key}"])

    unsafe = []
    for bridge_key, manifest in bridges.items():
        for key in _automatic_boundary_failures(manifest):
            unsafe.append(f"{bridge_key}:{key}")
    missing_flags = [x for x in REQUIRED_CORE_INTEGRATION_FLAGS[:-1] if not caps.get("coreIntegration", {}).get(x)]
    add(
        "workbench-safety-boundaries",
        not unsafe and not missing_flags,
        f"unsafe-boundaries={unsafe or 'none'}; missing-core-integration-flags={missing_flags or 'none'}",
        ["v6.4-v6.13 bridge manifests", "/integration/core/certification/report/local"],
    )

    required = {c["case_key"] for c in CASE_CATALOG if c.get("required", True)}
    by_key = {r["caseKey"]: r for r in results}
    missing = sorted(required - set(by_key))
    nonpassing = sorted(k for k in required if by_key.get(k, {}).get("status") != "pass")
    record = {
        "ok": True,
        "schema": LOCAL_REPORT_SCHEMA,
        "version": VERSION,
        "contract": CORE_CERTIFICATION_CONTRACT,
        "product": PRODUCT_KEY,
        "productRef": PRODUCT_REF,
        "runtime": RUNTIME_KIND,
        "caseResults": results,
        "requiredCaseKeys": sorted(required),
        "missingRequiredCaseKeys": missing,
        "nonpassingRequiredCaseKeys": nonpassing,
        "declaredConformance": not missing and not nonpassing,
        "certificationScope": "platform-runtime-contract-conformance-only",
        "scientificValidityCertified": False,
        "productQualityCertified": False,
        "authorizationGranted": False,
        "productRankingPerformed": False,
        "reproducibilityInferred": False,
        "truthDeterminationPerformed": False,
    }
    record["reportHash"] = content_hash(record)
    return record


def certification_manifest() -> Dict[str, Any]:
    record = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "productRef": PRODUCT_REF,
        "runtime": RUNTIME_KIND,
        "bridgeRef": BRIDGE_REF,
        "coreCertificationContract": CORE_CERTIFICATION_CONTRACT,
        "runtimeContractRef": CORE_RUNTIME_CONTRACT,
        "coreUnifiedRuntimeContract": CORE_UNIFIED_RUNTIME_CONTRACT,
        "coreComputationLineageContract": CORE_COMPUTATION_LINEAGE_CONTRACT,
        "corePaths": CORE_PATHS,
        "resultStatuses": sorted(RESULT_STATUSES),
        "defaultCaseKeys": [x["case_key"] for x in CASE_CATALOG],
        "certificationCapabilities": [
            "deterministic-local-conformance-report",
            "core-certification-suite-planning",
            "core-product-and-case-registration-planning",
            "core-conformance-run-and-result-planning",
            "exchange-trace-reproduction-check-planning",
            "certification-evidence-planning",
            "core-run-report-consumption",
            "core-suite-bundle-consumption",
            "immutable-certification-snapshot-planning",
        ],
        "boundaries": {
            "certificationMeansRuntimeContractConformanceOnly": True,
            "workbenchInvokesProductsForCertification": False,
            "automaticCoreDispatchAuthorized": False,
            "automaticCorePersistenceAuthorized": False,
            "scientificValidityCertificationAuthorized": False,
            "productQualityCertificationAuthorized": False,
            "productAuthorizationAuthorized": False,
            "productRankingAuthorized": False,
            "missingEvidenceInferenceAuthorized": False,
            "reproducibilityInferenceAuthorized": False,
            "failedCaseAutoResolutionAuthorized": False,
            "truthDeterminationAuthorized": False,
        },
    }
    record["manifestHash"] = content_hash(record)
    return record


def prepare_suite(req: SuitePrepareInput) -> Dict[str, Any]:
    caps = capabilities_record()
    data = {
        "suite_key": req.suiteKey.strip(),
        "title": req.title.strip(),
        "contract_ref": CORE_RUNTIME_CONTRACT,
        "contract_version": "1.0",
        "status": "active",
        "required_operations": [x["operation"] for x in CASE_CATALOG],
        "required_capabilities": [x for x in caps.get("capabilities", []) if x.startswith("platform-core") or x.startswith("core-") or x.startswith("workbench-research-state")],
        "visibility": req.visibility,
        "metadata": {"workbenchVersion": VERSION, "certificationContract": CORE_CERTIFICATION_CONTRACT, **req.metadata},
        "provenance": {"preparedBy": BRIDGE_REF, "localReportHash": local_certification_report()["reportHash"]},
        "created_by": req.createdBy,
    }
    return _core_request(CORE_PATHS["suites"], data, "create-certification-suite")


def prepare_product(req: ProductPrepareInput) -> Dict[str, Any]:
    caps = capabilities_record()
    runtime = adapter_manifest()
    data = {
        "product_key": "workbench",
        "suite_id": req.coreSuiteId.strip(),
        "product_ref": PRODUCT_REF,
        "product_version": VERSION,
        "runtime_binding_ref": req.runtimeBindingRef,
        "declared_capabilities": caps.get("capabilities", []),
        "declared_object_types": runtime.get("supportedObjectTypes", []),
        "visibility": req.visibility,
        "metadata": {"workbenchVersion": VERSION, "runtime": RUNTIME_KIND, **req.metadata},
    }
    return _core_request(CORE_PATHS["products"], data, "register-workbench-product")


def prepare_cases(req: CasesPrepareInput) -> Dict[str, Any]:
    requests = []
    for case in CASE_CATALOG:
        data = {
            "case_key": case["case_key"],
            "suite_id": req.coreSuiteId.strip(),
            "operation": case["operation"],
            "object_type": case.get("object_type"),
            "requirement": case["requirement"],
            "required": case.get("required", True),
            "expected_evidence": case.get("expected_evidence", []),
            "visibility": req.visibility,
            "metadata": {"workbenchVersion": VERSION},
        }
        requests.append(_core_request(CORE_PATHS["cases"], data, f"register-case:{case['case_key']}"))
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "coreSuiteId": req.coreSuiteId,
        "caseCount": len(requests),
        "caseKeys": [x["case_key"] for x in CASE_CATALOG],
        "coreRequests": requests,
        "automaticCoreDispatchAuthorized": False,
        "automaticCorePersistenceAuthorized": False,
    }


def prepare_run(req: RunPrepareInput) -> Dict[str, Any]:
    data = {
        "run_key": req.runKey.strip(),
        "suite_id": req.coreSuiteId.strip(),
        "product_id": req.coreProductId.strip(),
        "executed_by": req.executedBy.strip(),
        "environment_ref": req.environmentRef,
        "started_at": req.startedAt,
        "completed_at": req.completedAt,
        "status": "recorded",
        "visibility": req.visibility,
        "metadata": {"workbenchVersion": VERSION, "localReportHash": local_certification_report()["reportHash"], **req.metadata},
        "provenance": {"preparedBy": BRIDGE_REF, "runtimeContract": CORE_RUNTIME_CONTRACT},
    }
    return _core_request(CORE_PATHS["runs"], data, "create-certification-run")


def prepare_results(req: ResultsPrepareInput) -> Dict[str, Any]:
    report = local_certification_report()
    requests = []
    missing_ids = []
    for result in report["caseResults"]:
        cid = (req.coreCaseIds.get(result["caseKey"]) or "").strip()
        if not cid:
            missing_ids.append(result["caseKey"])
            continue
        data = {
            "run_id": req.coreRunId.strip(),
            "case_id": cid,
            "status": result["status"],
            "observed_behavior": result["observedBehavior"],
            "evidence_refs": result["evidenceRefs"],
            "executed_by": req.executedBy.strip(),
            "visibility": req.visibility,
            "metadata": {"workbenchVersion": VERSION, "localReportHash": report["reportHash"]},
        }
        requests.append(_core_request(CORE_PATHS["caseResults"], data, f"record-case-result:{result['caseKey']}"))
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "coreRunId": req.coreRunId,
        "ready": not missing_ids,
        "missingCoreCaseIds": missing_ids,
        "coreRequests": requests,
        "automaticCoreDispatchAuthorized": False,
        "automaticCorePersistenceAuthorized": False,
    }


def prepare_ancillary(req: AncillaryPrepareInput) -> Dict[str, Any]:
    status = "pass"
    exchange = _core_request(CORE_PATHS["exchangeChecks"], {
        "run_id": req.coreRunId,
        "source_product_ref": req.sourceProductRef,
        "target_product_ref": req.targetProductRef,
        "exchange_ref": req.exchangeRef,
        "object_refs": sorted(set(x.strip() for x in req.objectRefs if x.strip())),
        "status": status,
        "evidence_refs": req.evidenceRefs,
        "visibility": req.visibility,
    }, "record-exchange-check")
    trace = _core_request(CORE_PATHS["traceChecks"], {
        "run_id": req.coreRunId,
        "object_ref": req.objectRef,
        "trace_type": "provenance",
        "expected_refs": sorted(set(x.strip() for x in req.expectedTraceRefs if x.strip())),
        "observed_refs": sorted(set(x.strip() for x in req.observedTraceRefs if x.strip())),
        "status": status if sorted(set(req.expectedTraceRefs)) == sorted(set(req.observedTraceRefs)) else "fail",
        "evidence_refs": req.evidenceRefs,
        "visibility": req.visibility,
    }, "record-trace-check")
    reproduction = _core_request(CORE_PATHS["reproductionChecks"], {
        "run_id": req.coreRunId,
        "project_ref": req.projectRef,
        "state_version_ref": req.stateVersionRef,
        "reconstruction_plan_ref": req.reconstructionPlanRef,
        "status": "pass" if req.stateVersionRef and req.reconstructionPlanRef else "blocked",
        "evidence_refs": req.evidenceRefs,
        "notes": "Workbench records reproduction evidence; it does not infer or certify reproducibility.",
        "visibility": req.visibility,
    }, "record-reproduction-check")
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "coreRequests": [exchange, trace, reproduction],
        "automaticCoreDispatchAuthorized": False,
        "automaticCorePersistenceAuthorized": False,
        "reproducibilityInferred": False,
    }


def prepare_evidence(req: EvidencePrepareInput) -> Dict[str, Any]:
    report = local_certification_report()
    evidence_ref = req.evidenceRef or f"sc://workbench/integration-certification/report/{report['reportHash']}"
    data = {
        "evidence_key": req.evidenceKey,
        "run_id": req.coreRunId,
        "evidence_type": "workbench-local-conformance-report",
        "evidence_ref": evidence_ref,
        "content_hash": report["reportHash"],
        "captured_by": req.capturedBy,
        "visibility": req.visibility,
        "metadata": {"schema": LOCAL_REPORT_SCHEMA, "workbenchVersion": VERSION},
    }
    return _core_request(CORE_PATHS["evidence"], data, "record-certification-evidence")


def prepare_finalize(req: FinalizePrepareInput) -> Dict[str, Any]:
    report = local_certification_report()
    revision = _core_request(CORE_PATHS["revisions"], {
        "suite_id": req.coreSuiteId,
        "prior_state": {},
        "revised_state": {"workbenchVersion": VERSION, "localReportHash": report["reportHash"], "declaredConformance": report["declaredConformance"]},
        "reason": req.reason,
        "created_by": req.createdBy,
    }, "revise-certification-suite")
    snapshot = _core_request(CORE_PATHS["snapshots"], {
        "suite_id": req.coreSuiteId,
        "provenance": {"workbenchVersion": VERSION, "localReportHash": report["reportHash"], "preparedBy": BRIDGE_REF},
        "created_by": req.createdBy,
    }, "snapshot-certification-suite")
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "coreRequests": [revision, snapshot],
        "automaticCoreDispatchAuthorized": False,
        "automaticCorePersistenceAuthorized": False,
    }


def consume_run_report(report: Dict[str, Any]) -> Dict[str, Any]:
    if report.get("contract") != CORE_CERTIFICATION_CONTRACT:
        raise ValueError(f"report.contract must be {CORE_CERTIFICATION_CONTRACT}")
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "coreCertificationContract": CORE_CERTIFICATION_CONTRACT,
        "coreRunId": (report.get("run") or {}).get("id"),
        "declaredConformance": bool(report.get("declared_conformance")),
        "missingRequiredCaseIds": report.get("missing_required_case_ids", []),
        "nonpassingRequiredCaseIds": report.get("nonpassing_required_case_ids", []),
        "caseResultCount": len(report.get("case_results", [])),
        "exchangeCheckCount": len(report.get("exchange_checks", [])),
        "traceCheckCount": len(report.get("trace_checks", [])),
        "reproductionCheckCount": len(report.get("reproduction_checks", [])),
        "evidenceCount": len(report.get("evidence", [])),
        "findingCount": len(report.get("findings", [])),
        "certificationScope": "platform-runtime-contract-conformance-only",
        "scientificValidityCertified": False,
        "productQualityCertified": False,
        "truthDeterminationPerformed": False,
        "readOnlyConsumption": True,
    }


def consume_suite_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    if bundle.get("contract") != CORE_CERTIFICATION_CONTRACT:
        raise ValueError(f"bundle.contract must be {CORE_CERTIFICATION_CONTRACT}")
    suite = bundle.get("suite") or {}
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "coreCertificationContract": CORE_CERTIFICATION_CONTRACT,
        "coreSuiteId": suite.get("id"),
        "suiteKey": suite.get("suite_key"),
        "productCount": len(bundle.get("products", [])),
        "caseCount": len(bundle.get("cases", [])),
        "runCount": len(bundle.get("runs", [])),
        "revisionCount": len(bundle.get("revisions", [])),
        "snapshotCount": len(bundle.get("snapshots", [])),
        "certificationScope": bundle.get("certification_scope", "platform_runtime_contract_conformance_only"),
        "readOnlyConsumption": True,
        "automaticCoreMutationAuthorized": False,
    }


@router.get("/integration/core/certification/manifest")
def manifest(x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return certification_manifest()


@router.get("/integration/core/certification/report/local")
def local_report(x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return local_certification_report()


@router.post("/integration/core/certification/suite/prepare")
def suite_prepare(req: SuitePrepareInput, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return prepare_suite(req)


@router.post("/integration/core/certification/product/prepare")
def product_prepare(req: ProductPrepareInput, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return prepare_product(req)


@router.post("/integration/core/certification/cases/prepare")
def cases_prepare(req: CasesPrepareInput, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return prepare_cases(req)


@router.post("/integration/core/certification/run/prepare")
def run_prepare(req: RunPrepareInput, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return prepare_run(req)


@router.post("/integration/core/certification/results/prepare")
def results_prepare(req: ResultsPrepareInput, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return prepare_results(req)


@router.post("/integration/core/certification/checks/prepare")
def checks_prepare(req: AncillaryPrepareInput, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return prepare_ancillary(req)


@router.post("/integration/core/certification/evidence/prepare")
def evidence_prepare(req: EvidencePrepareInput, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return prepare_evidence(req)


@router.post("/integration/core/certification/finalize/prepare")
def finalize_prepare(req: FinalizePrepareInput, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return prepare_finalize(req)


@router.post("/integration/core/certification/run-report/consume")
def run_report_consume(req: CoreReportConsumeInput, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return consume_run_report(req.report)


@router.post("/integration/core/certification/suite-bundle/consume")
def suite_bundle_consume(req: CoreBundleConsumeInput, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return consume_suite_bundle(req.bundle)


@router.get("/v6140/status")
def status() -> Dict[str, Any]:
    report = local_certification_report()
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Platform Integration Certification",
        "coreCertificationContract": CORE_CERTIFICATION_CONTRACT,
        "localConformanceReport": True,
        "declaredConformance": report["declaredConformance"],
        "certificationSuitePlanning": True,
        "productCaseRunPlanning": True,
        "exchangeTraceReproductionChecks": True,
        "coreRunReportConsumption": True,
        "coreSuiteBundleConsumption": True,
        "immutableCertificationSnapshotPlanning": True,
        "certificationScope": "platform-runtime-contract-conformance-only",
        "automaticCoreDispatch": False,
        "automaticCorePersistence": False,
        "scientificValidityCertification": False,
        "productQualityCertification": False,
        "productAuthorization": False,
        "productRanking": False,
        "truthDetermination": False,
    }
