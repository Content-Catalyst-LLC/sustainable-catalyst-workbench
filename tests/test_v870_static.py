from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def test_v870_identity_router_compose():
    assert 'APP_VERSION = "9.6.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="9.6.0"' in main and 'from app.v870 import router as v870_router' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:9.6.0' in compose and "d.get('version')=='9.6.0'" in compose and './data:/data' in compose


def test_v870_contract_routes_boundaries():
    src=(ROOT/'backend/app/v870.py').read_text()
    for literal in ('sc-workbench-linked-scientific-views/1.0','/linked-scientific-views/manifest','/linked-scientific-views/query','/linked-scientific-views/selection/resolve','/integration/core/linked-scientific-views/plan','/v870/status'):
        assert literal in src
    for boundary in ('filtersMutateScientificObjects','selectionMutatesScientificObjects','automaticScientificInterpretationAuthorized','automaticCausalInferenceAuthorized','automaticWinnerSelectionAuthorized','automaticCoreDispatchAuthorized'):
        assert boundary in src


def test_v870_capabilities_docs():
    cap=(ROOT/'backend/app/v640.py').read_text()
    for flag in ('linkedScientificViews','linkedScientificCrossFiltering','linkedScientificSelectionPropagation','linkedScientificFacetCounts','linkedScientificCorePlanning'): assert flag in cap
    assert (ROOT/'RELEASE_NOTES_8.7.0_LINKED_SCIENTIFIC_VIEWS_CROSS_FILTERING.md').exists()
    assert (ROOT/'V870_LINKED_SCIENTIFIC_VIEWS_MAP.md').exists()
    assert (ROOT/'workbench-v8.9.0.env.example').exists()


def test_v870_wordpress():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 9.6.0' in main and "define('SCWB_VERSION', '9.6.0')" in main and 'SCWB_DIR' not in main
    assert 'includes/scwb-v870-linked-scientific-views.php' in main
    inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v870-linked-scientific-views.php').read_text()
    for literal in ('/v870/status','sc_workbench_linked_scientific_views','linked-scientific-views/query','linked-scientific-views/selection'):
        assert literal in inc
