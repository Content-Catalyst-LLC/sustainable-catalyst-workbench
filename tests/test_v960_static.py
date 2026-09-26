from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v960_identity_and_registration():
    assert 'APP_VERSION = "9.12.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="9.12.0"' in main and 'from app.v960 import router as v960_router' in main
    assert 'sustainable-catalyst-workbench:9.12.0' in (ROOT/'compose.yml').read_text()

def test_v960_backend_contract_surface():
    t=(ROOT/'backend/app/v960.py').read_text()
    for s in ('/results-synthesis/manifest','/results-synthesis/source-catalog/{project_key}','/results-synthesis/compose','/results-synthesis/syntheses','/results-synthesis/publication-plan','/integration/core/results-synthesis/plan','/v960/status'): assert s in t
    for s in ('automaticNarrativeGeneration','automaticFindingGeneration','automaticHypothesisAcceptance','automaticSignificanceDecision','automaticCausalInference','automaticPublication','automaticCoreDispatch'): assert s in t

def test_v960_wordpress_surface():
    p=ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v960-scientific-results-narrative-synthesis.php'; assert p.exists(); t=p.read_text()
    assert "add_shortcode('sc_workbench_scientific_results_synthesis'" in t and "add_shortcode('sc_workbench_scientific_results_synthesis_status'" in t
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text(); assert 'Version: 9.12.0' in main and "define('SCWB_VERSION', '9.12.0');" in main and 'scwb-v960-scientific-results-narrative-synthesis.php' in main

def test_v960_release_assets_and_hardening():
    installer=(ROOT/'installers/apply_and_push_workbench_v9_6_0_macos.sh').read_text(); deploy=(ROOT/'deploy/contabo/upgrade_workbench_backend_v9_6_0_contabo.sh').read_text()
    assert 'rsync -a --checksum' in installer and '__pycache__' in installer and '.pytest_cache' in installer and "r.APP_VERSION=='9.6.0'" in installer
    assert 'rsync -a --checksum' in deploy and '__pycache__' in deploy and '127.0.0.1:8088' in deploy and "h['version']=='9.6.0'" in deploy
    assert (ROOT/'RELEASE_NOTES_9.6.0_SCIENTIFIC_RESULTS_NARRATIVE_SYNTHESIS.md').exists()
    assert (ROOT/'V960_SCIENTIFIC_RESULTS_NARRATIVE_SYNTHESIS_MAP.md').exists()
    assert (ROOT/'workbench-v9.6.0.env.example').exists()

def test_v960_capability_registry():
    t=(ROOT/'backend/app/v640.py').read_text()
    for s in ('scientificResultsNarrativeSynthesis','scientificResultsResearcherAuthoredNarrative','scientificResultsSourceBinding','scientificResultsStatementTraceability','scientificResultsContentAddressedRecords','scientificResultsPublicationPlanning','scientificResultsCorePlanning'): assert s in t
