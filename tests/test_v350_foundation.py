from datetime import datetime, timezone, timedelta
from app.v350 import (
    DeviceRecord, CapabilityDiscoveryRequest, ConsentRequest, DeviceTask,
    SessionRequest, CalibrationRequest, RunPlanRequest, LogRequest,
    RecoveryRequest, SimulationRequest, normalize_device, discover_capabilities,
    build_consent_policy, build_session, build_calibration_schedule,
    build_run_plan, build_device_log, build_recovery_plan, build_simulation_twin,
)


def device(status="available"):
    return DeviceRecord(device_id="scope-1", name="Bench Scope", device_type="instrument", transport="usb", capabilities=["read", "acquire", "calibrate"], status=status)


def consent(*ops):
    return build_consent_policy(ConsentRequest(device_ids=["scope-1"], allowed_operations=list(ops or ("discover", "read", "acquire", "calibrate")), expires_at=(datetime.now(timezone.utc)+timedelta(hours=2)).isoformat()))["consent"]


def test_device_normalization_is_stable_and_hashed():
    result = normalize_device(device())
    assert result["deviceId"] == "scope-1"
    assert result["deviceHash"]
    assert result["schema"] == "sc-workbench-device-record/1.0"


def test_capability_discovery_blocks_arbitrary_shell_markers():
    result = discover_capabilities(CapabilityDiscoveryRequest(device=device(), observed_interfaces=["USB-TMC"], observed_commands=["read", "shell"]))["capabilities"]
    assert "shell" in result["blockedOperations"]
    assert result["arbitraryCommandExecution"] is False


def test_sensitive_consent_requires_confirmation_phrase():
    try:
        build_consent_policy(ConsentRequest(device_ids=["scope-1"], allowed_operations=["read", "flash"]))
    except ValueError as error:
        assert "confirmation phrase" in str(error)
    else:
        raise AssertionError("sensitive consent safeguard was not enforced")


def test_blocked_consent_operation_is_rejected():
    try:
        build_consent_policy(ConsentRequest(device_ids=["scope-1"], allowed_operations=["shell"]))
    except ValueError as error:
        assert "blocked operations" in str(error)
    else:
        raise AssertionError("blocked operation was accepted")


def test_run_plan_validates_consent_and_inventory():
    result = build_run_plan(RunPlanRequest(project_id="p1", devices=[device()], tasks=[DeviceTask(device_id="scope-1", operation="acquire")], consent=consent("acquire")))
    assert result["ok"] is True
    assert result["run"]["state"] == "ready"
    assert result["run"]["arbitraryCommandExecution"] is False


def test_run_plan_blocks_unapproved_operation():
    result = build_run_plan(RunPlanRequest(devices=[device()], tasks=[DeviceTask(device_id="scope-1", operation="write")], consent=consent("read")))
    assert result["ok"] is False
    assert "operation not allowed by consent" in result["issues"][0]


def test_calibration_schedule_prioritizes_overdue_device():
    old = (datetime.now(timezone.utc)-timedelta(days=3)).isoformat()
    current = (datetime.now(timezone.utc)+timedelta(days=90)).isoformat()
    result = build_calibration_schedule(CalibrationRequest(devices=[DeviceRecord(device_id="a", calibration_due_at=current), DeviceRecord(device_id="b", calibration_due_at=old)]))["schedule"]
    assert result["devices"][0]["deviceId"] == "b"
    assert result["counts"]["overdue"] == 1


def test_chained_log_and_recovery_plan_preserve_traceability():
    first = build_device_log(LogRequest(run_id="run-1", device_id="scope-1", event="start"))["log"]
    second = build_device_log(LogRequest(run_id="run-1", device_id="scope-1", event="fail", previous_log_hash=first["logHash"]))["log"]
    assert second["previousLogHash"] == first["logHash"]
    run = build_run_plan(RunPlanRequest(run_id="run-1", devices=[device()], tasks=[DeviceTask(task_id="t1", device_id="scope-1", operation="acquire", rollback={"operation":"reset"}), DeviceTask(task_id="t2", device_id="scope-1", operation="validate")], consent=consent("acquire", "validate")))["run"]
    recovery = build_recovery_plan(RecoveryRequest(run=run, failed_task_id="t2", failure_type="communication"))["recovery"]
    assert recovery["rollbackSteps"][0]["taskId"] == "t1"
    assert recovery["requiresFreshConsent"] is True


def test_simulation_twin_is_explicitly_not_hardware():
    result = build_simulation_twin(SimulationRequest(device=device(status="offline"), seed=7))["simulation"]
    assert result["hardwarePresent"] is False
    assert result["clearlyLabeledSimulation"] is True
    assert result["device"]["status"] == "simulated"
