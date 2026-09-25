from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v840_identity_router_compose():
    assert 'APP_VERSION = "9.1.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="9.1.0"' in main and 'from app.v840 import router as v840_router' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:9.1.0' in compose and "d.get('version')=='9.1.0'" in compose and './data:/data' in compose

def test_v840_contract_routes_boundaries():
    src=(ROOT/'backend/app/v840.py').read_text()
    for literal in ('sc-workbench-interactive-execution-console/1.0','/execution-console/manifest','/execution-console/jobs/prepare','/execution-console/jobs/{job_id}/queue','/execution-console/jobs/{job_id}/run','/execution-console/jobs/{job_id}/cancel','/execution-console/compare','/integration/core/execution-console/plan','/v840/status'):
        assert literal in src
    for forbidden in ('subprocess.run(', 'os.system(', 'eval(', 'exec('): assert forbidden not in src
    for boundary in ('hiddenBackgroundWorkerImplied','arbitraryCodeExecutionAuthorized','runningJobPreemptionAuthorized','automaticCoreDispatchAuthorized'):
        assert boundary in src

def test_v840_capabilities_docs():
    cap=(ROOT/'backend/app/v640.py').read_text()
    for flag in ('interactiveExecutionConsole','executionConsoleDurableJobs','executionConsoleExplicitDispatch','executionConsoleJobComparison','executionConsoleCorePlanning'): assert flag in cap
    assert (ROOT/'RELEASE_NOTES_8.4.0_INTERACTIVE_EXECUTION_CONSOLE.md').exists()
    assert (ROOT/'V840_INTERACTIVE_EXECUTION_CONSOLE_MAP.md').exists()
    assert (ROOT/'workbench-v8.4.0.env.example').exists()

def test_v840_wordpress():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 9.1.0' in main and "define('SCWB_VERSION', '9.1.0')" in main and 'SCWB_DIR' not in main
    assert 'includes/scwb-v840-interactive-execution-console.php' in main
    inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v840-interactive-execution-console.php').read_text()
    assert '/v840/status' in inc and 'sc_workbench_execution_console_status' in inc and '/execution-console/status' in inc
