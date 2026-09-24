from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def test_v730_release_identity_router_compose():
    assert 'APP_VERSION = "8.11.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="8.11.0"' in main
    assert 'from app.v730 import router as v730_router' in main and 'app.include_router(v730_router)' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:8.11.0' in compose and "d.get('version')=='8.11.0'" in compose


def test_v730_data_workspace_surfaces_and_core_contract():
    src=(ROOT/'backend/app/v730.py').read_text()
    for literal in ('/data-workspace/manifest','/data-workspace/build','/data-workspace/units/convert','/data-workspace/derive','/data-workspace/execution-binding/plan','/integration/core/data-workspace/lineage/plan','/v730/status','sc.research.computation-analysis-execution-lineage.v1'):
        assert literal in src
    for forbidden in ('subprocess.run(', 'os.system(', 'eval(', 'exec('): assert forbidden not in src
    assert 'automaticCoreDispatchAuthorized' in src and 'automaticDataFetchAuthorized' in src


def test_v730_wordpress_identity_bootstrap_and_status_surface():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 8.11.0' in main and "define('SCWB_VERSION', '8.11.0')" in main
    assert 'includes/scwb-v730-data-variable-parameter-workspace.php' in main
    assert 'SCWB_DIR' not in main
    inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v730-data-variable-parameter-workspace.php').read_text()
    assert '/v730/status' in inc and 'sc_workbench_data_workspace_status' in inc and '/data-workspace/status' in inc


def test_v730_capability_registry_and_docs():
    cap=(ROOT/'backend/app/v640.py').read_text(); assert 'dataset-variable-parameter-workspace' in cap and 'workspaceLineagePlanning' in cap
    assert (ROOT/'RELEASE_NOTES_7.3.0_DATASET_VARIABLE_PARAMETER_WORKSPACE.md').exists()
    assert (ROOT/'V730_DATA_WORKSPACE_OBJECT_MAP.md').exists()
    assert (ROOT/'workbench-v7.3.0.env.example').exists()
