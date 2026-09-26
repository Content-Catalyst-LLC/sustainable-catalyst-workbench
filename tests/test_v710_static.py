from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def test_v710_release_identity_router_compose():
    assert 'APP_VERSION = "10.0.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text()
    assert 'version="10.0.0"' in main
    assert 'from app.v710 import router as v710_router' in main
    assert 'app.include_router(v710_router)' in main
    compose=(ROOT/'compose.yml').read_text()
    assert 'sustainable-catalyst-workbench:10.0.0' in compose
    assert "d.get('version')=='10.0.0'" in compose


def test_v710_wordpress_identity_bootstrap_and_status_surface():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 10.0.0' in main
    assert "define('SCWB_VERSION', '10.0.0')" in main
    assert "includes/scwb-v710-unified-execution-object-model.php" in main
    assert 'SCWB_DIR' not in main
    inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v710-unified-execution-object-model.php').read_text()
    assert '/v710/status' in inc
    assert 'sc_workbench_execution_object_status' in inc
    assert '/execution-object/status' in inc


def test_v710_object_model_surfaces_and_boundaries():
    source=(ROOT/'backend/app/v710.py').read_text()
    for literal in (
        '/execution/objects/manifest','/execution/objects/execute','/execution/objects/workflow/run',
        '/execution/objects/project','/execution/objects/validate','/execution/objects/revise',
        '/integration/core/execution-objects/binding/plan','/v710/status',
        'sc-workbench-execution-object/1.0','sc.research.unified-research-scientific-investigation-runtime.v1',
        '/v1/research/unified-runtime/execution-bindings','/v1/research/runtime-contract/invocations',
        '/v1/research/runtime-contract/results','resultContentImmutable',
    ):
        assert literal in source
    assert 'eval(' not in source and 'exec(' not in source and 'subprocess' not in source


def test_v710_docs_release_scripts_and_packages_contract_present():
    required=[
        'RELEASE_NOTES_7.1.0_UNIFIED_EXECUTION_OBJECT_MODEL.md',
        'V710_UNIFIED_EXECUTION_OBJECT_SCHEMA.md',
        'BUILD_VALIDATION_7.1.0.txt',
        'WORKBENCH_V710_TERMINAL_COMMANDS.txt',
        'scripts/test_v710_release.sh',
        'deploy/contabo/upgrade_workbench_backend_v7_1_0_contabo.sh',
        'installers/apply_and_push_workbench_v7_1_0_macos.sh',
    ]
    for rel in required: assert (ROOT/rel).exists(),rel
