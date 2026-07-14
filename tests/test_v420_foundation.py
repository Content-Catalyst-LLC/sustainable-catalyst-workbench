from app.v420 import (
    BUILTIN_TEMPLATES, TemplateCatalogRequest, TemplateValidationRequest,
    GuidedIntakeRequest, RequirementPlanRequest, MilestonePlanRequest,
    ValidationGateRequest, StarterEvidenceRequest, ScaffoldRequest,
    AdaptTemplateRequest, TemplatePackageRequest, status, catalog_templates,
    validate_template, build_guided_intake, build_requirement_plan,
    build_milestone_plan, evaluate_validation_gates, build_starter_evidence,
    build_project_scaffold, adapt_template, build_template_package,
)


def test_status_declares_guided_workspace_and_safety():
    result = status()
    assert result["version"] == "4.2.0"
    assert result["expectedStudioCount"] == 24
    assert result["templateCount"] == 6
    assert result["automaticExperimentExecutionAuthorized"] is False
    assert result["automaticCertificationAuthorized"] is False


def test_catalog_returns_hashed_templates():
    result = catalog_templates(TemplateCatalogRequest())
    assert result["catalog"]["templateCount"] == 6
    assert all(item["templateHash"] for item in result["catalog"]["templates"])


def test_catalog_domain_filter_includes_engineering_template():
    result = catalog_templates(TemplateCatalogRequest(domain="mechanical"))
    ids = {item["templateId"] for item in result["catalog"]["templates"]}
    assert "engineering-design" in ids


def test_builtin_template_validates():
    result = validate_template(TemplateValidationRequest(template=BUILTIN_TEMPLATES["scientific-investigation"]))
    assert result["ok"] is True
    assert result["template"]["automaticExecutionAuthorized"] is False


def test_template_validation_blocks_missing_gates():
    template = dict(BUILTIN_TEMPLATES["scientific-investigation"])
    template["defaultGates"] = []
    result = validate_template(TemplateValidationRequest(template=template))
    assert result["ok"] is False
    assert any(item["code"] == "missing-defaultGates" or item["code"] == "validation-gate-required" for item in result["findings"])


def test_guided_intake_marks_high_stakes_for_professional_review():
    result = build_guided_intake(GuidedIntakeRequest(title="Bridge Study", domain="civil", project_type="engineering", objective="Evaluate a retrofit concept.", high_stakes=True))
    assert result["ok"] is True
    assert result["intake"]["professionalReviewRequired"] is True
    assert result["intake"]["automaticPublicationAuthorized"] is False


def test_requirement_plan_merges_duplicate_ids():
    result = build_requirement_plan(RequirementPlanRequest(template_id="engineering-design", additional_requirements=[{"id":"requirements","title":"Custom measurable requirements","priority":"must"}]))
    ids = [item["requirementId"] for item in result["plan"]["requirements"]]
    assert len(ids) == len(set(ids))
    assert any(item.startswith("duplicate-requirement-merged") for item in result["findings"])


def test_milestone_plan_preserves_stage_order():
    result = build_milestone_plan(MilestonePlanRequest(template_id="scientific-investigation", start_date="2026-07-14"))
    assert result["ok"] is True
    assert result["plan"]["milestones"][0]["stage"] == "frame"
    assert result["plan"]["milestones"][-1]["stage"] == "report"


def test_validation_gate_blocks_missing_evidence():
    result = evaluate_validation_gates(ValidationGateRequest(template_id="instrument-validation", evidence=[], approvals=[]))
    assert result["ok"] is False
    assert result["report"]["gates"][0]["state"] == "blocked"


def test_validation_gate_requires_human_approval_after_evidence():
    evidence = [{"type":"calibration-record"},{"type":"reference-standard"},{"type":"dataset"},{"type":"uncertainty"},{"type":"acceptance-report"}]
    result = evaluate_validation_gates(ValidationGateRequest(template_id="instrument-validation", evidence=evidence, approvals=[]))
    assert result["ok"] is False
    assert all(item["state"] == "approval-required" for item in result["report"]["gates"])


def test_starter_evidence_is_unverified():
    result = build_starter_evidence(StarterEvidenceRequest(domain="chemistry", objective="Validate a sensor."))
    assert result["ok"] is True
    assert all(item["verified"] is False for item in result["package"]["records"])
    assert result["package"]["automaticClaimApprovalAuthorized"] is False


def test_scaffold_is_team_ready_and_nonexecuting():
    result = build_project_scaffold(ScaffoldRequest(template_id="engineering-design", intake={"title":"Controller","domain":"electrical"}, team_bindings=[{"userId":"u1","role":"project-owner"}]))
    assert result["ok"] is True
    assert result["scaffold"]["teamBindings"][0]["userId"] == "u1"
    assert result["scaffold"]["automaticDeviceControlAuthorized"] is False


def test_adaptation_preserves_source_template():
    result = adapt_template(AdaptTemplateRequest(template_id="predictive-analysis", domain="health", high_stakes=True, team_mode=True))
    assert result["ok"] is True
    assert result["plan"]["sourceTemplateMutated"] is False
    assert result["plan"]["requiresHumanAcceptance"] is True


def test_package_removes_secret_fields():
    result = build_template_package(TemplatePackageRequest(template={"templateId":"x","apiToken":"secret"}, scaffold={"password":"secret","projectId":"p"}))
    package = result["package"]
    assert "apiToken" not in package["template"]
    assert "password" not in package["scaffold"]
    assert package["secretsIncluded"] is False


def test_scaffold_hash_is_stable_for_same_input():
    request = ScaffoldRequest(template_id="scientific-investigation", intake={"title":"Stable","domain":"physics"})
    first = build_project_scaffold(request)["scaffold"]["scaffoldHash"]
    second = build_project_scaffold(request)["scaffold"]["scaffoldHash"]
    assert first == second
