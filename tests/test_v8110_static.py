from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v8110_release_identity_and_routes():
    assert 'APP_VERSION = "8.11.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="8.11.0"' in main and 'from app.v8110 import router as v8110_router' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:8.11.0' in compose and "d.get('version')=='8.11.0'" in compose and '127.0.0.1:8088:8088' in compose

def test_v8110_artifacts_and_capability_registry():
    for p in ['backend/app/v8110.py','backend/tests/test_research_publication_evidence_handoff_v8110.py','RELEASE_NOTES_8.11.0_RESEARCH_PUBLICATION_EVIDENCE_HANDOFF.md','V8110_RESEARCH_PUBLICATION_EVIDENCE_HANDOFF_MAP.md','docs/V8110_RESEARCH_PUBLICATION_EVIDENCE_HANDOFF.md','scripts/test_v8110_release.sh','deploy/contabo/upgrade_workbench_backend_v8_11_0_contabo.sh','installers/apply_and_push_workbench_v8_11_0_macos.sh','wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v8110-research-publication-evidence-handoff.php','workbench-v8.11.0.env.example']:
        assert (ROOT/p).exists(),p
    caps=(ROOT/'backend/app/v640.py').read_text()
    for flag in ('researchPublicationEvidenceHandoff','publicationHandoffEvidenceManifest','publicationHandoffImmutablePackages','publicationHandoffMultiDestinationPlanning','publicationHandoffCorePlanning','publicationHandoffKnowledgeLibraryPlanning','publicationHandoffResearchLabPlanning'):
        assert flag in caps

def test_v8110_wordpress_and_boundary_contract():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text(); assert 'Version: 8.11.0' in main and "define('SCWB_VERSION', '8.11.0')" in main and 'SCWB_DIR' not in main
    assert 'scwb-v8110-research-publication-evidence-handoff.php' in main
    src=(ROOT/'backend/app/v8110.py').read_text()
    for literal in ('/publication-handoff/manifest','/publication-handoff/source-catalog/{project_key}','/publication-handoff/build','/publication-handoff/packages','/integration/core/publication-handoff/plan','/v8110/status'):
        assert literal in src
    for boundary in ('publicationPerformed','findingsAutomaticallyGenerated','scientificValidityInferred','evidenceConflictsAutomaticallyResolved','automaticCoreDispatchPerformed'):
        assert boundary in src

def test_v8110_deployer_uses_correct_workbench_port():
    deploy=(ROOT/'deploy/contabo/upgrade_workbench_backend_v8_11_0_contabo.sh').read_text(); assert '127.0.0.1:8088' in deploy and '127.0.0.1:8000' not in deploy
