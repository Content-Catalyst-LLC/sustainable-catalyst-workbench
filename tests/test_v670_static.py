from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PLUGIN=ROOT/'wordpress-plugin/sustainable-catalyst-workbench'

def test_v670_release_identity_and_router_registration():
    assert 'APP_VERSION = "9.10.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'from app.v670 import router as v670_router' in main and 'app.include_router(v670_router)' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:9.10.0' in compose and "d.get('version')=='9.10.0'" in compose

def test_v670_exact_core_lineage_contract_and_paths():
    s=(ROOT/'backend/app/v670.py').read_text()
    assert 'sc.research.computation-analysis-execution-lineage.v1' in s
    for path in ('/v1/research/computation-lineage/executions','/inputs','/parameters','/assumptions','/environments','/steps','/outputs','/research-bindings','/dependencies','/verifications','/revisions','/snapshots'): assert path in s
    assert 'coreExecutionIdMustComeFromCore' in s and 'automaticCorePersistenceAuthorized' in s

def test_v670_session_integration_and_boundary():
    s=(ROOT/'backend/app/v670.py').read_text(); assert 'build_execution_binding' in s; assert '/v1/research/unified-runtime/execution-bindings' in s
    for marker in ('coreExecutesWorkbenchCode','coreInfersFindingsOrClaims','coreValidatesScientificResults','coreInfersReproducibility','coreDeterminesTruth'): assert marker in s

def test_v670_wordpress_identity_and_status_bridge():
    main=(PLUGIN/'sustainable-catalyst-workbench.php').read_text(); inc=(PLUGIN/'includes/scwb-v670-computation-execution-lineage.php').read_text()
    assert 'Version: 9.10.0' in main and "define('SCWB_VERSION', '9.10.0')" in main and 'scwb-v670-computation-execution-lineage.php' in main
    assert '/v670/status' in inc and 'sc_workbench_core_execution_lineage_status' in inc

def test_v640_capabilities_advertise_v670_lineage_bridge():
    s=(ROOT/'backend/app/v640.py').read_text(); assert '"executionLineageBridge": True' in s and 'platform-core-computation-execution-lineage-bridge' in s
