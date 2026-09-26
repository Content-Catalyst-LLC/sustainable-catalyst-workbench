from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def test_v790_identity_router_compose():
    assert 'APP_VERSION = "9.8.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="9.8.0"' in main
    assert 'from app.v790 import router as v790_router' in main and 'app.include_router(v790_router)' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:9.8.0' in compose and "d.get('version')=='9.8.0'" in compose


def test_v790_surfaces_and_boundaries():
    src=(ROOT/'backend/app/v790.py').read_text()
    for literal in ('/workflow-graph/manifest','/workflow-graph/validate','/workflow-graph/plan','/workflow-graph/run','/workflow-graph/run/validate','/integration/core/workflow-graph/plan','/v790/status','sc.research.workflow-orchestration.v1'):
        assert literal in src
    for forbidden in ('subprocess.run(', 'os.system(', 'eval(', 'exec('): assert forbidden not in src
    for boundary in ('hiddenOutputSubstitutionPerformed','automaticCoreDispatchAuthorized','scientificValidityCertified'):
        assert boundary in src


def test_v790_wordpress():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 9.8.0' in main and "define('SCWB_VERSION', '9.8.0')" in main and 'SCWB_DIR' not in main
    assert 'includes/scwb-v790-scientific-workflow-graph.php' in main
    inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v790-scientific-workflow-graph.php').read_text()
    assert '/v790/status' in inc and 'sc_workbench_workflow_graph_status' in inc and '/workflow-graph/status' in inc


def test_v790_capabilities_docs_env():
    cap=(ROOT/'backend/app/v640.py').read_text(); assert 'scientific-workflow-graph' in cap and 'scientificWorkflowGraph' in cap
    assert (ROOT/'RELEASE_NOTES_7.9.0_SCIENTIFIC_WORKFLOW_GRAPH.md').exists()
    assert (ROOT/'V790_SCIENTIFIC_WORKFLOW_GRAPH_MAP.md').exists()
    assert (ROOT/'workbench-v8.5.0.env.example').exists()
