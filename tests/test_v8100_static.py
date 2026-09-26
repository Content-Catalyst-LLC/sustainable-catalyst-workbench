from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def test_v8100_release_identity_and_routes():
    assert 'APP_VERSION = "9.10.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text()
    assert 'version="9.10.0"' in main and 'from app.v8100 import router as v8100_router' in main
    compose=(ROOT/'compose.yml').read_text()
    assert 'sustainable-catalyst-workbench:9.10.0' in compose and "d.get('version')=='9.10.0'" in compose and '127.0.0.1:8088:8088' in compose


def test_v8100_artifacts_and_capability_registry():
    for p in [
        'backend/app/v8100.py','backend/tests/test_reproducible_analysis_board_v8100.py',
        'RELEASE_NOTES_8.10.0_REPRODUCIBLE_ANALYSIS_BOARD.md','V8100_REPRODUCIBLE_ANALYSIS_BOARD_MAP.md',
        'docs/V8100_REPRODUCIBLE_ANALYSIS_BOARD.md','scripts/test_v8100_release.sh',
        'deploy/contabo/upgrade_workbench_backend_v8_10_0_contabo.sh','installers/apply_and_push_workbench_v8_10_0_macos.sh',
        'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v8100-reproducible-analysis-board.php',
        'workbench-v8.10.0.env.example']:
        assert (ROOT/p).exists(),p
    caps=(ROOT/'backend/app/v640.py').read_text()
    for flag in ('reproducibleAnalysisBoard','analysisBoardCrossObjectAssembly','analysisBoardImmutableSnapshots','analysisBoardProvenance','analysisBoardResearcherNarrative','analysisBoardCorePlanning'):
        assert flag in caps


def test_v8100_wordpress_and_boundary_contract():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 9.10.0' in main and "define('SCWB_VERSION', '9.10.0')" in main and 'SCWB_DIR' not in main
    assert 'scwb-v8100-reproducible-analysis-board.php' in main
    src=(ROOT/'backend/app/v8100.py').read_text()
    for literal in ('/analysis-board/manifest','/analysis-board/source-catalog/{project_key}','/analysis-board/build','/analysis-board/snapshots','/integration/core/analysis-board/plan','/v8100/status'):
        assert literal in src
    for boundary in ('boardIsScientificSourceOfTruth','findingsAutomaticallyGenerated','scientificValidityInferred','automaticWinnerSelectionPerformed','automaticCoreDispatchPerformed'):
        assert boundary in src


def test_v8100_deployer_uses_correct_workbench_port():
    deploy=(ROOT/'deploy/contabo/upgrade_workbench_backend_v8_10_0_contabo.sh').read_text()
    assert '127.0.0.1:8088' in deploy and '127.0.0.1:8000' not in deploy
