from backend.app.v400 import (
    CapabilityRegistryRequest,
    ConnectedProjectRequest,
    ConnectionGraphRequest,
    WorkflowPlanRequest,
    SharedContextRequest,
    IntegrationHealthRequest,
    TraceabilityRequest,
    SyncPlanRequest,
    DossierRequest,
    ReleaseManifestRequest,
    ExtensionValidationRequest,
    build_capability_registry,
    build_connected_project,
    build_connection_graph,
    build_workflow_plan,
    build_shared_context,
    build_integration_health,
    build_traceability,
    build_sync_plan,
    build_connected_dossier,
    build_release_manifest,
    validate_extension_contract,
    status,
)


def test_status_declares_connected_milestone_and_boundaries():
    result = status()
    assert result["ok"] is True
    assert result["version"] == "4.0.0"
    assert result["offlineSupported"] is True
    assert result["automaticPublicationAuthorized"] is False
    assert result["remoteShellAllowed"] is False


def test_capability_registry_is_ready_when_required_capabilities_exist():
    result = build_capability_registry(CapabilityRegistryRequest(studios=["connected", "simulation"]))
    assert result["ok"] is True
    assert result["registry"]["missingCapabilities"] == []
    assert result["registry"]["registryHash"]


def test_capability_registry_reports_missing_capabilities():
    result = build_capability_registry(CapabilityRegistryRequest(required_capabilities=["simulation", "devices"], available_capabilities=["simulation"]))
    assert result["ok"] is False
    assert result["registry"]["missingCapabilities"] == ["devices"]


def test_connected_project_hashes_records_and_rejects_duplicates():
    result = build_connected_project(ConnectedProjectRequest(records=[{"id": "r1", "value": 1}, {"id": "r1", "value": 2}]))
    assert result["ok"] is False
    assert result["project"]["recordCount"] == 1
    assert result["project"]["duplicateRecordIds"] == ["r1"]
    assert result["project"]["records"][0]["recordHash"]


def test_connection_graph_builds_components_and_isolated_nodes():
    result = build_connection_graph(ConnectionGraphRequest(nodes=[{"id": "a"}, {"id": "b"}, {"id": "c"}], edges=[{"source": "a", "target": "b"}]))
    assert result["ok"] is True
    assert result["graph"]["componentCount"] == 2
    assert result["graph"]["isolatedNodeIds"] == ["c"]


def test_connection_graph_rejects_unknown_edge_endpoint():
    result = build_connection_graph(ConnectionGraphRequest(nodes=[{"id": "a"}], edges=[{"source": "a", "target": "missing"}]))
    assert result["ok"] is False
    assert result["graph"]["invalidEdges"][0]["target"] == "missing"


def test_workflow_orders_dependencies():
    result = build_workflow_plan(WorkflowPlanRequest(steps=[
        {"id": "analyze", "requires": ["calculations"]},
        {"id": "review", "dependsOn": ["analyze"], "requires": ["reviews"]},
    ]))
    assert result["ok"] is True
    assert result["plan"]["executionOrder"] == ["analyze", "review"]
    assert result["plan"]["automaticExecutionAuthorized"] is False


def test_workflow_blocks_remote_shell_and_unapproved_step():
    result = build_workflow_plan(WorkflowPlanRequest(steps=[{"id": "unsafe", "operation": "remote-shell", "approval": "owner"}]))
    assert result["ok"] is False
    codes = {item["code"] for item in result["plan"]["issues"]}
    assert {"blocked-operation", "approval-required"}.issubset(codes)


def test_shared_context_detects_variable_conflicts():
    result = build_shared_context(SharedContextRequest(variables=[{"name": "temperature", "value": 20}, {"name": "temperature", "value": 25}]))
    assert result["ok"] is False
    assert result["context"]["conflicts"][0]["name"] == "temperature"


def test_integration_health_allows_optional_degradation():
    result = build_integration_health(IntegrationHealthRequest(integrations=[
        {"id": "workbench", "required": True, "status": "ready"},
        {"id": "site-intelligence", "required": False, "status": "offline"},
    ]))
    assert result["ok"] is True
    assert result["report"]["degraded"] is True
    assert result["report"]["offlineFallbackAvailable"] is True


def test_integration_health_blocks_required_failure():
    result = build_integration_health(IntegrationHealthRequest(integrations=[{"id": "workbench", "required": True, "status": "offline"}]))
    assert result["ok"] is False


def test_traceability_requires_record_evidence_and_review():
    result = build_traceability(TraceabilityRequest(
        requirements=[{"id": "req-1", "recordIds": ["r1"], "evidenceIds": ["e1"], "reviewIds": []}],
        records=[{"id": "r1"}], evidence=[{"id": "e1"}], reviews=[]))
    assert result["ok"] is False
    assert result["report"]["coveragePercent"] == 0.0


def test_traceability_reports_full_coverage():
    result = build_traceability(TraceabilityRequest(
        requirements=[{"id": "req-1", "recordIds": ["r1"], "evidenceIds": ["e1"], "reviewIds": ["v1"]}],
        records=[{"id": "r1"}], evidence=[{"id": "e1"}], reviews=[{"id": "v1"}]))
    assert result["ok"] is True
    assert result["report"]["coveragePercent"] == 100.0


def test_sync_requires_backup_for_destructive_conflict_resolution():
    result = build_sync_plan(SyncPlanRequest(local_records=[{"id": "r1", "value": 1}], remote_records=[{"id": "r1", "value": 2}], strategy="keep-local", backup_verified=False))
    assert result["ok"] is False
    assert result["plan"]["blockingIssues"] == ["verified-backup-required"]


def test_sync_preserves_both_with_rename_without_backup():
    result = build_sync_plan(SyncPlanRequest(local_records=[{"id": "r1", "value": 1}], remote_records=[{"id": "r1", "value": 2}], strategy="rename"))
    assert result["ok"] is True
    assert result["plan"]["actions"][0]["action"] == "preserve-both"


def test_connected_dossier_is_hashed_and_never_claims_certification():
    result = build_connected_dossier(DossierRequest(project={"projectId": "p1"}, evidence=[{"id": "e1"}], reviews=[{"id": "v1"}]))
    assert result["ok"] is True
    assert result["dossier"]["counts"]["evidence"] == 1
    assert result["dossier"]["certificationClaim"] is False
    assert result["dossier"]["dossierHash"]


def test_release_manifest_requires_human_approval():
    result = build_release_manifest(ReleaseManifestRequest(human_approval=False))
    assert result["ok"] is False
    assert "human-approval-required" in result["manifest"]["blockingIssues"]
    assert result["manifest"]["automaticPublicationAuthorized"] is False


def test_release_manifest_passes_complete_human_reviewed_record():
    result = build_release_manifest(ReleaseManifestRequest(
        capability_registry={"ready": True, "registryHash": "a"},
        integration_health={"ready": True, "healthHash": "b"},
        traceability={"ready": True, "traceabilityHash": "c"},
        evaluations=[{"type": "security", "ready": True}],
        human_approval=True,
    ))
    assert result["ok"] is True
    assert result["manifest"]["status"] == "ready-for-connected-release"
    assert result["manifest"]["remoteShellAllowed"] is False


def test_extension_validation_reports_missing_contract_members():
    result = validate_extension_contract(ExtensionValidationRequest(contract={"hooks": ["scwb:ready"]}, required_hooks=["scwb:ready"], required_routes=["/v400/status"], required_schemas=["project/1.0"]))
    assert result["ok"] is False
    assert result["report"]["missing"]["routes"] == ["/v400/status"]
