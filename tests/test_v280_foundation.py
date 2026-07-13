from backend.app.v280 import (
    CheckpointRequest,
    CheckpointRule,
    ProtocolRequest,
    ProtocolStep,
    ReproMetric,
    ReproducibilityRequest,
    ScheduleRequest,
    ScheduleTask,
    VersionManifestRequest,
    WorkflowRequest,
    WorkflowTask,
    compare_reproducibility,
    evaluate_checkpoint,
    evaluate_schedule,
    plan_workflow,
    validate_protocol,
    version_manifest,
)


def test_protocol_validation_orders_steps_and_hashes():
    result = validate_protocol(ProtocolRequest(steps=[
        ProtocolStep(id="prepare", title="Prepare", procedure="Prepare sample", outputs=["sample"], checkpoint="Mass recorded"),
        ProtocolStep(id="measure", title="Measure", procedure="Acquire data", dependencies=["prepare"], outputs=["dataset"], checkpoint="Signal valid"),
    ]))
    assert result["ok"] is True
    assert result["topologicalOrder"] == ["prepare", "measure"]
    assert len(result["protocolHash"]) == 64


def test_protocol_detects_cycle():
    result = validate_protocol(ProtocolRequest(steps=[
        ProtocolStep(id="a", title="A", dependencies=["b"]),
        ProtocolStep(id="b", title="B", dependencies=["a"]),
    ]))
    assert result["ok"] is False
    assert any(item["code"] == "dependency-cycle" for item in result["findings"])


def test_workflow_critical_path():
    result = plan_workflow(WorkflowRequest(tasks=[
        WorkflowTask(id="a", title="Acquire", duration_minutes=10),
        WorkflowTask(id="b", title="Analyze", duration_minutes=20, dependencies=["a"]),
        WorkflowTask(id="c", title="Document", duration_minutes=5, dependencies=["b"]),
    ]))
    assert result["ok"] is True
    assert result["estimatedCriticalPathMinutes"] == 35


def test_schedule_conflict_detection():
    result = evaluate_schedule(ScheduleRequest(tasks=[
        ScheduleTask(id="a", start_minute=0, duration_minutes=20, resource="sensor"),
        ScheduleTask(id="b", start_minute=10, duration_minutes=20, resource="sensor"),
    ]))
    assert result["ok"] is False
    assert any(item["code"] == "resource-conflict" for item in result["findings"])


def test_manifest_is_deterministic():
    request = VersionManifestRequest(dataset={"b": 2, "a": 1}, configuration={"gain": 4}, code_revision="abc")
    first = version_manifest(request)
    second = version_manifest(request)
    assert first["manifestHash"] == second["manifestHash"]
    assert len(first["datasetHash"]) == 64


def test_checkpoint_rules():
    result = evaluate_checkpoint(CheckpointRequest(observed={"temperature": 21.0, "status": "ready"}, rules=[
        CheckpointRule(key="temperature", operator="between", lower=20, upper=22),
        CheckpointRule(key="status", operator="equal", expected="ready"),
    ]))
    assert result["ok"] is True
    assert result["counts"]["pass"] == 2


def test_reproducibility_comparison():
    result = compare_reproducibility(ReproducibilityRequest(
        run_ids=["r1", "r2", "r3"],
        dataset_hashes=["d", "d", "d"],
        configuration_hashes=["c", "c", "c"],
        code_revisions=["g", "g", "g"],
        metrics=[ReproMetric(key="rmse", values=[1.0, 1.001, 0.999], absolute_tolerance=0.01)],
    ))
    assert result["ok"] is True
    assert result["metricFailures"] == 0
