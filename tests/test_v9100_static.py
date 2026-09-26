from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v9100_identity_and_registration():
    assert 'APP_VERSION = "9.11.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="9.11.0"' in main and 'from app.v9100 import router as v9100_router' in main
    assert 'sustainable-catalyst-workbench:9.11.0' in (ROOT/'compose.yml').read_text()

def test_v9100_backend_contract_surface():
    t=(ROOT/'backend/app/v9100.py').read_text()
    for s in ('/scientific-research-handoff/manifest','/scientific-research-handoff/source-catalog/{project_key}','/scientific-research-handoff/compose','/scientific-research-handoff/handoffs','/scientific-research-handoff/destination-plan','/integration/core/scientific-research-handoff/plan','/v9100/status'): assert s in t
    for s in ('platform-core','knowledge-library','research-lab','decision-studio','external-publication','archive'): assert s in t
    for s in ('automaticDestinationDispatch','automaticNativeImportActivation','automaticScientificValidityInference','automaticPublication','automaticDecisionRecommendation','governedCoreObjectCreated'): assert s in t

def test_v9100_wordpress_surface():
    p=ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v9100-platform-wide-scientific-research-handoff.php'; assert p.exists(); t=p.read_text()
    assert "add_shortcode('sc_workbench_scientific_research_handoff'" in t and "add_shortcode('sc_workbench_scientific_research_handoff_status'" in t
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text(); assert 'Version: 9.11.0' in main and "define('SCWB_VERSION', '9.11.0');" in main and 'scwb-v9100-platform-wide-scientific-research-handoff.php' in main

def test_v9100_release_assets_and_hardening():
    installer=(ROOT/'installers/apply_and_push_workbench_v9_10_0_macos.sh').read_text(); deploy=(ROOT/'deploy/contabo/upgrade_workbench_backend_v9_10_0_contabo.sh').read_text()
    assert 'rsync -a --checksum' in installer and '__pycache__' in installer and '.pytest_cache' in installer and "r.APP_VERSION=='9.10.0'" in installer
    assert 'rsync -a --checksum' in deploy and '__pycache__' in deploy and '127.0.0.1:8088' in deploy and "h['version']=='9.10.0'" in deploy
    assert (ROOT/'RELEASE_NOTES_9.10.0_PLATFORM_WIDE_SCIENTIFIC_RESEARCH_HANDOFF.md').exists()
    assert (ROOT/'V9100_PLATFORM_WIDE_SCIENTIFIC_RESEARCH_HANDOFF_MAP.md').exists()
    assert (ROOT/'workbench-v9.10.0.env.example').exists()

def test_v9100_capability_registry():
    t=(ROOT/'backend/app/v640.py').read_text()
    for s in ('platformWideScientificResearchHandoff','scientificResearchPortableTransportBinding','scientificResearchDestinationContracts','scientificResearchDestinationReadiness','scientificResearchRequirementReporting','scientificResearchContentAddressedHandoffs','scientificResearchCrossProductPlanning','scientificResearchCoreGovernancePlanning'): assert s in t
