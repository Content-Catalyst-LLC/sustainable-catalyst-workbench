"""Workbench v4.0.2 — Project Graph, Synchronization, and Recovery Hardening."""
from __future__ import annotations

from collections import defaultdict, deque
from hashlib import sha256
import json
from typing import Any, Dict, List, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v402", tags=["Workbench v4.0.2"])
VERSION = "4.0.2"
EXPECTED_STUDIO_COUNT = 22
DESTRUCTIVE_ACTIONS = {"overwrite-remote", "overwrite-local", "delete-local", "delete-remote", "purge-tombstone", "rollback"}
TERMINAL_TRANSACTION_STATES = {"committed", "rolled-back", "aborted"}


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


def _record_id(record: Dict[str, Any], fallback: str) -> str:
    for key in ("id", "recordId", "record_id", "projectId", "project_id"):
        if record.get(key):
            return str(record[key])
    return fallback


def _record_hash(record: Dict[str, Any]) -> str:
    payload = {key: value for key, value in record.items() if key not in {"recordHash", "hash", "updatedAt", "syncedAt"}}
    return str(record.get("recordHash") or record.get("hash") or stable_hash(payload))


def _unique(values: List[str]) -> List[str]:
    seen, result = set(), []
    for value in values:
        item = str(value).strip()
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _components(node_ids: set[str], adjacency: Dict[str, List[str]]) -> List[List[str]]:
    components, visited = [], set()
    for node_id in sorted(node_ids):
        if node_id in visited:
            continue
        queue, component = deque([node_id]), []
        visited.add(node_id)
        while queue:
            current = queue.popleft()
            component.append(current)
            for neighbor in adjacency.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def _directed_cycles(node_ids: set[str], adjacency: Dict[str, List[str]]) -> List[List[str]]:
    state: Dict[str, int] = {node: 0 for node in node_ids}
    stack: List[str] = []
    cycles: List[List[str]] = []

    def visit(node: str) -> None:
        state[node] = 1
        stack.append(node)
        for neighbor in adjacency.get(node, []):
            if state.get(neighbor, 0) == 0:
                visit(neighbor)
            elif state.get(neighbor) == 1 and neighbor in stack:
                start = stack.index(neighbor)
                cycle = stack[start:] + [neighbor]
                if cycle not in cycles:
                    cycles.append(cycle)
        stack.pop()
        state[node] = 2

    for node in sorted(node_ids):
        if state[node] == 0:
            visit(node)
    return cycles


class GraphIntegrityRequest(BaseModel):
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    directed: bool = True
    required_roots: List[str] = Field(default_factory=list)
    expected_node_hashes: Dict[str, str] = Field(default_factory=dict)
    allow_self_loops: bool = False


class CheckpointRequest(BaseModel):
    project_id: str = "default"
    records: List[Dict[str, Any]] = Field(default_factory=list)
    graph: Dict[str, Any] = Field(default_factory=dict)
    previous_checkpoint_hash: str = ""
    label: str = "pre-sync"


class ReconciliationRequest(BaseModel):
    project_id: str = "default"
    local_records: List[Dict[str, Any]] = Field(default_factory=list)
    remote_records: List[Dict[str, Any]] = Field(default_factory=list)
    base_records: List[Dict[str, Any]] = Field(default_factory=list)
    strategy: Literal["manual", "keep-local", "keep-remote", "newest", "rename"] = "manual"
    backup_verified: bool = False


class SyncJournalRequest(BaseModel):
    project_id: str = "default"
    operations: List[Dict[str, Any]] = Field(default_factory=list)
    checkpoint_hash: str = ""
    previous_journal_hash: str = ""
    transaction_id: str = ""


class ReceiptVerificationRequest(BaseModel):
    journal: Dict[str, Any] = Field(default_factory=dict)
    receipt: Dict[str, Any] = Field(default_factory=dict)
    checkpoint: Dict[str, Any] = Field(default_factory=dict)


class RecoveryPlanRequest(BaseModel):
    journal: Dict[str, Any] = Field(default_factory=dict)
    receipt: Dict[str, Any] = Field(default_factory=dict)
    checkpoint: Dict[str, Any] = Field(default_factory=dict)
    backup_verified: bool = False
    allow_rollback: bool = False


class RetentionPlanRequest(BaseModel):
    tombstones: List[Dict[str, Any]] = Field(default_factory=list)
    retention_days: int = 30
    backup_verified: bool = False


class StressEvaluationRequest(BaseModel):
    nodes: int = 0
    edges: int = 0
    records: int = 0
    conflicts: int = 0
    duration_seconds: float = 0.0
    peak_memory_mb: float = 0.0
    max_duration_seconds: float = 30.0
    max_memory_mb: float = 512.0
    max_conflict_ratio: float = 0.05


def audit_graph_integrity(request: GraphIntegrityRequest) -> Dict[str, Any]:
    nodes, node_ids, duplicate_nodes, hash_mismatches = [], set(), [], []
    for index, raw in enumerate(request.nodes):
        node = dict(raw)
        node_id = _record_id(node, f"node-{index + 1}")
        if node_id in node_ids:
            duplicate_nodes.append(node_id)
            continue
        node_ids.add(node_id)
        node["id"] = node_id
        actual_hash = _record_hash(node)
        expected_hash = request.expected_node_hashes.get(node_id)
        if expected_hash and expected_hash != actual_hash:
            hash_mismatches.append({"nodeId": node_id, "expected": expected_hash, "actual": actual_hash})
        node["nodeHash"] = actual_hash
        nodes.append(node)

    edges, edge_ids, duplicate_edges, dangling_edges, self_loops = [], set(), [], [], []
    undirected: Dict[str, List[str]] = defaultdict(list)
    directed: Dict[str, List[str]] = defaultdict(list)
    inbound = defaultdict(int)
    outbound = defaultdict(int)
    for index, raw in enumerate(request.edges):
        edge = dict(raw)
        edge_id = str(edge.get("id") or f"edge-{index + 1}")
        source, target = str(edge.get("source", "")), str(edge.get("target", ""))
        if edge_id in edge_ids:
            duplicate_edges.append(edge_id)
            continue
        edge_ids.add(edge_id)
        if source not in node_ids or target not in node_ids:
            dangling_edges.append({"edgeId": edge_id, "source": source, "target": target})
            continue
        if source == target and not request.allow_self_loops:
            self_loops.append(edge_id)
            continue
        edge.update({"id": edge_id, "source": source, "target": target})
        edge["edgeHash"] = stable_hash({key: value for key, value in edge.items() if key != "edgeHash"})
        edges.append(edge)
        undirected[source].append(target)
        undirected[target].append(source)
        directed[source].append(target)
        outbound[source] += 1
        inbound[target] += 1

    components = _components(node_ids, undirected)
    cycles = _directed_cycles(node_ids, directed) if request.directed else []
    roots = [node for node in sorted(node_ids) if inbound[node] == 0]
    missing_roots = [root for root in _unique(request.required_roots) if root not in node_ids]
    isolated = [node for node in sorted(node_ids) if not undirected.get(node)]
    findings = []
    for code, items, severity in (
        ("duplicate-node-id", duplicate_nodes, "critical"),
        ("duplicate-edge-id", duplicate_edges, "critical"),
        ("dangling-edge", dangling_edges, "critical"),
        ("self-loop", self_loops, "high"),
        ("node-hash-mismatch", hash_mismatches, "critical"),
        ("required-root-missing", missing_roots, "critical"),
        ("directed-cycle", cycles, "high"),
        ("disconnected-component", components[1:] if len(components) > 1 else [], "high"),
        ("isolated-node", isolated, "medium"),
    ):
        if items:
            findings.append({"code": code, "severity": severity, "items": items})
    report = {
        "schema": "sc-workbench-project-graph-integrity-report/1.0",
        "version": VERSION,
        "nodeCount": len(nodes),
        "edgeCount": len(edges),
        "rootNodes": roots,
        "componentCount": len(components),
        "components": components,
        "cycles": cycles,
        "isolatedNodes": isolated,
        "findings": findings,
        "criticalFindingCount": sum(1 for finding in findings if finding["severity"] == "critical"),
        "ready": not any(finding["severity"] in {"critical", "high"} for finding in findings),
        "automaticMutationAuthorized": False,
    }
    report["graphHash"] = stable_hash({"nodes": nodes, "edges": edges})
    report["reportHash"] = stable_hash(report)
    return {"ok": report["ready"], "report": report}


def build_recovery_checkpoint(request: CheckpointRequest) -> Dict[str, Any]:
    records = []
    for index, raw in enumerate(request.records):
        record = dict(raw)
        record_id = _record_id(record, f"record-{index + 1}")
        records.append({"id": record_id, "recordHash": _record_hash(record), "type": record.get("type", "workbench-record")})
    records.sort(key=lambda item: item["id"])
    graph_hash = str(request.graph.get("graphHash") or stable_hash(request.graph))
    leaf_hashes = [item["recordHash"] for item in records] + [graph_hash]
    merkle_root = stable_hash(sorted(leaf_hashes))
    checkpoint = {
        "schema": "sc-workbench-recovery-checkpoint/1.0",
        "version": VERSION,
        "projectId": request.project_id.strip() or "default",
        "label": request.label.strip() or "pre-sync",
        "records": records,
        "recordCount": len(records),
        "graphHash": graph_hash,
        "merkleRoot": merkle_root,
        "previousCheckpointHash": request.previous_checkpoint_hash,
        "restorable": True,
        "automaticRestoreAuthorized": False,
    }
    checkpoint["checkpointHash"] = stable_hash(checkpoint)
    return {"ok": True, "checkpoint": checkpoint}


def build_sync_reconciliation(request: ReconciliationRequest) -> Dict[str, Any]:
    def index(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        result = {}
        for position, raw in enumerate(records):
            record = dict(raw)
            record_id = _record_id(record, f"record-{position + 1}")
            result[record_id] = {"record": record, "hash": _record_hash(record)}
        return result

    local, remote, base = index(request.local_records), index(request.remote_records), index(request.base_records)
    ids = sorted(set(local) | set(remote) | set(base))
    states, conflicts, actions, blocked = [], [], [], []
    for record_id in ids:
        l, r, b = local.get(record_id), remote.get(record_id), base.get(record_id)
        lh, rh, bh = l and l["hash"], r and r["hash"], b and b["hash"]
        if l and r and lh == rh:
            state = "in-sync"
        elif l and not r:
            state = "local-only" if not b else "remote-deleted"
        elif r and not l:
            state = "remote-only" if not b else "local-deleted"
        elif not l and not r:
            state = "deleted-both"
        elif b and lh == bh and rh != bh:
            state = "remote-changed"
        elif b and rh == bh and lh != bh:
            state = "local-changed"
        elif b and lh != bh and rh != bh and lh != rh:
            state = "conflict"
        else:
            state = "diverged"
        entry = {"recordId": record_id, "state": state, "localHash": lh, "remoteHash": rh, "baseHash": bh}
        states.append(entry)
        if state in {"conflict", "diverged", "local-deleted", "remote-deleted"}:
            conflicts.append(entry)

        action = None
        if state == "local-only": action = "create-remote"
        elif state == "remote-only": action = "create-local"
        elif state == "local-changed": action = "update-remote"
        elif state == "remote-changed": action = "update-local"
        elif state in {"conflict", "diverged", "local-deleted", "remote-deleted"}:
            if request.strategy == "keep-local": action = "overwrite-remote" if l else "delete-remote"
            elif request.strategy == "keep-remote": action = "overwrite-local" if r else "delete-local"
            elif request.strategy == "rename": action = "create-conflict-copy"
            elif request.strategy == "newest":
                local_time = str((l or {}).get("record", {}).get("updatedAt", ""))
                remote_time = str((r or {}).get("record", {}).get("updatedAt", ""))
                action = "overwrite-remote" if local_time > remote_time else "overwrite-local"
            else: action = "manual-review"
        if action:
            operation = {"recordId": record_id, "action": action, "idempotencyKey": stable_hash([request.project_id, record_id, action, lh, rh, bh])}
            if action in DESTRUCTIVE_ACTIONS and not request.backup_verified:
                operation["blockedBy"] = "verified-backup-required"
                blocked.append(operation)
            else:
                actions.append(operation)

    plan = {
        "schema": "sc-workbench-sync-reconciliation-plan/1.0",
        "version": VERSION,
        "projectId": request.project_id.strip() or "default",
        "strategy": request.strategy,
        "states": states,
        "conflicts": conflicts,
        "actions": actions,
        "blockedActions": blocked,
        "backupVerified": request.backup_verified,
        "automaticExecutionAuthorized": False,
        "automaticDeletionAuthorized": False,
        "ready": not conflicts and not blocked,
    }
    plan["planHash"] = stable_hash(plan)
    return {"ok": plan["ready"], "plan": plan}


def build_sync_journal(request: SyncJournalRequest) -> Dict[str, Any]:
    operations = []
    for index, raw in enumerate(request.operations):
        operation = dict(raw)
        operation.setdefault("sequence", index + 1)
        operation.setdefault("status", "prepared")
        operation.setdefault("idempotencyKey", stable_hash([request.project_id, operation.get("recordId"), operation.get("action"), operation["sequence"]]))
        operation["operationHash"] = stable_hash({key: value for key, value in operation.items() if key != "operationHash"})
        operations.append(operation)
    transaction_id = request.transaction_id.strip() or "txn-" + stable_hash([request.project_id, request.checkpoint_hash, operations])[:16]
    journal = {
        "schema": "sc-workbench-sync-transaction-journal/1.0",
        "version": VERSION,
        "transactionId": transaction_id,
        "projectId": request.project_id.strip() or "default",
        "state": "prepared",
        "phases": ["prepared", "applying", "verifying", "committed"],
        "operations": operations,
        "operationCount": len(operations),
        "checkpointHash": request.checkpoint_hash,
        "previousJournalHash": request.previous_journal_hash,
        "resumeSupported": True,
        "automaticCommitAuthorized": False,
    }
    journal["journalHash"] = stable_hash(journal)
    return {"ok": bool(request.checkpoint_hash), "journal": journal}


def verify_sync_receipt(request: ReceiptVerificationRequest) -> Dict[str, Any]:
    journal, receipt, checkpoint = request.journal, request.receipt, request.checkpoint
    expected_journal_hash = str(journal.get("journalHash") or stable_hash({key: value for key, value in journal.items() if key != "journalHash"}))
    expected_checkpoint_hash = str(checkpoint.get("checkpointHash") or journal.get("checkpointHash") or "")
    operation_count = int(journal.get("operationCount", len(journal.get("operations", []))))
    received_operations = receipt.get("operations", []) if isinstance(receipt.get("operations"), list) else []
    findings = []
    if receipt.get("transactionId") != journal.get("transactionId"): findings.append("transaction-id-mismatch")
    if receipt.get("journalHash") != expected_journal_hash: findings.append("journal-hash-mismatch")
    if expected_checkpoint_hash and receipt.get("checkpointHash") != expected_checkpoint_hash: findings.append("checkpoint-hash-mismatch")
    if len(received_operations) != operation_count: findings.append("operation-receipt-count-mismatch")
    failed = [item for item in received_operations if str(item.get("status", "")).lower() not in {"applied", "verified", "skipped-idempotent"}]
    if failed: findings.append("operation-receipt-failure")
    if str(receipt.get("state", "")).lower() != "committed": findings.append("transaction-not-committed")
    report = {
        "schema": "sc-workbench-sync-receipt-verification/1.0",
        "version": VERSION,
        "transactionId": journal.get("transactionId"),
        "expectedOperationCount": operation_count,
        "receivedOperationCount": len(received_operations),
        "failedOperations": failed,
        "findings": findings,
        "verified": not findings,
        "automaticAcceptanceAuthorized": False,
    }
    report["verificationHash"] = stable_hash(report)
    return {"ok": report["verified"], "report": report}


def build_interrupted_sync_recovery(request: RecoveryPlanRequest) -> Dict[str, Any]:
    journal, receipt, checkpoint = request.journal, request.receipt, request.checkpoint
    state = str(journal.get("state", "unknown")).lower()
    receipt_result = verify_sync_receipt(ReceiptVerificationRequest(journal=journal, receipt=receipt, checkpoint=checkpoint)) if receipt else {"ok": False, "report": {"findings": ["receipt-missing"]}}
    checkpoint_valid = bool(checkpoint.get("checkpointHash")) and checkpoint.get("checkpointHash") == journal.get("checkpointHash")
    actions, blocked = [], []
    if state in TERMINAL_TRANSACTION_STATES:
        actions.append({"action": "archive-transaction", "safe": True})
    elif state == "prepared":
        actions.append({"action": "resume-from-first-operation", "safe": True})
    elif state == "applying":
        actions.append({"action": "resume-idempotent-operations", "safe": True})
    elif state == "verifying":
        actions.append({"action": "re-run-receipt-verification", "safe": True})
    else:
        actions.append({"action": "manual-transaction-inspection", "safe": True})
    if not receipt_result["ok"]:
        actions.append({"action": "request-target-receipt", "safe": True})
    if checkpoint_valid and request.backup_verified and request.allow_rollback:
        actions.append({"action": "rollback", "safe": False, "requiresConfirmation": "ROLLBACK CONNECTED PROJECT"})
    elif state not in TERMINAL_TRANSACTION_STATES:
        blocked.append({"action": "rollback", "blockedBy": "verified-backup-and-explicit-authorization-required"})
    plan = {
        "schema": "sc-workbench-interrupted-sync-recovery-plan/1.0",
        "version": VERSION,
        "transactionId": journal.get("transactionId"),
        "journalState": state,
        "checkpointValid": checkpoint_valid,
        "receiptVerified": receipt_result["ok"],
        "actions": actions,
        "blockedActions": blocked,
        "automaticRollbackAuthorized": False,
        "automaticDeletionAuthorized": False,
        "ready": bool(actions) and not (state not in TERMINAL_TRANSACTION_STATES and not checkpoint_valid),
    }
    plan["recoveryPlanHash"] = stable_hash(plan)
    return {"ok": plan["ready"], "plan": plan}


def build_tombstone_retention_plan(request: RetentionPlanRequest) -> Dict[str, Any]:
    retain, purge, blocked = [], [], []
    for index, raw in enumerate(request.tombstones):
        item = dict(raw)
        item_id = _record_id(item, f"tombstone-{index + 1}")
        age = max(0, int(item.get("ageDays", 0)))
        entry = {"recordId": item_id, "ageDays": age, "retentionDays": request.retention_days}
        if age < request.retention_days:
            retain.append(entry)
        elif not request.backup_verified:
            entry["blockedBy"] = "verified-backup-required"
            blocked.append(entry)
        else:
            entry["action"] = "purge-tombstone"
            entry["requiresConfirmation"] = "PURGE SYNC TOMBSTONES"
            purge.append(entry)
    plan = {
        "schema": "sc-workbench-sync-tombstone-retention-plan/1.0",
        "version": VERSION,
        "retentionDays": request.retention_days,
        "retain": retain,
        "purgeCandidates": purge,
        "blocked": blocked,
        "automaticPurgeAuthorized": False,
        "ready": not blocked,
    }
    plan["planHash"] = stable_hash(plan)
    return {"ok": plan["ready"], "plan": plan}


def evaluate_graph_sync_stress(request: StressEvaluationRequest) -> Dict[str, Any]:
    ratio = request.conflicts / max(request.records, 1)
    findings = []
    if request.duration_seconds > request.max_duration_seconds: findings.append({"code": "duration-budget-exceeded", "severity": "high"})
    if request.peak_memory_mb > request.max_memory_mb: findings.append({"code": "memory-budget-exceeded", "severity": "high"})
    if ratio > request.max_conflict_ratio: findings.append({"code": "conflict-ratio-exceeded", "severity": "high"})
    if request.edges > max(request.nodes * 20, 1000): findings.append({"code": "graph-density-review", "severity": "medium"})
    report = {
        "schema": "sc-workbench-project-graph-sync-stress-report/1.0",
        "version": VERSION,
        "nodes": request.nodes,
        "edges": request.edges,
        "records": request.records,
        "conflicts": request.conflicts,
        "conflictRatio": ratio,
        "durationSeconds": request.duration_seconds,
        "peakMemoryMb": request.peak_memory_mb,
        "budgets": {"durationSeconds": request.max_duration_seconds, "memoryMb": request.max_memory_mb, "conflictRatio": request.max_conflict_ratio},
        "findings": findings,
        "ready": not any(item["severity"] == "high" for item in findings),
        "humanReviewRequired": True,
    }
    report["reportHash"] = stable_hash(report)
    return {"ok": report["ready"], "report": report}


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-workbench-project-graph-sync-recovery-status/1.0",
        "version": VERSION,
        "milestone": "Project Graph, Synchronization, and Recovery Hardening",
        "expectedStudioCount": EXPECTED_STUDIO_COUNT,
        "threeWayReconciliation": True,
        "idempotentSyncJournals": True,
        "contentAddressedCheckpoints": True,
        "interruptedSyncRecovery": True,
        "renderRequired": False,
        "automaticExecutionAuthorized": False,
        "automaticRollbackAuthorized": False,
        "automaticDeletionAuthorized": False,
    }


@router.get("/status")
def status_route() -> Dict[str, Any]: return status()

@router.post("/graph/audit")
def graph_audit_route(request: GraphIntegrityRequest) -> Dict[str, Any]: return audit_graph_integrity(request)

@router.post("/checkpoint/build")
def checkpoint_route(request: CheckpointRequest) -> Dict[str, Any]: return build_recovery_checkpoint(request)

@router.post("/sync/reconcile")
def sync_reconcile_route(request: ReconciliationRequest) -> Dict[str, Any]: return build_sync_reconciliation(request)

@router.post("/sync/journal")
def sync_journal_route(request: SyncJournalRequest) -> Dict[str, Any]: return build_sync_journal(request)

@router.post("/sync/receipt/verify")
def sync_receipt_route(request: ReceiptVerificationRequest) -> Dict[str, Any]: return verify_sync_receipt(request)

@router.post("/recovery/plan")
def recovery_route(request: RecoveryPlanRequest) -> Dict[str, Any]: return build_interrupted_sync_recovery(request)

@router.post("/tombstones/retention")
def tombstone_route(request: RetentionPlanRequest) -> Dict[str, Any]: return build_tombstone_retention_plan(request)

@router.post("/stress/evaluate")
def stress_route(request: StressEvaluationRequest) -> Dict[str, Any]: return evaluate_graph_sync_stress(request)
