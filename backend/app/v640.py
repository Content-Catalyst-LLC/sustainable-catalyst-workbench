"""Workbench v6.4.0 — Platform Core Connectivity Foundation.

This release establishes a bounded, explicit service contract between Platform
Core and Workbench. It provides Core-compatible health/capability surfaces,
configuration diagnostics, request-context reporting, and optional service-token
validation for Core integration routes. It does not dispatch work to Platform
Core, execute arbitrary Core instructions, persist Core state, or alter legacy
Workbench computation contracts.
"""
from __future__ import annotations

import hmac
import os
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND

VERSION = APP_VERSION
SCHEMA = "sc-workbench-core-connectivity/1.0"
CORE_RUNTIME_CONTRACT = "sc.research.unified-runtime-contract.v1"
CORE_PRODUCT_KEY = "platform-core"

router = APIRouter(tags=["workbench-v640-core-connectivity"])


def _bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _clean_url(value: str) -> str:
    value = (value or "").strip()
    return value.rstrip("/")


def core_config() -> dict[str, Any]:
    """Return non-secret Core connectivity configuration state."""
    core_url = _clean_url(os.getenv("SCWB_CORE_URL", ""))
    service_token = os.getenv("SCWB_SERVICE_TOKEN", "")
    api_key = os.getenv("SCWB_CORE_API_KEY", "")
    enabled = _bool("SCWB_CORE_ENABLED", bool(core_url))
    required = _bool("SCWB_CORE_REQUIRED", False)
    token_required = _bool("SCWB_REQUIRE_SERVICE_TOKEN", False)
    expected_prefix = os.getenv("SCWB_CORE_EXPECTED_VERSION_PREFIX", "3.").strip()
    return {
        "coreUrlConfigured": bool(core_url),
        "coreEnabled": enabled,
        "coreRequired": required,
        "expectedCoreVersionPrefix": expected_prefix,
        "serviceTokenConfigured": bool(service_token),
        "serviceTokenRequiredForCoreIntegrationRoutes": token_required,
        "coreApiKeyConfigured": bool(api_key),
        "outboundDispatchEnabled": False,
    }


def _authorize_core_route(service_token: str | None) -> None:
    """Validate the shared service token when explicitly required.

    Token validation is intentionally limited to the new Core integration
    surface in v6.4.0. Existing Workbench public/scientific endpoints retain
    their prior access semantics until a later migration explicitly changes
    them.
    """
    if not _bool("SCWB_REQUIRE_SERVICE_TOKEN", False):
        return
    expected = os.getenv("SCWB_SERVICE_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=503, detail="Workbench service-token enforcement is enabled but SCWB_SERVICE_TOKEN is not configured.")
    supplied = service_token or ""
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Valid X-SC-Service-Token required for Platform Core integration routes.")


def health_record() -> dict[str, Any]:
    cfg = core_config()
    token_config_ok = not cfg["serviceTokenRequiredForCoreIntegrationRoutes"] or cfg["serviceTokenConfigured"]
    return {
        "ok": bool(token_config_ok),
        "schema": "sc-workbench-health/1.0",
        "product": PRODUCT_KEY,
        "name": PRODUCT_NAME,
        "version": VERSION,
        "runtime": RUNTIME_KIND,
        "coreCompatible": True,
        "coreConnectivityContract": SCHEMA,
        "runtimeContractTarget": CORE_RUNTIME_CONTRACT,
        "readiness": "ready" if token_config_ok else "configuration-error",
    }


def runtime_record() -> dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-workbench-runtime/1.0",
        "product": PRODUCT_KEY,
        "version": VERSION,
        "runtime": RUNTIME_KIND,
        "executionRole": "specialist-computation-plane",
        "orchestrationRole": "platform-core",
        "boundaries": {
            "coreMayRouteRequests": True,
            "coreMayInspectHealth": True,
            "coreMayInspectCapabilities": True,
            "coreMayExecuteWorkbenchCodeDirectly": False,
            "workbenchMayDispatchToCoreAutomatically": False,
            "automaticRemoteActionAuthorized": False,
            "automaticPersistenceToCoreAuthorized": False,
            "arbitraryCodeFromCoreAuthorized": False,
        },
    }


def capabilities_record() -> dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-workbench-capabilities/1.0",
        "product": PRODUCT_KEY,
        "version": VERSION,
        "capabilities": [
            "calculations",
            "models",
            "visual-analysis",
            "visual-research-object-handoff",
            "mathematics",
            "numerical-computing",
            "simulation",
            "signals-controls",
            "electronics-embedded",
            "fpga-digital-logic",
            "energy-systems-explicit-input-execution",
            "canonical-computational-projects",
            "reproducible-computational-exports",
            "platform-core-gateway-health",
            "platform-core-request-context",
            "platform-core-service-token-validation",
            "platform-core-unified-runtime-contract-adapter",
            "platform-core-project-reference-mapping",
            "platform-core-exchange-envelope-adapter",
            "platform-core-invocation-result-lineage-requests",
            "platform-core-unified-research-session-bridge",
            "platform-core-project-session-bindings",
            "platform-core-computation-execution-lineage-bridge",
            "platform-core-execution-session-bindings",
            "platform-core-scenario-uncertainty-compute-runtime",
            "monte-carlo-lhs-sobol-morris-runtime",
            "platform-core-visual-reasoning-runtime-adapter",
            "renderer-neutral-visual-research-manifests",
            "platform-core-predictive-intelligence-runtime",
            "predictive-forecast-backtest-calibration-runtime",
            "platform-core-forensic-quantitative-reconstruction-runtime",
            "forensic-trajectory-temporal-uncertainty-runtime",
            "platform-core-research-state-reproduction-snapshot-integration",
            "platform-core-aware-workbench-experience",
            "platform-core-integration-certification",
            "workbench-declared-runtime-conformance-evidence",
            "core-context-readiness-next-action-planning",
            "workbench-research-state-snapshot-resume-runtime",
            "unified-scientific-engineering-execution-runtime",
            "canonical-unified-execution-envelope",
            "dependency-ordered-scientific-engineering-workflows",
            "platform-core-unified-execution-lineage-planning",
            "unified-execution-object-model",
            "content-addressed-execution-objects",
            "execution-object-integrity-validation",
            "platform-core-execution-object-binding-planning",
            "scientific-runtime-orchestrator",
            "deterministic-runtime-routing",
            "bounded-runtime-adapter-registry",
            "external-runtime-handoff-planning",
            "platform-core-research-workflow-orchestration-planning",
            "dataset-variable-parameter-workspace",
            "content-addressed-research-input-objects",
            "unit-aware-parameter-and-variable-layer",
            "workspace-execution-binding-planning",
            "platform-core-workspace-lineage-planning",
            "numerical-methods-solver-runtime",
            "canonical-numerical-problem-specifications",
            "solver-convergence-residual-diagnostics",
            "numerical-convergence-study-runtime",
            "platform-core-numerical-solver-lineage-planning",
            "simulation-dynamical-systems-runtime",
            "canonical-dynamical-simulation-specifications",
            "trajectory-event-stability-diagnostics",
            "bounded-dynamical-parameter-sweeps",
            "platform-core-simulation-lineage-planning",
            "engineering-systems-runtime",
            "canonical-bounded-engineering-analysis",
            "cross-domain-engineering-system-bundles",
            "platform-core-engineering-lineage-planning",
            "optimization-design-space-runtime",
            "bounded-design-variable-objective-constraint-spaces",
            "pareto-frontier-and-full-factorial-exploration",
            "constrained-weighted-sum-optimization",
            "engineering-simulation-candidate-handoff-planning",
            "platform-core-design-space-lineage-planning",
            "scientific-workflow-graph",
            "typed-scientific-workflow-nodes",
            "dependency-directed-acyclic-workflows",
            "explicit-cross-node-result-bindings",
            "content-addressed-workflow-graph-plans",
            "platform-core-scientific-workflow-planning",
            "interactive-computational-notebook-runtime",
            "typed-reproducible-notebook-cells",
            "explicit-notebook-cell-dependencies",
            "content-addressed-notebook-runs",
            "notebook-replay-planning",
            "platform-core-notebook-workflow-planning",
            "visual-scientific-computing-workspace",
            "renderer-neutral-scientific-views",
            "linked-scientific-views-and-cross-filtering",
            "explicit-parameter-control-recompute-planning",
            "notebook-to-visual-workspace-projection",
            "platform-core-visual-workspace-planning",
            "reproducible-experiment-engineering-package",
            "content-addressed-research-package-manifests",
            "explicit-replay-and-export-planning",
            "workbench-state-package-assembly",
            "platform-core-reproducible-package-planning",
            "model-validation-verification-framework",
            "reference-benchmark-validation",
            "observed-predicted-dataset-comparison",
            "numerical-convergence-verification",
            "content-addressed-vv-reports",
            "platform-core-validation-verification-lineage-planning",
        ],
        "coreIntegration": {
            "connectivityFoundation": True,
            "unifiedRuntimeContractAdapter": True,
            "unifiedResearchSessionBinding": True,
            "executionLineageBridge": True,
            "scenarioUncertaintyRuntime": True,
            "visualReasoningRuntimeAdapter": True,
            "predictiveIntelligenceRuntime": True,
            "forensicQuantitativeReconstructionRuntime": True,
            "researchStateReproductionSnapshotIntegration": True,
            "coreAwareWorkbenchExperience": True,
            "platformIntegrationCertification": True,
            "unifiedScientificEngineeringExecutionRuntime": True,
            "unifiedExecutionObjectModel": True,
            "scientificRuntimeOrchestrator": True,
            "researchWorkflowOrchestrationPlanning": True,
            "datasetVariableParameterWorkspace": True,
            "workspaceExecutionBindingPlanning": True,
            "workspaceLineagePlanning": True,
            "numericalMethodsSolverRuntime": True,
            "numericalSolverLineagePlanning": True,
            "simulationDynamicalSystemsRuntime": True,
            "simulationLineagePlanning": True,
            "engineeringSystemsRuntime": True,
            "engineeringLineagePlanning": True,
            "optimizationDesignSpaceRuntime": True,
            "designSpaceParetoExploration": True,
            "designSpaceCandidateHandoffPlanning": True,
            "designSpaceLineagePlanning": True,
            "scientificWorkflowGraph": True,
            "workflowGraphExplicitBindings": True,
            "workflowGraphCorePlanning": True,
            "interactiveComputationalNotebookRuntime": True,
            "notebookExplicitCellDependencies": True,
            "notebookReplayPlanning": True,
            "notebookCoreWorkflowPlanning": True,
            "visualScientificComputingWorkspace": True,
            "visualScientificLinkedViews": True,
            "visualScientificControlPlanning": True,
            "visualScientificCorePlanning": True,
            "reproducibleExperimentEngineeringPackage": True,
            "reproduciblePackageAssembly": True,
            "reproduciblePackageReplayPlanning": True,
            "reproduciblePackageCorePlanning": True,
            "modelValidationVerificationFramework": True,
            "validationBenchmarkEvaluation": True,
            "validationDatasetComparison": True,
            "validationConvergenceVerification": True,
            "validationVerificationLineagePlanning": True,
        },
        "nextContract": CORE_RUNTIME_CONTRACT,
    }


def core_status_record(request: Request) -> dict[str, Any]:
    cfg = core_config()
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "coreProduct": CORE_PRODUCT_KEY,
        "configuration": cfg,
        "requestContext": {
            "requestId": request.headers.get("x-request-id", ""),
            "gatewayService": request.headers.get("x-sc-gateway-service", ""),
            "coreVersion": request.headers.get("x-sc-core-version", ""),
            "serviceTokenPresented": bool(request.headers.get("x-sc-service-token", "")),
        },
        "compatibility": {
            "healthPath": "/health",
            "runtimePath": "/runtime",
            "capabilitiesPath": "/capabilities",
            "integrationStatusPath": "/integration/core/status",
            "expectedGatewayService": PRODUCT_KEY,
            "runtimeContractTarget": CORE_RUNTIME_CONTRACT,
        },
        "security": {
            "secretsReturned": False,
            "serviceTokenComparedConstantTime": True,
            "legacyEndpointAccessChanged": False,
        },
        "execution": {
            "coreDispatchPerformed": False,
            "workbenchComputationPerformed": False,
            "persistencePerformed": False,
        },
    }


@router.get("/health")
def health() -> dict[str, Any]:
    return health_record()


@router.get("/runtime")
def runtime() -> dict[str, Any]:
    return runtime_record()


@router.get("/capabilities")
def capabilities() -> dict[str, Any]:
    return capabilities_record()


@router.get("/integration/core/status")
def core_status(
    request: Request,
    x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token"),
) -> dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return core_status_record(request)


@router.get("/v640/status")
def v640_status() -> dict[str, Any]:
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Platform Core Connectivity Foundation",
        "healthPath": "/health",
        "coreIntegrationStatusPath": "/integration/core/status",
        "serviceTokenSupport": True,
        "outboundCoreDispatch": False,
        "legacyEndpointAccessChanged": False,
    }
