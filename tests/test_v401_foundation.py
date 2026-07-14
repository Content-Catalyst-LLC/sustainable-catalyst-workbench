from backend.app.v401 import (
    ActivationAuditRequest,
    SchemaCompatibilityRequest,
    ProjectPropagationRequest,
    HandoffRoundTripRequest,
    AssetAuditRequest,
    IntegrationProbeRequest,
    RepairPlanRequest,
    FixtureEvaluationRequest,
    build_activation_audit,
    build_schema_compatibility,
    build_project_propagation,
    validate_handoff_roundtrip,
    build_asset_audit,
    build_integration_probe,
    build_repair_plan,
    evaluate_fixture,
    stable_hash,
    status,
)


def ready_studios(count=22):
    return [{"key": f"studio-{i}", "shortcode": f"sc_{i}", "registered": True, "rendered": True, "state": "ready"} for i in range(count)]


def test_status_declares_patch_and_safety_boundaries():
    result = status()
    assert result["version"] == "4.0.1"
    assert result["expectedStudioCount"] == 22
    assert result["automaticRepairAuthorized"] is False
    assert result["automaticDestructiveActionAuthorized"] is False


def test_activation_audit_passes_complete_rendered_registry():
    result = build_activation_audit(ActivationAuditRequest(studios=ready_studios()))
    assert result["ok"] is True
    assert result["audit"]["registeredStudioCount"] == 22
    assert result["audit"]["renderedStudioCount"] == 22


def test_activation_audit_blocks_literal_shortcode_output():
    result = build_activation_audit(ActivationAuditRequest(studios=ready_studios(), exposed_shortcode_text=['[sc_workbench_robotics_studio project="default"]']))
    assert result["ok"] is False
    assert result["audit"]["findings"][0]["code"] == "literal-shortcode-output"


def test_schema_report_accepts_current_connected_project():
    result = build_schema_compatibility(SchemaCompatibilityRequest(records=[{"id":"p1","schema":"sc-workbench-connected-environment-project/1.0","version":"4.0.1"}]))
    assert result["ok"] is True
    assert len(result["report"]["compatible"]) == 1


def test_schema_report_blocks_below_floor_record():
    result = build_schema_compatibility(SchemaCompatibilityRequest(records=[{"schema":"sc-workbench-connected-environment-project/1.0","version":"3.9.0"}]))
    assert result["ok"] is False
    assert result["report"]["incompatible"][0]["reason"] == "below-compatibility-floor"


def test_project_propagation_builds_actions_and_detects_missing_required_studio():
    result = build_project_propagation(ProjectPropagationRequest(project_id="p1", studios=["connected"], required_studios=["connected","lab"]))
    assert result["ok"] is False
    assert result["plan"]["missingRequiredStudios"] == ["lab"]
    assert result["plan"]["actions"][0]["projectId"] == "p1"


def test_handoff_roundtrip_validates_matching_receipt_hash():
    packet = {"schema":"handoff/1.0","projectId":"p1","source":"workbench","target":"decision-studio"}
    packet_hash = stable_hash(packet)
    result = validate_handoff_roundtrip(HandoffRoundTripRequest(source="workbench", target="decision-studio", packet={**packet,"packetHash":packet_hash}, receipt={"status":"accepted","packetHash":packet_hash}))
    assert result["ok"] is True


def test_handoff_roundtrip_rejects_hash_mismatch():
    packet = {"schema":"handoff/1.0","projectId":"p1","source":"workbench","target":"site-intelligence"}
    result = validate_handoff_roundtrip(HandoffRoundTripRequest(source="workbench", target="site-intelligence", packet=packet, receipt={"status":"accepted","packetHash":"wrong"}))
    assert result["ok"] is False


def test_asset_audit_detects_literal_shortcode_and_missing_asset():
    result = build_asset_audit(AssetAuditRequest(assets=[{"handle":"scwb-v401","loaded":False,"version":"4.0.1"}], rendered_html='[sc_workbench_controls_studio project="default"]'))
    codes = {item["code"] for item in result["report"]["findings"]}
    assert result["ok"] is False
    assert {"asset-missing","literal-shortcode-output"}.issubset(codes)


def test_integration_probe_uses_offline_fallback_for_required_service():
    result = build_integration_probe(IntegrationProbeRequest(integrations=[{"id":"site-intelligence","required":True,"status":"offline"}], offline_available=True))
    assert result["ok"] is True
    assert result["report"]["degraded"][0]["fallback"] == "offline-fastapi"


def test_repair_plan_blocks_destructive_recovery_without_backup():
    result = build_repair_plan(RepairPlanRequest(findings=[{"code":"schema-incompatible"}], backup_verified=False, allow_destructive=True))
    assert result["ok"] is False
    assert result["plan"]["blockedActions"][0]["blockedBy"] == "verified-backup-required"


def test_fixture_evaluation_passes_complete_fixture():
    fixture = {"project":{"projectId":"p1"},"requiredStudios":["connected"],"studios":[{"key":"connected"}],"integrations":[{"id":"workbench","required":True,"status":"ready"}],"workflow":[{"id":"review"}],"records":[{"id":"r1"}]}
    result = evaluate_fixture(FixtureEvaluationRequest(fixture=fixture))
    assert result["ok"] is True
    assert result["evaluation"]["humanReviewRequired"] is True


def test_fixture_evaluation_detects_duplicates_and_missing_project():
    result = evaluate_fixture(FixtureEvaluationRequest(fixture={"records":[{"id":"r1"},{"id":"r1"}]}))
    assert result["ok"] is False
    assert "duplicate-record-identifiers" in result["evaluation"]["findings"]
