from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def test_v860_identity_router_compose():
    assert 'APP_VERSION = "9.9.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="9.9.0"' in main and 'from app.v860 import router as v860_router' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:9.9.0' in compose and "d.get('version')=='9.9.0'" in compose and './data:/data' in compose


def test_v860_contract_routes_boundaries():
    src=(ROOT/'backend/app/v860.py').read_text()
    for literal in ('sc-workbench-visual-research-canvas/1.0','/research-canvas/manifest','/research-canvas/{project_key}','/research-canvas/{project_key}/layout','/research-canvas/{project_key}/layout/save','/research-canvas/{project_key}/lineage-overlay','/research-canvas/selection/resolve','/integration/core/research-canvas/plan','/v860/status'):
        assert literal in src
    for boundary in ('canvasIsScientificSourceOfTruth','scientificPayloadsDuplicated','automaticScientificInterpretationAuthorized','automaticCausalInferenceAuthorized','automaticCoreDispatchAuthorized'):
        assert boundary in src


def test_v860_capabilities_docs():
    cap=(ROOT/'backend/app/v640.py').read_text()
    for flag in ('visualResearchCanvas','visualResearchCanvasPersistentLayout','visualResearchCanvasLineageOverlay','visualResearchCanvasLinkedSelection','visualResearchCanvasCorePlanning'): assert flag in cap
    assert (ROOT/'RELEASE_NOTES_8.6.0_VISUAL_RESEARCH_CANVAS.md').exists()
    assert (ROOT/'V860_VISUAL_RESEARCH_CANVAS_MAP.md').exists()
    assert (ROOT/'workbench-v8.6.0.env.example').exists()


def test_v860_wordpress():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 9.9.0' in main and "define('SCWB_VERSION', '9.9.0')" in main and 'SCWB_DIR' not in main
    assert 'includes/scwb-v860-visual-research-canvas.php' in main
    inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v860-visual-research-canvas.php').read_text()
    for literal in ('/v860/status','sc_workbench_visual_research_canvas','visual-research-canvas','/research-canvas/'):
        assert literal in inc
