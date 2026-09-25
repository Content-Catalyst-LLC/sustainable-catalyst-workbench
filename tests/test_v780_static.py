from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v780_identity_router_compose():
    assert 'APP_VERSION = "9.1.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="9.1.0"' in main
    assert 'from app.v780 import router as v780_router' in main and 'app.include_router(v780_router)' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:9.1.0' in compose and "d.get('version')=='9.1.0'" in compose

def test_v780_surfaces_and_boundaries():
    src=(ROOT/'backend/app/v780.py').read_text()
    for literal in ('/validation/manifest','/validation/benchmark/evaluate','/validation/dataset-compare','/validation/convergence/evaluate','/validation/report/build','/validation/report/validate','/integration/core/validation-lineage/plan','/v780/status','sc.research.computation-analysis-execution-lineage.v1'):
        assert literal in src
    for forbidden in ('subprocess.run(', 'os.system(', 'eval(', 'exec('): assert forbidden not in src
    for boundary in ('scientificValidityCertificationAuthorized','truthDeterminationAuthorized','fitnessForPurposeCertificationAuthorized','automaticModelAcceptanceAuthorized'):
        assert boundary in src

def test_v780_wordpress():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 9.1.0' in main and "define('SCWB_VERSION', '9.1.0')" in main and 'SCWB_DIR' not in main
    assert 'includes/scwb-v780-model-validation-verification.php' in main
    inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v780-model-validation-verification.php').read_text()
    assert '/v780/status' in inc and 'sc_workbench_model_validation_status' in inc and '/model-validation/status' in inc

def test_v780_capabilities_docs_env():
    cap=(ROOT/'backend/app/v640.py').read_text(); assert 'model-validation-verification-framework' in cap and 'modelValidationVerificationFramework' in cap
    assert (ROOT/'RELEASE_NOTES_7.8.0_MODEL_VALIDATION_VERIFICATION_FRAMEWORK.md').exists()
    assert (ROOT/'V780_MODEL_VALIDATION_VERIFICATION_MAP.md').exists()
    assert (ROOT/'workbench-v7.8.0.env.example').exists()
