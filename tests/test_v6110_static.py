from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_identity_and_registration():
    assert 'APP_VERSION = "6.13.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'from app.v6110 import router as v6110_router' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:6.13.0' in compose and "d.get('version')=='6.13.0'" in compose

def test_core_contracts_present():
    src=(ROOT/'backend/app/v6110.py').read_text()
    for contract in ('sc.open-forensics.quantitative-reconstruction.v1','sc.forensic-quantitative-handoff.v1','sc.open-forensics.quantitative-reproduction-package.v1','sc.open-forensics.forensic-timeline.v1','sc.open-forensics.spatial-temporal-evidence.v1','sc.open-forensics.competing-hypothesis-matrix.v1'):
        assert contract in src

def test_forensic_guardrails_present():
    src=(ROOT/'backend/app/v6110.py').read_text(); assert 'hypothesisRankingAuthorized' in src and 'truthDeterminationAuthorized' in src and 'guiltOrResponsibilityDeterminationAuthorized' in src

def test_wordpress_identity_and_include():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 6.13.0' in main and "define('SCWB_VERSION', '6.13.0')" in main and 'scwb-v6110-forensic-quantitative-reconstruction.php' in main
    assert "require_once __DIR__ . '/includes/scwb-v6100-predictive-intelligence-runtime.php';" in main
    assert "require_once __DIR__ . '/includes/scwb-v6110-forensic-quantitative-reconstruction.php';" in main
    assert 'SCWB_DIR' not in main

def test_release_artifacts_declared():
    for rel in ('RELEASE_NOTES_6.11.0_FORENSIC_QUANTITATIVE_RECONSTRUCTION_RUNTIME.md','docs/V6110_FORENSIC_QUANTITATIVE_RECONSTRUCTION_RUNTIME.md','docs/V6110_CORE_FORENSIC_FIELD_MAP.md','workbench-v6.11.0.env.example'):
        assert (ROOT/rel).exists(), rel
