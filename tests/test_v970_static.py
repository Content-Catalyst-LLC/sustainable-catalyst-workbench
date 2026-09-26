from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v970_identity_and_registration():
    assert 'APP_VERSION = "10.0.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="10.0.0"' in main and 'from app.v970 import router as v970_router' in main
    assert 'sustainable-catalyst-workbench:10.0.0' in (ROOT/'compose.yml').read_text()

def test_v970_backend_contract_surface():
    t=(ROOT/'backend/app/v970.py').read_text()
    for s in ('/reproduction-replication/manifest','/reproduction-replication/source-catalog/{project_key}','/reproduction-replication/compose','/reproduction-replication/workflows','/reproduction-replication/execution-plan','/reproduction-replication/compare','/integration/core/reproduction-replication/plan','/v970/status'): assert s in t
    for s in ('automaticExecution','automaticReplicationVerdict','automaticScientificValidityInference','automaticHypothesisAcceptance','automaticCausalInference','automaticCoreDispatch'): assert s in t

def test_v970_wordpress_surface():
    p=ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v970-reproduction-replication-workflow.php'; assert p.exists(); t=p.read_text()
    assert "add_shortcode('sc_workbench_reproduction_replication'" in t and "add_shortcode('sc_workbench_reproduction_replication_status'" in t
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text(); assert 'Version: 10.0.0' in main and "define('SCWB_VERSION', '10.0.0');" in main and 'scwb-v970-reproduction-replication-workflow.php' in main

def test_v970_release_assets_and_hardening():
    installer=(ROOT/'installers/apply_and_push_workbench_v9_7_0_macos.sh').read_text(); deploy=(ROOT/'deploy/contabo/upgrade_workbench_backend_v9_7_0_contabo.sh').read_text()
    assert 'rsync -a --checksum' in installer and '__pycache__' in installer and '.pytest_cache' in installer and "r.APP_VERSION=='9.7.0'" in installer
    assert 'rsync -a --checksum' in deploy and '__pycache__' in deploy and '127.0.0.1:8088' in deploy and "h['version']=='9.7.0'" in deploy
    assert (ROOT/'RELEASE_NOTES_9.7.0_REPRODUCTION_REPLICATION_WORKFLOW.md').exists()
    assert (ROOT/'V970_REPRODUCTION_REPLICATION_WORKFLOW_MAP.md').exists()
    assert (ROOT/'workbench-v9.7.0.env.example').exists()

def test_v970_capability_registry():
    t=(ROOT/'backend/app/v640.py').read_text()
    for s in ('reproductionReplicationWorkflow','reproductionReplicationTargetBinding','reproductionReplicationEnvironmentCapture','reproductionReplicationComparisonCriteria','reproductionReplicationResultComparison','reproductionReplicationContentAddressedRecords','reproductionReplicationCorePlanning'): assert s in t
