from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def test_v890_release_identity_and_routes():
    assert 'APP_VERSION = "10.0.0"' in (ROOT / 'backend/app/release.py').read_text()
    main = (ROOT / 'backend/app/main.py').read_text()
    assert 'version="10.0.0"' in main and 'from app.v890 import router as v890_router' in main
    compose = (ROOT / 'compose.yml').read_text()
    assert 'sustainable-catalyst-workbench:10.0.0' in compose and "d.get('version')=='10.0.0'" in compose and '127.0.0.1:8088:8088' in compose


def test_v890_artifacts_and_capability_registry():
    for p in [
        'backend/app/v890.py',
        'backend/tests/test_interactive_scientific_figure_visualization_composer_v890.py',
        'RELEASE_NOTES_8.9.0_INTERACTIVE_SCIENTIFIC_FIGURE_VISUALIZATION_COMPOSER.md',
        'V890_INTERACTIVE_SCIENTIFIC_FIGURE_VISUALIZATION_COMPOSER_MAP.md',
        'docs/V890_INTERACTIVE_SCIENTIFIC_FIGURE_VISUALIZATION_COMPOSER.md',
        'scripts/test_v890_release.sh',
        'deploy/contabo/upgrade_workbench_backend_v8_9_0_contabo.sh',
        'installers/apply_and_push_workbench_v8_9_0_macos.sh',
        'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v890-interactive-scientific-figure-visualization-composer.php',
        'workbench-v8.9.0.env.example',
    ]:
        assert (ROOT / p).exists(), p
    caps = (ROOT / 'backend/app/v640.py').read_text()
    for flag in ('interactiveScientificFigureComposer', 'scientificFigureMultiPanelComposition', 'scientificFigureMetricDataBinding', 'scientificFigureProvenanceManifest', 'scientificFigureLinkedSelection', 'scientificFigureExportPlanning', 'scientificFigureCorePlanning'):
        assert flag in caps


def test_v890_wordpress_and_neutrality_contract():
    main = (ROOT / 'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 10.0.0' in main and "define('SCWB_VERSION', '10.0.0')" in main and 'SCWB_DIR' not in main
    assert 'scwb-v890-interactive-scientific-figure-visualization-composer.php' in main
    src = (ROOT / 'backend/app/v890.py').read_text()
    for literal in ('/figure-composer/manifest', '/figure-composer/source-catalog/{project_key}', '/figure-composer/compose', '/integration/core/figure-composer/plan', '/v890/status'):
        assert literal in src
    for boundary in ('automaticScientificEncodingSelectionPerformed', 'automaticWinnerSelectionPerformed', 'scientificValidityInferred', 'statisticalSignificanceInferred', 'automaticCoreDispatchPerformed'):
        assert boundary in src
