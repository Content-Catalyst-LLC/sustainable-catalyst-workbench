from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def test_v720_release_identity_router_compose():
    assert 'APP_VERSION = "7.9.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="7.9.0"' in main
    assert 'from app.v720 import router as v720_router' in main and 'app.include_router(v720_router)' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:7.9.0' in compose and "d.get('version')=='7.9.0'" in compose


def test_v720_runtime_orchestrator_surfaces_and_core_contract():
    src=(ROOT/'backend/app/v720.py').read_text()
    for literal in ('/execution/orchestrator/manifest','/execution/orchestrator/runtimes','/execution/orchestrator/route',
                    '/execution/orchestrator/execute','/execution/orchestrator/workflow/run','/execution/orchestrator/external/plan',
                    '/integration/core/runtime-orchestrator/workflow/plan','/v720/status','sc.research.workflow-orchestration.v1'):
        assert literal in src
    for forbidden in ('subprocess.run(', 'os.system(', 'eval(', 'exec('): assert forbidden not in src
    assert 'automaticExternalDispatchAuthorized' in src and 'automaticCoreDispatchAuthorized' in src


def test_v720_wordpress_identity_bootstrap_and_status_surface():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 7.9.0' in main and "define('SCWB_VERSION', '7.9.0')" in main
    assert 'includes/scwb-v720-scientific-runtime-orchestrator.php' in main
    assert 'SCWB_DIR' not in main
    inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v720-scientific-runtime-orchestrator.php').read_text()
    assert '/v720/status' in inc and 'sc_workbench_runtime_orchestrator_status' in inc and '/runtime-orchestrator/status' in inc


def test_v720_capability_registry_and_docs():
    cap=(ROOT/'backend/app/v640.py').read_text()
    assert 'scientific-runtime-orchestrator' in cap and 'researchWorkflowOrchestrationPlanning' in cap
    assert (ROOT/'RELEASE_NOTES_7.2.0_SCIENTIFIC_RUNTIME_ORCHESTRATOR.md').exists()
    assert (ROOT/'V720_RUNTIME_ADAPTER_MAP.md').exists()
    assert (ROOT/'docs/V720_SCIENTIFIC_RUNTIME_ORCHESTRATOR.md').exists()
    assert (ROOT/'workbench-v7.2.0.env.example').exists()
