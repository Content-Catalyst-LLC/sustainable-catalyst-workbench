from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def test_v830_identity_router_compose():
    assert 'APP_VERSION = "8.4.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="8.4.0"' in main and 'from app.v830 import router as v830_router' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:8.4.0' in compose and "d.get('version')=='8.4.0'" in compose and './data:/data' in compose


def test_v830_contract_routes_boundaries():
    src=(ROOT/'backend/app/v830.py').read_text()
    for literal in ('sc-workbench-research-asset-artifact-registry/1.0','/research-assets/manifest','/research-assets/register','/research-assets/index/project','/research-assets/search','/integration/core/research-assets/plan','/v830/status'):
        assert literal in src
    for forbidden in ('subprocess.run(', 'os.system(', 'eval(', 'exec('): assert forbidden not in src
    for boundary in ('scientificPayloadsDuplicated','scientificExecutionPerformed','automaticRemoteRetrievalAuthorized','automaticCoreDispatchAuthorized'):
        assert boundary in src


def test_v830_capabilities_docs():
    cap=(ROOT/'backend/app/v640.py').read_text()
    for flag in ('researchAssetArtifactRegistry','researchAssetProjectIndexing','researchAssetSearch','researchAssetRevisionHistory','researchAssetCorePlanning'): assert flag in cap
    assert (ROOT/'RELEASE_NOTES_8.3.0_RESEARCH_ASSET_ARTIFACT_REGISTRY.md').exists()
    assert (ROOT/'V830_RESEARCH_ASSET_ARTIFACT_REGISTRY_MAP.md').exists()
    assert (ROOT/'workbench-v8.3.0.env.example').exists()


def test_v830_wordpress():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 8.4.0' in main and "define('SCWB_VERSION', '8.4.0')" in main and 'SCWB_DIR' not in main
    assert 'includes/scwb-v830-research-asset-artifact-registry.php' in main
    inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v830-research-asset-artifact-registry.php').read_text()
    assert '/v830/status' in inc and 'sc_workbench_research_asset_registry_status' in inc and '/research-asset-registry/status' in inc
