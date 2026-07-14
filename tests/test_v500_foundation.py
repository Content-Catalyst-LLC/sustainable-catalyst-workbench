from backend.app.v500 import (
    SurfaceRegistryInput, PlatformProjectInput, PortfolioInput, WorkflowPlanInput,
    IntegrityAuditInput, GovernanceGateInput, DeploymentPlanInput, DossierInput,
    PlatformPackageInput, status_record, build_surface_registry, build_platform_project,
    build_portfolio, build_workflow_plan, audit_integrity, evaluate_governance_gate,
    build_deployment_plan, build_dossier, build_platform_package,
)

SURFACES=[{"id":x,"state":"ready","version":"5.0.0"} for x in ["workbench","lab","site-intelligence","decision-studio","research-librarian","knowledge-library","wordpress","offline"]]

def project(**kwargs):
    data=dict(title="Integrated project",domains=["engineering"],surfaces=SURFACES,requirements=[{"id":"REQ-1","professionalReviewRequired":False}],evidence=[{"id":"EV-1"}],records=[{"id":"REC-1"}])
    data.update(kwargs);return build_platform_project(PlatformProjectInput(**data))

def integrity(p=None,**kwargs):
    return audit_integrity(IntegrityAuditInput(project=p or project(),**kwargs))

def gate(p=None,i=None,**kwargs):
    data=dict(project=p or project(),integrity=i or integrity(p),traceabilityComplete=True,securityReviewPassed=True,evaluationPassed=True,humanApproved=True,approver="Reviewer")
    data.update(kwargs);return evaluate_governance_gate(GovernanceGateInput(**data))

def test_status_integrates_all_surfaces_and_keeps_boundaries():
    r=status_record();assert r["version"]=="5.0.0";assert r["expectedStudioCount"]==28;assert len(r["integratedSurfaces"])==8;assert not r["automaticPublicationAuthorized"];assert not r["remoteShellAuthorized"]

def test_surface_registry_ready_and_stable():
    a=build_surface_registry(SurfaceRegistryInput(surfaces=SURFACES));b=build_surface_registry(SurfaceRegistryInput(surfaces=SURFACES));assert a["ready"];assert a["registryHash"]==b["registryHash"]

def test_surface_registry_blocks_missing_required_surface():
    r=build_surface_registry(SurfaceRegistryInput(surfaces=SURFACES[:-1]));assert not r["ready"];assert "offline" in r["missingRequiredSurfaces"]

def test_surface_registry_reports_degraded_fallback():
    surfaces=[dict(x) for x in SURFACES];surfaces[2]["state"]="degraded";r=build_surface_registry(SurfaceRegistryInput(surfaces=surfaces));assert "site-intelligence" in r["degradedSurfaces"];assert r["offlineFallbackAvailable"]

def test_project_is_content_hashed_and_nonexecuting():
    r=project();assert len(r["projectHash"])==64;assert r["readyForIntegrityAudit"];assert not r["automaticProjectExecutionAuthorized"]

def test_project_blocks_duplicate_records_and_missing_domain():
    r=project(domains=[],records=[{"id":"X"},{"id":"X"}]);codes={x["code"] for x in r["blockers"]};assert "duplicate-record" in codes;assert "domain-required" in codes

def test_high_stakes_project_requires_professional_review_boundary():
    r=project(highStakes=True);assert any(x["code"]=="professional-review-boundary-required" for x in r["blockers"])

def test_portfolio_counts_domains_and_blocks_duplicate_ids():
    p=project();r=build_portfolio(PortfolioInput(projects=[p,p]));assert r["projectCount"]==2;assert r["duplicateProjectIds"]==[p["projectId"]];assert not r["automaticPortfolioPublicationAuthorized"]

def test_workflow_orders_cross_surface_stages():
    r=build_workflow_plan(WorkflowPlanInput(title="Flow",stages=[{"id":"a","surface":"research-librarian","dependsOn":[]},{"id":"b","surface":"workbench","dependsOn":["a"]}]));assert r["ready"];assert r["executionOrder"]==["a","b"];assert len(r["crossSurfaceHandoffs"])==1

def test_workflow_detects_missing_dependency_and_cycle():
    r=build_workflow_plan(WorkflowPlanInput(title="Bad",stages=[{"id":"a","dependsOn":["b","missing"]},{"id":"b","dependsOn":["a"]}]));codes={x["code"] for x in r["blockers"]};assert "missing-stage-dependency" in codes;assert "workflow-cycle" in codes;assert not r["automaticWorkflowExecutionAuthorized"]

def test_high_stakes_workflow_requires_professional_review_stage():
    r=build_workflow_plan(WorkflowPlanInput(title="High",highStakes=True,stages=[{"id":"a"}]));assert any(x["code"]=="professional-review-stage-required" for x in r["blockers"])

def test_integrity_passes_canonical_project():
    r=integrity(requiredEvidenceIds=["EV-1"],requiredRequirementIds=["REQ-1"]);assert r["passed"];assert not r["automaticRepairAuthorized"]

def test_integrity_detects_schema_and_broken_links():
    p=project(records=[{"id":"REC-1","linkedRecordIds":["REC-404"]}]);p["schema"]="wrong";r=integrity(p);assert not r["passed"];codes={x["code"] for x in r["findings"]};assert "schema-mismatch" in codes;assert "broken-record-links" in codes

def test_governance_gate_requires_named_human_approval():
    r=gate(humanApproved=False,approver="");assert not r["approved"];assert any(x["code"]=="human-approval-required" for x in r["blockers"])

def test_governance_gate_approves_only_human_controlled_release():
    r=gate();assert r["approved"];assert r["state"]=="approved-for-human-controlled-release";assert not r["automaticPublicationAuthorized"];assert not r["automaticCertificationAuthorized"]

def test_high_stakes_gate_requires_professional_review():
    p=project(highStakes=True,requirements=[{"id":"REQ-1","professionalReviewRequired":True}]);i=integrity(p);r=gate(p,i,professionalReviewPassed=False);assert any(x["code"]=="professional-review-required" for x in r["blockers"])

def test_deployment_requires_checksums_backup_rollback_gate_and_approval():
    r=build_deployment_plan(DeploymentPlanInput(project=project()));codes={x["code"] for x in r["blockers"]};assert {"package-checksum-required","backup-required","rollback-required","governance-gate-required","explicit-approval-required"}.issubset(codes);assert not r["remoteShellAuthorized"]

def test_deployment_ready_after_all_controls():
    g=gate();r=build_deployment_plan(DeploymentPlanInput(project=project(),packageChecksumsVerified=True,backupVerified=True,rollbackVerified=True,governanceGate=g,explicitApproval=True));assert r["ready"];assert not r["automaticDeploymentAuthorized"]

def test_dossier_is_component_hashed_and_nonpublishing():
    p=project();i=integrity(p);g=gate(p,i);d=build_dossier(DossierInput(project=p,integrity=i,governance=g,artifacts=[{"id":"A"}]));assert d["readyForControlledRelease"];assert len(d["dossierHash"])==64;assert not d["automaticPublicationAuthorized"]

def test_package_requires_project_dossier_and_files():
    r=build_platform_package(PlatformPackageInput(project={}));codes={x["code"] for x in r["blockers"]};assert {"project-required","dossier-required","files-required"}.issubset(codes)

def test_package_redacts_secrets_and_remains_noninstalling():
    p=project();i=integrity(p);g=gate(p,i);d=build_dossier(DossierInput(project=p,integrity=i,governance=g));p["apiKey"]="secret";r=build_platform_package(PlatformPackageInput(project=p,dossier=d,files={"README.md":"ok"}));assert r["ready"];assert "apiKey" not in r["project"];assert r["removedSensitivePaths"];assert not r["automaticInstallationAuthorized"];assert not r["automaticExecutionAuthorized"]
