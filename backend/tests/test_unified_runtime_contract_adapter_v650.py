from fastapi.testclient import TestClient

from app.main import app
from app.v600 import ComputationalObject, ProjectInput, SharedVariable
from app.v650 import (
    CORE_RUNTIME_CONTRACT,
    PRODUCT_REF,
    SCHEMA,
    SUPPORTED_CAPABILITIES,
    SUPPORTED_OPERATIONS,
    ContractValidateRequest,
    ExchangeBuildRequest,
    ExchangeConsumeRequest,
    InvocationBuildRequest,
    ProductBindingRequest,
    ProjectMapRequest,
    ResultBuildRequest,
    adapter_manifest,
    build_exchange,
    build_invocation,
    build_product_binding,
    build_result,
    consume_exchange,
    map_project,
    validate_contract_bundle,
)


def client():
    return TestClient(app)


def sample_project():
    return ProjectInput(
        projectId="core-adapter-demo",
        title="Core Adapter Demo",
        variables=[SharedVariable(name="mass", value=4.0, units="kg")],
        objects=[
            ComputationalObject(
                objectId="model-1",
                kind="model",
                studio="numerical-computing",
                variableInputs=["mass"],
                payload={"method": "bounded-demo"},
                sourceSchema="sc-test/model",
                sourceVersion="1.0",
            )
        ],
    )


def test_manifest_declares_core_contract_and_boundaries():
    m = adapter_manifest()
    assert m["ok"] is True
    assert m["schema"] == SCHEMA
    assert m["version"] == "7.8.0"
    assert m["contract"] == CORE_RUNTIME_CONTRACT
    assert m["productRef"] == PRODUCT_REF
    assert "context:handoff" in m["supportedCapabilities"]
    assert m["boundaries"]["automaticCoreDispatchAuthorized"] is False
    assert m["boundaries"]["arbitraryCoreInstructionExecutionAuthorized"] is False


def test_contract_bundle_validation_matches_core_296_shape():
    bundle = {
        "release": "2.96.0",
        "contract_schema": CORE_RUNTIME_CONTRACT,
        "contract": {
            "id": "contract-1",
            "contract_key": "core-runtime-v1",
            "contract_version": "1.0",
            "required_capabilities": ["object:read", "object:version", "provenance:trace"],
        },
        "operations": [
            {"operation": "read"},
            {"operation": "handoff"},
            {"operation": "snapshot"},
        ],
    }
    report = validate_contract_bundle(ContractValidateRequest(bundle=bundle))
    assert report["ok"] is True
    assert report["schemaCompatible"] is True
    assert report["declaredCompatibility"] is True
    assert report["missingRequiredCapabilities"] == []
    assert report["unknownDeclaredOperations"] == []


def test_contract_bundle_reports_missing_declared_capability_without_inference():
    bundle = {
        "contract_schema": CORE_RUNTIME_CONTRACT,
        "contract": {"required_capabilities": ["workflow:state"]},
        "operations": [{"operation": "read"}],
    }
    report = validate_contract_bundle(ContractValidateRequest(bundle=bundle))
    assert report["ok"] is True
    assert report["declaredCompatibility"] is False
    assert report["missingRequiredCapabilities"] == ["workflow:state"]
    assert report["contractSemanticsDeclaredNotInferred"] is True


def test_product_binding_builds_exact_core_request_shape():
    result = build_product_binding(ProductBindingRequest(contractId="contract-1"))
    data = result["productBinding"]
    assert data["contract_id"] == "contract-1"
    assert data["product_ref"] == PRODUCT_REF
    assert data["product_version"] == "7.8.0"
    assert data["supported_capabilities"] == SUPPORTED_CAPABILITIES
    assert result["coreRequest"]["path"] == "/v1/research/runtime-contract/product-bindings"
    assert result["coreRequest"]["automaticDispatchAuthorized"] is False


def test_project_mapping_preserves_workbench_hashes_and_generates_core_refs():
    result = map_project(ProjectMapRequest(project=sample_project()))
    assert result["ok"] is True
    assert result["projectRef"] == "sc://workbench/project/core-adapter-demo"
    assert result["objects"][0]["objectRef"] == "sc://workbench/object/core-adapter-demo/model-1"
    assert len(result["objects"][0]["contentHash"]) == 64
    assert result["automaticCorePersistenceAuthorized"] is False


def test_inbound_exchange_is_accepted_only_for_workbench_supported_operation():
    exchange = {
        "id": "ex-1",
        "exchange_key": "demo",
        "contract_id": "contract-1",
        "project_ref": "project:1",
        "source_product_ref": "product:library",
        "target_product_ref": PRODUCT_REF,
        "operation": "handoff",
        "object_refs": ["dataset:1", "protocol:1"],
        "provenance_refs": ["prov:1"],
        "envelope_hash": "abc",
    }
    result = consume_exchange(ExchangeConsumeRequest(exchange=exchange))
    assert result["ok"] is True
    plan = result["result"]
    assert plan["accepted"] is True
    assert plan["importPlan"]["requiresExplicitExecutionRequest"] is True
    assert plan["importPlan"]["automaticExecutionAuthorized"] is False


def test_inbound_exchange_for_other_target_is_not_accepted():
    result = consume_exchange(ExchangeConsumeRequest(exchange={
        "target_product_ref": "product:lab",
        "operation": "handoff",
        "object_refs": [],
    }))
    assert result["ok"] is False
    assert result["result"]["acceptedTarget"] is False


def test_outbound_exchange_matches_core_create_exchange_fields():
    result = build_exchange(ExchangeBuildRequest(
        contractId="contract-1",
        projectRef="project:1",
        targetProductRef="product:lab",
        operation="handoff",
        objectRefs=["result:2", "result:1", "result:1"],
        provenanceRefs=["prov:1"],
    ))
    data = result["exchange"]
    assert data["source_product_ref"] == PRODUCT_REF
    assert data["target_product_ref"] == "product:lab"
    assert data["object_refs"] == ["result:1", "result:2"]
    assert result["coreRequest"]["path"] == "/v1/research/runtime-contract/exchanges"


def test_update_operation_is_core_known_but_not_workbench_declared():
    assert "update" not in SUPPORTED_OPERATIONS
    c = client()
    response = c.post("/integration/core/runtime-contract/exchanges/build", json={
        "contractId": "contract-1",
        "projectRef": "project:1",
        "targetProductRef": "product:lab",
        "operation": "update",
    })
    assert response.status_code == 400


def test_invocation_builder_uses_workbench_as_caller_and_runtime():
    result = build_invocation(InvocationBuildRequest(
        contractId="contract-1",
        projectRef="project:1",
        operation="read",
        inputRefs=["dataset:1"],
    ))
    data = result["invocation"]
    assert data["caller_ref"] == PRODUCT_REF
    assert data["runtime_ref"] == "sc://workbench/runtime/7.8.0"
    assert result["coreRequest"]["path"] == "/v1/research/runtime-contract/invocations"


def test_result_builder_hashes_payload_when_hash_not_supplied():
    result = build_result(ResultBuildRequest(
        invocationId="inv-1",
        projectRef="project:1",
        resultType="analysis_output",
        objectRef="sc://workbench/result/1",
        resultPayload={"value": 42},
    ))
    data = result["resultBinding"]
    assert len(data["content_hash"]) == 64
    assert result["coreRequest"]["path"] == "/v1/research/runtime-contract/results"


def test_service_token_policy_applies_to_new_adapter_routes(monkeypatch):
    monkeypatch.setenv("SCWB_REQUIRE_SERVICE_TOKEN", "true")
    monkeypatch.setenv("SCWB_SERVICE_TOKEN", "secret-650")
    c = client()
    assert c.get("/integration/core/runtime-contract/manifest").status_code == 401
    ok = c.get("/integration/core/runtime-contract/manifest", headers={"X-SC-Service-Token": "secret-650"})
    assert ok.status_code == 200
    assert ok.json()["version"] == "7.8.0"


def test_release_status_is_public_and_non_dispatching(monkeypatch):
    monkeypatch.setenv("SCWB_REQUIRE_SERVICE_TOKEN", "true")
    monkeypatch.setenv("SCWB_SERVICE_TOKEN", "secret-650")
    body = client().get("/v650/status").json()
    assert body["ok"] is True
    assert body["contract"] == CORE_RUNTIME_CONTRACT
    assert body["automaticCoreDispatch"] is False
    assert body["automaticCorePersistence"] is False
