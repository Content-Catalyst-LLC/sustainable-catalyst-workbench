from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v690_release_identity_and_routes():
    assert 'APP_VERSION = "7.3.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'from app.v690 import router as v690_router' in main and 'app.include_router(v690_router)' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:7.3.0' in compose and "d.get('version')=='7.3.0'" in compose

def test_v690_core_visual_contracts_and_boundaries_present():
    t=(ROOT/'backend/app/v690.py').read_text()
    for s in ('sc.visual-runtime.scene.v1','sc.visual-runtime.grammar.v1','sc.visual-runtime.unified-reasoning.v1','sc.visual-runtime.cross-product-integration.v1','/v1/visual-reasoning/objects','/v1/visual-runtime/scenes','/v1/visual-runtime/grammar/specifications'):
        assert s in t
    assert 'automaticCoreDispatchAuthorized' in t and 'rendererExecutionByCore' in t

def test_v690_wordpress_bridge_and_shortcode():
    p=ROOT/'wordpress-plugin/sustainable-catalyst-workbench'; main=(p/'sustainable-catalyst-workbench.php').read_text(); inc=(p/'includes/scwb-v690-core-visual-reasoning-runtime.php').read_text()
    assert 'Version: 7.3.0' in main and "define('SCWB_VERSION', '7.3.0')" in main
    assert 'scwb-v690-core-visual-reasoning-runtime.php' in main
    assert '/v690/status' in inc and 'sc_workbench_visual_reasoning_status' in inc

def test_v690_release_assets_exist():
    for rel in ('RELEASE_NOTES_6.9.0_CORE_VISUAL_REASONING_RUNTIME_ADAPTER.md','BUILD_VALIDATION_6.9.0.txt','WORKBENCH_V690_TERMINAL_COMMANDS.txt','docs/V690_CORE_VISUAL_REASONING_RUNTIME_ADAPTER.md','docs/V690_CORE_VISUAL_FIELD_MAP.md','scripts/test_v690_release.sh','deploy/contabo/upgrade_workbench_backend_v6_9_0_contabo.sh','workbench-v6.9.0.env.example'):
        assert (ROOT/rel).exists(), rel
