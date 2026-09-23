from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def test_v740_release_identity_router_compose():
    assert 'APP_VERSION = "8.7.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="8.7.0"' in main
    assert 'from app.v740 import router as v740_router' in main and 'app.include_router(v740_router)' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:8.7.0' in compose and "d.get('version')=='8.7.0'" in compose


def test_v740_solver_surfaces_and_boundaries():
    src=(ROOT/'backend/app/v740.py').read_text()
    for literal in ('/solvers/manifest','/solvers/catalog','/solvers/solve','/solvers/validate','/solvers/convergence-study','/solvers/workspace-binding/plan','/integration/core/solver-lineage/plan','/v740/status','sc.research.computation-analysis-execution-lineage.v1'):
        assert literal in src
    for forbidden in ('subprocess.run(', 'os.system(', 'eval(', 'exec('): assert forbidden not in src
    assert 'automaticSolverFallbackAuthorized' in src and 'scientificValidityCertified' in src


def test_v740_wordpress_identity_and_status_surface():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 8.7.0' in main and "define('SCWB_VERSION', '8.7.0')" in main
    assert 'includes/scwb-v740-numerical-methods-solver-runtime.php' in main
    assert 'SCWB_DIR' not in main
    inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v740-numerical-methods-solver-runtime.php').read_text()
    assert '/v740/status' in inc and 'sc_workbench_numerical_solver_status' in inc and '/numerical-solver/status' in inc


def test_v740_capabilities_docs_env():
    cap=(ROOT/'backend/app/v640.py').read_text(); assert 'numerical-methods-solver-runtime' in cap and 'numericalMethodsSolverRuntime' in cap
    assert (ROOT/'RELEASE_NOTES_7.4.0_NUMERICAL_METHODS_SOLVER_RUNTIME.md').exists()
    assert (ROOT/'V740_NUMERICAL_SOLVER_METHOD_MAP.md').exists()
    assert (ROOT/'workbench-v7.4.0.env.example').exists()
