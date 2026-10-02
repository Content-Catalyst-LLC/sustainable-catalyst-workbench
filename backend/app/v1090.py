"""Workbench v10.9.0 — Agent / Computational Graph Workspace.

Defines governed computational-agent and graph workflow contracts for research computation:
explicit nodes/edges, DAG validation, tool/action contracts, human approval gates, checkpoints,
handoffs, replayability, state transitions, execution provenance, and Platform Core promotion planning.

This release is declarative by default. It does not autonomously execute external side effects,
silently call tools, bypass approval gates, self-modify workflow graphs, or dispatch governed
Platform Core objects automatically.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Set

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v810 import _atomic_json_write, _json_read, _store_root

VERSION = APP_VERSION
SCHEMA = "sc-workbench-agent-computational-graph-workspace/1.0"
GRAPH_SCHEMA = "sc-workbench-agent-computational-graph/1.0"
RUN_SCHEMA = "sc-workbench-agent-computational-graph-run/1.0"
EVENT_SCHEMA = "sc-workbench-agent-computational-graph-event/1.0"
REPLAY_SCHEMA = "sc-workbench-agent-computational-graph-replay-plan/1.0"
DIAGNOSTIC_SCHEMA = "sc-workbench-agent-computational-graph-diagnostic/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-agent-computational-graph-core-plan/1.0"

router = APIRouter(tags=["workbench-v1090-agent-computational-graph-workspace"])

_HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")

NodeKind = Literal[
    "agent",
    "compute",
    "tool",
    "transform",
    "decision",
    "human-approval",
    "checkpoint",
    "handoff",
]
ExecutionState = Literal[
    "planned", "ready", "running", "blocked", "waiting-approval",
    "succeeded", "failed", "cancelled", "skipped",
]
ActionRisk = Literal["none", "read-only", "external-side-effect", "destructive"]
CoreObjectKind = Literal["graph", "run", "event", "replay-plan", "diagnostic"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_hash(value: str) -> bool:
    return bool(_HASH_RE.match(value or ""))


def _project_root(project_key: str) -> Path:
    return _store_root() / "agent-computational-graph" / _stable_id(project_key)


def _graph_dir(project_key: str) -> Path:
    return _project_root(project_key) / "graphs"


def _graph_path(project_key: str, graph_hash: str) -> Path:
    return _graph_dir(project_key) / f"{graph_hash}.json"


def _run_dir(project_key: str, graph_hash: str) -> Path:
    return _project_root(project_key) / "runs" / graph_hash


def _run_path(project_key: str, graph_hash: str, run_hash: str) -> Path:
    return _run_dir(project_key, graph_hash) / f"{run_hash}.json"


class ToolContract(BaseModel):
    toolKey: str = Field(min_length=1, max_length=300)
    action: str = Field(min_length=1, max_length=500)
    risk: ActionRisk = "read-only"
    inputSchema: Dict[str, Any] = Field(default_factory=dict)
    outputSchema: Dict[str, Any] = Field(default_factory=dict)
    idempotent: bool = False
    reversible: bool = False
    requiresHumanApproval: bool = False
    notes: str = Field(default="", max_length=10000)

    @model_validator(mode="after")
    def validate_risk(self):
        if self.risk in {"external-side-effect", "destructive"} and not self.requiresHumanApproval:
            raise ValueError("side-effecting/destructive tool contracts require human approval")
        return self


class AgentContract(BaseModel):
    agentKey: str = Field(min_length=1, max_length=300)
    role: str = Field(min_length=1, max_length=500)
    objective: str = Field(default="", max_length=10000)
    allowedToolKeys: List[str] = Field(default_factory=list, max_length=1000)
    maxSteps: Optional[int] = Field(default=None, ge=1, le=100000)
    requiresHumanApprovalForSideEffects: bool = True
    notes: str = Field(default="", max_length=10000)


class GraphNode(BaseModel):
    nodeKey: str = Field(min_length=1, max_length=300)
    kind: NodeKind
    title: str = Field(min_length=1, max_length=500)
    agentKey: Optional[str] = Field(default=None, max_length=300)
    toolKey: Optional[str] = Field(default=None, max_length=300)
    operation: Optional[str] = Field(default=None, max_length=1000)
    config: Dict[str, Any] = Field(default_factory=dict)
    checkpoint: bool = False
    approvalRequired: bool = False

    @model_validator(mode="after")
    def validate_kind_binding(self):
        if self.kind == "agent" and not self.agentKey:
            raise ValueError("agent node requires agentKey")
        if self.kind == "tool" and not self.toolKey:
            raise ValueError("tool node requires toolKey")
        if self.kind == "human-approval":
            self.approvalRequired = True
        return self


class GraphEdge(BaseModel):
    fromNode: str = Field(min_length=1, max_length=300)
    toNode: str = Field(min_length=1, max_length=300)
    condition: Optional[str] = Field(default=None, max_length=5000)
    label: Optional[str] = Field(default=None, max_length=500)


class GraphRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=300)
    graphKey: str = Field(min_length=1, max_length=300)
    title: str = Field(min_length=1, max_length=500)

    agents: List[AgentContract] = Field(default_factory=list, max_length=1000)
    tools: List[ToolContract] = Field(default_factory=list, max_length=1000)
    nodes: List[GraphNode] = Field(default_factory=list, min_length=1, max_length=10000)
    edges: List[GraphEdge] = Field(default_factory=list, max_length=50000)

    datasetRecordHashes: List[str] = Field(default_factory=list, max_length=10000)
    modelRecordHashes: List[str] = Field(default_factory=list, max_length=10000)
    scientificMLStudyHashes: List[str] = Field(default_factory=list, max_length=10000)
    uncertaintyStudyHashes: List[str] = Field(default_factory=list, max_length=10000)
    explainabilityStudyHashes: List[str] = Field(default_factory=list, max_length=10000)

    allowExternalSideEffects: bool = False
    requireExplicitRunApproval: bool = True
    notes: str = Field(default="", max_length=10000)

    @model_validator(mode="after")
    def validate_graph(self):
        for collection_name in (
            "datasetRecordHashes", "modelRecordHashes", "scientificMLStudyHashes",
            "uncertaintyStudyHashes", "explainabilityStudyHashes"
        ):
            for value in getattr(self, collection_name):
                if not _is_hash(value):
                    raise ValueError(f"{collection_name} must contain SHA-256 digests")

        node_keys = [n.nodeKey for n in self.nodes]
        if len(set(node_keys)) != len(node_keys):
            raise ValueError("node keys must be unique")

        agent_keys = [a.agentKey for a in self.agents]
        if len(set(agent_keys)) != len(agent_keys):
            raise ValueError("agent keys must be unique")

        tool_keys = [t.toolKey for t in self.tools]
        if len(set(tool_keys)) != len(tool_keys):
            raise ValueError("tool keys must be unique")

        node_set = set(node_keys)
        for e in self.edges:
            if e.fromNode not in node_set or e.toNode not in node_set:
                raise ValueError("edges must reference existing nodes")
            if e.fromNode == e.toNode:
                raise ValueError("self-cycle edges are not allowed")

        agent_set = set(agent_keys)
        tool_set = set(tool_keys)

        for n in self.nodes:
            if n.agentKey and n.agentKey not in agent_set:
                raise ValueError(f"node references undefined agentKey: {n.agentKey}")
            if n.toolKey and n.toolKey not in tool_set:
                raise ValueError(f"node references undefined toolKey: {n.toolKey}")

        for a in self.agents:
            unknown = [k for k in a.allowedToolKeys if k not in tool_set]
            if unknown:
                raise ValueError(f"agent {a.agentKey} references undefined tools: {unknown}")

        risky_tools = {t.toolKey for t in self.tools if t.risk in {"external-side-effect", "destructive"}}
        if risky_tools and not self.allowExternalSideEffects:
            # Contract may exist, but graph must not be executable for side effects.
            pass

        # DAG validation.
        adjacency = {k: [] for k in node_keys}
        indegree = {k: 0 for k in node_keys}
        for e in self.edges:
            adjacency[e.fromNode].append(e.toNode)
            indegree[e.toNode] += 1

        queue = [k for k, v in indegree.items() if v == 0]
        visited = 0
        while queue:
            n = queue.pop(0)
            visited += 1
            for nxt in adjacency[n]:
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)
        if visited != len(node_keys):
            raise ValueError("computational graph must be acyclic")

        # Any risky tool node must have an approval node upstream somewhere.
        risky_node_keys = {n.nodeKey for n in self.nodes if n.kind == "tool" and n.toolKey in risky_tools}
        if risky_node_keys:
            parents = {k: [] for k in node_keys}
            for e in self.edges:
                parents[e.toNode].append(e.fromNode)
            approval_nodes = {n.nodeKey for n in self.nodes if n.kind == "human-approval"}

            def has_approval_ancestor(node_key: str) -> bool:
                stack = list(parents[node_key])
                seen: Set[str] = set()
                while stack:
                    cur = stack.pop()
                    if cur in seen:
                        continue
                    seen.add(cur)
                    if cur in approval_nodes:
                        return True
                    stack.extend(parents[cur])
                return False

            missing = [k for k in risky_node_keys if not has_approval_ancestor(k)]
            if missing:
                raise ValueError(f"risky tool nodes require upstream human approval: {missing}")

        return self


class NodeRunState(BaseModel):
    nodeKey: str = Field(min_length=1, max_length=300)
    state: ExecutionState
    startedAt: Optional[str] = None
    completedAt: Optional[str] = None
    outputRecordHash: Optional[str] = None
    error: Optional[str] = Field(default=None, max_length=10000)

    @model_validator(mode="after")
    def validate_hash(self):
        if self.outputRecordHash is not None and not _is_hash(self.outputRecordHash):
            raise ValueError("outputRecordHash must be a SHA-256 digest")
        return self


class RunRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=300)
    graphHash: str
    requestedBy: str = Field(default="user", max_length=300)
    approved: bool = False
    dryRun: bool = True
    executionRuntime: Optional[str] = Field(default=None, max_length=300)
    executionRuntimeVersion: Optional[str] = Field(default=None, max_length=300)
    nodeStates: List[NodeRunState] = Field(default_factory=list, max_length=10000)
    notes: str = Field(default="", max_length=10000)

    @model_validator(mode="after")
    def validate_hash(self):
        if not _is_hash(self.graphHash):
            raise ValueError("graphHash must be a SHA-256 digest")
        return self


class ReplayRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=300)
    graphHash: str
    runHash: str
    fromCheckpointNode: Optional[str] = Field(default=None, max_length=300)
    requestedBy: str = Field(default="user", max_length=300)

    @model_validator(mode="after")
    def validate_hashes(self):
        if not _is_hash(self.graphHash) or not _is_hash(self.runHash):
            raise ValueError("graphHash and runHash must be SHA-256 digests")
        return self


class CorePlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=300)
    objectKind: CoreObjectKind
    objectHash: str
    requestedBy: str = Field(default="user", max_length=300)

    @model_validator(mode="after")
    def validate_hash(self):
        if not _is_hash(self.objectHash):
            raise ValueError("objectHash must be a SHA-256 digest")
        return self


def _topological_order(req: GraphRequest) -> List[str]:
    keys = [n.nodeKey for n in req.nodes]
    adjacency = {k: [] for k in keys}
    indegree = {k: 0 for k in keys}
    for e in req.edges:
        adjacency[e.fromNode].append(e.toNode)
        indegree[e.toNode] += 1

    queue = sorted([k for k, v in indegree.items() if v == 0])
    order = []
    while queue:
        cur = queue.pop(0)
        order.append(cur)
        for nxt in sorted(adjacency[cur]):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
                queue.sort()
    return order


def _issues_for(req: GraphRequest) -> List[Dict[str, str]]:
    issues = []
    risky = [t for t in req.tools if t.risk in {"external-side-effect", "destructive"}]

    if risky and not req.allowExternalSideEffects:
        issues.append({
            "severity": "warning",
            "code": "external-side-effects-disabled",
            "message": "The graph contains side-effecting tool contracts, but external side effects are disabled for this graph.",
        })

    if risky:
        issues.append({
            "severity": "warning",
            "code": "side-effects-require-human-approval",
            "message": "Side-effecting or destructive actions require an explicit human approval gate before execution.",
        })

    issues.append({
        "severity": "info",
        "code": "agents-are-governed-computational-actors",
        "message": "Agent nodes are constrained by explicit graph, tool, approval, and provenance contracts.",
    })

    issues.append({
        "severity": "warning",
        "code": "graph-plan-not-execution",
        "message": "A composed graph is a governed execution plan and does not itself execute tools or external actions.",
    })
    return issues


def _graph_payload(req: GraphRequest) -> Dict[str, Any]:
    payload = req.model_dump(mode="json")
    payload.update({
        "schema": GRAPH_SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "topologicalOrder": _topological_order(req),
        "issues": _issues_for(req),
        "automaticToolExecution": False,
        "automaticExternalSideEffects": False,
        "automaticApprovalBypass": False,
        "selfModificationAllowed": False,
    })
    return payload


def compose_graph(req: GraphRequest) -> Dict[str, Any]:
    payload = _graph_payload(req)
    graph_hash = content_hash(payload)
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "graphHash": graph_hash,
        "graph": payload,
        "issues": payload["issues"],
        "graphReady": True,
    }


def save_graph(req: GraphRequest) -> Dict[str, Any]:
    row = compose_graph(req)
    path = _graph_path(req.projectKey, row["graphHash"])
    existing = _json_read(path) if path.exists() else None
    if existing is not None:
        return {**row, "saved": True, "idempotent": True}
    record = {**row["graph"], "graphHash": row["graphHash"], "createdAt": _now()}
    _atomic_json_write(path, record)
    return {**row, "saved": True, "idempotent": False}


def list_graphs(project_key: str) -> Dict[str, Any]:
    rows = []
    directory = _graph_dir(project_key)
    if directory.exists():
        for path in sorted(directory.glob("*.json")):
            row = _json_read(path)
            if isinstance(row, dict):
                rows.append(row)
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "projectKey": project_key, "graphs": rows}


def get_graph(project_key: str, graph_hash: str) -> Dict[str, Any]:
    path = _graph_path(project_key, graph_hash)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Agent/computational graph not found")
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "graph": _json_read(path)}


def record_run(req: RunRequest) -> Dict[str, Any]:
    graph_path = _graph_path(req.projectKey, req.graphHash)
    if not graph_path.exists():
        raise HTTPException(status_code=404, detail="Agent/computational graph not found")
    graph = _json_read(graph_path)

    if graph.get("requireExplicitRunApproval", True) and not req.approved:
        raise HTTPException(status_code=409, detail="Run requires explicit approval")

    if graph.get("allowExternalSideEffects", False) and req.dryRun:
        pass

    payload = req.model_dump(mode="json")
    payload.update({
        "schema": RUN_SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "graphKey": graph["graphKey"],
        "graphHash": req.graphHash,
        "topologicalOrder": graph["topologicalOrder"],
        "externalSideEffectsExecuted": False,
        "approvalBypassed": False,
    })

    run_hash = content_hash(payload)
    path = _run_path(req.projectKey, req.graphHash, run_hash)
    existing = _json_read(path) if path.exists() else None
    if existing is None:
        payload.update({"runHash": run_hash, "recordedAt": _now()})
        _atomic_json_write(path, payload)

    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "runHash": run_hash,
        "run": existing or payload,
        "idempotent": existing is not None,
    }


def list_runs(project_key: str, graph_hash: str) -> Dict[str, Any]:
    rows = []
    directory = _run_dir(project_key, graph_hash)
    if directory.exists():
        for path in sorted(directory.glob("*.json")):
            row = _json_read(path)
            if isinstance(row, dict):
                rows.append(row)
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "projectKey": project_key,
        "graphHash": graph_hash,
        "runs": rows,
    }


def replay_plan(req: ReplayRequest) -> Dict[str, Any]:
    graph_path = _graph_path(req.projectKey, req.graphHash)
    run_path = _run_path(req.projectKey, req.graphHash, req.runHash)
    if not graph_path.exists():
        raise HTTPException(status_code=404, detail="Agent/computational graph not found")
    if not run_path.exists():
        raise HTTPException(status_code=404, detail="Graph run not found")

    graph = _json_read(graph_path)
    run = _json_read(run_path)

    if req.fromCheckpointNode is not None:
        checkpoints = {
            n["nodeKey"]
            for n in graph.get("nodes", [])
            if n.get("checkpoint") or n.get("kind") == "checkpoint"
        }
        if req.fromCheckpointNode not in checkpoints:
            raise HTTPException(status_code=422, detail="Requested replay node is not a checkpoint")

    payload = {
        "schema": REPLAY_SCHEMA,
        "version": VERSION,
        "projectKey": req.projectKey,
        "graphHash": req.graphHash,
        "runHash": req.runHash,
        "fromCheckpointNode": req.fromCheckpointNode,
        "requestedBy": req.requestedBy,
        "topologicalOrder": graph["topologicalOrder"],
        "sourceNodeStates": run.get("nodeStates", []),
        "automaticExecution": False,
        "explicitApprovalRequired": True,
    }
    payload["replayPlanHash"] = content_hash(payload)
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "replayPlan": payload}


def diagnose(req: GraphRequest) -> Dict[str, Any]:
    issues = _issues_for(req)
    return {
        "ok": True,
        "schema": DIAGNOSTIC_SCHEMA,
        "version": VERSION,
        "issues": issues,
        "blocking": any(i["severity"] == "error" for i in issues),
        "topologicalOrder": _topological_order(req),
    }


def core_plan(req: CorePlanRequest) -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": CORE_PLAN_SCHEMA,
        "version": VERSION,
        "plan": {
            "objectKind": req.objectKind,
            "objectHash": req.objectHash,
            "requestedBy": req.requestedBy,
            "governedCoreObjectCreated": False,
            "automaticDispatch": False,
            "requiredAction": "Submit through a governed Platform Core handoff after explicit review.",
        },
    }


def manifest() -> Dict[str, Any]:
    body = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Agent / Computational Graph Workspace",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "graphSchema": GRAPH_SCHEMA,
        "runSchema": RUN_SCHEMA,
        "capabilities": {
            "governedAgentContracts": True,
            "toolActionContracts": True,
            "directedAcyclicGraphValidation": True,
            "topologicalExecutionPlanning": True,
            "humanApprovalGates": True,
            "sideEffectRiskContracts": True,
            "checkpointNodes": True,
            "handoffNodes": True,
            "decisionNodes": True,
            "nodeExecutionStateRecords": True,
            "runProvenance": True,
            "replayPlanning": True,
            "datasetModelStudyBindings": True,
            "scientificMLHandoffs": True,
            "uncertaintyHandoffs": True,
            "explainabilityHandoffs": True,
            "platformCorePromotionPlanning": True,
        },
        "boundaries": {
            "automaticToolExecution": False,
            "automaticExternalSideEffects": False,
            "automaticHumanApproval": False,
            "automaticApprovalBypass": False,
            "autonomousGraphSelfModification": False,
            "automaticCoreDispatch": False,
            "governedCoreObjectCreated": False,
        },
        "nodeKinds": [
            "agent", "compute", "tool", "transform", "decision",
            "human-approval", "checkpoint", "handoff",
        ],
        "executionStates": [
            "planned", "ready", "running", "blocked", "waiting-approval",
            "succeeded", "failed", "cancelled", "skipped",
        ],
    }
    body["manifestHash"] = content_hash({
        k: v for k, v in body.items()
        if k not in {"ok", "manifestHash"}
    })
    return body


@router.get("/v1090/status")
def status_route():
    return manifest()


@router.post("/agent-graph/graphs/compose")
def compose_route(req: GraphRequest):
    return compose_graph(req)


@router.post("/agent-graph/graphs")
def save_route(req: GraphRequest):
    return save_graph(req)


@router.get("/agent-graph/graphs/{project_key}")
def list_route(project_key: str):
    return list_graphs(project_key)


@router.get("/agent-graph/graphs/{project_key}/{graph_hash}")
def get_route(project_key: str, graph_hash: str):
    return get_graph(project_key, graph_hash)


@router.post("/agent-graph/runs")
def run_route(req: RunRequest):
    return record_run(req)


@router.get("/agent-graph/runs/{project_key}/{graph_hash}")
def runs_route(project_key: str, graph_hash: str):
    return list_runs(project_key, graph_hash)


@router.post("/agent-graph/replay-plan")
def replay_route(req: ReplayRequest):
    return replay_plan(req)


@router.post("/agent-graph/diagnose")
def diagnose_route(req: GraphRequest):
    return diagnose(req)


@router.post("/agent-graph/core-plan")
def core_plan_route(req: CorePlanRequest):
    return core_plan(req)
