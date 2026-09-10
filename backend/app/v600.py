"""Workbench v6.0.0 — Unified Computational Workbench.

Creates canonical computational projects that link the mathematics, graph,
geometry, numerical, signals/control, electronics/embedded, FPGA/digital-logic,
and legacy Workbench studios through shared variables, object dependencies,
provenance, revision history, portable exports, and explicit cross-platform
handoff packets.

The v6.0.x API is deliberately deterministic and non-executing. It does not
open files, invoke shells, run generated code, program devices, publish content,
or perform destructive synchronization. Existing specialist v5.x endpoints
remain responsible for bounded computation; v6.0.x composes their result
objects into an auditable project graph.
"""
from __future__ import annotations

from collections import Counter, deque
from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator, model_validator

from app.v510 import content_hash

VERSION = "6.0.1"
PROJECT_SCHEMA = "sc-workbench-computational-project/1.0"
VARIABLE_SCHEMA = "sc-workbench-shared-variable-set/1.0"
LINK_SCHEMA = "sc-workbench-linked-object-graph/1.0"
PROVENANCE_SCHEMA = "sc-workbench-computational-provenance/1.0"
HISTORY_SCHEMA = "sc-workbench-computational-history/1.0"
EXPORT_SCHEMA = "sc-workbench-computational-export/1.0"
HANDOFF_SCHEMA = "sc-workbench-computational-handoff/1.0"

MAX_VARIABLES = 128
MAX_OBJECTS = 256
MAX_LINKS = 1024
MAX_HISTORY_EVENTS = 512
MAX_SOURCES = 256
MAX_PAYLOAD_DEPTH = 16

STUDIOS = (
    "mathematics",
    "graph-mathematics",
    "dynamic-geometry",
    "numerical-computing",
    "signals-control",
    "electronics-embedded",
    "digital-logic",
    "computational-blackboard",
    "prototype-bench",
    "simulation",
    "instrumentation",
    "robotics-controls",
    "research-lab",
    "data-pipelines",
    "evaluation-lab",
    "other",
)

HANDOFF_TARGETS = (
    "lab",
    "decision-studio",
    "knowledge-library",
    "research-librarian",
    "site-intelligence",
    "workspace",
    "offline",
)

router = APIRouter(prefix="/v600", tags=["workbench-v600-unified-computational"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _slug(value: str, fallback: str = "item") -> str:
    text = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return (text[:96] or fallback)


def _bounded_payload(value: Any, depth: int = 0) -> Any:
    if depth > MAX_PAYLOAD_DEPTH:
        raise ValueError("Payload nesting exceeds the v6.0.x project limit.")
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value[:20000]
    if isinstance(value, list):
        if len(value) > 4096:
            raise ValueError("Payload list exceeds 4096 items.")
        return [_bounded_payload(item, depth + 1) for item in value]
    if isinstance(value, dict):
        if len(value) > 1024:
            raise ValueError("Payload object exceeds 1024 keys.")
        return {str(key)[:160]: _bounded_payload(item, depth + 1) for key, item in value.items()}
    raise ValueError(f"Unsupported payload value type: {type(value).__name__}")


class SharedVariable(BaseModel):
    name: str
    value: Any = None
    valueType: Literal["number", "string", "boolean", "vector", "matrix", "expression", "object-ref", "json"] = "number"
    units: str = ""
    description: str = ""
    sourceObjectId: str = ""
    locked: bool = False

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = str(value).strip()
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", value):
            raise ValueError("Variable names must start with a letter and contain only letters, numbers, and underscores.")
        return value


class ComputationalObject(BaseModel):
    objectId: str
    kind: str
    studio: str = "other"
    title: str = ""
    payload: Dict[str, Any] = Field(default_factory=dict)
    variableInputs: List[str] = Field(default_factory=list)
    variableOutputs: List[str] = Field(default_factory=list)
    dependencyObjectIds: List[str] = Field(default_factory=list)
    sourceSchema: str = ""
    sourceVersion: str = ""
    createdAt: str = Field(default_factory=_now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("objectId")
    @classmethod
    def validate_object_id(cls, value: str) -> str:
        return _slug(value, "object")

    @field_validator("kind")
    @classmethod
    def validate_kind(cls, value: str) -> str:
        value = _slug(value, "computational-object")
        return value[:80]

    @field_validator("studio")
    @classmethod
    def validate_studio(cls, value: str) -> str:
        normalized = _slug(value, "other")
        return normalized if normalized in STUDIOS else "other"


class ProjectInput(BaseModel):
    projectId: str
    title: str = "Untitled computational project"
    description: str = ""
    activeStudio: str = "computational-project"
    variables: List[SharedVariable] = Field(default_factory=list)
    objects: List[ComputationalObject] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("projectId")
    @classmethod
    def validate_project_id(cls, value: str) -> str:
        return _slug(value, "project")

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = str(value).strip()
        if not value:
            raise ValueError("Project title is required.")
        return value[:180]

    @model_validator(mode="after")
    def validate_limits(self):
        if len(self.variables) > MAX_VARIABLES:
            raise ValueError(f"A computational project supports at most {MAX_VARIABLES} shared variables.")
        if len(self.objects) > MAX_OBJECTS:
            raise ValueError(f"A computational project supports at most {MAX_OBJECTS} objects.")
        variable_names = [item.name for item in self.variables]
        if len(variable_names) != len(set(variable_names)):
            raise ValueError("Shared variable names must be unique.")
        object_ids = [item.objectId for item in self.objects]
        if len(object_ids) != len(set(object_ids)):
            raise ValueError("Computational object IDs must be unique.")
        return self


class ProjectBuildRequest(BaseModel):
    project: ProjectInput


class VariableSetRequest(BaseModel):
    variables: List[SharedVariable] = Field(default_factory=list)
    overrides: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_limits(self):
        if len(self.variables) > MAX_VARIABLES:
            raise ValueError(f"At most {MAX_VARIABLES} shared variables are supported.")
        names = [item.name for item in self.variables]
        if len(names) != len(set(names)):
            raise ValueError("Shared variable names must be unique.")
        unknown = sorted(set(self.overrides) - set(names))
        if unknown:
            raise ValueError("Overrides reference unknown variables: " + ", ".join(unknown))
        return self


class ObjectLink(BaseModel):
    fromObjectId: str
    toObjectId: str
    relation: Literal["depends-on", "feeds", "derives-from", "references", "validates", "compares"] = "feeds"
    fromPort: str = ""
    toPort: str = ""
    variableNames: List[str] = Field(default_factory=list)

    @field_validator("fromObjectId", "toObjectId")
    @classmethod
    def normalize_ids(cls, value: str) -> str:
        return _slug(value, "object")


class LinkGraphRequest(BaseModel):
    objects: List[ComputationalObject] = Field(default_factory=list)
    links: List[ObjectLink] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_limits(self):
        if len(self.objects) > MAX_OBJECTS:
            raise ValueError(f"At most {MAX_OBJECTS} objects are supported.")
        if len(self.links) > MAX_LINKS:
            raise ValueError(f"At most {MAX_LINKS} object links are supported.")
        return self


class ProvenanceOperation(BaseModel):
    operationId: str = ""
    objectId: str
    action: str
    inputs: List[str] = Field(default_factory=list)
    method: str = ""
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=_now)
    actor: str = "user"


class ProvenanceRequest(BaseModel):
    projectId: str
    projectHash: str = ""
    objects: List[ComputationalObject] = Field(default_factory=list)
    operations: List[ProvenanceOperation] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_limits(self):
        if len(self.objects) > MAX_OBJECTS:
            raise ValueError(f"At most {MAX_OBJECTS} objects are supported.")
        if len(self.sources) > MAX_SOURCES:
            raise ValueError(f"At most {MAX_SOURCES} provenance sources are supported.")
        return self


class HistoryEvent(BaseModel):
    eventId: str = ""
    action: str
    objectId: str = ""
    summary: str = ""
    actor: str = "user"
    timestamp: str = Field(default_factory=_now)
    data: Dict[str, Any] = Field(default_factory=dict)


class HistoryRequest(BaseModel):
    projectId: str
    baseProjectHash: str = ""
    events: List[HistoryEvent] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_limits(self):
        if len(self.events) > MAX_HISTORY_EVENTS:
            raise ValueError(f"At most {MAX_HISTORY_EVENTS} history events are supported.")
        return self


class ExportRequest(BaseModel):
    project: ProjectInput
    provenance: Dict[str, Any] = Field(default_factory=dict)
    history: Dict[str, Any] = Field(default_factory=dict)
    includePayloads: bool = True
    includeMetadata: bool = True
    format: Literal["json", "manifest"] = "json"


class HandoffRequest(BaseModel):
    project: ProjectInput
    targetSurface: Literal[
        "lab", "decision-studio", "knowledge-library", "research-librarian", "site-intelligence", "workspace", "offline"
    ]
    objectIds: List[str] = Field(default_factory=list)
    purpose: str = "continue-analysis"
    notes: str = ""


def _normalize_variable(variable: SharedVariable, override: Any = None, overridden: bool = False) -> Dict[str, Any]:
    value = override if overridden else variable.value
    record = {
        "name": variable.name,
        "value": _bounded_payload(value),
        "valueType": variable.valueType,
        "units": str(variable.units)[:80],
        "description": str(variable.description)[:500],
        "sourceObjectId": _slug(variable.sourceObjectId, "") if variable.sourceObjectId else "",
        "locked": bool(variable.locked),
        "overridden": bool(overridden),
    }
    record["variableHash"] = content_hash(record)
    return record


def resolve_variables(request: VariableSetRequest) -> Dict[str, Any]:
    resolved: List[Dict[str, Any]] = []
    locked_override_attempts: List[str] = []
    for variable in request.variables:
        has_override = variable.name in request.overrides
        if has_override and variable.locked:
            locked_override_attempts.append(variable.name)
            has_override = False
        resolved.append(_normalize_variable(variable, request.overrides.get(variable.name), has_override))
    by_name = {item["name"]: item for item in resolved}
    base = {
        "schema": VARIABLE_SCHEMA,
        "version": VERSION,
        "variables": resolved,
        "variableNames": sorted(by_name),
        "lockedOverrideAttempts": sorted(locked_override_attempts),
        "ready": not locked_override_attempts,
    }
    base["variableSetHash"] = content_hash(base)
    return {"ok": base["ready"], "schema": VARIABLE_SCHEMA, "version": VERSION, "result": base, "variableSetHash": base["variableSetHash"]}


def _normalize_object(item: ComputationalObject) -> Dict[str, Any]:
    record = {
        "objectId": item.objectId,
        "kind": item.kind,
        "studio": item.studio,
        "title": str(item.title)[:180],
        "payload": _bounded_payload(item.payload),
        "variableInputs": sorted(set(item.variableInputs)),
        "variableOutputs": sorted(set(item.variableOutputs)),
        "dependencyObjectIds": sorted({_slug(dep, "object") for dep in item.dependencyObjectIds}),
        "sourceSchema": str(item.sourceSchema)[:180],
        "sourceVersion": str(item.sourceVersion)[:80],
        "createdAt": item.createdAt,
        "metadata": _bounded_payload(item.metadata),
    }
    record["objectHash"] = content_hash(record)
    return record


def build_project(request: ProjectBuildRequest) -> Dict[str, Any]:
    project = request.project
    variables = [_normalize_variable(item) for item in project.variables]
    objects = [_normalize_object(item) for item in project.objects]
    variable_names = {item["name"] for item in variables}
    object_ids = {item["objectId"] for item in objects}
    issues: List[Dict[str, Any]] = []
    for item in objects:
        missing_vars = sorted((set(item["variableInputs"]) | set(item["variableOutputs"])) - variable_names)
        missing_deps = sorted(set(item["dependencyObjectIds"]) - object_ids)
        if missing_vars:
            issues.append({"objectId": item["objectId"], "code": "missing-variable", "items": missing_vars})
        if missing_deps:
            issues.append({"objectId": item["objectId"], "code": "missing-object-dependency", "items": missing_deps})
    studio_counts = dict(sorted(Counter(item["studio"] for item in objects).items()))
    kind_counts = dict(sorted(Counter(item["kind"] for item in objects).items()))
    record = {
        "schema": PROJECT_SCHEMA,
        "version": VERSION,
        "projectId": project.projectId,
        "title": project.title,
        "description": str(project.description)[:4000],
        "activeStudio": _slug(project.activeStudio, "computational-project"),
        "variables": variables,
        "objects": objects,
        "tags": sorted({str(tag).strip()[:80] for tag in project.tags if str(tag).strip()}),
        "metadata": _bounded_payload(project.metadata),
        "studioCounts": studio_counts,
        "objectKindCounts": kind_counts,
        "variableCount": len(variables),
        "objectCount": len(objects),
        "integrityIssues": issues,
        "ready": not issues,
        "browserLocalOperation": True,
        "optionalWordPressPersistence": True,
        "automaticExecutionAuthorized": False,
    }
    record["projectHash"] = content_hash(record)
    return {"ok": record["ready"], "schema": PROJECT_SCHEMA, "version": VERSION, "project": record, "projectHash": record["projectHash"]}


def build_link_graph(request: LinkGraphRequest) -> Dict[str, Any]:
    objects = [_normalize_object(item) for item in request.objects]
    ids = {item["objectId"] for item in objects}
    links: List[Dict[str, Any]] = []
    issues: List[Dict[str, Any]] = []
    adjacency: Dict[str, Set[str]] = {object_id: set() for object_id in ids}
    indegree: Dict[str, int] = {object_id: 0 for object_id in ids}
    seen_links: Set[Tuple[str, str, str, str, str]] = set()
    for link in request.links:
        key = (link.fromObjectId, link.toObjectId, link.relation, link.fromPort, link.toPort)
        if key in seen_links:
            issues.append({"code": "duplicate-link", "fromObjectId": link.fromObjectId, "toObjectId": link.toObjectId})
            continue
        seen_links.add(key)
        if link.fromObjectId not in ids or link.toObjectId not in ids:
            issues.append({"code": "unknown-object", "fromObjectId": link.fromObjectId, "toObjectId": link.toObjectId})
            continue
        if link.fromObjectId == link.toObjectId:
            issues.append({"code": "self-link", "objectId": link.fromObjectId})
        record = link.model_dump()
        record["variableNames"] = sorted(set(record["variableNames"]))
        record["linkHash"] = content_hash(record)
        links.append(record)
        if link.toObjectId not in adjacency[link.fromObjectId]:
            adjacency[link.fromObjectId].add(link.toObjectId)
            indegree[link.toObjectId] += 1
    queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
    order: List[str] = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for target in sorted(adjacency[node]):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    cycle_nodes = sorted(node for node, degree in indegree.items() if degree > 0)
    base = {
        "schema": LINK_SCHEMA,
        "version": VERSION,
        "objects": objects,
        "links": links,
        "objectCount": len(objects),
        "linkCount": len(links),
        "topologicalOrder": order if not cycle_nodes else [],
        "cycleDetected": bool(cycle_nodes),
        "cycleObjectIds": cycle_nodes,
        "issues": issues,
        "ready": not issues and not cycle_nodes,
    }
    base["graphHash"] = content_hash(base)
    return {"ok": base["ready"], "schema": LINK_SCHEMA, "version": VERSION, "result": base, "graphHash": base["graphHash"]}


def build_provenance(request: ProvenanceRequest) -> Dict[str, Any]:
    objects = [_normalize_object(item) for item in request.objects]
    object_ids = {item["objectId"] for item in objects}
    operations: List[Dict[str, Any]] = []
    issues: List[Dict[str, Any]] = []
    parent_hash = request.projectHash.strip()
    for index, operation in enumerate(request.operations, start=1):
        object_id = _slug(operation.objectId, "object")
        if object_id not in object_ids:
            issues.append({"code": "unknown-operation-object", "objectId": object_id})
        record = {
            "operationId": _slug(operation.operationId or f"operation-{index}", f"operation-{index}"),
            "objectId": object_id,
            "action": _slug(operation.action, "operation"),
            "inputs": sorted(set(operation.inputs)),
            "method": str(operation.method)[:240],
            "parameters": _bounded_payload(operation.parameters),
            "timestamp": operation.timestamp,
            "actor": str(operation.actor)[:120],
            "parentHash": parent_hash,
        }
        record["operationHash"] = content_hash(record)
        parent_hash = record["operationHash"]
        operations.append(record)
    sources = []
    for index, raw in enumerate(request.sources, start=1):
        source = _bounded_payload(raw)
        if not isinstance(source, dict):
            continue
        source.setdefault("sourceId", f"source-{index}")
        source["sourceHash"] = content_hash(source)
        sources.append(source)
    base = {
        "schema": PROVENANCE_SCHEMA,
        "version": VERSION,
        "projectId": _slug(request.projectId, "project"),
        "projectHash": request.projectHash.strip(),
        "objects": objects,
        "operations": operations,
        "sources": sources,
        "issues": issues,
        "chainHeadHash": parent_hash,
        "humanReviewRequired": True,
        "automaticCertificationAuthorized": False,
    }
    base["provenanceHash"] = content_hash(base)
    return {"ok": not issues, "schema": PROVENANCE_SCHEMA, "version": VERSION, "result": base, "provenanceHash": base["provenanceHash"]}


def build_history(request: HistoryRequest) -> Dict[str, Any]:
    parent_hash = request.baseProjectHash.strip()
    events: List[Dict[str, Any]] = []
    for index, event in enumerate(request.events, start=1):
        record = {
            "eventId": _slug(event.eventId or f"event-{index}", f"event-{index}"),
            "revision": index,
            "action": _slug(event.action, "change"),
            "objectId": _slug(event.objectId, "") if event.objectId else "",
            "summary": str(event.summary)[:1000],
            "actor": str(event.actor)[:120],
            "timestamp": event.timestamp,
            "data": _bounded_payload(event.data),
            "parentHash": parent_hash,
        }
        record["eventHash"] = content_hash(record)
        parent_hash = record["eventHash"]
        events.append(record)
    base = {
        "schema": HISTORY_SCHEMA,
        "version": VERSION,
        "projectId": _slug(request.projectId, "project"),
        "baseProjectHash": request.baseProjectHash.strip(),
        "events": events,
        "revisionCount": len(events),
        "headHash": parent_hash,
        "appendOnlyModel": True,
    }
    base["historyHash"] = content_hash(base)
    return {"ok": True, "schema": HISTORY_SCHEMA, "version": VERSION, "result": base, "historyHash": base["historyHash"]}


def build_export(request: ExportRequest) -> Dict[str, Any]:
    project_result = build_project(ProjectBuildRequest(project=request.project))
    project = dict(project_result["project"])
    if not request.includePayloads:
        for item in project["objects"]:
            item["payload"] = {}
    if not request.includeMetadata:
        project["metadata"] = {}
        for item in project["objects"]:
            item["metadata"] = {}
    manifest = {
        "schema": EXPORT_SCHEMA,
        "version": VERSION,
        "format": request.format,
        "project": project,
        "provenance": _bounded_payload(request.provenance),
        "history": _bounded_payload(request.history),
        "includePayloads": request.includePayloads,
        "includeMetadata": request.includeMetadata,
        "generatedAt": _now(),
        "portable": True,
        "requiresExternalExecutionForGeneratedCode": True,
        "automaticPublicationAuthorized": False,
    }
    hashable = dict(manifest)
    hashable.pop("generatedAt", None)
    manifest["exportHash"] = content_hash(hashable)
    return {"ok": project_result["ok"], "schema": EXPORT_SCHEMA, "version": VERSION, "result": manifest, "exportHash": manifest["exportHash"]}


def build_handoff(request: HandoffRequest) -> Dict[str, Any]:
    project_result = build_project(ProjectBuildRequest(project=request.project))
    project = project_result["project"]
    by_id = {item["objectId"]: item for item in project["objects"]}
    requested = [_slug(item, "object") for item in request.objectIds]
    selected_ids = requested or sorted(by_id)
    missing = sorted(set(selected_ids) - set(by_id))
    selected = [by_id[item] for item in selected_ids if item in by_id]
    packet = {
        "schema": HANDOFF_SCHEMA,
        "version": VERSION,
        "handoffId": _slug(f"{project['projectId']}-{request.targetSurface}-{request.purpose}", "handoff"),
        "projectId": project["projectId"],
        "projectHash": project["projectHash"],
        "targetSurface": request.targetSurface,
        "purpose": _slug(request.purpose, "continue-analysis"),
        "notes": str(request.notes)[:4000],
        "objects": selected,
        "objectIds": [item["objectId"] for item in selected],
        "missingObjectIds": missing,
        "sharedVariables": project["variables"],
        "requiresTargetImportConfirmation": True,
        "automaticRemoteActionAuthorized": False,
        "automaticPublicationAuthorized": False,
        "automaticDestructiveSynchronizationAuthorized": False,
        "generatedAt": _now(),
    }
    hashable = dict(packet)
    hashable.pop("generatedAt", None)
    packet["handoffHash"] = content_hash(hashable)
    return {"ok": not missing and project_result["ok"], "schema": HANDOFF_SCHEMA, "version": VERSION, "result": packet, "handoffHash": packet["handoffHash"]}


def status_record() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-workbench-unified-computational-status/1.0",
        "version": VERSION,
        "foundation": "Workbench v5.1–v5.9 specialist computation + v3.x/v4.x project infrastructure",
        "capabilities": [
            "canonical-computational-projects",
            "shared-project-variables",
            "linked-computational-objects",
            "cross-studio-dependency-graphs",
            "computational-provenance",
            "append-only-project-history",
            "portable-computational-exports",
            "cross-platform-handoff-packets",
            "browser-local-project-operation",
            "optional-wordpress-project-persistence",
            "canonical-content-hashes",
        ],
        "specialistStudios": list(STUDIOS[:-1]),
        "handoffTargets": list(HANDOFF_TARGETS),
        "limits": {
            "maxSharedVariables": MAX_VARIABLES,
            "maxComputationalObjects": MAX_OBJECTS,
            "maxObjectLinks": MAX_LINKS,
            "maxHistoryEvents": MAX_HISTORY_EVENTS,
        },
        "automaticExecutionAuthorized": False,
        "automaticPublicationAuthorized": False,
        "automaticCertificationAuthorized": False,
        "automaticDeviceProgrammingAuthorized": False,
        "automaticDestructiveSynchronizationAuthorized": False,
        "remoteShellAuthorized": False,
        "arbitraryCodeExecutionAuthorized": False,
    }


@router.get("/status")
def status() -> Dict[str, Any]:
    return status_record()


@router.post("/project/build")
def project_build(request: ProjectBuildRequest) -> Dict[str, Any]:
    return build_project(request)


@router.post("/variables/resolve")
def variables_resolve(request: VariableSetRequest) -> Dict[str, Any]:
    return resolve_variables(request)


@router.post("/links/validate")
def links_validate(request: LinkGraphRequest) -> Dict[str, Any]:
    return build_link_graph(request)


@router.post("/provenance/build")
def provenance_build(request: ProvenanceRequest) -> Dict[str, Any]:
    return build_provenance(request)


@router.post("/history/build")
def history_build(request: HistoryRequest) -> Dict[str, Any]:
    return build_history(request)


@router.post("/export/build")
def export_build(request: ExportRequest) -> Dict[str, Any]:
    return build_export(request)


@router.post("/handoff/build")
def handoff_build(request: HandoffRequest) -> Dict[str, Any]:
    return build_handoff(request)
