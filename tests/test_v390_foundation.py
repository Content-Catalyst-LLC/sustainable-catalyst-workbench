from app.v390 import (
    AccessibilityAuditRequest, PerformanceBudgetRequest, SecurityAuditRequest,
    CompatibilityMatrixRequest, MigrationStressRequest, FailureInjectionRequest,
    OnboardingPackageRequest, ExtensionContractRequest, ReleaseGateRequest,
    status, build_accessibility_report, build_performance_report, build_security_report,
    build_compatibility_report, build_migration_stress_report,
    build_failure_recovery_report, build_onboarding_package,
    build_extension_contract, build_release_gate,
)


def ready_records():
    return [{"type": item, "ready": True} for item in status()["requiredEvaluations"]]


def test_status_requires_human_release_approval():
    result = status()
    assert result["version"] == "3.9.0"
    assert result["humanReleaseApprovalRequired"] is True
    assert result["automaticPublicationAuthorized"] is False


def test_accessibility_passes_clean_evaluation():
    result = build_accessibility_report(AccessibilityAuditRequest(pages_tested=12))
    assert result["ok"] is True
    assert result["report"]["certificationClaim"] is False
    assert result["report"]["reportHash"]


def test_accessibility_blocks_keyboard_and_contrast_failures():
    result = build_accessibility_report(AccessibilityAuditRequest(keyboard_navigation=False, contrast_failures=2))
    assert result["ok"] is False
    assert len(result["report"]["findings"]) == 2


def test_performance_budget_passes_default_values():
    result = build_performance_report(PerformanceBudgetRequest())
    assert result["ok"] is True
    assert all(item["passed"] for item in result["report"]["metrics"].values())


def test_performance_budget_blocks_lcp_regression():
    result = build_performance_report(PerformanceBudgetRequest(lcp_ms=4000))
    assert result["ok"] is False
    assert result["report"]["metrics"]["lcp_ms"]["passed"] is False


def test_security_blocks_public_write_and_secret_findings():
    result = build_security_report(SecurityAuditRequest(public_write_routes=1, secret_findings=1))
    assert result["ok"] is False
    assert result["report"]["remoteShellAllowed"] is False
    assert len(result["report"]["findings"]) == 2


def test_compatibility_matrix_counts_combinations():
    result = build_compatibility_report(CompatibilityMatrixRequest(browsers=["Chrome","Firefox"], editors=["Gutenberg"], viewports=["mobile","desktop"], runtimes=["browser-local","wordpress"]))
    assert result["ok"] is True
    assert result["report"]["matrixSize"] == 8


def test_compatibility_high_failure_blocks_release():
    result = build_compatibility_report(CompatibilityMatrixRequest(failures=[{"id":"safari-mobile","severity":"high"}]))
    assert result["ok"] is False


def test_migration_stress_requires_backup_and_rollback():
    result = build_migration_stress_report(MigrationStressRequest(backup_verified=False, rollback_verified=False))
    assert result["ok"] is False
    assert {item["code"] for item in result["report"]["findings"]} == {"backup-unverified","rollback-unverified"}


def test_migration_stress_reports_throughput():
    result = build_migration_stress_report(MigrationStressRequest(records=10000, observed_duration_ms=2000))
    assert result["ok"] is True
    assert result["report"]["throughputRecordsPerSecond"] == 5000.0


def test_failure_recovery_blocks_data_loss():
    result = build_failure_recovery_report(FailureInjectionRequest(scenarios=[{"id":"quota","severity":"critical","recovered":True,"dataLoss":True}]))
    assert result["ok"] is False
    assert result["report"]["automaticDataDeletion"] is False


def test_onboarding_requires_examples_and_quickstarts():
    result = build_onboarding_package(OnboardingPackageRequest(quickstarts=[], example_projects=0))
    assert result["ok"] is False
    assert set(result["package"]["missingItems"]) == {"quickstarts","example-projects"}


def test_stable_extension_contract_blocks_breaking_changes():
    result = build_extension_contract(ExtensionContractRequest(schemas=["project/1.0"], breaking_changes=["remove-hook"]))
    assert result["ok"] is False
    assert "stable-contract-has-breaking-changes" in result["contract"]["blockingIssues"]


def test_release_gate_holds_without_human_approval():
    result = build_release_gate(ReleaseGateRequest(evaluations=ready_records(), human_approval=False))
    assert result["ok"] is False
    assert result["gate"]["status"] == "hold"
    assert "human-approval-required" in result["gate"]["blockingIssues"]


def test_release_gate_passes_complete_reviewed_evidence():
    result = build_release_gate(ReleaseGateRequest(evaluations=ready_records(), human_approval=True))
    assert result["ok"] is True
    assert result["gate"]["status"] == "ready-for-public-release"
    assert result["gate"]["automaticPublicationAuthorized"] is False
    assert result["gate"]["gateHash"]


def test_release_gate_blocks_unresolved_critical_finding():
    result = build_release_gate(ReleaseGateRequest(evaluations=ready_records(), human_approval=True, unresolved_findings=[{"code":"security","severity":"critical"}]))
    assert result["ok"] is False
    assert "unresolved-high-or-critical-findings" in result["gate"]["blockingIssues"]
