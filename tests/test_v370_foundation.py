import pytest

from app.v370 import (
    CalculationContractRequest,
    DomainProfileRequest,
    ExperimentContractRequest,
    IntegrationBundleRequest,
    LanguageEquivalenceRequest,
    NotebookEntryRequest,
    ReportTemplateRequest,
    SyncPlanRequest,
    ValidationContractRequest,
    build_calculation_contract,
    build_domain_profile,
    build_experiment_contract,
    build_integration_bundle,
    build_language_equivalence,
    build_notebook_entry,
    build_report_template,
    build_sync_plan,
    build_validation_contract,
    list_domain_registry,
)


def test_domain_registry_covers_current_and_planned_labs():
    result = list_domain_registry()
    assert result["registry"]["domainCount"] >= 20
    keys = {item["domain"] for item in result["registry"]["domains"]}
    assert {"physics", "electrical-embedded", "civil-infrastructure", "rocket-propulsion", "biomedical"}.issubset(keys)


def test_domain_profile_reports_missing_capability():
    result = build_domain_profile(DomainProfileRequest(domain="physics", requested_capabilities=["mechanics", "clinical-diagnosis"]))
    assert result["ok"] is False
    assert result["profile"]["missingCapabilities"] == ["clinical-diagnosis"]


def test_unsupported_domain_is_rejected():
    with pytest.raises(ValueError):
        build_domain_profile(DomainProfileRequest(domain="alchemy"))


def test_calculation_contract_requires_inputs_and_flags_missing_units():
    result = build_calculation_contract(CalculationContractRequest(domain="mechanical-thermal", title="Heat flow", equation="q=kA dT/L", inputs={"k": 1, "A": 2}, units={"k": "W/mK"}))
    assert result["ok"] is False
    assert result["contract"]["missingUnits"] == ["A"]
    assert result["contract"]["humanReviewRequired"] is True


def test_calculation_without_inputs_is_rejected():
    with pytest.raises(ValueError):
        build_calculation_contract(CalculationContractRequest(domain="physics", inputs={}))


def test_biomedical_experiment_requires_safety_review_and_no_execution():
    result = build_experiment_contract(ExperimentContractRequest(domain="biomedical", dependent_variables=["signal quality"], protocol_steps=["load de-identified sample", "analyze"] , replicates=3))
    contract = result["contract"]
    assert contract["safetyReviewRequired"] is True
    assert contract["executionAuthorized"] is False


def test_experiment_requires_protocol_and_dependent_variable():
    with pytest.raises(ValueError):
        build_experiment_contract(ExperimentContractRequest(domain="chemistry", protocol_steps=[]))


def test_validation_never_auto_certifies():
    result = build_validation_contract(ValidationContractRequest(domain="physics", supplied_checks=["dimensional-consistency", "boundary-conditions", "uncertainty", "independent-check"], reviewer="Reviewer"))
    assert result["ok"] is True
    assert result["validation"]["status"] == "review-ready"
    assert result["validation"]["autoValidated"] is False


def test_validation_blocks_missing_domain_checks():
    result = build_validation_contract(ValidationContractRequest(domain="civil-infrastructure", supplied_checks=["load-cases"], reviewer="Engineer"))
    assert result["ok"] is False
    assert result["validation"]["status"] == "blocked"
    assert result["validation"]["missingChecks"]


def test_notebook_entry_has_stable_identity_and_links():
    result = build_notebook_entry(NotebookEntryRequest(domain="astronomy", observations=["Signal detected"], calculation_ids=["calc-1"], author="Analyst"))
    entry = result["entry"]
    assert entry["entryId"].startswith("note-astronomy-")
    assert entry["calculationIds"] == ["calc-1"]
    assert entry["entryHash"]


def test_report_template_contains_validation_and_reproducibility():
    result = build_report_template(ReportTemplateRequest(domain="energy-engineering", record_ids=["calc-1", "exp-1"]))
    sections = result["reportTemplate"]["sections"]
    assert "Validation evidence" in sections
    assert "Reproducibility package" in sections
    assert result["reportTemplate"]["publicationState"] == "draft"


def test_sync_plan_holds_conflicts_for_manual_review():
    result = build_sync_plan(SyncPlanRequest(domain="urban-spatial", workbench_hash="aaa", lab_hash="bbb", conflict_strategy="manual"))
    plan = result["syncPlan"]
    assert result["ok"] is False
    assert plan["action"] == "hold-for-review"
    assert plan["backupRequired"] is True
    assert plan["destructiveOverwrite"] is False


def test_bundle_manifest_hashes_every_record():
    records = [{"schema": "demo/1.0", "value": 1}, {"schema": "demo/1.0", "value": 2}]
    result = build_integration_bundle(IntegrationBundleRequest(domain="circular-economy", records=records))
    assert result["bundle"]["manifest"]["recordCount"] == 2
    assert len(result["bundle"]["manifest"]["records"]) == 2
    assert result["bundleHash"]


def test_language_equivalence_supports_requested_runtime_set():
    result = build_language_equivalence(LanguageEquivalenceRequest(domain="aerospace", equation="L=0.5*rho*v^2*S*Cl", languages=["python", "r", "javascript", "rust", "go"]))
    assert result["ok"] is True
    assert set(result["plan"]["languages"]) == {"python", "r", "javascript", "rust", "go"}
    assert result["plan"]["humanReviewRequired"] is True


def test_language_equivalence_reports_unsupported_runtime():
    result = build_language_equivalence(LanguageEquivalenceRequest(domain="physics", languages=["python", "fortran-77-unknown"]))
    assert result["ok"] is False
    assert result["plan"]["unsupportedLanguages"] == ["fortran-77-unknown"]
