from fastapi.testclient import TestClient
from app.main import app
from app.v600 import ComputationalObject, ProjectInput, SharedVariable
from app.v640 import CORE_RUNTIME_CONTRACT
from app.v650 import PRODUCT_REF
from app.v660 import CORE_UNIFIED_RUNTIME_CONTRACT, SCHEMA, CoreBundleConsumeRequest, ExecutionBindingRequest, HandoffBindingRequest, PackageBindingRequest, ProjectSessionBindRequest, SessionCreateRequest, ValidationBindingRequest, VisualBindingRequest, bridge_manifest, build_execution_binding, build_handoff_binding, build_package_binding, build_project_session_bindings, build_session_create, build_validation_binding, build_visual_binding, consume_core_bundle

def client(): return TestClient(app)
def sample_project(): return ProjectInput(projectId="session-bridge-demo",title="Session Bridge Demo",variables=[SharedVariable(name="mass",value=5.0,units="kg")],objects=[ComputationalObject(objectId="model-1",kind="model",studio="numerical-computing",variableInputs=["mass"],payload={"method":"bounded-demo"},sourceSchema="sc-test/model",sourceVersion="1.0")])

def test_manifest_targets_exact_core_300_contract_and_guardrails():
 m=bridge_manifest(); assert m["version"]=="8.5.0" and m["schema"]==SCHEMA; assert m["runtimeContractRef"]==CORE_RUNTIME_CONTRACT; assert m["coreUnifiedRuntimeContract"]==CORE_UNIFIED_RUNTIME_CONTRACT; assert m["corePaths"]["sessions"]=="/v1/research/unified-runtime/sessions"; assert m["boundaries"]["coreSessionIdMustComeFromCore"] is True; assert m["boundaries"]["automaticCorePersistenceAuthorized"] is False

def test_session_create_is_phase_one_and_matches_core_fields():
 x=build_session_create(SessionCreateRequest(project=sample_project())); d=x["sessionDraft"]; assert x["phase"]=="prepare-session"; assert d["project_ref"]=="sc://workbench/project/session-bridge-demo"; assert d["runtime_contract_ref"]==CORE_RUNTIME_CONTRACT; assert d["metadata"]["workbenchVersion"]=="8.5.0"; assert x["coreRequest"]["path"]=="/v1/research/unified-runtime/sessions"; assert x["coreRequest"]["automaticDispatchAuthorized"] is False

def test_session_create_preserves_explicit_core_project_ref():
 assert build_session_create(SessionCreateRequest(project=sample_project(),coreProjectRef="project:core:42"))["sessionDraft"]["project_ref"]=="project:core:42"

def test_project_bind_requires_real_core_session_id():
 r=client().post("/integration/core/unified-runtime/projects/bind",json={"coreSessionId":"","project":{"projectId":"x","title":"X"}}); assert r.status_code==422

def test_project_session_binding_builds_product_project_object_and_variable_bindings():
 x=build_project_session_bindings(ProjectSessionBindRequest(coreSessionId="session-core-1",project=sample_project())); assert x["ok"] is True and x["coreSessionId"]=="session-core-1"; assert x["productBinding"]["product_ref"]==PRODUCT_REF and x["productBinding"]["product_version"]=="8.5.0"; types=[b["object_type"] for b in x["objectBindings"]]; assert "workbench.computational-project" in types and "workbench.computational-object" in types and "workbench.shared-variable-set" in types; assert x["bindingCount"]==len(x["objectBindings"])+1; assert all(req["data"]["session_id"]=="session-core-1" for req in x["coreRequests"])

def test_project_session_binding_can_omit_variable_set():
 x=build_project_session_bindings(ProjectSessionBindRequest(coreSessionId="s1",project=sample_project(),includeVariableSet=False)); assert "workbench.shared-variable-set" not in [b["object_type"] for b in x["objectBindings"]]

def test_execution_binding_matches_core_execution_shape():
 x=build_execution_binding(ExecutionBindingRequest(coreSessionId="s1",executionRef="sc://workbench/execution/1",inputRefs=["dataset:1"],outputRefs=["result:1"])); d=x["binding"]; assert d["session_id"]=="s1" and d["execution_ref"]=="sc://workbench/execution/1"; assert d["input_refs"]==["dataset:1"] and d["output_refs"]==["result:1"]; assert x["coreRequest"]["path"]=="/v1/research/unified-runtime/execution-bindings"

def test_visual_binding_matches_core_visual_shape():
 x=build_visual_binding(VisualBindingRequest(coreSessionId="s1",visualRef="visual:1",sceneRef="scene:1",sourceRefs=["result:1"])); assert x["binding"]["scene_ref"]=="scene:1" and x["coreRequest"]["path"]=="/v1/research/unified-runtime/visual-bindings"

def test_validation_binding_matches_core_validation_shape():
 x=build_validation_binding(ValidationBindingRequest(coreSessionId="s1",validationRef="validation:1",validationType="replication",targetRefs=["result:1"])); assert x["binding"]["validation_type"]=="replication" and x["coreRequest"]["path"]=="/v1/research/unified-runtime/validation-bindings"

def test_package_binding_matches_core_package_shape():
 x=build_package_binding(PackageBindingRequest(coreSessionId="s1",packageRef="package:1",contentHash="abc",memberRefs=["result:1"])); assert x["binding"]["content_hash"]=="abc" and x["coreRequest"]["path"]=="/v1/research/unified-runtime/package-bindings"

def test_handoff_binding_matches_core_handoff_shape():
 x=build_handoff_binding(HandoffBindingRequest(coreSessionId="s1",handoffRef="handoff:1",targetProductRef="product:lab")); assert x["binding"]["source_product_ref"]==PRODUCT_REF and x["binding"]["target_product_ref"]=="product:lab"; assert x["coreRequest"]["path"]=="/v1/research/unified-runtime/handoff-bindings"

def test_core_bundle_consumer_accepts_exact_core_runtime_bundle():
 x=consume_core_bundle(CoreBundleConsumeRequest(bundle={"contract":CORE_UNIFIED_RUNTIME_CONTRACT,"session":{"id":"s1","project_ref":"project:1","runtime_contract_ref":CORE_RUNTIME_CONTRACT},"product_bindings":[{"product_ref":PRODUCT_REF}],"object_bindings":[{"object_type":"workbench.computational-project","object_ref":"sc://workbench/project/1"}],"execution_bindings":[{"execution_ref":"execution:1"}],"visual_bindings":[{"visual_ref":"visual:1"}],"package_bindings":[{"package_ref":"package:1"}],"handoff_bindings":[{"handoff_ref":"handoff:1"}],"underlying_objects_remain_authoritative":True})); assert x["ok"] is True; c=x["context"]; assert c["coreSessionId"]=="s1" and c["workbenchProductBindingPresent"] is True; assert c["readOnlyContext"] is True and c["automaticWorkbenchMutationAuthorized"] is False

def test_core_bundle_consumer_rejects_wrong_runtime_contract():
 assert consume_core_bundle(CoreBundleConsumeRequest(bundle={"session":{"id":"s1","project_ref":"project:1","runtime_contract_ref":"wrong"}}))["ok"] is False

def test_service_token_policy_applies_to_v660_routes(monkeypatch):
 monkeypatch.setenv("SCWB_REQUIRE_SERVICE_TOKEN","true"); monkeypatch.setenv("SCWB_SERVICE_TOKEN","secret-660"); c=client(); assert c.get("/integration/core/unified-runtime/manifest").status_code==401; ok=c.get("/integration/core/unified-runtime/manifest",headers={"X-SC-Service-Token":"secret-660"}); assert ok.status_code==200 and ok.json()["version"]=="8.5.0"

def test_v660_status_public_and_non_dispatching():
 b=client().get("/v660/status").json(); assert b["ok"] is True and b["version"]=="8.5.0"; assert b["twoPhaseSessionBinding"] is True; assert b["automaticCoreDispatch"] is False and b["automaticCorePersistence"] is False

def test_capabilities_advertise_session_bridge():
 c=client().get("/capabilities").json(); assert c["version"]=="8.5.0"; assert c["coreIntegration"]["unifiedResearchSessionBinding"] is True; assert "platform-core-unified-research-session-bridge" in c["capabilities"]
