from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v9110_identity_and_registration():
    assert 'APP_VERSION = "9.11.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="9.11.0"' in main and 'from app.v9110 import router as v9110_router' in main
    assert 'sustainable-catalyst-workbench:9.11.0' in (ROOT/'compose.yml').read_text()

def test_v9110_backend_contract_surface():
    t=(ROOT/'backend/app/v9110.py').read_text()
    for s in ('/research-study-certification/manifest','/research-study-certification/source-catalog/{project_key}','/research-study-certification/evaluate','/research-study-certification/certifications','/integration/core/research-study-certification/plan','/v9110/status'): assert s in t
    for s in ('study-foundation','analysis-complete','reproducible-study','portable-study','handoff-ready','full-v9'): assert s in t
    for s in ('certificationIsScientificValidity','certificationIsPeerReview','automaticStudyApproval','automaticHypothesisAcceptance','automaticRemediation','automaticCoreDispatch','governedCoreObjectCreated'): assert s in t

def test_v9110_wordpress_surface():
    p=ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v9110-end-to-end-research-study-certification.php'; assert p.exists(); t=p.read_text()
    assert "add_shortcode('sc_workbench_research_study_certification'" in t and "add_shortcode('sc_workbench_research_study_certification_status'" in t
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text(); assert 'Version: 9.11.0' in main and "define('SCWB_VERSION', '9.11.0');" in main and 'scwb-v9110-end-to-end-research-study-certification.php' in main

def test_v9110_release_assets_and_hardening():
    installer=(ROOT/'installers/apply_and_push_workbench_v9_11_0_macos.sh').read_text(); deploy=(ROOT/'deploy/contabo/upgrade_workbench_backend_v9_11_0_contabo.sh').read_text()
    assert 'rsync -a --checksum' in installer and '__pycache__' in installer and '.pytest_cache' in installer and "r.APP_VERSION=='9.11.0'" in installer
    assert 'rsync -a --checksum' in deploy and '__pycache__' in deploy and '127.0.0.1:8088' in deploy and "h['version']=='9.11.0'" in deploy
    assert (ROOT/'RELEASE_NOTES_9.11.0_END_TO_END_RESEARCH_STUDY_CERTIFICATION.md').exists()
    assert (ROOT/'V9110_END_TO_END_RESEARCH_STUDY_CERTIFICATION_MAP.md').exists()
    assert (ROOT/'workbench-v9.11.0.env.example').exists()

def test_v9110_capability_registry():
    t=(ROOT/'backend/app/v640.py').read_text()
    for s in ('endToEndResearchStudyCertification','researchStudyCertificationProfiles','researchStudyCertificationObjectIntegrity','researchStudyCertificationLineageCoherence','researchStudyCertificationReproducibilityReadiness','researchStudyCertificationPortabilityReadiness','researchStudyCertificationHandoffReadiness','researchStudyCertificationContentAddressedRecords','researchStudyCertificationCorePlanning'): assert s in t
