from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v820_identity_router_compose():
    assert 'APP_VERSION = "9.1.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="9.1.0"' in main and 'from app.v820 import router as v820_router' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:9.1.0' in compose and "d.get('version')=='9.1.0'" in compose and './data:/data' in compose

def test_v820_contract_routes_and_boundaries():
    src=(ROOT/'backend/app/v820.py').read_text()
    for literal in ('sc-workbench-unified-research-project-workspace/1.0','/research-projects/manifest','/research-projects/build','/research-projects/save','/research-projects/surface/plan','/integration/core/research-project-workspace/plan','/v820/status'):
        assert literal in src
    for forbidden in ('subprocess.run(', 'os.system(', 'eval(', 'exec('): assert forbidden not in src
    for boundary in ('scientificExecutionPerformed','automaticNotebookReplayAuthorized','automaticWorkflowExecutionAuthorized','automaticCoreDispatchAuthorized'):
        assert boundary in src

def test_v820_capabilities_and_docs():
    cap=(ROOT/'backend/app/v640.py').read_text()
    for flag in ('unifiedResearchProjectWorkspace','researchProjectDashboardSummaries','researchProjectSurfaceNavigation','researchProjectActivityHistory','researchProjectCoreSessionPlanning'): assert flag in cap
    assert (ROOT/'RELEASE_NOTES_8.2.0_UNIFIED_RESEARCH_PROJECT_WORKSPACE.md').exists()
    assert (ROOT/'V820_UNIFIED_RESEARCH_PROJECT_WORKSPACE_MAP.md').exists()
    assert (ROOT/'workbench-v8.2.0.env.example').exists()

def test_v820_wordpress():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 9.1.0' in main and "define('SCWB_VERSION', '9.1.0')" in main and 'SCWB_DIR' not in main
    assert 'includes/scwb-v820-unified-research-project-workspace.php' in main
    inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v820-unified-research-project-workspace.php').read_text()
    assert '/v820/status' in inc and 'sc_workbench_research_project_status' in inc and '/research-project/status' in inc
