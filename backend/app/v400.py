"""Workbench v4.0.0 — Connected Scientific and Engineering Workbench."""
from __future__ import annotations

from collections import defaultdict, deque
from hashlib import sha256
import json
from typing import Any, Dict, List, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v400", tags=["Workbench v4.0.0"])
VERSION = "4.0.0"
SCHEMA_PREFIX = "sc-workbench-connected-environment"
CORE_PLATFORMS = [
    "workbench",
    "sustainable-catalyst-lab",
    "site-intelligence",
    "decision-studio",
    "research-librarian",
    "knowledge-library",
]
CORE_CAPABILITIES = [
    "projects",
    "calculations",
    "code",
    "simulation",
    "devices",
    "experiments",
    "evidence",
    "reviews",
    "documentation",
    "offline",
]
BLOCKED_OPERATIONS = {"remote-shell", "arbitrary-command", "disable-safety", "automatic-publication"}


def _dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return value


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


def _unique(values: List[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        item = str(value).strip()
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _record_id(record: Dict[str, Any], fallback: str) -> str:
    for key in ("id", "recordId", "record_id", "projectId", "project_id"):
        if record.get(key):
            return str(record[key])
    return fallback


class CapabilityRegistryRequest(BaseModel):
    studios: List[str] = Field(default_factory=list)
    platforms: List[str] = Field(default_factory=lambda: CORE_PLATFORMS.copy())
    domains: List[str] = Field(default_factory=list)
    runtimes: List[str] = Field(default_factory=lambda: ["python", "javascript", "go", "r", "rust"])
    services: List[str] = Field(default_factory=lambda: ["browser-local", "wordpress", "offline-fastapi"])
    required_capabilities: List[str] = Field(default_factory=lambda: CORE_CAPABILITIES.copy())
    available_capabilities: List[str] = Field(default_factory=lambda: CORE_CAPABILITIES.copy())


class ConnectedProjectRequest(BaseModel):
    project_id: str = "default"
    title: str = "Connected Workbench Project"
    owner: str = ""
    storage_mode: Literal["browser-local", "wordpress", "hybrid", "offline"] = "browser-local"
    objectives: List[str] = Field(default_factory=list)
    records: List[Dict[str, Any]] = Field(default_factory=list)
    platform_links: List[Dict[str, Any]] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    runtimes: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    review_state: str = "draft"


class ConnectionGraphRequest(BaseModel):
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)


class WorkflowPlanRequest(BaseModel):
    project_id: str = "default"
    objective: str = ""
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    available_capabilities: List[str] = Field(default_factory=lambda: CORE_CAPABILITIES.copy())
    approvals: List[str] = Field(default_factory=list)


class SharedContextRequest(BaseModel):
    project_id: str = "default"
    variables: List[Dict[str, Any]] = Field(default_factory=list)
    assumptions: List[Dict[str, Any]] = Field(default_factory=list)
    units: Dict[str, str] = Field(default_factory=dict)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    uncertainties: List[Dict[str, Any]] = Field(default_factory=list)


class IntegrationHealthRequest(BaseModel):
    integrations: List[Dict[str, Any]] = Field(default_factory=lambda: [
        {"id": platform, "required": platform == "workbench", "status": "ready", "version": "unknown"}
        for platform in CORE_PLATFORMS
    ])


class TraceabilityRequest(BaseModel):
    requirements: List[Dict[str, Any]] = Field(default_factory=list)
    records: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    reviews: List[Dict[str, Any]] = Field(default_factory=list)


class SyncPlanRequest(BaseModel):
    local_records: List[Dict[str, Any]] = Field(default_factory=list)
    remote_records: List[Dict[str, Any]] = Field(default_factory=list)
    strategy: Literal["manual", "keep-local", "keep-remote", "newest", "rename"] = "manual"
    backup_verified: bool = False


class DossierRequest(BaseModel):
    project: Dict[str, Any] = Field(default_factory=dict)
    graph: Dict[str, Any] = Field(default_factory=dict)
    workflow: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    reviews: List[Dict[str, Any]] = Field(default_factory=list)
    evaluations: List[Dict[str, Any]] = Field(default_factory=list)
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)


class ReleaseManifestRequest(BaseModel):
    project: Dict[str, Any] = Field(default_factory=dict)
    capability_registry: Dict[str, Any] = Field(default_factory=dict)
    integration_health: Dict[str, Any] = Field(default_factory=dict)
    traceability: Dict[str, Any] = Field(default_factory=dict)
    evaluations: List[Dict[str, Any]] = Field(default_factory=list)
    unresolved_findings: List[Dict[str, Any]] = Field(default_factory=list)
    human_approval: bool = False


class ExtensionValidationRequest(BaseModel):
    contract: Dict[str, Any] = Field(default_factory=dict)
    required_hooks: List[str] = Field(default_factory=list)
    required_routes: List[str] = Field(default_factory=list)
    required_schemas: List[str] = Field(default_factory=list)


def build_capability_registry(request: CapabilityRegistryRequest) -> Dict[str, Any]:
    available = _unique(request.available_capabilities)
    required = _unique(request.required_capabilities)
    missing = [item for item in required if item not in available]
    registry = {
        "schema": f"{SCHEMA_PREFIX}-capability-registry/1.0",
        "version": VERSION,
        "studios": _unique(request.studios),
        "platforms": _unique(request.platforms),
        "domains": _unique(request.domains),
        "runtimes": _unique(request.runtimes),
        "services": _unique(request.services),
        "requiredCapabilities": required,
        "availableCapabilities": available,
        "missingCapabilities": missing,
        "ready": not missing,
        "automaticExecutionAuthorized": False,
    }
    registry["registryHash"] = stable_hash(registry)
    return {"ok": registry["ready"], "registry": registry}


def build_connected_project(request: ConnectedProjectRequest) -> Dict[str, Any]:
    records, seen = [], set()
    duplicate_ids = []
    for index, raw in enumerate(request.records):
        record = dict(raw)
        rid = _record_id(record, f"record-{index + 1}")
        if rid in seen:
            duplicate_ids.append(rid)
            continue
        seen.add(rid)
        record["id"] = rid
        record.setdefault("type", "workbench-record")
        record.setdefault("source", "workbench")
        record["recordHash"] = stable_hash({k: v for k, v in record.items() if k != "recordHash"})
        records.append(record)
    project = {
        "schema": f"{SCHEMA_PREFIX}-project/1.0",
        "version": VERSION,
        "projectId": request.project_id.strip() or "default",
        "title": request.title.strip() or "Connected Workbench Project",
        "owner": request.owner.strip(),
        "storageMode": request.storage_mode,
        "objectives": _unique(request.objectives),
        "records": records,
        "platformLinks": request.platform_links,
        "domains": _unique(request.domains),
        "runtimes": _unique(request.runtimes),
        "evidenceIds": _unique(request.evidence_ids),
        "reviewState": request.review_state,
        "recordCount": len(records),
        "duplicateRecordIds": _unique(duplicate_ids),
        "humanControlRequired": True,
    }
    project["projectHash"] = stable_hash(project)
    return {"ok": not duplicate_ids, "project": project}


def build_connection_graph(request: ConnectionGraphRequest) -> Dict[str, Any]:
    nodes, node_ids, duplicate_nodes = [], set(), []
    for index, raw in enumerate(request.nodes):
        node = dict(raw)
        node_id = _record_id(node, f"node-{index + 1}")
        if node_id in node_ids:
            duplicate_nodes.append(node_id)
            continue
        node_ids.add(node_id)
        node["id"] = node_id
        node.setdefault("type", "record")
        nodes.append(node)
    edges, invalid_edges = [], []
    adjacency: Dict[str, List[str]] = defaultdict(list)
    for index, raw in enumerate(request.edges):
        edge = dict(raw)
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if source not in node_ids or target not in node_ids:
            invalid_edges.append({"index": index, "source": source, "target": target})
            continue
        edge.setdefault("id", f"edge-{index + 1}")
        edge.setdefault("relation", "related-to")
        edges.append(edge)
        adjacency[source].append(target)
        adjacency[target].append(source)
    components, visited = [], set()
    for node_id in sorted(node_ids):
        if node_id in visited:
            continue
        queue, component = deque([node_id]), []
        visited.add(node_id)
        while queue:
            current = queue.popleft()
            component.append(current)
            for neighbor in adjacency[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        components.append(sorted(component))
    isolated = sorted([node_id for node_id in node_ids if not adjacency[node_id]])
    graph = {
        "schema": f"{SCHEMA_PREFIX}-connection-graph/1.0",
        "version": VERSION,
        "nodes": nodes,
        "edges": edges,
        "nodeCount": len(nodes),
        "edgeCount": len(edges),
        "components": components,
        "componentCount": len(components),
        "isolatedNodeIds": isolated,
        "duplicateNodeIds": _unique(duplicate_nodes),
        "invalidEdges": invalid_edges,
        "ready": not duplicate_nodes and not invalid_edges,
    }
    graph["graphHash"] = stable_hash(graph)
    return {"ok": graph["ready"], "graph": graph}


def build_workflow_plan(request: WorkflowPlanRequest) -> Dict[str, Any]:
    available = set(_unique(request.available_capabilities))
    approvals = set(_unique(request.approvals))
    steps, step_ids, issues = [], set(), []
    for index, raw in enumerate(request.steps):
        step = dict(raw)
        step_id = _record_id(step, f"step-{index + 1}")
        if step_id in step_ids:
            issues.append({"code": "duplicate-step", "stepId": step_id, "blocking": True})
            continue
        step_ids.add(step_id)
        step["id"] = step_id
        step.setdefault("dependsOn", [])
        step.setdefault("requires", [])
        step.setdefault("operation", "analyze")
        steps.append(step)
    indegree = {step["id"]: 0 for step in steps}
    children: Dict[str, List[str]] = defaultdict(list)
    for step in steps:
        for dependency in step.get("dependsOn", []):
            if dependency not in indegree:
                issues.append({"code": "missing-dependency", "stepId": step["id"], "dependency": dependency, "blocking": True})
                continue
            indegree[step["id"]] += 1
            children[dependency].append(step["id"])
        missing = [cap for cap in step.get("requires", []) if cap not in available]
        if missing:
            issues.append({"code": "missing-capability", "stepId": step["id"], "capabilities": missing, "blocking": True})
        operation = str(step.get("operation", ""))
        if operation in BLOCKED_OPERATIONS:
            issues.append({"code": "blocked-operation", "stepId": step["id"], "operation": operation, "blocking": True})
        approval = str(step.get("approval", ""))
        if approval and approval not in approvals:
            issues.append({"code": "approval-required", "stepId": step["id"], "approval": approval, "blocking": True})
    queue = deque(sorted([step_id for step_id, count in indegree.items() if count == 0]))
    ordered = []
    while queue:
        current = queue.popleft()
        ordered.append(current)
        for child in sorted(children[current]):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(ordered) != len(steps):
        issues.append({"code": "dependency-cycle", "blocking": True})
    plan = {
        "schema": f"{SCHEMA_PREFIX}-workflow-plan/1.0",
        "version": VERSION,
        "projectId": request.project_id,
        "objective": request.objective,
        "steps": steps,
        "executionOrder": ordered,
        "issues": issues,
        "ready": not any(item.get("blocking") for item in issues),
        "automaticExecutionAuthorized": False,
        "humanApprovalRequired": True,
    }
    plan["planHash"] = stable_hash(plan)
    return {"ok": plan["ready"], "plan": plan}


def build_shared_context(request: SharedContextRequest) -> Dict[str, Any]:
    variables, by_name, conflicts = [], {}, []
    for index, raw in enumerate(request.variables):
        variable = dict(raw)
        name = str(variable.get("name") or f"variable-{index + 1}")
        variable["name"] = name
        if name in by_name and by_name[name].get("value") != variable.get("value"):
            conflicts.append({"name": name, "values": [by_name[name].get("value"), variable.get("value")]})
            continue
        by_name[name] = variable
        variables.append(variable)
    context = {
        "schema": f"{SCHEMA_PREFIX}-shared-context/1.0",
        "version": VERSION,
        "projectId": request.project_id,
        "variables": variables,
        "assumptions": request.assumptions,
        "units": request.units,
        "evidence": request.evidence,
        "uncertainties": request.uncertainties,
        "conflicts": conflicts,
        "ready": not conflicts,
        "provenanceRequired": True,
    }
    context["contextHash"] = stable_hash(context)
    return {"ok": context["ready"], "context": context}


def build_integration_health(request: IntegrationHealthRequest) -> Dict[str, Any]:
    integrations, findings = [], []
    for raw in request.integrations:
        item = dict(raw)
        item_id = str(item.get("id", "unknown"))
        status = str(item.get("status", "unknown"))
        required = bool(item.get("required", False))
        ready = status in {"ready", "online", "available"}
        item.update({"id": item_id, "status": status, "required": required, "ready": ready})
        integrations.append(item)
        if required and not ready:
            findings.append({"code": "required-integration-unavailable", "integration": item_id, "blocking": True})
        elif not ready:
            findings.append({"code": "optional-integration-unavailable", "integration": item_id, "blocking": False})
    report = {
        "schema": f"{SCHEMA_PREFIX}-integration-health/1.0",
        "version": VERSION,
        "integrations": integrations,
        "findings": findings,
        "ready": not any(item["blocking"] for item in findings),
        "degraded": any(not item["ready"] for item in integrations),
        "offlineFallbackAvailable": True,
    }
    report["healthHash"] = stable_hash(report)
    return {"ok": report["ready"], "report": report}


def build_traceability(request: TraceabilityRequest) -> Dict[str, Any]:
    record_ids = {_record_id(item, f"record-{index + 1}") for index, item in enumerate(request.records)}
    evidence_ids = {_record_id(item, f"evidence-{index + 1}") for index, item in enumerate(request.evidence)}
    review_ids = {_record_id(item, f"review-{index + 1}") for index, item in enumerate(request.reviews)}
    matrix, gaps = [], []
    for index, raw in enumerate(request.requirements):
        requirement = dict(raw)
        req_id = _record_id(requirement, f"requirement-{index + 1}")
        linked_records = [item for item in requirement.get("recordIds", []) if item in record_ids]
        linked_evidence = [item for item in requirement.get("evidenceIds", []) if item in evidence_ids]
        linked_reviews = [item for item in requirement.get("reviewIds", []) if item in review_ids]
        covered = bool(linked_records and linked_evidence and linked_reviews)
        entry = {
            "requirementId": req_id,
            "recordIds": linked_records,
            "evidenceIds": linked_evidence,
            "reviewIds": linked_reviews,
            "covered": covered,
        }
        matrix.append(entry)
        if not covered:
            gaps.append(req_id)
    total = len(matrix)
    covered_count = sum(1 for item in matrix if item["covered"])
    report = {
        "schema": f"{SCHEMA_PREFIX}-traceability-matrix/1.0",
        "version": VERSION,
        "matrix": matrix,
        "requirementCount": total,
        "coveredRequirementCount": covered_count,
        "coveragePercent": round((covered_count / total) * 100, 2) if total else 100.0,
        "gapRequirementIds": gaps,
        "ready": not gaps,
    }
    report["traceabilityHash"] = stable_hash(report)
    return {"ok": report["ready"], "report": report}


def build_sync_plan(request: SyncPlanRequest) -> Dict[str, Any]:
    local = {_record_id(item, f"local-{index + 1}"): item for index, item in enumerate(request.local_records)}
    remote = {_record_id(item, f"remote-{index + 1}"): item for index, item in enumerate(request.remote_records)}
    all_ids = sorted(set(local) | set(remote))
    actions, conflicts = [], []
    for record_id in all_ids:
        left, right = local.get(record_id), remote.get(record_id)
        if left is None:
            actions.append({"recordId": record_id, "action": "import-remote"})
            continue
        if right is None:
            actions.append({"recordId": record_id, "action": "export-local"})
            continue
        left_hash = left.get("recordHash") or stable_hash(left)
        right_hash = right.get("recordHash") or stable_hash(right)
        if left_hash == right_hash:
            actions.append({"recordId": record_id, "action": "unchanged"})
            continue
        conflict = {"recordId": record_id, "localHash": left_hash, "remoteHash": right_hash}
        conflicts.append(conflict)
        action = {
            "manual": "review-conflict",
            "keep-local": "overwrite-remote",
            "keep-remote": "overwrite-local",
            "newest": "select-newest",
            "rename": "preserve-both",
        }[request.strategy]
        actions.append({"recordId": record_id, "action": action})
    destructive = request.strategy in {"keep-local", "keep-remote"} and bool(conflicts)
    blocking = destructive and not request.backup_verified
    plan = {
        "schema": f"{SCHEMA_PREFIX}-sync-plan/1.0",
        "version": VERSION,
        "strategy": request.strategy,
        "actions": actions,
        "conflicts": conflicts,
        "backupVerified": request.backup_verified,
        "blockingIssues": ["verified-backup-required"] if blocking else [],
        "ready": not blocking,
        "automaticCloudUpload": False,
    }
    plan["syncHash"] = stable_hash(plan)
    return {"ok": plan["ready"], "plan": plan}


def build_connected_dossier(request: DossierRequest) -> Dict[str, Any]:
    dossier = {
        "schema": f"{SCHEMA_PREFIX}-dossier/1.0",
        "version": VERSION,
        "project": request.project,
        "connectionGraph": request.graph,
        "workflow": request.workflow,
        "evidence": request.evidence,
        "reviews": request.reviews,
        "evaluations": request.evaluations,
        "artifacts": request.artifacts,
        "counts": {
            "evidence": len(request.evidence),
            "reviews": len(request.reviews),
            "evaluations": len(request.evaluations),
            "artifacts": len(request.artifacts),
        },
        "humanReviewRequired": True,
        "certificationClaim": False,
    }
    dossier["dossierHash"] = stable_hash(dossier)
    return {"ok": True, "dossier": dossier}


def build_release_manifest(request: ReleaseManifestRequest) -> Dict[str, Any]:
    unresolved = [item for item in request.unresolved_findings if str(item.get("severity", "")).lower() in {"high", "critical"}]
    registry_ready = bool(request.capability_registry.get("ready", True))
    integrations_ready = bool(request.integration_health.get("ready", True))
    traceability_ready = bool(request.traceability.get("ready", True))
    evaluation_failures = [item for item in request.evaluations if not item.get("ready", item.get("ok", False))]
    blocking = []
    if not registry_ready:
        blocking.append("capability-registry-incomplete")
    if not integrations_ready:
        blocking.append("required-integration-unavailable")
    if not traceability_ready:
        blocking.append("traceability-gaps")
    if evaluation_failures:
        blocking.append("evaluation-failures")
    if unresolved:
        blocking.append("unresolved-high-or-critical-findings")
    if not request.human_approval:
        blocking.append("human-approval-required")
    manifest = {
        "schema": f"{SCHEMA_PREFIX}-release-manifest/1.0",
        "version": VERSION,
        "project": request.project,
        "capabilityRegistryHash": request.capability_registry.get("registryHash", ""),
        "integrationHealthHash": request.integration_health.get("healthHash", ""),
        "traceabilityHash": request.traceability.get("traceabilityHash", ""),
        "evaluationCount": len(request.evaluations),
        "blockingIssues": blocking,
        "status": "ready-for-connected-release" if not blocking else "hold",
        "humanApproval": request.human_approval,
        "automaticPublicationAuthorized": False,
        "automaticDeviceControlAuthorized": False,
        "remoteShellAllowed": False,
    }
    manifest["manifestHash"] = stable_hash(manifest)
    return {"ok": not blocking, "manifest": manifest}


def validate_extension_contract(request: ExtensionValidationRequest) -> Dict[str, Any]:
    contract = dict(request.contract)
    hooks = set(contract.get("hooks", []))
    routes = set(contract.get("restRoutes", contract.get("routes", [])))
    schemas = set(contract.get("schemas", []))
    missing = {
        "hooks": [item for item in request.required_hooks if item not in hooks],
        "routes": [item for item in request.required_routes if item not in routes],
        "schemas": [item for item in request.required_schemas if item not in schemas],
    }
    ready = not any(missing.values())
    report = {
        "schema": f"{SCHEMA_PREFIX}-extension-validation/1.0",
        "version": VERSION,
        "contract": contract,
        "missing": missing,
        "ready": ready,
    }
    report["validationHash"] = stable_hash(report)
    return {"ok": ready, "report": report}


@router.get("/status")
def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": f"{SCHEMA_PREFIX}-status/1.0",
        "version": VERSION,
        "milestone": "Connected Scientific and Engineering Workbench",
        "platforms": CORE_PLATFORMS,
        "capabilities": CORE_CAPABILITIES,
        "offlineSupported": True,
        "renderRequired": False,
        "paidServiceRequired": False,
        "humanControlRequired": True,
        "automaticPublicationAuthorized": False,
        "remoteShellAllowed": False,
    }


@router.post("/capabilities/registry")
def capability_registry(request: CapabilityRegistryRequest) -> Dict[str, Any]:
    return build_capability_registry(request)


@router.post("/project/build")
def connected_project(request: ConnectedProjectRequest) -> Dict[str, Any]:
    return build_connected_project(request)


@router.post("/graph/build")
def connection_graph(request: ConnectionGraphRequest) -> Dict[str, Any]:
    return build_connection_graph(request)


@router.post("/workflow/plan")
def workflow_plan(request: WorkflowPlanRequest) -> Dict[str, Any]:
    return build_workflow_plan(request)


@router.post("/context/build")
def shared_context(request: SharedContextRequest) -> Dict[str, Any]:
    return build_shared_context(request)


@router.post("/integration/health")
def integration_health(request: IntegrationHealthRequest) -> Dict[str, Any]:
    return build_integration_health(request)


@router.post("/traceability/build")
def traceability(request: TraceabilityRequest) -> Dict[str, Any]:
    return build_traceability(request)


@router.post("/sync/plan")
def sync_plan(request: SyncPlanRequest) -> Dict[str, Any]:
    return build_sync_plan(request)


@router.post("/dossier/build")
def connected_dossier(request: DossierRequest) -> Dict[str, Any]:
    return build_connected_dossier(request)


@router.post("/release/manifest")
def release_manifest(request: ReleaseManifestRequest) -> Dict[str, Any]:
    return build_release_manifest(request)


@router.post("/extension/validate")
def extension_validate(request: ExtensionValidationRequest) -> Dict[str, Any]:
    return validate_extension_contract(request)
