from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v980_identity_and_registration():
    assert 'APP_VERSION = "9.8.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="9.8.0"' in main and 'from app.v980 import router as v980_router' in main
    assert 'sustainable-catalyst-workbench:9.8.0' in (ROOT/'compose.yml').read_text()

def test_v980_backend_contract_surface():
    t=(ROOT/'backend/app/v980.py').read_text()
    for s in ('/cross-study-meta/manifest','/cross-study-meta/source-catalog/{project_key}','/cross-study-meta/analyze','/cross-study-meta/meta-analyses','/cross-study-meta/visualization-plan','/integration/core/cross-study-meta/plan','/v980/status'): assert s in t
    for s in ('automaticStudyComparabilityDecision','automaticPreferredModelSelection','automaticSignificanceConclusion','automaticCausalInference','automaticPublicationBiasConclusion','automaticScientificValidityInference','automaticCoreDispatch'): assert s in t

def test_v980_wordpress_surface():
    p=ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v980-cross-study-meta-analysis-workspace.php'; assert p.exists(); t=p.read_text()
    assert "add_shortcode('sc_workbench_cross_study_meta_analysis'" in t and "add_shortcode('sc_workbench_cross_study_meta_analysis_status'" in t
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text(); assert 'Version: 9.8.0' in main and "define('SCWB_VERSION', '9.8.0');" in main and 'scwb-v980-cross-study-meta-analysis-workspace.php' in main

def test_v980_release_assets_and_hardening():
    installer=(ROOT/'installers/apply_and_push_workbench_v9_8_0_macos.sh').read_text(); deploy=(ROOT/'deploy/contabo/upgrade_workbench_backend_v9_8_0_contabo.sh').read_text()
    assert 'rsync -a --checksum' in installer and '__pycache__' in installer and '.pytest_cache' in installer and "r.APP_VERSION=='9.8.0'" in installer
    assert 'rsync -a --checksum' in deploy and '__pycache__' in deploy and '127.0.0.1:8088' in deploy and "h['version']=='9.8.0'" in deploy
    assert (ROOT/'RELEASE_NOTES_9.8.0_CROSS_STUDY_COMPARISON_META_ANALYSIS_WORKSPACE.md').exists()
    assert (ROOT/'V980_CROSS_STUDY_COMPARISON_META_ANALYSIS_WORKSPACE_MAP.md').exists()
    assert (ROOT/'workbench-v9.8.0.env.example').exists()

def test_v980_capability_registry():
    t=(ROOT/'backend/app/v640.py').read_text()
    for s in ('crossStudyMetaAnalysisWorkspace','crossStudyEffectNormalization','crossStudyFixedEffectMetaAnalysis','crossStudyRandomEffectsMetaAnalysis','crossStudyHeterogeneityDiagnostics','crossStudySubgroupAnalysis','crossStudyLeaveOneOutSensitivity','crossStudyCorePlanning'): assert s in t
