from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def test_v700_release_identity_and_router():
    assert 'APP_VERSION = "7.0.0"' in (ROOT/'backend/app/release.py').read_text()
    main = (ROOT/'backend/app/main.py').read_text()
    assert 'version="7.0.0"' in main
    assert 'from app.v700 import router as v700_router' in main
    assert 'app.include_router(v700_router)' in main
    compose = (ROOT/'compose.yml').read_text()
    assert 'sustainable-catalyst-workbench:7.0.0' in compose
    assert "d.get('version')=='7.0.0'" in compose


def test_v700_wordpress_identity_and_safe_bootstrap():
    main = (ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 7.0.0' in main
    assert "define('SCWB_VERSION', '7.0.0')" in main
    assert "includes/scwb-v700-unified-execution-runtime.php" in main
    assert 'SCWB_DIR' not in main
    inc = (ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v700-unified-execution-runtime.php').read_text()
    assert '/v700/status' in inc
    assert 'sc_workbench_unified_execution_status' in inc
    assert '/unified-execution/status' in inc


def test_v700_source_has_required_surfaces_and_boundaries():
    source = (ROOT/'backend/app/v700.py').read_text()
    for literal in (
        '/execution/runtime/manifest', '/execution/runtime/catalog', '/execution/runtime/execute',
        '/execution/runtime/workflow/run', '/integration/core/unified-execution/lineage/plan', '/v700/status',
        'sc-workbench-unified-execution-result/1.0', 'sc.research.computation-analysis-execution-lineage.v1',
        'automaticCoreDispatchAuthorized', 'automaticCorePersistenceAuthorized', 'arbitraryPythonExecutionAuthorized',
    ):
        assert literal in source
    assert 'eval(' not in source
    assert 'exec(' not in source
    assert 'subprocess' not in source


def test_v700_docs_and_release_scripts_present():
    required = [
        'RELEASE_NOTES_7.0.0_UNIFIED_SCIENTIFIC_ENGINEERING_EXECUTION_RUNTIME.md',
        'V700_UNIFIED_EXECUTION_OPERATION_MAP.md',
        'BUILD_VALIDATION_7.0.0.txt',
        'WORKBENCH_V700_TERMINAL_COMMANDS.txt',
        'scripts/test_v700_release.sh',
        'deploy/contabo/upgrade_workbench_backend_v7_0_0_contabo.sh',
        'installers/apply_and_push_workbench_v7_0_0_macos.sh',
    ]
    for rel in required:
        assert (ROOT/rel).exists(), rel
