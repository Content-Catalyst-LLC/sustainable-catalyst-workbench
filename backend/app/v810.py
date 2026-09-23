"""Workbench v8.1.0 — Research Environment Persistence & Recovery.

Durable, revisioned persistence for v8 unified computational research environments.
The store is file-backed, atomically written, append-only at the revision layer, and
checkpoint-aware. Recovery always creates a new revision instead of destructively
rewinding history. No scientific computation, notebook replay, workflow execution,
or Platform Core dispatch is performed by this persistence layer.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from .release import APP_VERSION
from .v510 import content_hash
from .v800 import ENVIRONMENT_SCHEMA, validate_environment

VERSION = APP_VERSION
SCHEMA = "sc-workbench-research-environment-persistence-recovery/1.0"
REVISION_SCHEMA = "sc-workbench-research-environment-revision/1.0"
CHECKPOINT_SCHEMA = "sc-workbench-research-environment-checkpoint/1.0"
RECOVERY_PLAN_SCHEMA = "sc-workbench-research-environment-recovery-plan/1.0"
RECOVERY_RESULT_SCHEMA = "sc-workbench-research-environment-recovery-result/1.0"
STORE_INDEX_SCHEMA = "sc-workbench-research-environment-store-index/1.0"
DEFAULT_STORE_ROOT = "/data/research-environments"
MAX_REVISIONS_RETURNED = 500
MAX_CHECKPOINTS_RETURNED = 500

router = APIRouter(tags=["workbench-v810-research-environment-persistence-recovery"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _store_root() -> Path:
    return Path(os.getenv("SCWB_RESEARCH_ENVIRONMENT_STORE", DEFAULT_STORE_ROOT)).expanduser().resolve()


def _key_id(environment_key: str) -> str:
    return hashlib.sha256(environment_key.encode("utf-8")).hexdigest()


def _env_dir(environment_key: str) -> Path:
    return _store_root() / "environments" / _key_id(environment_key)


def _json_read(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        value = json.load(fh)
    if not isinstance(value, dict):
        raise ValueError(f"invalid object in {path.name}")
    return value


def _atomic_json_write(path: Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    with tmp.open("w", encoding="utf-8") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


@contextmanager
def _environment_lock(environment_key: str):
    lock_path = _store_root() / "locks" / f"{_key_id(environment_key)}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def _ensure_environment(environment: Dict[str, Any]) -> str:
    result = validate_environment(environment)
    if not result.get("valid"):
        raise ValueError("researchEnvironment integrity validation failed")
    key = str(environment.get("environmentKey") or "").strip()
    if not key:
        raise ValueError("researchEnvironment.environmentKey is required")
    return key


def _index_path(environment_key: str) -> Path:
    return _env_dir(environment_key) / "index.json"


def _load_index(environment_key: str) -> Dict[str, Any]:
    path = _index_path(environment_key)
    if not path.exists():
        return {
            "schema": STORE_INDEX_SCHEMA,
            "version": VERSION,
            "environmentKey": environment_key,
            "currentRevision": 0,
            "currentRevisionHash": None,
            "revisionCount": 0,
            "checkpointCount": 0,
            "updatedAt": None,
        }
    idx = _json_read(path)
    if idx.get("environmentKey") != environment_key:
        raise ValueError("environment store key mismatch")
    return idx


def _revision_path(environment_key: str, revision: int) -> Path:
    return _env_dir(environment_key) / "revisions" / f"{revision:010d}.json"


def _revision_hash(record: Dict[str, Any]) -> str:
    candidate = deepcopy(record)
    candidate.pop("revisionHash", None)
    candidate.pop("revisionRef", None)
    return content_hash(candidate)


def _validate_revision_record(record: Dict[str, Any]) -> bool:
    given = record.get("revisionHash")
    if not given or given != _revision_hash(record):
        return False
    env = record.get("researchEnvironment")
    return isinstance(env, dict) and bool(validate_environment(env).get("valid")) and record.get("environmentHash") == env.get("environmentHash")


def _load_revision(environment_key: str, revision: int) -> Dict[str, Any]:
    path = _revision_path(environment_key, revision)
    if not path.exists():
        raise FileNotFoundError(f"revision {revision} not found for environment {environment_key}")
    record = _json_read(path)
    if not _validate_revision_record(record):
        raise ValueError(f"stored revision {revision} failed integrity validation")
    return record


def _write_revision(
    environment: Dict[str, Any], *, revision: int, parent_revision: int,
    parent_revision_hash: Optional[str], actor: str, reason: str,
    recovered_from: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    key = _ensure_environment(environment)
    record: Dict[str, Any] = {
        "ok": True,
        "schema": REVISION_SCHEMA,
        "version": VERSION,
        "environmentKey": key,
        "revision": revision,
        "parentRevision": parent_revision or None,
        "parentRevisionHash": parent_revision_hash,
        "environmentHash": environment.get("environmentHash"),
        "researchEnvironment": deepcopy(environment),
        "savedAt": _now(),
        "actor": actor,
        "reason": reason,
        "recoveredFrom": deepcopy(recovered_from),
        "revisionHash": "",
        "revisionRef": "",
    }
    rh = _revision_hash(record)
    record["revisionHash"] = rh
    record["revisionRef"] = f"sc://workbench/research-environment/{key}/revision/{revision}/{rh}"
    _atomic_json_write(_revision_path(key, revision), record)
    return record


class SaveEnvironmentRequest(BaseModel):
    researchEnvironment: Dict[str, Any]
    expectedCurrentRevision: Optional[int] = Field(default=None, ge=0)
    actor: str = Field(default="workbench", min_length=1, max_length=160)
    reason: str = Field(default="save", min_length=1, max_length=500)


class CheckpointRequest(BaseModel):
    environmentKey: str = Field(min_length=1, max_length=160)
    revision: Optional[int] = Field(default=None, ge=1)
    label: str = Field(default="checkpoint", min_length=1, max_length=240)
    note: str = Field(default="", max_length=2000)
    actor: str = Field(default="workbench", min_length=1, max_length=160)


class RecoveryTarget(BaseModel):
    revision: Optional[int] = Field(default=None, ge=1)
    checkpointId: str = Field(default="", max_length=256)

    @model_validator(mode="after")
    def exactly_one(self):
        if bool(self.revision) == bool(self.checkpointId):
            raise ValueError("exactly one of revision or checkpointId is required")
        return self


class RecoveryPlanRequest(BaseModel):
    environmentKey: str = Field(min_length=1, max_length=160)
    target: RecoveryTarget


class RecoveryApplyRequest(BaseModel):
    environmentKey: str = Field(min_length=1, max_length=160)
    target: RecoveryTarget
    expectedCurrentRevision: Optional[int] = Field(default=None, ge=0)
    actor: str = Field(default="workbench", min_length=1, max_length=160)
    reason: str = Field(default="recovery", min_length=1, max_length=500)


def manifest() -> Dict[str, Any]:
    root = _store_root()
    record = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Research Environment Persistence & Recovery",
        "environmentSchema": ENVIRONMENT_SCHEMA,
        "storage": {
            "kind": "atomic-file-store",
            "configuredRoot": str(root),
            "containerPersistentPath": "/data",
            "appendOnlyRevisionHistory": True,
            "immutableCheckpoints": True,
            "optimisticRevisionChecks": True,
        },
        "boundaries": {
            "automaticScientificExecutionAuthorized": False,
            "automaticNotebookReplayAuthorized": False,
            "automaticWorkflowExecutionAuthorized": False,
            "automaticCoreDispatchAuthorized": False,
            "destructiveHistoryRewriteAuthorized": False,
            "recoveryCreatesNewRevision": True,
        },
    }
    record["manifestHash"] = content_hash(record)
    return record


def save_environment(req: SaveEnvironmentRequest) -> Dict[str, Any]:
    key = _ensure_environment(req.researchEnvironment)
    with _environment_lock(key):
        idx = _load_index(key)
        current = int(idx.get("currentRevision") or 0)
        if req.expectedCurrentRevision is not None and req.expectedCurrentRevision != current:
            raise RuntimeError(f"revision conflict: expected {req.expectedCurrentRevision}, current {current}")
        parent_hash = idx.get("currentRevisionHash")
        revision = current + 1
        rec = _write_revision(req.researchEnvironment, revision=revision, parent_revision=current, parent_revision_hash=parent_hash, actor=req.actor, reason=req.reason)
        idx.update({
            "schema": STORE_INDEX_SCHEMA,
            "version": VERSION,
            "environmentKey": key,
            "currentRevision": revision,
            "currentRevisionHash": rec["revisionHash"],
            "revisionCount": revision,
            "updatedAt": rec["savedAt"],
        })
        _atomic_json_write(_index_path(key), idx)
        _atomic_json_write(_env_dir(key) / "current.json", rec)
        return {**rec, "persistence": {"stored": True, "atomicWrite": True, "currentRevision": revision}}


def load_environment(environment_key: str, revision: Optional[int] = None) -> Dict[str, Any]:
    with _environment_lock(environment_key):
        idx = _load_index(environment_key)
        target = revision or int(idx.get("currentRevision") or 0)
        if target < 1:
            raise FileNotFoundError(f"environment {environment_key} has no saved revisions")
        rec = _load_revision(environment_key, target)
        return {
            "ok": True,
            "schema": SCHEMA,
            "version": VERSION,
            "environmentKey": environment_key,
            "requestedRevision": revision,
            "currentRevision": int(idx.get("currentRevision") or 0),
            "revision": rec,
            "researchEnvironment": rec["researchEnvironment"],
        }


def list_revisions(environment_key: str) -> Dict[str, Any]:
    with _environment_lock(environment_key):
        idx = _load_index(environment_key)
        current = int(idx.get("currentRevision") or 0)
        records: List[Dict[str, Any]] = []
        for rev in range(max(1, current - MAX_REVISIONS_RETURNED + 1), current + 1):
            rec = _load_revision(environment_key, rev)
            records.append({k: rec.get(k) for k in ("revision", "revisionRef", "revisionHash", "parentRevision", "parentRevisionHash", "environmentHash", "savedAt", "actor", "reason", "recoveredFrom")})
        return {"ok": True, "schema": SCHEMA, "version": VERSION, "environmentKey": environment_key, "currentRevision": current, "revisionCount": int(idx.get("revisionCount") or current), "revisions": records}


def _checkpoint_index_path(environment_key: str) -> Path:
    return _env_dir(environment_key) / "checkpoints" / "index.json"


def _load_checkpoint_index(environment_key: str) -> Dict[str, Any]:
    p = _checkpoint_index_path(environment_key)
    if not p.exists():
        return {"schema": CHECKPOINT_SCHEMA, "version": VERSION, "environmentKey": environment_key, "checkpointIds": []}
    return _json_read(p)


def create_checkpoint(req: CheckpointRequest) -> Dict[str, Any]:
    with _environment_lock(req.environmentKey):
        idx = _load_index(req.environmentKey)
        rev = req.revision or int(idx.get("currentRevision") or 0)
        if rev < 1:
            raise FileNotFoundError("no saved revision exists to checkpoint")
        target = _load_revision(req.environmentKey, rev)
        record: Dict[str, Any] = {
            "ok": True,
            "schema": CHECKPOINT_SCHEMA,
            "version": VERSION,
            "environmentKey": req.environmentKey,
            "revision": rev,
            "revisionHash": target["revisionHash"],
            "environmentHash": target["environmentHash"],
            "label": req.label,
            "note": req.note,
            "actor": req.actor,
            "createdAt": _now(),
            "checkpointId": "",
            "checkpointHash": "",
        }
        basis = deepcopy(record); basis.pop("checkpointId", None); basis.pop("checkpointHash", None)
        ch = content_hash(basis)
        cid = f"cp-{rev}-{ch[:20]}"
        record["checkpointHash"] = ch; record["checkpointId"] = cid
        cp_path = _env_dir(req.environmentKey) / "checkpoints" / f"{cid}.json"
        if not cp_path.exists():
            _atomic_json_write(cp_path, record)
        cpidx = _load_checkpoint_index(req.environmentKey)
        ids = list(cpidx.get("checkpointIds", []))
        if cid not in ids:
            ids.append(cid)
        cpidx.update({"checkpointIds": ids[-MAX_CHECKPOINTS_RETURNED:], "updatedAt": record["createdAt"]})
        _atomic_json_write(_checkpoint_index_path(req.environmentKey), cpidx)
        idx["checkpointCount"] = len(ids)
        idx["updatedAt"] = record["createdAt"]
        _atomic_json_write(_index_path(req.environmentKey), idx)
        return record


def _load_checkpoint(environment_key: str, checkpoint_id: str) -> Dict[str, Any]:
    if not checkpoint_id.startswith("cp-") or "/" in checkpoint_id or ".." in checkpoint_id:
        raise ValueError("invalid checkpointId")
    p = _env_dir(environment_key) / "checkpoints" / f"{checkpoint_id}.json"
    if not p.exists():
        raise FileNotFoundError(f"checkpoint {checkpoint_id} not found")
    rec = _json_read(p)
    basis = deepcopy(rec); given = basis.pop("checkpointHash", ""); basis.pop("checkpointId", None)
    if not given or given != content_hash(basis):
        raise ValueError("checkpoint integrity validation failed")
    return rec


def list_checkpoints(environment_key: str) -> Dict[str, Any]:
    with _environment_lock(environment_key):
        cpidx = _load_checkpoint_index(environment_key)
        cps = [_load_checkpoint(environment_key, cid) for cid in cpidx.get("checkpointIds", [])[-MAX_CHECKPOINTS_RETURNED:]]
        return {"ok": True, "schema": CHECKPOINT_SCHEMA, "version": VERSION, "environmentKey": environment_key, "checkpointCount": len(cps), "checkpoints": cps}


def _resolve_target(environment_key: str, target: RecoveryTarget) -> tuple[Dict[str, Any], Dict[str, Any]]:
    if target.revision:
        rev = _load_revision(environment_key, target.revision)
        return rev, {"kind": "revision", "revision": target.revision, "revisionHash": rev["revisionHash"]}
    cp = _load_checkpoint(environment_key, target.checkpointId)
    rev = _load_revision(environment_key, int(cp["revision"]))
    if rev["revisionHash"] != cp["revisionHash"]:
        raise ValueError("checkpoint revision hash no longer matches stored revision")
    return rev, {"kind": "checkpoint", "checkpointId": cp["checkpointId"], "checkpointHash": cp["checkpointHash"], "revision": cp["revision"], "revisionHash": cp["revisionHash"]}


def recovery_plan(req: RecoveryPlanRequest) -> Dict[str, Any]:
    with _environment_lock(req.environmentKey):
        idx = _load_index(req.environmentKey)
        current = int(idx.get("currentRevision") or 0)
        if current < 1:
            raise FileNotFoundError("no saved environment exists to recover")
        target_rev, source = _resolve_target(req.environmentKey, req.target)
        plan = {
            "ok": True,
            "schema": RECOVERY_PLAN_SCHEMA,
            "version": VERSION,
            "environmentKey": req.environmentKey,
            "currentRevision": current,
            "currentRevisionHash": idx.get("currentRevisionHash"),
            "target": source,
            "targetEnvironmentHash": target_rev["environmentHash"],
            "targetEnvironmentValid": True,
            "recoveryCreatesNewRevision": True,
            "destructiveRollbackPerformed": False,
            "scientificExecutionPerformed": False,
            "automaticReplayAuthorized": False,
        }
        plan["planHash"] = content_hash(plan)
        return plan


def apply_recovery(req: RecoveryApplyRequest) -> Dict[str, Any]:
    with _environment_lock(req.environmentKey):
        idx = _load_index(req.environmentKey)
        current = int(idx.get("currentRevision") or 0)
        if req.expectedCurrentRevision is not None and req.expectedCurrentRevision != current:
            raise RuntimeError(f"revision conflict: expected {req.expectedCurrentRevision}, current {current}")
        target_rev, source = _resolve_target(req.environmentKey, req.target)
        new_rev = current + 1
        rec = _write_revision(
            target_rev["researchEnvironment"], revision=new_rev, parent_revision=current,
            parent_revision_hash=idx.get("currentRevisionHash"), actor=req.actor, reason=req.reason,
            recovered_from=source,
        )
        idx.update({"version": VERSION, "currentRevision": new_rev, "currentRevisionHash": rec["revisionHash"], "revisionCount": new_rev, "updatedAt": rec["savedAt"]})
        _atomic_json_write(_index_path(req.environmentKey), idx)
        _atomic_json_write(_env_dir(req.environmentKey) / "current.json", rec)
        result = {
            "ok": True,
            "schema": RECOVERY_RESULT_SCHEMA,
            "version": VERSION,
            "environmentKey": req.environmentKey,
            "previousRevision": current,
            "newRevision": new_rev,
            "newRevisionHash": rec["revisionHash"],
            "recoveredFrom": source,
            "researchEnvironment": rec["researchEnvironment"],
            "destructiveRollbackPerformed": False,
            "scientificExecutionPerformed": False,
            "automaticReplayAuthorized": False,
        }
        result["recoveryResultHash"] = content_hash(result)
        return result


@router.get("/research-environment/persistence/manifest")
def manifest_endpoint():
    return manifest()


@router.post("/research-environment/persistence/save")
def save_endpoint(req: SaveEnvironmentRequest):
    try:
        return save_environment(req)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/research-environment/persistence/{environment_key}")
def load_endpoint(environment_key: str, revision: Optional[int] = None):
    try:
        return load_environment(environment_key, revision)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/research-environment/persistence/{environment_key}/revisions")
def revisions_endpoint(environment_key: str):
    try:
        return list_revisions(environment_key)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/research-environment/checkpoints/create")
def checkpoint_endpoint(req: CheckpointRequest):
    try:
        return create_checkpoint(req)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/research-environment/checkpoints/{environment_key}")
def checkpoints_endpoint(environment_key: str):
    try:
        return list_checkpoints(environment_key)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/research-environment/recovery/plan")
def recovery_plan_endpoint(req: RecoveryPlanRequest):
    try:
        return recovery_plan(req)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/research-environment/recovery/apply")
def recovery_apply_endpoint(req: RecoveryApplyRequest):
    try:
        return apply_recovery(req)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/v810/status")
def status():
    return {
        "ok": True,
        "version": VERSION,
        "release": "Research Environment Persistence & Recovery",
        "schema": SCHEMA,
        "environmentSchema": ENVIRONMENT_SCHEMA,
        "atomicFilePersistence": True,
        "appendOnlyRevisionHistory": True,
        "immutableCheckpoints": True,
        "optimisticRevisionChecks": True,
        "recoveryCreatesNewRevision": True,
        "destructiveHistoryRewriteAuthorized": False,
        "automaticScientificExecutionAuthorized": False,
        "automaticNotebookReplayAuthorized": False,
        "automaticWorkflowExecutionAuthorized": False,
        "automaticCoreDispatchAuthorized": False,
        "storeRoot": str(_store_root()),
    }
