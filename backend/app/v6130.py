"""Workbench v6.13.0 — Core-Aware Workbench Experience.

Read/plan experience layer spanning the Platform Core integrations introduced in
v6.4–v6.12. It assembles one deterministic view of Core-aware Workbench context,
reports compatibility/readiness, identifies missing Core-issued identifiers, and
prepares explicit next-action plans. It does not dispatch writes to Core, mutate
Core state, execute specialist computation, auto-restore snapshots, replay
executions, or determine research truth.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v640 import CORE_RUNTIME_CONTRACT, _authorize_core_route
from .v650 import PRODUCT_REF
from .v660 import CORE_UNIFIED_RUNTIME_CONTRACT
from .v670 import CORE_COMPUTATION_LINEAGE_CONTRACT
from .v690 import (
    CORE_SCENE_CONTRACT,
    CORE_COMPOSITION_CONTRACT,
    CORE_GRAMMAR_CONTRACT,
    CORE_UNIFIED_VISUAL_CONTRACT,
)
from .v6100 import (
    CORE_PREDICTIVE_MODEL_CONTRACT,
    CORE_FORECAST_CONTRACT,
    CORE_PROBABILISTIC_FORECAST_CONTRACT,
    CORE_CALIBRATION_CONTRACT,
)
from .v6110 import CORE_FORENSIC_QUANTITATIVE_CONTRACT
from .v6120 import (
    CORE_PROJECT_STATE_CONTRACT,
    CORE_REPRODUCIBLE_RESEARCH_CONTRACT,
    CORE_CONTEXT_HANDOFF_CONTRACT,
)

VERSION = APP_VERSION
SCHEMA = "sc-workbench-core-aware-experience/1.0"
CONTEXT_SCHEMA = "sc-workbench-core-aware-context/1.0"
ACTION_PLAN_SCHEMA = "sc-workbench-core-aware-action-plan/1.0"
COMPATIBILITY_SCHEMA = "sc-workbench-core-aware-compatibility/1.0"
BRIDGE_REF = "workbench:/integration/core/experience"

router = APIRouter(tags=["workbench-v6130-core-aware-experience"])

BRIDGES: List[Dict[str, Any]] = [
    {"key":"connectivity","since":"6.4.0","statusPath":"/integration/core/status","purpose":"Core connectivity and compatibility"},
    {"key":"runtimeContract","since":"6.5.0","statusPath":"/integration/core/runtime-contract/manifest","purpose":"Unified runtime contract adapter"},
    {"key":"researchSession","since":"6.6.0","statusPath":"/integration/core/unified-runtime/manifest","purpose":"Unified research project and session bridge"},
    {"key":"executionLineage","since":"6.7.0","statusPath":"/integration/core/computation-lineage/manifest","purpose":"Computation and execution lineage"},
    {"key":"scenarioUncertainty","since":"6.8.0","statusPath":"/integration/core/scenario-uncertainty/manifest","purpose":"Scenario and uncertainty numerical runtime"},
    {"key":"visualReasoning","since":"6.9.0","statusPath":"/integration/core/visual-reasoning/manifest","purpose":"Visual reasoning runtime adapter"},
    {"key":"predictiveIntelligence","since":"6.10.0","statusPath":"/integration/core/predictive-intelligence/manifest","purpose":"Predictive intelligence runtime"},
    {"key":"forensicQuantitative","since":"6.11.0","statusPath":"/integration/core/forensic-quantitative/manifest","purpose":"Forensic quantitative reconstruction"},
    {"key":"researchState","since":"6.12.0","statusPath":"/integration/core/research-state/manifest","purpose":"Research state, reproduction and snapshots"},
]

ACTION_CATALOG: Dict[str, Dict[str, Any]] = {
    "inspect-core-connectivity": {"method":"GET","path":"/integration/core/status","requires":[]},
    "validate-runtime-contract": {"method":"POST","path":"/integration/core/runtime-contract/validate","requires":[]},
    "map-workbench-project": {"method":"POST","path":"/integration/core/runtime-contract/project/map","requires":["projectRef"]},
    "prepare-research-session": {"method":"POST","path":"/integration/core/unified-runtime/sessions/build","requires":["projectRef","coreProjectRef"]},
    "bind-project-to-session": {"method":"POST","path":"/integration/core/unified-runtime/projects/bind","requires":["projectRef","coreSessionId"]},
    "register-execution-lineage": {"method":"POST","path":"/integration/core/computation-lineage/executions/build","requires":["projectRef","coreSessionId"]},
    "bind-execution-to-session": {"method":"POST","path":"/integration/core/computation-lineage/executions/session-binding/build","requires":["coreSessionId","coreExecutionId"]},
    "run-scenario-uncertainty": {"method":"POST","path":"/integration/core/scenario-uncertainty/scenario/affine/run","requires":["projectRef"]},
    "prepare-visual-object": {"method":"POST","path":"/integration/core/visual-reasoning/object/plan","requires":["projectRef"]},
    "prepare-predictive-model": {"method":"POST","path":"/integration/core/predictive-intelligence/model/plan","requires":["projectRef"]},
    "consume-forensic-handoff": {"method":"POST","path":"/integration/core/forensic-quantitative/handoff/consume","requires":["projectRef"]},
    "capture-research-state": {"method":"POST","path":"/research-state/snapshot/build","requires":["projectRef"]},
    "prepare-core-project-state": {"method":"POST","path":"/integration/core/research-state/project-state/prepare","requires":["projectRef"]},
    "prepare-reproduction-package": {"method":"POST","path":"/integration/core/research-state/reproduction/prepare","requires":["projectRef","coreProjectRef"]},
    "resume-from-core-state": {"method":"POST","path":"/integration/core/research-state/resume/consume","requires":["coreStateId"]},
}


class CoreAwareContextInput(BaseModel):
    projectRef: str = Field(min_length=1, max_length=1000)
    projectTitle: Optional[str] = Field(default=None, max_length=1000)
    coreProjectRef: Optional[str] = Field(default=None, max_length=1000)
    coreSessionId: Optional[str] = Field(default=None, max_length=1000)
    coreExecutionId: Optional[str] = Field(default=None, max_length=1000)
    coreVisualObjectId: Optional[str] = Field(default=None, max_length=1000)
    corePredictiveModelId: Optional[str] = Field(default=None, max_length=1000)
    coreForensicReconstructionId: Optional[str] = Field(default=None, max_length=1000)
    coreStateId: Optional[str] = Field(default=None, max_length=1000)
    corePackageId: Optional[str] = Field(default=None, max_length=1000)
    coreContextId: Optional[str] = Field(default=None, max_length=1000)
    localSnapshotHash: Optional[str] = Field(default=None, max_length=256)
    objectRefs: List[str] = Field(default_factory=list, max_length=500)
    executionRefs: List[str] = Field(default_factory=list, max_length=500)
    visualRefs: List[str] = Field(default_factory=list, max_length=500)
    notes: Optional[str] = Field(default=None, max_length=4000)


class CompatibilityInput(BaseModel):
    coreReachable: bool = True
    coreVersion: Optional[str] = Field(default=None, max_length=100)
    expectedCoreVersionPrefix: Optional[str] = Field(default="3.", max_length=100)
    runtimeContract: Optional[str] = Field(default=CORE_RUNTIME_CONTRACT, max_length=500)
    unifiedRuntimeContract: Optional[str] = Field(default=CORE_UNIFIED_RUNTIME_CONTRACT, max_length=500)
    serviceTokenRequired: bool = False
    serviceTokenConfigured: bool = False


class ActionPlanInput(BaseModel):
    action: Literal[
        "inspect-core-connectivity", "validate-runtime-contract", "map-workbench-project",
        "prepare-research-session", "bind-project-to-session", "register-execution-lineage",
        "bind-execution-to-session", "run-scenario-uncertainty", "prepare-visual-object",
        "prepare-predictive-model", "consume-forensic-handoff", "capture-research-state",
        "prepare-core-project-state", "prepare-reproduction-package", "resume-from-core-state",
    ]
    context: CoreAwareContextInput


def _clean(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    x = str(v).strip()
    return x or None


def experience_manifest() -> Dict[str, Any]:
    record = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "productRef": PRODUCT_REF,
        "runtime": RUNTIME_KIND,
        "bridgeRef": BRIDGE_REF,
        "bridges": BRIDGES,
        "contracts": {
            "runtime": CORE_RUNTIME_CONTRACT,
            "unifiedResearchRuntime": CORE_UNIFIED_RUNTIME_CONTRACT,
            "computationLineage": CORE_COMPUTATION_LINEAGE_CONTRACT,
            "visualScene": CORE_SCENE_CONTRACT,
            "visualComposition": CORE_COMPOSITION_CONTRACT,
            "visualGrammar": CORE_GRAMMAR_CONTRACT,
            "unifiedVisualReasoning": CORE_UNIFIED_VISUAL_CONTRACT,
            "predictiveModel": CORE_PREDICTIVE_MODEL_CONTRACT,
            "forecastProvenance": CORE_FORECAST_CONTRACT,
            "probabilisticForecast": CORE_PROBABILISTIC_FORECAST_CONTRACT,
            "calibration": CORE_CALIBRATION_CONTRACT,
            "forensicQuantitative": CORE_FORENSIC_QUANTITATIVE_CONTRACT,
            "projectState": CORE_PROJECT_STATE_CONTRACT,
            "reproducibleResearch": CORE_REPRODUCIBLE_RESEARCH_CONTRACT,
            "contextHandoff": CORE_CONTEXT_HANDOFF_CONTRACT,
        },
        "experienceCapabilities": [
            "single-core-aware-context-view",
            "core-id-presence-and-gap-detection",
            "compatibility-and-readiness-evaluation",
            "explicit-next-action-planning",
            "cross-bridge-provenance-summary",
            "research-state-and-reproduction-awareness",
            "predictive-forensic-visual-handoff-awareness",
        ],
        "boundaries": {
            "experienceLayerExecutesComputation": False,
            "automaticCoreDispatchAuthorized": False,
            "automaticCorePersistenceAuthorized": False,
            "automaticStateRestoreAuthorized": False,
            "automaticExecutionReplayAuthorized": False,
            "coreIdsMustComeFromCore": True,
            "truthDeterminationAuthorized": False,
        },
    }
    record["manifestHash"] = content_hash(record)
    return record


def assemble_context(req: CoreAwareContextInput) -> Dict[str, Any]:
    ids = {
        "coreProjectRef": _clean(req.coreProjectRef),
        "coreSessionId": _clean(req.coreSessionId),
        "coreExecutionId": _clean(req.coreExecutionId),
        "coreVisualObjectId": _clean(req.coreVisualObjectId),
        "corePredictiveModelId": _clean(req.corePredictiveModelId),
        "coreForensicReconstructionId": _clean(req.coreForensicReconstructionId),
        "coreStateId": _clean(req.coreStateId),
        "corePackageId": _clean(req.corePackageId),
        "coreContextId": _clean(req.coreContextId),
    }
    missing = [k for k,v in ids.items() if not v]
    present = [k for k,v in ids.items() if v]
    stages = [
        {"key":"project","ready":True,"ref":req.projectRef},
        {"key":"core-project","ready":bool(ids["coreProjectRef"]),"ref":ids["coreProjectRef"]},
        {"key":"research-session","ready":bool(ids["coreSessionId"]),"ref":ids["coreSessionId"]},
        {"key":"execution-lineage","ready":bool(ids["coreExecutionId"]),"ref":ids["coreExecutionId"]},
        {"key":"visual-reasoning","ready":bool(ids["coreVisualObjectId"]),"ref":ids["coreVisualObjectId"]},
        {"key":"predictive-intelligence","ready":bool(ids["corePredictiveModelId"]),"ref":ids["corePredictiveModelId"]},
        {"key":"forensic-quantitative","ready":bool(ids["coreForensicReconstructionId"]),"ref":ids["coreForensicReconstructionId"]},
        {"key":"research-state","ready":bool(ids["coreStateId"]),"ref":ids["coreStateId"]},
        {"key":"reproduction-package","ready":bool(ids["corePackageId"]),"ref":ids["corePackageId"]},
        {"key":"cross-product-context","ready":bool(ids["coreContextId"]),"ref":ids["coreContextId"]},
    ]
    next_actions = ["inspect-core-connectivity", "validate-runtime-contract", "map-workbench-project"]
    if not ids["coreProjectRef"]:
        next_actions.append("map-workbench-project")
    elif not ids["coreSessionId"]:
        next_actions.append("prepare-research-session")
    elif not ids["coreExecutionId"]:
        next_actions.append("register-execution-lineage")
    if not ids["coreStateId"]:
        next_actions.append("capture-research-state")
        next_actions.append("prepare-core-project-state")
    if ids["coreProjectRef"] and not ids["corePackageId"]:
        next_actions.append("prepare-reproduction-package")
    # de-dupe while preserving order
    next_actions = list(dict.fromkeys(next_actions))
    record = {
        "ok": True,
        "schema": CONTEXT_SCHEMA,
        "version": VERSION,
        "projectRef": req.projectRef.strip(),
        "projectTitle": _clean(req.projectTitle),
        "coreIds": ids,
        "presentCoreIds": present,
        "missingCoreIds": missing,
        "localSnapshotHash": _clean(req.localSnapshotHash),
        "objectRefs": sorted(set(x.strip() for x in req.objectRefs if x.strip())),
        "executionRefs": sorted(set(x.strip() for x in req.executionRefs if x.strip())),
        "visualRefs": sorted(set(x.strip() for x in req.visualRefs if x.strip())),
        "stages": stages,
        "nextActions": next_actions,
        "automaticDispatchAuthorized": False,
        "automaticPersistenceAuthorized": False,
        "automaticRestoreAuthorized": False,
        "automaticReplayAuthorized": False,
    }
    record["contextHash"] = content_hash(record)
    return record


def evaluate_compatibility(req: CompatibilityInput) -> Dict[str, Any]:
    reasons: List[str] = []
    if not req.coreReachable:
        reasons.append("core-unreachable")
    if req.runtimeContract != CORE_RUNTIME_CONTRACT:
        reasons.append("runtime-contract-mismatch")
    if req.unifiedRuntimeContract != CORE_UNIFIED_RUNTIME_CONTRACT:
        reasons.append("unified-runtime-contract-mismatch")
    if req.serviceTokenRequired and not req.serviceTokenConfigured:
        reasons.append("service-token-required-but-not-configured")
    if req.coreVersion and req.expectedCoreVersionPrefix and not req.coreVersion.startswith(req.expectedCoreVersionPrefix):
        reasons.append("core-version-prefix-mismatch")
    return {
        "ok": True,
        "schema": COMPATIBILITY_SCHEMA,
        "version": VERSION,
        "compatible": not reasons,
        "readiness": "ready" if not reasons else "attention-required",
        "reasons": reasons,
        "expected": {
            "runtimeContract": CORE_RUNTIME_CONTRACT,
            "unifiedRuntimeContract": CORE_UNIFIED_RUNTIME_CONTRACT,
            "coreVersionPrefix": req.expectedCoreVersionPrefix,
        },
        "automaticRepairAuthorized": False,
    }


def build_action_plan(req: ActionPlanInput) -> Dict[str, Any]:
    spec = ACTION_CATALOG[req.action]
    ctx = assemble_context(req.context)
    values = {"projectRef": req.context.projectRef, **ctx["coreIds"]}
    missing = [name for name in spec["requires"] if not _clean(values.get(name))]
    record = {
        "ok": True,
        "schema": ACTION_PLAN_SCHEMA,
        "version": VERSION,
        "action": req.action,
        "ready": not missing,
        "missingRequirements": missing,
        "request": {"method": spec["method"], "path": spec["path"]},
        "contextRef": f"sc://workbench/core-aware-context/{ctx['contextHash'][:16]}",
        "automaticDispatchAuthorized": False,
        "automaticCorePersistenceAuthorized": False,
        "callerMustReviewAndInvoke": True,
    }
    record["planHash"] = content_hash(record)
    return record


@router.get("/integration/core/experience/manifest")
def manifest(x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return experience_manifest()


@router.post("/integration/core/experience/context/assemble")
def context_assemble(req: CoreAwareContextInput, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return assemble_context(req)


@router.post("/integration/core/experience/compatibility/evaluate")
def compatibility_evaluate(req: CompatibilityInput, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return evaluate_compatibility(req)


@router.post("/integration/core/experience/actions/plan")
def actions_plan(req: ActionPlanInput, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return build_action_plan(req)


@router.get("/v6130/status")
def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Core-Aware Workbench Experience",
        "coreAwareContext": True,
        "compatibilityEvaluation": True,
        "nextActionPlanning": True,
        "crossBridgeAwareness": True,
        "researchStateAwareness": True,
        "predictiveForensicVisualAwareness": True,
        "automaticCoreDispatch": False,
        "automaticCorePersistence": False,
        "automaticStateRestore": False,
        "automaticExecutionReplay": False,
    }
