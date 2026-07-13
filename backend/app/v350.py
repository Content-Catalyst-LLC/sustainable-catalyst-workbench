from __future__ import annotations

from datetime import datetime, timezone, timedelta
from hashlib import sha256
import json
import re
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

VERSION = "3.5.0"
DEVICE_SCHEMA = "sc-workbench-device-record/1.0"
CAPABILITY_SCHEMA = "sc-workbench-device-capabilities/1.0"
CONSENT_SCHEMA = "sc-workbench-device-consent/1.0"
SESSION_SCHEMA = "sc-workbench-instrument-session/1.0"
CALIBRATION_SCHEMA = "sc-workbench-calibration-schedule/1.0"
RUN_SCHEMA = "sc-workbench-device-run/1.0"
LOG_SCHEMA = "sc-workbench-device-log/1.0"
RECOVERY_SCHEMA = "sc-workbench-device-recovery/1.0"
SIMULATION_SCHEMA = "sc-workbench-hardware-simulation/1.0"

router = APIRouter(prefix="/v350", tags=["workbench-v350"])

SAFE_OPERATIONS = {"discover", "read", "acquire", "calibrate", "simulate", "validate", "upload", "flash", "write", "reset", "power-cycle"}
SENSITIVE_OPERATIONS = {"upload", "flash", "write", "reset", "power-cycle"}
BLOCKED_OPERATIONS = {"shell", "exec", "arbitrary-command", "remote-shell", "disable-safety"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _hash(value: Any) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def _slug(value: Any, fallback: str = "record") -> str:
    text = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return text[:120] or fallback


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class DeviceRecord(BaseModel):
    device_id: str = ""
    name: str = "Device"
    device_type: Literal["microcontroller", "single-board-computer", "fpga", "instrument", "sensor", "actuator", "gateway", "simulator", "other"] = "other"
    transport: Literal["usb", "serial", "network", "bluetooth", "gpio", "i2c", "spi", "virtual", "manual", "unknown"] = "unknown"
    address: str = ""
    vendor: str = ""
    model: str = ""
    firmware: str = ""
    capabilities: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    status: Literal["available", "busy", "offline", "maintenance", "unknown", "simulated"] = "unknown"
    calibration_due_at: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class CapabilityDiscoveryRequest(BaseModel):
    device: DeviceRecord
    observed_interfaces: list[str] = Field(default_factory=list)
    observed_commands: list[str] = Field(default_factory=list)
    simulation_allowed: bool = True


class ConsentRequest(BaseModel):
    project_id: str = "default"
    actor_id: str = "local-user"
    device_ids: list[str] = Field(default_factory=list)
    allowed_operations: list[str] = Field(default_factory=lambda: ["discover", "read", "acquire", "calibrate", "simulate", "validate"])
    expires_at: str = ""
    confirmation_phrase: str = ""
    local_only: bool = True


class DeviceTask(BaseModel):
    task_id: str = ""
    device_id: str
    operation: str
    capability: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    expected_duration_seconds: float = 0
    rollback: dict[str, Any] = Field(default_factory=dict)
    requires_calibration: bool = False


class SessionRequest(BaseModel):
    project_id: str = "default"
    session_id: str = ""
    title: str = "Instrument session"
    operator_id: str = "local-user"
    devices: list[DeviceRecord] = Field(default_factory=list)
    consent: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""


class CalibrationRequest(BaseModel):
    devices: list[DeviceRecord] = Field(default_factory=list)
    default_interval_days: int = 180
    warning_days: int = 30
    as_of: str = ""


class RunPlanRequest(BaseModel):
    project_id: str = "default"
    run_id: str = ""
    title: str = "Device run"
    devices: list[DeviceRecord] = Field(default_factory=list)
    tasks: list[DeviceTask] = Field(default_factory=list)
    consent: dict[str, Any] = Field(default_factory=dict)
    simulation_mode: bool = False
    stop_on_error: bool = True


class LogRequest(BaseModel):
    run_id: str
    device_id: str
    level: Literal["debug", "info", "warning", "error", "critical"] = "info"
    event: str
    message: str = ""
    measurements: dict[str, Any] = Field(default_factory=dict)
    previous_log_hash: str = ""


class RecoveryRequest(BaseModel):
    run: dict[str, Any]
    failed_task_id: str = ""
    failure_type: str = "unknown"
    device_states: list[dict[str, Any]] = Field(default_factory=list)


class SimulationRequest(BaseModel):
    device: DeviceRecord
    seed: int = 1
    noise_fraction: float = 0.01
    initial_state: dict[str, Any] = Field(default_factory=dict)


def normalize_device(device: DeviceRecord) -> dict[str, Any]:
    data = device.model_dump()
    data["deviceId"] = _slug(data.pop("device_id") or f"{data.get('vendor')}-{data.get('model')}-{data.get('name')}", "device")
    data["deviceType"] = data.pop("device_type")
    data["calibrationDueAt"] = data.pop("calibration_due_at")
    data["capabilities"] = sorted({_slug(item, "capability") for item in data.get("capabilities", []) if str(item).strip()})
    data["tags"] = sorted({_slug(item, "tag") for item in data.get("tags", []) if str(item).strip()})
    data["address"] = str(data.get("address", "")).strip()[:500]
    data["schema"] = DEVICE_SCHEMA
    data["version"] = VERSION
    data["updatedAt"] = _now()
    data["deviceHash"] = _hash({k: v for k, v in data.items() if k != "deviceHash"})
    return data


def discover_capabilities(request: CapabilityDiscoveryRequest) -> dict[str, Any]:
    device = normalize_device(request.device)
    interfaces = sorted({_slug(item, "interface") for item in request.observed_interfaces if str(item).strip()})
    observed = sorted({_slug(item, "operation") for item in request.observed_commands if str(item).strip()})
    blocked = sorted(set(observed) & BLOCKED_OPERATIONS)
    operations = sorted((set(observed) & SAFE_OPERATIONS) | {"discover", "read"})
    capabilities = sorted(set(device["capabilities"]) | set(interfaces))
    result = {
        "schema": CAPABILITY_SCHEMA,
        "version": VERSION,
        "deviceId": device["deviceId"],
        "interfaces": interfaces,
        "capabilities": capabilities,
        "allowedOperations": operations,
        "blockedOperations": blocked,
        "simulationAvailable": bool(request.simulation_allowed),
        "arbitraryCommandExecution": False,
        "discoveredAt": _now(),
    }
    result["capabilityHash"] = _hash(result)
    return {"ok": True, "capabilities": result, "capabilityHash": result["capabilityHash"]}


def build_consent_policy(request: ConsentRequest) -> dict[str, Any]:
    operations = {_slug(item, "operation") for item in request.allowed_operations if str(item).strip()}
    blocked = sorted(operations & BLOCKED_OPERATIONS)
    if blocked:
        raise ValueError("blocked operations may not be granted: " + ", ".join(blocked))
    unsupported = sorted(operations - SAFE_OPERATIONS)
    if unsupported:
        raise ValueError("unsupported operations: " + ", ".join(unsupported))
    sensitive = sorted(operations & SENSITIVE_OPERATIONS)
    if sensitive and request.confirmation_phrase.strip() != "AUTHORIZE LOCAL DEVICE CONTROL":
        raise ValueError("sensitive device operations require the confirmation phrase AUTHORIZE LOCAL DEVICE CONTROL")
    expires = _parse_time(request.expires_at)
    if expires is None:
        expires = datetime.now(timezone.utc) + timedelta(hours=8)
    if expires <= datetime.now(timezone.utc):
        raise ValueError("consent expiration must be in the future")
    record = {
        "schema": CONSENT_SCHEMA,
        "version": VERSION,
        "projectId": _slug(request.project_id, "default"),
        "actorId": _slug(request.actor_id, "local-user"),
        "deviceIds": sorted({_slug(item, "device") for item in request.device_ids if str(item).strip()}),
        "allowedOperations": sorted(operations),
        "sensitiveOperations": sensitive,
        "localOnly": bool(request.local_only),
        "arbitraryCommandExecution": False,
        "issuedAt": _now(),
        "expiresAt": expires.isoformat(),
    }
    record["consentHash"] = _hash(record)
    return {"ok": True, "consent": record, "consentHash": record["consentHash"]}


def _validate_consent(consent: dict[str, Any], tasks: list[DeviceTask]) -> list[str]:
    issues: list[str] = []
    allowed = set(consent.get("allowedOperations", []))
    devices = set(consent.get("deviceIds", []))
    expires = _parse_time(str(consent.get("expiresAt", "")))
    if expires is None or expires <= datetime.now(timezone.utc):
        issues.append("consent is missing or expired")
    for task in tasks:
        operation = _slug(task.operation, "operation")
        device_id = _slug(task.device_id, "device")
        if operation in BLOCKED_OPERATIONS:
            issues.append(f"{task.task_id or operation}: blocked operation")
        elif operation not in SAFE_OPERATIONS:
            issues.append(f"{task.task_id or operation}: unsupported operation")
        elif operation not in allowed:
            issues.append(f"{task.task_id or operation}: operation not allowed by consent")
        if devices and device_id not in devices:
            issues.append(f"{task.task_id or operation}: device not allowed by consent")
    return sorted(set(issues))


def build_session(request: SessionRequest) -> dict[str, Any]:
    devices = [normalize_device(item) for item in request.devices]
    record = {
        "schema": SESSION_SCHEMA,
        "version": VERSION,
        "sessionId": _slug(request.session_id or f"{request.project_id}-{request.title}-{_now()}", "session"),
        "projectId": _slug(request.project_id, "default"),
        "title": request.title.strip()[:300],
        "operatorId": _slug(request.operator_id, "local-user"),
        "devices": devices,
        "deviceIds": [item["deviceId"] for item in devices],
        "consentHash": str(request.consent.get("consentHash", "")),
        "notes": request.notes.strip()[:4000],
        "state": "planned",
        "startedAt": "",
        "endedAt": "",
        "createdAt": _now(),
    }
    record["sessionHash"] = _hash(record)
    return {"ok": True, "session": record, "sessionHash": record["sessionHash"]}


def build_calibration_schedule(request: CalibrationRequest) -> dict[str, Any]:
    if request.default_interval_days < 1 or request.warning_days < 0:
        raise ValueError("calibration intervals must be positive")
    as_of = _parse_time(request.as_of) or datetime.now(timezone.utc)
    rows = []
    for raw in request.devices:
        device = normalize_device(raw)
        due = _parse_time(device.get("calibrationDueAt"))
        if due is None:
            due = as_of + timedelta(days=request.default_interval_days)
            source = "default-interval"
        else:
            source = "device-record"
        remaining = int((due - as_of).total_seconds() // 86400)
        if remaining < 0:
            state = "overdue"
        elif remaining <= request.warning_days:
            state = "due-soon"
        else:
            state = "current"
        rows.append({"deviceId": device["deviceId"], "name": device["name"], "dueAt": due.isoformat(), "daysRemaining": remaining, "state": state, "source": source})
    order = {"overdue": 0, "due-soon": 1, "current": 2}
    rows.sort(key=lambda item: (order[item["state"]], item["dueAt"], item["deviceId"]))
    result = {"schema": CALIBRATION_SCHEMA, "version": VERSION, "asOf": as_of.isoformat(), "devices": rows, "counts": {state: sum(1 for row in rows if row["state"] == state) for state in order}}
    result["scheduleHash"] = _hash(result)
    return {"ok": True, "schedule": result, "scheduleHash": result["scheduleHash"]}


def build_run_plan(request: RunPlanRequest) -> dict[str, Any]:
    devices = [normalize_device(item) for item in request.devices]
    device_map = {item["deviceId"]: item for item in devices}
    issues = _validate_consent(request.consent, request.tasks)
    normalized_tasks = []
    previous = ""
    for index, task in enumerate(request.tasks):
        operation = _slug(task.operation, "operation")
        device_id = _slug(task.device_id, "device")
        task_id = _slug(task.task_id or f"task-{index + 1}-{device_id}-{operation}", "task")
        device = device_map.get(device_id)
        if device is None and not request.simulation_mode:
            issues.append(f"{task_id}: device is not in the run inventory")
        if device and device.get("status") == "offline" and not request.simulation_mode:
            issues.append(f"{task_id}: device is offline")
        record = {
            "taskId": task_id,
            "sequence": index + 1,
            "deviceId": device_id,
            "operation": operation,
            "capability": _slug(task.capability, "") if task.capability else "",
            "parameters": task.parameters,
            "expectedDurationSeconds": max(0.0, float(task.expected_duration_seconds)),
            "rollback": task.rollback,
            "requiresCalibration": bool(task.requires_calibration),
            "previousTaskHash": previous,
        }
        record["taskHash"] = _hash(record)
        previous = record["taskHash"]
        normalized_tasks.append(record)
    issues = sorted(set(issues))
    run = {
        "schema": RUN_SCHEMA,
        "version": VERSION,
        "runId": _slug(request.run_id or f"{request.project_id}-{request.title}-{_now()}", "run"),
        "projectId": _slug(request.project_id, "default"),
        "title": request.title.strip()[:300],
        "devices": devices,
        "tasks": normalized_tasks,
        "consentHash": str(request.consent.get("consentHash", "")),
        "simulationMode": bool(request.simulation_mode),
        "stopOnError": bool(request.stop_on_error),
        "state": "blocked" if issues else "ready",
        "issues": issues,
        "arbitraryCommandExecution": False,
        "createdAt": _now(),
    }
    run["runHash"] = _hash(run)
    return {"ok": not issues, "run": run, "runHash": run["runHash"], "issues": issues}


def build_device_log(request: LogRequest) -> dict[str, Any]:
    record = {
        "schema": LOG_SCHEMA,
        "version": VERSION,
        "runId": _slug(request.run_id, "run"),
        "deviceId": _slug(request.device_id, "device"),
        "level": request.level,
        "event": _slug(request.event, "event"),
        "message": request.message.strip()[:4000],
        "measurements": request.measurements,
        "previousLogHash": request.previous_log_hash,
        "timestamp": _now(),
    }
    record["logHash"] = _hash(record)
    return {"ok": True, "log": record, "logHash": record["logHash"]}


def build_recovery_plan(request: RecoveryRequest) -> dict[str, Any]:
    run = request.run or {}
    tasks = run.get("tasks", []) or []
    failed = request.failed_task_id
    completed = []
    rollback_steps = []
    for task in tasks:
        task_id = str(task.get("taskId", ""))
        if task_id == failed:
            break
        completed.append(task_id)
    for task in reversed(tasks):
        task_id = str(task.get("taskId", ""))
        if task_id not in completed:
            continue
        rollback = task.get("rollback") or {}
        if rollback:
            rollback_steps.append({"taskId": task_id, "deviceId": task.get("deviceId", ""), "rollback": rollback, "requiresConsent": True})
    plan = {
        "schema": RECOVERY_SCHEMA,
        "version": VERSION,
        "runId": run.get("runId", ""),
        "failedTaskId": failed,
        "failureType": _slug(request.failure_type, "unknown"),
        "completedTaskIds": completed,
        "rollbackSteps": rollback_steps,
        "deviceStates": request.device_states,
        "requiresFreshConsent": bool(rollback_steps),
        "recommendedState": "manual-review" if request.failure_type in {"safety", "hardware-damage", "unknown"} else "rollback-ready",
        "createdAt": _now(),
    }
    plan["recoveryHash"] = _hash(plan)
    return {"ok": True, "recovery": plan, "recoveryHash": plan["recoveryHash"]}


def build_simulation_twin(request: SimulationRequest) -> dict[str, Any]:
    device = normalize_device(request.device)
    twin = {
        "schema": SIMULATION_SCHEMA,
        "version": VERSION,
        "simulationId": _slug(f"simulation-{device['deviceId']}-{request.seed}", "simulation"),
        "sourceDeviceId": device["deviceId"],
        "device": {**device, "status": "simulated", "transport": "virtual"},
        "seed": int(request.seed),
        "noiseFraction": max(0.0, min(float(request.noise_fraction), 1.0)),
        "state": request.initial_state,
        "hardwarePresent": False,
        "clearlyLabeledSimulation": True,
        "createdAt": _now(),
    }
    twin["simulationHash"] = _hash(twin)
    return {"ok": True, "simulation": twin, "simulationHash": twin["simulationHash"]}


@router.get("/status")
def status() -> dict[str, Any]:
    return {"ok": True, "version": VERSION, "schemas": [DEVICE_SCHEMA, CAPABILITY_SCHEMA, CONSENT_SCHEMA, SESSION_SCHEMA, CALIBRATION_SCHEMA, RUN_SCHEMA, LOG_SCHEMA, RECOVERY_SCHEMA, SIMULATION_SCHEMA], "arbitraryCommandExecution": False}


@router.post("/device/normalize")
def api_device(request: DeviceRecord):
    return {"ok": True, "device": normalize_device(request)}


@router.post("/capabilities/discover")
def api_capabilities(request: CapabilityDiscoveryRequest):
    return discover_capabilities(request)


@router.post("/consent/build")
def api_consent(request: ConsentRequest):
    try:
        return build_consent_policy(request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/session/build")
def api_session(request: SessionRequest):
    return build_session(request)


@router.post("/calibration/schedule")
def api_calibration(request: CalibrationRequest):
    try:
        return build_calibration_schedule(request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/run/plan")
def api_run(request: RunPlanRequest):
    return build_run_plan(request)


@router.post("/log/build")
def api_log(request: LogRequest):
    return build_device_log(request)


@router.post("/recovery/plan")
def api_recovery(request: RecoveryRequest):
    return build_recovery_plan(request)


@router.post("/simulation/build")
def api_simulation(request: SimulationRequest):
    return build_simulation_twin(request)
