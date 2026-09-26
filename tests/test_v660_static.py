from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v660_release_identity_and_router_registration():
    release=(ROOT/'backend/app/release.py').read_text(); assert 'APP_VERSION = "9.7.0"' in release
    main=(ROOT/'backend/app/main.py').read_text(); assert 'from app.v660 import router as v660_router' in main and 'app.include_router(v660_router)' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:9.7.0' in compose and "d.get('version')=='9.7.0'" in compose

def test_v660_bridge_declares_core_300_paths_and_two_phase_boundary():
    s=(ROOT/'backend/app/v660.py').read_text()
    for path in ('/v1/research/unified-runtime/sessions','/v1/research/unified-runtime/product-bindings','/v1/research/unified-runtime/object-bindings','/v1/research/unified-runtime/execution-bindings','/v1/research/unified-runtime/visual-bindings','/v1/research/unified-runtime/package-bindings','/v1/research/unified-runtime/handoff-bindings'): assert path in s
    assert 'coreSessionIdMustComeFromCore' in s and 'automaticCorePersistenceAuthorized' in s

def test_v660_wordpress_identity_and_status_bridge():
    p=ROOT/'wordpress-plugin/sustainable-catalyst-workbench'; main=(p/'sustainable-catalyst-workbench.php').read_text(); inc=(p/'includes/scwb-v660-unified-research-session-bridge.php').read_text()
    assert 'Version: 9.7.0' in main and "define('SCWB_VERSION', '9.7.0')" in main and 'scwb-v660-unified-research-session-bridge.php' in main
    assert '/v660/status' in inc and 'sc_workbench_core_session_status' in inc

def test_v640_capabilities_now_advertise_v660_bridge():
    s=(ROOT/'backend/app/v640.py').read_text(); assert '"unifiedResearchSessionBinding": True' in s and 'platform-core-unified-research-session-bridge' in s
