from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v750_release_identity_router_compose():
    assert 'APP_VERSION = "8.3.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="8.3.0"' in main
    assert 'from app.v750 import router as v750_router' in main and 'app.include_router(v750_router)' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:8.3.0' in compose and "d.get('version')=='8.3.0'" in compose

def test_v750_simulation_surfaces_and_boundaries():
    src=(ROOT/'backend/app/v750.py').read_text()
    for literal in ('/simulations/manifest','/simulations/catalog','/simulations/run','/simulations/validate','/simulations/parameter-sweep','/simulations/workspace-binding/plan','/integration/core/simulation-lineage/plan','/v750/status','sc.research.computation-analysis-execution-lineage.v1'):
        assert literal in src
    for forbidden in ('subprocess.run(', 'os.system(', 'eval(', 'exec('): assert forbidden not in src
    assert 'automaticModelSelectionAuthorized' in src and 'scientificValidityCertified' in src and 'stabilityProofCertified' in src

def test_v750_wordpress_identity_and_status_surface():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 8.3.0' in main and "define('SCWB_VERSION', '8.3.0')" in main
    assert 'includes/scwb-v750-simulation-dynamical-systems-runtime.php' in main and 'SCWB_DIR' not in main
    inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v750-simulation-dynamical-systems-runtime.php').read_text()
    assert '/v750/status' in inc and 'sc_workbench_simulation_runtime_status' in inc and '/simulation-runtime/status' in inc

def test_v750_capabilities_docs_env():
    cap=(ROOT/'backend/app/v640.py').read_text(); assert 'simulation-dynamical-systems-runtime' in cap and 'simulationDynamicalSystemsRuntime' in cap
    assert (ROOT/'RELEASE_NOTES_7.5.0_SIMULATION_DYNAMICAL_SYSTEMS_RUNTIME.md').exists()
    assert (ROOT/'V750_SIMULATION_DYNAMICAL_SYSTEMS_MAP.md').exists()
    assert (ROOT/'workbench-v7.5.0.env.example').exists()
