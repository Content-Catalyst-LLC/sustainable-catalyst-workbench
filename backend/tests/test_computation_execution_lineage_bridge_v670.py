from fastapi.testclient import TestClient

from app.main import app
from app.v670 import (
    CORE_COMPUTATION_LINEAGE_CONTRACT,
    AssumptionItem,
    CoreLineageBundleConsumeRequest,
    DependencyItem,
    EnvironmentItem,
    ExecutionComponentsRequest,
    ExecutionCreateRequest,
    ExecutionLifecycleRequest,
    InputItem,
    OutputItem,
    ParameterItem,
    ResearchBindingItem,
    SessionExecutionBindingBuildRequest,
    StepItem,
    VerificationItem,
    build_components,
    build_execution_create,
    build_lifecycle,
    build_session_execution_binding,
    consume_core_lineage_bundle,
    lineage_manifest,
)


def client():
    return TestClient(app)


def test_manifest_targets_exact_core_287_contract_and_boundary():
    m = lineage_manifest()
    assert m["version"] == "7.0.0"
    assert m["coreComputationLineageContract"] == "sc.research.computation-analysis-execution-lineage.v1"
    assert m["corePaths"]["executions"] == "/v1/research/computation-lineage/executions"
    assert m["corePaths"]["unifiedSessionExecutionBindings"] == "/v1/research/unified-runtime/execution-bindings"
    assert m["boundaries"]["coreExecutionIdMustComeFromCore"] is True
    assert m["boundaries"]["coreExecutesWorkbenchCode"] is False
    assert m["boundaries"]["coreDeterminesTruth"] is False


def test_execution_registration_matches_core_shape_and_preserves_workbench_ref():
    x = build_execution_create(ExecutionCreateRequest(
        executionKey="eng-001",
        title="Engineering calculation",
        executionType="engineering_calculation",
        projectRef="project:core:42",
        coreSessionId="session:1",
        codeRef="git:abc123",
        sourceRevision="abc123",
    ))
    d = x["executionDraft"]
    assert x["phase"] == "prepare-core-execution"
    assert d["execution_key"] == "eng-001"
    assert d["runtime_kind"] == "workbench"
    assert d["project_ref"] == "project:core:42"
    assert d["external_run_ref"] == "sc://workbench/execution/eng-001"
    assert d["metadata"]["coreSessionId"] == "session:1"
    assert d["metadata"]["workbenchExecutionHash"] == x["executionHash"]
    assert x["coreRequest"]["path"] == "/v1/research/computation-lineage/executions"
    assert x["coreRequest"]["payload"] == {"data": d}
    assert x["coreExecutionIdMustComeFromCore"] is True


def test_execution_registration_rejects_unknown_core_enum():
    r = client().post("/integration/core/computation-lineage/executions/build", json={"executionKey":"x","title":"X","executionType":"not-real"})
    assert r.status_code == 422


def sample_components():
    return ExecutionComponentsRequest(
        coreExecutionId="core-exec-1",
        coreSessionId="core-session-1",
        projectRef="project:core:42",
        workbenchExecutionRef="sc://workbench/execution/eng-001",
        environmentRef="sc://workbench/environment/env-1",
        methodRef="method:energy-balance",
        inputs=[InputItem(inputKey="dataset", inputType="dataset", objectRef="dataset:climate-v4", versionRef="v4", contentHash="sha256:111")],
        parameters=[ParameterItem(parameterKey="alpha", value={"number":0.05}, unit="1")],
        assumptions=[AssumptionItem(assumptionKey="steady", statementText="Steady-state assumption declared.", evidenceRefs=["source:1"])],
        environments=[EnvironmentItem(environmentKey="env-1", runtimeVersion="6.12.0", packages=["numpy==2.x"], environmentHash="sha256:env")],
        steps=[
            StepItem(stepKey="solve", sequence=2, stepType="analyze", toolRef="workbench:numerical", inputRefs=["dataset:climate-v4"], outputRefs=["result:2"]),
            StepItem(stepKey="prepare", sequence=1, stepType="prepare", toolRef="workbench:data", outputRefs=["result:1"]),
        ],
        outputs=[OutputItem(outputKey="coef", outputType="statistic", objectRef="result:coef-1", contentHash="sha256:222", metadata={"units":"kg"})],
        researchBindings=[ResearchBindingItem(bindingKey="claim", sourceOutputRef="result:coef-1", targetType="claim", targetRef="claim:42", relation="basis_for")],
        dependencies=[DependencyItem(dependencyKey="upstream", upstreamExecutionRef="core-exec-0", upstreamOutputRef="result:prior")],
        verifications=[VerificationItem(verificationKey="checksum", verificationType="checksum", status="passed", evidence={"hash":"sha256:222"})],
    )


def test_component_plan_covers_all_core_lineage_families_and_orders_steps():
    x = build_components(sample_components())
    assert x["ok"] is True
    assert x["coreExecutionRef"] == "sc://platform-core/computation-lineage/execution/core-exec-1"
    assert x["componentCounts"] == {"inputs":1,"parameters":1,"assumptions":1,"environments":1,"steps":2,"outputs":1,"researchBindings":1,"dependencies":1,"verifications":1}
    assert x["requestCount"] == 10
    paths = [r["path"] for r in x["coreRequests"]]
    for suffix in ("/inputs","/parameters","/assumptions","/environments","/steps","/outputs","/research-bindings","/dependencies","/verifications"):
        assert f"/v1/research/computation-lineage/executions/core-exec-1{suffix}" in paths
    step_requests = [r for r in x["coreRequests"] if r["path"].endswith("/steps")]
    assert [r["data"]["step_key"] for r in step_requests] == ["prepare","solve"]
    assert x["orderedStepsPreserved"] is True
    assert x["contentHashesPreserved"] is True
    assert x["verificationEvidencePreserved"] is True


def test_component_plan_builds_v660_unified_session_execution_binding():
    x = build_components(sample_components())
    b = x["unifiedSessionExecutionBinding"]
    assert b is not None
    assert b["binding"]["session_id"] == "core-session-1"
    assert b["binding"]["execution_ref"] == "sc://platform-core/computation-lineage/execution/core-exec-1"
    assert b["binding"]["input_refs"] == ["dataset:climate-v4"]
    assert b["binding"]["output_refs"] == ["result:coef-1"]
    assert b["coreRequest"]["path"] == "/v1/research/unified-runtime/execution-bindings"


def test_component_plan_without_session_does_not_fabricate_binding():
    r = sample_components().model_copy(update={"coreSessionId":""})
    assert build_components(r)["unifiedSessionExecutionBinding"] is None


def test_component_plan_requires_core_execution_id():
    r = client().post("/integration/core/computation-lineage/executions/components/build", json={"coreExecutionId":""})
    assert r.status_code == 422


def test_explicit_session_binding_builder_uses_core_execution_ref():
    x = build_session_execution_binding(SessionExecutionBindingBuildRequest(coreExecutionId="e-2", coreSessionId="s-2", inputRefs=["in:1"], outputRefs=["out:1"]))
    assert x["binding"]["execution_ref"] == "sc://platform-core/computation-lineage/execution/e-2"
    assert x["binding"]["session_id"] == "s-2"
    assert x["binding"]["runtime"] == "workbench"


def test_lifecycle_build_creates_revision_then_snapshot_requests():
    x = build_lifecycle(ExecutionLifecycleRequest(coreExecutionId="e-3", status="completed", sourceRevision="gitsha", finishedAt="2026-09-22T01:00:00Z"))
    assert len(x["coreRequests"]) == 2
    assert x["coreRequests"][0]["path"].endswith("/e-3/revisions")
    assert x["coreRequests"][0]["data"]["status"] == "completed"
    assert x["coreRequests"][1]["path"].endswith("/e-3/snapshots")
    assert x["snapshotRequested"] is True


def test_lifecycle_can_omit_snapshot():
    x = build_lifecycle(ExecutionLifecycleRequest(coreExecutionId="e-4", includeSnapshot=False))
    assert len(x["coreRequests"]) == 1
    assert x["snapshotRequested"] is False


def test_bundle_consumer_is_read_only_and_declared_not_inferred():
    bundle = {
        "execution":{"id":"e-5","execution_key":"eng-5","execution_type":"engineering_calculation","runtime_kind":"workbench","status":"completed","project_ref":"p:1","external_run_ref":"sc://workbench/execution/eng-5","source_revision":"abc"},
        "inputs":[{"object_ref":"dataset:1"}],
        "parameters":[],"assumptions":[],"environments":[],"steps":[],
        "outputs":[{"object_ref":"result:1"}],
        "research_bindings":[],"dependencies":[],"verifications":[],"revisions":[],"snapshots":[],
    }
    x = consume_core_lineage_bundle(CoreLineageBundleConsumeRequest(bundle=bundle))
    assert x["ok"] is True
    c = x["context"]
    assert c["coreExecutionId"] == "e-5"
    assert c["inputRefs"] == ["dataset:1"] and c["outputRefs"] == ["result:1"]
    assert c["lineageIsDeclaredNotInferred"] is True
    assert c["scientificValidityInferred"] is False
    assert c["reproducibilityInferred"] is False
    assert c["automaticWorkbenchMutationAuthorized"] is False


def test_bundle_consumer_rejects_missing_execution_id():
    x = consume_core_lineage_bundle(CoreLineageBundleConsumeRequest(bundle={"execution":{}}))
    assert x["ok"] is False


def test_service_token_policy_applies_to_v670_routes(monkeypatch):
    monkeypatch.setenv("SCWB_REQUIRE_SERVICE_TOKEN","true")
    monkeypatch.setenv("SCWB_SERVICE_TOKEN","secret-670")
    c = client()
    assert c.get("/integration/core/computation-lineage/manifest").status_code == 401
    ok = c.get("/integration/core/computation-lineage/manifest", headers={"X-SC-Service-Token":"secret-670"})
    assert ok.status_code == 200 and ok.json()["version"] == "7.0.0"


def test_v670_status_and_capabilities():
    c = client()
    status = c.get("/v670/status").json()
    assert status["ok"] is True and status["version"] == "7.0.0"
    assert status["coreComputationLineageContract"] == CORE_COMPUTATION_LINEAGE_CONTRACT
    assert status["twoPhaseExecutionLineage"] is True
    caps = c.get("/capabilities").json()
    assert caps["version"] == "7.0.0"
    assert caps["coreIntegration"]["executionLineageBridge"] is True
    assert "platform-core-computation-execution-lineage-bridge" in caps["capabilities"]


def test_live_endpoints_build_valid_plans_without_dispatch():
    c = client()
    r = c.post("/integration/core/computation-lineage/executions/build", json={"executionKey":"deploy","title":"Deploy verification"})
    assert r.status_code == 200 and r.json()["automaticCorePersistenceAuthorized"] is False
    r = c.post("/integration/core/computation-lineage/executions/components/build", json={"coreExecutionId":"e-deploy","inputs":[],"outputs":[]})
    assert r.status_code == 200 and r.json()["requestCount"] == 0
    r = c.post("/integration/core/computation-lineage/executions/lifecycle/build", json={"coreExecutionId":"e-deploy","includeSnapshot":False})
    assert r.status_code == 200 and len(r.json()["coreRequests"]) == 1
